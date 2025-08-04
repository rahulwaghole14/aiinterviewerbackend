from django.urls import path
from .views import (
    NotificationListView,
    NotificationDetailView,
    MarkNotificationReadView,
    BulkMarkReadView,
    NotificationSummaryView,
    UserNotificationPreferenceView,
    CreateNotificationView,
    NotificationTemplateListView,
    UnreadNotificationsCountView
)

urlpatterns = [
    # Notification management
    path('', NotificationListView.as_view(), name='notification-list'),
    path('<int:pk>/', NotificationDetailView.as_view(), name='notification-detail'),
    path('mark-read/', MarkNotificationReadView.as_view(), name='mark-notification-read'),
    path('bulk-mark-read/', BulkMarkReadView.as_view(), name='bulk-mark-read'),
    path('summary/', NotificationSummaryView.as_view(), name='notification-summary'),
    path('unread-count/', UnreadNotificationsCountView.as_view(), name='unread-count'),
    
    # User preferences
    path('preferences/', UserNotificationPreferenceView.as_view(), name='notification-preferences'),
    
    # Admin only
    path('create/', CreateNotificationView.as_view(), name='create-notification'),
    path('templates/', NotificationTemplateListView.as_view(), name='notification-templates'),
] 