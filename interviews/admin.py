from django.contrib import admin
from .models import Interview, InterviewSlot, InterviewSchedule, InterviewConflict, AIInterviewConfiguration


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


@admin.register(InterviewSlot)
class InterviewSlotAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "slot_type",
        "status",
        "start_time",
        "end_time",
        "ai_interview_type",
        "company",
        "job",
        "max_candidates",
        "current_bookings",
        "is_available",
    )
    list_filter = ("status", "slot_type", "ai_interview_type", "company", "created_at")
    search_fields = ("company__name", "job__job_title", "notes")
    readonly_fields = ("created_at", "updated_at", "is_available")
    fieldsets = (
        (
            "Slot Details",
            {
                "fields": (
                    "slot_type",
                    "status",
                    ("start_time", "end_time"),
                    "duration_minutes",
                    "ai_interview_type",
                    "ai_configuration",
                )
            },
        ),
        (
            "Context",
            {
                "fields": (
                    "company",
                    "job",
                    "notes",
                )
            },
        ),
        (
            "Capacity",
            {
                "fields": (
                    "max_candidates",
                    "current_bookings",
                )
            },
        ),
        (
            "Recurring",
            {
                "fields": (
                    "is_recurring",
                    "recurring_pattern",
                )
            },
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    def is_available(self, obj):
        return obj.is_available()
    is_available.boolean = True
    is_available.short_description = "Available"


@admin.register(InterviewSchedule)
class InterviewScheduleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "interview",
        "slot",
        "status",
        "booked_at",
        "confirmed_at",
    )
    list_filter = ("status", "booked_at", "confirmed_at")
    search_fields = ("interview__candidate__full_name", "slot__ai_interview_type")
    readonly_fields = ("booked_at",)


@admin.register(InterviewConflict)
class InterviewConflictAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "conflict_type",
        "resolution",
        "primary_interview",
        "detected_at",
        "resolved_at",
    )
    list_filter = ("conflict_type", "resolution", "detected_at")
    search_fields = ("primary_interview__candidate__full_name", "resolution_notes")


@admin.register(AIInterviewConfiguration)
class AIInterviewConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "company",
        "interview_type",
        "day_of_week",
        "start_time",
        "end_time",
        "valid_from",
    )
    list_filter = ("interview_type", "day_of_week", "company")
    search_fields = ("company__name", "interview_type")
