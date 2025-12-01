import time
import cv2
import numpy as np
import os
import subprocess
import platform
from datetime import datetime
from django.conf import settings


def get_ffmpeg_path():
    """Get FFmpeg executable path. Checks multiple Windows paths, then system PATH."""
    if platform.system() == 'Windows':
        # Try multiple possible Windows paths (user might have different installation)
        # Note: Always use full path with ffmpeg.exe at the end
        possible_paths = [
            r"C:\ffmpeg-7.0.2-essentials_build\bin\ffmpeg.exe",  # User's actual path (without C:\ffmpeg prefix)
            r"C:\ffmpeg\ffmpeg-7.0.2-essentials_build\bin\ffmpeg.exe",  # With C:\ffmpeg prefix
            r"C:\ffmpeg\bin\ffmpeg.exe",  # Simplified path
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",  # Program Files location
            r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",  # Program Files (x86)
        ]
        
        # Check each path
        for ffmpeg_path in possible_paths:
            if os.path.exists(ffmpeg_path):
                print(f"✅ Found FFmpeg at: {ffmpeg_path}")
                # Verify it actually works
                try:
                    result = subprocess.run(
                        [ffmpeg_path, '-version'],
                        capture_output=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        print(f"✅ FFmpeg verified and working")
                        return ffmpeg_path
                    else:
                        print(f"⚠️ FFmpeg found but version check failed: {ffmpeg_path}")
                except Exception as e:
                    print(f"⚠️ FFmpeg found but cannot execute: {ffmpeg_path} - {e}")
                    continue
        
        # If none of the specific paths work, try system PATH
        print(f"⚠️ FFmpeg not found in common Windows paths, trying system PATH...")
    
    # Fallback to system PATH
    try:
        # Test if ffmpeg is available in PATH
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
        if result.returncode == 0:
            print(f"✅ Using FFmpeg from system PATH")
            return 'ffmpeg'
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # Last resort: try the most likely Windows path even if file doesn't exist
    # (sometimes file exists but os.path.exists fails due to permissions)
    if platform.system() == 'Windows':
        # Try user's actual path first
        fallback_paths = [
            r"C:\ffmpeg-7.0.2-essentials_build\bin\ffmpeg.exe",  # User's path
            r"C:\ffmpeg\ffmpeg-7.0.2-essentials_build\bin\ffmpeg.exe",  # Alternative
        ]
        for fallback_path in fallback_paths:
            print(f"⚠️ Trying fallback path: {fallback_path}")
            # Try to execute it even if os.path.exists says it doesn't exist
            try:
                result = subprocess.run(
                    [fallback_path, '-version'],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    print(f"✅ Fallback path works: {fallback_path}")
                    return fallback_path
            except:
                continue
    
    # Last resort: try 'ffmpeg' from PATH
    print(f"❌ FFmpeg not found in any location!")
    print(f"   Please ensure FFmpeg is installed at: C:\\ffmpeg-7.0.2-essentials_build\\bin\\ffmpeg.exe")
    print(f"   Or add FFmpeg to your system PATH")
    print(f"   Using 'ffmpeg' from PATH as last resort (may fail)")
    return 'ffmpeg'  # Will likely fail, but we'll try


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
        # NEW: frame buffer and thread control
        self._frame_lock = None
        self._latest_frame = None
        self._running = False
        
        # Warning tracking for counts
        self._warning_counts = {}
        self._last_warning_logged = {}  # Track last time each warning was logged to avoid spam
        
        # Cached fallback frame to avoid regenerating
        self._cached_fallback_frame = None
        self._fallback_frame_cache_time = 0
        self._fallback_print_time = 0  # Track when we last printed fallback warning
        
        # YOLO model - NOT loaded during initialization (only during technical interview)
        self._yolo = None
        self._yolo_loaded = False
        self._proctoring_active = False  # Flag to track if proctoring/warning capture is active
        
        # Video recording - record raw video frames in parallel with YOLO detection
        self._video_writer = None
        self._recording_active = False
        self._video_file_path = None
        self._frame_width = 640
        self._frame_height = 480
        self._fps = 5  # Record at 5 fps to match actual capture rate (sleep 0.2s = 5 fps)
        # Note: This FPS matches the frame capture rate in _capture_and_detect_loop (time.sleep(0.2) = 5 fps)
        self._last_frame_time = None
        self._frame_timestamps = []  # Track frame timestamps for accurate playback
        
        # NEW: start basic frame capture loop (without YOLO) if camera available
        # This allows camera to work for identity verification without YOLO
        try:
            import threading
            import cv2
            if self.video.isOpened():
                self._frame_lock = threading.Lock()
                self._running = True
                # Start basic frame capture only (no YOLO detection yet)
                self._detector_thread = threading.Thread(target=self._capture_and_detect_loop, daemon=True)
                self._detector_thread.start()
                print(f"✅ Basic camera frame capture started for session {self.session_id} (YOLO not loaded yet)")
        except Exception as e:
            print(f"⚠️ Failed to start frame capture loop: {e}")
    
    def activate_yolo_proctoring(self):
        """Activate YOLO model and start proctoring warnings when technical interview starts"""
        if self._yolo_loaded:
            print(f"✅ YOLO already loaded for session {self.session_id}")
            self._proctoring_active = True
            return True
        
        try:
            from ultralytics import YOLO
            try:
                # Load YOLO model only when technical interview starts
                self._yolo = YOLO('yolov8n.pt')
                self._yolo_loaded = True
                self._proctoring_active = True
                print(f"✅ YOLOv8 model loaded and proctoring activated for session {self.session_id}")
                # Start video recording when proctoring starts
                self.start_video_recording()
                return True
            except Exception as e:
                print(f"⚠️ Could not load yolov8n.pt: {e}")
                self._yolo = None
                return False
        except Exception as e:
            print(f"ℹ️ ultralytics not installed; falling back to Haar cascade. {e}")
            return False
    
    def start_video_recording(self):
        """Start recording video frames to a file. Returns the exact start timestamp for synchronization."""
        if self._recording_active:
            print(f"⚠️ Video recording already active for session {self.session_id}")
            return getattr(self, '_recording_start_timestamp', None)
        
        try:
            # CRITICAL: Record timestamp IMMEDIATELY when recording starts (not when first frame is written)
            # This ensures audio can start at the exact same moment for perfect synchronization
            import time
            self._recording_start_timestamp = time.time()  # Record timestamp NOW, before any async operations
            self._first_frame_written = False  # Flag to track first frame
            print(f"🕐 Video recording start timestamp recorded IMMEDIATELY: {self._recording_start_timestamp}")
            
            # Create video directories if they don't exist
            # Raw videos (without audio) go to interview_videos_raw/
            # Merged videos (with audio) go to interview_videos_merged/
            raw_video_dir = os.path.join(settings.MEDIA_ROOT, 'interview_videos_raw')
            merged_video_dir = os.path.join(settings.MEDIA_ROOT, 'interview_videos_merged')
            os.makedirs(raw_video_dir, exist_ok=True)
            os.makedirs(merged_video_dir, exist_ok=True)
            
            # Generate video filename with session ID and timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            video_filename = f"{self.session_id}_{timestamp}.mp4"
            # Save raw video (without audio) to interview_videos_raw/
            self._video_file_path = os.path.join(raw_video_dir, video_filename)
            
            # Initialize VideoWriter with H.264 codec (browser-compatible)
            # Try different codecs in order of preference
            codecs_to_try = [
                ('avc1', 'H.264/AVC1 - Best browser compatibility'),
                ('H264', 'H.264 - Alternative'),
                ('XVID', 'XVID - Fallback'),
                ('mp4v', 'MP4V - Last resort')
            ]
            
            self._video_writer = None
            for codec_name, description in codecs_to_try:
                try:
                    fourcc = cv2.VideoWriter_fourcc(*codec_name)
                    # Try to create video writer with this codec
                    test_writer = cv2.VideoWriter(
                        self._video_file_path,
                        fourcc,
                        self._fps,
                        (self._frame_width, self._frame_height)
                    )
                    # Test if it's actually opened
                    if test_writer.isOpened():
                        self._video_writer = test_writer
                        print(f"✅ Video writer created with codec: {codec_name} ({description})")
                        break
                    else:
                        test_writer.release()
                        print(f"⚠️ Codec {codec_name} failed to open, trying next...")
                except Exception as e:
                    print(f"⚠️ Error with codec {codec_name}: {e}")
                    continue
            
            # If all codecs failed, use default
            if self._video_writer is None:
                print(f"⚠️ All codecs failed, using default")
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                self._video_writer = cv2.VideoWriter(
                    self._video_file_path,
                    fourcc,
                    self._fps,
                    (self._frame_width, self._frame_height)
                )
            
            if self._video_writer.isOpened():
                self._recording_active = True
                print(f"✅ Video recording started for session {self.session_id}: {video_filename}")
                # Return the exact timestamp that was recorded at the start of this function
                # This ensures audio can start at the EXACT same moment for perfect synchronization
                print(f"🕐 Video recording active - start timestamp: {self._recording_start_timestamp}")
                return self._recording_start_timestamp
            else:
                print(f"❌ Failed to open video writer for session {self.session_id}")
                self._video_writer = None
                return None
        except Exception as e:
            print(f"❌ Error starting video recording for session {self.session_id}: {e}")
            import traceback
            traceback.print_exc()
            self._video_writer = None
            return None
    
    def ensure_browser_compatible_video(self, video_path):
        """Convert video to H.264 format for browser compatibility."""
        if not os.path.exists(video_path):
            return None
        
        try:
            import subprocess
            # Get FFmpeg path
            ffmpeg_path = get_ffmpeg_path()
            
            # Check if ffmpeg is available
            try:
                result = subprocess.run([ffmpeg_path, '-version'], capture_output=True, timeout=5)
                if result.returncode != 0:
                    print(f"⚠️ FFmpeg found but version check failed")
                    return None
            except (FileNotFoundError, subprocess.TimeoutExpired) as e:
                print(f"⚠️ FFmpeg not found at {ffmpeg_path}: {e}")
                return None
            
            # Create converted video path
            base_name = os.path.splitext(video_path)[0]
            converted_video_path = f"{base_name}_converted.mp4"
            
            # Skip if already converted
            if '_converted' in video_path or '_with_audio' in video_path:
                print(f"✅ Video already converted: {video_path}")
                return video_path
            
            print(f"🔄 Converting video to H.264 for browser compatibility: {video_path}")
            convert_cmd = [
                ffmpeg_path,
                '-i', video_path,
                '-c:v', 'libx264',  # H.264 codec
                '-preset', 'medium',  # Encoding speed
                '-crf', '23',  # Quality (18-28 range, 23 is good)
                '-movflags', '+faststart',  # Enable fast start for web playback
                '-pix_fmt', 'yuv420p',  # Ensure compatibility
                '-r', '5',  # Set output frame rate to 5 fps (matches recording)
                '-vsync', 'cfr',  # Constant frame rate for correct playback speed
                '-y',  # Overwrite output file
                converted_video_path
            ]
            
            result = subprocess.run(
                convert_cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0 and os.path.exists(converted_video_path):
                try:
                    os.remove(video_path)  # Remove original
                except:
                    pass
                print(f"✅ Video converted to H.264: {converted_video_path}")
                return converted_video_path
            else:
                print(f"⚠️ Video conversion failed: {result.stderr}")
                print(f"⚠️ Original video path: {video_path}")
                print(f"⚠️ Attempted output: {converted_video_path}")
                # Return original path even if conversion failed
                return video_path
        except Exception as e:
            print(f"⚠️ Error converting video: {e}")
            return None
    
    def stop_video_recording(self, audio_file_path=None, audio_start_timestamp=None, video_start_timestamp=None):
        """Stop recording and save video file. Optionally merge with audio using ffmpeg.
        
        Args:
            audio_file_path: Path to audio file to merge
            audio_start_timestamp: Unix timestamp when audio recording started (for sync)
            video_start_timestamp: Unix timestamp when video recording started (for sync)
        """
        # CRITICAL: Record video stop timestamp for audio synchronization
        import time
        video_stop_timestamp = time.time()
        self._recording_stop_timestamp = video_stop_timestamp
        print(f"🕐 Video recording stop timestamp: {video_stop_timestamp}")
        
        # Allow merging even if recording was already stopped (for audio merge after cleanup)
        video_path = self._video_file_path
        
        # If recording is active, stop it first
        if self._recording_active:
            try:
                self._recording_active = False
                
                if self._video_writer:
                    self._video_writer.release()
                    self._video_writer = None
                    print(f"✅ Video recording stopped for session {self.session_id} at {video_stop_timestamp}")
            except Exception as e:
                print(f"⚠️ Error stopping video writer: {e}")
        
        # Debug logging
        print(f"🔍 stop_video_recording called:")
        print(f"   audio_file_path: {audio_file_path}")
        print(f"   video_path: {video_path}")
        print(f"   _recording_active: {self._recording_active}")
        
        # Auto-discover audio file if not provided
        if not audio_file_path:
            auto_audio_path = self._find_audio_file_for_session()
            if auto_audio_path:
                audio_file_path = auto_audio_path
                print(f"🔎 Auto-detected audio file for merging: {audio_file_path}")
            else:
                print(f"ℹ️ No auto-detected audio file found for session {self.session_id}")
        elif audio_file_path and not os.path.isabs(audio_file_path):
            # Convert relative paths to absolute
            audio_file_path = os.path.join(settings.MEDIA_ROOT, audio_file_path)
        
        # If no video path exists, try to find it from the session or file system
        if not video_path or not os.path.exists(video_path):
            print(f"⚠️ Video path not set or file doesn't exist: {video_path}")
            
            # First, try to find video file in file system by session_id
            # Search in both old and new folders for backward compatibility
            search_dirs = [
                os.path.join(settings.MEDIA_ROOT, 'interview_videos_raw'),
                os.path.join(settings.MEDIA_ROOT, 'interview_videos'),  # Old folder
            ]
            
            # Search for video files matching this session_id
            found_video = None
            for search_dir in search_dirs:
                if not os.path.exists(search_dir):
                    continue
                try:
                    for filename in os.listdir(search_dir):
                        # Match by session_id (UUID) - can be full UUID or partial
                        session_id_str = str(self.session_id)
                        if filename.startswith(session_id_str) and filename.endswith('.mp4'):
                            # Prefer non-converted, non-merged videos for merging
                            if '_converted' not in filename and '_with_audio' not in filename:
                                found_video = os.path.join(search_dir, filename)
                                print(f"✅ Found raw video file in filesystem: {found_video}")
                                break
                    # If no raw video found, try any video with this session_id (but not merged)
                    if not found_video:
                        for filename in os.listdir(search_dir):
                            session_id_str = str(self.session_id)
                            if filename.startswith(session_id_str) and filename.endswith('.mp4'):
                                if '_with_audio' not in filename:  # Don't use already merged videos
                                    found_video = os.path.join(search_dir, filename)
                                    print(f"✅ Found video file in filesystem (may be converted): {found_video}")
                                    break
                    if found_video:
                        break
                except Exception as e:
                    print(f"⚠️ Error searching video directory {search_dir}: {e}")
            
            # If still not found, try InterviewSession database lookup
            if not found_video:
                try:
                    from interview_app.models import InterviewSession
                    # Try to find session by session_id (UUID) or session_key
                    session = None
                    try:
                        # First try by session_id (UUID) - this is the primary key
                        session = InterviewSession.objects.get(id=self.session_id)
                        print(f"✅ Found InterviewSession by id (UUID): {session.id}")
                    except InterviewSession.DoesNotExist:
                        try:
                            # If that fails, try by session_key (hex string)
                            session = InterviewSession.objects.get(session_key=self.session_id)
                            print(f"✅ Found InterviewSession by session_key: {session.session_key}")
                        except InterviewSession.DoesNotExist:
                            # Try to find any session with matching session_id in session_key field (partial match)
                            sessions = InterviewSession.objects.filter(session_key__icontains=str(self.session_id)[:8])
                            if sessions.exists():
                                session = sessions.first()
                                print(f"✅ Found InterviewSession by partial match: {session.id}")
                            else:
                                print(f"⚠️ InterviewSession not found for session_id: {self.session_id}")
                    
                    if session:
                        if session.interview_video:
                            video_path_str = str(session.interview_video)
                            found_video = os.path.join(settings.MEDIA_ROOT, video_path_str)
                            
                            # If it's a converted video, try to find the original for merging
                            if '_converted' in video_path_str and os.path.exists(found_video):
                                # Look for original video (without _converted) for merging
                                original_name = video_path_str.replace('_converted', '')
                                original_path = os.path.join(settings.MEDIA_ROOT, original_name)
                                if os.path.exists(original_path):
                                    found_video = original_path
                                    print(f"✅ Found original video for merging (not converted): {found_video}")
                                else:
                                    print(f"⚠️ Original video not found, will use converted: {found_video}")
                            elif not os.path.exists(found_video):
                                print(f"⚠️ Video file from InterviewSession doesn't exist: {found_video}")
                                found_video = None
                            else:
                                print(f"✅ Found video file from InterviewSession: {found_video}")
                        else:
                            print(f"⚠️ No video path in InterviewSession (session found but no video)")
                            # Video might not be saved to DB yet, but exists on disk (found above)
                            if not found_video:
                                print(f"   Will search filesystem for video files...")
                    else:
                        print(f"⚠️ InterviewSession not found for session_id: {self.session_id}")
                        # Continue - we might find video in filesystem
                except Exception as e:
                    print(f"⚠️ Error looking up video from InterviewSession: {e}")
                    import traceback
                    traceback.print_exc()
            
            # If we found a video, use it
            if found_video and os.path.exists(found_video):
                video_path = found_video
                self._video_file_path = video_path
                print(f"✅ Using video file: {video_path}")
                print(f"   File size: {os.path.getsize(video_path) / 1024 / 1024:.2f} MB")
            else:
                # Last resort: search all video directories for any file with session_id
                print(f"⚠️ Video not found in standard locations, doing comprehensive search...")
                all_video_dirs = [
                    os.path.join(settings.MEDIA_ROOT, 'interview_videos_raw'),
                    os.path.join(settings.MEDIA_ROOT, 'interview_videos_merged'),
                    os.path.join(settings.MEDIA_ROOT, 'interview_videos'),  # Old folder
                ]
                session_id_str = str(self.session_id)
                for search_dir in all_video_dirs:
                    if not os.path.exists(search_dir):
                        continue
                    try:
                        for filename in os.listdir(search_dir):
                            if session_id_str in filename and filename.endswith('.mp4'):
                                # Skip already merged videos if we're trying to merge
                                if audio_file_path and '_with_audio' in filename:
                                    continue
                                candidate_path = os.path.join(search_dir, filename)
                                if os.path.exists(candidate_path):
                                    found_video = candidate_path
                                    print(f"✅ Found video in comprehensive search: {found_video}")
                                    break
                        if found_video:
                            break
                    except Exception as e:
                        print(f"⚠️ Error searching {search_dir}: {e}")
                
                if found_video and os.path.exists(found_video):
                    video_path = found_video
                    self._video_file_path = video_path
                    print(f"✅ Using video file from comprehensive search: {video_path}")
                else:
                    print(f"❌ Could not find video file for session {self.session_id}")
                    print(f"   Searched in: {all_video_dirs}")
                    if audio_file_path:
                        print(f"   Cannot merge audio - video file doesn't exist")
                    return None
        
        # Log file details
        if audio_file_path:
            print(f"   audio_file_path exists: {os.path.exists(audio_file_path)}")
            if os.path.exists(audio_file_path):
                audio_size = os.path.getsize(audio_file_path) / 1024 / 1024
                print(f"   audio_file_size: {audio_size:.2f} MB")
        if video_path:
            print(f"   video_path exists: {os.path.exists(video_path)}")
            if os.path.exists(video_path):
                video_size = os.path.getsize(video_path) / 1024 / 1024
                print(f"   video_file_size: {video_size:.2f} MB")
        
        try:
            
            # If audio file is provided, merge video and audio using ffmpeg
            # Also convert to H.264 for browser compatibility
            if audio_file_path and os.path.exists(audio_file_path) and os.path.exists(video_path):
                try:
                    # Verify and process audio file before merging
                    try:
                        from interview_app.audio_processor import verify_audio_file, process_uploaded_audio, get_audio_info
                        
                        # Verify audio file
                        if not verify_audio_file(audio_file_path):
                            print(f"⚠️ Audio file verification failed, but attempting merge anyway...")
                        
                        # Get audio info for debugging
                        audio_info = get_audio_info(audio_file_path)
                        if audio_info:
                            print(f"📊 Audio file info:")
                            print(f"   Duration: {audio_info['duration']:.2f}s")
                            print(f"   Sample rate: {audio_info['sample_rate']}Hz")
                            print(f"   Channels: {audio_info['channels']}")
                            print(f"   Codec: {audio_info['codec']}")
                        
                        # Process audio if needed (convert to WAV for better compatibility)
                        file_ext = os.path.splitext(audio_file_path)[1].lower()
                        if file_ext not in ['.wav', '.mp3']:
                            print(f"🔄 Audio format ({file_ext}) may not be optimal, converting to WAV...")
                            processed_audio = process_uploaded_audio(audio_file_path, convert_to_wav=True)
                            if processed_audio and os.path.exists(processed_audio):
                                print(f"✅ Using processed audio: {processed_audio}")
                                audio_file_path = processed_audio
                            else:
                                print(f"⚠️ Audio processing failed, using original: {audio_file_path}")
                    except Exception as e:
                        print(f"⚠️ Error processing audio before merge: {e}")
                        # Continue with original audio file
                    
                    # Get FFmpeg path first and verify it works
                    ffmpeg_path = get_ffmpeg_path()
                    
                    # Verify FFmpeg is accessible
                    try:
                        test_result = subprocess.run(
                            [ffmpeg_path, '-version'],
                            capture_output=True,
                            timeout=5
                        )
                        if test_result.returncode != 0:
                            raise FileNotFoundError(f"FFmpeg at {ffmpeg_path} returned non-zero exit code")
                        print(f"✅ FFmpeg verified at: {ffmpeg_path}")
                    except Exception as e:
                        print(f"❌ FFmpeg verification failed: {e}")
                        raise FileNotFoundError(f"FFmpeg not accessible at {ffmpeg_path}")
                    
                    # Normalize all paths to avoid separator issues
                    video_path = os.path.normpath(video_path)
                    audio_file_path = os.path.normpath(audio_file_path)
                    
                    # Create output path for merged video in interview_videos_merged/ folder
                    merged_video_dir = os.path.join(settings.MEDIA_ROOT, 'interview_videos_merged')
                    os.makedirs(merged_video_dir, exist_ok=True)
                    
                    # Get base filename (without directory)
                    video_basename = os.path.basename(video_path)
                    base_name = os.path.splitext(video_basename)[0]
                    # Remove any existing suffixes like _converted
                    if '_converted' in base_name:
                        base_name = base_name.replace('_converted', '')
                    
                    # Save merged video to interview_videos_merged/ folder
                    merged_video_filename = f"{base_name}_with_audio.mp4"
                    merged_video_path = os.path.join(merged_video_dir, merged_video_filename)
                    merged_video_path = os.path.normpath(merged_video_path)
                    
                    # Get file sizes for logging
                    video_size = os.path.getsize(video_path) / 1024 / 1024
                    audio_size = os.path.getsize(audio_file_path) / 1024 / 1024
                    print(f"📊 Merging video ({video_size:.2f} MB) with audio ({audio_size:.2f} MB)...")
                    print(f"   Normalized video path: {video_path}")
                    print(f"   Normalized audio path: {audio_file_path}")
                    print(f"   Normalized output path: {merged_video_path}")
                    
                    # CRITICAL: Calculate time offset for synchronization using timestamps
                    time_offset = 0.0
                    audio_offset = 0.0  # Initialize audio offset
                    
                    # Get video start timestamp (prefer from first frame, fallback to parameter or attribute)
                    video_ts = None
                    if hasattr(self, '_recording_start_timestamp') and self._recording_start_timestamp:
                        video_ts = self._recording_start_timestamp
                        print(f"🕐 Video start timestamp (from first frame): {video_ts}")
                    elif video_start_timestamp:
                        video_ts = video_start_timestamp
                        print(f"🕐 Video start timestamp (from parameter): {video_ts}")
                    
                    # CRITICAL: Get video and audio durations FIRST to determine exact trimming
                    vid_dur = 0
                    aud_dur = 0
                    try:
                        # Get video duration FIRST (this is the reference)
                        probe_cmd = [ffmpeg_path, '-i', video_path, '-show_entries', 'format=duration', '-v', 'quiet', '-of', 'csv=p=0']
                        video_duration = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)
                        if video_duration.returncode == 0:
                            vid_dur = float(video_duration.stdout.strip()) if video_duration.stdout.strip() else 0
                            print(f"   📹 Video duration: {vid_dur:.2f} seconds ({vid_dur/60:.2f} minutes)")
                        
                        # Get audio duration
                        probe_cmd = [ffmpeg_path, '-i', audio_file_path, '-show_entries', 'format=duration', '-v', 'quiet', '-of', 'csv=p=0']
                        audio_duration = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)
                        if audio_duration.returncode == 0:
                            aud_dur = float(audio_duration.stdout.strip()) if audio_duration.stdout.strip() else 0
                            print(f"   🎙️ Audio duration: {aud_dur:.2f} seconds ({aud_dur/60:.2f} minutes)")
                    except Exception as e:
                        print(f"   ⚠️ Could not probe durations: {e}")
                    
                    # Get audio start timestamp and calculate offset
                    audio_trim_start = 0.0  # How much to skip from audio START
                    audio_trim_end = None   # How much to trim from audio END (duration limit)
                    extra_audio_at_start = False
                    extra_audio_at_end = False
                    
                    if audio_start_timestamp:
                        audio_ts = audio_start_timestamp
                        print(f"🕐 Audio start timestamp: {audio_ts}")
                        
                        # Calculate time difference (positive = audio started after video, negative = audio started before)
                        if video_ts:
                            time_diff = audio_ts - video_ts
                            print(f"⏱️ Time difference: {time_diff:.3f} seconds ({time_diff * 1000:.1f}ms)")
                            
                            if abs(time_diff) > 0.1:  # More than 100ms difference
                                if time_diff > 0:
                                    # Audio started AFTER video - extra audio is at the START
                                    audio_trim_start = time_diff
                                    extra_audio_at_start = True
                                    print(f"🔧 Audio started {time_diff:.3f}s AFTER video")
                                    print(f"   → Extra audio is at the START of audio file")
                                    print(f"   → Will skip {audio_trim_start:.3f}s from audio start using -ss")
                                else:
                                    # Audio started BEFORE video - extra audio is at the START
                                    audio_trim_start = abs(time_diff)
                                    extra_audio_at_start = True
                                    print(f"🔧 Audio started {abs(time_diff):.3f}s BEFORE video")
                                    print(f"   → Extra audio is at the START of audio file")
                                    print(f"   → Will skip {audio_trim_start:.3f}s from audio start using -ss")
                            else:
                                print(f"✅ Audio and video start times are synchronized (< 100ms difference)")
                    else:
                        print(f"⚠️ No audio timestamp provided - assuming audio and video start together")
                    
                    # CRITICAL: Determine if extra audio is at the END
                    # Calculate if audio continues after video stops
                    if vid_dur > 0 and aud_dur > 0:
                        # Calculate effective audio duration after trimming start
                        effective_audio_dur = aud_dur - audio_trim_start
                        
                        if effective_audio_dur > vid_dur:
                            # Audio is longer than video even after trimming start
                            # Extra audio is at the END
                            extra_audio_at_end = True
                            audio_trim_end = vid_dur  # Limit audio to video duration
                            extra_duration = effective_audio_dur - vid_dur
                            print(f"🔧 Audio continues AFTER video stops")
                            print(f"   → Effective audio duration (after start trim): {effective_audio_dur:.2f}s")
                            print(f"   → Video duration: {vid_dur:.2f}s")
                            print(f"   → Extra audio at END: {extra_duration:.2f}s")
                            print(f"   → Will trim audio to match video duration: {audio_trim_end:.2f}s using -t")
                        elif effective_audio_dur < vid_dur:
                            # Audio is shorter than video (after trimming start)
                            print(f"🔧 Audio is shorter than video after trimming start")
                            print(f"   → Effective audio duration: {effective_audio_dur:.2f}s")
                            print(f"   → Video duration: {vid_dur:.2f}s")
                            print(f"   → Will use -shortest flag (video will be trimmed)")
                        else:
                            print(f"✅ Audio and video durations match perfectly after start trim")
                    
                    # Build FFmpeg command with time offset for synchronization
                    ffmpeg_cmd_simple = [ffmpeg_path]
                    
                    # Add video input
                    ffmpeg_cmd_simple.extend(['-i', video_path])
                    
                    # Add audio input with offset if needed
                    if audio_trim_start > 0.1:
                        # Use -ss to skip the beginning of audio to align with video
                        ffmpeg_cmd_simple.extend(['-ss', f'{audio_trim_start:.3f}', '-i', audio_file_path])
                        print(f"🔧 Applying audio start trim: skipping {audio_trim_start:.3f}s from audio start")
                    else:
                        # No offset needed - audio and video are already aligned
                        ffmpeg_cmd_simple.extend(['-i', audio_file_path])
                    
                    # Add encoding options
                    ffmpeg_cmd_simple.extend([
                        '-c:v', 'copy',  # Copy video stream (faster, no re-encoding)
                        '-c:a', 'aac',  # Encode audio as AAC
                        '-b:a', '192k',
                        '-ar', '44100',  # Audio sample rate
                        '-ac', '1',  # Mono audio
                    ])
                    
                    # CRITICAL: ALWAYS trim audio to match video duration exactly
                    # Video duration is the authoritative reference - audio MUST match it
                    if vid_dur > 0:
                        # ALWAYS use -t to limit audio to exact video duration
                        # This ensures audio and video end at the exact same time
                        ffmpeg_cmd_simple.extend(['-t', f'{vid_dur:.3f}'])
                        print(f"🔧 CRITICAL: Using -t {vid_dur:.3f} to ensure audio matches video duration EXACTLY")
                        print(f"   This ensures audio and video end at the exact same time")
                    elif audio_trim_end and audio_trim_end > 0:
                        # Fallback: use calculated trim end
                        ffmpeg_cmd_simple.extend(['-t', f'{audio_trim_end:.3f}'])
                        print(f"🔧 Using -t {audio_trim_end:.3f} to trim audio END to match video duration")
                    else:
                        # Last resort: use -shortest
                        ffmpeg_cmd_simple.extend(['-shortest'])
                        print(f"🔧 Using -shortest flag (fallback - video duration not available)")
                    
                    # Summary of trimming strategy
                    print(f"📊 Audio-Video Synchronization Summary:")
                    if extra_audio_at_start:
                        print(f"   ✅ Extra audio at START: {audio_trim_start:.3f}s will be skipped")
                    if extra_audio_at_end:
                        print(f"   ✅ Extra audio at END: {audio_trim_end:.2f}s duration limit applied")
                    if not extra_audio_at_start and not extra_audio_at_end:
                        print(f"   ✅ No extra audio - perfect synchronization")
                    
                    ffmpeg_cmd_simple.extend([
                        '-y',  # Overwrite output file
                        merged_video_path
                    ])
                    
                    # Advanced command with re-encoding (fallback if simple fails)
                    # Also includes time offset for synchronization
                    ffmpeg_cmd_advanced = [ffmpeg_path]
                    
                    # Add video input
                    ffmpeg_cmd_advanced.extend(['-i', video_path])
                    
                    # Add audio input with offset if needed
                    if audio_offset > 0.1:  # More than 100ms offset
                        # Use -ss to skip the beginning of audio to align with video
                        ffmpeg_cmd_advanced.extend(['-ss', f'{audio_offset:.3f}', '-i', audio_file_path])
                        print(f"🔧 Advanced merge: Applying audio offset: skipping {audio_offset:.3f}s from audio start")
                    else:
                        # No offset needed
                        ffmpeg_cmd_advanced.extend(['-i', audio_file_path])
                    
                    # Add filter complex for synchronization
                    if audio_offset > 0.1:
                        # Adjust audio PTS to account for the offset
                        filter_complex = f'[0:v]setpts=PTS-STARTPTS[v];[1:a]asetpts=PTS-STARTPTS+{audio_offset}/TB[a]'
                    else:
                        filter_complex = '[0:v]setpts=PTS-STARTPTS[v];[1:a]asetpts=PTS-STARTPTS[a]'
                    
                    ffmpeg_cmd_advanced.extend([
                        '-filter_complex', filter_complex,
                        '-map', '[v]',
                        '-map', '[a]',
                        '-c:v', 'libx264',
                        '-preset', 'medium',
                        '-crf', '23',
                        '-pix_fmt', 'yuv420p',
                        '-c:a', 'aac',
                        '-b:a', '192k',
                        '-ar', '44100',
                        '-shortest',
                        '-movflags', '+faststart',
                        '-y',
                        merged_video_path
                    ])
                    
                    # Try simple command first
                    ffmpeg_cmd = ffmpeg_cmd_simple
                    use_simple = True
                    
                    print(f"🔄 Merging video and audio using FFmpeg (simple method)...")
                    print(f"   FFmpeg: {ffmpeg_path}")
                    print(f"   Command: {' '.join(ffmpeg_cmd_simple)}")
                    
                    # Log duration comparison if we have both (already calculated above)
                    if vid_dur > 0 and aud_dur > 0:
                        duration_diff = abs(vid_dur - aud_dur)
                        if duration_diff > 1:  # More than 1 second difference
                            print(f"   ⚠️ Duration mismatch: {duration_diff:.2f} seconds ({duration_diff/60:.2f} minutes)")
                            if vid_dur < aud_dur:
                                print(f"   ✅ Audio will be trimmed to match video duration: {vid_dur:.2f}s")
                            else:
                                print(f"   ✅ Video will be trimmed to match audio duration: {aud_dur:.2f}s")
                        else:
                            print(f"   ✅ Durations are well matched (difference: {duration_diff:.2f}s)")
                    
                    result = subprocess.run(
                        ffmpeg_cmd,
                        capture_output=True,
                        text=True,
                        timeout=600,  # 10 minute timeout for large files
                        encoding='utf-8',
                        errors='replace'  # Handle encoding errors gracefully
                    )
                    
                    # If simple command failed, try advanced command
                    if result.returncode != 0 and use_simple:
                        print(f"⚠️ Simple merge failed (code: {result.returncode}), trying advanced method...")
                        print(f"   Simple error: {result.stderr[:500] if result.stderr else result.stdout[:500]}")
                        ffmpeg_cmd = ffmpeg_cmd_advanced
                        use_simple = False
                        result = subprocess.run(
                            ffmpeg_cmd,
                            capture_output=True,
                            text=True,
                            timeout=600,
                            encoding='utf-8',
                            errors='replace'
                        )
                    
                    if result.returncode == 0 and os.path.exists(merged_video_path):
                        merged_size = os.path.getsize(merged_video_path) / 1024 / 1024
                        if merged_size > 0:
                            # Verify the merged video has audio track
                            try:
                                verify_cmd = [
                                    ffmpeg_path,
                                    '-i', merged_video_path,
                                    '-hide_banner'
                                ]
                                verify_result = subprocess.run(
                                    verify_cmd,
                                    capture_output=True,
                                    text=True,
                                    timeout=10
                                )
                                # Check if audio stream is present in output
                                if 'Audio:' in verify_result.stderr or 'Stream #0:1' in verify_result.stderr:
                                    print(f"✅ Verified: Merged video contains audio track")
                                else:
                                    print(f"⚠️ Warning: Merged video may not have audio track")
                                    print(f"   FFmpeg output: {verify_result.stderr[:500]}")
                            except Exception as e:
                                print(f"⚠️ Could not verify audio in merged video: {e}")
                            
                            # Remove original video without audio
                            try:
                                if os.path.exists(video_path):
                                    os.remove(video_path)
                                    print(f"🗑️ Removed original video without audio: {video_path}")
                                else:
                                    print(f"ℹ️ Original video already removed or doesn't exist: {video_path}")
                            except Exception as e:
                                print(f"⚠️ Could not remove original video: {e}")
                                import traceback
                                traceback.print_exc()
                            
                            video_path = merged_video_path
                            self._video_file_path = merged_video_path
                            print(f"✅ Video and audio merged successfully!")
                            print(f"   Output: {merged_video_path} ({merged_size:.2f} MB)")
                            print(f"   Frame rate: 5 fps (preserved from recording)")
                            print(f"   ✅ ONLY merged video exists - original removed")
                        else:
                            print(f"❌ Merged video file is empty!")
                            raise Exception("Merged video file is empty")
                    else:
                        error_msg = result.stderr if result.stderr else result.stdout
                        print(f"❌ FFmpeg merge failed!")
                        print(f"   Return code: {result.returncode}")
                        print(f"   Command used: {' '.join(ffmpeg_cmd)}")
                        print(f"   Full error output:")
                        print(f"   {'='*80}")
                        if error_msg:
                            # Print full error, split into chunks if too long
                            error_lines = error_msg.split('\n')
                            for i, line in enumerate(error_lines[:50]):  # First 50 lines
                                print(f"   {line}")
                            if len(error_lines) > 50:
                                print(f"   ... ({len(error_lines) - 50} more lines)")
                        else:
                            print(f"   (No error output available)")
                        print(f"   {'='*80}")
                        
                        # Don't raise exception - let it fall through to save video without audio
                        # But log the error clearly
                        print(f"⚠️ CRITICAL: Merge failed - video will be saved WITHOUT audio")
                        print(f"⚠️ This should NOT happen - merge must succeed for proper functionality")
                        raise Exception(f"FFmpeg merge failed with return code {result.returncode}. Check error output above.")
                        
                except FileNotFoundError as e:
                    print(f"❌ FFmpeg not found: {e}")
                    print(f"⚠️ Video saved without audio - FFmpeg is required for audio merging")
                    print(f"⚠️ Please install FFmpeg at one of these locations:")
                    print(f"   - C:\\ffmpeg-7.0.2-essentials_build\\bin\\ffmpeg.exe")
                    print(f"   - C:\\ffmpeg\\ffmpeg-7.0.2-essentials_build\\bin\\ffmpeg.exe")
                    print(f"   Or add FFmpeg to your system PATH")
                except Exception as e:
                    print(f"❌ Error merging audio with video: {e}")
                    import traceback
                    traceback.print_exc()
                    print(f"⚠️ CRITICAL ERROR: Merge failed - video will be saved WITHOUT audio")
                    print(f"⚠️ This is a critical failure - the video should NOT be saved without audio")
                    # Don't save the video if merge failed - raise exception to prevent saving
                    raise Exception(f"Cannot save video without audio - merge failed: {str(e)}")
            else:
                # No audio file, but still try to convert to H.264 for browser compatibility
                if not audio_file_path:
                    print(f"⚠️ No audio_file_path provided - video will be saved without audio")
                elif not os.path.exists(audio_file_path):
                    print(f"⚠️ Audio file does not exist: {audio_file_path}")
                    print(f"   Current working directory: {os.getcwd()}")
                    print(f"   Checking if it's a relative path...")
                    # Try to find audio file in common locations
                    possible_locations = [
                        audio_file_path,
                        os.path.join(os.getcwd(), audio_file_path),
                        os.path.join(settings.MEDIA_ROOT, audio_file_path) if 'settings' in globals() else None,
                    ]
                    found_audio = None
                    for loc in possible_locations:
                        if loc and os.path.exists(loc):
                            print(f"   ✅ Found audio at: {loc}")
                            found_audio = loc
                            break
                    
                    # If we found the audio file, manually trigger merge
                    if found_audio and os.path.exists(video_path):
                        print(f"   🔄 Attempting merge with found audio path: {found_audio}")
                        # Normalize paths
                        video_path = os.path.normpath(video_path)
                        found_audio = os.path.normpath(found_audio)
                        
                        # Re-check the condition with found audio path
                        audio_file_path = found_audio
                        # Now the condition at line 404 should pass, so we need to manually do the merge
                        # Actually, we can't easily re-enter the if block, so let's do the merge here
                        try:
                            ffmpeg_path = get_ffmpeg_path()
                            test_result = subprocess.run([ffmpeg_path, '-version'], capture_output=True, timeout=5)
                            if test_result.returncode != 0:
                                raise FileNotFoundError(f"FFmpeg at {ffmpeg_path} returned non-zero exit code")
                            print(f"✅ FFmpeg verified at: {ffmpeg_path}")
                            
                            # Save merged video to interview_videos_merged/ folder
                            merged_video_dir = os.path.join(settings.MEDIA_ROOT, 'interview_videos_merged')
                            os.makedirs(merged_video_dir, exist_ok=True)
                            video_basename = os.path.basename(video_path)
                            base_name = os.path.splitext(video_basename)[0]
                            if '_converted' in base_name:
                                base_name = base_name.replace('_converted', '')
                            merged_video_filename = f"{base_name}_with_audio.mp4"
                            merged_video_path = os.path.join(merged_video_dir, merged_video_filename)
                            merged_video_path = os.path.normpath(merged_video_path)
                            video_size = os.path.getsize(video_path) / 1024 / 1024
                            audio_size = os.path.getsize(found_audio) / 1024 / 1024
                            print(f"📊 Merging video ({video_size:.2f} MB) with audio ({audio_size:.2f} MB)...")
                            
                            # Try simple command first
                            ffmpeg_cmd = [
                                ffmpeg_path, '-i', video_path, '-i', found_audio,
                                '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
                                '-shortest', '-y', merged_video_path
                            ]
                            
                            print(f"🔄 Merging video and audio using FFmpeg (simple method)...")
                            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=600, encoding='utf-8', errors='replace')
                            
                            # If simple fails, try advanced
                            if result.returncode != 0:
                                print(f"⚠️ Simple merge failed, trying advanced method...")
                                ffmpeg_cmd = [
                                    ffmpeg_path, '-i', video_path, '-i', found_audio,
                                    '-filter_complex', '[0:v]setpts=PTS-STARTPTS[v];[1:a]asetpts=PTS-STARTPTS[a]',
                                    '-map', '[v]', '-map', '[a]',
                                    '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
                                    '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
                                    '-shortest', '-movflags', '+faststart', '-y', merged_video_path
                                ]
                                result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=600, encoding='utf-8', errors='replace')
                            
                            if result.returncode == 0 and os.path.exists(merged_video_path):
                                merged_size = os.path.getsize(merged_video_path) / 1024 / 1024
                                if merged_size > 0:
                                    try:
                                        if os.path.exists(video_path):
                                            os.remove(video_path)
                                            print(f"🗑️ Removed original video without audio: {video_path}")
                                        else:
                                            print(f"ℹ️ Original video already removed or doesn't exist: {video_path}")
                                    except Exception as e:
                                        print(f"⚠️ Could not remove original video: {e}")
                                        import traceback
                                        traceback.print_exc()
                                    video_path = merged_video_path
                                    self._video_file_path = merged_video_path
                                    print(f"✅ Video and audio merged successfully! ({merged_size:.2f} MB)")
                                    print(f"   ✅ ONLY merged video exists - original removed")
                                    if os.path.exists(video_path):
                                        # Return relative path from MEDIA_ROOT
                                        relative_path = os.path.relpath(video_path, settings.MEDIA_ROOT)
                                        relative_path = relative_path.replace('\\', '/')
                                        return relative_path
                            else:
                                error_msg = result.stderr if result.stderr else result.stdout
                                print(f"❌ Manual merge failed!")
                                print(f"   Return code: {result.returncode}")
                                print(f"   Error: {error_msg[:1000] if error_msg else 'No error output'}")
                                raise Exception(f"Manual merge failed: {error_msg[:200] if error_msg else 'Unknown error'}")
                        except Exception as e:
                            print(f"❌ Error in manual merge attempt: {e}")
                            import traceback
                            traceback.print_exc()
                            # Don't save video if merge failed
                            raise Exception(f"Cannot save video - manual merge failed: {str(e)}")
                elif not os.path.exists(video_path):
                    print(f"⚠️ Video file does not exist: {video_path}")
                    # Try to find video in raw folder
                    raw_video_dir = os.path.join(settings.MEDIA_ROOT, 'interview_videos_raw')
                    if os.path.exists(raw_video_dir):
                        video_basename = os.path.basename(video_path) if video_path else None
                        if video_basename:
                            alt_path = os.path.join(raw_video_dir, video_basename)
                            if os.path.exists(alt_path):
                                video_path = alt_path
                                print(f"✅ Found video in raw folder: {video_path}")
                
                if os.path.exists(video_path):
                    try:
                        # Get FFmpeg path
                        ffmpeg_path = get_ffmpeg_path()
                        
                        print(f"🔄 Converting video to H.264 for browser compatibility...")
                        # Save converted video to raw folder
                        raw_video_dir = os.path.join(settings.MEDIA_ROOT, 'interview_videos_raw')
                        os.makedirs(raw_video_dir, exist_ok=True)
                        video_basename = os.path.basename(video_path)
                        base_name = os.path.splitext(video_basename)[0]
                        converted_video_filename = f"{base_name}_converted.mp4"
                        converted_video_path = os.path.join(raw_video_dir, converted_video_filename)
                        # Preserve frame rate to ensure correct playback speed
                        convert_cmd = [
                            ffmpeg_path,
                            '-i', video_path,
                            '-c:v', 'libx264',
                            '-preset', 'medium',
                            '-crf', '23',
                            '-pix_fmt', 'yuv420p',  # Ensure pixel format compatibility
                            '-r', '5',  # Set output frame rate to 5 fps (matches recording)
                            '-vsync', 'cfr',  # Constant frame rate for correct playback speed
                            '-movflags', '+faststart',
                            '-y',
                            converted_video_path
                        ]
                        convert_result = subprocess.run(
                            convert_cmd,
                            capture_output=True,
                            text=True,
                            timeout=300
                        )
                        if convert_result.returncode == 0 and os.path.exists(converted_video_path):
                            try:
                                os.remove(video_path)
                            except:
                                pass
                            video_path = converted_video_path
                            self._video_file_path = converted_video_path
                            print(f"✅ Video converted to H.264: {converted_video_path}")
                        else:
                            print(f"⚠️ Video conversion failed: {convert_result.stderr}")
                            print(f"⚠️ Using original video (may not play in browser): {video_path}")
                    except FileNotFoundError:
                        print(f"⚠️ FFmpeg not found - video may not be browser-compatible.")
                        print(f"⚠️ Install ffmpeg to enable H.264 conversion.")
                    except Exception as e:
                        print(f"⚠️ Error converting video: {e}")
                        print(f"⚠️ Using original video: {video_path}")
            
            # Return the relative path for saving to InterviewSession
            # CRITICAL: Only return merged videos (with _with_audio suffix)
            if video_path and os.path.exists(video_path):
                # Normalize path
                video_path = os.path.normpath(video_path)
                
                # Verify file is not empty
                file_size = os.path.getsize(video_path)
                if file_size == 0:
                    print(f"❌ Video file is empty: {video_path}")
                    return None
                
                # CRITICAL CHECK: Only allow merged videos to be saved
                has_audio = '_with_audio' in video_path or 'interview_videos_merged' in video_path
                if not has_audio:
                    print(f"❌ CRITICAL ERROR: Attempting to return unmerged video path!")
                    print(f"   Path: {video_path}")
                    print(f"   This should NEVER happen - merge must succeed before returning path")
                    # Try to find merged version in interview_videos_merged/ folder
                    merged_video_dir = os.path.join(settings.MEDIA_ROOT, 'interview_videos_merged')
                    video_basename = os.path.basename(video_path)
                    base_name = os.path.splitext(video_basename)[0]
                    if '_converted' in base_name:
                        base_name = base_name.replace('_converted', '')
                    merged_filename = f"{base_name}_with_audio.mp4"
                    merged_path = os.path.join(merged_video_dir, merged_filename)
                    merged_path = os.path.normpath(merged_path)
                    if os.path.exists(merged_path):
                        print(f"   ✅ Found merged version, using: {merged_path}")
                        video_path = merged_path
                        has_audio = True
                        file_size = os.path.getsize(video_path)
                    else:
                        print(f"   ❌ Merged version not found: {merged_path}")
                        print(f"   ❌ REFUSING to return unmerged video path - raising exception")
                        raise Exception(f"Cannot return unmerged video path. Merge must succeed. Expected merged file at: {merged_path}")
                
                audio_status = "with merged audio"
                
                # Get relative path from MEDIA_ROOT
                relative_path = os.path.relpath(video_path, settings.MEDIA_ROOT)
                # Convert to forward slashes for Django
                relative_path = relative_path.replace('\\', '/')
                print(f"✅ Video file saved {audio_status}: {relative_path} ({file_size / 1024 / 1024:.2f} MB)")
                print(f"   ✅ Verified: Path contains '_with_audio' or is in interview_videos_merged/ - merge successful")
                return relative_path
            else:
                print(f"❌ Video file not found at {video_path}")
                return None
        except Exception as e:
            print(f"❌ Error stopping video recording for session {self.session_id}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _capture_and_detect_loop(self):
        """Continuously capture frames, update latest frame, and run simple face-based warnings."""
        # Load Haar cascade once (fallback if YOLO not available)
        try:
            import cv2
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            face_cascade = cv2.CascadeClassifier(cascade_path)
        except Exception as e:
            print(f"⚠️ Failed to load Haar cascade: {e}")
            face_cascade = None
        
        import time
        import time as _t
        import threading
        import queue
        
        last_gray = None
        last_motion_ts = _t.time()
        LOW_MOTION_WINDOW_SEC = 8.0
        MOTION_LOW_THRESH = 2.5  # mean absolute diff threshold (tune if needed)
        
        # Background thread for saving snapshots and logging to DB (non-blocking)
        warning_queue = queue.Queue(maxsize=10)  # Limit queue size
        
        def _background_warning_logger():
            """Background thread to save snapshots and log to database without blocking detection."""
            while self._running:
                try:
                    # Get warning data from queue (with short timeout to prevent blocking)
                    warning_data = warning_queue.get(timeout=0.5)
                    if warning_data is None:
                        break
                    warning_type, frame_copy, snapshot_filename = warning_data
                    
                    # Save snapshot only if proctoring is active (technical interview started)
                    # Skip snapshot saving during identity verification
                    if self._proctoring_active and frame_copy is not None and snapshot_filename:
                        try:
                            img_dir = os.path.join(settings.MEDIA_ROOT, "proctoring_snaps")
                            os.makedirs(img_dir, exist_ok=True)
                            img_path = os.path.join(img_dir, snapshot_filename)
                            cv2.imwrite(img_path, frame_copy)
                            print(f"📸 Snapshot saved: {snapshot_filename}")
                        except Exception as e:
                            print(f"[Proctoring] Failed to save snapshot: {e}")
                    elif not self._proctoring_active:
                        # Proctoring not active - skip snapshot saving
                        print(f"⚠️ Skipping snapshot save - proctoring not active yet (still in identity verification)")
                    
                    # Log to database (with timeout to prevent blocking)
                    # Only log warnings if proctoring is active (technical interview started)
                    if self._proctoring_active:
                        try:
                            from .models import InterviewSession, WarningLog
                            from django.db import transaction
                            # Use select_for_update with nowait to prevent blocking
                            try:
                                session = InterviewSession.objects.select_for_update(nowait=True).get(id=self.session_id)
                                with transaction.atomic():
                                    WarningLog.objects.create(
                                        session=session,
                                        warning_type=warning_type,
                                        snapshot=snapshot_filename
                                    )
                            except Exception as db_error:
                                # Skip database logging if it would block - snapshot is still saved
                                # Only print if it's not the expected "no column named snapshot" error
                                if 'snapshot' not in str(db_error).lower():
                                    pass  # Other errors are silently skipped
                        except Exception as e:
                            # Silently continue - snapshot was saved, DB logging is optional
                            pass
                    else:
                        # Proctoring not active yet (still in identity verification), don't save warnings
                        print(f"⚠️ Warning detected but proctoring not active yet - skipping snapshot save")
                    
                    warning_queue.task_done()
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"[Proctoring] Background logger error: {e}")
        
        logger_thread = threading.Thread(target=_background_warning_logger, daemon=True)
        logger_thread.start()
        self._warning_logger_queue = warning_queue
        
        # YOLO detection frequency - run every ~1.5 seconds to significantly reduce CPU usage
        last_yolo_time = _t.time()
        YOLO_INTERVAL = 1.5  # Run YOLO every 1.5 seconds (reduced from 0.5s for better performance)
        
        # Add debouncing for absence warning - require continuous absence for 3 seconds
        absence_start_time = None
        ABSENCE_THRESHOLD_SEC = 3.0  # Must be absent for 3 seconds before warning
        
        while self._running:
            try:
                # Check if video is still opened, try to reopen if needed (but don't spam logs)
                if not self.video.isOpened():
                    # Only print warning every 30 seconds to reduce log spam
                    now_check = _t.time()
                    if not hasattr(self, '_last_reopen_attempt_time'):
                        self._last_reopen_attempt_time = 0
                    if now_check - self._last_reopen_attempt_time > 30:
                        print(f"⚠️ Camera closed for session {str(self.session_id)[:8]}, attempting to reopen...")
                        self._last_reopen_attempt_time = now_check
                    
                    try:
                        if hasattr(self.video, 'cap') and self.video.cap:
                            self.video.release()
                        self.video = _VideoCapture()
                        if not self.video.isOpened():
                            time.sleep(2.0)  # Wait longer before retry
                            continue
                        else:
                            print(f"✅ Camera successfully reopened for session {str(self.session_id)[:8]}")
                    except Exception as e:
                        if now_check - self._last_reopen_attempt_time <= 30:
                            # Only log if we haven't logged recently
                            pass
                        time.sleep(2.0)
                        continue
                
                ret, frame = self.video.read()
                if not ret or frame is None:
                    time.sleep(0.1)  # Increased sleep to reduce CPU when camera fails
                    continue
                
                # Record frame to video file (parallel with YOLO detection)
                if self._recording_active and self._video_writer is not None:
                    try:
                        # Resize frame to match recording dimensions if needed
                        if frame.shape[1] != self._frame_width or frame.shape[0] != self._frame_height:
                            frame_resized = cv2.resize(frame, (self._frame_width, self._frame_height))
                        else:
                            frame_resized = frame
                        
                        # Write frame with timestamp tracking
                        current_time = _t.time()
                        
                        # Mark first frame as written (timestamp already recorded in start_video_recording)
                        if not self._first_frame_written:
                            self._first_frame_written = True
                            print(f"🕐 FIRST FRAME WRITTEN - Video recording timestamp was: {self._recording_start_timestamp}")
                        
                        if self._last_frame_time is not None:
                            self._frame_timestamps.append(current_time - self._last_frame_time)
                        self._last_frame_time = current_time
                        
                        self._video_writer.write(frame_resized)
                    except Exception as e:
                        print(f"⚠️ Error writing frame to video: {e}")
                
                # Save latest frame (only update if lock is available quickly)
                if self._frame_lock is not None:
                    try:
                        # Use non-blocking lock acquisition to prevent blocking
                        if self._frame_lock.acquire(blocking=False):
                            try:
                                self._latest_frame = frame.copy()
                            finally:
                                self._frame_lock.release()
                        else:
                            # Lock is held, skip frame update this cycle (reduces blocking)
                            pass
                    except Exception:
                        pass
                
                # Run detections - YOLO only every 0.5s to reduce CPU usage
                has_person = False
                multiple_people = False
                phone_detected = False
                
                now_ts = _t.time()
                should_run_yolo = (now_ts - last_yolo_time) >= YOLO_INTERVAL

                # Only run YOLO if proctoring is active (technical interview has started)
                # Skip YOLO during identity verification
                if should_run_yolo and self._yolo is not None and self._proctoring_active:
                    try:
                        # Run YOLO with lower confidence for sensitivity; small imgsz for speed
                        results = self._yolo.predict(source=frame, imgsz=480, conf=0.35, iou=0.45, verbose=False)
                        if results and len(results) > 0:
                            r0 = results[0]
                            # Map class indices to names
                            names = r0.names if hasattr(r0, 'names') else getattr(self._yolo, 'names', {})
                            cls = r0.boxes.cls.cpu().numpy().tolist() if hasattr(r0, 'boxes') and r0.boxes is not None else []
                            labels = [str(names.get(int(c), str(int(c)))) for c in cls]
                            person_count = sum(1 for l in labels if l.lower() == 'person')
                            phone_count = sum(1 for l in labels if 'phone' in l.lower())
                            has_person = person_count >= 1
                            multiple_people = person_count >= 2
                            phone_detected = phone_count >= 1
                        last_yolo_time = now_ts
                    except Exception as e:
                        # Fall back to Haar if YOLO fails mid-run
                        print(f"⚠️ YOLO detection error; falling back to Haar: {e}")
                        self._yolo = None

                if self._yolo is None or not should_run_yolo:
                    # Haar-based fallback (always runs, or when YOLO skipped)
                    faces = []
                    try:
                        if face_cascade is not None:
                            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
                    except Exception:
                        faces = []
                    face_count = len(faces) if faces is not None else 0
                    # Only update if YOLO didn't run (to preserve YOLO results)
                    if self._yolo is None or not should_run_yolo:
                        has_person = face_count >= 1
                        multiple_people = face_count >= 2
                    # phone_detected remains False in Haar fallback

                # Update warnings from detections with logging - ensure state is always fresh
                prev_no_person = self._last_warning_state.get("no_person", False)
                prev_warning_active = self._last_warning_state.get("no_person_warning_active", False)
                prev_multiple = self._last_warning_state.get("multiple_people", False)
                prev_phone = self._last_warning_state.get("phone_detected", False)
                
                # Debounced absence detection - require continuous absence for threshold duration
                now_abs = _t.time()
                if not has_person:
                    # Person is absent - start/continue tracking absence duration
                    if absence_start_time is None:
                        absence_start_time = now_abs
                    absence_duration = now_abs - absence_start_time
                    
                    # Only activate warning if absent for threshold duration
                    if absence_duration >= ABSENCE_THRESHOLD_SEC:
                        self._last_warning_state["no_person"] = True
                        self._last_warning_state["no_person_warning_active"] = True
                    else:
                        # Still within threshold - don't activate warning yet
                        self._last_warning_state["no_person"] = False
                        self._last_warning_state["no_person_warning_active"] = False
                else:
                    # Person is present - reset absence tracking immediately
                    absence_start_time = None
                    self._last_warning_state["no_person"] = False
                    self._last_warning_state["no_person_warning_active"] = False
                
                # Update other warning states
                self._last_warning_state["multiple_people"] = multiple_people
                self._last_warning_state["phone_detected"] = phone_detected
                
                # Clear warnings when conditions are no longer met
                if has_person and prev_warning_active:
                    # Person returned - clear no_person warnings
                    self._last_warning_logged.pop('no_person', None)
                if not multiple_people and prev_multiple:
                    # Multiple people cleared
                    self._last_warning_state["multiple_people"] = False
                if not phone_detected and prev_phone:
                    # Phone cleared
                    self._last_warning_state["phone_detected"] = False
                
                # Log warnings to database with snapshots when they occur (non-blocking via queue)
                self._log_warning_with_snapshot_async('multiple_people', multiple_people, prev_multiple, frame)
                self._log_warning_with_snapshot_async('phone_detected', phone_detected, prev_phone, frame)
                
                # Handle no_person warning - only log when warning becomes active (not just when person absent)
                current_warning_active = self._last_warning_state.get("no_person_warning_active", False)
                if current_warning_active and not prev_warning_active:
                    # Warning just became active - log it
                    self._log_warning_with_snapshot_async('no_person', True, False, frame, rate_limit_seconds=15)
                elif has_person and prev_warning_active:
                    # Person returned - reset rate limit when person returns
                    self._last_warning_logged.pop('no_person', None)

                # Motion-based detection (low concentration only)
                try:
                    gray_small = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    gray_small = cv2.resize(gray_small, (160, 120))
                    if last_gray is not None:
                        diff = cv2.absdiff(gray_small, last_gray)
                        motion_score = float(diff.mean())
                        now_ts = _t.time()
                        
                        # Low concentration detection
                        prev_low_concentration = self._last_warning_state.get("low_concentration", False)
                        if motion_score > MOTION_LOW_THRESH:
                            last_motion_ts = now_ts
                            # Clear low concentration when motion detected
                            if prev_low_concentration:
                                self._last_warning_state["low_concentration"] = False
                        # Low concentration if no meaningful motion for a window and a person present
                        low_concentration = has_person and (now_ts - last_motion_ts) >= LOW_MOTION_WINDOW_SEC
                        self._last_warning_state["low_concentration"] = low_concentration
                        
                        # Log low concentration warning with snapshot when first detected
                        if low_concentration and not prev_low_concentration:
                            self._log_warning_with_snapshot_async('low_concentration', True, False, frame)
                        # Clear when person moves
                        elif not low_concentration and prev_low_concentration:
                            self._last_warning_state["low_concentration"] = False
                    last_gray = gray_small
                except Exception as e:
                    # Motion detection errors are not critical - continue silently
                    pass
                # Sleep to cap CPU usage - increased to reduce load
                time.sleep(0.2)  # Increased from 0.1s to 0.2s to cut CPU usage in half
            except Exception as e:
                print(f"⚠️ Detection loop error: {e}")
                time.sleep(0.1)

    def get_frame(self) -> bytes:
        """Get a frame as JPEG bytes."""
        try:
            # Check if video is opened - if not, return fallback (don't try to reopen here as detection loop handles it)
            if not self.video.isOpened():
                return self._create_fallback_frame()
            
            frame = None
            # Try to get frame from detection loop buffer first (most efficient)
            # Use non-blocking lock to prevent get_frame() from blocking
            if self._frame_lock is not None:
                try:
                    if self._frame_lock.acquire(blocking=False):
                        try:
                            if self._latest_frame is not None:
                                frame = self._latest_frame.copy()
                        finally:
                            self._frame_lock.release()
                except Exception as e:
                    pass
            
            # If no buffered frame, read directly from camera (fallback)
            if frame is None:
                try:
                    ret, tmp = self.video.read()
                    if ret and tmp is not None and tmp.size > 0:
                        frame = tmp
                        # Also update the buffer if we got a frame (non-blocking)
                        if self._frame_lock is not None:
                            try:
                                if self._frame_lock.acquire(blocking=False):
                                    try:
                                        self._latest_frame = frame.copy()
                                    finally:
                                        self._frame_lock.release()
                            except:
                                pass
                except Exception:
                    pass
            
            # If we have a valid frame, add overlays and encode
            if frame is not None and frame.size > 0:
                try:
                    # Add overlays
                    import time as time_module
                    timestamp = time_module.strftime("%H:%M:%S")
                    cv2.putText(frame, timestamp, (20, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    session_text = f"Session: {str(self.session_id)[:8]}"
                    cv2.putText(frame, session_text, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    
                    # Add "LIVE" indicator to show feed is active
                    cv2.rectangle(frame, (frame.shape[1] - 120, 10), (frame.shape[1] - 10, 40), (0, 255, 0), -1)
                    cv2.putText(frame, "LIVE", (frame.shape[1] - 110, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
                    
                    # Encode as JPEG with lower quality for faster transmission
                    ok, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    if ok and buf is not None and len(buf) > 0:
                        return buf.tobytes()
                except Exception as e:
                    print(f"[Camera] Error encoding frame: {e}")
                    pass
            
            # Fallback if all else fails
            return self._create_fallback_frame()
        except Exception as e:
            print(f"[Camera] Error in get_frame: {e}")
            return self._create_fallback_frame()

    def _create_fallback_frame(self) -> bytes:
        """Create a fallback frame when camera is not available."""
        # Only print warning every 10 seconds to reduce log spam
        now = time.time()
        if now - self._fallback_print_time > 10:
            print(f"⚠️ Camera not available for session {str(self.session_id)[:8]}... using fallback frames")
            self._fallback_print_time = now
        
        # Cache fallback frame for 1 second to avoid regenerating
        if self._cached_fallback_frame is None or (now - self._fallback_frame_cache_time) > 1.0:
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            
            # Add session info with green background box
            text = f"Session: {str(self.session_id)[:8]}"
            cv2.rectangle(frame, (10, 20), (630, 60), (0, 128, 0), -1)
            cv2.putText(frame, text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # Add status message with background
            if not self.video.isOpened():
                status_text = "Camera Not Available"
                text_size = cv2.getTextSize(status_text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
                cv2.rectangle(frame, (10, 70), (20 + text_size[0], 110), (0, 0, 128), -1)
                cv2.putText(frame, status_text, (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            else:
                status_text = "Camera Loading..."
                text_size = cv2.getTextSize(status_text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
                cv2.rectangle(frame, (10, 70), (20 + text_size[0], 110), (128, 128, 128), -1)
                cv2.putText(frame, status_text, (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # Add timestamp with background
            timestamp = time.strftime("%H:%M:%S")
            text_size = cv2.getTextSize(timestamp, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            cv2.rectangle(frame, (10, frame.shape[0] - 35), (20 + text_size[0], frame.shape[0] - 5), (64, 64, 64), -1)
            cv2.putText(frame, timestamp, (20, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Add a pulsing indicator in the corner to show stream is alive
            import time as time_module
            pulse = int(time_module.time() * 2) % 2
            cv2.circle(frame, (620, 30), 10, (0, 255, 0) if pulse else (0, 128, 0), -1)
            
            ok, buf = cv2.imencode('.jpg', frame)
            if ok and buf is not None and len(buf) > 0:
                self._cached_fallback_frame = buf.tobytes()
                self._fallback_frame_cache_time = now
                return self._cached_fallback_frame
            else:
                # Last resort: return a minimal valid JPEG
                return b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x01\xe0\x02\x80\x03\x01"\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
        else:
            # Return cached fallback frame
            return self._cached_fallback_frame

    def _log_warning_with_snapshot_async(self, warning_type, current_state, prev_state, frame, rate_limit_seconds=2):
        """Log warning to database with snapshot capture (non-blocking via background thread).
        
        Args:
            warning_type: Type of warning (e.g., 'multiple_people', 'phone_detected')
            current_state: Current warning state (True/False)
            prev_state: Previous warning state (True/False)
            frame: Current camera frame (numpy array)
            rate_limit_seconds: Minimum seconds between logs for same warning (default 2)
        """
        # Only log warnings if proctoring is active (technical interview has started)
        # Skip warnings during identity verification
        if not self._proctoring_active:
            return
        
        # Only log when warning first becomes active (transitions from False to True)
        if not current_state or prev_state:
            return
        
        # Rate limiting to avoid spam - increased for better performance
        now = time.time()
        last_logged = self._last_warning_logged.get(warning_type, 0)
        # Increased default rate limit to 10 seconds for most warnings, 15 seconds for no_person
        effective_rate_limit = 15 if warning_type == 'no_person' else (10 if rate_limit_seconds < 10 else rate_limit_seconds)
        if now - last_logged < effective_rate_limit:
            return
        
        # Update warning count and timestamp immediately (non-blocking)
        self._warning_counts[warning_type] = self._warning_counts.get(warning_type, 0) + 1
        self._last_warning_logged[warning_type] = now
        
        # Queue warning for background thread (non-blocking I/O)
        try:
            if hasattr(self, '_warning_logger_queue'):
                snapshot_filename = None
                if frame is not None:
                    ts = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
                    session_id_str = str(self.session_id)
                    snapshot_filename = f"{session_id_str}_{warning_type}_{ts}.jpg"
                
                # Copy frame to avoid reference issues
                frame_copy = frame.copy() if frame is not None else None
                
                # Try to put in queue (non-blocking if queue is full)
                try:
                    self._warning_logger_queue.put_nowait((warning_type, frame_copy, snapshot_filename))
                except:
                    # Queue full - skip this warning to avoid blocking
                    pass
        except Exception as e:
            print(f"[Proctoring] Failed to queue warning {warning_type}: {e}")

    def get_latest_warnings(self) -> dict:
        """Get current warning states and include warning counts."""
        warnings = self._last_warning_state.copy()
        # Ensure all expected keys exist with default False
        expected_keys = [
            'no_person_warning_active', 'multiple_people', 'phone_detected',
            'no_person', 'low_concentration', 'tab_switched',
            'excessive_noise', 'multiple_speakers'
        ]
        for key in expected_keys:
            if key not in warnings:
                warnings[key] = False
        # Add warning counts as metadata (can be used for display)
        warnings['_counts'] = self._warning_counts.copy()
        return warnings
    
    def get_warning_counts(self) -> dict:
        """Get warning counts for the session."""
        return self._warning_counts.copy()

    def set_tab_switch_status(self, hidden: bool) -> None:
        """Set tab switch status and log warning with snapshot if tab was switched."""
        prev_tab_switched = self._last_warning_state.get("tab_switched", False)
        self._last_warning_state["tab_switched"] = bool(hidden)
        
        # Log warning when tab is switched (becomes True)
        if hidden and not prev_tab_switched:
            # Get latest frame for snapshot (non-blocking)
            frame = None
            if self._frame_lock is not None:
                try:
                    if self._frame_lock.acquire(blocking=False):
                        try:
                            if self._latest_frame is not None:
                                frame = self._latest_frame.copy()
                        finally:
                            self._frame_lock.release()
                except:
                    pass
            
            if frame is not None:
                self._log_warning_with_snapshot_async('tab_switched', True, False, frame, rate_limit_seconds=3)

    def cleanup(self):
        """Clean up camera resources and return video path if recording was active."""
        print(f"🧹 Cleaning up simple camera for session {self.session_id}")
        video_path = None
        try:
            self._running = False
            # Stop video recording before cleanup
            video_path = self.stop_video_recording()
            
            # Join thread if exists
            t = getattr(self, '_detector_thread', None)
            if t and t.is_alive():
                t.join(timeout=1.5)
        except Exception as e:
            print(f"⚠️ Error during camera cleanup: {e}")
        if self.video:
            self.video.release()
        print(f"✅ Simple camera cleanup completed for session {self.session_id}")
        return video_path

    def _find_audio_file_for_session(self):
        """Attempt to locate the most recent audio file for this session."""
        try:
            from interview_app.models import InterviewSession
            session = InterviewSession.objects.get(id=self.session_id)
            session_key = session.session_key
        except Exception as e:
            print(f"⚠️ Could not resolve session key for audio lookup: {e}")
            session_key = None
        
        audio_dir = os.path.join(settings.MEDIA_ROOT, 'interview_audio')
        if not os.path.isdir(audio_dir):
            return None
        
        prefixes = []
        if session_key:
            prefixes.append(session_key)
        prefixes.append(str(self.session_id))
        
        latest_file = None
        latest_mtime = 0
        
        for filename in os.listdir(audio_dir):
            for prefix in prefixes:
                if filename.startswith(prefix):
                    path = os.path.join(audio_dir, filename)
                    try:
                        mtime = os.path.getmtime(path)
                        if mtime > latest_mtime:
                            latest_file = path
                            latest_mtime = mtime
                    except OSError:
                        continue
        
        if latest_file:
            print(f"🔎 Auto-detected audio file: {latest_file}")
        return latest_file
