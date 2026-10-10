from __future__ import annotations


def test_queryset_order_by_ascending(miniproject_env) -> None:
    """Test ordering results in ascending order."""
    from users.models import User

    from fastframe.db.session import session_scope

    with session_scope():
        User.objects.create(email="charlie@example.com", is_active=True)
        User.objects.create(email="alice@example.com", is_active=True)
        User.objects.create(email="bob@example.com", is_active=True)

        users = User.objects.order_by("email")
        emails = [u.email for u in users]
        assert emails == ["alice@example.com", "bob@example.com", "charlie@example.com"]


def test_queryset_order_by_descending(miniproject_env) -> None:
    """Test ordering results in descending order with '-' prefix."""
    from users.models import User

    from fastframe.db.session import session_scope

    with session_scope():
        User.objects.create(email="alice@example.com", is_active=True)
        User.objects.create(email="charlie@example.com", is_active=True)
        User.objects.create(email="bob@example.com", is_active=True)

        users = User.objects.order_by("-email")
        emails = [u.email for u in users]
        assert emails == ["charlie@example.com", "bob@example.com", "alice@example.com"]


def test_queryset_order_by_multiple_fields(miniproject_env) -> None:
    """Test ordering by multiple fields."""
    from users.models import User

    from fastframe.db.session import session_scope

    with session_scope():
        User.objects.create(email="alice@example.com", is_active=False)
        User.objects.create(email="bob@example.com", is_active=True)
        User.objects.create(email="charlie@example.com", is_active=False)
        User.objects.create(email="dave@example.com", is_active=True)

        # Order by is_active descending, then email ascending
        users = User.objects.order_by("-is_active", "email")
        results = [(u.is_active, u.email) for u in users]
        assert results == [
            (True, "bob@example.com"),
            (True, "dave@example.com"),
            (False, "alice@example.com"),
            (False, "charlie@example.com"),
        ]


def test_queryset_limit(miniproject_env) -> None:
    """Test limiting query results."""
    from users.models import User

    from fastframe.db.session import session_scope

    with session_scope():
        for i in range(10):
            User.objects.create(email=f"user{i}@example.com", is_active=True)

        users = User.objects.order_by("email").limit(3)
        assert len(users) == 3
        assert users[0].email == "user0@example.com"
        assert users[2].email == "user2@example.com"


def test_queryset_offset(miniproject_env) -> None:
    """Test offsetting query results."""
    from users.models import User

    from fastframe.db.session import session_scope

    with session_scope():
        for i in range(10):
            User.objects.create(email=f"user{i}@example.com", is_active=True)

        users = User.objects.order_by("email").offset(5)
        assert len(users) == 5
        assert users[0].email == "user5@example.com"


def test_queryset_limit_and_offset(miniproject_env) -> None:
    """Test combining limit and offset for pagination."""
    from users.models import User

    from fastframe.db.session import session_scope

    with session_scope():
        for i in range(20):
            User.objects.create(email=f"user{i:02d}@example.com", is_active=True)

        # Page 2: skip 10, take 5
        page2 = User.objects.order_by("email").offset(10).limit(5)
        assert len(page2) == 5
        assert page2[0].email == "user10@example.com"
        assert page2[4].email == "user14@example.com"


def test_queryset_chaining(miniproject_env) -> None:
    """Test chaining filter, order_by, limit together."""
    from users.models import User

    from fastframe.db.session import session_scope

    with session_scope():
        User.objects.create(email="active1@example.com", is_active=True)
        User.objects.create(email="inactive1@example.com", is_active=False)
        User.objects.create(email="active2@example.com", is_active=True)
        User.objects.create(email="active3@example.com", is_active=True)
        User.objects.create(email="inactive2@example.com", is_active=False)

        # Get top 2 active users by email
        users = User.objects.filter(is_active=True).order_by("email").limit(2)
        assert len(users) == 2
        assert users[0].email == "active1@example.com"
        assert users[1].email == "active2@example.com"


def test_queryset_exclude(miniproject_env) -> None:
    """Test excluding objects with exclude()."""
    from users.models import User

    from fastframe.db.session import session_scope

    with session_scope():
        User.objects.create(email="active@example.com", is_active=True)
        User.objects.create(email="inactive1@example.com", is_active=False)
        User.objects.create(email="inactive2@example.com", is_active=False)

        inactive_users = User.objects.exclude(is_active=True)
        assert len(inactive_users) == 2
        emails = [u.email for u in inactive_users]
        assert "active@example.com" not in emails


def test_queryset_exclude_accepts_lookups(miniproject_env) -> None:
    """exclude() mirrors filter(): field__lookup kwargs work, not just equality."""
    from users.models import User

    from fastframe.db.session import session_scope

    with session_scope():
        User.objects.create(email="active@example.com", is_active=True)
        User.objects.create(email="inactive1@example.com", is_active=False)
        User.objects.create(email="inactive2@example.com", is_active=False)

        remaining = User.objects.exclude(email__icontains="inactive1")
        emails = {u.email for u in remaining}
        assert emails == {"active@example.com", "inactive2@example.com"}


def test_queryset_exclude_multiple_conditions_are_anded_then_negated(miniproject_env) -> None:
    """exclude(a=1, b=2) drops rows matching a=1 AND b=2, not a=1 OR b=2."""
    from users.models import User

    from fastframe.db.session import session_scope

    with session_scope():
        User.objects.create(email="active@example.com", is_active=True)
        User.objects.create(email="inactive1@example.com", is_active=False)
        User.objects.create(email="inactive2@example.com", is_active=False)

        # Only the row matching BOTH conditions is dropped.
        remaining = User.objects.exclude(is_active=True, email="active@example.com")
        emails = {u.email for u in remaining}
        assert emails == {"inactive1@example.com", "inactive2@example.com"}

        # Chaining two .exclude() calls negates each condition independently.
        remaining_chained = User.objects.exclude(is_active=True).exclude(email="inactive1@example.com")
        chained_emails = {u.email for u in remaining_chained}
        assert chained_emails == {"inactive2@example.com"}


def test_queryset_exclude_accepts_q_objects(miniproject_env) -> None:
    """exclude() accepts Q() objects, same as filter()."""
    from users.models import User

    from fastframe.db.session import session_scope
    from fastframe.models import Q

    with session_scope():
        User.objects.create(email="active@example.com", is_active=True)
        User.objects.create(email="inactive1@example.com", is_active=False)
        User.objects.create(email="inactive2@example.com", is_active=False)

        remaining = User.objects.exclude(Q(is_active=True) | Q(email__icontains="inactive1"))
        emails = {u.email for u in remaining}
        assert emails == {"inactive2@example.com"}


def test_queryset_filter_through_relationship(miniproject_env) -> None:
    """.filter() walks a relationship path, e.g. post__author__email."""
    from posts.models import Post
    from users.models import User

    from fastframe.db.session import session_scope

    with session_scope():
        alice = User.objects.create(email="alice@example.com", is_active=True)
        bob = User.objects.create(email="bob@example.com", is_active=True)
        Post.objects.create(title="Alice's post", content="...", author_id=alice.id)
        Post.objects.create(title="Bob's post", content="...", author_id=bob.id)

        matches = Post.objects.filter(author__email__icontains="alice")
        titles = [p.title for p in matches]
        assert titles == ["Alice's post"]

        # Reverse FK (one-to-many): find users who authored a given post.
        authors = User.objects.filter(posts__title="Bob's post")
        emails = [u.email for u in authors]
        assert emails == ["bob@example.com"]


def test_queryset_exists(miniproject_env) -> None:
    """Test exists() method."""
    from users.models import User

    from fastframe.db.session import session_scope

    with session_scope():
        assert not User.objects.exists()
        assert not User.objects.filter(email="test@example.com").exists()

        User.objects.create(email="test@example.com", is_active=True)

        assert User.objects.exists()
        assert User.objects.filter(email="test@example.com").exists()
        assert not User.objects.filter(email="notfound@example.com").exists()


def test_queryset_list_like_behavior(miniproject_env) -> None:
    """Test that QuerySet acts like a list for backward compatibility."""
    from users.models import User

    from fastframe.db.session import session_scope

    with session_scope():
        User.objects.create(email="a@example.com", is_active=True)
        User.objects.create(email="b@example.com", is_active=True)
        User.objects.create(email="c@example.com", is_active=True)

        users = User.objects.filter(is_active=True)

        # Test iteration
        count = 0
        for _user in users:
            count += 1
        assert count == 3

        # Test length
        assert len(users) == 3

        # Test indexing
        assert users[0].email == "a@example.com"
        assert users[-1].email == "c@example.com"

        # Test slicing
        assert len(users[0:2]) == 2


def test_queryset_filter_chaining(miniproject_env) -> None:
    """Test that filter can be chained multiple times."""
    from users.models import User

    from fastframe.db.session import session_scope

    with session_scope():
        User.objects.create(email="alice@example.com", is_active=True)
        User.objects.create(email="bob@gmail.com", is_active=True)
        User.objects.create(email="charlie@example.com", is_active=False)

        # Chain filters
        users = User.objects.filter(is_active=True).filter(email="alice@example.com")
        assert len(users) == 1
        assert users[0].email == "alice@example.com"


def test_queryset_lazy_evaluation(miniproject_env) -> None:
    """Test that QuerySet doesn't execute until needed."""
    from users.models import User

    from fastframe.db.session import session_scope

    with session_scope():
        User.objects.create(email="test@example.com", is_active=True)

        # Creating the queryset shouldn't execute a query yet
        qs = User.objects.filter(is_active=True).order_by("email").limit(10)

        # Only when we iterate or call len() should it execute
        result = list(qs)
        assert len(result) == 1
