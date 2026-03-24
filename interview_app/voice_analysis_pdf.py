"""
Voice Analysis PDF Report Generator
Generates PDF reports for voice activity detection and speaker diarization analysis
"""

import os
import io
from datetime import datetime
from django.conf import settings
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.db import models
from weasyprint import HTML, CSS
from .models import InterviewSession
from .voice_models import VoiceActivityDetection, SpeakerDiarization, AnswerVoiceAnalysis

def generate_voice_analysis_pdf(session_key, save_to_session=True):
    """
    Generate a PDF report for voice analysis of an interview session
    
    Args:
        session_key (str): Interview session key
        save_to_session (bool): Whether to save the PDF path to the session model
        
    Returns:
        HttpResponse: PDF file response or file path if save_to_session is True
    """
    try:
        # Get session
        session = InterviewSession.objects.get(session_key=session_key)
        
        # Get voice analysis data - prioritize overall analysis
        vad_data = VoiceActivityDetection.objects.filter(session=session).order_by('analysis_start_time')
        diar_data = SpeakerDiarization.objects.filter(session=session).order_by('analysis_start_time')
        
        # Separate overall analysis (no question) from per-question analysis
        overall_vad = vad_data.filter(question__isnull=True).first()
        overall_diar = diar_data.filter(question__isnull=True).first()
        per_question_vad = vad_data.filter(question__isnull=False)
        per_question_diar = diar_data.filter(question__isnull=False)
        
        # Get answer voice analysis data
        answer_analyses = AnswerVoiceAnalysis.objects.filter(
            session=session
        ).order_by('answer_number')
        
        # Prepare data for template
        voice_analysis_data = {
            'session': session,
            'overall_vad': overall_vad,
            'overall_diar': overall_diar,
            'per_question_vad': per_question_vad,
            'per_question_diar': per_question_diar,
            'answer_analyses': answer_analyses,
            'total_answers': answer_analyses.count(),
            'vad_data': vad_data,
            'diarization_data': diar_data,
            'total_vad_records': vad_data.count(),
            'total_diar_records': diar_data.count(),
            'has_answer_analysis': answer_analyses.exists(),
            'has_overall_analysis': overall_vad is not None or overall_diar is not None,
            'generated_at': datetime.now(),
            'has_warnings': False,
            'warnings': []
        }
        
        # Analyze for warnings - prioritize overall analysis
        if overall_vad:
            if overall_vad.silence_percentage > 70:
                voice_analysis_data['warnings'].append({
                    'type': 'High Silence',
                    'severity': 'warning',
                    'message': f'Overall silence detected for {overall_vad.silence_percentage:.1f}% of interview',
                    'timestamp': overall_vad.analysis_start_time,
                    'analysis_type': 'overall'
                })
                voice_analysis_data['has_warnings'] = True
            
            if overall_vad.response_delay_seconds and overall_vad.response_delay_seconds > 5:
                voice_analysis_data['warnings'].append({
                    'type': 'Response Delay',
                    'severity': 'warning',
                    'message': f'Average response delay of {overall_vad.response_delay_seconds:.1f} seconds detected',
                    'timestamp': overall_vad.analysis_start_time,
                    'analysis_type': 'overall'
                })
                voice_analysis_data['has_warnings'] = True
        
        if overall_diar:
            if overall_diar.num_speakers > 2:
                voice_analysis_data['warnings'].append({
                    'type': 'Multiple Speakers',
                    'severity': 'critical',
                    'message': f'{overall_diar.num_speakers} speakers detected during interview (expected 2)',
                    'timestamp': overall_diar.analysis_start_time,
                    'analysis_type': 'overall'
                })
                voice_analysis_data['has_warnings'] = True
            
            if overall_diar.speaker_changes > 20:  # Higher threshold for overall interview
                voice_analysis_data['warnings'].append({
                    'type': 'Frequent Speaker Changes',
                    'severity': 'warning',
                    'message': f'{overall_diar.speaker_changes} speaker changes detected during interview',
                    'timestamp': overall_diar.analysis_start_time,
                    'analysis_type': 'overall'
                })
                voice_analysis_data['has_warnings'] = True
        
        # Also check per-question analysis if available (but with lower priority)
        for vad in per_question_vad:
            if vad.silence_percentage > 80:  # Higher threshold for individual questions
                voice_analysis_data['warnings'].append({
                    'type': 'High Silence in Question',
                    'severity': 'warning',
                    'message': f'Silence detected for {vad.silence_percentage:.1f}% in a question response',
                    'timestamp': vad.analysis_start_time,
                    'analysis_type': 'per_question'
                })
                voice_analysis_data['has_warnings'] = True
        
        # Check answer analysis for warnings
        for answer in answer_analyses:
            if answer.multiple_speakers_detected:
                voice_analysis_data['warnings'].append({
                    'type': 'Multiple Speakers in Answer',
                    'severity': 'critical',
                    'message': f'Multiple speakers detected in Answer {answer.answer_number}',
                    'timestamp': answer.created_at,
                    'analysis_type': 'answer_analysis',
                    'answer_number': answer.answer_number
                })
                voice_analysis_data['has_warnings'] = True
            
            if answer.silence_percentage > 50:  # High threshold for individual answers
                voice_analysis_data['warnings'].append({
                    'type': 'High Silence in Answer',
                    'severity': 'warning',
                    'message': f'High silence ({answer.silence_percentage:.1f}%) detected in Answer {answer.answer_number}',
                    'timestamp': answer.created_at,
                    'analysis_type': 'answer_analysis',
                    'answer_number': answer.answer_number
                })
                voice_analysis_data['has_warnings'] = True
            
            if answer.segment_duration < 10:  # Very short answers
                voice_analysis_data['warnings'].append({
                    'type': 'Very Short Answer',
                    'severity': 'warning',
                    'message': f'Answer {answer.answer_number} is very short ({answer.segment_duration:.1f}s)',
                    'timestamp': answer.created_at,
                    'analysis_type': 'answer_analysis',
                    'answer_number': answer.answer_number
                })
                voice_analysis_data['has_warnings'] = True
        
        # Calculate averages - prioritize overall analysis
        if overall_vad:
            voice_analysis_data['avg_silence'] = overall_vad.silence_percentage
            voice_analysis_data['avg_response_delay'] = overall_vad.response_delay_seconds or 0
            voice_analysis_data['total_speech_time'] = overall_vad.total_speech_time
            voice_analysis_data['total_duration'] = overall_vad.total_speech_time + overall_vad.pause_duration
        elif vad_data.exists():
            voice_analysis_data['avg_silence'] = vad_data.aggregate(
                models.Avg('silence_percentage')
            )['silence_percentage__avg'] or 0
            voice_analysis_data['avg_response_delay'] = vad_data.aggregate(
                models.Avg('response_delay_seconds')
            )['response_delay_seconds__avg'] or 0
            voice_analysis_data['total_speech_time'] = vad_data.aggregate(
                models.Sum('total_speech_time')
            )['total_speech_time__sum'] or 0
            voice_analysis_data['total_duration'] = voice_analysis_data['total_speech_time']
        else:
            voice_analysis_data['avg_silence'] = 0
            voice_analysis_data['avg_response_delay'] = 0
            voice_analysis_data['total_speech_time'] = 0
            voice_analysis_data['total_duration'] = 0
        
        if overall_diar:
            voice_analysis_data['avg_speaker_changes'] = overall_diar.speaker_changes
            voice_analysis_data['candidate_speech_percentage'] = overall_diar.candidate_speech_percentage
            voice_analysis_data['interviewer_speech_percentage'] = overall_diar.interviewer_speech_percentage
            voice_analysis_data['num_speakers'] = overall_diar.num_speakers
        elif diar_data.exists():
            voice_analysis_data['avg_speaker_changes'] = diar_data.aggregate(
                models.Avg('speaker_changes')
            )['speaker_changes__avg'] or 0
            voice_analysis_data['candidate_speech_percentage'] = diar_data.aggregate(
                models.Avg('candidate_speech_percentage')
            )['candidate_speech_percentage__avg'] or 0
            voice_analysis_data['interviewer_speech_percentage'] = diar_data.aggregate(
                models.Avg('interviewer_speech_percentage')
            )['interviewer_speech_percentage__avg'] or 0
            voice_analysis_data['num_speakers'] = diar_data.last().num_speakers if diar_data.exists() else 0
        else:
            voice_analysis_data['avg_speaker_changes'] = 0
            voice_analysis_data['candidate_speech_percentage'] = 0
            voice_analysis_data['interviewer_speech_percentage'] = 0
            voice_analysis_data['num_speakers'] = 0
        
        # Calculate answer-specific metrics
        answer_metrics = {}
        if answer_analyses.exists():
            answer_metrics = answer_analyses.aggregate(
                avg_silence=models.Avg('silence_percentage'),
                avg_speech=models.Avg('speech_percentage'),
                avg_duration=models.Avg('segment_duration'),
                avg_wpm=models.Avg('words_per_minute'),
                avg_filler_count=models.Avg('filler_word_count'),
                total_duration=models.Sum('segment_duration'),
                multiple_speaker_count=models.Count('id', filter=models.Q(multiple_speakers_detected=True))
            )
            
            total_filler_words = 0
            if answer_analyses:
                for answer in answer_analyses:
                    total_filler_words += answer.filler_word_count
            
            voice_analysis_data['answer_metrics'] = {
                'avg_silence_percentage': answer_metrics['avg_silence'] or 0,
                'avg_speech_percentage': answer_metrics['avg_speech'] or 0,
                'avg_duration_seconds': answer_metrics['avg_duration'] or 0,
                'avg_words_per_minute': answer_metrics['avg_wpm'] or 0,
                'avg_filler_word_count': answer_metrics['avg_filler_count'] or 0,
                'total_filler_words': total_filler_words or 0,
                'total_answer_duration': answer_metrics['total_duration'] or 0,
                'multiple_speaker_answers': answer_metrics['multiple_speaker_count'],
                'multiple_speaker_percentage': (answer_metrics['multiple_speaker_count'] / answer_analyses.count() * 100) if answer_analyses.count() > 0 else 0
            }
        else:
            voice_analysis_data['answer_metrics'] = {
                'avg_silence_percentage': 0,
                'avg_speech_percentage': 0,
                'avg_duration_seconds': 0,
                'avg_words_per_minute': 0,
                'avg_filler_word_count': 0,
                'total_filler_words': 0,
                'total_answer_duration': 0,
                'multiple_speaker_answers': 0,
                'multiple_speaker_percentage': 0
            }
        
        # Render HTML template
        html_string = render_to_string('voice_analysis_report_simple.html', {
            'session': session,
            'vad_data': vad_data,
            'diar_data': diar_data,
            'answer_analyses': answer_analyses,
            'total_answers': voice_analysis_data.get('total_answers', 0),
            'answer_metrics': answer_metrics,
            'overall_vad': overall_vad,
            'overall_diar': overall_diar,
            'has_answer_analysis': voice_analysis_data.get('has_answer_analysis', False),
            'has_warnings': voice_analysis_data.get('has_warnings', False),
            'warnings': voice_analysis_data.get('warnings', []),
            'avg_silence': voice_analysis_data.get('avg_silence', 0),
            'avg_response_delay': voice_analysis_data.get('avg_response_delay', 0),
            'total_filler_words': voice_analysis_data.get('total_filler_words', 0)
        })
        
        # Create PDF
        html = HTML(string=html_string)
        css = CSS(string='''
            @page {
                size: A4;
                margin: 2cm;
            }
            body {
                font-family: Arial, sans-serif;
                font-size: 12px;
                line-height: 1.6;
            }
            .header {
                text-align: center;
                border-bottom: 2px solid #333;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }
            .warning {
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                padding: 10px;
                margin: 10px 0;
                border-radius: 5px;
            }
            .critical {
                background-color: #f8d7da;
                border: 1px solid #f5c6cb;
                padding: 10px;
                margin: 10px 0;
                border-radius: 5px;
            }
            .section {
                margin: 20px 0;
                padding: 15px;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 10px 0;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
                font-weight: bold;
            }
        ''')
        
        pdf = html.write_pdf(stylesheets=[css])
        
        # Generate filename
        filename = f"voice_analysis_{session.candidate_name}_{session.created_at.strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Also save to local file
        save_dir = os.path.join(settings.MEDIA_ROOT, 'voice_analysis_reports')
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join(save_dir, filename)
        
        with open(file_path, 'wb') as f:
            f.write(pdf)
        
        if save_to_session:
            relative_path = os.path.join('voice_analysis_reports', filename)
            session.voice_analysis_pdf = relative_path
            session.save(update_fields=['voice_analysis_pdf'])
            print(f"✅ Voice analysis PDF saved to: {file_path}")
        
        # Return HttpResponse always
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    except InterviewSession.DoesNotExist:
        return HttpResponse("Session not found", status=404)
    except Exception as e:
        print(f"Error generating voice analysis PDF: {e}")
        return HttpResponse(f"Error generating PDF: {str(e)}", status=500)
