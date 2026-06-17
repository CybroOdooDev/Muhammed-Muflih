from django.conf import settings
from django.db import models


class OdooCredential(models.Model):
    user    = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="odoo_credentials",
    )
    name    = models.CharField(max_length=100, default='Default')
    url     = models.CharField(max_length=255)
    db      = models.CharField(max_length=255)
    login   = models.CharField(max_length=255)
    api_key = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.user} → {self.url}"
