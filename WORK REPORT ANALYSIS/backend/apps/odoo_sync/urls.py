from django.urls import path

from .views import OdooConnectView, OdooDailyTaskView, OdooEmployees2View, OdooInspectView, OdooScrumView, OdooStatusView, OdooTimesheet2View, OdooTimesheetView

urlpatterns = [
    path("status/",       OdooStatusView.as_view()),
    path("connect/",      OdooConnectView.as_view()),
    path("scrum/",        OdooScrumView.as_view()),
    path("daily-tasks/",  OdooDailyTaskView.as_view()),
    path("timesheet/",    OdooTimesheetView.as_view()),
    path("timesheet-entries/", OdooTimesheet2View.as_view()),
    path("employees/",         OdooEmployees2View.as_view()),
    path("inspect/",      OdooInspectView.as_view()),
]
