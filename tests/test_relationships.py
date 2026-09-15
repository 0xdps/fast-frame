from __future__ import annotations


def test_foreign_key_and_relationship(miniproject_env) -> None:
    """Verify FK constraints and SQLAlchemy relationships work correctly."""
    from posts.models import Post
    from users.models import User

    from fastframe.db.session import get_current_session, session_scope

    with session_scope():
        session = get_current_session()
        
        # Create a user
        user = User.objects.create(email="author@example.com", is_active=True)
        assert user.id is not None
        
        # Create posts using the manager
        post1 = Post.objects.create(
            title="First Post",
            content="Hello world",
            author_id=user.id
        )
        post2 = Post.objects.create(
            title="Second Post",
            content="More content",
            author_id=user.id
        )
        
        # Refresh to load relationships
        session.refresh(user)
        session.refresh(post1)
        
        # Test relationship navigation (SQLAlchemy escape hatch)
        assert len(user.posts) == 2
        assert post1.author.email == "author@example.com"
        assert post2.author.email == "author@example.com"
        
        # Test filtering posts by author using manager
        user_posts = Post.objects.filter(author_id=user.id)
        assert len(user_posts) == 2


def test_post_migration_created_fk(miniproject_env) -> None:
    """Verify the posts migration file was generated with FK constraint."""
    migrations_dir = miniproject_env / "users" / "migrations" / "versions"
    migration_files = list(migrations_dir.glob("*.py"))
    
    # Find migration with posts table
    posts_migration = None
    for mig_file in migration_files:
        content = mig_file.read_text()
        if "create_table('posts'" in content:
            posts_migration = content
            break
    
    assert posts_migration is not None, "Posts migration not found"
    assert "ForeignKeyConstraint" in posts_migration
    assert "author_id" in posts_migration
