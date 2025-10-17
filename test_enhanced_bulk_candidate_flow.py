#!/usr/bin/env python3
"""
Test script for enhanced bulk candidate creation flow
Matches the frontend flow: Extract → Preview/Edit → Submit
"""

import requests
import os
import json
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"


def test_enhanced_bulk_candidate_flow():
    """Test the enhanced bulk candidate creation flow"""

    print("🧪 Testing Enhanced Bulk Candidate Creation Flow")
    print("=" * 60)

    # Step 1: Login to get authentication token
    print("\n1️⃣ Authenticating...")
    login_data = {"email": "company_test@example.com", "password": "password123"}

    response = requests.post(f"{API_BASE}/auth/login/", json=login_data)
    print(f"   Login Status: {response.status_code}")

    if response.status_code != 200:
        print("   ❌ Login failed")
        return

    token = response.json().get("token")
    headers = {"Authorization": f"Token {token}", "Content-Type": "multipart/form-data"}

    print("   ✅ Login successful")

    # Step 2: Test bulk extraction (Step 1 of frontend flow)
    print("\n2️⃣ Testing Bulk Data Extraction...")

    # Prepare test files (using existing test resumes)
    test_files = []
    media_dir = Path("media/resumes")

    if media_dir.exists():
        # Get first 3 PDF files for testing
        pdf_files = list(media_dir.glob("*.pdf"))[:3]
        for pdf_file in pdf_files:
            test_files.append(
                (
                    "resume_files",
                    (pdf_file.name, open(pdf_file, "rb"), "application/pdf"),
                )
            )

    if not test_files:
        print("   ⚠️ No test files found in media/resumes/")
        print("   Creating dummy test...")
        # Create a dummy test with minimal data
        test_data = {"domain": "Data Science", "role": "Data Scientist"}
        response = requests.post(
            f"{API_BASE}/candidates/bulk-create/?step=extract",
            data=test_data,
            headers={"Authorization": f"Token {token}"},
        )
        print(f"   Bulk Extract Status: {response.status_code}")
        if response.status_code == 400:
            print("   ✅ Validation working (expected error for missing files)")
            print(f"   Response: {response.json()}")
        return

    # Prepare form data
    form_data = {"domain": "Data Science", "role": "Data Scientist"}

    print(f"   Uploading {len(test_files)} files for extraction...")

    # Make the extraction request using the correct endpoint
    response = requests.post(
        f"{API_BASE}/candidates/bulk-create/?step=extract",
        data=form_data,
        files=test_files,
        headers={"Authorization": f"Token {token}"},
    )

    print(f"   Bulk Extract Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print("   ✅ Bulk data extraction successful!")
        print(f"   Message: {result.get('message')}")
        print(f"   Domain: {result.get('domain')}")
        print(f"   Role: {result.get('role')}")

        summary = result.get("summary", {})
        print(f"   Total Files: {summary.get('total_files')}")
        print(f"   Successful Extractions: {summary.get('successful_extractions')}")
        print(f"   Failed Extractions: {summary.get('failed_extractions')}")

        # Show extracted candidates
        extracted_candidates = result.get("extracted_candidates", [])
        print("\n   📋 Extracted Candidates (for frontend preview):")
        for i, candidate in enumerate(extracted_candidates, 1):
            if candidate.get("can_edit"):
                extracted_data = candidate.get("extracted_data", {})
                print(f"   {i}. ✅ {candidate.get('filename')}")
                print(f"      Name: {extracted_data.get('name', 'Not found')}")
                print(f"      Email: {extracted_data.get('email', 'Not found')}")
                print(f"      Phone: {extracted_data.get('phone', 'Not found')}")
                print(
                    f"      Experience: {extracted_data.get('work_experience', 'Not found')} years"
                )
            else:
                print(
                    f"   {i}. ❌ {candidate.get('filename')} -> Error: {candidate.get('error')}"
                )

        # Step 3: Simulate frontend editing and submit (Step 2 of frontend flow)
        print("\n3️⃣ Testing Bulk Candidate Submission (after editing)...")

        # Simulate edited data (in real frontend, user would edit this)
        edited_candidates = []
        for candidate in extracted_candidates:
            if candidate.get("can_edit"):
                extracted_data = candidate.get("extracted_data", {})
                # Simulate user editing the data
                edited_data = {
                    "name": extracted_data.get("name", "Unknown"),
                    "email": extracted_data.get("email", ""),
                    "phone": extracted_data.get("phone", ""),
                    "work_experience": extracted_data.get("work_experience", 0),
                }

                # Simulate user making some edits
                if not edited_data["name"]:
                    edited_data["name"] = "Unknown Candidate"
                if not edited_data["email"]:
                    edited_data["email"] = "unknown@example.com"

                edited_candidates.append(
                    {"filename": candidate.get("filename"), "edited_data": edited_data}
                )

        # Prepare submission data
        submission_data = {
            "domain": "Data Science",
            "role": "Data Scientist",
            "candidates": edited_candidates,
        }

        print(f"   Submitting {len(edited_candidates)} edited candidates...")

        # Make the submission request using the correct endpoint
        response = requests.post(
            f"{API_BASE}/candidates/bulk-create/?step=submit",
            json=submission_data,
            headers={
                "Authorization": f"Token {token}",
                "Content-Type": "application/json",
            },
        )

        print(f"   Bulk Submit Status: {response.status_code}")

        if response.status_code == 201:
            result = response.json()
            print("   ✅ Bulk candidate submission successful!")
            print(f"   Message: {result.get('message')}")

            summary = result.get("summary", {})
            print(f"   Total Candidates: {summary.get('total_candidates')}")
            print(f"   Successful Creations: {summary.get('successful_creations')}")
            print(f"   Failed Creations: {summary.get('failed_creations')}")

            # Show individual results
            results = result.get("results", [])
            print("\n   📋 Individual Results:")
            for i, res in enumerate(results, 1):
                if res.get("success"):
                    print(
                        f"   {i}. ✅ {res.get('filename')} -> Candidate: {res.get('candidate_name')}"
                    )
                else:
                    print(
                        f"   {i}. ❌ {res.get('filename')} -> Error: {res.get('error_message')}"
                    )

        else:
            print("   ❌ Bulk candidate submission failed")
            print(f"   Response: {response.text}")

    else:
        print("   ❌ Bulk data extraction failed")
        print(f"   Response: {response.text}")

    # Step 4: Verify candidates were created
    print("\n4️⃣ Verifying created candidates...")

    response = requests.get(
        f"{API_BASE}/candidates/", headers={"Authorization": f"Token {token}"}
    )

    if response.status_code == 200:
        candidates = response.json()
        print(f"   Total candidates in system: {len(candidates)}")

        # Show recent candidates
        recent_candidates = candidates[-5:] if len(candidates) > 5 else candidates
        print("\n   📋 Recent Candidates:")
        for candidate in recent_candidates:
            print(
                f"   - {candidate.get('full_name', 'Unknown')} ({candidate.get('domain')}) - {candidate.get('status')}"
            )

    # Clean up test files
    for _, file_tuple in test_files:
        if len(file_tuple) > 1:
            file_tuple[1].close()

    print("\n✅ Enhanced bulk candidate flow test completed!")


def test_enhanced_flow_validation():
    """Test validation for enhanced bulk candidate flow"""

    print("\n🧪 Testing Enhanced Bulk Candidate Flow Validation")
    print("=" * 60)

    # Step 1: Login
    login_data = {"email": "company_test@example.com", "password": "password123"}

    response = requests.post(f"{API_BASE}/auth/login/", json=login_data)
    if response.status_code != 200:
        print("   ❌ Login failed")
        return

    token = response.json().get("token")
    headers = {"Authorization": f"Token {token}"}

    # Test 1: Missing domain in extraction
    print("\n1️⃣ Testing missing domain in extraction...")
    test_data = {"role": "Data Scientist"}
    response = requests.post(
        f"{API_BASE}/candidates/bulk-create/?step=extract",
        data=test_data,
        headers=headers,
    )
    print(f"   Status: {response.status_code} (Expected: 400)")
    if response.status_code == 400:
        print("   ✅ Validation working")

    # Test 2: Missing candidates in submission
    print("\n2️⃣ Testing missing candidates in submission...")
    test_data = {"domain": "Data Science", "role": "Data Scientist"}
    response = requests.post(
        f"{API_BASE}/candidates/bulk-create/?step=submit",
        json=test_data,
        headers=headers,
    )
    print(f"   Status: {response.status_code} (Expected: 400)")
    if response.status_code == 400:
        print("   ✅ Validation working")

    # Test 3: Invalid candidate data in submission
    print("\n3️⃣ Testing invalid candidate data in submission...")
    test_data = {
        "domain": "Data Science",
        "role": "Data Scientist",
        "candidates": [{"filename": "test.pdf", "edited_data": {}}],  # Missing name
    }
    response = requests.post(
        f"{API_BASE}/candidates/bulk-create/?step=submit",
        json=test_data,
        headers=headers,
    )
    print(f"   Status: {response.status_code} (Expected: 400)")
    if response.status_code == 400:
        print("   ✅ Validation working")

    print("\n✅ Enhanced flow validation tests completed!")


if __name__ == "__main__":
    print("🚀 Starting Enhanced Bulk Candidate Creation Flow Tests")
    print("=" * 80)

    # Test validation first
    test_enhanced_flow_validation()

    # Test actual functionality
    test_enhanced_bulk_candidate_flow()

    print("\n🎉 All enhanced flow tests completed!")
