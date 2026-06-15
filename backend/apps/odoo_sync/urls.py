from django.urls import path

from .views import OdooConnectView, OdooDailyTaskView, OdooInspectView, OdooScrumView, OdooStatusView

urlpatterns = [
    path("status/",       OdooStatusView.as_view()),
    path("connect/",      OdooConnectView.as_view()),
    path("scrum/",        OdooScrumView.as_view()),
    path("daily-tasks/",  OdooDailyTaskView.as_view()),
    path("inspect/",      OdooInspectView.as_view()),
]
