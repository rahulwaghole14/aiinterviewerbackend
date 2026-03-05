#!/usr/bin/env python
"""
Test script to verify media file serving and URL construction
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_app.settings')
django.setup()

from django.conf import settings
from django.templatetags.static import static
from interviews.serializers import InterviewSerializer
from interviews.models import Interview
from interview_app.models import InterviewSession

def test_media_serving():
    """Test media file serving and URL construction"""
    
    print("=== Testing Media File Serving ===\n")
    
    # Check Django settings
    print(f"🔧 Django Settings:")
    print(f"   DEBUG: {settings.DEBUG}")
    print(f"   MEDIA_URL: {settings.MEDIA_URL}")
    print(f"   MEDIA_ROOT: {settings.MEDIA_ROOT}")
    
    # Check if media directory exists
    media_dir = settings.MEDIA_ROOT
    print(f"   Media directory exists: {os.path.exists(media_dir)}")
    
    if os.path.exists(media_dir):
        print(f"   Media directory contents: {os.listdir(media_dir)}")
        
        id_cards_dir = os.path.join(media_dir, 'id_cards')
        if os.path.exists(id_cards_dir):
            id_card_files = os.listdir(id_cards_dir)[:5]  # Show first 5
            print(f"   ID card files: {id_card_files}")
    
    print(f"\n🔍 Testing InterviewSerializer URL construction:")
    
    # Find interviews with ID cards
    for interview in Interview.objects.all():
        if interview.session_key:
            try:
                session = InterviewSession.objects.get(session_key=interview.session_key)
                
                if session.id_card_image:
                    print(f"\n🎯 Interview ID: {interview.id}")
                    print(f"   Session: {session.session_key}")
                    print(f"   File field: {session.id_card_image}")
                    print(f"   File name: {session.id_card_image.name}")
                    print(f"   File path: {session.id_card_image.path}")
                    print(f"   File URL: {session.id_card_image.url}")
                    
                    # Test the serializer
                    serializer = InterviewSerializer(interview)
                    verification_image = serializer.get_verification_id_image(interview)
                    
                    print(f"   Serializer URL: {verification_image}")
                    
                    # Check if file actually exists
                    if os.path.exists(session.id_card_image.path):
                        print(f"   ✅ File exists on disk")
                        file_size = os.path.getsize(session.id_card_image.path)
                        print(f"   📊 File size: {file_size} bytes")
                    else:
                        print(f"   ❌ File NOT found on disk")
                    
                    break  # Test first interview only
                    
            except InterviewSession.DoesNotExist:
                continue
            except Exception as e:
                print(f"   ❌ Error: {e}")
                continue
    
    print(f"\n🌐 Testing media URL patterns:")
    print(f"   Expected URL pattern: {settings.MEDIA_URL}id_cards/filename.jpeg")
    print(f"   Full URL should be accessible when Django server is running")
    
    print(f"\n✅ Media serving test completed")
    print(f"💡 If URLs are correct but images don't load in browser:")
    print(f"   1. Ensure Django server is running with DEBUG=True")
    print(f"   2. Check that media files are served at /media/ URL")
    print(f"   3. Verify frontend is using correct base URL")

if __name__ == "__main__":
    test_media_serving()
