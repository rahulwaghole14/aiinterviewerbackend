#!/usr/bin/env python3
"""
Comprehensive API Testing Script for AI Interviewer Platform
Tests all endpoints systematically and provides detailed results
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

# Test credentials
TEST_CREDENTIALS = {
    "company": {"email": "company_test@example.com", "password": "password123"},
    "agency": {"email": "agency_test@example.com", "password": "password123"},
    "recruiter": {"email": "recruiter_test@example.com", "password": "password123"},
    "admin": {"email": "admin@rslsolution.com", "password": "admin123"},
}


class APITester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        self.user_id = None
        self.job_id = None
        self.candidate_id = None
        self.resume_id = None
        self.interview_id = None

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
            print(f"   Error: {error}")

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
            self.log_test("/api/auth/login/", "POST", response.status_code, data)
            print(f"✅ Login successful! User ID: {self.user_id}")
            return True
        else:
            self.log_test(
                "/api/auth/login/", "POST", response.status_code, error=response.text
            )
            return False

    def test_auth_endpoints(self):
        """Test authentication endpoints"""
        print("\n🔐 Testing Authentication Endpoints...")

        # Test registration
        registration_data = {
            "email": "testuser@example.com",
            "password": "password123",
            "full_name": "Test User",
            "role": "COMPANY",
            "company_name": "Test Company",
        }

        response = self.session.post(
            f"{API_BASE}/auth/register/",
            json=registration_data,
            headers={"Content-Type": "application/json"},
        )
        self.log_test(
            "/api/auth/register/",
            "POST",
            response.status_code,
            response.json() if response.status_code == 201 else None,
        )

        # Test logout
        if self.auth_token:
            response = self.session.post(f"{API_BASE}/auth/logout/")
            self.log_test("/api/auth/logout/", "POST", response.status_code)

    def test_user_management(self):
        """Test user management endpoints"""
        print("\n👤 Testing User Management Endpoints...")

        # Get user profile
        response = self.session.get(f"{API_BASE}/users/profile/")
        self.log_test(
            "/api/users/profile/",
            "GET",
            response.status_code,
            response.json() if response.status_code == 200 else None,
        )

        # Update user profile
        if response.status_code == 200:
            update_data = {"full_name": "Updated Test User"}
            response = self.session.patch(
                f"{API_BASE}/users/profile/",
                json=update_data,
                headers={"Content-Type": "application/json"},
            )
            self.log_test(
                "/api/users/profile/",
                "PATCH",
                response.status_code,
                response.json() if response.status_code == 200 else None,
            )

    def test_domain_management(self):
        """Test domain management endpoints"""
        print("\n🏢 Testing Domain Management Endpoints...")

        # Get all domains
        response = self.session.get(f"{API_BASE}/jobs/domains/")
        self.log_test(
            "/api/jobs/domains/",
            "GET",
            response.status_code,
            response.json() if response.status_code == 200 else None,
        )

        # Get active domains
        response = self.session.get(f"{API_BASE}/jobs/domains/active/")
        self.log_test(
            "/api/jobs/domains/active/",
            "GET",
            response.status_code,
            response.json() if response.status_code == 200 else None,
        )

    def test_job_management(self):
        """Test job management endpoints"""
        print("\n💼 Testing Job Management Endpoints...")

        # Get all jobs
        response = self.session.get(f"{API_BASE}/jobs/")
        self.log_test(
            "/api/jobs/",
            "GET",
            response.status_code,
            response.json() if response.status_code == 200 else None,
        )

        # Create a new job
        job_data = {
            "title": "Test Software Engineer",
            "description": "Test job description",
            "requirements": "Python, Django, React",
            "location": "Remote",
            "salary_min": 50000,
            "salary_max": 80000,
            "job_type": "FULL_TIME",
            "experience_level": "MID_LEVEL",
        }

        response = self.session.post(
            f"{API_BASE}/jobs/",
            json=job_data,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 201:
            job_response = response.json()
            self.job_id = job_response.get("id")
            self.log_test("/api/jobs/", "POST", response.status_code, job_response)

            # Get specific job
            response = self.session.get(f"{API_BASE}/jobs/{self.job_id}/")
            self.log_test(
                f"/api/jobs/{self.job_id}/",
                "GET",
                response.status_code,
                response.json() if response.status_code == 200 else None,
            )
        else:
            self.log_test(
                "/api/jobs/", "POST", response.status_code, error=response.text
            )

    def test_candidate_management(self):
        """Test candidate management endpoints"""
        print("\n👤 Testing Candidate Management Endpoints...")

        # Get all candidates
        response = self.session.get(f"{API_BASE}/candidates/")
        self.log_test(
            "/api/candidates/",
            "GET",
            response.status_code,
            response.json() if response.status_code == 200 else None,
        )

        # Create a new candidate
        candidate_data = {
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

        response = self.session.post(
            f"{API_BASE}/candidates/",
            json=candidate_data,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 201:
            candidate_response = response.json()
            self.candidate_id = candidate_response.get("id")
            self.log_test(
                "/api/candidates/", "POST", response.status_code, candidate_response
            )

            # Get specific candidate
            response = self.session.get(f"{API_BASE}/candidates/{self.candidate_id}/")
            self.log_test(
                f"/api/candidates/{self.candidate_id}/",
                "GET",
                response.status_code,
                response.json() if response.status_code == 200 else None,
            )
        else:
            self.log_test(
                "/api/candidates/", "POST", response.status_code, error=response.text
            )

    def test_resume_management(self):
        """Test resume management endpoints"""
        print("\n📄 Testing Resume Management Endpoints...")

        # Get all resumes
        response = self.session.get(f"{API_BASE}/resumes/")
        self.log_test(
            "/api/resumes/",
            "GET",
            response.status_code,
            response.json() if response.status_code == 200 else None,
        )

        # Test resume upload (simulated)
        if self.candidate_id:
            resume_data = {
                "candidate": self.candidate_id,
                "title": "Test Resume",
                "description": "Test resume description",
            }

            response = self.session.post(
                f"{API_BASE}/resumes/",
                json=resume_data,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 201:
                resume_response = response.json()
                self.resume_id = resume_response.get("id")
                self.log_test(
                    "/api/resumes/", "POST", response.status_code, resume_response
                )
            else:
                self.log_test(
                    "/api/resumes/", "POST", response.status_code, error=response.text
                )

    def test_interview_management(self):
        """Test interview management endpoints"""
        print("\n📅 Testing Interview Management Endpoints...")

        # Get all interviews
        response = self.session.get(f"{API_BASE}/interviews/")
        self.log_test(
            "/api/interviews/",
            "GET",
            response.status_code,
            response.json() if response.status_code == 200 else None,
        )

        # Create a new interview
        if self.candidate_id and self.job_id:
            interview_data = {
                "candidate": self.candidate_id,
                "job": self.job_id,
                "interview_type": "TECHNICAL",
                "scheduled_date": "2024-01-15T10:00:00Z",
                "duration_minutes": 60,
                "interviewer_name": "Test Interviewer",
                "notes": "Test interview notes",
            }

            response = self.session.post(
                f"{API_BASE}/interviews/",
                json=interview_data,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 201:
                interview_response = response.json()
                self.interview_id = interview_response.get("id")
                self.log_test(
                    "/api/interviews/", "POST", response.status_code, interview_response
                )
            else:
                self.log_test(
                    "/api/interviews/",
                    "POST",
                    response.status_code,
                    error=response.text,
                )

    def test_notifications(self):
        """Test notification endpoints"""
        print("\n🔔 Testing Notification Endpoints...")

        # Get all notifications
        response = self.session.get(f"{API_BASE}/notifications/")
        self.log_test(
            "/api/notifications/",
            "GET",
            response.status_code,
            response.json() if response.status_code == 200 else None,
        )

        # Mark notifications as read
        response = self.session.post(f"{API_BASE}/notifications/mark-read/")
        self.log_test(
            "/api/notifications/mark-read/",
            "POST",
            response.status_code,
            response.json() if response.status_code == 200 else None,
        )

    def test_dashboard(self):
        """Test dashboard endpoints"""
        print("\n📊 Testing Dashboard Endpoints...")

        # Get dashboard analytics
        response = self.session.get(f"{API_BASE}/dashboard/analytics/")
        self.log_test(
            "/api/dashboard/analytics/",
            "GET",
            response.status_code,
            response.json() if response.status_code == 200 else None,
        )

        # Get recent activities
        response = self.session.get(f"{API_BASE}/dashboard/recent-activities/")
        self.log_test(
            "/api/dashboard/recent-activities/",
            "GET",
            response.status_code,
            response.json() if response.status_code == 200 else None,
        )

    def test_company_management(self):
        """Test company management endpoints"""
        print("\n🏢 Testing Company Management Endpoints...")

        # Get all companies
        response = self.session.get(f"{API_BASE}/companies/")
        self.log_test(
            "/api/companies/",
            "GET",
            response.status_code,
            response.json() if response.status_code == 200 else None,
        )

        # Get company profile
        response = self.session.get(f"{API_BASE}/companies/profile/")
        self.log_test(
            "/api/companies/profile/",
            "GET",
            response.status_code,
            response.json() if response.status_code == 200 else None,
        )

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Comprehensive API Testing...")
        print("=" * 60)

        # Test with different user types
        user_types = ["company", "agency", "recruiter", "admin"]

        for user_type in user_types:
            print(f"\n👤 Testing as {user_type.upper()} user")
            print("-" * 40)

            if self.login(user_type):
                self.test_auth_endpoints()
                self.test_user_management()
                self.test_domain_management()
                self.test_job_management()
                self.test_candidate_management()
                self.test_resume_management()
                self.test_interview_management()
                self.test_notifications()
                self.test_dashboard()
                self.test_company_management()

                # Logout before testing next user
                self.session.post(f"{API_BASE}/auth/logout/")
                self.auth_token = None
                self.session.headers.pop("Authorization", None)
            else:
                print(f"❌ Failed to login as {user_type}")

        # Generate test report
        self.generate_report()

    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📊 TEST REPORT SUMMARY")
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
        with open("api_test_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2)

        print(f"\n📄 Detailed results saved to: api_test_results.json")


if __name__ == "__main__":
    tester = APITester()
    tester.run_all_tests()
