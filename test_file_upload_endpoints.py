#!/usr/bin/env python3
"""
File Upload API Testing Script for AI Interviewer Platform
Tests bulk upload and candidate creation endpoints with sample resume files
"""

import requests
import json
import os
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

# Test credentials
TEST_CREDENTIALS = {
    "company": {"email": "company_test@example.com", "password": "password123"}
}


class FileUploadAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        self.user_id = None
        self.domain_id = None

    def log_test(self, endpoint, method, status_code, response_data=None, error=None):
        """Log test results"""
        result = {
            "timestamp": datetime.now().isoformat(),
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "success": 200 <= status_code < 300,
            "response_data": response_data,
            "error": error,
        }
        self.test_results.append(result)

        # Print result
        status_icon = "✅" if result["success"] else "❌"
        print(f"{status_icon} {method} {endpoint} - {status_code}")
        if error:
            print(f"   Error: {error[:200]}...")

    def login(self, user_type="company"):
        """Login and get auth token"""
        print(f"\n🔐 Logging in as {user_type} user...")

        credentials = TEST_CREDENTIALS[user_type]
        response = self.session.post(
            f"{API_BASE}/auth/login/",
            json=credentials,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 200:
            data = response.json()
            self.auth_token = data.get("token")
            self.user_id = data.get("user", {}).get("id")
            self.session.headers.update({"Authorization": f"Token {self.auth_token}"})
            self.log_test("/auth/login/", "POST", response.status_code, data)
            print(f"✅ Login successful! User ID: {self.user_id}")
            return True
        else:
            self.log_test(
                "/auth/login/", "POST", response.status_code, error=response.text
            )
            return False

    def get_domain_id(self):
        """Get a domain ID for testing"""
        response = self.session.get(f"{API_BASE}/jobs/domains/")
        if response.status_code == 200:
            domains = response.json()
            if domains:
                self.domain_id = domains[0].get("id")
                print(f"✅ Using domain ID: {self.domain_id}")
                return True
        return False

    def test_bulk_candidate_extract(self):
        """Test bulk candidate creation - extract step"""
        print("\n👤 Testing Bulk Candidate Creation - Extract Step...")

        # Get sample resume files
        test_files_dir = "test_files"
        resume_files = []

        if os.path.exists(test_files_dir):
            for filename in os.listdir(test_files_dir):
                if filename.endswith(".pdf"):
                    file_path = os.path.join(test_files_dir, filename)
                    resume_files.append(
                        (
                            "resume_files",
                            (filename, open(file_path, "rb"), "application/pdf"),
                        )
                    )

        if not resume_files:
            print("❌ No resume files found in test_files directory")
            return False

        # Prepare form data
        data = {"domain": str(self.domain_id), "role": "Software Engineer"}

        try:
            response = self.session.post(
                f"{API_BASE}/candidates/bulk-create/?step=extract",
                data=data,
                files=resume_files,
            )

            self.log_test(
                "/candidates/bulk-create/?step=extract",
                "POST",
                response.status_code,
                response.json() if response.status_code < 300 else None,
                response.text if response.status_code >= 400 else None,
            )

            # Close files
            for _, (_, file_obj, _) in resume_files:
                file_obj.close()

            return response.status_code < 300

        except Exception as e:
            # Close files on error
            for _, (_, file_obj, _) in resume_files:
                file_obj.close()
            self.log_test(
                "/candidates/bulk-create/?step=extract", "POST", 0, error=str(e)
            )
            return False

    def test_bulk_candidate_submit(self):
        """Test bulk candidate creation - submit step"""
        print("\n👤 Testing Bulk Candidate Creation - Submit Step...")

        # This would typically use the extracted data from the previous step
        # For testing, we'll create a mock submission
        submit_data = {
            "domain": str(self.domain_id),
            "role": "Software Engineer",
            "candidates": [
                {
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john.doe@example.com",
                    "phone": "+1234567890",
                    "experience_years": 3,
                    "current_company": "Test Company",
                    "current_position": "Software Engineer",
                    "expected_salary": 70000,
                    "notice_period": 30,
                    "skills": ["Python", "Django", "React"],
                    "education": "Bachelor's in Computer Science",
                }
            ],
        }

        response = self.session.post(
            f"{API_BASE}/candidates/bulk-create/?step=submit",
            json=submit_data,
            headers={"Content-Type": "application/json"},
        )

        self.log_test(
            "/candidates/bulk-create/?step=submit",
            "POST",
            response.status_code,
            response.json() if response.status_code < 300 else None,
            response.text if response.status_code >= 400 else None,
        )

        return response.status_code < 300

    def test_create_candidate_with_resume(self):
        """Test creating a single candidate with resume file"""
        print("\n👤 Testing Create Candidate with Resume...")

        # Get a sample resume file
        test_files_dir = "test_files"
        resume_file = None

        if os.path.exists(test_files_dir):
            for filename in os.listdir(test_files_dir):
                if filename.endswith(".pdf"):
                    file_path = os.path.join(test_files_dir, filename)
                    resume_file = (
                        "resume_file",
                        (filename, open(file_path, "rb"), "application/pdf"),
                    )
                    break

        if not resume_file:
            print("❌ No resume file found in test_files directory")
            return False

        # Prepare form data
        data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane.smith@example.com",
            "phone": "+1234567891",
            "experience_years": 2,
            "current_company": "Test Company",
            "current_position": "Junior Developer",
            "expected_salary": 60000,
            "notice_period": 30,
            "skills": ["JavaScript", "React", "Node.js"],
            "education": "Bachelor's in Computer Science",
        }

        try:
            response = self.session.post(
                f"{API_BASE}/candidates/", data=data, files=[resume_file]
            )

            self.log_test(
                "/candidates/",
                "POST",
                response.status_code,
                response.json() if response.status_code < 300 else None,
                response.text if response.status_code >= 400 else None,
            )

            # Close file
            resume_file[1][1].close()

            return response.status_code < 300

        except Exception as e:
            # Close file on error
            resume_file[1][1].close()
            self.log_test("/candidates/", "POST", 0, error=str(e))
            return False

    def test_bulk_resume_upload(self):
        """Test bulk resume upload"""
        print("\n📄 Testing Bulk Resume Upload...")

        # Get sample resume files
        test_files_dir = "test_files"
        resume_files = []

        if os.path.exists(test_files_dir):
            for filename in os.listdir(test_files_dir):
                if filename.endswith(".pdf"):
                    file_path = os.path.join(test_files_dir, filename)
                    resume_files.append(
                        ("files", (filename, open(file_path, "rb"), "application/pdf"))
                    )

        if not resume_files:
            print("❌ No resume files found in test_files directory")
            return False

        try:
            response = self.session.post(
                f"{API_BASE}/resumes/bulk-upload/", files=resume_files
            )

            self.log_test(
                "/resumes/bulk-upload/",
                "POST",
                response.status_code,
                response.json() if response.status_code < 300 else None,
                response.text if response.status_code >= 400 else None,
            )

            # Close files
            for _, (_, file_obj, _) in resume_files:
                file_obj.close()

            return response.status_code < 300

        except Exception as e:
            # Close files on error
            for _, (_, file_obj, _) in resume_files:
                file_obj.close()
            self.log_test("/resumes/bulk-upload/", "POST", 0, error=str(e))
            return False

    def test_incorrect_methods(self):
        """Test incorrect HTTP methods to verify the 405 errors"""
        print("\n🚫 Testing Incorrect HTTP Methods...")

        # Test GET on bulk-create (should return 405)
        response = self.session.get(f"{API_BASE}/candidates/bulk-create/?step=extract")
        self.log_test(
            "/candidates/bulk-create/?step=extract",
            "GET",
            response.status_code,
            None,
            response.text if response.status_code >= 400 else None,
        )

        # Test POST without files on bulk-upload (should return 400)
        response = self.session.post(f"{API_BASE}/resumes/bulk-upload/", json={})
        self.log_test(
            "/resumes/bulk-upload/",
            "POST",
            response.status_code,
            None,
            response.text if response.status_code >= 400 else None,
        )

    def run_all_tests(self):
        """Run all file upload tests"""
        print("🚀 Starting File Upload API Testing...")
        print("=" * 60)

        # Login first
        if not self.login("company"):
            print("❌ Failed to login")
            return

        # Get domain ID
        if not self.get_domain_id():
            print("❌ Failed to get domain ID")
            return

        # Test the problematic endpoints
        self.test_bulk_candidate_extract()
        self.test_bulk_candidate_submit()
        self.test_create_candidate_with_resume()
        self.test_bulk_resume_upload()

        # Test incorrect methods
        self.test_incorrect_methods()

        # Generate test report
        self.generate_report()

    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📊 FILE UPLOAD API TEST REPORT")
        print("=" * 60)

        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - successful_tests

        print(f"Total Tests: {total_tests}")
        print(f"✅ Successful: {successful_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")

        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(
                        f"  - {result['method']} {result['endpoint']} ({result['status_code']})"
                    )
                    if result["error"]:
                        print(f"    Error: {result['error'][:100]}...")

        # Save detailed results to file
        with open("file_upload_test_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2)

        print(f"\n📄 Detailed results saved to: file_upload_test_results.json")
        print(f"🎉 File Upload API Testing Complete!")


if __name__ == "__main__":
    tester = FileUploadAPITester()
    tester.run_all_tests()
