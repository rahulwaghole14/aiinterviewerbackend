#!/usr/bin/env python3
"""
Comprehensive CRUD Operations Test - FIXED VERSION
Tests Create, Read, Update, Delete operations for:
- Candidates
- Companies  
- Hiring Agencies
- Recruiters

Fixed issues:
- Hiring Agency UPDATE/DELETE: Use correct URL patterns
- Recruiter CREATE: Use correct endpoint
- Candidate CREATE: Handle resume_file requirement
"""

import requests
import json
import time
import os
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@rslsolution.com"
ADMIN_PASSWORD = "admin123"

class CRUDTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_data = {}
        
    def login(self, email: str, password: str) -> bool:
        """Login and get auth token"""
        try:
            response = self.session.post(f"{BASE_URL}/api/auth/login/", json={
                "email": email,
                "password": password
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('token')
                self.session.headers.update({'Authorization': f'Token {self.auth_token}'})
                print(f"✅ Login successful for {email}")
                return True
            else:
                print(f"❌ Login failed for {email}: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Login error for {email}: {str(e)}")
            return False
    
    def create_test_resume_file(self) -> str:
        """Create a temporary test resume file"""
        test_content = """
        JOHN DOE
        Software Engineer
        john.doe@example.com
        +1234567890
        
        EXPERIENCE:
        - Senior Developer at Tech Corp (2018-2023)
        - Python, Django, React, AWS
        - 5 years of experience
        """
        
        filename = f"test_resume_{int(time.time())}.txt"
        with open(filename, 'w') as f:
            f.write(test_content)
        return filename
    
    def test_company_crud(self) -> Dict[str, Any]:
        """Test Company CRUD operations"""
        print("\n" + "="*60)
        print("🏢 TESTING COMPANY CRUD OPERATIONS")
        print("="*60)
        
        results = {"create": False, "read": False, "update": False, "delete": False}
        
        # CREATE
        print("\n📝 Testing Company CREATE...")
        company_data = {
            "name": f"Test Company CRUD {int(time.time())}",
            "email": f"testcompany{int(time.time())}@example.com",
            "password": "company123",
            "description": "Test company for CRUD operations",
            "is_active": True
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/api/companies/", json=company_data)
            if response.status_code == 201:
                created_company = response.json()
                company_id = created_company['id']
                self.test_data['company_id'] = company_id
                print(f"✅ Company created successfully: ID {company_id}")
                results["create"] = True
            else:
                print(f"❌ Company creation failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Company creation error: {str(e)}")
        
        # READ (List)
        print("\n📖 Testing Company READ (List)...")
        try:
            response = self.session.get(f"{BASE_URL}/api/companies/")
            if response.status_code == 200:
                companies = response.json()
                print(f"✅ Companies list retrieved: {len(companies)} companies")
                results["read"] = True
            else:
                print(f"❌ Companies list failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Companies list error: {str(e)}")
        
        # READ (Detail)
        if self.test_data.get('company_id'):
            print(f"\n📖 Testing Company READ (Detail) - ID {self.test_data['company_id']}...")
            try:
                response = self.session.get(f"{BASE_URL}/api/companies/{self.test_data['company_id']}/")
                if response.status_code == 200:
                    company_detail = response.json()
                    print(f"✅ Company detail retrieved: {company_detail['name']}")
                else:
                    print(f"❌ Company detail failed: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"❌ Company detail error: {str(e)}")
        
        # UPDATE
        if self.test_data.get('company_id'):
            print(f"\n✏️ Testing Company UPDATE - ID {self.test_data['company_id']}...")
            update_data = {
                "name": f"Updated Test Company {int(time.time())}",
                "description": "Updated description for CRUD test"
            }
            try:
                response = self.session.put(f"{BASE_URL}/api/companies/{self.test_data['company_id']}/", json=update_data)
                if response.status_code == 200:
                    updated_company = response.json()
                    print(f"✅ Company updated successfully: {updated_company['name']}")
                    results["update"] = True
                else:
                    print(f"❌ Company update failed: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"❌ Company update error: {str(e)}")
        
        # DELETE
        if self.test_data.get('company_id'):
            print(f"\n🗑️ Testing Company DELETE - ID {self.test_data['company_id']}...")
            try:
                response = self.session.delete(f"{BASE_URL}/api/companies/{self.test_data['company_id']}/")
                if response.status_code == 204:
                    print(f"✅ Company deleted successfully")
                    results["delete"] = True
                else:
                    print(f"❌ Company deletion failed: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"❌ Company deletion error: {str(e)}")
        
        return results
    
    def test_hiring_agency_crud(self) -> Dict[str, Any]:
        """Test Hiring Agency CRUD operations"""
        print("\n" + "="*60)
        print("👥 TESTING HIRING AGENCY CRUD OPERATIONS")
        print("="*60)
        
        results = {"create": False, "read": False, "update": False, "delete": False}
        
        # CREATE
        print("\n📝 Testing Hiring Agency CREATE...")
        agency_data = {
            "first_name": f"Test Agency {int(time.time())}",
            "last_name": "CRUD",
            "email": f"testagency{int(time.time())}@example.com",
            "password": "agency123",
            "phone_number": "+1234567890",
            "role": "Hiring Agency",
            "input_company_name": "Test Company for Agency",
            "linkedin_url": "https://linkedin.com/in/testagency"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/api/hiring_agency/add_user/", json=agency_data)
            if response.status_code == 201:
                created_agency = response.json()
                agency_id = created_agency['id']
                self.test_data['agency_id'] = agency_id
                print(f"✅ Hiring Agency created successfully: ID {agency_id}")
                results["create"] = True
            else:
                print(f"❌ Hiring Agency creation failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Hiring Agency creation error: {str(e)}")
        
        # READ (List)
        print("\n📖 Testing Hiring Agency READ (List)...")
        try:
            response = self.session.get(f"{BASE_URL}/api/hiring_agency/")
            if response.status_code == 200:
                agencies = response.json()
                print(f"✅ Hiring Agencies list retrieved: {len(agencies)} agencies")
                results["read"] = True
            else:
                print(f"❌ Hiring Agencies list failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Hiring Agencies list error: {str(e)}")
        
        # READ (Detail)
        if self.test_data.get('agency_id'):
            print(f"\n📖 Testing Hiring Agency READ (Detail) - ID {self.test_data['agency_id']}...")
            try:
                response = self.session.get(f"{BASE_URL}/api/hiring_agency/{self.test_data['agency_id']}/")
                if response.status_code == 200:
                    agency_detail = response.json()
                    print(f"✅ Hiring Agency detail retrieved: {agency_detail['first_name']} {agency_detail['last_name']}")
                else:
                    print(f"❌ Hiring Agency detail failed: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"❌ Hiring Agency detail error: {str(e)}")
        
        # UPDATE - Use the correct URL pattern from router
        if self.test_data.get('agency_id'):
            print(f"\n✏️ Testing Hiring Agency UPDATE - ID {self.test_data['agency_id']}...")
            update_data = {
                "first_name": f"Updated Agency {int(time.time())}",
                "last_name": "Updated CRUD",
                "phone_number": "+1987654321"
            }
            try:
                # Use the router-generated URL pattern
                response = self.session.put(f"{BASE_URL}/api/hiring_agency/hiring_agency/{self.test_data['agency_id']}/", json=update_data)
                if response.status_code == 200:
                    updated_agency = response.json()
                    print(f"✅ Hiring Agency updated successfully: {updated_agency['first_name']} {updated_agency['last_name']}")
                    results["update"] = True
                else:
                    print(f"❌ Hiring Agency update failed: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"❌ Hiring Agency update error: {str(e)}")
        
        # DELETE - Use the correct URL pattern from router
        if self.test_data.get('agency_id'):
            print(f"\n🗑️ Testing Hiring Agency DELETE - ID {self.test_data['agency_id']}...")
            try:
                # Use the router-generated URL pattern
                response = self.session.delete(f"{BASE_URL}/api/hiring_agency/hiring_agency/{self.test_data['agency_id']}/")
                if response.status_code == 204:
                    print(f"✅ Hiring Agency deleted successfully")
                    results["delete"] = True
                else:
                    print(f"❌ Hiring Agency deletion failed: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"❌ Hiring Agency deletion error: {str(e)}")
        
        return results
    
    def test_recruiter_crud(self) -> Dict[str, Any]:
        """Test Recruiter CRUD operations"""
        print("\n" + "="*60)
        print("👨‍💼 TESTING RECRUITER CRUD OPERATIONS")
        print("="*60)
        
        results = {"create": False, "read": False, "update": False, "delete": False}
        
        # CREATE - Use the correct endpoint
        print("\n📝 Testing Recruiter CREATE...")
        recruiter_data = {
            "first_name": f"Test Recruiter {int(time.time())}",
            "last_name": "CRUD",
            "email": f"testrecruiter{int(time.time())}@example.com",
            "phone_number": "+1234567890",
            "company_name": "Test Company for Recruiter",
            "linkedin_url": "https://linkedin.com/in/testrecruiter"
        }
        
        try:
            # Use the correct endpoint from companies/urls.py
            response = self.session.post(f"{BASE_URL}/api/companies/recruiters/create/", json=recruiter_data)
            if response.status_code == 201:
                created_recruiter = response.json()
                recruiter_id = created_recruiter['id']
                self.test_data['recruiter_id'] = recruiter_id
                print(f"✅ Recruiter created successfully: ID {recruiter_id}")
                results["create"] = True
            else:
                print(f"❌ Recruiter creation failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Recruiter creation error: {str(e)}")
        
        # READ (List)
        print("\n📖 Testing Recruiter READ (List)...")
        try:
            response = self.session.get(f"{BASE_URL}/api/companies/recruiters/")
            if response.status_code == 200:
                recruiters = response.json()
                print(f"✅ Recruiters list retrieved: {len(recruiters)} recruiters")
                results["read"] = True
            else:
                print(f"❌ Recruiters list failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Recruiters list error: {str(e)}")
        
        # READ (Detail)
        if self.test_data.get('recruiter_id'):
            print(f"\n📖 Testing Recruiter READ (Detail) - ID {self.test_data['recruiter_id']}...")
            try:
                response = self.session.get(f"{BASE_URL}/api/companies/recruiters/{self.test_data['recruiter_id']}/")
                if response.status_code == 200:
                    recruiter_detail = response.json()
                    print(f"✅ Recruiter detail retrieved: {recruiter_detail['first_name']} {recruiter_detail['last_name']}")
                else:
                    print(f"❌ Recruiter detail failed: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"❌ Recruiter detail error: {str(e)}")
        
        # UPDATE
        if self.test_data.get('recruiter_id'):
            print(f"\n✏️ Testing Recruiter UPDATE - ID {self.test_data['recruiter_id']}...")
            update_data = {
                "first_name": f"Updated Recruiter {int(time.time())}",
                "last_name": "Updated CRUD",
                "phone_number": "+1987654321"
            }
            try:
                response = self.session.put(f"{BASE_URL}/api/companies/recruiters/{self.test_data['recruiter_id']}/", json=update_data)
                if response.status_code == 200:
                    updated_recruiter = response.json()
                    print(f"✅ Recruiter updated successfully: {updated_recruiter['first_name']} {updated_recruiter['last_name']}")
                    results["update"] = True
                else:
                    print(f"❌ Recruiter update failed: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"❌ Recruiter update error: {str(e)}")
        
        # DELETE
        if self.test_data.get('recruiter_id'):
            print(f"\n🗑️ Testing Recruiter DELETE - ID {self.test_data['recruiter_id']}...")
            try:
                response = self.session.delete(f"{BASE_URL}/api/companies/recruiters/{self.test_data['recruiter_id']}/")
                if response.status_code == 204:
                    print(f"✅ Recruiter deleted successfully")
                    results["delete"] = True
                else:
                    print(f"❌ Recruiter deletion failed: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"❌ Recruiter deletion error: {str(e)}")
        
        return results
    
    def test_candidate_crud(self) -> Dict[str, Any]:
        """Test Candidate CRUD operations"""
        print("\n" + "="*60)
        print("👤 TESTING CANDIDATE CRUD OPERATIONS")
        print("="*60)
        
        results = {"create": False, "read": False, "update": False, "delete": False}
        
        # CREATE - Handle resume_file requirement
        print("\n📝 Testing Candidate CREATE...")
        
        # Create a test resume file
        test_resume_file = self.create_test_resume_file()
        
        try:
            with open(test_resume_file, 'rb') as f:
                files = {'resume_file': (test_resume_file, f, 'text/plain')}
                data = {
                    "full_name": f"Test Candidate {int(time.time())}",
                    "email": f"testcandidate{int(time.time())}@example.com",
                    "phone": "+1234567890",
                    "poc_email": "poc@example.com",
                    "work_experience": 5,
                    "domain": "Technology"
                }
                
                response = self.session.post(f"{BASE_URL}/api/candidates/", data=data, files=files)
                if response.status_code == 201:
                    created_candidate = response.json()
                    candidate_id = created_candidate['id']
                    self.test_data['candidate_id'] = candidate_id
                    print(f"✅ Candidate created successfully: ID {candidate_id}")
                    results["create"] = True
                else:
                    print(f"❌ Candidate creation failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Candidate creation error: {str(e)}")
        finally:
            # Clean up test file
            if os.path.exists(test_resume_file):
                os.remove(test_resume_file)
        
        # READ (List)
        print("\n📖 Testing Candidate READ (List)...")
        try:
            response = self.session.get(f"{BASE_URL}/api/candidates/")
            if response.status_code == 200:
                candidates = response.json()
                print(f"✅ Candidates list retrieved: {len(candidates)} candidates")
                results["read"] = True
            else:
                print(f"❌ Candidates list failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Candidates list error: {str(e)}")
        
        # READ (Detail)
        if self.test_data.get('candidate_id'):
            print(f"\n📖 Testing Candidate READ (Detail) - ID {self.test_data['candidate_id']}...")
            try:
                response = self.session.get(f"{BASE_URL}/api/candidates/{self.test_data['candidate_id']}/")
                if response.status_code == 200:
                    candidate_detail = response.json()
                    print(f"✅ Candidate detail retrieved: {candidate_detail['full_name']}")
                else:
                    print(f"❌ Candidate detail failed: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"❌ Candidate detail error: {str(e)}")
        
        # UPDATE
        if self.test_data.get('candidate_id'):
            print(f"\n✏️ Testing Candidate UPDATE - ID {self.test_data['candidate_id']}...")
            update_data = {
                "full_name": f"Updated Candidate {int(time.time())}",
                "work_experience": 7,
                "poc_email": "updated.poc@example.com"
            }
            try:
                response = self.session.put(f"{BASE_URL}/api/candidates/{self.test_data['candidate_id']}/", json=update_data)
                if response.status_code == 200:
                    updated_candidate = response.json()
                    print(f"✅ Candidate updated successfully: {updated_candidate['full_name']}")
                    results["update"] = True
                else:
                    print(f"❌ Candidate update failed: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"❌ Candidate update error: {str(e)}")
        
        # DELETE
        if self.test_data.get('candidate_id'):
            print(f"\n🗑️ Testing Candidate DELETE - ID {self.test_data['candidate_id']}...")
            try:
                response = self.session.delete(f"{BASE_URL}/api/candidates/{self.test_data['candidate_id']}/")
                if response.status_code == 204:
                    print(f"✅ Candidate deleted successfully")
                    results["delete"] = True
                else:
                    print(f"❌ Candidate deletion failed: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"❌ Candidate deletion error: {str(e)}")
        
        return results
    
    def run_all_tests(self):
        """Run all CRUD tests"""
        print("🚀 STARTING COMPREHENSIVE CRUD OPERATIONS TEST - FIXED VERSION")
        print("="*80)
        
        # Login as admin
        if not self.login(ADMIN_EMAIL, ADMIN_PASSWORD):
            print("❌ Cannot proceed without admin login")
            return
        
        # Run all CRUD tests
        company_results = self.test_company_crud()
        hiring_agency_results = self.test_hiring_agency_crud()
        recruiter_results = self.test_recruiter_crud()
        candidate_results = self.test_candidate_crud()
        
        # Summary
        print("\n" + "="*80)
        print("📊 CRUD OPERATIONS TEST SUMMARY")
        print("="*80)
        
        entities = [
            ("🏢 Company", company_results),
            ("👥 Hiring Agency", hiring_agency_results),
            ("👨‍💼 Recruiter", recruiter_results),
            ("👤 Candidate", candidate_results)
        ]
        
        for entity_name, results in entities:
            print(f"\n{entity_name}:")
            for operation, success in results.items():
                status = "✅ PASS" if success else "❌ FAIL"
                print(f"  {operation.upper()}: {status}")
        
        # Overall status
        all_results = [company_results, hiring_agency_results, recruiter_results, candidate_results]
        total_operations = sum(len(results) for results in all_results)
        successful_operations = sum(sum(results.values()) for results in all_results)
        
        print(f"\n📈 OVERALL RESULTS:")
        print(f"  Total Operations: {total_operations}")
        print(f"  Successful: {successful_operations}")
        print(f"  Failed: {total_operations - successful_operations}")
        print(f"  Success Rate: {(successful_operations/total_operations)*100:.1f}%")
        
        if successful_operations == total_operations:
            print("\n🎉 ALL CRUD OPERATIONS PASSED!")
        else:
            print(f"\n⚠️ {total_operations - successful_operations} operations failed")

if __name__ == "__main__":
    tester = CRUDTester()
    tester.run_all_tests()
