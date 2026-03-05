#!/usr/bin/env python
"""
Test script to create proper media URLs for frontend consumption
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_app.settings')
django.setup()

from django.conf import settings
from interviews.serializers import InterviewSerializer
from interviews.models import Interview
from interview_app.models import InterviewSession

def test_media_urls():
    """Test and create proper media URLs for frontend"""
    
    print("=== Testing Media URLs for Frontend ===\n")
    
    # Find interviews with ID cards
    for interview in Interview.objects.all():
        if interview.session_key:
            try:
                session = InterviewSession.objects.get(session_key=interview.session_key)
                
                if session.id_card_image:
                    print(f"🎯 Interview ID: {interview.id}")
                    print(f"   Session: {session.session_key}")
                    
                    # Test the serializer
                    serializer = InterviewSerializer(interview)
                    verification_image = serializer.get_verification_id_image(interview)
                    
                    print(f"   📸 Verification Image URL: {verification_image}")
                    
                    # Create different URL formats for testing
                    base_url = "http://127.0.0.1:8000"  # Default Django dev server
                    
                    urls_to_test = [
                        f"{base_url}{verification_image}",  # Full URL with base
                        verification_image,  # Relative URL
                        f"{verification_image.lstrip('/')}",  # Without leading slash
                    ]
                    
                    print(f"\n   🌐 URL Formats to Test:")
                    for i, url in enumerate(urls_to_test, 1):
                        print(f"      {i}. {url}")
                    
                    # Check file path
                    print(f"\n   📁 File Details:")
                    print(f"      File field: {session.id_card_image}")
                    print(f"      File name: {session.id_card_image.name}")
                    print(f"      File path: {session.id_card_image.path}")
                    print(f"      File exists: {os.path.exists(session.id_card_image.path)}")
                    
                    if os.path.exists(session.id_card_image.path):
                        file_size = os.path.getsize(session.id_card_image.path)
                        print(f"      File size: {file_size} bytes")
                    
                    break  # Test first interview only
                    
            except InterviewSession.DoesNotExist:
                continue
            except Exception as e:
                print(f"   ❌ Error: {e}")
                continue
    
    print(f"\n🔧 Frontend Integration Guide:")
    print(f"   1. Use relative URLs: '/media/id_cards/filename.jpeg'")
    print(f"   2. Django dev server serves media at: http://127.0.0.1:8000/media/")
    print(f"   3. In production, configure media serving (nginx/AWS S3)")
    print(f"   4. Ensure CORS allows media file access")
    
    print(f"\n📋 Django Media Configuration:")
    print(f"   DEBUG: {settings.DEBUG}")
    print(f"   MEDIA_URL: {settings.MEDIA_URL}")
    print(f"   MEDIA_ROOT: {settings.MEDIA_ROOT}")
    print(f"   Media files served: {'YES' if settings.DEBUG else 'NO (configure production serving)'}")
    
    print(f"\n✅ Media URL test completed")

if __name__ == "__main__":
    test_media_urls()
