"""
Voice Analysis Workflow Service
Handles the complete voice analysis workflow for interviews:
1. Voice Activity Detection (VAD)
2. Speaker Diarization
3. PDF Report Generation
4. Integration with interview completion
"""

import os
import json
import logging
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
from .voice_analysis_pdf import generate_voice_analysis_pdf
from .voice_analysis_service import VoiceAnalysisService

logger = logging.getLogger(__name__)

class VoiceAnalysisWorkflow:
    """Complete voice analysis workflow for interviews"""
    
    def __init__(self):
        self.hf_token = os.getenv('HUGGINGFACE_TOKEN', '')
        self.voice_service = VoiceAnalysisService()
    
    def _find_audio_file(self, session_key):
        """
        Find audio file for a session using the same logic as analyze_audio_from_session
        
        Args:
            session_key (str): Interview session key
            
        Returns:
            str: Path to audio file or None if not found
        """
        from django.conf import settings
        import os
        import glob
        
        # Priority 1: Check for converted WAV audio file (HuggingFace compatible)
        converted_wav_path = f"{settings.MEDIA_ROOT}/interview_audio/{session_key}_interview_audio_converted.wav"
        if os.path.exists(converted_wav_path):
            return converted_wav_path
        
        # Priority 2: Check for timestamped WAV files (new format)
        timestamped_wav_pattern = f"{settings.MEDIA_ROOT}/interview_audio/*_{session_key}_*.wav"
        timestamped_files = glob.glob(timestamped_wav_pattern)
        if timestamped_files:
            return timestamped_files[0]  # Return the first match
        
        # Priority 3: Check for timestamped WAV files without session_key prefix
        timestamped_wav_pattern2 = f"{settings.MEDIA_ROOT}/interview_audio/{session_key}_*.wav"
        timestamped_files2 = glob.glob(timestamped_wav_pattern2)
        if timestamped_files2:
            return timestamped_files2[0]  # Return the first match
        
        # Priority 4: Check for original WAV audio file
        wav_file_path = f"{settings.MEDIA_ROOT}/interview_audio/{session_key}_interview_audio.wav"
        if os.path.exists(wav_file_path):
            return wav_file_path
        
        # Priority 5: Check for WebM audio file
        webm_file_path = f"{settings.MEDIA_ROOT}/interview_audio/{session_key}_interview_audio.webm"
        if os.path.exists(webm_file_path):
            return webm_file_path
        
        # Priority 6: Check interview video (contains audio)
        from interview_app.models import InterviewSession
        session = InterviewSession.objects.get(session_key=session_key)
        if session.interview_video and hasattr(session.interview_video, 'path'):
            video_path = session.interview_video.path
            if os.path.exists(video_path):
                # Extract audio from video for analysis
                audio_path = self.extract_audio_from_video(video_path)
                logger.info(f"Using extracted audio from video: {audio_path}")
                return audio_path
        
        return None
    
    def analyze_audio_from_session(self, session_key):
        """
        Analyze audio from interview session using HuggingFace models
        
        Args:
            session_key (str): Interview session key
            
        Returns:
            dict: Analysis results
        """
        try:
            from interview_app.models import InterviewSession
            session = InterviewSession.objects.get(session_key=session_key)
            
            # Get audio file path using the helper method
            audio_path = self._find_audio_file(session_key)
            
            # If no audio found, return error
            if not audio_path or not os.path.exists(audio_path):
                logger.error(f"No audio file found for session {session_key}")
                return {"error": "No audio file found for analysis"}
            
            # Use real HuggingFace models for analysis
            logger.info(f"Starting real voice analysis with HuggingFace models: {audio_path}")
            
            # Perform actual voice analysis using HuggingFace models
            analysis_result = self.voice_service.analyze_complete_interview_audio(audio_path, session_key)
            
            if analysis_result.get('success'):
                logger.info(f"Real voice analysis completed for session {session_key}")
                
                # Extract real metrics from analysis
                vad_results = analysis_result.get('vad', {})
                diar_results = analysis_result.get('diarization', {})
                
                # Handle None results gracefully
                if vad_results is None:
                    vad_results = {}
                if diar_results is None:
                    diar_results = {}
                
                return {
                    "success": True,
                    "vad_id": str(vad_results.get('id', '')),
                    "diar_id": str(diar_results.get('id', '')),
                    "speech_time": vad_results.get('total_speech_time', 0.0),
                    "pause_time": vad_results.get('pause_duration', 0.0),
                    "speech_percentage": vad_results.get('speech_percentage', 0.0),
                    "silence_percentage": vad_results.get('silence_percentage', 0.0),
                    "num_speakers": diar_results.get('num_speakers', 1),
                    "candidate_speech_percentage": diar_results.get('candidate_speech_percentage', 0.0),
                    "interviewer_speech_percentage": diar_results.get('interviewer_speech_percentage', 0.0),
                    "real_analysis": True
                }
            else:
                logger.error(f"Real voice analysis failed: {analysis_result.get('error')}")
                return {"error": analysis_result.get('error', 'Unknown error')}
            
        except Exception as e:
            logger.error(f"Audio analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
    
    def extract_audio_from_video(self, video_path):
        """Extract audio from video file using FFmpeg"""
        try:
            import subprocess
            import tempfile
            
            # Create temporary audio file
            temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            temp_audio.close()
            
            # Use FFmpeg to extract audio
            ffmpeg_path = self.get_ffmpeg_path()
            if not ffmpeg_path:
                logger.error("FFmpeg not available for audio extraction")
                return None
            
            cmd = [
                ffmpeg_path,
                '-i', video_path,
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # Audio codec
                '-ar', '16000',  # Sample rate
                '-ac', '1',  # Mono
                '-y',  # Overwrite
                temp_audio.name
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info(f"✅ Audio extracted from video: {temp_audio.name}")
                return temp_audio.name
            else:
                logger.error(f"❌ Audio extraction failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error extracting audio from video: {e}")
            return None
    
    def get_ffmpeg_path(self):
        """Get FFmpeg executable path"""
        try:
            from interview_app.audio_processor import get_ffmpeg_path
            return get_ffmpeg_path()
        except:
            return None
    
    def analyze_interview_audio(self, session_key, audio_file_path=None):
        """
        Perform complete voice analysis for an interview session
        
        Args:
            session_key (str): Interview session key
            audio_file_path (str): Path to audio file (optional, will use session video if not provided)
            
        Returns:
            dict: Analysis results with PDF URL
        """
        try:
            logger.info(f"🎙 Starting voice analysis workflow for session: {session_key}")
            
            # Get session
            session = InterviewSession.objects.get(session_key=session_key)
            
            # Use session video if no audio file provided
            if not audio_file_path and session.interview_video:
                audio_file_path = session.interview_video.path
            elif not audio_file_path:
                logger.warning(f"No audio file available for session {session_key}")
                return {"error": "No audio file available"}
            
            # Step 1: Perform Voice Activity Detection
            logger.info("🔍 Performing Voice Activity Detection...")
            vad_result = self.voice_service.analyze_voice_activity(session_key, audio_file_path)
            
            # Step 2: Perform Speaker Diarization
            logger.info("👥 Performing Speaker Diarization...")
            diar_result = self.voice_service.analyze_speaker_diarization(session_key, audio_file_path)
            
            # Step 3: Generate PDF Report
            logger.info("📄 Generating Voice Analysis PDF...")
            pdf_result = self.generate_voice_analysis_report(session_key)
            
            # Step 4: Update session with PDF
            if pdf_result and pdf_result.get('success'):
                session.voice_analysis_pdf = pdf_result.get('pdf_path')
                session.save(update_fields=['voice_analysis_pdf'])
                logger.info(f"✅ Voice analysis PDF saved to session: {pdf_result.get('pdf_path')}")
            
            return {
                "success": True,
                "vad_result": vad_result,
                "diar_result": diar_result,
                "pdf_result": pdf_result,
                "session_id": str(session.id)
            }
            
        except Exception as e:
            logger.error(f"❌ Voice analysis workflow failed: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
    
    def generate_voice_analysis_report(self, session_key):
        """
        Generate voice analysis PDF report using exact format template
        
        Args:
            session_key (str): Interview session key
            
        Returns:
            dict: Result with PDF path and URL
        """
        try:
            from django.core.files.base import ContentFile
            from django.core.files.storage import default_storage
            from django.template.loader import render_to_string
            import tempfile
            import os
            from weasyprint import HTML, CSS
            
            # Get session and analysis data
            session = InterviewSession.objects.get(session_key=session_key)
            
            # Get overall VAD data
            vad_data = VoiceActivityDetection.objects.filter(
                session=session, 
                question__isnull=True
            ).first()
            
            # Get overall diarization data
            diar_data = SpeakerDiarization.objects.filter(
                session=session,
                question__isnull=True
            ).first()
            
            # Prepare template context
            context = {
                'session': session,
                'overall_vad': vad_data,
                'overall_diar': diar_data,
                'has_warnings': False,
                'warnings': []
            }
            
            # Render HTML template using image format (exact match to your image)
            html_content = render_to_string('voice_analysis_report_image_format.html', context)
            
            # Generate PDF using WeasyPrint
            html = HTML(string=html_content)
            pdf_content = html.write_pdf()
            
            # Save PDF to file storage
            filename = f"voice_analysis_{session.candidate_name.replace(' ', '_')}_{session.created_at.strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf_path = f"voice_analysis_reports/{filename}"
            
            # Save to storage
            default_storage.save(pdf_path, ContentFile(pdf_content))
            pdf_url = default_storage.url(pdf_path)
            
            # Update session with PDF file
            session.voice_analysis_pdf.name = pdf_path
            session.save(update_fields=['voice_analysis_pdf'])
            
            logger.info(f"✅ Voice analysis PDF generated: {pdf_url}")
            
            return {
                "success": True,
                "pdf_path": pdf_path,
                "pdf_url": pdf_url
            }
                
        except Exception as e:
            logger.error(f"❌ Voice analysis PDF generation failed: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
    
    def trigger_voice_analysis_on_completion(self, session_key):
        """
        Trigger voice analysis when interview is completed
        This method should be called when an interview is marked as completed
        
        Args:
            session_key (str): Interview session key
        """
        import time
        
        try:
            logger.info(f"Triggering voice analysis for completed interview: {session_key}")
            
            # Wait for audio file to be available (up to 30 seconds)
            logger.info("Waiting for audio file to be available...")
            audio_file_path = self._find_audio_file(session_key)
            max_wait_time = 30  # seconds
            wait_interval = 2   # seconds
            waited_time = 0
            
            while not audio_file_path and waited_time < max_wait_time:
                logger.info(f"Audio file not found, waiting {wait_interval}s... (total waited: {waited_time}s)")
                time.sleep(wait_interval)
                waited_time += wait_interval
                audio_file_path = self._find_audio_file(session_key)
            
            if not audio_file_path:
                logger.error(f"ERROR: No audio file found for session {session_key} after waiting {max_wait_time}s")
                return {
                    "success": False,
                    "error": f"No audio file found after waiting {max_wait_time}s"
                }
            
            logger.info(f"✅ Audio file found: {audio_file_path}")
            
            # Step 1: Analyze audio from session
            logger.info("Analyzing audio from interview session...")
            analysis_result = self.analyze_audio_from_session(session_key)
            
            # Step 2: Generate PDF report
            logger.info("Generating voice analysis PDF...")
            pdf_result = self.generate_voice_analysis_report(session_key)
            
            if pdf_result.get('success'):
                logger.info(f"Voice analysis completed for session {session_key}")
                return {
                    "success": True,
                    "analysis": analysis_result,
                    "pdf": pdf_result
                }
            else:
                logger.error(f"PDF generation failed: {pdf_result.get('error')}")
                return pdf_result
                
        except Exception as e:
            logger.error(f"Failed to trigger voice analysis: {e}")
            return {"error": str(e)}
    
    def get_voice_analysis_summary(self, session_key):
        """
        Get voice analysis summary for display
        
        Args:
            session_key (str): Interview session key
            
        Returns:
            dict: Voice analysis summary
        """
        try:
            from .voice_models import VoiceActivityDetection, SpeakerDiarization
            
            session = InterviewSession.objects.get(session_key=session_key)
            
            # Get overall VAD data
            vad_data = VoiceActivityDetection.objects.filter(
                session=session, 
                question__isnull=True
            ).first()
            
            # Get overall diarization data
            diar_data = SpeakerDiarization.objects.filter(
                session=session,
                question__isnull=True
            ).first()
            
            summary = {
                "session_key": session_key,
                "candidate_name": session.candidate_name,
                "pdf_available": bool(session.voice_analysis_pdf),
                "pdf_url": session.voice_analysis_pdf.url if session.voice_analysis_pdf else None,
                "voice_activity": None,
                "speaker_diarization": None
            }
            
            if vad_data:
                summary["voice_activity"] = {
                    "speech_time": vad_data.total_speech_time,
                    "pause_time": vad_data.pause_duration,
                    "speech_percentage": vad_data.speech_percentage,
                    "silence_percentage": vad_data.silence_percentage,
                    "response_delay": vad_data.response_delay_seconds
                }
            
            if diar_data:
                summary["speaker_diarization"] = {
                    "num_speakers": diar_data.num_speakers,
                    "speaker_changes": diar_data.speaker_changes,
                    "candidate_speech_percentage": diar_data.candidate_speech_percentage,
                    "interviewer_speech_percentage": diar_data.interviewer_speech_percentage
                }
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Failed to get voice analysis summary: {e}")
            return {"error": str(e)}

# Global instance
voice_analysis_workflow = VoiceAnalysisWorkflow()
