"""
Quick Test of Speaker Detection Logic
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_app.settings')
django.setup()

from interview_app.models import InterviewSession, SpeakerDiarization

def quick_speaker_test():
    """Check current speaker diarization results"""
    
    session_key = "e518869a7b6f494e8400ea8dcaa4e700"
    
    print("=" * 70)
    print(f"QUICK SPEAKER TEST FOR SESSION: {session_key}")
    print("=" * 70)
    
    try:
        session = InterviewSession.objects.get(session_key=session_key)
        print(f"✅ Found session: {session.id}")
        
        # Check existing diarization data
        diar_data = SpeakerDiarization.objects.filter(
            session=session,
            question__isnull=True
        ).first()
        
        if diar_data:
            print(f"📊 Existing Diarization Data:")
            print(f"   Speakers: {diar_data.num_speakers}")
            print(f"   Candidate %: {diar_data.candidate_speech_percentage:.1f}%")
            print(f"   Interviewer %: {diar_data.interviewer_speech_percentage:.1f}%")
            print(f"   Speaker Changes: {diar_data.speaker_changes}")
            
            if diar_data.num_speakers == 1:
                print(f"   ✅ CORRECT: 1 speaker detected")
            else:
                print(f"   ❌ ISSUE: {diar_data.num_speakers} speakers detected")
                
                # Show speaker labels if available
                if diar_data.speaker_labels:
                    print(f"   Speaker Labels: {list(diar_data.speaker_labels.keys())}")
                    
                    # Calculate dominant speaker percentage
                    total_time = 0
                    speaker_times = {}
                    
                    for speaker, segments in diar_data.speaker_labels.items():
                        speaker_time = sum(seg['duration'] for seg in segments)
                        speaker_times[speaker] = speaker_time
                        total_time += speaker_time
                    
                    if speaker_times:
                        dominant_speaker = max(speaker_times, key=speaker_times.get)
                        dominant_percentage = (speaker_times[dominant_speaker] / total_time) * 100
                        
                        print(f"   Dominant Speaker: {dominant_speaker} ({dominant_percentage:.1f}%)")
                        
                        if dominant_percentage > 70:
                            print(f"   💡 Should be treated as single speaker (>70%)")
                        else:
                            print(f"   ⚠️ Genuine multi-speaker scenario")
        else:
            print(f"❌ No diarization data found - need to run voice analysis")
            
    except InterviewSession.DoesNotExist:
        print(f"❌ Session not found: {session_key}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    quick_speaker_test()
