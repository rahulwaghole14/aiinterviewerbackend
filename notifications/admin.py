from django.contrib import admin
from .models import Notification, NotificationTemplate, UserNotificationPreference

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'recipient', 'notification_type', 'title', 'priority', 
        'status', 'created_at', 'is_read_display'
    ]
    list_filter = [
        'notification_type', 'priority', 'status', 'created_at',
        'email_sent', 'in_app_sent', 'sms_sent'
    ]
    search_fields = ['recipient__email', 'title', 'message']
    readonly_fields = ['created_at', 'sent_at', 'read_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('recipient', 'notification_type', 'title', 'message')
        }),
        ('Delivery Settings', {
            'fields': ('priority', 'channels', 'status')
        }),
        ('Delivery Tracking', {
            'fields': ('email_sent', 'in_app_sent', 'sms_sent'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'sent_at', 'read_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        })
    )
    
    def is_read_display(self, obj):
        """Display if notification is read"""
        return obj.status == 'read'
    is_read_display.boolean = True
    is_read_display.short_description = 'Read'

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'notification_type', 'priority', 'is_active', 
        'created_at', 'updated_at'
    ]
    list_filter = ['notification_type', 'priority', 'is_active', 'created_at']
    search_fields = ['name', 'title_template', 'message_template']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']
    
    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'notification_type', 'is_active')
        }),
        ('Content', {
            'fields': ('title_template', 'message_template')
        }),
        ('Settings', {
            'fields': ('priority', 'channels')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(UserNotificationPreference)
class UserNotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'email_enabled', 'in_app_enabled', 'sms_enabled',
        'interview_notifications', 'resume_notifications', 'system_notifications'
    ]
    list_filter = [
        'email_enabled', 'in_app_enabled', 'sms_enabled',
        'interview_notifications', 'resume_notifications', 'system_notifications',
        'daily_digest', 'weekly_summary'
    ]
    search_fields = ['user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Channel Preferences', {
            'fields': ('email_enabled', 'in_app_enabled', 'sms_enabled')
        }),
        ('Type Preferences', {
            'fields': ('interview_notifications', 'resume_notifications', 'system_notifications')
        }),
        ('Frequency Preferences', {
            'fields': ('daily_digest', 'weekly_summary')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    ) 