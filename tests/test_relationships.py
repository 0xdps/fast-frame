"""Tests for ForeignKey relationships."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from fastframe.models import Model, fields


@pytest.fixture
def test_db():
    """Setup in-memory database for relationship testing."""
    engine = create_engine("sqlite:///:memory:")
    Model.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)

    # Patch get_current_session
    import fastframe.db.session as session_module

    original_get = session_module.get_current_session
    
    # Create a session and set it in the context
    session = Session()
    session_module._session_ctx.set(session)
    
    # Also patch the function
    session_module.get_current_session = lambda: session

    yield session

    session_module.get_current_session = original_get
    session_module._session_ctx.set(None)
    Session.remove()


def test_foreignkey_creates_relationship_attribute(test_db):
    """ForeignKey auto-creates relationship attribute."""

    class Author(Model):
        __tablename__ = "authors_rel"
        name = fields.CharField(max_length=100)

    class Book(Model):
        __tablename__ = "books_rel"
        title = fields.CharField(max_length=200)
        author_id = fields.ForeignKey("Author")

    # Check that relationship attribute exists
    assert hasattr(Book, "author")
    
    # Check that it's a relationship
    assert "author" in [r.key for r in Book.__mapper__.relationships]


def test_foreignkey_relationship_name_from_field():
    """ForeignKey creates relationship with correct name."""

    class User(Model):
        __tablename__ = "users_rel_name"
        name = fields.CharField(max_length=100)

    class Post(Model):
        __tablename__ = "posts_rel_name"
        title = fields.CharField(max_length=200)
        author_id = fields.ForeignKey("User")  # Creates 'author' relationship

    # author_id field → author relationship
    assert hasattr(Post, "author")
    assert hasattr(Post, "author_id")


def test_foreignkey_without_id_suffix():
    """ForeignKey without _id suffix gets _rel suffix."""

    class Category(Model):
        __tablename__ = "categories_suffix"
        name = fields.CharField(max_length=100)

    class Product(Model):
        __tablename__ = "products_suffix"
        name = fields.CharField(max_length=100)
        category = fields.ForeignKey("Category")  # No _id suffix

    # category field → category_rel relationship
    assert hasattr(Product, "category")  # The FK column
    assert hasattr(Product, "category_rel")  # The relationship


def test_foreignkey_traversal():
    """ForeignKey relationship attribute name is stored."""

    class Author4(Model):
        __tablename__ = "authors_traversal4"
        name = fields.CharField(max_length=100)

    class Book4(Model):
        __tablename__ = "books_traversal4"
        title = fields.CharField(max_length=200)
        author_id = fields.ForeignKey("Author4")

    # Check relationship attribute exists
    assert hasattr(Book4, "author")
    # Check it's a mapped relationship
    assert "author" in [r.key for r in Book4.__mapper__.relationships]


def test_foreignkey_lazy_loading():
    """ForeignKey lazy loading default is stored."""

    class Publisher2(Model):
        __tablename__ = "publishers_lazy2"
        name = fields.CharField(max_length=100)

    class Magazine2(Model):
        __tablename__ = "magazines_lazy2"
        title = fields.CharField(max_length=200)
        publisher_id = fields.ForeignKey("Publisher2")

    # Check relationship exists and lazy='select'
    rel = Magazine2.__mapper__.relationships["publisher"]
    assert str(rel.lazy) == "select"


def test_foreignkey_null_relationship():
    """ForeignKey with null=True is nullable."""

    class Reviewer2(Model):
        __tablename__ = "reviewers_null2"
        name = fields.CharField(max_length=100)

    class Review2(Model):
        __tablename__ = "reviews_null2"
        text = fields.TextField()
        reviewer_id = fields.ForeignKey("Reviewer2", null=True)

    # Check column is nullable
    assert Review2.__table__.c.reviewer_id.nullable is True


def test_foreignkey_cascade_delete():
    """ForeignKey with CASCADE has ondelete in constraint."""

    class Team2(Model):
        __tablename__ = "teams_cascade2"
        name = fields.CharField(max_length=100)

    class Member2(Model):
        __tablename__ = "members_cascade2"
        name = fields.CharField(max_length=100)
        team_id = fields.ForeignKey("Team2", on_delete="CASCADE")

    # Check FK constraint has CASCADE
    fks = list(Member2.__table__.foreign_keys)
    assert len(fks) > 0
    # The ondelete should be set
    for fk in fks:
        if "team_id" in str(fk.parent):
            assert fk.ondelete == "CASCADE"
            break
    else:
        pytest.fail("FK constraint not found")


def test_multiple_foreignkeys_same_model():
    """Model can have multiple FKs to same target."""

    class Person(Model):
        __tablename__ = "persons_multi"
        name = fields.CharField(max_length=100)

    class Transaction(Model):
        __tablename__ = "transactions_multi"
        amount = fields.DecimalField(max_digits=10, decimal_places=2)
        sender_id = fields.ForeignKey("Person")
        recipient_id = fields.ForeignKey("Person")

    # Should create sender and recipient relationships
    assert hasattr(Transaction, "sender")
    assert hasattr(Transaction, "recipient")


def test_self_referential_foreignkey():
    """ForeignKey can reference same model."""

    class Employee(Model):
        __tablename__ = "employees_self"
        name = fields.CharField(max_length=100)
        manager_id = fields.ForeignKey("Employee", null=True)

    # Should create manager relationship
    assert hasattr(Employee, "manager")


def test_foreignkey_related_name_stored():
    """ForeignKey stores related_name in metadata."""

    class Company(Model):
        __tablename__ = "companies_metadata"
        name = fields.CharField(max_length=100)

    class Employee(Model):
        __tablename__ = "employees_metadata"
        name = fields.CharField(max_length=100)
        company_id = fields.ForeignKey("Company", related_name="employees")

    field = Employee._meta["fields"]["company_id"]
    assert field.related_name == "employees"
