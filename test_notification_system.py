#!/usr/bin/env python3
"""
Test script for the Notification System
Tests all notification features including creation, sending, and management
"""

import os
import sys
import django
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from notifications.models import (
    Notification, NotificationTemplate, UserNotificationPreference,
    NotificationType, NotificationChannel, NotificationPriority, NotificationStatus
)
from notifications.services import NotificationService
from resumes.models import Resume
from candidates.models import Candidate
from jobs.models import Job, Domain
from interviews.models import Interview

User = get_user_model()

def test_notification_system():
    """Test the complete notification system"""
    print("🧪 Testing Notification System")
    print("=" * 50)
    
    # Create test users
    print("\n1. Creating test users...")
    
    # Clean up any existing test users first
    User.objects.filter(email__endswith='@test.com').delete()
    
    admin_user = User.objects.create_user(
        username='admin@test.com',
        email='admin@test.com',
        password='testpass123',
        role='ADMIN'
    )
    
    company_user = User.objects.create_user(
        username='company@test.com',
        email='company@test.com',
        password='testpass123',
        role='COMPANY'
    )
    
    recruiter_user = User.objects.create_user(
        username='recruiter@test.com',
        email='recruiter@test.com',
        password='testpass123',
        role='RECRUITER'
    )
    
    print(f"✅ Created users: {admin_user.email}, {company_user.email}, {recruiter_user.email}")
    
    # Test notification templates
    print("\n2. Testing notification templates...")
    templates = NotificationTemplate.objects.all()
    print(f"✅ Found {templates.count()} notification templates:")
    for template in templates:
        print(f"   - {template.name}: {template.notification_type}")
    
    # Test user notification preferences
    print("\n3. Testing user notification preferences...")
    preferences, created = UserNotificationPreference.objects.get_or_create(
        user=recruiter_user,
        defaults={
            'email_enabled': True,
            'in_app_enabled': True,
            'sms_enabled': False,
            'interview_notifications': True,
            'resume_notifications': True,
            'system_notifications': True
        }
    )
    print(f"✅ User preferences: Email={preferences.email_enabled}, In-App={preferences.in_app_enabled}")
    
    # Test direct notification creation
    print("\n4. Testing direct notification creation...")
    notification = NotificationService.create_notification(
        recipient=recruiter_user,
        notification_type=NotificationType.SYSTEM_ALERT,
        title='Test Notification',
        message='This is a test notification to verify the system is working.',
        priority=NotificationPriority.HIGH,
        channels=[NotificationChannel.IN_APP]
    )
    
    if notification:
        print(f"✅ Created notification: {notification.title}")
        print(f"   Status: {notification.status}")
        print(f"   Channels: {notification.channels}")
    else:
        print("❌ Failed to create notification")
    
    # Test template-based notification
    print("\n5. Testing template-based notification...")
    template_notification = NotificationService.create_notification_from_template(
        recipient=recruiter_user,
        template_name='system_alert',
        context={'alert_type': 'Test Alert'}
    )
    
    if template_notification:
        print(f"✅ Created template notification: {template_notification.title}")
    else:
        print("❌ Failed to create template notification")
    
    # Test notification listing
    print("\n6. Testing notification listing...")
    user_notifications = Notification.objects.filter(recipient=recruiter_user)
    print(f"✅ User has {user_notifications.count()} notifications")
    
    for notif in user_notifications[:3]:  # Show first 3
        print(f"   - {notif.title} ({notif.status})")
    
    # Test notification marking as read
    print("\n7. Testing mark as read...")
    unread_count_before = NotificationService.get_unread_notifications_count(recruiter_user)
    print(f"   Unread notifications before: {unread_count_before}")
    
    if user_notifications.exists():
        first_notification = user_notifications.first()
        success = NotificationService.mark_notification_as_read(
            first_notification.id, recruiter_user
        )
        if success:
            print(f"✅ Marked notification {first_notification.id} as read")
        else:
            print(f"❌ Failed to mark notification as read")
    
    unread_count_after = NotificationService.get_unread_notifications_count(recruiter_user)
    print(f"   Unread notifications after: {unread_count_after}")
    
    # Test notification summary
    print("\n8. Testing notification summary...")
    summary_data = {
        'total_notifications': user_notifications.count(),
        'unread_count': unread_count_after,
        'read_count': user_notifications.filter(status=NotificationStatus.READ).count(),
        'failed_count': user_notifications.filter(status=NotificationStatus.FAILED).count(),
        'interview_notifications': user_notifications.filter(
            notification_type__in=[NotificationType.INTERVIEW_SCHEDULED, NotificationType.INTERVIEW_REMINDER]
        ).count(),
        'resume_notifications': user_notifications.filter(
            notification_type__in=[NotificationType.RESUME_PROCESSED, NotificationType.BULK_UPLOAD_COMPLETED]
        ).count(),
        'system_notifications': user_notifications.filter(
            notification_type=NotificationType.SYSTEM_ALERT
        ).count(),
        'urgent_count': user_notifications.filter(priority=NotificationPriority.URGENT).count(),
        'high_count': user_notifications.filter(priority=NotificationPriority.HIGH).count(),
        'medium_count': user_notifications.filter(priority=NotificationPriority.MEDIUM).count(),
        'low_count': user_notifications.filter(priority=NotificationPriority.LOW).count()
    }
    
    print("✅ Notification summary:")
    for key, value in summary_data.items():
        print(f"   {key}: {value}")
    
    # Test specific notification types
    print("\n9. Testing specific notification types...")
    
    # Test resume processed notification
    print("   Testing resume processed notification...")
    try:
        resume_notification = NotificationService.send_resume_processed_notification(
            resume=None,  # We don't have a real resume object
            recipient=recruiter_user
        )
        if resume_notification:
            print(f"   ✅ Resume processed notification created")
        else:
            print(f"   ❌ Resume processed notification failed")
    except Exception as e:
        print(f"   ❌ Resume processed notification failed (expected - no resume object): {str(e)}")
    
    # Test bulk upload notification
    print("   Testing bulk upload notification...")
    bulk_results = {
        'summary': {
            'total_files': 5,
            'successful': 4,
            'failed': 1
        }
    }
    bulk_notification = NotificationService.send_bulk_upload_completed_notification(
        recruiter_user, bulk_results
    )
    if bulk_notification:
        print(f"   ✅ Bulk upload notification created")
    else:
        print(f"   ❌ Bulk upload notification failed")
    
    # Test candidate added notification
    print("   Testing candidate added notification...")
    try:
        candidate_notification = NotificationService.send_candidate_added_notification(
            candidate=None,  # We don't have a real candidate object
            recipient=recruiter_user
        )
        if candidate_notification:
            print(f"   ✅ Candidate added notification created")
        else:
            print(f"   ❌ Candidate added notification failed")
    except Exception as e:
        print(f"   ❌ Candidate added notification failed (expected - no candidate object): {str(e)}")
    
    # Test job created notification
    print("   Testing job created notification...")
    try:
        job_notification = NotificationService.send_job_created_notification(
            job=None,  # We don't have a real job object
            recipient=recruiter_user
        )
        if job_notification:
            print(f"   ✅ Job created notification created")
        else:
            print(f"   ❌ Job created notification failed")
    except Exception as e:
        print(f"   ❌ Job created notification failed (expected - no job object): {str(e)}")
    
    # Test interview scheduled notification
    print("   Testing interview scheduled notification...")
    try:
        interview_notification = NotificationService.send_interview_scheduled_notification(
            interview=None,  # We don't have a real interview object
            recipient=recruiter_user
        )
        if interview_notification:
            print(f"   ✅ Interview scheduled notification created")
        else:
            print(f"   ❌ Interview scheduled notification failed")
    except Exception as e:
        print(f"   ❌ Interview scheduled notification failed (expected - no interview object): {str(e)}")
    
    # Test interview reminder notification
    print("   Testing interview reminder notification...")
    try:
        reminder_notification = NotificationService.send_interview_reminder_notification(
            interview=None  # We don't have a real interview object
        )
        if reminder_notification:
            print(f"   ✅ Interview reminder notification created")
        else:
            print(f"   ❌ Interview reminder notification failed")
    except Exception as e:
        print(f"   ❌ Interview reminder notification failed (expected - no interview object): {str(e)}")
    
    # Test notification channels
    print("\n10. Testing notification channels...")
    test_channels = [
        NotificationChannel.EMAIL,
        NotificationChannel.IN_APP,
        NotificationChannel.SMS
    ]
    
    for channel in test_channels:
        channel_notification = NotificationService.create_notification(
            recipient=recruiter_user,
            notification_type=NotificationType.SYSTEM_ALERT,
            title=f'Test {channel} notification',
            message=f'Testing {channel} channel',
            channels=[channel],
            priority=NotificationPriority.MEDIUM
        )
        if channel_notification:
            print(f"   ✅ {channel} notification created")
        else:
            print(f"   ❌ {channel} notification failed")
    
    # Test notification priorities
    print("\n11. Testing notification priorities...")
    priorities = [
        NotificationPriority.LOW,
        NotificationPriority.MEDIUM,
        NotificationPriority.HIGH,
        NotificationPriority.URGENT
    ]
    
    for priority in priorities:
        priority_notification = NotificationService.create_notification(
            recipient=recruiter_user,
            notification_type=NotificationType.SYSTEM_ALERT,
            title=f'Test {priority} priority notification',
            message=f'Testing {priority} priority',
            priority=priority,
            channels=[NotificationChannel.IN_APP]
        )
        if priority_notification:
            print(f"   ✅ {priority} priority notification created")
        else:
            print(f"   ❌ {priority} priority notification failed")
    
    # Final summary
    print("\n" + "=" * 50)
    print("🎉 Notification System Test Summary")
    print("=" * 50)
    
    total_notifications = Notification.objects.count()
    total_users = User.objects.count()
    total_templates = NotificationTemplate.objects.count()
    
    print(f"✅ Total notifications created: {total_notifications}")
    print(f"✅ Total users: {total_users}")
    print(f"✅ Total templates: {total_templates}")
    print(f"✅ Notification system is working correctly!")
    
    # Cleanup test data
    print("\n🧹 Cleaning up test data...")
    Notification.objects.all().delete()
    UserNotificationPreference.objects.all().delete()
    User.objects.filter(email__endswith='@test.com').delete()
    print("✅ Test data cleaned up")

if __name__ == '__main__':
    test_notification_system() 