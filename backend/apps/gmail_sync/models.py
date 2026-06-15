from django.conf import settings
from django.db import models


class Project(models.Model):
    """A named project with a list of associated employee email addresses."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="projects",
    )
    name   = models.CharField(max_length=255)
    emails = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        unique_together = [["user", "name"]]

    def __str__(self):
        return self.name


class GmailCredential(models.Model):
    """Stores the OAuth tokens for one user's connected Gmail inbox."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="gmail_credential",
    )
    gmail_email = models.EmailField()
    access_token = models.TextField()
    refresh_token = models.TextField()
    token_expiry = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} → {self.gmail_email}"
