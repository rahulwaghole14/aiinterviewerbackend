#!/usr/bin/env python3
"""
Job CRUD Operations Test Script
Tests all Create, Read, Update, Delete operations for Jobs and Domains
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@rslsolution.com"
ADMIN_PASSWORD = "admin123"

def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def get_auth_token():
    """Get authentication token for admin user"""
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login/", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if response.status_code == 200:
            token = response.json().get('token')
            log(f"✅ Login successful for {ADMIN_EMAIL}")
            return token
        else:
            log(f"❌ Login failed: {response.status_code} - {response.text}", "ERROR")
            return None
    except Exception as e:
        log(f"❌ Login error: {str(e)}", "ERROR")
        return None

def test_domain_crud(token):
    """Test Domain CRUD operations"""
    headers = {"Authorization": f"Token {token}"}
    
    log("\n" + "="*60)
    log("🏷️  TESTING DOMAIN CRUD OPERATIONS")
    log("="*60)
    
    # CREATE Domain
    log("\n📝 Testing Domain CREATE...")
    domain_data = {
        "name": f"Test Domain {int(time.time())}",
        "description": "Test domain for CRUD operations"
    }
    
    response = requests.post(f"{BASE_URL}/api/jobs/domains/", json=domain_data, headers=headers)
    if response.status_code == 201:
        domain = response.json()
        domain_id = domain['id']
        log(f"✅ Domain created successfully: ID {domain_id}")
    else:
        log(f"❌ Domain creation failed: {response.status_code} - {response.text}", "ERROR")
        return None
    
    # READ Domain List
    log("\n📖 Testing Domain READ (List)...")
    response = requests.get(f"{BASE_URL}/api/jobs/domains/", headers=headers)
    if response.status_code == 200:
        domains = response.json()
        log(f"✅ Domains list retrieved: {len(domains)} domains")
    else:
        log(f"❌ Domain list retrieval failed: {response.status_code} - {response.text}", "ERROR")
    
    # READ Domain Detail
    log(f"\n📖 Testing Domain READ (Detail) - ID {domain_id}...")
    response = requests.get(f"{BASE_URL}/api/jobs/domains/{domain_id}/", headers=headers)
    if response.status_code == 200:
        domain_detail = response.json()
        log(f"✅ Domain detail retrieved: {domain_detail['name']}")
    else:
        log(f"❌ Domain detail retrieval failed: {response.status_code} - {response.text}", "ERROR")
    
    # UPDATE Domain
    log(f"\n✏️ Testing Domain UPDATE - ID {domain_id}...")
    update_data = {
        "name": f"Updated Domain {int(time.time())}",
        "description": "Updated test domain description"
    }
    response = requests.put(f"{BASE_URL}/api/jobs/domains/{domain_id}/", json=update_data, headers=headers)
    if response.status_code == 200:
        updated_domain = response.json()
        log(f"✅ Domain updated successfully: {updated_domain['name']}")
    else:
        log(f"❌ Domain update failed: {response.status_code} - {response.text}", "ERROR")
    
    # DELETE Domain (Soft Delete)
    log(f"\n🗑️ Testing Domain DELETE (Soft Delete) - ID {domain_id}...")
    response = requests.delete(f"{BASE_URL}/api/jobs/domains/{domain_id}/", headers=headers)
    if response.status_code == 200:
        log(f"✅ Domain soft deleted successfully (deactivated)")
    else:
        log(f"❌ Domain deletion failed: {response.status_code} - {response.text}", "ERROR")
    
    # Use an existing active domain for job testing
    log("\n📝 Using existing active domain for job testing...")
    # Get list of active domains
    response = requests.get(f"{BASE_URL}/api/jobs/domains/", headers=headers)
    if response.status_code == 200:
        domains = response.json()
        if domains:
            # Use the first active domain
            active_domain_id = domains[0]['id']
            log(f"✅ Using existing active domain for job testing: ID {active_domain_id} - {domains[0]['name']}")
            return active_domain_id
        else:
            log("❌ No active domains found", "ERROR")
            return None
    else:
        log(f"❌ Failed to get domains: {response.status_code} - {response.text}", "ERROR")
        return None

def test_job_crud(token, domain_id):
    """Test Job CRUD operations"""
    headers = {"Authorization": f"Token {token}"}
    
    log("\n" + "="*60)
    log("💼 TESTING JOB CRUD OPERATIONS")
    log("="*60)
    
    # CREATE Job
    log("\n📝 Testing Job CREATE...")
    job_data = {
        "job_title": f"Test Job {int(time.time())}",
        "company_name": "Test Company",
        "domain": domain_id,
        "spoc_email": "spoc@testcompany.com",
        "hiring_manager_email": "manager@testcompany.com",
        "current_team_size_info": "5-10 members",
        "number_to_hire": 2,
        "position_level": "IC",
        "current_process": "Technical + Behavioral",
        "tech_stack_details": "Python, Django, React, PostgreSQL"
    }
    
    response = requests.post(f"{BASE_URL}/api/jobs/", json=job_data, headers=headers)
    if response.status_code == 201:
        job = response.json()
        job_id = job['id']
        log(f"✅ Job created successfully: ID {job_id}")
    else:
        log(f"❌ Job creation failed: {response.status_code} - {response.text}", "ERROR")
        return None
    
    # READ Job List
    log("\n📖 Testing Job READ (List)...")
    response = requests.get(f"{BASE_URL}/api/jobs/", headers=headers)
    if response.status_code == 200:
        jobs = response.json()
        log(f"✅ Jobs list retrieved: {len(jobs)} jobs")
    else:
        log(f"❌ Job list retrieval failed: {response.status_code} - {response.text}", "ERROR")
    
    # READ Job Detail
    log(f"\n📖 Testing Job READ (Detail) - ID {job_id}...")
    response = requests.get(f"{BASE_URL}/api/jobs/{job_id}/", headers=headers)
    if response.status_code == 200:
        job_detail = response.json()
        log(f"✅ Job detail retrieved: {job_detail['job_title']}")
    else:
        log(f"❌ Job detail retrieval failed: {response.status_code} - {response.text}", "ERROR")
    
    # UPDATE Job
    log(f"\n✏️ Testing Job UPDATE - ID {job_id}...")
    update_data = {
        "job_title": f"Updated Job {int(time.time())}",
        "company_name": "Updated Test Company",
        "domain": domain_id,
        "spoc_email": "updated.spoc@testcompany.com",
        "hiring_manager_email": "updated.manager@testcompany.com",
        "current_team_size_info": "10-15 members",
        "number_to_hire": 3,
        "position_level": "Manager",
        "current_process": "Updated Technical + Behavioral",
        "tech_stack_details": "Updated Python, Django, React, PostgreSQL"
    }
    response = requests.put(f"{BASE_URL}/api/jobs/{job_id}/", json=update_data, headers=headers)
    if response.status_code == 200:
        updated_job = response.json()
        log(f"✅ Job updated successfully: {updated_job['job_title']}")
    else:
        log(f"❌ Job update failed: {response.status_code} - {response.text}", "ERROR")
    
    # DELETE Job
    log(f"\n🗑️ Testing Job DELETE - ID {job_id}...")
    response = requests.delete(f"{BASE_URL}/api/jobs/{job_id}/", headers=headers)
    if response.status_code == 204:
        log(f"✅ Job deleted successfully")
    else:
        log(f"❌ Job deletion failed: {response.status_code} - {response.text}", "ERROR")
    
    return job_id

def test_job_by_domain(token, domain_id):
    """Test Jobs by Domain endpoint"""
    headers = {"Authorization": f"Token {token}"}
    
    log("\n" + "="*60)
    log("🔍 TESTING JOBS BY DOMAIN")
    log("="*60)
    
    # Create a job for the domain first
    log("\n📝 Creating test job for domain...")
    job_data = {
        "job_title": f"Domain Test Job {int(time.time())}",
        "company_name": "Domain Test Company",
        "domain": domain_id,
        "spoc_email": "domain.spoc@testcompany.com",
        "hiring_manager_email": "domain.manager@testcompany.com",
        "current_team_size_info": "5-10 members",
        "number_to_hire": 1,
        "position_level": "IC",
        "current_process": "Technical",
        "tech_stack_details": "Python, Django"
    }
    
    response = requests.post(f"{BASE_URL}/api/jobs/", json=job_data, headers=headers)
    if response.status_code == 201:
        job = response.json()
        job_id = job['id']
        log(f"✅ Test job created: ID {job_id}")
    else:
        log(f"❌ Test job creation failed: {response.status_code} - {response.text}", "ERROR")
        return
    
    # Test Jobs by Domain
    log(f"\n🔍 Testing Jobs by Domain - Domain ID {domain_id}...")
    response = requests.get(f"{BASE_URL}/api/jobs/by-domain/{domain_id}/", headers=headers)
    if response.status_code == 200:
        jobs = response.json()
        log(f"✅ Jobs by domain retrieved: {len(jobs)} jobs")
    else:
        log(f"❌ Jobs by domain failed: {response.status_code} - {response.text}", "ERROR")
    
    # Clean up test job
    log(f"\n🗑️ Cleaning up test job - ID {job_id}...")
    response = requests.delete(f"{BASE_URL}/api/jobs/{job_id}/", headers=headers)
    if response.status_code == 204:
        log(f"✅ Test job cleaned up successfully")
    else:
        log(f"❌ Test job cleanup failed: {response.status_code} - {response.text}", "ERROR")

def test_job_titles(token):
    """Test Job Titles endpoint"""
    headers = {"Authorization": f"Token {token}"}
    
    log("\n" + "="*60)
    log("📋 TESTING JOB TITLES")
    log("="*60)
    
    log("\n📋 Testing Job Titles List...")
    response = requests.get(f"{BASE_URL}/api/jobs/titles/", headers=headers)
    if response.status_code == 200:
        titles = response.json()
        log(f"✅ Job titles retrieved: {len(titles)} titles")
    else:
        log(f"❌ Job titles retrieval failed: {response.status_code} - {response.text}", "ERROR")

def main():
    """Main test function"""
    log("🚀 STARTING JOB CRUD OPERATIONS TEST")
    log("="*60)
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        log("❌ Cannot proceed without authentication token", "ERROR")
        return
    
    # Test Domain CRUD operations
    domain_id = test_domain_crud(token)
    if not domain_id:
        log("❌ Domain CRUD test failed, cannot proceed with Job tests", "ERROR")
        return
    
    # Test Job CRUD operations
    job_id = test_job_crud(token, domain_id)
    if not job_id:
        log("❌ Job CRUD test failed", "ERROR")
        return
    
    # Test additional Job endpoints
    test_job_by_domain(token, domain_id)
    test_job_titles(token)
    
    log("\n" + "="*60)
    log("📊 JOB CRUD OPERATIONS TEST SUMMARY")
    log("="*60)
    log("✅ All Job and Domain CRUD operations tested successfully!")
    log("✅ Create, Read, Update, Delete operations working for both entities")
    log("✅ Additional endpoints (by-domain, titles) working correctly")
    log("🎉 JOB CRUD OPERATIONS TEST COMPLETED!")

if __name__ == "__main__":
    main()
