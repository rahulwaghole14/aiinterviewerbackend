#!/usr/bin/env python3
"""
Working test script for Bulk Resume Upload API
Creates test user and tests uploading multiple resume files
"""

import os
import django
from datetime import datetime

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_platform.settings")
django.setup()

import requests
import json
from django.contrib.auth import get_user_model

User = get_user_model()

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"


def log(message, level="INFO"):
    """Log messages with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")


def create_test_user():
    """Create a test user for authentication"""
    try:
        user, created = User.objects.get_or_create(
            username="test_bulk_user",
            defaults={
                "email": "test_bulk@example.com",
                "role": "HIRING_AGENCY",
                "is_staff": True,
                "is_active": True,
            },
        )
        if created:
            user.set_password("test123")
            user.save()
            log("✓ Created test user: test_bulk_user")
        else:
            # Update password to ensure we know it
            user.set_password("test123")
            user.save()
            log("✓ Updated test user password: test_bulk_user")
        return user
    except Exception as e:
        log(f"✗ Error creating test user: {str(e)}", "ERROR")
        return None


def create_test_files():
    """Create test PDF files for upload"""
    test_files = []

    # Create test PDF content (simplified)
    test_resumes = [
        {
            "name": "john_doe_resume.pdf",
            "content": """
            JOHN DOE
            Software Engineer
            Email: john.doe@email.com
            Phone: +1-555-123-4567
            
            EXPERIENCE:
            Senior Developer at Tech Corp - 5 years
            Python, Django, React
            """,
        },
        {
            "name": "jane_smith_resume.pdf",
            "content": """
            JANE SMITH
            Data Scientist
            Email: jane.smith@email.com
            Phone: +1-555-987-6543
            
            EXPERIENCE:
            Data Analyst at Analytics Inc - 3 years
            Python, SQL, Machine Learning
            """,
        },
        {
            "name": "mike_wilson_resume.pdf",
            "content": """
            MIKE WILSON
            Frontend Developer
            Email: mike.wilson@email.com
            Phone: +1-555-456-7890
            
            EXPERIENCE:
            UI Developer at Web Solutions - 4 years
            JavaScript, React, Vue.js
            """,
        },
    ]

    # Create test files directory
    test_dir = "test_files"
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)

    for resume in test_resumes:
        file_path = os.path.join(test_dir, resume["name"])
        with open(file_path, "w") as f:
            f.write(resume["content"])
        test_files.append(file_path)
        log(f"Created test file: {file_path}")

    return test_files


def test_bulk_resume_upload():
    """Test bulk resume upload API with authentication"""
    log("=" * 60)
    log("TESTING BULK RESUME UPLOAD API WITH WORKING AUTHENTICATION")
    log("=" * 60)

    # Create test user
    log("Creating test user...")
    user = create_test_user()
    if not user:
        log("Failed to create test user. Exiting.", "ERROR")
        return

    # Create test files
    log("Creating test files...")
    test_files = create_test_files()

    # Authenticate user
    log("Authenticating user...")
    auth_data = {"email": "test_bulk@example.com", "password": "test123"}

    auth_response = requests.post(f"{BASE_URL}/auth/login/", json=auth_data)
    if auth_response.status_code != 200:
        log(f"✗ Authentication failed: {auth_response.status_code}", "ERROR")
        log(f"Response: {auth_response.text}")
        return

    token = auth_response.json()["token"]
    headers = {"Authorization": f"Token {token}"}
    log("✓ Authenticated successfully")

    # Test bulk upload
    log("Testing bulk resume upload...")

    # Prepare files for upload
    files = []
    for file_path in test_files:
        with open(file_path, "rb") as f:
            files.append(
                ("files", (os.path.basename(file_path), f.read(), "application/pdf"))
            )

    # Make bulk upload request
    try:
        response = requests.post(
            f"{API_BASE}/resumes/bulk-upload/", files=files, headers=headers
        )

        log(f"Response Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            log("✓ Bulk upload successful!")
            log(f"Message: {data.get('message', 'N/A')}")

            # Display summary
            summary = data.get("summary", {})
            log(
                f"Summary: {summary.get('total_files', 0)} total, "
                f"{summary.get('successful', 0)} successful, "
                f"{summary.get('failed', 0)} failed"
            )

            # Display individual results
            results = data.get("results", [])
            log(f"Individual Results ({len(results)} files):")
            for i, result in enumerate(results, 1):
                if result.get("success"):
                    log(
                        f"  {i}. ✓ {result.get('filename')} - ID: {result.get('resume_id')}"
                    )
                    extracted = result.get("extracted_data", {})
                    if extracted:
                        log(f"     Extracted: {extracted}")
                else:
                    log(
                        f"  {i}. ✗ {result.get('filename')} - Error: {result.get('error_message')}"
                    )

        elif response.status_code == 400:
            log("✗ Bad Request", "ERROR")
            log(f"Response: {response.text}")
        elif response.status_code == 401:
            log("✗ Unauthorized - Authentication required", "ERROR")
        else:
            log(f"✗ Unexpected status: {response.status_code}", "ERROR")
            log(f"Response: {response.text}")

    except Exception as e:
        log(f"✗ Exception during upload: {str(e)}", "ERROR")

    # Clean up test files
    log("Cleaning up test files...")
    for file_path in test_files:
        try:
            os.remove(file_path)
            log(f"Removed: {file_path}")
        except:
            pass

    # Remove test directory if empty
    try:
        os.rmdir("test_files")
    except:
        pass

    log("=" * 60)
    log("BULK RESUME UPLOAD TESTING COMPLETED")
    log("=" * 60)


if __name__ == "__main__":
    try:
        test_bulk_resume_upload()
        log("\n🎉 Bulk upload test completed!")

    except KeyboardInterrupt:
        log("\n⚠️  Testing interrupted by user")
    except Exception as e:
        log(f"\n💥 Unexpected error: {str(e)}", "ERROR")
