from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db import models
from .models import InterviewSession, InterviewQuestion
import json

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_question_answer_pair(request):
    """
    Save a question-answer pair for an interview session.
    Handles all question types: INTRODUCTION, TECHNICAL, BEHAVIORAL, CODING, PRECLOSING, CLOSING
    """
    try:
        data = request.data
        session_id = data.get('session_id')
        question_text = data.get('question_text')
        transcribed_answer = data.get('transcribed_answer')
        question_type = data.get('question_type', 'TECHNICAL')
        question_level = data.get('question_level', 'MAIN')
        
        if not session_id or not question_text:
            return Response(
                {'error': 'session_id and question_text are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get interview session
        session = get_object_or_404(InterviewSession, id=session_id)
        
        # Get next order number for this session
        last_question = InterviewQuestion.objects.filter(session=session).order_by('-order').first()
        next_order = (last_question.order + 1) if last_question else 0
        
        # Create question-answer pair
        question = InterviewQuestion.objects.create(
            session=session,
            question_text=question_text,
            transcribed_answer=transcribed_answer,
            question_type=question_type,
            question_level=question_level,
            order=next_order,
            asked_at=timezone.now(),
            answered_at=timezone.now() if transcribed_answer else None,
            role='AI'  # This is the AI interviewer's question
        )
        
        return Response({
            'success': True,
            'question_id': str(question.id),
            'order': question.order,
            'question_type': question.question_type,
            'message': f'Question-answer pair saved successfully for {session.candidate_name}'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': f'Failed to save question-answer pair: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_answer_for_question(request, question_id):
    """
    Update only the answer for an existing question.
    Used when answer is transcribed after question was asked.
    """
    try:
        data = request.data
        transcribed_answer = data.get('transcribed_answer')
        response_time_seconds = data.get('response_time_seconds')
        words_per_minute = data.get('words_per_minute')
        filler_word_count = data.get('filler_word_count')
        
        if not transcribed_answer:
            return Response(
                {'error': 'transcribed_answer is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get question
        question = get_object_or_404(InterviewQuestion, id=question_id)
        
        # Update answer and metadata
        question.transcribed_answer = transcribed_answer
        question.answered_at = timezone.now()
        
        if response_time_seconds is not None:
            question.response_time_seconds = response_time_seconds
        if words_per_minute is not None:
            question.words_per_minute = words_per_minute
        if filler_word_count is not None:
            question.filler_word_count = filler_word_count
        
        question.save()
        
        return Response({
            'success': True,
            'question_id': str(question.id),
            'message': 'Answer updated successfully'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Failed to update answer: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_interview_questions(request, session_id):
    """
    Get all question-answer pairs for an interview session.
    Returns questions in order with their answers.
    """
    try:
        session = get_object_or_404(InterviewSession, id=session_id)
        
        questions = InterviewQuestion.objects.filter(session=session).order_by('order')
        
        questions_data = []
        for question in questions:
            questions_data.append({
                'id': str(question.id),
                'question_text': question.question_text,
                'transcribed_answer': question.transcribed_answer,
                'question_type': question.question_type,
                'question_level': question.question_level,
                'order': question.order,
                'conversation_sequence': question.conversation_sequence,
                'asked_at': question.asked_at.isoformat() if question.asked_at else None,
                'answered_at': question.answered_at.isoformat() if question.answered_at else None,
                'response_time_seconds': question.response_time_seconds,
                'words_per_minute': question.words_per_minute,
                'filler_word_count': question.filler_word_count,
                'role': question.role,
                'is_follow_up': question.is_follow_up,
                'question_category': question.question_category,
                'coding_language': question.coding_language
            })
        
        return Response({
            'success': True,
            'session_id': str(session.id),
            'candidate_name': session.candidate_name,
            'total_questions': len(questions_data),
            'questions': questions_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Failed to get questions: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_interview_conversation(request):
    """
    Save multiple question-answer pairs at once.
    Useful for bulk saving or importing interview data.
    """
    try:
        data = request.data
        session_id = data.get('session_id')
        conversation_pairs = data.get('conversation_pairs', [])
        
        if not session_id or not conversation_pairs:
            return Response(
                {'error': 'session_id and conversation_pairs are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get interview session
        session = get_object_or_404(InterviewSession, id=session_id)
        
        # Get next order number for this session
        last_question = InterviewQuestion.objects.filter(session=session).order_by('-order').first()
        start_order = (last_question.order + 1) if last_question else 0
        
        saved_questions = []
        for i, pair in enumerate(conversation_pairs):
            question_text = pair.get('question_text')
            transcribed_answer = pair.get('transcribed_answer')
            question_type = pair.get('question_type', 'TECHNICAL')
            question_level = pair.get('question_level', 'MAIN')
            
            if not question_text:
                continue  # Skip invalid pairs
            
            # Create question-answer pair
            question = InterviewQuestion.objects.create(
                session=session,
                question_text=question_text,
                transcribed_answer=transcribed_answer,
                question_type=question_type,
                question_level=question_level,
                order=start_order + i,
                asked_at=timezone.now(),
                answered_at=timezone.now() if transcribed_answer else None,
                role='AI'
            )
            
            saved_questions.append({
                'question_id': str(question.id),
                'order': question.order,
                'question_type': question.question_type
            })
        
        return Response({
            'success': True,
            'session_id': str(session.id),
            'saved_questions': len(saved_questions),
            'questions': saved_questions,
            'message': f'Saved {len(saved_questions)} question-answer pairs for {session.candidate_name}'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': f'Failed to save conversation: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_interview_statistics(request, session_id):
    """
    Get statistics about an interview session.
    Includes question counts by type, answer rates, etc.
    """
    try:
        session = get_object_or_404(InterviewSession, id=session_id)
        
        questions = InterviewQuestion.objects.filter(session=session)
        
        # Basic stats
        total_questions = questions.count()
        answered_questions = questions.filter(transcribed_answer__isnull=False).count()
        
        # Questions by type
        questions_by_type = {}
        for qtype, _ in InterviewQuestion.QUESTION_TYPE_CHOICES:
            count = questions.filter(question_type=qtype).count()
            if count > 0:
                questions_by_type[qtype] = count
        
        # Questions by level
        questions_by_level = {}
        for level, _ in InterviewQuestion.QUESTION_LEVEL_CHOICES:
            count = questions.filter(question_level=level).count()
            if count > 0:
                questions_by_level[level] = count
        
        # Performance metrics
        avg_response_time = questions.filter(
            response_time_seconds__isnull=False
        ).aggregate(avg_time=models.Avg('response_time_seconds'))['avg_time']
        
        avg_wpm = questions.filter(
            words_per_minute__isnull=False
        ).aggregate(avg_wpm=models.Avg('words_per_minute'))['avg_wpm']
        
        return Response({
            'success': True,
            'session_id': str(session.id),
            'candidate_name': session.candidate_name,
            'total_questions': total_questions,
            'answered_questions': answered_questions,
            'answer_rate': (answered_questions / total_questions * 100) if total_questions > 0 else 0,
            'questions_by_type': questions_by_type,
            'questions_by_level': questions_by_level,
            'average_response_time_seconds': avg_response_time,
            'average_words_per_minute': avg_wpm,
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Failed to get statistics: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
