from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta

from .models import (
    Notification,
    NotificationTemplate,
    UserNotificationPreference,
    NotificationType,
    NotificationStatus,
    NotificationPriority,
)
from .serializers import (
    NotificationSerializer,
    NotificationListSerializer,
    NotificationTemplateSerializer,
    UserNotificationPreferenceSerializer,
    NotificationSummarySerializer,
    MarkNotificationReadSerializer,
    CreateNotificationSerializer,
    NotificationFilterSerializer,
    BulkMarkReadSerializer,
)
from .services import NotificationService
from utils.logger import ActionLogger


class NotificationListView(generics.ListAPIView):
    """List user's notifications with filtering and search"""

    serializer_class = NotificationListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["notification_type", "priority", "status"]
    search_fields = ["title", "message"]
    ordering_fields = ["created_at", "priority"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Filter notifications for current user"""
        queryset = Notification.objects.filter(recipient=self.request.user)

        # Apply additional filters
        notification_type = self.request.query_params.get("notification_type")
        priority = self.request.query_params.get("priority")
        is_read = self.request.query_params.get("is_read")
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")

        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)

        if priority:
            queryset = queryset.filter(priority=priority)

        if is_read is not None:
            is_read_bool = is_read.lower() == "true"
            if is_read_bool:
                queryset = queryset.filter(status=NotificationStatus.READ)
            else:
                queryset = queryset.exclude(status=NotificationStatus.READ)

        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)

        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)

        return queryset

    def list(self, request, *args, **kwargs):
        """Log notification listing"""
        ActionLogger.log_user_action(
            user=request.user,
            action="notification_list",
            details={"count": self.get_queryset().count()},
            status="SUCCESS",
        )
        return super().list(request, *args, **kwargs)


class NotificationDetailView(generics.RetrieveAPIView):
    """Get detailed notification information"""

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        """Log notification retrieval and mark as read"""
        notification = self.get_object()

        # Mark as read if not already read
        if notification.status != NotificationStatus.READ:
            notification.mark_as_read()

        ActionLogger.log_user_action(
            user=request.user,
            action="notification_view",
            details={"notification_id": notification.id},
            status="SUCCESS",
        )

        return super().retrieve(request, *args, **kwargs)


class MarkNotificationReadView(APIView):
    """Mark a notification as read"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = MarkNotificationReadSerializer(data=request.data)
        if serializer.is_valid():
            notification_id = serializer.validated_data["notification_id"]

            success = NotificationService.mark_notification_as_read(
                notification_id, request.user
            )

            if success:
                return Response(
                    {"message": "Notification marked as read"},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"error": "Notification not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BulkMarkReadView(APIView):
    """Mark multiple notifications as read"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BulkMarkReadSerializer(data=request.data)
        if serializer.is_valid():
            mark_all = serializer.validated_data.get("mark_all", False)

            if mark_all:
                # Mark all unread notifications as read
                updated_count = Notification.objects.filter(
                    recipient=request.user,
                    status__in=[NotificationStatus.PENDING, NotificationStatus.SENT],
                ).update(status=NotificationStatus.READ, read_at=timezone.now())
            else:
                # Mark specific notifications as read
                notification_ids = serializer.validated_data["notification_ids"]
                updated_count = Notification.objects.filter(
                    recipient=request.user, id__in=notification_ids
                ).update(status=NotificationStatus.READ, read_at=timezone.now())

            ActionLogger.log_user_action(
                user=request.user,
                action="bulk_mark_notifications_read",
                details={"updated_count": updated_count, "mark_all": mark_all},
                status="SUCCESS",
            )

            return Response(
                {"message": f"{updated_count} notifications marked as read"},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NotificationSummaryView(APIView):
    """Get notification summary statistics"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        notifications = Notification.objects.filter(recipient=user)

        # Basic counts
        total_notifications = notifications.count()
        unread_count = notifications.filter(
            status__in=[NotificationStatus.PENDING, NotificationStatus.SENT]
        ).count()
        read_count = notifications.filter(status=NotificationStatus.READ).count()
        failed_count = notifications.filter(status=NotificationStatus.FAILED).count()

        # Counts by type
        interview_notifications = notifications.filter(
            notification_type__in=[
                NotificationType.INTERVIEW_SCHEDULED,
                NotificationType.INTERVIEW_REMINDER,
            ]
        ).count()

        resume_notifications = notifications.filter(
            notification_type__in=[
                NotificationType.RESUME_PROCESSED,
                NotificationType.BULK_UPLOAD_COMPLETED,
            ]
        ).count()

        system_notifications = notifications.filter(
            notification_type=NotificationType.SYSTEM_ALERT
        ).count()

        # Counts by priority
        urgent_count = notifications.filter(
            priority=NotificationPriority.URGENT
        ).count()
        high_count = notifications.filter(priority=NotificationPriority.HIGH).count()
        medium_count = notifications.filter(
            priority=NotificationPriority.MEDIUM
        ).count()
        low_count = notifications.filter(priority=NotificationPriority.LOW).count()

        summary = {
            "total_notifications": total_notifications,
            "unread_count": unread_count,
            "read_count": read_count,
            "failed_count": failed_count,
            "interview_notifications": interview_notifications,
            "resume_notifications": resume_notifications,
            "system_notifications": system_notifications,
            "urgent_count": urgent_count,
            "high_count": high_count,
            "medium_count": medium_count,
            "low_count": low_count,
        }

        ActionLogger.log_user_action(
            user=request.user,
            action="notification_summary",
            details=summary,
            status="SUCCESS",
        )

        return Response(summary)


class UserNotificationPreferenceView(generics.RetrieveUpdateAPIView):
    """Get and update user notification preferences"""

    serializer_class = UserNotificationPreferenceSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """Get or create user preferences"""
        preferences, created = UserNotificationPreference.objects.get_or_create(
            user=self.request.user,
            defaults={
                "email_enabled": True,
                "in_app_enabled": True,
                "sms_enabled": False,
                "interview_notifications": True,
                "resume_notifications": True,
                "system_notifications": True,
                "daily_digest": False,
                "weekly_summary": False,
            },
        )
        return preferences

    def update(self, request, *args, **kwargs):
        """Log preference update"""
        ActionLogger.log_user_action(
            user=request.user,
            action="notification_preferences_update",
            details=request.data,
            status="SUCCESS",
        )
        return super().update(request, *args, **kwargs)


class CreateNotificationView(APIView):
    """Create a custom notification (admin only)"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Check if user is admin
        if not (
            request.user.is_superuser
            or getattr(request.user, "role", "").lower() == "admin"
        ):
            return Response(
                {"error": "Only admins can create notifications"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CreateNotificationSerializer(data=request.data)
        if serializer.is_valid():
            from django.contrib.auth import get_user_model

            User = get_user_model()

            try:
                recipient = User.objects.get(
                    id=serializer.validated_data["recipient_id"]
                )

                notification = NotificationService.create_notification(
                    recipient=recipient,
                    notification_type=serializer.validated_data["notification_type"],
                    title=serializer.validated_data["title"],
                    message=serializer.validated_data["message"],
                    priority=serializer.validated_data.get(
                        "priority", NotificationPriority.MEDIUM
                    ),
                    channels=serializer.validated_data.get("channels"),
                    metadata=serializer.validated_data.get("metadata"),
                )

                if notification:
                    ActionLogger.log_user_action(
                        user=request.user,
                        action="custom_notification_created",
                        details={
                            "recipient_id": recipient.id,
                            "notification_id": notification.id,
                            "type": serializer.validated_data["notification_type"],
                        },
                        status="SUCCESS",
                    )

                    return Response(
                        {
                            "message": "Notification created and sent successfully",
                            "notification_id": notification.id,
                        },
                        status=status.HTTP_201_CREATED,
                    )
                else:
                    return Response(
                        {"error": "Failed to create notification"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

            except User.DoesNotExist:
                return Response(
                    {"error": "Recipient user not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NotificationTemplateListView(generics.ListAPIView):
    """List notification templates (admin only)"""

    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsAuthenticated]
    queryset = NotificationTemplate.objects.filter(is_active=True)

    def get_queryset(self):
        # Check if user is admin
        if not (
            self.request.user.is_superuser
            or getattr(self.request.user, "role", "").lower() == "admin"
        ):
            return NotificationTemplate.objects.none()

        return super().get_queryset()


class UnreadNotificationsCountView(APIView):
    """Get count of unread notifications"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = NotificationService.get_unread_notifications_count(request.user)
        return Response({"unread_count": count})
