
import threading
import time
from django.conf import settings
import atexit

# Make heavy imports optional
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

class SimpleVideoCamera:
    def __init__(self, session_id):
        self.session_id = session_id
        self.video = None
        self.is_running = False
        self.lock = threading.Lock()
        self.warnings = {"multiple_people": False, "phone_detected": False, "no_person": False, "low_concentration": False, "tab_switched": False, "no_person_warning_active": False, "excessive_noise": False, "multiple_speakers": False}
        
        if CV2_AVAILABLE:
            try:
                # Try to open camera
                self.video = cv2.VideoCapture(0)
                if not self.video.isOpened():
                    print("Warning: Could not open camera, using fallback")
                    self.video = None
                else:
                    print(f"Camera opened successfully for session {session_id}")
            except Exception as e:
                print(f"Camera error: {e}")
                self.video = None
        else:
            print("Warning: OpenCV not available, camera functionality disabled")
            self.video = None
    
    def get_frame(self):
        if not CV2_AVAILABLE:
            return self._get_fallback_frame()
            
        if self.video and self.video.isOpened():
            try:
                ret, frame = self.video.read()
                if ret:
                    # Simple face detection
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                    
                    # Update warnings
                    with self.lock:
                        if len(faces) == 0:
                            self.warnings["no_person"] = True
                        elif len(faces) > 1:
                            self.warnings["multiple_people"] = True
                        else:
                            self.warnings["no_person"] = False
                            self.warnings["multiple_people"] = False
                    
                    # Encode frame
                    ret, jpeg = cv2.imencode('.jpg', frame)
                    return jpeg.tobytes()
                else:
                    return self._get_fallback_frame()
            except Exception as e:
                print(f"Frame capture error: {e}")
                return self._get_fallback_frame()
        else:
            return self._get_fallback_frame()
    
    def _get_fallback_frame(self):
        """Generate a simple fallback frame"""
        if not CV2_AVAILABLE or not NUMPY_AVAILABLE:
            # Return a simple placeholder image
            return b'placeholder_image_data'
            
        # Create a simple colored frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[:] = (100, 100, 100)  # Gray background
        
        # Add text
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(frame, "Camera Loading...", (200, 240), font, 1, (255, 255, 255), 2)
        cv2.putText(frame, "Session: " + str(self.session_id), (200, 280), font, 0.7, (255, 255, 255), 2)
        
        ret, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes()
    
    def get_latest_warnings(self):
        with self.lock:
            return self.warnings.copy()
    
    def set_tab_switch_status(self, status):
        with self.lock:
            self.warnings["tab_switched"] = status
    
    def cleanup(self):
        if self.video:
            self.video.release()
        print(f"Camera cleaned up for session {self.session_id}")

# Global camera instances
CAMERAS = {}
camera_lock = threading.Lock()

def get_camera_for_session(session_key):
    with camera_lock:
        if session_key in CAMERAS:
            return CAMERAS[session_key]
        
        # Create new camera instance
        camera = SimpleVideoCamera(session_key)
        CAMERAS[session_key] = camera
        return camera

def release_camera_for_session(session_key):
    with camera_lock:
        if session_key in CAMERAS:
            CAMERAS[session_key].cleanup()
            del CAMERAS[session_key]

# Cleanup on exit
def cleanup_all_cameras():
    with camera_lock:
        for camera in CAMERAS.values():
            camera.cleanup()
        CAMERAS.clear()

atexit.register(cleanup_all_cameras)
