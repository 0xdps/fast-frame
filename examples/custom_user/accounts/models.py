"""Custom user model selected with AUTH_USER_MODEL."""

from fastframe.contrib.auth.hashers import check_password, make_password
from fastframe.models import Model, fields


class CustomUser(Model):
    """Same login fields as the built-in user, plus a phone number."""

    username = fields.CharField(max_length=150, unique=True)
    email = fields.EmailField(unique=True)
    phone = fields.CharField(max_length=20, blank=True, default="")
    first_name = fields.CharField(max_length=150, blank=True, default="")
    last_name = fields.CharField(max_length=150, blank=True, default="")
    password = fields.CharField(max_length=255, write_only=True)
    is_active = fields.BooleanField(default=True)
    user_data = fields.JSONField(default=dict)
    date_joined = fields.DateTimeField(auto_now_add=True)
    last_login = fields.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "accounts_users"
        ordering = ["username"]
        verbose_name = "User"
        verbose_name_plural = "Users"
        app_label = "accounts"

    def set_password(self, raw_password: str) -> None:
        self.password = make_password(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password(raw_password, self.password)
