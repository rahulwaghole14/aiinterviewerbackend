#!/usr/bin/env python3
"""
Simple test script for Dashboard & Analytics System
Creates test users and tests dashboard functionality
"""

import os
import django
from datetime import datetime, timedelta

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_platform.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from dashboard.models import (
    DashboardAnalytics,
    DashboardMetric,
    UserActivity,
    DashboardWidget,
    SystemPerformance,
)

User = get_user_model()


def log(message, level="INFO"):
    """Log messages with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")


def test_dashboard_system():
    """Test the dashboard system"""
    log("=" * 60)
    log("TESTING DASHBOARD & ANALYTICS SYSTEM")
    log("=" * 60)

    # Create test users
    log("Creating test users...")

    admin_user, created = User.objects.get_or_create(
        username="admin",
        defaults={
            "email": "admin@test.com",
            "role": "ADMIN",
            "is_staff": True,
            "is_superuser": True,
        },
    )
    if created:
        admin_user.set_password("admin123")
        admin_user.save()
        log("✓ Created admin user")
    else:
        log("✓ Admin user already exists")

    company_user, created = User.objects.get_or_create(
        username="company_user",
        defaults={
            "email": "company@test.com",
            "role": "COMPANY",
            "company_name": "Test Company",
        },
    )
    if created:
        company_user.set_password("company123")
        company_user.save()
        log("✓ Created company user")
    else:
        log("✓ Company user already exists")

    agency_user, created = User.objects.get_or_create(
        username="agency_user",
        defaults={"email": "agency@test.com", "role": "HIRING_AGENCY"},
    )
    if created:
        agency_user.set_password("agency123")
        agency_user.save()
        log("✓ Created hiring agency user")
    else:
        log("✓ Hiring agency user already exists")

    # Test dashboard models
    log("\nTesting Dashboard Models")
    log("-" * 40)

    # Create test metrics
    metric = DashboardMetric.objects.create(
        metric_type="resume_upload",
        value=100,
        user=admin_user,
        company_name="Test Company",
        data={"test": "data"},
    )
    log(f"✓ Created DashboardMetric: {metric}")

    activity = UserActivity.objects.create(
        user=admin_user, activity_type="login", details={"test": "data"}
    )
    log(f"✓ Created UserActivity: {activity}")

    widget = DashboardWidget.objects.create(
        user=admin_user,
        widget_type="resume_stats",
        position=1,
        settings={"test": "settings"},
    )
    log(f"✓ Created DashboardWidget: {widget}")

    perf = SystemPerformance.objects.create(
        metric_name="test_performance", value=95.5, unit="%"
    )
    log(f"✓ Created SystemPerformance: {perf}")

    # Test analytics
    log("\nTesting DashboardAnalytics")
    log("-" * 40)

    try:
        # Set up date range
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)

        # Test dashboard data for admin user
        dashboard_data = DashboardAnalytics.get_user_dashboard_data(admin_user)
        log(f"✓ Dashboard data keys: {list(dashboard_data.keys())}")

        # Test individual statistics methods
        resume_stats = DashboardAnalytics._get_resume_stats(
            admin_user, start_date, end_date, {}
        )
        log(f"✓ Resume statistics: {resume_stats}")

        interview_stats = DashboardAnalytics._get_interview_stats(
            admin_user, start_date, end_date, {}
        )
        log(f"✓ Interview statistics: {interview_stats}")

        candidate_stats = DashboardAnalytics._get_candidate_stats(
            admin_user, start_date, end_date, {}
        )
        log(f"✓ Candidate statistics: {candidate_stats}")

        job_stats = DashboardAnalytics._get_job_stats(
            admin_user, start_date, end_date, {}
        )
        log(f"✓ Job statistics: {job_stats}")

        activity_data = DashboardAnalytics._get_activity_data(
            admin_user, start_date, end_date
        )
        log(f"✓ User activity: {activity_data}")

        performance_data = DashboardAnalytics._get_performance_data(
            start_date, end_date
        )
        log(f"✓ System performance: {performance_data}")

    except Exception as e:
        log(f"✗ Error testing analytics: {str(e)}", "ERROR")

    # Test for different user roles
    log("\nTesting Analytics for Different User Roles")
    log("-" * 40)

    for user, role in [
        (admin_user, "ADMIN"),
        (company_user, "COMPANY"),
        (agency_user, "HIRING_AGENCY"),
    ]:
        try:
            dashboard_data = DashboardAnalytics.get_user_dashboard_data(user)
            log(f"✓ {role} user dashboard data: {len(dashboard_data)} keys")
        except Exception as e:
            log(f"✗ Error testing {role} user analytics: {str(e)}", "ERROR")

    # Clean up test data
    log("\nCleaning up test data...")
    metric.delete()
    activity.delete()
    widget.delete()
    perf.delete()

    log("\n" + "=" * 60)
    log("DASHBOARD & ANALYTICS SYSTEM TESTING COMPLETED")
    log("=" * 60)


if __name__ == "__main__":
    try:
        test_dashboard_system()
        log("\n🎉 All dashboard tests completed successfully!")
    except Exception as e:
        log(f"\n💥 Unexpected error: {str(e)}", "ERROR")
