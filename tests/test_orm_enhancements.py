"""Integration tests for the "richer ORM" additions:

F()/FExpression wiring (atomic updates + column-to-column filters), eager
loading, bulk operations, get_or_create/update_or_create, values()/
values_list(), only()/defer(), and atomic().

Uses the `miniproject_env` fixture (a real bootstrapped project) so these
exercise the full session/engine stack, not isolated unit logic.
"""

from __future__ import annotations

from contextlib import contextmanager

import pytest

from fastframe.db.session import session_scope
from fastframe.models import Model, fields
from fastframe.models.query import F


class Counter(Model):
    name = fields.CharField(max_length=100)
    value = fields.IntegerField(default=0)
    threshold = fields.IntegerField(default=0)

    class Meta:
        db_table = "orm_enh_counters"
        app_label = "orm_enh"


class Publisher(Model):
    name = fields.CharField(max_length=100)

    class Meta:
        db_table = "orm_enh_publishers"
        app_label = "orm_enh"


class Book(Model):
    title = fields.CharField(max_length=100)
    publisher_id = fields.ForeignKey("Publisher", related_name="books")

    class Meta:
        db_table = "orm_enh_books"
        app_label = "orm_enh"


def _create_all():
    from fastframe.db.engine import get_engine

    Model.metadata.create_all(bind=get_engine())


@contextmanager
def _count_queries():
    from sqlalchemy import event

    from fastframe.db.engine import get_engine

    counter = {"n": 0}
    engine = get_engine()

    def _before_cursor_execute(*args, **kwargs):
        counter["n"] += 1

    event.listen(engine, "before_cursor_execute", _before_cursor_execute)
    try:
        yield counter
    finally:
        event.remove(engine, "before_cursor_execute", _before_cursor_execute)


def test_f_expression_increment_is_atomic_and_refreshes_instance(miniproject_env):
    _create_all()
    with session_scope():
        for c in list(Counter.objects.all()):
            c.delete()
        c = Counter(name="hits", value=5, threshold=10)
        c.save()
        counter_id = c.id

    with session_scope():
        c = Counter.objects.get(id=counter_id)
        c.value = F("value") + 1
        c.save()
        assert c.value == 6

    with session_scope():
        reloaded = Counter.objects.get(id=counter_id)
        assert reloaded.value == 6


def test_f_expression_supports_all_arithmetic_ops(miniproject_env):
    _create_all()
    with session_scope():
        for c in list(Counter.objects.all()):
            c.delete()
        c = Counter(name="math", value=10, threshold=2)
        c.save()
        counter_id = c.id

    with session_scope():
        c = Counter.objects.get(id=counter_id)
        c.value = F("value") - 3
        c.save()
        assert c.value == 7

    with session_scope():
        c = Counter.objects.get(id=counter_id)
        c.value = F("value") * 2
        c.save()
        assert c.value == 14

    with session_scope():
        c = Counter.objects.get(id=counter_id)
        c.value = F("value") / 2
        c.save()
        assert c.value == 7


def test_f_expression_on_unsaved_instance_raises(miniproject_env):
    import pytest

    _create_all()
    with session_scope():
        c = Counter(name="new", value=1, threshold=1)
        c.value = F("value") + 1
        with pytest.raises(ValueError, match="unsaved"):
            c.save()


def test_filter_with_f_compares_two_columns(miniproject_env):
    _create_all()
    with session_scope():
        for c in list(Counter.objects.all()):
            c.delete()
        Counter(name="above", value=100, threshold=1).save()
        Counter(name="below", value=1, threshold=100).save()
        Counter(name="equal", value=5, threshold=5).save()

        above = list(Counter.objects.filter(value__gt=F("threshold")))
        assert [c.name for c in above] == ["above"]

        at_least = list(Counter.objects.filter(value__gte=F("threshold")))
        assert {c.name for c in at_least} == {"above", "equal"}


def _make_publishers_and_books():
    for p in list(Publisher.objects.all()):
        p.delete()
    p1 = Publisher(name="Acme")
    p1.save()
    p2 = Publisher(name="Globex")
    p2.save()
    Book(title="Book A", publisher_id=p1.id).save()
    Book(title="Book B", publisher_id=p1.id).save()
    Book(title="Book C", publisher_id=p2.id).save()


def test_select_related_avoids_n_plus_1_for_forward_fk(miniproject_env):
    _create_all()
    with session_scope():
        _make_publishers_and_books()

    with session_scope():
        with _count_queries() as counter:
            books = list(Book.objects.select_related("publisher").order_by("title"))
            names = [book.publisher.name for book in books]
        assert names == ["Acme", "Acme", "Globex"]
        assert counter["n"] == 1  # one JOINed query, not one-per-book


def test_without_select_related_issues_extra_queries(miniproject_env):
    """Without select_related, each *distinct* related row needs its own
    query the first time it's touched (SQLAlchemy's identity map only
    dedupes a many-to-one lookup against an object already loaded in the
    same session) — so this scales with the data, unlike the single JOIN
    query select_related() produces above.
    """
    _create_all()
    with session_scope():
        for p in list(Publisher.objects.all()):
            p.delete()
        publishers = [Publisher(name=f"Pub {i}") for i in range(3)]
        for p in publishers:
            p.save()
        for i, p in enumerate(publishers):
            Book(title=f"Book {i}", publisher_id=p.id).save()

    with session_scope():
        with _count_queries() as counter:
            books = list(Book.objects.order_by("title"))
            for book in books:
                _ = book.publisher.name
        assert counter["n"] == 1 + len(books)  # the N+1 this feature avoids


def test_prefetch_related_avoids_n_plus_1_for_reverse_fk(miniproject_env):
    _create_all()
    with session_scope():
        _make_publishers_and_books()

    with session_scope():
        with _count_queries() as counter:
            publishers = list(Publisher.objects.prefetch_related("books").order_by("name"))
            titles_by_publisher = [
                sorted(book.title for book in pub.books) for pub in publishers
            ]
        assert titles_by_publisher == [["Book A", "Book B"], ["Book C"]]
        assert counter["n"] == 2  # one query for publishers, one batched IN query for books


def test_bulk_create_inserts_and_populates_pks(miniproject_env):
    _create_all()
    with session_scope():
        for c in list(Counter.objects.all()):
            c.delete()
        objects = [Counter(name=f"c{i}", value=i) for i in range(5)]
        created = Counter.objects.bulk_create(objects)
        assert all(obj.id is not None for obj in created)
        assert Counter.objects.count() == 5


def test_bulk_create_respects_batch_size(miniproject_env):
    _create_all()
    with session_scope():
        for c in list(Counter.objects.all()):
            c.delete()
        objects = [Counter(name=f"c{i}", value=i) for i in range(7)]
        Counter.objects.bulk_create(objects, batch_size=3)
        assert Counter.objects.count() == 7


def test_bulk_update_writes_specified_fields_only(miniproject_env):
    _create_all()
    with session_scope():
        for c in list(Counter.objects.all()):
            c.delete()
        c1 = Counter(name="a", value=1, threshold=100)
        c1.save()
        c2 = Counter(name="b", value=2, threshold=200)
        c2.save()

        c1.value = 10
        c1.threshold = 999  # not in `fields` below -> should NOT be written
        c2.value = 20
        c1_id, c2_id = c1.id, c2.id

        updated = Counter.objects.bulk_update([c1, c2], fields=["value"])
        assert updated == 2

    with session_scope():
        reloaded1 = Counter.objects.get(id=c1_id)
        reloaded2 = Counter.objects.get(id=c2_id)
        assert reloaded1.value == 10
        assert reloaded1.threshold == 100  # untouched
        assert reloaded2.value == 20


def test_queryset_update_is_a_single_bulk_statement(miniproject_env):
    _create_all()
    with session_scope():
        for c in list(Counter.objects.all()):
            c.delete()
        Counter(name="low", value=1, threshold=0).save()
        Counter(name="high", value=100, threshold=0).save()

        with _count_queries() as counter:
            matched = Counter.objects.filter(value__gte=50).update(threshold=1)
        assert matched == 1
        assert counter["n"] == 1

    with session_scope():
        low = Counter.objects.get(name="low")
        high = Counter.objects.get(name="high")
        assert low.threshold == 0
        assert high.threshold == 1


def test_queryset_update_with_f_expression(miniproject_env):
    _create_all()
    with session_scope():
        for c in list(Counter.objects.all()):
            c.delete()
        Counter(name="a", value=5, threshold=0).save()
        Counter(name="b", value=7, threshold=0).save()

        Counter.objects.all().update(value=F("value") + 1)

    with session_scope():
        values = sorted(c.value for c in Counter.objects.all())
        assert values == [6, 8]


def test_queryset_delete_is_a_single_bulk_statement(miniproject_env):
    _create_all()
    with session_scope():
        for c in list(Counter.objects.all()):
            c.delete()
        Counter(name="keep", value=1, threshold=0).save()
        Counter(name="drop", value=2, threshold=0).save()

        with _count_queries() as counter:
            deleted = Counter.objects.filter(name="drop").delete()
        assert deleted == 1
        assert counter["n"] == 1

    with session_scope():
        remaining = [c.name for c in Counter.objects.all()]
        assert remaining == ["keep"]


def test_get_or_create_creates_when_missing(miniproject_env):
    _create_all()
    with session_scope():
        for c in list(Counter.objects.all()):
            c.delete()
        obj, created = Counter.objects.get_or_create(
            name="unique-name", defaults={"value": 42}
        )
        assert created is True
        assert obj.value == 42
        assert Counter.objects.count() == 1


def test_get_or_create_returns_existing_when_found(miniproject_env):
    _create_all()
    with session_scope():
        for c in list(Counter.objects.all()):
            c.delete()
        Counter(name="existing", value=1).save()

        obj, created = Counter.objects.get_or_create(
            name="existing", defaults={"value": 999}
        )
        assert created is False
        assert obj.value == 1  # defaults ignored when found
        assert Counter.objects.count() == 1


def test_update_or_create_updates_when_found(miniproject_env):
    _create_all()
    with session_scope():
        for c in list(Counter.objects.all()):
            c.delete()
        Counter(name="existing", value=1).save()

        obj, created = Counter.objects.update_or_create(
            name="existing", defaults={"value": 50}
        )
        assert created is False
        assert obj.value == 50
        assert Counter.objects.count() == 1


def test_update_or_create_creates_when_missing(miniproject_env):
    _create_all()
    with session_scope():
        for c in list(Counter.objects.all()):
            c.delete()
        obj, created = Counter.objects.update_or_create(
            name="brand-new", defaults={"value": 7}
        )
        assert created is True
        assert obj.value == 7
        assert Counter.objects.count() == 1


def test_values_returns_dicts(miniproject_env):
    _create_all()
    with session_scope():
        for c in list(Counter.objects.all()):
            c.delete()
        Counter(name="a", value=1, threshold=10).save()
        Counter(name="b", value=2, threshold=20).save()

        rows = list(Counter.objects.order_by("name").values("name", "value"))
        assert rows == [
            {"name": "a", "value": 1},
            {"name": "b", "value": 2},
        ]


def test_values_with_no_fields_returns_all_columns(miniproject_env):
    _create_all()
    with session_scope():
        for c in list(Counter.objects.all()):
            c.delete()
        Counter(name="a", value=1, threshold=10).save()

        rows = list(Counter.objects.values())
        assert len(rows) == 1
        assert set(rows[0].keys()) == {"id", "name", "value", "threshold"}


def test_values_list_returns_tuples(miniproject_env):
    _create_all()
    with session_scope():
        for c in list(Counter.objects.all()):
            c.delete()
        Counter(name="a", value=1).save()
        Counter(name="b", value=2).save()

        rows = list(Counter.objects.order_by("name").values_list("name", "value"))
        assert rows == [("a", 1), ("b", 2)]


def test_values_list_flat_returns_scalars(miniproject_env):
    _create_all()
    with session_scope():
        for c in list(Counter.objects.all()):
            c.delete()
        Counter(name="a", value=1).save()
        Counter(name="b", value=2).save()

        names = list(Counter.objects.order_by("name").values_list("name", flat=True))
        assert names == ["a", "b"]


def test_values_list_flat_with_multiple_fields_raises():
    with pytest.raises(TypeError, match="flat=True"):
        Counter.objects.values_list("name", "value", flat=True)


def test_values_respects_filters(miniproject_env):
    _create_all()
    with session_scope():
        for c in list(Counter.objects.all()):
            c.delete()
        Counter(name="a", value=100).save()
        Counter(name="b", value=1).save()

        rows = list(Counter.objects.filter(value__gte=50).values_list("name", flat=True))
        assert rows == ["a"]


def test_only_loads_named_columns_eagerly(miniproject_env):
    _create_all()
    with session_scope():
        for c in list(Counter.objects.all()):
            c.delete()
        Counter(name="a", value=1, threshold=99).save()

    with session_scope():
        with _count_queries() as counter:
            c = Counter.objects.only("id", "name").first()
            _ = c.name  # already loaded -> no extra query
        assert counter["n"] == 1

        with _count_queries() as counter:
            _ = c.threshold  # deferred -> lazy loads now
        assert counter["n"] == 1


def test_defer_skips_named_columns_eagerly(miniproject_env):
    _create_all()
    with session_scope():
        for c in list(Counter.objects.all()):
            c.delete()
        Counter(name="a", value=1, threshold=99).save()

    with session_scope():
        with _count_queries() as counter:
            c = Counter.objects.defer("threshold").first()
            _ = c.name  # not deferred -> no extra query
        assert counter["n"] == 1

        with _count_queries() as counter:
            assert c.threshold == 99  # deferred -> lazy loads now, but is correct
        assert counter["n"] == 1


def test_atomic_commits_on_success(miniproject_env):
    from fastframe.models import atomic

    _create_all()
    with session_scope():
        for c in list(Counter.objects.all()):
            c.delete()
        with atomic():
            Counter(name="a", value=1).save()
            Counter(name="b", value=2).save()
        assert Counter.objects.count() == 2

    with session_scope():
        assert Counter.objects.count() == 2


def test_atomic_rolls_back_only_its_own_block_on_error(miniproject_env):
    from fastframe.models import atomic

    _create_all()
    with session_scope():
        for c in list(Counter.objects.all()):
            c.delete()
        Counter(name="outside", value=0).save()

        try:
            with atomic():
                Counter(name="doomed", value=1).save()
                raise RuntimeError("boom")
        except RuntimeError:
            pass

        # The atomic() block's insert was rolled back...
        names = {c.name for c in Counter.objects.all()}
        assert names == {"outside"}

        # ...but the outer session/transaction is still usable.
        Counter(name="after", value=2).save()
        assert {c.name for c in Counter.objects.all()} == {"outside", "after"}

    with session_scope():
        assert {c.name for c in Counter.objects.all()} == {"outside", "after"}


def test_atomic_is_importable_from_db_and_models(miniproject_env):
    from fastframe.db import atomic as atomic_from_db
    from fastframe.models import atomic as atomic_from_models

    assert atomic_from_db is atomic_from_models
