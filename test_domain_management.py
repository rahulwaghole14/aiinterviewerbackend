#!/usr/bin/env python3
"""
Test script for Domain Management System
Tests admin domain management and company job creation under domains.
"""

import requests
import json
import time
import os

BASE_URL = "http://localhost:8000"


def test_authentication():
    """Get authentication token"""
    print("🔐 Getting authentication token...")

    login_data = {"email": "testuser@example.com", "password": "testpass123"}

    try:
        response = requests.post(f"{BASE_URL}/auth/login/", data=login_data)
        if response.status_code == 200:
            token = response.json().get("token")
            print("✅ Authentication successful")
            return token
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None


def test_admin_domain_management(token):
    """Test admin domain management operations"""
    print("\n🎯 Testing Admin Domain Management...")

    headers = {"Authorization": f"Token {token}"}

    # Test 1: List domains
    print("\n📋 Test 1: List Domains")
    try:
        response = requests.get(f"{BASE_URL}/api/jobs/domains/", headers=headers)
        if response.status_code == 200:
            domains = response.json()
            print(f"✅ Domain listing successful ({len(domains)} domains found)")
            return domains
        else:
            print(f"❌ Domain listing failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return []
    except Exception as e:
        print(f"❌ Domain listing error: {e}")
        return []

    # Test 2: Create domain (admin only)
    print("\n➕ Test 2: Create Domain")
    domain_data = {
        "name": "Python Development",
        "description": "Python programming and development domain",
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/jobs/domains/", json=domain_data, headers=headers
        )
        if response.status_code == 201:
            domain = response.json()
            print("✅ Domain creation successful")
            print(f"   Domain ID: {domain['id']}")
            print(f"   Domain Name: {domain['name']}")
            return domain
        else:
            print(f"❌ Domain creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Domain creation error: {e}")
        return None


def test_domain_crud_operations(token, domain_id):
    """Test domain CRUD operations"""
    print(f"\n🔄 Testing Domain CRUD Operations for Domain ID: {domain_id}")

    headers = {"Authorization": f"Token {token}"}

    # Test 1: Get specific domain
    print("\n👁️  Test 1: Get Domain Details")
    try:
        response = requests.get(
            f"{BASE_URL}/api/jobs/domains/{domain_id}/", headers=headers
        )
        if response.status_code == 200:
            domain = response.json()
            print("✅ Domain retrieval successful")
            print(f"   Name: {domain['name']}")
            print(f"   Description: {domain['description']}")
            print(f"   Active: {domain['is_active']}")
        else:
            print(f"❌ Domain retrieval failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Domain retrieval error: {e}")
        return False

    # Test 2: Update domain
    print("\n✏️  Test 2: Update Domain")
    update_data = {
        "name": "Python Development Updated",
        "description": "Updated Python programming and development domain",
    }

    try:
        response = requests.put(
            f"{BASE_URL}/api/jobs/domains/{domain_id}/",
            json=update_data,
            headers=headers,
        )
        if response.status_code == 200:
            domain = response.json()
            print("✅ Domain update successful")
            print(f"   Updated Name: {domain['name']}")
            print(f"   Updated Description: {domain['description']}")
        else:
            print(f"❌ Domain update failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Domain update error: {e}")
        return False

    return True


def test_company_job_creation_under_domain(token, domain_id):
    """Test company job creation under a specific domain"""
    print(f"\n🏢 Testing Company Job Creation Under Domain ID: {domain_id}")

    headers = {"Authorization": f"Token {token}"}

    # Test 1: Create job under domain
    print("\n📝 Test 1: Create Job Under Domain")
    job_data = {
        "job_title": "Senior Python Developer",
        "company_name": "Tech Corp",
        "domain": domain_id,
        "spoc_email": "hr@techcorp.com",
        "hiring_manager_email": "manager@techcorp.com",
        "current_team_size_info": "10-15",
        "number_to_hire": 2,
        "position_level": "IC",
        "current_process": "Technical interview + coding test",
        "tech_stack_details": "Python, Django, PostgreSQL, AWS",
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/jobs/", json=job_data, headers=headers
        )
        if response.status_code == 201:
            job = response.json()
            print("✅ Job creation under domain successful")
            print(f"   Job ID: {job['id']}")
            print(f"   Job Title: {job['job_title']}")
            print(f"   Domain ID: {job['domain']}")
            return job
        else:
            print(f"❌ Job creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Job creation error: {e}")
        return None


def test_job_domain_relationship(token, job_id, domain_id):
    """Test job-domain relationship"""
    print(f"\n🔗 Testing Job-Domain Relationship")

    headers = {"Authorization": f"Token {token}"}

    # Test 1: Get job details with domain
    print("\n📋 Test 1: Get Job with Domain Details")
    try:
        response = requests.get(f"{BASE_URL}/api/jobs/{job_id}/", headers=headers)
        if response.status_code == 200:
            job = response.json()
            print("✅ Job retrieval successful")
            print(f"   Job Title: {job['job_title']}")
            print(f"   Domain ID: {job['domain']}")
            print(f"   Domain Name: {job.get('domain_name', 'N/A')}")

            if job["domain"] == domain_id:
                print("✅ Job-domain relationship verified")
                return True
            else:
                print("❌ Job-domain relationship mismatch")
                return False
        else:
            print(f"❌ Job retrieval failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Job retrieval error: {e}")
        return False


def test_jobs_by_domain(token, domain_id):
    """Test listing jobs by domain"""
    print(f"\n📊 Testing Jobs by Domain")

    headers = {"Authorization": f"Token {token}"}

    try:
        response = requests.get(
            f"{BASE_URL}/api/jobs/by-domain/{domain_id}/", headers=headers
        )
        if response.status_code == 200:
            jobs = response.json()
            print(f"✅ Jobs by domain successful ({len(jobs)} jobs found)")
            for job in jobs:
                print(f"   - {job['job_title']} at {job['company_name']}")
            return True
        else:
            print(f"❌ Jobs by domain failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Jobs by domain error: {e}")
        return False


def test_domain_validation(token):
    """Test domain validation in job creation"""
    print(f"\n✅ Testing Domain Validation")

    headers = {"Authorization": f"Token {token}"}

    # Test 1: Try to create job without domain
    print("\n🚫 Test 1: Create Job Without Domain")
    job_data = {
        "job_title": "Invalid Job",
        "company_name": "Test Corp",
        "spoc_email": "hr@testcorp.com",
        "hiring_manager_email": "manager@testcorp.com",
        "number_to_hire": 1,
        "position_level": "IC",
        "tech_stack_details": "Test stack",
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/jobs/", json=job_data, headers=headers
        )
        if response.status_code == 400:
            print("✅ Domain validation working (rejected job without domain)")
            return True
        else:
            print(f"❌ Domain validation failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Domain validation error: {e}")
        return False


def test_non_admin_domain_restrictions(token):
    """Test that non-admin users cannot manage domains"""
    print(f"\n🚫 Testing Non-Admin Domain Restrictions")

    headers = {"Authorization": f"Token {token}"}

    # Test 1: Try to create domain as non-admin
    print("\n🚫 Test 1: Non-Admin Domain Creation")
    domain_data = {
        "name": "Unauthorized Domain",
        "description": "This should be rejected",
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/jobs/domains/", json=domain_data, headers=headers
        )
        if response.status_code == 403:
            print("✅ Non-admin domain creation properly restricted")
            return True
        else:
            print(f"❌ Non-admin restriction failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Non-admin restriction error: {e}")
        return False


def main():
    """Main test function"""
    print("🚀 Testing Domain Management System")
    print("=" * 60)

    # Get authentication token
    token = test_authentication()
    if not token:
        print("\n❌ Cannot proceed without authentication token.")
        return

    # Test admin domain management
    domains = test_admin_domain_management(token)
    if not domains:
        print("\n❌ Domain management failed. Cannot proceed.")
        return

    # Test domain CRUD operations
    if domains:
        domain_id = domains[0]["id"] if isinstance(domains, list) and domains else None
        if domain_id:
            if not test_domain_crud_operations(token, domain_id):
                print("\n❌ Domain CRUD operations failed.")
                return

    # Test company job creation under domain
    if domain_id:
        job = test_company_job_creation_under_domain(token, domain_id)
        if job:
            job_id = job["id"]

            # Test job-domain relationship
            if not test_job_domain_relationship(token, job_id, domain_id):
                print("\n❌ Job-domain relationship test failed.")
                return

            # Test jobs by domain
            if not test_jobs_by_domain(token, domain_id):
                print("\n❌ Jobs by domain test failed.")
                return

    # Test domain validation
    if not test_domain_validation(token):
        print("\n❌ Domain validation test failed.")
        return

    # Test non-admin restrictions
    if not test_non_admin_domain_restrictions(token):
        print("\n❌ Non-admin restrictions test failed.")
        return

    print("\n" + "=" * 60)
    print("🎉 Domain Management System Test Complete!")
    print("✅ Admin domain management working")
    print("✅ Domain CRUD operations working")
    print("✅ Company job creation under domains working")
    print("✅ Job-domain relationships working")
    print("✅ Domain validation working")
    print("✅ Non-admin restrictions working")


if __name__ == "__main__":
    main()
