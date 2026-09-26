# ORM features

FastFrame's ORM stays a **thin layer over SQLAlchemy** — models are
SQLAlchemy declarative classes, `Model.objects` is a small, chainable
manager, and nothing here is a query-algebra replacement for SQLAlchemy
itself. The goal of this page's features is narrower and more concrete:
cover the day-to-day 90% of CRUD-app workflows (filtering, pagination,
avoiding N+1, bulk writes, atomic increments) well enough that most code
never needs to drop to raw SQLAlchemy — without adding real query
composition.

**Deliberately not here, and not planned:** `annotate()`, subquery
expression composition, and window functions. If you need those, use
SQLAlchemy directly — `Model.metadata`, `Model.__table__`, and a plain
SQLAlchemy `Session` (`fastframe.db.session.get_current_session()`) are
always available; see [design-principles.md](design-principles.md).

## Field lookups

`.filter()`/`.exclude()` accept Django-style `field__lookup=value` kwargs:

```python
Post.objects.filter(views__gte=100)
Post.objects.filter(title__icontains="fastapi")
Post.objects.filter(author_id__in=[1, 2, 3])
Post.objects.filter(deleted_at__isnull=True)
```

| Lookup | Meaning |
| --- | --- |
| `exact` (default, or no `__`) | `field == value` |
| `iexact` | Case-insensitive exact match |
| `contains` | `field.contains(value)` |
| `icontains` | Case-insensitive substring match |
| `gt`, `gte`, `lt`, `lte` | Comparisons |
| `in` | `field.in_(value)` — `value` is any iterable |
| `isnull` | `field IS NULL` (`True`) / `IS NOT NULL` (`False`) |
| `startswith`, `istartswith` | Prefix match (case-sensitive / insensitive) |
| `endswith`, `iendswith` | Suffix match (case-sensitive / insensitive) |

Plain equality (`.filter(status="published")`) also works without `__`.

## Q objects — AND / OR / NOT composition

`Q()` composes boolean conditions beyond what keyword-argument AND'ing
can express:

```python
from fastframe.models import Q

# (published=True AND featured=True) OR author="alice"
Post.objects.filter(Q(published=True, featured=True) | Q(author="alice"))

# NOT published
Post.objects.filter(~Q(published=True))
```

`Q(**kwargs)` conditions support the same field lookups as `.filter()`
(`Q(views__gte=100)`). `&`, `|`, and `~` combine and negate `Q` objects;
multiple `Q`/keyword conditions passed to the same `.filter()` call are
AND'ed together, same as Django.

## F objects — reference another field's current value

`F()` refers to a column's value *in the database*, for two things: comparing two columns in a filter, and atomic updates.

### Comparing two columns

```python
from fastframe.models import F

# Rows where karma is greater than num_posts, computed in SQL —
# not fetched into Python and compared there.
User.objects.filter(karma__gt=F("num_posts"))
```

### Atomic increments (`save()`)

```python
user = User.objects.get(id=1)
user.karma = F("karma") + 1
user.save()
```

This issues a single `UPDATE users SET karma = karma + 1 WHERE id = 1` —
not a read-modify-write — so it's safe under concurrent writers (two
requests incrementing at once both apply, instead of one silently
clobbering the other). `+`, `-`, `*`, and `/` are supported and can be
mixed with plain numbers. The instance is refreshed from the database
afterward, so `user.karma` reflects the real, post-update value.

Only F-valued attributes are included in that statement — save any other
plain attribute changes on the same instance separately (before or after
setting the `F()` value).

### Atomic increments (queryset-level, many rows at once)

```python
Post.objects.filter(author_id=1).update(views=F("views") + 1)
```

See [`QuerySet.update()`](#bulk-update-and-delete) below — same
atomicity, applied to every matching row in one statement instead of one.

## Avoiding N+1: `select_related()` / `prefetch_related()`

The classic ORM trap: fetching a list of objects, then accessing a
relationship on each one in a loop, issuing one extra query *per row*.

```python
# N+1: one query for the posts, then one more per post for .author
for post in Post.objects.all():
    print(post.author.name)
```

`select_related()` (forward, one-to-one/ForeignKey relationships) joins
the related table into a single query:

```python
# One query total (a JOIN)
for post in Post.objects.select_related("author"):
    print(post.author.name)
```

`prefetch_related()` (reverse-FK / many-to-many relationships, where a
JOIN would duplicate rows) issues one extra query, batched with
`WHERE fk IN (...)`, instead of one per row:

```python
# Two queries total: one for authors, one batched query for all their posts
for author in Author.objects.prefetch_related("posts"):
    print([p.title for p in author.posts])
```

Both support Django-style `__` nesting for relationships of
relationships: `.select_related("author__profile")`,
`.prefetch_related("posts__tags")`.

Use `select_related` for "each row has exactly one related object"
(ForeignKey, one-to-one); use `prefetch_related` for "each row can have
many" (reverse FK, ManyToMany) — using `select_related` on a
many-relationship would multiply rows via the JOIN.

## Bulk create and update

```python
# One (or a few, if batch_size is set) round-trip instead of N .save() calls
Post.objects.bulk_create([Post(title=f"Post {i}") for i in range(1000)])

# Update specific fields on many existing objects
posts = list(Post.objects.filter(author_id=1))
for p in posts:
    p.views += 1
Post.objects.bulk_update(posts, fields=["views"])
```

`bulk_create(objects, batch_size=None)` inserts every object via
SQLAlchemy's own multi-row INSERT batching and populates auto-generated
primary keys back onto each object. `bulk_update(objects, fields,
batch_size=None)` writes only the named fields for objects that already
have a primary key, via one batched UPDATE per chunk — any *other*
in-memory attribute you've changed on those same objects is discarded
(not silently persisted later) rather than accidentally slipping in; call
`.save()` separately for those.

`batch_size` splits either call into chunks — bounds memory / a single
statement's parameter count for very large lists.

## Bulk update and delete (queryset-level)

For updating/deleting *every row matching a filter*, without loading
objects into Python at all:

```python
Post.objects.filter(author_id=1).update(published=True)
Post.objects.filter(status="draft", created_at__lt=cutoff).delete()
```

Both return the number of matched rows, execute as a single SQL
statement, and bypass per-instance hooks — there's no `.save()`/`.delete()`
call per row. Use a loop calling `.save()`/`.delete()` instead if you
need per-instance behavior (e.g. an override, or an `ondelete=` behavior
modeled only at the ORM level).

## `get_or_create()` / `update_or_create()`

```python
user, created = User.objects.get_or_create(
    username="alice", defaults={"email": "alice@example.com"}
)

setting, created = Setting.objects.update_or_create(
    key="theme", defaults={"value": "dark"}
)
```

`get_or_create(defaults=None, **kwargs)` looks up an object matching
`kwargs`; if missing, creates one from `kwargs` + `defaults`. Returns
`(object, created)`. `update_or_create` is the same, except an existing
match gets `defaults` applied and saved. Neither is race-safe under
concurrent writers without a matching unique constraint — a row inserted
concurrently between the lookup and the create can still raise an
`IntegrityError`; catch that and retry `.get()` if you need to handle it.

## `values()` / `values_list()` — skip full model instantiation

For read-only projections where you don't need (or want the cost of)
full model instances:

```python
Post.objects.values("id", "title")
# -> [{"id": 1, "title": "..."}, {"id": 2, "title": "..."}, ...]

Post.objects.values_list("id", "title")
# -> [(1, "..."), (2, "..."), ...]

Post.objects.values_list("id", flat=True)
# -> [1, 2, 3, ...]
```

Both keep whatever `.filter()`/`.order_by()` was already applied. No
fields given returns every column. `flat=True` requires exactly one
field, and returns bare scalars instead of one-tuples.

## `only()` / `defer()` — partial column loading

For full model instances where you want to skip loading a couple of
large or rarely-needed columns:

```python
# Only id/title loaded up front; other columns lazy-load on first access
Post.objects.only("id", "title")

# Every column except body loaded up front; body lazy-loads on first access
Post.objects.defer("body")
```

Unlike `values()`/`values_list()`, these still return real model
instances with the normal API — deferred columns just cost one extra
query the first time they're actually touched.

## `atomic()` — group operations into one all-or-nothing unit

```python
from fastframe.models import atomic

with atomic():
    account_a.balance = F("balance") - amount
    account_a.save()
    account_b.balance = F("balance") + amount
    account_b.save()
```

Wraps a SAVEPOINT around the *current* session (the same one your
request/shell/`session_scope()` is already using). If the block raises,
everything written inside it is rolled back and the exception propagates
— the outer session/transaction is untouched and can keep going. Safe to
nest; also importable from `fastframe.db`.

## Escape hatch: raw SQLAlchemy

Every model is a real SQLAlchemy declarative class, and the current
session is always reachable:

```python
from sqlalchemy import select, func
from fastframe.db.session import get_current_session

session = get_current_session()
stmt = select(Post.author_id, func.count()).group_by(Post.author_id)
rows = session.execute(stmt).all()
```

Reach for this for anything genuinely query-algebra-shaped (aggregation
with `GROUP BY`, subqueries, window functions, CTEs) — that's
SQLAlchemy's job, not this ORM's.
