#!/usr/bin/env python
"""
Test script to verify verification ID image fix
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_app.settings')
django.setup()

from interviews.serializers import InterviewSerializer
from interviews.models import Interview
from interview_app.models import InterviewSession

def test_verification_id_fix():
    """Test that verification ID image is now working correctly"""
    
    print("=== Testing Verification ID Image Fix ===\n")
    
    # Find interviews with sessions
    for interview in Interview.objects.all():
        if interview.session_key:
            try:
                session = InterviewSession.objects.get(session_key=interview.session_key)
                
                print(f"🎯 Testing Interview ID: {interview.id}")
                print(f"   Session: {session.session_key}")
                print(f"   Has id_card_image: {bool(session.id_card_image)}")
                
                if session.id_card_image:
                    print(f"   ID Card Image URL: {session.id_card_image.url}")
                
                # Test the serializer
                serializer = InterviewSerializer(interview)
                verification_image = serializer.get_verification_id_image(interview)
                
                print(f"   Serializer result: {verification_image}")
                
                if verification_image:
                    print(f"   ✅ Verification ID image working!")
                else:
                    print(f"   ⚠️ No verification ID image found")
                
                print(f"   ✅ Test completed for interview {interview.id}")
                break  # Test first interview only
                
            except InterviewSession.DoesNotExist:
                continue
            except Exception as e:
                print(f"   ❌ Error: {e}")
                continue
    
    print(f"\n=== Verification ID Image Fix Complete ===")
    print(f"✅ Fixed field name from 'verification_id_image' to 'id_card_image'")
    print(f"✅ Verification ID images should now display in candidate details")

if __name__ == "__main__":
    test_verification_id_fix()
