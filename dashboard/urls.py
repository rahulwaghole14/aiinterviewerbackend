from django.urls import path
from .views import (
    DashboardDataView,
    DashboardSummaryView,
    ResumeStatsView,
    InterviewStatsView,
    CandidateStatsView,
    JobStatsView,
    UserActivityListView,
    DashboardWidgetListView,
    DashboardWidgetDetailView,
    WidgetSettingsView,
    ChartDataView,
    ExportDashboardDataView,
)

urlpatterns = [
    # Main dashboard endpoints
    path("", DashboardDataView.as_view(), name="dashboard-data"),
    path("summary/", DashboardSummaryView.as_view(), name="dashboard-summary"),
    path("analytics/", DashboardDataView.as_view(), name="dashboard-analytics"),
    path(
        "recent-activities/", UserActivityListView.as_view(), name="recent-activities"
    ),
    # Individual statistics endpoints
    path("resume-stats/", ResumeStatsView.as_view(), name="resume-stats"),
    path("interview-stats/", InterviewStatsView.as_view(), name="interview-stats"),
    path("candidate-stats/", CandidateStatsView.as_view(), name="candidate-stats"),
    path("job-stats/", JobStatsView.as_view(), name="job-stats"),
    # Activity tracking
    path("activities/", UserActivityListView.as_view(), name="user-activities"),
    # Widget management
    path("widgets/", DashboardWidgetListView.as_view(), name="widget-list"),
    path(
        "widgets/<int:pk>/", DashboardWidgetDetailView.as_view(), name="widget-detail"
    ),
    path("widgets/settings/", WidgetSettingsView.as_view(), name="widget-settings"),
    # Chart data
    path("charts/<str:chart_type>/", ChartDataView.as_view(), name="chart-data"),
    # Data export
    path("export/", ExportDashboardDataView.as_view(), name="export-data"),
]
