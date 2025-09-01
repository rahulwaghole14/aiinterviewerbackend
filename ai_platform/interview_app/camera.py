import threading
import os
import time
import atexit
import wave
from django.db import connection
from .models import InterviewSession, WarningLog

# Make heavy imports optional
try:
    import cv2
    CV2_AVAILABLE = True
except (ImportError, OSError):
    CV2_AVAILABLE = False
    cv2 = None

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    YOLO = None

try:
    import torch
    TORCH_AVAILABLE = True
except (ImportError, OSError):
    TORCH_AVAILABLE = False
    torch = None

try:
    from scipy.spatial import distance as dist
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    dist = None

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except (ImportError, OSError):
    SOUNDDEVICE_AVAILABLE = False
    sd = None

try:
    from pyannote.audio import Pipeline
    PYANNOTE_AVAILABLE = True
except ImportError:
    PYANNOTE_AVAILABLE = False
    Pipeline = None

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except (ImportError, OSError):
    MEDIAPIPE_AVAILABLE = False
    mp = None

try:
    import ffmpeg
    FFMPEG_AVAILABLE = True
except (ImportError, OSError):
    FFMPEG_AVAILABLE = False
    ffmpeg = None

# IMPORTANT: Use environment variable for Hugging Face token!
HF_TOKEN = os.environ.get('HF_TOKEN', None)

# --- TUNED PARAMETERS ---
NO_PERSON_WARNING_SECONDS = 30

# --- UNIFIED AUDIO MONITOR ---
class UnifiedAudioMonitor:
    def __init__(self, temp_audio_path, noise_threshold=40, grace_period_seconds=3):
        self.lock = threading.RLock()
        self.temp_audio_path = temp_audio_path
        self.audio_file = None
        self.noise_threshold, self.noise_grace_period = noise_threshold, grace_period_seconds
        self.is_noisy, self.noisy_start_time = False, None
        self.speaker_grace_period, self.speaker_warning_active, self.speaker_warning_start_time = grace_period_seconds, False, None
        self.pipeline, self.SAMPLE_RATE, self.is_recording = None, 16000, True
        self.CHUNK_SAMPLES = int(1 * self.SAMPLE_RATE)

        if not HF_TOKEN or "YOUR_HUGGING" in HF_TOKEN:
            print("WARNING: Hugging Face token not set. Speaker detection disabled.")
        else:
            try:
                self.pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token=HF_TOKEN)
            except Exception as e:
                print(f"FATAL: Could not load pyannote model: {e}")

        self.thread = threading.Thread(target=self.start_monitoring, daemon=True)
        self.thread.start()

    def get_statuses(self):
        with self.lock:
            return {"noise": self.is_noisy, "speakers": self.speaker_warning_active}

    def process_audio_chunk(self, indata):
        volume_norm = np.linalg.norm(indata) * 10
        with self.lock:
            if volume_norm > self.noise_threshold:
                if self.noisy_start_time is None:
                    self.noisy_start_time = time.time()
                if (time.time() - self.noisy_start_time) > self.noise_grace_period:
                    self.is_noisy = True
            else:
                self.noisy_start_time, self.is_noisy = None, False

        if self.pipeline:
            try:
                audio_tensor = torch.from_numpy(indata.T).float()
                num_speakers = len(self.pipeline({"waveform": audio_tensor, "sample_rate": self.SAMPLE_RATE}).labels())
                with self.lock:
                    if num_speakers > 1:
                        if self.speaker_warning_start_time is None:
                            self.speaker_warning_start_time = time.time()
                        if (time.time() - self.speaker_warning_start_time) > self.speaker_grace_period:
                            self.speaker_warning_active = True
                    else:
                        self.speaker_warning_start_time, self.speaker_warning_active = None, False
            except Exception:
                pass

    def close_audio_file(self):
        if self.audio_file:
            try:
                self.audio_file.close()
            except Exception:
                pass

    def start_monitoring(self):
        try:
            self.audio_file = wave.open(self.temp_audio_path, 'wb')
            self.audio_file.setnchannels(1)
            self.audio_file.setsampwidth(2)
            self.audio_file.setframerate(self.SAMPLE_RATE)
            with sd.InputStream(callback=self.audio_callback, channels=1, samplerate=self.SAMPLE_RATE, blocksize=self.CHUNK_SAMPLES, dtype='int16'):
                while self.is_recording:
                    time.sleep(1.0)
        except Exception as e:
            print(f"FATAL: Could not start unified audio monitor: {e}")

    def audio_callback(self, indata, frames, time_info, status):
        if self.audio_file and self.is_recording:
            try:
                self.audio_file.writeframes(indata.tobytes())
            except (ValueError, AttributeError):
                pass # Ignore errors on fast shutdown

# --- MOVEMENT DETECTOR CLASS (FULL CODE RESTORED) ---
class MovementDetector:
    def __init__(self, movement_threshold=250, grace_period=1.2):
        self.background, self.movement_threshold = None, movement_threshold
        self.grace_period, self.movement_counter = grace_period, 0

    def detect(self, frame):
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            if self.background is None:
                self.background = gray
                return False
            frame_delta = cv2.absdiff(self.background, gray)
            thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=2)
            contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if sum(cv2.contourArea(c) for c in contours) > self.movement_threshold:
                self.movement_counter += 1
            else:
                self.movement_counter = 0
            self.background = gray
            return self.movement_counter >= self.grace_period
        except Exception:
            return False

# --- EYE TRACKER CLASS (FULL CODE RESTORED) ---
class EyeTracker:
    def __init__(self, ear_threshold=0.25, ear_consecutive_frames=8):
        self.ear_threshold, self.ear_consecutive_frames, self.gaze_counter = ear_threshold, ear_consecutive_frames, 0
        self.face_mesh = None
        try:
            self.mp_face_mesh = mp.solutions.face_mesh
            self.face_mesh = self.mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5, min_tracking_confidence=0.5)
        except Exception as e:
            print(f"FATAL: Could not initialize MediaPipe Face Mesh: {e}")
        self.LEFT_EYE_INDICES = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
        self.RIGHT_EYE_INDICES = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]

    def eye_aspect_ratio(self, landmarks, eye_indices):
        eye_points = np.array([[landmarks[i].x, landmarks[i].y] for i in eye_indices])
        p1, p4, p2, p6, p3, p5 = eye_points[8], eye_points[0], eye_points[12], eye_points[4], eye_points[14], eye_points[6]
        A, B, C = dist.euclidean(p2, p6), dist.euclidean(p3, p5), dist.euclidean(p1, p4)
        return (A + B) / (2.0 * C)

    def detect(self, frame):
        if not self.face_mesh:
            return False
        try:
            results = self.face_mesh.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            if not results.multi_face_landmarks:
                self.gaze_counter += 1
            else:
                landmarks = results.multi_face_landmarks[0].landmark
                ear = (self.eye_aspect_ratio(landmarks, self.LEFT_EYE_INDICES) + self.eye_aspect_ratio(landmarks, self.RIGHT_EYE_INDICES)) / 2.0
                if ear < self.ear_threshold:
                    self.gaze_counter += 1
                else:
                    self.gaze_counter = 0
            return self.gaze_counter >= self.ear_consecutive_frames
        except Exception:
            return False

    def __del__(self):
        if self.face_mesh:
            self.face_mesh.close()

# --- MAIN VIDEOCAMERA CLASS ---
class VideoCamera:
    def __init__(self, session_id):
        self.session_id = session_id
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"--- AI models will run on device: {self.device.upper()} ---")
        self.lock = threading.RLock()
        self.screenshot_dir = os.path.join(settings.MEDIA_ROOT, 'proctoring_evidence'); os.makedirs(self.screenshot_dir, exist_ok=True)
        self.recording_dir = os.path.join(settings.MEDIA_ROOT, 'proctoring_recordings'); os.makedirs(self.recording_dir, exist_ok=True)
        ts = time.strftime("%Y%m%d-%H%M%S")
        self.temp_video_path, self.temp_audio_path = os.path.join(self.recording_dir, f"temp_video_{ts}.avi"), os.path.join(self.recording_dir, f"temp_audio_{ts}.wav")
        self.final_video_path = os.path.join(self.recording_dir, f"session_{ts}.mp4")
        self.is_recording = True
        self.video_writer = None
        self.movement_detector = MovementDetector()
        self.eye_tracker = EyeTracker()
        self.audio_monitor = UnifiedAudioMonitor(self.temp_audio_path)
        self.object_model = None
        try:
            self.object_model, self.PERSON_CLASS, self.PHONE_CLASS = YOLO('yolov8n.pt'), 0, 67
        except Exception as e:
            print(f"FATAL: Error loading AI model: {e}")
        
        self.video = cv2.VideoCapture(0)
        if not self.video.isOpened():
            raise RuntimeError("Could not start camera.")
        
        self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        w, h = int(self.video.get(3)), int(self.video.get(4))
        self.setup_video_writer(w, h, 20)
        self.frame = None
        self.frame_counter = 0
        self.AI_PROCESS_EVERY_N_FRAMES = 15
        self.IGNORE_SCREENSHOT_WARNINGS = {'tab_switched', 'excessive_noise', 'multiple_speakers', 'excessive_movement'}
        self.warnings = {"multiple_people": False, "phone_detected": False, "no_person": False, "low_concentration": False, "tab_switched": False, "no_person_warning_active": False,# "excessive_movement": False,
                        "excessive_noise": False, "multiple_speakers": False}
        self.last_warning_state = self.warnings.copy()
        self.no_person_start_time = None
        self.thread = threading.Thread(target=self.update, daemon=True)
        self.thread.start()
        atexit.register(self.cleanup)

    def cleanup(self):
        self.is_recording = False
        time.sleep(1.5)
        if self.video: self.video.release()
        if self.video_writer: self.video_writer.release()
        if self.audio_monitor: self.audio_monitor.is_recording = False; self.audio_monitor.close_audio_file()
        try:
            if not os.path.exists(self.temp_video_path) or not os.path.exists(self.temp_audio_path):
                return
            input_video, input_audio = ffmpeg.input(self.temp_video_path), ffmpeg.input(self.temp_audio_path)
            ffmpeg.output(input_video, input_audio, self.final_video_path, vcodec='copy', acodec='aac').run(quiet=True, overwrite_output=True)
            
            # Save video reference to database
            if os.path.exists(self.final_video_path):
                try:
                    from django.core.files import File
                    from django.utils import timezone
                    
                    session = InterviewSession.objects.get(id=self.session_id)
                    with open(self.final_video_path, 'rb') as video_file:
                        session.recording_video.save(
                            f"interview_recording_{self.session_id}.mp4",
                            File(video_file),
                            save=True
                        )
                    session.recording_created_at = timezone.now()
                    session.save()
                    print(f"--- Video recording saved to database for session {self.session_id} ---")
                except Exception as e:
                    print(f"--- Error saving video to database: {e} ---")
                    
        except Exception as e:
            print(f"--- FATAL: An error occurred during file merge: {e} ---")
        finally:
            if os.path.exists(self.temp_video_path): os.remove(self.temp_video_path)
            if os.path.exists(self.temp_audio_path): os.remove(self.temp_audio_path)

    def __del__(self):
        pass

    def setup_video_writer(self, width, height, fps):
        self.video_writer = cv2.VideoWriter(self.temp_video_path, cv2.VideoWriter_fourcc(*'XVID'), fps, (width, height))

    def save_warning_screenshot(self, frame, warning_type):
        try:
            filepath = os.path.join(self.screenshot_dir, f"{time.strftime('%Y%m%d-%H%M%S')}_{warning_type}.jpg")
            cv2.putText(frame, f"WARNING: {warning_type.replace('_', ' ').upper()}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.imwrite(filepath, frame)
        except Exception as e:
            print(f"Error saving screenshot: {e}")

    def get_latest_warnings(self):
        with self.lock:
            return self.warnings.copy()

    def set_tab_switch_status(self, status):
        with self.lock:
            self.warnings["tab_switched"] = status

    def get_frame(self):
        with self.lock:
            if self.frame is None:
                return self.create_placeholder_frame("Loading Stream...")
            _, jpeg = cv2.imencode('.jpg', self.frame)
            return jpeg.tobytes()

    def update(self):
        from .models import WarningLog
        while self.is_recording:
            try:
                if not self.video or not self.video.isOpened():
                    break
                ret, frame = self.video.read()
                if not ret:
                    time.sleep(0.1)
                    continue

                if self.video_writer:
                    self.video_writer.write(frame)

                with self.lock:
                    # self.warnings["excessive_movement"] = self.movement_detector.detect(frame.copy())
                    self.warnings["low_concentration"] = self.eye_tracker.detect(frame.copy())
                    audio_statuses = self.audio_monitor.get_statuses()
                    self.warnings["multiple_speakers"], self.warnings["excessive_noise"] = audio_statuses["speakers"], audio_statuses["noise"]

                    self.frame_counter += 1
                    if self.frame_counter % self.AI_PROCESS_EVERY_N_FRAMES == 0:
                        self.process_frame_for_yolo(frame.copy())

                    with self.lock:
                        if self.warnings["no_person"]:
                            if self.no_person_start_time is None:
                                self.no_person_start_time = time.time()
                            elif time.time() - self.no_person_start_time > NO_PERSON_WARNING_SECONDS:
                                self.warnings["no_person_warning_active"] = True
                        else:
                            self.no_person_start_time = None
                            self.warnings["no_person_warning_active"] = False

                        for warning_type, is_active in self.warnings.items():
                            if is_active and not self.last_warning_state.get(warning_type, False):
                                WarningLog.objects.create(session_id=self.session_id, warning_type=warning_type)
                                print(f"!!! New warning logged: {warning_type} !!!")
                                if warning_type not in self.IGNORE_SCREENSHOT_WARNINGS:
                                    threading.Thread(target=self.save_warning_screenshot, args=(frame.copy(), warning_type)).start()

                        self.last_warning_state = self.warnings.copy()
                        self.frame = frame
            except Exception as e:
                print(f"ERROR in camera update loop: {e}")
                time.sleep(1)

    def process_frame_for_yolo(self, frame):
        try:
            results = self.object_model.predict(frame, classes=[self.PERSON_CLASS, self.PHONE_CLASS], device=self.device, verbose=False, conf=0.25)
            person_detections, phone_count = [], 0
            if results:
                for r in results:
                    for box in r.boxes:
                        cls = int(box.cls)
                        if cls == self.PERSON_CLASS:
                            person_detections.append((box.xyxy[0][2] - box.xyxy[0][0]) * (box.xyxy[0][3] - box.xyxy[0][1]))
                        elif cls == self.PHONE_CLASS:
                            phone_count += 1
            
            person_count = 0
            if person_detections:
                person_detections.sort(reverse=True)
                main_person_area = person_detections[0]
                person_count = 1
                for area in person_detections[1:]:
                    if area / main_person_area > 0.35:
                        person_count += 1
            
            with self.lock:
                self.warnings["no_person"] = person_count == 0
                self.warnings["multiple_people"] = person_count > 1
                self.warnings["phone_detected"] = phone_count > 0
        except Exception as e:
            print(f"Error in YOLO processing: {e}")

    def create_placeholder_frame(self, text):
        placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(placeholder, text, (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        _, jpeg = cv2.imencode('.jpg', placeholder)
        return jpeg.tobytes()