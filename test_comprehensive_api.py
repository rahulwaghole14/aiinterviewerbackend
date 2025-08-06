#!/usr/bin/env python3
"""
Comprehensive API Testing Script for AI Interviewer Platform
Tests all endpoints systematically and matches Postman collection
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

# Test credentials
TEST_CREDENTIALS = {
    "company": {
        "email": "company_test@example.com",
        "password": "password123"
    },
    "agency": {
        "email": "agency_test@example.com", 
        "password": "password123"
    },
    "recruiter": {
        "email": "recruiter_test@example.com",
        "password": "password123"
    },
    "admin": {
        "email": "admin@rslsolution.com",
        "password": "admin123"
    }
}

class ComprehensiveAPITester:
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
            "error": error
        }
        self.test_results.append(result)
        
        # Print result
        status_icon = "✅" if result["success"] else "❌"
        print(f"{status_icon} {method} {endpoint} - {status_code}")
        if error:
            print(f"   Error: {error}")
    
    def test_endpoint(self, method, endpoint, data=None, description=""):
        """Test a single endpoint"""
        try:
            if method == "GET":
                response = self.session.get(f"{API_BASE}{endpoint}")
            elif method == "POST":
                response = self.session.post(f"{API_BASE}{endpoint}", json=data)
            elif method == "PATCH":
                response = self.session.patch(f"{API_BASE}{endpoint}", json=data)
            elif method == "PUT":
                response = self.session.put(f"{API_BASE}{endpoint}", json=data)
            elif method == "DELETE":
                response = self.session.delete(f"{API_BASE}{endpoint}")
            
            self.log_test(endpoint, method, response.status_code, 
                         response.json() if response.status_code < 300 else None,
                         response.text if response.status_code >= 400 else None)
            
            return response.status_code < 300, response
            
        except Exception as e:
            self.log_test(endpoint, method, 0, error=str(e))
            return False, None
    
    def login(self, user_type="company"):
        """Login and get auth token"""
        print(f"\n🔐 Logging in as {user_type} user...")
        
        credentials = TEST_CREDENTIALS[user_type]
        response = self.session.post(
            f"{API_BASE}/auth/login/",
            json=credentials,
            headers={"Content-Type": "application/json"}
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
            self.log_test("/auth/login/", "POST", response.status_code, error=response.text)
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
            "company_name": "Test Company"
        }
        
        self.test_endpoint("POST", "/auth/register/", registration_data)
        
        # Test user profile
        self.test_endpoint("GET", "/auth/profile/")
        
        # Test profile update
        update_data = {"full_name": "Updated Test User"}
        self.test_endpoint("PATCH", "/auth/profile/", update_data)
    
    def test_domain_management(self):
        """Test domain management endpoints"""
        print("\n🏢 Testing Domain Management Endpoints...")
        
        self.test_endpoint("GET", "/jobs/domains/")
        self.test_endpoint("GET", "/jobs/domains/active/")
    
    def test_job_management(self):
        """Test job management endpoints"""
        print("\n💼 Testing Job Management Endpoints...")
        
        # Get all jobs
        self.test_endpoint("GET", "/jobs/")
        
        # Create a new job
        job_data = {
            "title": "Test Software Engineer",
            "description": "Test job description",
            "requirements": "Python, Django, React",
            "location": "Remote",
            "salary_min": 50000,
            "salary_max": 80000,
            "job_type": "FULL_TIME",
            "experience_level": "MID_LEVEL"
        }
        
        success, response = self.test_endpoint("POST", "/jobs/", job_data)
        if success and response:
            job_response = response.json()
            self.job_id = job_response.get("id")
            if self.job_id:
                self.test_endpoint("GET", f"/jobs/{self.job_id}/")
    
    def test_candidate_management(self):
        """Test candidate management endpoints"""
        print("\n👤 Testing Candidate Management Endpoints...")
        
        # Get all candidates
        self.test_endpoint("GET", "/candidates/")
        
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
            "education": "Bachelor's in Computer Science"
        }
        
        success, response = self.test_endpoint("POST", "/candidates/", candidate_data)
        if success and response:
            candidate_response = response.json()
            self.candidate_id = candidate_response.get("id")
            if self.candidate_id:
                self.test_endpoint("GET", f"/candidates/{self.candidate_id}/")
    
    def test_resume_management(self):
        """Test resume management endpoints"""
        print("\n📄 Testing Resume Management Endpoints...")
        
        self.test_endpoint("GET", "/resumes/")
        
        # Test bulk upload endpoint
        self.test_endpoint("GET", "/resumes/bulk-upload/")
    
    def test_interview_management(self):
        """Test interview management endpoints"""
        print("\n📅 Testing Interview Management Endpoints...")
        
        self.test_endpoint("GET", "/interviews/")
        
        # Create interview if we have candidate and job
        if self.candidate_id and self.job_id:
            interview_data = {
                "candidate": self.candidate_id,
                "job": self.job_id,
                "interview_type": "TECHNICAL",
                "scheduled_date": "2024-01-15T10:00:00Z",
                "duration_minutes": 60,
                "interviewer_name": "Test Interviewer",
                "notes": "Test interview notes"
            }
            
            success, response = self.test_endpoint("POST", "/interviews/", interview_data)
            if success and response:
                interview_response = response.json()
                self.interview_id = interview_response.get("id")
    
    def test_notifications(self):
        """Test notification endpoints"""
        print("\n🔔 Testing Notification Endpoints...")
        
        self.test_endpoint("GET", "/notifications/")
        self.test_endpoint("POST", "/notifications/mark-read/")
    
    def test_dashboard(self):
        """Test dashboard endpoints"""
        print("\n📊 Testing Dashboard Endpoints...")
        
        self.test_endpoint("GET", "/dashboard/")
        self.test_endpoint("GET", "/dashboard/summary/")
        self.test_endpoint("GET", "/dashboard/analytics/")
        self.test_endpoint("GET", "/dashboard/recent-activities/")
        self.test_endpoint("GET", "/dashboard/activities/")
        self.test_endpoint("GET", "/dashboard/performance/")
        self.test_endpoint("GET", "/dashboard/resume-stats/")
        self.test_endpoint("GET", "/dashboard/interview-stats/")
        self.test_endpoint("GET", "/dashboard/candidate-stats/")
        self.test_endpoint("GET", "/dashboard/job-stats/")
    
    def test_company_management(self):
        """Test company management endpoints"""
        print("\n🏢 Testing Company Management Endpoints...")
        
        self.test_endpoint("GET", "/companies/")
        self.test_endpoint("GET", "/companies/profile/")
        
        # Create company
        company_data = {
            "name": "Test Company",
            "description": "A test company",
            "is_active": True
        }
        
        success, response = self.test_endpoint("POST", "/companies/", company_data)
        if success and response:
            company_response = response.json()
            company_id = company_response.get("id")
            if company_id:
                self.test_endpoint("GET", f"/companies/{company_id}/")
                self.test_endpoint("PUT", f"/companies/{company_id}/", company_data)
    
    def test_evaluation(self):
        """Test evaluation endpoints"""
        print("\n📊 Testing Evaluation Endpoints...")
        
        self.test_endpoint("GET", "/evaluation/")
    
    def test_hiring_agency(self):
        """Test hiring agency endpoints"""
        print("\n🏢 Testing Hiring Agency Endpoints...")
        
        self.test_endpoint("GET", "/hiring_agency/")
    
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
                self.test_domain_management()
                self.test_job_management()
                self.test_candidate_management()
                self.test_resume_management()
                self.test_interview_management()
                self.test_notifications()
                self.test_dashboard()
                self.test_company_management()
                self.test_evaluation()
                self.test_hiring_agency()
                
                # Logout
                self.test_endpoint("POST", "/auth/logout/")
                self.auth_token = None
                self.session.headers.pop("Authorization", None)
            else:
                print(f"❌ Failed to login as {user_type}")
        
        # Generate test report
        self.generate_report()
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST REPORT")
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
                    print(f"  - {result['method']} {result['endpoint']} ({result['status_code']})")
                    if result["error"]:
                        print(f"    Error: {result['error'][:100]}...")
        
        # Save detailed results to file
        with open("comprehensive_api_test_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: comprehensive_api_test_results.json")
        print(f"🎉 API Testing Complete!")

if __name__ == "__main__":
    tester = ComprehensiveAPITester()
    tester.run_all_tests() 