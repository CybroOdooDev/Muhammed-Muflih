from django.urls import path

from .views import (
    GmailConnectView, GmailStatusView, GmailSyncView,
    WorkDayCountView, EmployeesListView,
    ProjectListCreateView, ProjectDetailView,
    MomSyncView, AIAnalyzeView,
)

urlpatterns = [
    path("connect/", GmailConnectView.as_view()),
    path("status/", GmailStatusView.as_view()),
    path("sync/", GmailSyncView.as_view()),
    path("mom/", MomSyncView.as_view()),
    path("workday-count/", WorkDayCountView.as_view()),
    path("employees/", EmployeesListView.as_view()),
    path("projects/", ProjectListCreateView.as_view()),
    path("projects/<int:pk>/", ProjectDetailView.as_view()),
    path("analyze/", AIAnalyzeView.as_view()),
]
