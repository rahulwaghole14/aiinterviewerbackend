from django.contrib import admin
from .models import Interview


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "candidate",
        "job",
        "status",
        "interview_round",
        "started_at",
        "ended_at",
        "updated_at",
    )
    list_filter = ("status", "interview_round", "created_at")
    search_fields = ("candidate__full_name", "job__job_title", "interview_round")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "candidate",
                    "job",
                    "status",
                    "interview_round",
                    "feedback",
                    ("started_at", "ended_at"),
                    "video_url",
                )
            },
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
