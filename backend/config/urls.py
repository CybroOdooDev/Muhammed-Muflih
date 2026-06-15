from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/gmail/", include("apps.gmail_sync.urls")),
    path("api/odoo/", include("apps.odoo_sync.urls")),
]
