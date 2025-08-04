#!/usr/bin/env python3
"""
Test script to show Bulk Resume Upload API response structure
Tests the API endpoint and shows what it responds with
"""

import requests
import json
import os
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

def log(message, level="INFO"):
    """Log messages with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def test_bulk_upload_endpoint():
    """Test the bulk upload endpoint to see its response structure"""
    log("=" * 60)
    log("TESTING BULK RESUME UPLOAD API RESPONSE STRUCTURE")
    log("=" * 60)
    
    # Test 1: Try without authentication
    log("Test 1: Testing without authentication...")
    try:
        response = requests.post(f"{API_BASE}/resumes/bulk-upload/")
        log(f"Response Status: {response.status_code}")
        if response.status_code == 401:
            log("✓ Correctly requires authentication")
            log(f"Response: {response.text}")
        else:
            log(f"Unexpected response: {response.text}")
    except Exception as e:
        log(f"✗ Exception: {str(e)}", "ERROR")
    
    # Test 2: Try with invalid data
    log("\nTest 2: Testing with invalid data...")
    try:
        response = requests.post(
            f"{API_BASE}/resumes/bulk-upload/",
            data={"invalid": "data"}
        )
        log(f"Response Status: {response.status_code}")
        log(f"Response: {response.text}")
    except Exception as e:
        log(f"✗ Exception: {str(e)}", "ERROR")
    
    # Test 3: Try with empty files
    log("\nTest 3: Testing with empty files...")
    try:
        response = requests.post(
            f"{API_BASE}/resumes/bulk-upload/",
            files={"files": ("test.txt", "", "text/plain")}
        )
        log(f"Response Status: {response.status_code}")
        log(f"Response: {response.text}")
    except Exception as e:
        log(f"✗ Exception: {str(e)}", "ERROR")
    
    # Test 4: Check the endpoint documentation
    log("\nTest 4: Checking endpoint availability...")
    try:
        response = requests.get(f"{API_BASE}/resumes/")
        log(f"Resumes endpoint Status: {response.status_code}")
        if response.status_code == 200:
            log("✓ Resumes endpoint is accessible")
        else:
            log(f"Resumes endpoint response: {response.text}")
    except Exception as e:
        log(f"✗ Exception: {str(e)}", "ERROR")
    
    log("=" * 60)
    log("BULK UPLOAD API STRUCTURE TESTING COMPLETED")
    log("=" * 60)

def show_expected_response_structure():
    """Show the expected response structure based on the code analysis"""
    log("\n" + "=" * 60)
    log("EXPECTED BULK UPLOAD API RESPONSE STRUCTURE")
    log("=" * 60)
    
    expected_response = {
        "message": "Processed 3 resumes: 2 successful, 1 failed",
        "results": [
            {
                "success": True,
                "filename": "john_doe_resume.pdf",
                "resume_id": "550e8400-e29b-41d4-a716-446655440000",
                "extracted_data": {
                    "name": "John Doe",
                    "email": "john.doe@email.com",
                    "phone": "+1-555-123-4567",
                    "work_experience": 5
                }
            },
            {
                "success": False,
                "filename": "invalid_file.txt",
                "error_message": "Unsupported file type. Only PDF, DOCX, and DOC files are allowed."
            },
            {
                "success": True,
                "filename": "jane_smith_resume.pdf",
                "resume_id": "550e8400-e29b-41d4-a716-446655440001",
                "extracted_data": {
                    "name": "Jane Smith",
                    "email": "jane.smith@email.com",
                    "phone": "+1-555-987-6543",
                    "work_experience": 3
                }
            }
        ],
        "summary": {
            "total_files": 3,
            "successful": 2,
            "failed": 1
        }
    }
    
    log("Expected Success Response (200 OK):")
    log(json.dumps(expected_response, indent=2))
    
    log("\nExpected Error Response (400 Bad Request):")
    error_response = {
        "files": [
            "This field is required."
        ]
    }
    log(json.dumps(error_response, indent=2))
    
    log("\nExpected Authentication Error (401 Unauthorized):")
    auth_error = {
        "error": "Authentication credentials were not provided."
    }
    log(json.dumps(auth_error, indent=2))
    
    log("\nKey Features of the Bulk Upload API:")
    log("1. Accepts up to 10 files per request")
    log("2. Supports PDF, DOCX, and DOC file formats")
    log("3. Automatically extracts data from resumes")
    log("4. Provides detailed results for each file")
    log("5. Includes summary statistics")
    log("6. Requires authentication")
    log("7. Logs all operations")
    log("8. Sends notifications upon completion")

if __name__ == "__main__":
    try:
        test_bulk_upload_endpoint()
        show_expected_response_structure()
        log("\n🎉 Bulk upload API structure analysis completed!")
        
    except KeyboardInterrupt:
        log("\n⚠️  Testing interrupted by user")
    except Exception as e:
        log(f"\n💥 Unexpected error: {str(e)}", "ERROR") 