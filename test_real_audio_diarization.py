#!/usr/bin/env python3
"""
Test speaker diarization fix with real interview audio files
"""

import os
import sys
import django
import logging

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_app.settings')
django.setup()

from interview_app.voice_analysis_service import VoiceAnalysisService
from interview_app.models import InterviewSession

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_real_audio_diarization():
    """Test speaker diarization with real interview audio files"""
    
    print("🎙️ Testing Speaker Diarization with Real Interview Audio")
    print("=" * 60)
    
    # Initialize voice analysis service
    voice_service = VoiceAnalysisService()
    
    # Available audio files and their corresponding sessions
    test_cases = [
        {
            'audio_path': 'media/interview_audio/3b43385056fa47fc9b7613e2630a4f2e_interview_audio_converted.wav',
            'session_key': '3b43385056fa47fc9b7613e2630a4f2e',
            'description': 'Converted interview audio'
        },
        {
            'audio_path': 'media/interview_audio/3d792a6a-6337-460a-94e3-f9019d011ee2_20260408_181908.wav',
            'session_key': None,  # Will try to find matching session
            'description': 'Original interview audio'
        },
        {
            'audio_path': 'media/interview_audio/434fce74-6fac-415e-88fb-272747584481_20260409_112048.wav',
            'session_key': None,  # Will try to find matching session
            'description': 'Recent interview audio'
        },
        {
            'audio_path': 'media/interview_audio/aa1b4a5f007545ca882055115e92bd27_interview_audio_converted.wav',
            'session_key': None,  # Will try to find matching session
            'description': 'Another converted interview audio'
        }
    ]
    
    # Check if models can be loaded
    print("\n🔧 Checking model availability...")
    if voice_service._ensure_models_loaded():
        print("✅ Models loaded successfully")
    else:
        print("❌ Failed to load models - will test fallback logic only")
    
    print(f"\n📁 Found {len(test_cases)} audio files to test")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*20} Test Case {i} {'='*20}")
        print(f"📝 Description: {test_case['description']}")
        print(f"🎵 Audio File: {test_case['audio_path']}")
        
        # Check if audio file exists
        if not os.path.exists(test_case['audio_path']):
            print(f"❌ Audio file not found: {test_case['audio_path']}")
            continue
        
        # Get file size
        file_size = os.path.getsize(test_case['audio_path'])
        print(f"📊 File Size: {file_size / (1024*1024):.2f} MB")
        
        # Try to find session key if not provided
        session_key = test_case['session_key']
        if not session_key:
            # Try to extract from filename
            filename = os.path.basename(test_case['audio_path'])
            if '_' in filename:
                potential_key = filename.split('_')[0]
                try:
                    session = InterviewSession.objects.get(session_key=potential_key)
                    session_key = potential_key
                    print(f"🔍 Found matching session: {session_key}")
                except InterviewSession.DoesNotExist:
                    print(f"⚠️  No matching session found for key: {potential_key}")
                    continue
        
        if not session_key:
            print("❌ No session key available, skipping...")
            continue
        
        try:
            # Test the diarization analysis
            print(f"\n👥 Running speaker diarization analysis...")
            
            result = voice_service.analyze_complete_interview_audio(
                audio_file_path=test_case['audio_path'],
                session_key=session_key
            )
            
            if result and result.get('success'):
                diarization = result.get('diarization')
                if diarization:
                    print(f"✅ Analysis completed successfully!")
                    print(f"📊 Results:")
                    print(f"   - Number of Speakers: {diarization.get('num_speakers', 'N/A')}")
                    print(f"   - Speaker Changes: {diarization.get('speaker_changes', 'N/A')}")
                    print(f"   - Candidate Speech: {diarization.get('candidate_speech_percentage', 'N/A'):.1f}%")
                    print(f"   - Interviewer Speech: {diarization.get('interviewer_speech_percentage', 'N/A'):.1f}%")
                    print(f"   - Total Interview Time: {diarization.get('total_interview_time', 'N/A'):.1f}s")
                    
                    # Check if the fix worked
                    num_speakers = diarization.get('num_speakers', 0)
                    if num_speakers == 1:
                        print("🎉 SUCCESS: Correctly detected as single speaker!")
                    elif num_speakers == 2:
                        candidate_pct = diarization.get('candidate_speech_percentage', 0)
                        if candidate_pct > 80:
                            print("⚠️  WARNING: 2 speakers detected but candidate dominates (>80%)")
                            print("   This might still be a single speaker with background noise")
                        else:
                            print("📝 INFO: Genuine 2-speaker conversation detected")
                    else:
                        print(f"❓ UNUSUAL: {num_speakers} speakers detected")
                    
                    # Show speaker labels if available
                    speaker_labels = diarization.get('speaker_labels', {})
                    if speaker_labels:
                        print(f"   - Speaker Details: {list(speaker_labels.keys())}")
                        
                else:
                    print("❌ No diarization results found")
            else:
                print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Error during analysis: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print("🎉 Real Audio Testing Complete!")
    print("\n📋 Summary:")
    print("- Check the results above for speaker counts")
    print("- Single speaker interviews should now show 1 speaker")
    print("- If you still see 2 speakers, check the candidate %")
    print("- Candidate % > 80% indicates likely single speaker with noise")

if __name__ == "__main__":
    test_real_audio_diarization()
