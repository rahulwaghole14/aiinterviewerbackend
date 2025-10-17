from django.contrib import admin
from .models import DashboardMetric, UserActivity, DashboardWidget, SystemPerformance


@admin.register(DashboardMetric)
class DashboardMetricAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "metric_type",
        "user",
        "company_name",
        "value",
        "date",
        "created_at",
    ]
    list_filter = ["metric_type", "date", "created_at"]
    search_fields = ["user__email", "company_name", "metric_type"]
    readonly_fields = ["created_at"]
    ordering = ["-created_at"]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("metric_type", "user", "company_name", "value", "date")},
        ),
        ("Additional Data", {"fields": ("data",), "classes": ("collapse",)}),
        ("Timestamps", {"fields": ("created_at",), "classes": ("collapse",)}),
    )


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "activity_type", "ip_address", "created_at"]
    list_filter = ["activity_type", "created_at"]
    search_fields = ["user__email", "activity_type", "details"]
    readonly_fields = ["created_at"]
    ordering = ["-created_at"]

    fieldsets = (
        ("Activity Information", {"fields": ("user", "activity_type", "details")}),
        (
            "Technical Details",
            {"fields": ("ip_address", "user_agent"), "classes": ("collapse",)},
        ),
        ("Timestamps", {"fields": ("created_at",), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")


@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "widget_type",
        "position",
        "is_enabled",
        "created_at",
        "updated_at",
    ]
    list_filter = ["widget_type", "is_enabled", "created_at"]
    search_fields = ["user__email", "widget_type"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["user", "position"]

    fieldsets = (
        (
            "Widget Information",
            {"fields": ("user", "widget_type", "position", "is_enabled")},
        ),
        ("Settings", {"fields": ("settings",), "classes": ("collapse",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")


@admin.register(SystemPerformance)
class SystemPerformanceAdmin(admin.ModelAdmin):
    list_display = ["id", "metric_name", "value", "unit", "timestamp"]
    list_filter = ["metric_name", "timestamp"]
    search_fields = ["metric_name"]
    readonly_fields = ["timestamp"]
    ordering = ["-timestamp"]

    fieldsets = (
        ("Performance Data", {"fields": ("metric_name", "value", "unit")}),
        ("Additional Information", {"fields": ("metadata",), "classes": ("collapse",)}),
        ("Timestamps", {"fields": ("timestamp",), "classes": ("collapse",)}),
    )
