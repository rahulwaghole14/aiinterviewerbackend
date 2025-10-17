import time
import cv2
import numpy as np


class _VideoCapture:
    def __init__(self, camera_index=0):
        print(f"🎥 Attempting to open camera {camera_index}")
        self.cap = None
        
        try:
            # Try DirectShow backend first (works on Windows)
            self.cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
            
            # If DirectShow fails, try default backend
            if not self.cap.isOpened():
                print(f"❌ DirectShow failed for camera {camera_index}, trying default...")
                self.cap = cv2.VideoCapture(camera_index)
            
            if not self.cap.isOpened():
                print(f"❌ Failed to open camera {camera_index}")
                # Try different camera indices
                for i in range(1, 5):
                    print(f"🎥 Trying camera {i} with DirectShow...")
                    self.cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
                    if self.cap.isOpened():
                        print(f"✅ Successfully opened camera {i}")
                        break
                    else:
                        print(f"❌ DirectShow failed for camera {i}, trying default...")
                        self.cap = cv2.VideoCapture(i)
                        if self.cap.isOpened():
                            print(f"✅ Successfully opened camera {i} with default backend")
                            break
                else:
                    print(f"❌ No cameras found - will use fallback frames")
                    self.cap = None
                    return
            
            if self.cap and self.cap.isOpened():
                # Set camera properties
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.cap.set(cv2.CAP_PROP_FPS, 30)
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                print(f"✅ Camera configured successfully")
                
                # Give camera a moment to initialize
                time.sleep(0.2)
                
                # Test reading a frame to ensure it's working
                ret, test_frame = self.cap.read()
                if ret and test_frame is not None:
                    print(f"✅ Camera test frame captured: {test_frame.shape}")
                else:
                    print(f"⚠️ Camera test frame failed, but camera is opened")
        except Exception as e:
            print(f"❌ Camera initialization error: {e}")
            self.cap = None
        
    def isOpened(self) -> bool:
        return self.cap is not None and self.cap.isOpened()
    
    def read(self):
        if self.cap and self.cap.isOpened():
            return self.cap.read()
        return False, None
    
    def release(self):
        if self.cap:
            self.cap.release()
            self.cap = None


class SimpleRealVideoCamera:
    """Simple synchronous camera implementation."""

    def __init__(self, session_id):
        self.session_id = session_id
        print(f"🎥 Initializing simple camera for session {session_id}")
        self.video = _VideoCapture()
        print(f"🎥 Camera isOpened: {self.video.isOpened()}")
        
        self._last_warning_state = {
            "no_person_warning_active": False,
            "multiple_people": False,
            "phone_detected": False,
            "no_person": False,
            "low_concentration": False,
            "tab_switched": False,
            "excessive_noise": False,
            "multiple_speakers": False,
        }

    def get_frame(self) -> bytes:
        """Get a frame as JPEG bytes."""
        try:
            if not self.video.isOpened():
                print(f"❌ Camera not opened for session {self.session_id}")
                return self._create_fallback_frame()
            
            print(f"📸 Attempting to read frame for session {self.session_id}")
            ret, frame = self.video.read()
            print(f"📸 Frame read result - ret: {ret}, frame shape: {frame.shape if frame is not None else 'None'}")
            
            if ret and frame is not None:
                print(f"📸 Captured real camera frame for session {self.session_id}, shape: {frame.shape}")
                # Add timestamp overlay
                timestamp = time.strftime("%H:%M:%S")
                cv2.putText(frame, timestamp, (20, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                # Add session info overlay
                session_text = f"Session: {str(self.session_id)[:8]}"
                cv2.putText(frame, session_text, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                # Encode as JPEG
                print(f"📸 Encoding frame as JPEG...")
                ok, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ok:
                    print(f"✅ Frame encoded successfully, size: {len(buf.tobytes())} bytes")
                    return buf.tobytes()
                else:
                    print(f"❌ Failed to encode frame")
                    return self._create_fallback_frame()
            else:
                print(f"❌ Failed to read frame from camera - ret: {ret}, frame: {frame is not None}")
                return self._create_fallback_frame()
                
        except Exception as e:
            print(f"❌ Error in get_frame: {e}")
            import traceback
            traceback.print_exc()
            return self._create_fallback_frame()

    def _create_fallback_frame(self) -> bytes:
        """Create a fallback frame when camera is not available."""
        print(f"⚠️ Creating fallback frame for session {self.session_id}")
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Add session info
        text = f"Session: {str(self.session_id)[:8]}"
        cv2.putText(frame, text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Add status message
        if not self.video.isOpened():
            cv2.putText(frame, "Camera Not Available", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        else:
            cv2.putText(frame, "Camera Loading...", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Add timestamp
        timestamp = time.strftime("%H:%M:%S")
        cv2.putText(frame, timestamp, (20, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        ok, buf = cv2.imencode('.jpg', frame)
        return buf.tobytes() if ok else b''

    def get_latest_warnings(self) -> dict:
        return self._last_warning_state

    def set_tab_switch_status(self, hidden: bool) -> None:
        self._last_warning_state["tab_switched"] = bool(hidden)

    def cleanup(self) -> None:
        """Clean up camera resources."""
        print(f"🧹 Cleaning up simple camera for session {self.session_id}")
        if self.video:
            self.video.release()
        print(f"✅ Simple camera cleanup completed for session {self.session_id}")
