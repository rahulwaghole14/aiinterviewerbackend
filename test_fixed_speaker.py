"""
Test Fixed Speaker Detection
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_app.settings')
django.setup()

from interview_app.voice_analysis_workflow import voice_analysis_workflow

def test_fixed_speaker():
    """Test if speaker diarization fix is working"""
    
    session_key = "e518869a7b6f494e8400ea8dcaa4e700"
    
    print("=" * 70)
    print(f"TESTING FIXED SPEAKER DETECTION FOR SESSION: {session_key}")
    print("=" * 70)
    
    try:
        # Run voice analysis workflow
        result = voice_analysis_workflow.analyze_audio_from_session(session_key)
        
        if result.get('success'):
            print(f"✅ Voice Analysis Successful!")
            print(f"   Speech Time: {result.get('speech_time', 0):.1f}s")
            print(f"   Pause Time: {result.get('pause_time', 0):.1f}s")
            print(f"   Speech %: {result.get('speech_percentage', 0):.1f}%")
            print(f"   Silence %: {result.get('silence_percentage', 0):.1f}%")
            print(f"   Speakers: {result.get('num_speakers', 0)}")
            print(f"   Real Analysis: {result.get('real_analysis', False)}")
            
            # Test PDF generation
            print(f"\n📄 Testing PDF Generation:")
            
            pdf_result = voice_analysis_workflow.generate_voice_analysis_report(session_key)
            
            if pdf_result.get('success'):
                print(f"   ✅ PDF Generated Successfully!")
                print(f"   PDF Path: {pdf_result.get('pdf_path')}")
                
            else:
                print(f"   ❌ PDF Generation Failed: {pdf_result.get('error')}")
                
        else:
            print(f"   ❌ Voice Analysis Failed: {result.get('error')}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n" + "=" * 70)
    print("EXPECTED RESULTS")
    print("=" * 70)
    print("If speaker detection is fixed:")
    print("- Speakers should be 1 (not 2)")
    print("- Speech time should be realistic")
    print("- PDF should show 1 speaker")
    print("\nIf still showing 2 speakers:")
    print("- Model sensitivity may be too high")
    print("- Background noise detection issue")
    print("- Need to adjust threshold to >80%")

if __name__ == "__main__":
    test_fixed_speaker()
