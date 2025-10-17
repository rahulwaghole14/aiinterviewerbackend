#!/usr/bin/env python3
"""
Test script to verify poc_email field in bulk candidate creation
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"


def test_poc_email_bulk_candidate_creation():
    """Test poc_email field in bulk candidate creation"""
    print("🔍 Testing POC Email in Bulk Candidate Creation")
    print("=" * 60)

    # First, create an admin user for testing
    print("🔧 Creating admin user for testing...")
    admin_data = {
        "email": "admin_poc_test@example.com",
        "password": "adminpass123",
        "full_name": "Admin POC Test User",
        "company_name": "Admin Company",
        "role": "ADMIN",
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/register/",
            json=admin_data,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 201:
            admin_data = response.json()
            admin_token = admin_data["token"]
            print("   ✅ Admin user created successfully")
        else:
            print(f"   ❌ Admin user creation failed: {response.text}")
            return False

    except Exception as e:
        print(f"   ❌ Error creating admin user: {str(e)}")
        return False

    # Test 1: Direct bulk creation with poc_email
    print("\n📝 Test 1: Direct bulk creation with poc_email")
    print("-" * 50)

    # Create a simple test file
    test_file_content = b"Test resume content"
    files = {"resume_files": ("test_resume.pdf", test_file_content, "application/pdf")}

    data = {
        "domain": "Data Science",
        "role": "Data Scientist",
        "poc_email": "poc@testcompany.com",
    }

    headers = {"Authorization": f"Token {admin_token}"}

    try:
        response = requests.post(
            f"{BASE_URL}/api/candidates/bulk-create/",
            data=data,
            files=files,
            headers=headers,
        )

        print(f"   Status Code: {response.status_code}")

        if response.status_code == 201:
            result = response.json()
            print("   ✅ Direct bulk creation successful!")
            print(f"   - Message: {result.get('message')}")
            print(
                f"   - Created candidates: {len(result.get('created_candidates', []))}"
            )

            # Check if candidates were created
            if result.get("created_candidates"):
                candidate_id = result["created_candidates"][0]["id"]
                print(f"   - First candidate ID: {candidate_id}")

                # Verify poc_email was saved
                return verify_poc_email_saved(
                    candidate_id, admin_token, "poc@testcompany.com"
                )
            else:
                print("   ⚠️  No candidates were created")
                return False
        else:
            print(f"   ❌ Direct bulk creation failed: {response.text}")
            return False

    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False


def test_poc_email_submit_step():
    """Test poc_email in submit step"""
    print("\n📝 Test 2: Submit step with poc_email")
    print("-" * 50)

    # Create admin user if not exists
    admin_data = {
        "email": "admin_submit_test@example.com",
        "password": "adminpass123",
        "full_name": "Admin Submit Test User",
        "company_name": "Admin Company",
        "role": "ADMIN",
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/register/",
            json=admin_data,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 201:
            admin_data = response.json()
            admin_token = admin_data["token"]
            print("   ✅ Admin user created/retrieved successfully")
        else:
            print(f"   ❌ Admin user creation failed: {response.text}")
            return False

    except Exception as e:
        print(f"   ❌ Error creating admin user: {str(e)}")
        return False

    # Test submit step with poc_email
    submit_data = {
        "domain": "Data Science",
        "role": "Data Scientist",
        "poc_email": "submit_poc@testcompany.com",
        "candidates": [
            {
                "filename": "test_resume.pdf",
                "edited_data": {
                    "name": "John Doe",
                    "email": "john.doe@example.com",
                    "phone": "+1234567890",
                    "work_experience": 5,
                },
            }
        ],
    }

    headers = {
        "Authorization": f"Token {admin_token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/candidates/bulk-create/?step=submit",
            json=submit_data,
            headers=headers,
        )

        print(f"   Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("   ✅ Submit step successful!")
            print(f"   - Message: {result.get('message')}")
            print(f"   - Results: {len(result.get('results', []))}")

            # Check if candidates were created
            if result.get("results"):
                for result_item in result["results"]:
                    if result_item.get("status") == "success":
                        candidate_id = result_item.get("candidate_id")
                        print(f"   - Candidate ID: {candidate_id}")

                        # Verify poc_email was saved
                        return verify_poc_email_saved(
                            candidate_id, admin_token, "submit_poc@testcompany.com"
                        )
            else:
                print("   ⚠️  No candidates were created")
                return False
        else:
            print(f"   ❌ Submit step failed: {response.text}")
            return False

    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False


def verify_poc_email_saved(candidate_id, admin_token, expected_poc_email):
    """Verify that poc_email was saved correctly"""
    print(f"\n🔍 Verifying poc_email for candidate {candidate_id}")
    print("-" * 50)

    headers = {"Authorization": f"Token {admin_token}"}

    try:
        # Get candidate details
        response = requests.get(
            f"{BASE_URL}/api/candidates/{candidate_id}/", headers=headers
        )

        print(f"   Status Code: {response.status_code}")

        if response.status_code == 200:
            candidate = response.json()
            actual_poc_email = candidate.get("poc_email")

            print(f"   - Expected poc_email: {expected_poc_email}")
            print(f"   - Actual poc_email: {actual_poc_email}")

            if actual_poc_email == expected_poc_email:
                print("   ✅ poc_email saved correctly!")
                return True
            else:
                print("   ❌ poc_email not saved correctly!")
                return False
        else:
            print(f"   ❌ Failed to get candidate: {response.text}")
            return False

    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False


def test_get_all_candidates_poc_email():
    """Test that poc_email is returned in get all candidates API"""
    print("\n📝 Test 3: Get all candidates API includes poc_email")
    print("-" * 50)

    # Create admin user if not exists
    admin_data = {
        "email": "admin_list_test@example.com",
        "password": "adminpass123",
        "full_name": "Admin List Test User",
        "company_name": "Admin Company",
        "role": "ADMIN",
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/register/",
            json=admin_data,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 201:
            admin_data = response.json()
            admin_token = admin_data["token"]
            print("   ✅ Admin user created/retrieved successfully")
        else:
            print(f"   ❌ Admin user creation failed: {response.text}")
            return False

    except Exception as e:
        print(f"   ❌ Error creating admin user: {str(e)}")
        return False

    headers = {"Authorization": f"Token {admin_token}"}

    try:
        response = requests.get(f"{BASE_URL}/api/candidates/", headers=headers)

        print(f"   Status Code: {response.status_code}")

        if response.status_code == 200:
            candidates = response.json()
            print(f"   ✅ Get all candidates successful!")
            print(f"   - Total candidates: {len(candidates)}")

            # Check if poc_email field is present in response
            if candidates:
                first_candidate = candidates[0]
                if "poc_email" in first_candidate:
                    print("   ✅ poc_email field is present in response!")
                    print(f"   - Sample poc_email: {first_candidate.get('poc_email')}")
                    return True
                else:
                    print("   ❌ poc_email field is missing from response!")
                    return False
            else:
                print("   ⚠️  No candidates found")
                return False
        else:
            print(f"   ❌ Get all candidates failed: {response.text}")
            return False

    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False


def main():
    """Main test function"""
    print("🚀 Starting POC Email Bulk Candidate Creation Tests")
    print("=" * 60)

    # Wait for server to start
    time.sleep(3)

    # Run tests
    test1_success = test_poc_email_bulk_candidate_creation()
    test2_success = test_poc_email_submit_step()
    test3_success = test_get_all_candidates_poc_email()

    # Summary
    print("\n📊 Test Summary")
    print("=" * 60)
    print(
        f"✅ Direct bulk creation with poc_email: {'PASS' if test1_success else 'FAIL'}"
    )
    print(f"✅ Submit step with poc_email: {'PASS' if test2_success else 'FAIL'}")
    print(
        f"✅ Get all candidates includes poc_email: {'PASS' if test3_success else 'FAIL'}"
    )

    if test1_success and test2_success and test3_success:
        print("\n🎉 SUCCESS: All poc_email tests passed!")
        return True
    else:
        print("\n❌ FAILED: Some poc_email tests failed!")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
