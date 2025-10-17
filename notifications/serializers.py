from rest_framework import serializers
from .models import (
    Notification,
    NotificationTemplate,
    UserNotificationPreference,
    NotificationType,
    NotificationChannel,
    NotificationPriority,
    NotificationStatus,
)


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model"""

    notification_type_display = serializers.CharField(
        source="get_notification_type_display", read_only=True
    )
    priority_display = serializers.CharField(
        source="get_priority_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    is_read = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "notification_type_display",
            "title",
            "message",
            "priority",
            "priority_display",
            "status",
            "status_display",
            "channels",
            "metadata",
            "created_at",
            "sent_at",
            "read_at",
            "is_read",
            "email_sent",
            "in_app_sent",
            "sms_sent",
        ]
        read_only_fields = [
            "id",
            "recipient",
            "notification_type",
            "title",
            "message",
            "priority",
            "status",
            "channels",
            "metadata",
            "created_at",
            "sent_at",
            "read_at",
            "email_sent",
            "in_app_sent",
            "sms_sent",
        ]

    def get_is_read(self, obj):
        """Check if notification is read"""
        return obj.status == NotificationStatus.READ


class NotificationListSerializer(serializers.ModelSerializer):
    """Simplified serializer for notification listing"""

    notification_type_display = serializers.CharField(
        source="get_notification_type_display", read_only=True
    )
    priority_display = serializers.CharField(
        source="get_priority_display", read_only=True
    )
    is_read = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "notification_type_display",
            "title",
            "priority",
            "priority_display",
            "created_at",
            "is_read",
        ]
        read_only_fields = fields

    def get_is_read(self, obj):
        """Check if notification is read"""
        return obj.status == NotificationStatus.READ


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """Serializer for NotificationTemplate model"""

    notification_type_display = serializers.CharField(
        source="get_notification_type_display", read_only=True
    )
    priority_display = serializers.CharField(
        source="get_priority_display", read_only=True
    )

    class Meta:
        model = NotificationTemplate
        fields = [
            "id",
            "name",
            "notification_type",
            "notification_type_display",
            "title_template",
            "message_template",
            "channels",
            "priority",
            "priority_display",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class UserNotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for UserNotificationPreference model"""

    class Meta:
        model = UserNotificationPreference
        fields = [
            "id",
            "email_enabled",
            "in_app_enabled",
            "sms_enabled",
            "interview_notifications",
            "resume_notifications",
            "system_notifications",
            "daily_digest",
            "weekly_summary",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class NotificationSummarySerializer(serializers.Serializer):
    """Serializer for notification summary statistics"""

    total_notifications = serializers.IntegerField()
    unread_count = serializers.IntegerField()
    read_count = serializers.IntegerField()
    failed_count = serializers.IntegerField()

    # Counts by type
    interview_notifications = serializers.IntegerField()
    resume_notifications = serializers.IntegerField()
    system_notifications = serializers.IntegerField()

    # Counts by priority
    urgent_count = serializers.IntegerField()
    high_count = serializers.IntegerField()
    medium_count = serializers.IntegerField()
    low_count = serializers.IntegerField()


class MarkNotificationReadSerializer(serializers.Serializer):
    """Serializer for marking notification as read"""

    notification_id = serializers.IntegerField()


class CreateNotificationSerializer(serializers.Serializer):
    """Serializer for creating custom notifications"""

    recipient_id = serializers.IntegerField()
    notification_type = serializers.ChoiceField(choices=NotificationType.choices)
    title = serializers.CharField(max_length=255)
    message = serializers.CharField()
    priority = serializers.ChoiceField(
        choices=NotificationPriority.choices, default=NotificationPriority.MEDIUM
    )
    channels = serializers.ListField(
        child=serializers.ChoiceField(choices=NotificationChannel.choices),
        required=False,
    )
    metadata = serializers.DictField(required=False)


class NotificationFilterSerializer(serializers.Serializer):
    """Serializer for filtering notifications"""

    notification_type = serializers.ChoiceField(
        choices=NotificationType.choices, required=False
    )
    priority = serializers.ChoiceField(
        choices=NotificationPriority.choices, required=False
    )
    status = serializers.ChoiceField(choices=NotificationStatus.choices, required=False)
    is_read = serializers.BooleanField(required=False)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    search = serializers.CharField(
        required=False, help_text="Search in title and message"
    )


class BulkMarkReadSerializer(serializers.Serializer):
    """Serializer for marking multiple notifications as read"""

    notification_ids = serializers.ListField(
        child=serializers.IntegerField(), min_length=1
    )
    mark_all = serializers.BooleanField(
        default=False, help_text="Mark all notifications as read"
    )


class NotificationChannelSerializer(serializers.Serializer):
    """Serializer for notification channels"""

    channel = serializers.ChoiceField(choices=NotificationChannel.choices)
    enabled = serializers.BooleanField()


class NotificationTypeSerializer(serializers.Serializer):
    """Serializer for notification types"""

    type = serializers.ChoiceField(choices=NotificationType.choices)
    enabled = serializers.BooleanField()
