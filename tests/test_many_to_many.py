"""Tests for ManyToManyField relationships."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from fastframe.models import Model, fields
from fastframe.models.fields import RelatedList


@pytest.fixture
def test_db():
    """Set up an in-memory database bound to the current session context."""
    engine = create_engine("sqlite:///:memory:")
    Model.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)

    import fastframe.db.session as session_module

    original_get = session_module.get_current_session

    session = Session()
    session_module._session_ctx.set(session)
    session_module.get_current_session = lambda: session

    yield session

    session_module.get_current_session = original_get
    session_module._session_ctx.set(None)
    Session.remove()


def test_m2m_creates_relationship_attribute():
    """ManyToManyField auto-creates a relationship attribute on both sides."""

    class M2MTag(Model):
        __tablename__ = "m2m_tags_basic"
        name = fields.CharField(max_length=50)

    class M2MPost(Model):
        __tablename__ = "m2m_posts_basic"
        title = fields.CharField(max_length=100)
        tags = fields.ManyToManyField("M2MTag", related_name="posts")

    assert hasattr(M2MPost, "tags")
    assert hasattr(M2MTag, "posts")
    assert "tags" in [r.key for r in M2MPost.__mapper__.relationships]
    assert "posts" in [r.key for r in M2MTag.__mapper__.relationships]


def test_m2m_join_table_created():
    """A hidden join table is auto-created with a predictable default name."""

    class M2MTagB(Model):
        __tablename__ = "m2m_tags_jointable"
        name = fields.CharField(max_length=50)

    class M2MPostB(Model):
        __tablename__ = "m2m_posts_jointable"
        title = fields.CharField(max_length=100)
        tags = fields.ManyToManyField("M2MTagB", related_name="posts")

    assert "m2m_posts_jointable_tags" in Model.metadata.tables


def test_m2m_custom_db_table():
    """db_table overrides the default join table name."""

    class M2MTagC(Model):
        __tablename__ = "m2m_tags_customtable"
        name = fields.CharField(max_length=50)

    class M2MPostC(Model):
        __tablename__ = "m2m_posts_customtable"
        title = fields.CharField(max_length=100)
        tags = fields.ManyToManyField("M2MTagC", related_name="posts", db_table="custom_post_tags")

    assert "custom_post_tags" in Model.metadata.tables
    assert "m2m_posts_customtable_tags" not in Model.metadata.tables


def test_m2m_add_and_query(test_db):
    """add() attaches related objects, visible from both sides."""

    class M2MTagD(Model):
        __tablename__ = "m2m_tags_add"
        name = fields.CharField(max_length=50)

    class M2MPostD(Model):
        __tablename__ = "m2m_posts_add"
        title = fields.CharField(max_length=100)
        tags = fields.ManyToManyField("M2MTagD", related_name="posts")

    Model.metadata.create_all(test_db.get_bind())

    tag1 = M2MTagD.objects.create(name="python")
    tag2 = M2MTagD.objects.create(name="web")
    post = M2MPostD.objects.create(title="Hello")

    post.tags.add(tag1, tag2)
    test_db.flush()

    assert isinstance(post.tags, RelatedList)
    assert {t.name for t in post.tags} == {"python", "web"}
    assert [p.title for p in tag1.posts] == ["Hello"]


def test_m2m_add_is_idempotent(test_db):
    """add() skips objects already present, avoiding duplicate join rows."""

    class M2MTagE(Model):
        __tablename__ = "m2m_tags_idempotent"
        name = fields.CharField(max_length=50)

    class M2MPostE(Model):
        __tablename__ = "m2m_posts_idempotent"
        title = fields.CharField(max_length=100)
        tags = fields.ManyToManyField("M2MTagE", related_name="posts")

    Model.metadata.create_all(test_db.get_bind())

    tag = M2MTagE.objects.create(name="python")
    post = M2MPostE.objects.create(title="Hello")

    post.tags.add(tag)
    post.tags.add(tag)  # duplicate add should be a no-op
    test_db.flush()

    assert len(post.tags) == 1


def test_m2m_remove(test_db):
    """remove() detaches a single related object."""

    class M2MTagF(Model):
        __tablename__ = "m2m_tags_remove"
        name = fields.CharField(max_length=50)

    class M2MPostF(Model):
        __tablename__ = "m2m_posts_remove"
        title = fields.CharField(max_length=100)
        tags = fields.ManyToManyField("M2MTagF", related_name="posts")

    Model.metadata.create_all(test_db.get_bind())

    tag1 = M2MTagF.objects.create(name="python")
    tag2 = M2MTagF.objects.create(name="web")
    post = M2MPostF.objects.create(title="Hello")
    post.tags.add(tag1, tag2)
    test_db.flush()

    post.tags.remove(tag1)
    test_db.flush()

    assert {t.name for t in post.tags} == {"web"}


def test_m2m_clear(test_db):
    """clear() detaches all related objects."""

    class M2MTagG(Model):
        __tablename__ = "m2m_tags_clear"
        name = fields.CharField(max_length=50)

    class M2MPostG(Model):
        __tablename__ = "m2m_posts_clear"
        title = fields.CharField(max_length=100)
        tags = fields.ManyToManyField("M2MTagG", related_name="posts")

    Model.metadata.create_all(test_db.get_bind())

    tag1 = M2MTagG.objects.create(name="python")
    tag2 = M2MTagG.objects.create(name="web")
    post = M2MPostG.objects.create(title="Hello")
    post.tags.add(tag1, tag2)
    test_db.flush()

    post.tags.clear()
    test_db.flush()

    assert list(post.tags) == []


def test_m2m_set_replaces_collection(test_db):
    """set() replaces the entire collection in one call."""

    class M2MTagH(Model):
        __tablename__ = "m2m_tags_set"
        name = fields.CharField(max_length=50)

    class M2MPostH(Model):
        __tablename__ = "m2m_posts_set"
        title = fields.CharField(max_length=100)
        tags = fields.ManyToManyField("M2MTagH", related_name="posts")

    Model.metadata.create_all(test_db.get_bind())

    tag1 = M2MTagH.objects.create(name="python")
    tag2 = M2MTagH.objects.create(name="web")
    tag3 = M2MTagH.objects.create(name="django")
    post = M2MPostH.objects.create(title="Hello")
    post.tags.add(tag1, tag2)
    test_db.flush()

    post.tags.set([tag3])
    test_db.flush()

    assert [t.name for t in post.tags] == ["django"]


def test_m2m_all_returns_plain_list(test_db):
    """all() returns a plain list snapshot."""

    class M2MTagI(Model):
        __tablename__ = "m2m_tags_all"
        name = fields.CharField(max_length=50)

    class M2MPostI(Model):
        __tablename__ = "m2m_posts_all"
        title = fields.CharField(max_length=100)
        tags = fields.ManyToManyField("M2MTagI", related_name="posts")

    Model.metadata.create_all(test_db.get_bind())

    tag = M2MTagI.objects.create(name="python")
    post = M2MPostI.objects.create(title="Hello")
    post.tags.add(tag)
    test_db.flush()

    snapshot = post.tags.all()
    assert isinstance(snapshot, list)
    assert [t.name for t in snapshot] == ["python"]


def test_m2m_deleting_one_side_does_not_delete_the_other(test_db):
    """Deleting a Post removes join rows but leaves the Tag intact."""

    class M2MTagJ(Model):
        __tablename__ = "m2m_tags_delete"
        name = fields.CharField(max_length=50)

    class M2MPostJ(Model):
        __tablename__ = "m2m_posts_delete"
        title = fields.CharField(max_length=100)
        tags = fields.ManyToManyField("M2MTagJ", related_name="posts")

    Model.metadata.create_all(test_db.get_bind())

    tag = M2MTagJ.objects.create(name="python")
    post = M2MPostJ.objects.create(title="Hello")
    post.tags.add(tag)
    test_db.flush()

    post.delete()
    test_db.flush()

    assert M2MTagJ.objects.filter(name="python").exists()
    assert M2MTagJ.objects.get(name="python").posts == []


def test_m2m_self_referential(test_db):
    """to='self' supports self-referential many-to-many (e.g. friends)."""

    class M2MPerson(Model):
        __tablename__ = "m2m_people_self"
        name = fields.CharField(max_length=50)
        friends = fields.ManyToManyField("self", related_name="friended_by")

    Model.metadata.create_all(test_db.get_bind())

    alice = M2MPerson.objects.create(name="Alice")
    bob = M2MPerson.objects.create(name="Bob")
    alice.friends.add(bob)
    test_db.flush()

    assert [p.name for p in alice.friends] == ["Bob"]
    assert [p.name for p in bob.friended_by] == ["Alice"]


def test_m2m_default_related_name(test_db):
    """Without related_name, the reverse accessor defaults to '<model>_set'."""

    class M2MSkill(Model):
        __tablename__ = "m2m_skills_default"
        name = fields.CharField(max_length=50)

    class M2MEmployee(Model):
        __tablename__ = "m2m_employees_default"
        name = fields.CharField(max_length=50)
        skills = fields.ManyToManyField("M2MSkill")

    Model.metadata.create_all(test_db.get_bind())

    skill = M2MSkill.objects.create(name="Python")
    employee = M2MEmployee.objects.create(name="Dana")
    employee.skills.add(skill)
    test_db.flush()

    assert hasattr(M2MSkill, "m2memployee_set")
    assert [e.name for e in skill.m2memployee_set] == ["Dana"]


def test_m2m_admin_schema_marks_field_as_many(test_db):
    """The admin schema flags ManyToManyField as a multi-reference field."""
    from fastframe.admin.serializers import model_schema

    class M2MTagL(Model):
        __tablename__ = "m2m_tags_schema"
        name = fields.CharField(max_length=50)

    class M2MPostL(Model):
        __tablename__ = "m2m_posts_schema"
        title = fields.CharField(max_length=100)
        tags = fields.ManyToManyField("M2MTagL", related_name="posts")

    schema = model_schema(M2MPostL)
    tags_field = next(f for f in schema["fields"] if f["name"] == "tags")
    assert tags_field["many"] is True
    assert tags_field["reference"] == "M2MTagL"
    assert tags_field["editable"] is False


def test_m2m_admin_serializes_as_pk_list(test_db):
    """serialize_instance() turns the M2M collection into a list of PKs."""
    from fastframe.admin.serializers import serialize_instance

    class M2MTagM(Model):
        __tablename__ = "m2m_tags_serialize"
        name = fields.CharField(max_length=50)

    class M2MPostM(Model):
        __tablename__ = "m2m_posts_serialize"
        title = fields.CharField(max_length=100)
        tags = fields.ManyToManyField("M2MTagM", related_name="posts")

    Model.metadata.create_all(test_db.get_bind())

    tag1 = M2MTagM.objects.create(name="python")
    tag2 = M2MTagM.objects.create(name="web")
    post = M2MPostM.objects.create(title="Hello")
    post.tags.add(tag1, tag2)
    test_db.flush()

    data = serialize_instance(post)
    assert sorted(data["tags"]) == sorted([tag1.id, tag2.id])


def test_m2m_admin_deserialize_ignores_field(test_db):
    """deserialize_payload() skips M2M keys (not settable via main payload yet)."""
    from fastframe.admin.serializers import deserialize_payload

    class M2MTagN(Model):
        __tablename__ = "m2m_tags_deserialize"
        name = fields.CharField(max_length=50)

    class M2MPostN(Model):
        __tablename__ = "m2m_posts_deserialize"
        title = fields.CharField(max_length=100)
        tags = fields.ManyToManyField("M2MTagN", related_name="posts")

    cleaned = deserialize_payload(M2MPostN, {"title": "Hello", "tags": [1, 2]})
    assert cleaned == {"title": "Hello"}


def test_m2m_full_clean_does_not_error_on_transient_instance():
    """full_clean() shouldn't choke on an unsaved instance's M2M collection."""

    class M2MTagK(Model):
        __tablename__ = "m2m_tags_fullclean"
        name = fields.CharField(max_length=50)

    class M2MPostK(Model):
        __tablename__ = "m2m_posts_fullclean"
        title = fields.CharField(max_length=100)
        tags = fields.ManyToManyField("M2MTagK", related_name="posts")

    post = M2MPostK(title="Draft")
    post.full_clean()  # should not raise
    assert list(post.tags) == []
