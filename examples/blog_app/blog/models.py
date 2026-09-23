"""Blog models - Category, Post, Tag, Comment."""

from fastframe.models import Model, fields


class Category(Model):
    """Blog category."""

    name = fields.CharField(max_length=100, unique=True)
    slug = fields.CharField(max_length=100, unique=True)
    description = fields.TextField(blank=True, default="")
    post_count = fields.IntegerField(default=0)

    class Meta:
        db_table = "categories"
        ordering = ["name"]
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        app_label = "blog"


class Post(Model):
    """Blog post."""

    title = fields.CharField(max_length=200)
    slug = fields.CharField(max_length=200, unique=True)
    content = fields.TextField()
    summary = fields.CharField(max_length=500, blank=True, default="")

    status = fields.CharField(
        max_length=20,
        default="draft",
        choices=[
            ("draft", "Draft"),
            ("published", "Published"),
            ("archived", "Archived"),
        ],
    )

    is_featured = fields.BooleanField(default=False)
    view_count = fields.IntegerField(default=0)
    like_count = fields.IntegerField(default=0)
    
    # Relationships
    author_id = fields.ForeignKey("SimpleUser", on_delete="CASCADE", related_name="posts")
    category_id = fields.ForeignKey("Category", on_delete="SET NULL", null=True, related_name="posts")

    class Meta:
        db_table = "posts"
        ordering = ["-id"]
        verbose_name = "Post"
        verbose_name_plural = "Posts"
        app_label = "blog"


class Tag(Model):
    """Content tag."""

    name = fields.CharField(max_length=50, unique=True)
    slug = fields.CharField(max_length=50, unique=True)
    usage_count = fields.IntegerField(default=0)

    class Meta:
        db_table = "tags"
        ordering = ["name"]
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        app_label = "blog"


class Comment(Model):
    """Comment on a post."""

    author_name = fields.CharField(max_length=100)
    author_email = fields.EmailField()
    content = fields.TextField()
    is_approved = fields.BooleanField(default=False)
    like_count = fields.IntegerField(default=0)
    
    # Relationships
    post_id = fields.ForeignKey("Post", on_delete="CASCADE", related_name="comments")

    class Meta:
        db_table = "comments"
        ordering = ["-id"]
        verbose_name = "Comment"
        verbose_name_plural = "Comments"
        app_label = "blog"
