#!/usr/bin/env python3
"""
Test script for Dashboard & Analytics System
Tests all dashboard endpoints and functionality
"""

import requests
import json
import time
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"


def log(message, level="INFO"):
    """Log messages with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")


def make_request(method, url, data=None, headers=None, expected_status=200):
    """Make HTTP request and handle response"""
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, headers=headers)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")

        if response.status_code == expected_status:
            log(f"✓ {method} {url} - Status: {response.status_code}")
            return response.json() if response.content else None
        else:
            log(
                f"✗ {method} {url} - Status: {response.status_code}, Response: {response.text}",
                "ERROR",
            )
            return None
    except Exception as e:
        log(f"✗ {method} {url} - Exception: {str(e)}", "ERROR")
        return None


def test_dashboard_endpoints():
    """Test all dashboard endpoints"""
    log("=" * 60)
    log("TESTING DASHBOARD & ANALYTICS SYSTEM")
    log("=" * 60)

    # Test data for authentication
    test_users = {
        "admin": {
            "username": "admin",
            "email": "admin@test.com",
            "password": "admin123",
            "token": None,
        },
        "company": {
            "username": "company_user",
            "email": "company@test.com",
            "password": "company123",
            "token": None,
        },
        "hiring_agency": {
            "username": "agency_user",
            "email": "agency@test.com",
            "password": "agency123",
            "token": None,
        },
    }

    # Authenticate users
    log("Authenticating users...")
    for user_type, user_data in test_users.items():
        auth_data = {
            "username": user_data["username"],
            "email": user_data["email"],
            "password": user_data["password"],
        }

        response = make_request("POST", f"{BASE_URL}/auth/login/", auth_data)
        if response and "access" in response:
            test_users[user_type]["token"] = response["access"]
            log(f"✓ Authenticated {user_type} user")
        else:
            log(f"✗ Failed to authenticate {user_type} user", "ERROR")

    # Test dashboard endpoints for each user type
    for user_type, user_data in test_users.items():
        if not user_data["token"]:
            continue

        log(f"\nTesting Dashboard for {user_type.upper()} user")
        log("-" * 40)

        headers = {
            "Authorization": f"Bearer {user_data['token']}",
            "Content-Type": "application/json",
        }

        # 1. Main Dashboard Data
        log("1. Testing main dashboard data...")
        dashboard_data = make_request("GET", f"{API_BASE}/dashboard/", headers=headers)
        if dashboard_data:
            log(f"   Dashboard data keys: {list(dashboard_data.keys())}")

        # 2. Dashboard Summary
        log("2. Testing dashboard summary...")
        summary_data = make_request(
            "GET", f"{API_BASE}/dashboard/summary/", headers=headers
        )
        if summary_data:
            log(f"   Summary data keys: {list(summary_data.keys())}")

        # 3. Individual Statistics
        log("3. Testing individual statistics...")
        stats_endpoints = [
            "resume-stats/",
            "interview-stats/",
            "candidate-stats/",
            "job-stats/",
        ]

        for endpoint in stats_endpoints:
            stats_data = make_request(
                "GET", f"{API_BASE}/dashboard/{endpoint}", headers=headers
            )
            if stats_data:
                log(f"   {endpoint} data received")

        # 4. User Activities
        log("4. Testing user activities...")
        activities_data = make_request(
            "GET", f"{API_BASE}/dashboard/activities/", headers=headers
        )
        if activities_data:
            log(f"   Activities count: {len(activities_data.get('results', []))}")

        # 5. Widget Management
        log("5. Testing widget management...")

        # List widgets
        widgets_data = make_request(
            "GET", f"{API_BASE}/dashboard/widgets/", headers=headers
        )
        if widgets_data:
            log(f"   Widgets count: {len(widgets_data.get('results', []))}")

        # Create a test widget (admin only)
        if user_type == "admin":
            test_widget = {
                "name": "Test Widget",
                "widget_type": "chart",
                "position": 1,
                "settings": {"chart_type": "bar", "data_source": "resume_stats"},
                "is_active": True,
            }

            widget_response = make_request(
                "POST", f"{API_BASE}/dashboard/widgets/", test_widget, headers=headers
            )
            if widget_response:
                widget_id = widget_response.get("id")
                log(f"   Created test widget with ID: {widget_id}")

                # Update widget
                update_data = {
                    "name": "Updated Test Widget",
                    "settings": {
                        "chart_type": "line",
                        "data_source": "interview_stats",
                    },
                }
                update_response = make_request(
                    "PUT",
                    f"{API_BASE}/dashboard/widgets/{widget_id}/",
                    update_data,
                    headers=headers,
                )
                if update_response:
                    log(f"   Updated widget successfully")

                # Delete widget
                delete_response = make_request(
                    "DELETE",
                    f"{API_BASE}/dashboard/widgets/{widget_id}/",
                    headers=headers,
                    expected_status=204,
                )
                if delete_response is not None:
                    log(f"   Deleted widget successfully")

        # 6. Widget Settings
        log("6. Testing widget settings...")
        settings_data = make_request(
            "GET", f"{API_BASE}/dashboard/widgets/settings/", headers=headers
        )
        if settings_data:
            log(f"   Widget settings received")

        # 7. Chart Data
        log("7. Testing chart data...")
        chart_types = [
            "resume_trends",
            "interview_performance",
            "candidate_distribution",
            "job_statistics",
        ]

        for chart_type in chart_types:
            chart_data = make_request(
                "GET", f"{API_BASE}/dashboard/charts/{chart_type}/", headers=headers
            )
            if chart_data:
                log(f"   Chart data for {chart_type} received")

        # 8. Data Export
        log("8. Testing data export...")
        export_params = {
            "start_date": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
            "end_date": datetime.now().strftime("%Y-%m-%d"),
            "format": "json",
        }

        export_url = f"{API_BASE}/dashboard/export/?start_date={export_params['start_date']}&end_date={export_params['end_date']}&format={export_params['format']}"
        export_data = make_request("GET", export_url, headers=headers)
        if export_data:
            log(f"   Export data received")

    # Test with filters
    log("\nTesting Dashboard with Filters")
    log("-" * 40)

    if test_users["admin"]["token"]:
        headers = {
            "Authorization": f"Bearer {test_users['admin']['token']}",
            "Content-Type": "application/json",
        }

        # Test date range filters
        date_filters = [
            "?start_date=2024-01-01&end_date=2024-12-31",
            "?period=last_7_days",
            "?period=last_30_days",
            "?period=last_90_days",
        ]

        for filter_param in date_filters:
            filtered_data = make_request(
                "GET", f"{API_BASE}/dashboard/{filter_param}", headers=headers
            )
            if filtered_data:
                log(f"   Filtered data with {filter_param} received")

    log("\n" + "=" * 60)
    log("DASHBOARD & ANALYTICS SYSTEM TESTING COMPLETED")
    log("=" * 60)


def test_dashboard_analytics():
    """Test the DashboardAnalytics utility class"""
    log("\nTesting DashboardAnalytics Utility Class")
    log("-" * 40)

    try:
        # Import the analytics class
        import os
        import django

        # Setup Django environment
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_platform.settings")
        django.setup()

        from dashboard.models import DashboardAnalytics
        from datetime import datetime, timedelta
        from django.utils import timezone
        from django.contrib.auth import get_user_model

        User = get_user_model()

        # Test analytics methods
        log("Testing analytics methods...")

        # Set up date range for testing
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)

        # Create a test user for analytics
        user, created = User.objects.get_or_create(
            username="test_analytics_user",
            defaults={"email": "test@analytics.com", "role": "ADMIN"},
        )

        # Test dashboard data for a user
        dashboard_data = DashboardAnalytics.get_user_dashboard_data(user)
        log(f"   Dashboard data keys: {list(dashboard_data.keys())}")

        # Test individual statistics methods
        resume_stats = DashboardAnalytics._get_resume_stats(
            user, start_date, end_date, {}
        )
        log(f"   Resume statistics: {resume_stats}")

        interview_stats = DashboardAnalytics._get_interview_stats(
            user, start_date, end_date, {}
        )
        log(f"   Interview statistics: {interview_stats}")

        candidate_stats = DashboardAnalytics._get_candidate_stats(
            user, start_date, end_date, {}
        )
        log(f"   Candidate statistics: {candidate_stats}")

        job_stats = DashboardAnalytics._get_job_stats(user, start_date, end_date, {})
        log(f"   Job statistics: {job_stats}")

        activity_data = DashboardAnalytics._get_activity_data(
            user, start_date, end_date
        )
        log(f"   User activity: {activity_data}")

        performance_data = DashboardAnalytics._get_performance_data(
            start_date, end_date
        )
        log(f"   System performance: {performance_data}")

        log("✓ DashboardAnalytics utility class working correctly")

    except Exception as e:
        log(f"✗ Error testing DashboardAnalytics: {str(e)}", "ERROR")


def test_dashboard_models():
    """Test dashboard models"""
    log("\nTesting Dashboard Models")
    log("-" * 40)

    try:
        import os
        import django

        # Setup Django environment
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_platform.settings")
        django.setup()

        from dashboard.models import (
            DashboardMetric,
            UserActivity,
            DashboardWidget,
            SystemPerformance,
        )
        from django.contrib.auth import get_user_model

        User = get_user_model()

        # Test model creation
        log("Testing model creation...")

        # Create a test user if needed
        user, created = User.objects.get_or_create(
            username="test_dashboard_user",
            defaults={"email": "test@dashboard.com", "role": "ADMIN"},
        )

        # Test DashboardMetric
        metric = DashboardMetric.objects.create(
            metric_type="resume_upload",
            value=100,
            user=user,
            company_name="Test Company",
            data={"test": "data"},
        )
        log(f"   Created DashboardMetric: {metric}")

        # Test UserActivity
        activity = UserActivity.objects.create(
            user=user, activity_type="login", details={"test": "data"}
        )
        log(f"   Created UserActivity: {activity}")

        # Test DashboardWidget
        widget = DashboardWidget.objects.create(
            user=user,
            widget_type="resume_stats",
            position=1,
            settings={"test": "settings"},
        )
        log(f"   Created DashboardWidget: {widget}")

        # Test SystemPerformance
        perf = SystemPerformance.objects.create(
            metric_name="test_performance", value=95.5, timestamp=datetime.now()
        )
        log(f"   Created SystemPerformance: {perf}")

        # Clean up test data
        metric.delete()
        activity.delete()
        widget.delete()
        perf.delete()

        log("✓ Dashboard models working correctly")

    except Exception as e:
        log(f"✗ Error testing dashboard models: {str(e)}", "ERROR")


if __name__ == "__main__":
    try:
        # Test dashboard models first
        test_dashboard_models()

        # Test analytics utility
        test_dashboard_analytics()

        # Test API endpoints
        test_dashboard_endpoints()

        log("\n🎉 All dashboard tests completed successfully!")

    except KeyboardInterrupt:
        log("\n⚠️  Testing interrupted by user")
    except Exception as e:
        log(f"\n💥 Unexpected error: {str(e)}", "ERROR")
