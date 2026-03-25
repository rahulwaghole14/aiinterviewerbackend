"""
Debug Speaker Detection Issue
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_app.settings')
django.setup()

from interview_app.voice_analysis_service import VoiceAnalysisService
from interviews.models import Interview
from django.conf import settings

def debug_speaker_detection(session_key):
    """Debug why 2 speakers are detected when there should be 1"""
    
    print("=" * 70)
    print(f"DEBUGGING SPEAKER DETECTION FOR SESSION: {session_key}")
    print("=" * 70)
    
    # Find audio file
    audio_path = None
    converted_wav_path = f"{settings.MEDIA_ROOT}/interview_audio/{session_key}_interview_audio_converted.wav"
    original_wav_path = f"{settings.MEDIA_ROOT}/interview_audio/{session_key}_interview_audio.wav"
    webm_path = f"{settings.MEDIA_ROOT}/interview_audio/{session_key}_interview_audio.webm"
    
    if os.path.exists(converted_wav_path):
        audio_path = converted_wav_path
        print(f"   Audio File: ✅ Converted WAV - {audio_path}")
    elif os.path.exists(original_wav_path):
        audio_path = original_wav_path
        print(f"   Audio File: ✅ Original WAV - {audio_path}")
    elif os.path.exists(webm_path):
        audio_path = webm_path
        print(f"   Audio File: ⚠️ WebM - {audio_path}")
    else:
        print(f"   Audio File: ❌ No audio file found")
        return
    
    # Check audio file info
    file_size = os.path.getsize(audio_path) / (1024*1024)
    print(f"   File Size: {file_size:.1f} MB")
    
    # Initialize voice analysis service
    voice_service = VoiceAnalysisService()
    
    print(f"\n🎙️ Testing Diarization Model:")
    
    try:
        # Load models
        voice_service._ensure_models_loaded()
        
        if not voice_service.diarization_model:
            print(f"   ❌ Diarization model not loaded")
            return
        
        # Run diarization
        diar_result = voice_service.diarization_model(audio_path)
        print(f"   Diarization Result Type: {type(diar_result)}")
        
        # Get detailed speaker information
        print(f"\n👥 Analyzing Speaker Detection:")
        
        speakers_found = set()
        speaker_segments = []
        
        for segment, track, speaker in diar_result.itertracks(yield_label=True):
            speakers_found.add(speaker)
            speaker_segments.append({
                'start': segment.start,
                'end': segment.end,
                'duration': segment.end - segment.start,
                'speaker': speaker
            })
        
        print(f"   Speakers Detected: {len(speakers_found)}")
        print(f"   Speaker Labels: {list(speakers_found)}")
        
        # Analyze speaker distribution
        print(f"\n📊 Speaker Distribution:")
        for speaker in sorted(speakers_found):
            speaker_time = sum(seg['duration'] for seg in speaker_segments if seg['speaker'] == speaker)
            speaker_percentage = (speaker_time / sum(seg['duration'] for seg in speaker_segments)) * 100
            print(f"   {speaker}: {speaker_time:.1f}s ({speaker_percentage:.1f}%)")
        
        # Show first few segments
        print(f"\n🔍 First 10 Segments:")
        for i, segment in enumerate(speaker_segments[:10]):
            print(f"   {i+1:1}. {segment['start']:.2f}s - {segment['end']:.2f}s: {segment['speaker']} ({segment['duration']:.2f}s)")
        
        # Check if this is a single speaker scenario
        print(f"\n🤔 Single Speaker Analysis:")
        
        if len(speakers_found) == 1:
            print(f"   ✅ Correctly detected 1 speaker")
        elif len(speakers_found) == 2:
            print(f"   ⚠️ Detected 2 speakers - analyzing...")
            
            # Check if one speaker is dominant (candidate) and other is minimal (noise/background)
            speaker_times = {}
            for speaker in speakers_found:
                speaker_times[speaker] = sum(seg['duration'] for seg in speaker_segments if seg['speaker'] == speaker)
            
            dominant_speaker = max(speaker_times, key=speaker_times.get)
            dominant_time = speaker_times[dominant_speaker]
            total_time = sum(speaker_times.values())
            dominant_percentage = (dominant_time / total_time) * 100
            
            print(f"   Dominant Speaker: {dominant_speaker} ({dominant_percentage:.1f}%)")
            
            # Check if one speaker is > 90% (likely single person with background noise)
            if dominant_percentage > 90:
                print(f"   ✅ Likely single speaker with {dominant_percentage:.1f}% speech time")
                print(f"   💡 Consider filtering out short segments < 1.0s")
            elif dominant_percentage > 80:
                print(f"   ⚠️ Likely single speaker but with significant background noise")
            else:
                print(f"   ❌ Genuine multi-speaker scenario")
                
        else:
            print(f"   ❌ Detected {len(speakers_found)} speakers (unexpected)")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n" + "=" * 70)
    print("SOLUTIONS")
    print("=" * 70)
    print("If 2 speakers detected when there should be 1:")
    print("1. Background noise being detected as separate speaker")
    print("2. Audio quality issues causing false speaker changes")
    print("3. Model sensitivity too high")
    print("4. Interviewer audio present in recording")
    print("\nFixes:")
    print("1. Filter out segments < 1.0s (likely noise)")
    print("2. Use 80% threshold for single speaker detection")
    print("3. Improve audio quality")
    print("4. Check if interviewer audio is mixed in")

if __name__ == "__main__":
    session_key = "e518869a7b6f494e8400ea8dcaa4e700"
    debug_speaker_detection(session_key)
