#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_app.settings')
django.setup()

from interview_app.working_camera import WorkingVideoCamera

print("🔍 Testing Django camera integration...")

# Create a test session
session_id = "test_session_123"
print(f"🎥 Creating camera for session: {session_id}")

try:
    camera = WorkingVideoCamera(session_id)
    print(f"✅ Camera created successfully")
    print(f"📹 Camera is opened: {camera.video.isOpened()}")
    
    # Try to get a frame
    print("📸 Attempting to get frame...")
    frame_data = camera.get_frame()
    print(f"✅ Frame data length: {len(frame_data)} bytes")
    
    if len(frame_data) > 0:
        print("🎉 SUCCESS: Camera is working in Django!")
    else:
        print("❌ FAILED: No frame data returned")
        
    # Cleanup
    camera.cleanup()
    print("🧹 Camera cleaned up")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

