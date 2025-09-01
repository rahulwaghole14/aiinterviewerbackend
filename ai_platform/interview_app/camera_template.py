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

