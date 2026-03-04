#!/usr/bin/env python
import requests
import json

# Test the video URL accessibility
base_url = "http://localhost:8000"
video_url = "/media/screen_recordings/screen_0b236cb2f26a4df0b3f45852aad3eff7_20260304_063133.webm"
full_url = f"{base_url}{video_url}"

print(f"Testing video URL: {full_url}")

try:
    response = requests.head(full_url)
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type', 'Not specified')}")
    print(f"Content-Length: {response.headers.get('content-length', 'Not specified')}")
    
    if response.status_code == 200:
        print("✅ Video URL is accessible!")
    else:
        print(f"❌ Video URL returned status: {response.status_code}")
        
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to server. Make sure the Django server is running on port 8000.")
except Exception as e:
    print(f"❌ Error: {e}")

# Also test the interviews API (without authentication)
print("\n" + "="*50)
print("Testing interviews API endpoint...")

api_url = f"{base_url}/api/interviews/"
try:
    response = requests.get(api_url)
    print(f"API Status Code: {response.status_code}")
    if response.status_code == 401:
        print("✅ API requires authentication (expected)")
    elif response.status_code == 200:
        print("⚠️ API is accessible without authentication")
    else:
        print(f"❌ Unexpected status: {response.status_code}")
except Exception as e:
    print(f"❌ API Error: {e}")
