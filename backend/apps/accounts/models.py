from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager


class User(AbstractUser):
    """Custom user. Authenticated via Google OAuth; email is the identifier.

    An account is auto-created on first Google login (see the auth view).
    Admins are flagged with role=ADMIN (or Django's is_staff).
    """

    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        EMPLOYEE = "employee", "Employee"

    username = None  # drop the username field; we log in with email
    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.EMPLOYEE
    )
    google_sub = models.CharField(
        max_length=255, blank=True, null=True, unique=True,
        help_text="Google account subject id (stable per Google account)",
    )
    picture = models.URLField(blank=True, default="")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN or self.is_staff
