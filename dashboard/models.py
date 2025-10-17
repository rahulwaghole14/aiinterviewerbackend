from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Count, Avg, Sum, Q
from datetime import datetime, timedelta
import json

User = get_user_model()


class DashboardMetric(models.Model):
    """Model to store dashboard metrics and analytics data"""

    METRIC_TYPES = [
        ("resume_upload", "Resume Uploads"),
        ("interview_scheduled", "Interviews Scheduled"),
        ("interview_completed", "Interviews Completed"),
        ("candidate_added", "Candidates Added"),
        ("job_created", "Jobs Created"),
        ("evaluation_completed", "Evaluations Completed"),
        ("user_activity", "User Activity"),
        ("system_performance", "System Performance"),
    ]

    metric_type = models.CharField(max_length=50, choices=METRIC_TYPES)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    company_name = models.CharField(max_length=255, null=True, blank=True)
    value = models.IntegerField(default=0)
    data = models.JSONField(default=dict, help_text="Additional metric data")
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["metric_type", "user", "company_name", "date"]
        indexes = [
            models.Index(fields=["metric_type", "date"]),
            models.Index(fields=["user", "date"]),
            models.Index(fields=["company_name", "date"]),
        ]

    def __str__(self):
        return f"{self.get_metric_type_display()} - {self.date} ({self.value})"


class UserActivity(models.Model):
    """Model to track user activity for analytics"""

    ACTIVITY_TYPES = [
        ("login", "User Login"),
        ("logout", "User Logout"),
        ("resume_upload", "Resume Upload"),
        ("interview_schedule", "Interview Schedule"),
        ("candidate_add", "Candidate Addition"),
        ("job_create", "Job Creation"),
        ("evaluation_submit", "Evaluation Submit"),
        ("bulk_upload", "Bulk Upload"),
        ("search", "Search"),
        ("export", "Data Export"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    details = models.JSONField(default=dict, help_text="Activity details")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "activity_type", "created_at"]),
            models.Index(fields=["activity_type", "created_at"]),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.get_activity_type_display()} - {self.created_at}"


class DashboardWidget(models.Model):
    """Model to store user dashboard widget preferences"""

    WIDGET_TYPES = [
        ("resume_stats", "Resume Statistics"),
        ("interview_stats", "Interview Statistics"),
        ("candidate_stats", "Candidate Statistics"),
        ("job_stats", "Job Statistics"),
        ("activity_chart", "Activity Chart"),
        ("performance_metrics", "Performance Metrics"),
        ("recent_activity", "Recent Activity"),
        ("quick_actions", "Quick Actions"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    widget_type = models.CharField(max_length=50, choices=WIDGET_TYPES)
    position = models.IntegerField(default=0, help_text="Widget position on dashboard")
    is_enabled = models.BooleanField(default=True)
    settings = models.JSONField(default=dict, help_text="Widget-specific settings")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["user", "widget_type"]
        ordering = ["position"]

    def __str__(self):
        return f"{self.user.email} - {self.get_widget_type_display()}"


class SystemPerformance(models.Model):
    """Model to track system performance metrics"""

    metric_name = models.CharField(max_length=100)
    value = models.FloatField()
    unit = models.CharField(max_length=20, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, help_text="Additional performance data")

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["metric_name", "timestamp"]),
        ]

    def __str__(self):
        return f"{self.metric_name}: {self.value} {self.unit} - {self.timestamp}"


class DashboardAnalytics:
    """Utility class for dashboard analytics calculations"""

    @staticmethod
    def get_user_dashboard_data(user, days=30):
        """Get comprehensive dashboard data for a user"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)

        # Get user's role and company
        user_role = getattr(user, "role", "")
        company_name = getattr(user, "company_name", "")

        # Base queryset filters
        base_filters = {}
        if user_role == "COMPANY":
            base_filters["company_name"] = company_name
        elif user_role in ["HIRING_AGENCY", "RECRUITER"]:
            base_filters["user"] = user

        # Resume statistics
        from resumes.models import Resume

        resume_stats = DashboardAnalytics._get_resume_stats(
            user, start_date, end_date, base_filters
        )

        # Interview statistics
        from interviews.models import Interview

        interview_stats = DashboardAnalytics._get_interview_stats(
            user, start_date, end_date, base_filters
        )

        # Candidate statistics
        from candidates.models import Candidate

        candidate_stats = DashboardAnalytics._get_candidate_stats(
            user, start_date, end_date, base_filters
        )

        # Job statistics
        from jobs.models import Job

        job_stats = DashboardAnalytics._get_job_stats(
            user, start_date, end_date, base_filters
        )

        # Activity data
        activity_data = DashboardAnalytics._get_activity_data(
            user, start_date, end_date
        )

        # Performance metrics
        performance_data = DashboardAnalytics._get_performance_data(
            start_date, end_date
        )

        return {
            "resume_stats": resume_stats,
            "interview_stats": interview_stats,
            "candidate_stats": candidate_stats,
            "job_stats": job_stats,
            "activity_data": activity_data,
            "performance_data": performance_data,
            "date_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days,
            },
        }

    @staticmethod
    def _get_resume_stats(user, start_date, end_date, base_filters):
        """Get resume upload statistics"""
        from resumes.models import Resume

        queryset = Resume.objects.filter(
            uploaded_at__date__range=[start_date, end_date]
        )

        # Apply role-based filters
        if base_filters.get("user"):
            queryset = queryset.filter(user=user)
        elif base_filters.get("company_name"):
            # Resume doesn't have company_name, filter by user's company
            queryset = queryset.filter(user__company_name=base_filters["company_name"])

        total_uploads = queryset.count()
        successful_uploads = (
            queryset.count()
        )  # All uploaded resumes are considered successful
        failed_uploads = 0  # No status field, so no failed uploads

        # Daily upload trend
        daily_uploads = (
            queryset.extra(select={"date": "DATE(resumes_resume.uploaded_at)"})
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )

        return {
            "total_uploads": total_uploads,
            "successful_uploads": successful_uploads,
            "failed_uploads": failed_uploads,
            "success_rate": (
                (successful_uploads / total_uploads * 100) if total_uploads > 0 else 0
            ),
            "daily_trend": list(daily_uploads),
            "recent_uploads": list(
                queryset.order_by("-uploaded_at")[:5].values(
                    "id", "file", "uploaded_at"
                )
            ),
        }

    @staticmethod
    def _get_interview_stats(user, start_date, end_date, base_filters):
        """Get interview statistics"""
        from interviews.models import Interview

        queryset = Interview.objects.filter(
            created_at__date__range=[start_date, end_date]
        )

        # Apply role-based filters
        if base_filters.get("user"):
            queryset = queryset.filter(candidate__recruiter=user)
        elif base_filters.get("company_name"):
            queryset = queryset.filter(job__company_name=base_filters["company_name"])

        total_interviews = queryset.count()
        scheduled_interviews = queryset.filter(status="scheduled").count()
        completed_interviews = queryset.filter(status="completed").count()
        cancelled_interviews = queryset.filter(
            status="error"
        ).count()  # Using 'error' as cancelled

        # Daily interview trend
        daily_interviews = (
            queryset.extra(select={"date": "DATE(interviews_interview.created_at)"})
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )

        return {
            "total_interviews": total_interviews,
            "scheduled_interviews": scheduled_interviews,
            "completed_interviews": completed_interviews,
            "cancelled_interviews": cancelled_interviews,
            "completion_rate": (
                (completed_interviews / total_interviews * 100)
                if total_interviews > 0
                else 0
            ),
            "daily_trend": list(daily_interviews),
            "upcoming_interviews": list(
                queryset.filter(status="scheduled", started_at__gte=timezone.now())
                .order_by("started_at")[:5]
                .values("id", "candidate__full_name", "started_at", "status")
            ),
        }

    @staticmethod
    def _get_candidate_stats(user, start_date, end_date, base_filters):
        """Get candidate statistics"""
        from candidates.models import Candidate

        queryset = Candidate.objects.filter(
            created_at__date__range=[start_date, end_date]
        )

        # Apply role-based filters
        if base_filters.get("user"):
            queryset = queryset.filter(recruiter=user)
        elif base_filters.get("company_name"):
            # Candidate doesn't have company_name, filter by job's company
            queryset = queryset.filter(job__company_name=base_filters["company_name"])

        total_candidates = queryset.count()
        active_candidates = queryset.filter(status="NEW").count()
        interviewed_candidates = queryset.filter(status="INTERNAL_INTERVIEWS").count()
        hired_candidates = queryset.filter(status="HIRED").count()

        # Domain distribution
        domain_distribution = (
            queryset.values("domain")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        return {
            "total_candidates": total_candidates,
            "active_candidates": active_candidates,
            "interviewed_candidates": interviewed_candidates,
            "hired_candidates": hired_candidates,
            "hiring_rate": (
                (hired_candidates / total_candidates * 100)
                if total_candidates > 0
                else 0
            ),
            "domain_distribution": list(domain_distribution),
            "recent_candidates": list(
                queryset.order_by("-created_at")[:5].values(
                    "id", "full_name", "email", "domain", "status", "created_at"
                )
            ),
        }

    @staticmethod
    def _get_job_stats(user, start_date, end_date, base_filters):
        """Get job statistics"""
        from jobs.models import Job

        queryset = Job.objects.filter(created_at__date__range=[start_date, end_date])

        # Apply role-based filters
        if base_filters.get("user"):
            # Job doesn't have created_by field, so we can't filter by user
            # For now, return all jobs for the user's company
            queryset = queryset.filter(company_name=getattr(user, "company_name", ""))
        elif base_filters.get("company_name"):
            queryset = queryset.filter(company_name=base_filters["company_name"])

        total_jobs = queryset.count()
        active_jobs = total_jobs  # All jobs are considered active since there's no is_active field
        closed_jobs = 0  # No closed jobs since there's no is_active field

        # Position level distribution
        level_distribution = (
            queryset.values("position_level")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        return {
            "total_jobs": total_jobs,
            "active_jobs": active_jobs,
            "closed_jobs": closed_jobs,
            "level_distribution": list(level_distribution),
            "recent_jobs": list(
                queryset.order_by("-created_at")[:5].values(
                    "id", "job_title", "company_name", "position_level", "created_at"
                )
            ),
        }

    @staticmethod
    def _get_activity_data(user, start_date, end_date):
        """Get user activity data"""
        queryset = UserActivity.objects.filter(
            user=user, created_at__date__range=[start_date, end_date]
        )

        total_activities = queryset.count()

        # Activity type distribution
        activity_distribution = (
            queryset.values("activity_type")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        # Daily activity trend
        daily_activity = (
            queryset.extra(select={"date": "DATE(dashboard_useractivity.created_at)"})
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )

        return {
            "total_activities": total_activities,
            "activity_distribution": list(activity_distribution),
            "daily_trend": list(daily_activity),
            "recent_activities": list(
                queryset.order_by("-created_at")[:10].values(
                    "activity_type", "details", "created_at"
                )
            ),
        }

    @staticmethod
    def _get_performance_data(start_date, end_date):
        """Get system performance data"""
        queryset = SystemPerformance.objects.filter(
            timestamp__date__range=[start_date, end_date]
        )

        # Get latest performance metrics
        latest_metrics = {}
        for metric in queryset.values("metric_name").distinct():
            metric_name = metric["metric_name"]
            latest = (
                queryset.filter(metric_name=metric_name).order_by("-timestamp").first()
            )
            if latest:
                latest_metrics[metric_name] = {
                    "value": latest.value,
                    "unit": latest.unit,
                    "timestamp": latest.timestamp,
                }

        return {
            "latest_metrics": latest_metrics,
            "performance_trend": list(
                queryset.order_by("-timestamp")[:20].values(
                    "metric_name", "value", "unit", "timestamp"
                )
            ),
        }
