from django.contrib import admin
from .models import Domain, Job


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "is_active", "created_at", "updated_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "description")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("name",)

    fieldsets = (
        (None, {"fields": ("name", "description", "is_active")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        "job_title",
        "company_name",
        "domain",
        "position_level",
        "number_to_hire",
        "created_at",
    )
    list_filter = ("domain", "position_level", "created_at")
    search_fields = ("job_title", "company_name", "tech_stack_details")
    readonly_fields = ("created_at",)

    fieldsets = (
        (None, {"fields": ("job_title", "company_name", "domain", "position_level")}),
        ("Contact Information", {"fields": ("spoc_email", "hiring_manager_email")}),
        (
            "Job Details",
            {
                "fields": (
                    "current_team_size_info",
                    "number_to_hire",
                    "current_process",
                    "tech_stack_details",
                )
            },
        ),
        ("Documents", {"fields": ("jd_file", "jd_link"), "classes": ("collapse",)}),
        ("Timestamps", {"fields": ("created_at",), "classes": ("collapse",)}),
    )
