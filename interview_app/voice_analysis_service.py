"""
Voice Analysis Service for Interview Project
Handles Voice Activity Detection and Speaker Diarization using Hugging Face models
"""
import os
import json
import logging
import time
import threading
import queue
import cv2
import numpy as np
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from .models import (
    InterviewSession, 
    InterviewQuestion, 
)
from .voice_models import (
    VoiceActivityDetection, 
    SpeakerDiarization,
    AnswerVoiceAnalysis,
)
from .yolo_camera import SimpleRealVideoCamera

logger = logging.getLogger(__name__)

class VoiceAnalysisService:
    """Service for voice activity detection and speaker diarization"""
    
    def __init__(self):
        self.hf_token = os.getenv('HUGGINGFACE_TOKEN', '')
        self.vad_model = None
        self.diarization_model = None
        self._models_loaded = False
        # Don't load models immediately - use lazy loading
    
    def _ensure_models_loaded(self):
        """Load models if not already loaded"""
        if self._models_loaded:
            return True
            
        try:
            if not self.hf_token:
                logger.warning("HUGGINGFACE_TOKEN not found in environment variables")
                return False
            
            # Save token to huggingface hub
            from huggingface_hub import HfFolder
            HfFolder.save_token(self.hf_token)
            logger.info("HuggingFace token saved to HfFolder")
            
            # Import here to avoid import errors if models are not installed
            try:
                from pyannote.audio import Pipeline
                import torch
                
                # Load Voice Activity Detection model
                logger.info("Loading Voice Activity Detection model...")
                self.vad_model = Pipeline.from_pretrained(
                    "pyannote/voice-activity-detection",
                    use_auth_token=self.hf_token
                )
                logger.info("✅ VAD model loaded successfully")
                
                # Load Speaker Diarization model
                logger.info("Loading Speaker Diarization model...")
                self.diarization_model = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=self.hf_token
                )
                logger.info("✅ Diarization model loaded successfully")
                
                # Move to GPU if available
                if torch.cuda.is_available():
                    self.diarization_model = self.diarization_model.to(torch.device("cuda"))
                    logger.info("Models loaded on GPU")
                else:
                    logger.info("Models loaded on CPU")
                
                # Verify models are actually loaded
                if self.vad_model is None or self.diarization_model is None:
                    logger.error("Models failed to load properly")
                    return False
                
                self._models_loaded = True
                return True
                    
            except ImportError as e:
                logger.error(f"Failed to import required libraries: {e}")
                logger.error("Please install: pyannote.audio, torch")
                return False
                
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def analyze_complete_interview_audio(self, audio_file_path, session_key):
        """
        Analyze the complete interview audio file for overall voice analysis
        
        Args:
            audio_file_path (str): Path to the complete interview audio file
            session_key (str): Interview session key
            
        Returns:
            dict: Overall analysis results for the entire interview
        """
        try:
            # Ensure models are loaded before analysis
            if not self._ensure_models_loaded():
                logger.error("Voice analysis models could not be loaded")
                return {
                    'error': 'Failed to load voice analysis models. Please check HUGGINGFACE_TOKEN and accept user agreements.',
                    'success': False
                }
            
            # Get session object
            session = InterviewSession.objects.get(session_key=session_key)
            
            logger.info(f"🎯 Analyzing complete interview audio: {audio_file_path}")
            
            # Perform Voice Activity Detection on entire audio
            vad_results = self._perform_overall_vad(audio_file_path, session)
            
            # Perform Speaker Diarization on entire audio
            diarization_results = self._perform_overall_diarization(audio_file_path, session)
            
            return {
                'vad': vad_results,
                'diarization': diarization_results,
                'success': True,
                'analysis_type': 'complete_interview'
            }
            
        except Exception as e:
            logger.error(f"Error analyzing complete interview audio: {e}")
            return {
                'error': str(e),
                'success': False
            }
    
    def _perform_overall_vad(self, audio_file_path, session):
        """Perform Voice Activity Detection on complete interview audio"""
        try:
            if not self.vad_model:
                logger.warning("VAD model not loaded")
                return None
            
            logger.info(f"🎙️ Performing overall VAD on complete interview: {audio_file_path}")
            
            # Run VAD on entire audio
            vad_result = self.vad_model(audio_file_path)
            
            # Extract metrics from pyannote VAD result
            # pyannote returns a Timeline object with segments
            total_duration = 0
            speech_duration = 0
            segments = []
            
            # Process VAD timeline
            for segment, track, label in vad_result.itertracks(yield_label=True):
                start_time = segment.start
                end_time = segment.end
                duration = end_time - start_time
                
                total_duration = max(total_duration, end_time)
                
                segments.append({
                    'start': start_time,
                    'end': end_time,
                    'label': label,
                    'duration': duration
                })
                
                if label == 'SPEECH':
                    speech_duration += duration
            
            pause_duration = total_duration - speech_duration
            
            # Calculate percentages
            speech_percentage = (speech_duration / total_duration * 100) if total_duration > 0 else 0
            silence_percentage = (pause_duration / total_duration * 100) if total_duration > 0 else 0
            
            # Clear any existing overall VAD records for this session
            VoiceActivityDetection.objects.filter(
                session=session, 
                question__isnull=True
            ).delete()
            
            # Save overall VAD record (no question associated)
            vad_record = VoiceActivityDetection.objects.create(
                session=session,
                question=None,  # No question - this is for the entire interview
                pause_duration=pause_duration,
                total_speech_time=speech_duration,
                speech_percentage=speech_percentage,
                silence_percentage=silence_percentage,
                vad_segments=segments,
                analysis_start_time=timezone.now(),
                analysis_end_time=timezone.now()
            )
            
            logger.info(f"✅ Overall VAD completed: Speech={speech_percentage:.1f}%, Silence={silence_percentage:.1f}%, Duration={total_duration:.1f}s")
            
            return {
                'id': str(vad_record.id),
                'total_duration': total_duration,
                'pause_duration': pause_duration,
                'total_speech_time': speech_duration,
                'speech_percentage': speech_percentage,
                'silence_percentage': silence_percentage,
                'segments': segments,
                'analysis_type': 'overall_interview'
            }
            
        except Exception as e:
            logger.error(f"Error in overall VAD analysis: {e}")
            return None
    
    def _perform_overall_diarization(self, audio_file_path, session):
        """Perform Speaker Diarization on complete interview audio"""
        try:
            if not self.diarization_model:
                logger.warning("Diarization model not loaded")
                return None
            
            logger.info(f"👥 Performing overall speaker diarization on complete interview: {audio_file_path}")
            
            # Run diarization on entire audio
            diarization = self.diarization_model(audio_file_path)
            
            # Process diarization results
            speaker_changes = 0
            speaker_change_timestamps = []
            speaker_labels = {}
            candidate_time = 0
            interviewer_time = 0
            
            # Track speakers and their speech time
            speaker_times = {}
            last_speaker = None
            
            # Iterate through diarization segments
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                start_time = turn.start
                end_time = turn.end
                duration = end_time - start_time
                
                # Track speaker changes
                if last_speaker != speaker:
                    speaker_changes += 1
                    speaker_change_timestamps.append(start_time)
                    last_speaker = speaker
                
                # Accumulate speaker time
                if speaker not in speaker_times:
                    speaker_times[speaker] = 0
                speaker_times[speaker] += duration
                
                # Track speaker labels
                if speaker not in speaker_labels:
                    speaker_labels[speaker] = []
                speaker_labels[speaker].append({
                    'start': start_time,
                    'end': end_time,
                    'duration': duration
                })
            
            # Determine number of speakers and handle single speaker with background noise
            num_speakers = len(speaker_times)
            total_speech_time = sum(speaker_times.values())
            
            # If 2 speakers detected but one is dominant (>65%), treat as single speaker
            if num_speakers == 2:
                dominant_speaker = max(speaker_times, key=speaker_times.get)
                dominant_time = speaker_times[dominant_speaker]
                dominant_percentage = (dominant_time / total_speech_time) * 100
                
                if dominant_percentage > 65:
                    logger.info(f"Dominant speaker {dominant_speaker} has {dominant_percentage:.1f}% of speech time - treating as single speaker")
                    num_speakers = 1
                    candidate_time = dominant_time
                    interviewer_time = 0
                else:
                    # Genuine multi-speaker scenario
                    # Assign candidate and interviewer based on speech time
                    sorted_speakers = sorted(speaker_times.items(), key=lambda x: x[1], reverse=True)
                    candidate_time = sorted_speakers[0][1]  # Most speaking time
                    interviewer_time = sorted_speakers[1][1]  # Second most speaking time
            elif num_speakers == 1:
                # Single speaker detected
                candidate_time = total_speech_time
                interviewer_time = 0
            else:
                # Multiple speakers detected
                sorted_speakers = sorted(speaker_times.items(), key=lambda x: x[1], reverse=True)
                if len(sorted_speakers) >= 1:
                    candidate_time = sorted_speakers[0][1]
                if len(sorted_speakers) >= 2:
                    interviewer_time = sorted_speakers[1][1]
            
            total_time = candidate_time + interviewer_time
            candidate_percentage = (candidate_time / total_time * 100) if total_time > 0 else 0
            interviewer_percentage = (interviewer_time / total_time * 100) if total_time > 0 else 0
            
            # Clear any existing overall diarization records for this session
            SpeakerDiarization.objects.filter(
                session=session, 
                question__isnull=True
            ).delete()
            
            # Save overall diarization record (no question associated)
            diarization_record = SpeakerDiarization.objects.create(
                session=session,
                question=None,  # No question - this is for the entire interview
                speaker_changes=speaker_changes,
                speaker_change_timestamps=speaker_change_timestamps,
                num_speakers=num_speakers,
                speaker_labels=speaker_labels,
                candidate_speech_percentage=candidate_percentage,
                interviewer_speech_percentage=interviewer_percentage,
                diarization_segments=[str(turn) for turn, _, _ in diarization.itertracks(yield_label=True)],
                analysis_start_time=timezone.now(),
                analysis_end_time=timezone.now()
            )
            
            logger.info(f"✅ Overall diarization completed: {len(speaker_labels)} speakers, {speaker_changes} changes, Candidate={candidate_percentage:.1f}%, Interviewer={interviewer_percentage:.1f}%")
            
            return {
                'id': str(diarization_record.id),
                'speaker_changes': speaker_changes,
                'speaker_change_timestamps': speaker_change_timestamps,
                'num_speakers': len(speaker_labels),
                'speaker_labels': speaker_labels,
                'candidate_speech_percentage': candidate_percentage,
                'interviewer_speech_percentage': interviewer_percentage,
                'total_interview_time': total_time,
                'candidate_time': candidate_time,
                'interviewer_time': interviewer_time,
                'analysis_type': 'overall_interview'
            }
            
        except Exception as e:
            logger.error(f"Error in overall diarization analysis: {e}")
            return None
