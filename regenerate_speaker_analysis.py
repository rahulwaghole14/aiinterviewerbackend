"""
Regenerate Voice Analysis with New 65% Threshold
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_app.settings')
django.setup()

from interview_app.voice_analysis_workflow import voice_analysis_workflow
from interview_app.models import InterviewSession, SpeakerDiarization

def regenerate_speaker_analysis():
    """Regenerate voice analysis with 65% threshold"""
    
    session_key = "e518869a7b6f494e8400ea8dcaa4e700"
    
    print("=" * 70)
    print(f"REGENERATING VOICE ANALYSIS WITH 65% THRESHOLD")
    print("=" * 70)
    
    try:
        # Get session
        session = InterviewSession.objects.get(session_key=session_key)
        print(f"✅ Found session: {session.id}")
        
        # Delete existing diarization data to force regeneration
        deleted_count = SpeakerDiarization.objects.filter(
            session=session,
            question__isnull=True
        ).delete()
        print(f"🗑️ Deleted {deleted_count[0]} existing diarization records")
        
        # Run voice analysis again
        print(f"🎯 Running voice analysis...")
        result = voice_analysis_workflow.analyze_audio_from_session(session_key)
        
        if result.get('success'):
            print(f"✅ Voice Analysis Successful!")
            print(f"   Speech Time: {result.get('speech_time', 0):.1f}s")
            print(f"   Pause Time: {result.get('pause_time', 0):.1f}s")
            print(f"   Speech %: {result.get('speech_percentage', 0):.1f}%")
            print(f"   Silence %: {result.get('silence_percentage', 0):.1f}%")
            print(f"   Speakers: {result.get('num_speakers', 0)}")
            
            # Check updated diarization data
            diar_data = SpeakerDiarization.objects.filter(
                session=session,
                question__isnull=True
            ).first()
            
            if diar_data:
                print(f"\n📊 Updated Diarization Data:")
                print(f"   Speakers: {diar_data.num_speakers}")
                print(f"   Candidate %: {diar_data.candidate_speech_percentage:.1f}%")
                print(f"   Interviewer %: {diar_data.interviewer_speech_percentage:.1f}%")
                
                if diar_data.num_speakers == 1:
                    print(f"   ✅ SUCCESS: Now showing 1 speaker!")
                else:
                    print(f"   ❌ Still showing {diar_data.num_speakers} speakers")
                    
            # Generate PDF
            print(f"\n📄 Generating PDF...")
            pdf_result = voice_analysis_workflow.generate_voice_analysis_report(session_key)
            
            if pdf_result.get('success'):
                print(f"   ✅ PDF Generated Successfully!")
                print(f"   PDF Path: {pdf_result.get('pdf_path')}")
                
                # Update session
                session.voice_analysis_pdf = pdf_result.get('pdf_path')
                session.save(update_fields=['voice_analysis_pdf'])
                print(f"   ✅ Session updated with PDF")
                
            else:
                print(f"   ❌ PDF Generation Failed: {pdf_result.get('error')}")
                
        else:
            print(f"   ❌ Voice Analysis Failed: {result.get('error')}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("With 65% threshold:")
    print("- 69.1% dominant speaker should be treated as single speaker")
    print("- Should show 1 speaker instead of 2")
    print("- PDF should display correct speaker count")

if __name__ == "__main__":
    regenerate_speaker_analysis()
