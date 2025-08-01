#!/usr/bin/env python3
"""
Test script for Bulk Resume Processing API
This demonstrates how the new bulk upload functionality works.
"""

import requests
import json
from pathlib import Path

# API Base URL
BASE_URL = "http://localhost:8000"

def test_bulk_resume_upload():
    """
    Test the bulk resume upload endpoint
    """
    print("🧪 Testing Bulk Resume Upload API")
    print("=" * 50)
    
    # Endpoint
    url = f"{BASE_URL}/api/resumes/bulk-upload/"
    
    # Sample files (you would replace these with actual files)
    files = {
        'files': [
            ('resume1.pdf', open('sample_resume1.pdf', 'rb'), 'application/pdf'),
            ('resume2.docx', open('sample_resume2.docx', 'rb'), 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
            ('resume3.pdf', open('sample_resume3.pdf', 'rb'), 'application/pdf'),
        ]
    }
    
    # Headers with authentication
    headers = {
        'Authorization': 'Token your-auth-token-here'
    }
    
    try:
        response = requests.post(url, files=files, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Bulk upload successful!")
            print(f"📊 Summary: {result['summary']}")
            print("\n📋 Results:")
            for i, res in enumerate(result['results'], 1):
                if res['success']:
                    print(f"  {i}. ✅ {res['filename']} - {res['extracted_data']}")
                else:
                    print(f"  {i}. ❌ {res['filename']} - {res['error_message']}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure Django server is running.")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_single_resume_upload():
    """
    Test the single resume upload endpoint
    """
    print("\n🧪 Testing Single Resume Upload API")
    print("=" * 50)
    
    url = f"{BASE_URL}/api/resumes/"
    
    files = {
        'file': ('resume.pdf', open('sample_resume.pdf', 'rb'), 'application/pdf')
    }
    
    headers = {
        'Authorization': 'Token your-auth-token-here'
    }
    
    try:
        response = requests.post(url, files=files, headers=headers)
        
        if response.status_code == 201:
            result = response.json()
            print("✅ Single upload successful!")
            print(f"📄 Resume ID: {result['id']}")
            print(f"📝 Parsed text length: {len(result['parsed_text'])} characters")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure Django server is running.")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_resume_listing():
    """
    Test the resume listing endpoint
    """
    print("\n🧪 Testing Resume Listing API")
    print("=" * 50)
    
    url = f"{BASE_URL}/api/resumes/"
    
    headers = {
        'Authorization': 'Token your-auth-token-here'
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Resume listing successful!")
            print(f"📊 Total resumes: {len(result)}")
            for i, resume in enumerate(result, 1):
                print(f"  {i}. {resume['id']} - {resume['file']}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure Django server is running.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 AI Interviewer Platform - API Testing")
    print("=" * 60)
    
    # Test all endpoints
    test_bulk_resume_upload()
    test_single_resume_upload()
    test_resume_listing()
    
    print("\n" + "=" * 60)
    print("📋 API Endpoints Summary:")
    print("  • POST /api/resumes/bulk-upload/ - Upload multiple resumes")
    print("  • POST /api/resumes/ - Upload single resume")
    print("  • GET  /api/resumes/ - List all resumes")
    print("  • GET  /api/resumes/{id}/ - Get specific resume")
    print("  • PUT  /api/resumes/{id}/ - Update resume")
    print("  • DELETE /api/resumes/{id}/ - Delete resume") 