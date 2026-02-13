"""
Simplified Q&A Views using InterviewQA model
"""
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
import uuid

from .models import InterviewSession, InterviewQA

@csrf_exempt
def save_question_answer_pair(request):
    """
    Save question-answer pair using simplified InterviewQA model
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
        session_key = data.get('session_key')
        question_text = data.get('question_text', '').strip()
        answer_text = data.get('answer_text', '').strip()
        question_type = data.get('question_type', 'TECHNICAL')
        audio_url = data.get('audio_url', '')
        question_number = data.get('question_number', 1)
        
        print(f"📝 Saving Q&A pair:")
        print(f"   Session: {session_key}")
        print(f"   Question {question_number}: {question_text[:50]}...")
        print(f"   Answer: {answer_text[:50]}...")
        
        # Get session
        session = get_object_or_404(InterviewSession, session_key=session_key)
        
        # Check if this question number already exists for this session
        existing_qa = InterviewQA.objects.filter(
            session=session,
            question_number=question_number
        ).first()
        
        if existing_qa:
            # Update existing record
            existing_qa.question_text = question_text
            existing_qa.answer_text = answer_text
            existing_qa.question_type = question_type
            existing_qa.audio_url = audio_url
            existing_qa.answered_at = timezone.now()
            
            # Calculate response time if asked_at exists
            if existing_qa.asked_at:
                time_diff = timezone.now() - existing_qa.asked_at
                existing_qa.response_time_seconds = time_diff.total_seconds()
            
            # Calculate speaking metrics
            if answer_text:
                word_count = len(answer_text.split())
                if existing_qa.response_time_seconds and existing_qa.response_time_seconds > 0:
                    minutes = existing_qa.response_time_seconds / 60
                    if minutes > 0:
                        existing_qa.words_per_minute = int(word_count / minutes)
                existing_qa.filler_word_count = 0  # TODO: Add filler word detection
            
            existing_qa.save()
            print(f"✅ Updated Q&A pair {question_number}")
            
        else:
            # Create new record
            qa_pair = InterviewQA.objects.create(
                session=session,
                question_number=question_number,
                question_text=question_text,
                answer_text=answer_text,
                question_type=question_type,
                audio_url=audio_url,
                asked_at=timezone.now(),
                answered_at=timezone.now() if answer_text else None,
            )
            print(f"✅ Created new Q&A pair {question_number}")
        
        return JsonResponse({
            'success': True,
            'message': f'Q&A pair {question_number} saved successfully',
            'question_number': question_number
        })
        
    except Exception as e:
        print(f"❌ Error saving Q&A pair: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@csrf_exempt
def get_qa_pairs(request):
    """
    Get all Q&A pairs for a session
    """
    try:
        session_key = request.GET.get('session_key')
        
        session = get_object_or_404(InterviewSession, session_key=session_key)
        
        qa_pairs = InterviewQA.objects.filter(
            session=session
        ).order_by('question_number')
        
        qa_data = []
        for qa in qa_pairs:
            qa_data.append({
                'question_number': qa.question_number,
                'question_text': qa.question_text,
                'answer_text': qa.answer_text,
                'question_type': qa.question_type,
                'audio_url': qa.audio_url,
                'asked_at': qa.asked_at.isoformat() if qa.asked_at else None,
                'answered_at': qa.answered_at.isoformat() if qa.answered_at else None,
                'response_time_seconds': qa.response_time_seconds,
                'words_per_minute': qa.words_per_minute,
                'filler_word_count': qa.filler_word_count,
            })
        
        print(f"📊 Retrieved {len(qa_data)} Q&A pairs for session {session_key}")
        
        return JsonResponse({
            'success': True,
            'qa_pairs': qa_data,
            'total_count': len(qa_data)
        })
        
    except Exception as e:
        print(f"❌ Error retrieving Q&A pairs: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@csrf_exempt
def update_answer_only(request):
    """
    Update only the answer for a specific question number
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
        session_key = data.get('session_key')
        question_number = data.get('question_number')
        answer_text = data.get('answer_text', '').strip()
        
        print(f"📝 Updating answer for question {question_number}")
        print(f"   Session: {session_key}")
        print(f"   Answer: {answer_text[:50]}...")
        
        session = get_object_or_404(InterviewSession, session_key=session_key)
        
        qa_pair = get_object_or_404(InterviewQA, session=session, question_number=question_number)
        
        qa_pair.answer_text = answer_text
        qa_pair.answered_at = timezone.now()
        
        # Calculate response time
        if qa_pair.asked_at:
            time_diff = timezone.now() - qa_pair.asked_at
            qa_pair.response_time_seconds = time_diff.total_seconds()
        
        # Calculate speaking metrics
        if answer_text:
            word_count = len(answer_text.split())
            if qa_pair.response_time_seconds and qa_pair.response_time_seconds > 0:
                minutes = qa_pair.response_time_seconds / 60
                if minutes > 0:
                    qa_pair.words_per_minute = int(word_count / minutes)
        
        qa_pair.save()
        
        print(f"✅ Updated answer for question {question_number}")
        
        return JsonResponse({
            'success': True,
            'message': f'Answer for question {question_number} updated successfully'
        })
        
    except Exception as e:
        print(f"❌ Error updating answer: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
