"""
Service for managing Q&A conversation pairs during interviews
"""
import uuid
import google.generativeai as genai
from django.utils import timezone
from django.conf import settings
from django.db import models
from .models import InterviewSession, QAConversationPair
import re

# Filler words for analysis
FILLER_WORDS = ['um', 'uh', 'er', 'ah', 'like', 'okay', 'right', 'so', 'you know', 'i mean', 'basically', 'actually', 'literally']

def save_qa_pair(session_key, question_text, answer_text, question_type='TECHNICAL', response_time_seconds=None):
    """
    Save a question-answer pair to the database with proper chronological sequencing
    
    Args:
        session_key: Interview session key
        question_text: Question asked by AI (or AI response for candidate questions)
        answer_text: Answer given by candidate (or candidate question)
        question_type: Type of question (INTRODUCTORY, TECHNICAL, FOLLOW_UP, CANDIDATE_QUESTION, etc.)
        response_time_seconds: Time taken to respond
    
    Returns:
        QAConversationPair object
    """
    try:
        # Get session
        session = InterviewSession.objects.get(session_key=session_key)
        
        # Get the next sequential question number for ALL types
        last_qa = QAConversationPair.objects.filter(session=session).order_by('-question_number').first()
        question_number = (last_qa.question_number + 1) if last_qa else 1
        
        # Use the same number for display order to maintain chronological sequence
        pdf_display_order = question_number
        
        print(f"🔢 Assigning question_number: {question_number} for type: {question_type}")
        print(f"📋 PDF display order: {pdf_display_order}")
        
        # Calculate answer metrics
        words_per_minute = calculate_words_per_minute(answer_text, response_time_seconds)
        filler_word_count = count_filler_words(answer_text)
        sentiment_score = calculate_sentiment_score(answer_text)
        
        # Create Q&A pair
        qa_pair = QAConversationPair.objects.create(
            session=session,
            session_key=session.session_key,  # Add session_key for easy identification
            question_text=question_text,
            answer_text=answer_text,
            question_type=question_type,
            question_number=question_number,
            response_time_seconds=response_time_seconds,
            words_per_minute=words_per_minute,
            filler_word_count=filler_word_count,
            sentiment_score=sentiment_score,
            pdf_display_order=pdf_display_order
        )
        
        print(f"✅ Q&A pair saved: #{question_number} ({question_type})")
        return qa_pair
        
    except InterviewSession.DoesNotExist:
        print(f"❌ Session not found: {session_key}")
        return None
    except Exception as e:
        print(f"❌ Error saving Q&A pair: {e}")
        return None

def analyze_qa_with_gemini(qa_pair):
    """
    Analyze a Q&A pair using Gemini AI
    
    Args:
        qa_pair: QAConversationPair object to analyze
    
    Returns:
        Tuple of (analysis_text, score)
    """
    try:
        # Configure Gemini
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Create analysis prompt
        prompt = f"""
        Analyze this interview question-answer pair:
        
        Question: {qa_pair.question_text}
        Answer: {qa_pair.answer_text}
        Question Type: {qa_pair.question_type}
        
        Provide:
        1. A detailed analysis of the answer quality (technical accuracy, communication, clarity)
        2. A score from 0-10 for this specific Q&A
        3. Key strengths and areas for improvement
        
        Format your response as:
        ANALYSIS: [your detailed analysis]
        SCORE: [0-10]
        STRENGTHS: [list strengths]
        IMPROVEMENTS: [list areas for improvement]
        """
        
        # Get analysis from Gemini
        response = model.generate_content(prompt)
        analysis_text = response.text
        
        # Extract score
        score = extract_score_from_analysis(analysis_text)
        
        # Update the Q&A pair with analysis
        qa_pair.llm_analysis = analysis_text
        qa_pair.llm_score = score
        qa_pair.analysis_timestamp = timezone.now()
        qa_pair.save(update_fields=['llm_analysis', 'llm_score', 'analysis_timestamp'])
        
        print(f"✅ Analyzed Q&A pair {qa_pair.question_number} with score: {score}")
        return analysis_text, score
        
    except Exception as e:
        print(f"❌ Error analyzing Q&A with Gemini: {e}")
        return None, None

def extract_score_from_analysis(analysis_text):
    """
    Extract score from Gemini analysis text
    """
    try:
        # Look for SCORE: pattern
        score_match = re.search(r'SCORE:\s*(\d+(?:\.\d+)?)', analysis_text, re.IGNORECASE)
        if score_match:
            score = float(score_match.group(1))
            return min(10, max(0, score))  # Ensure score is between 0-10
    except:
        pass
    
    # Default score if extraction fails
    return 5.0

def calculate_words_per_minute(text, response_time_seconds):
    """
    Calculate words per minute from answer text and response time
    """
    if not text or not response_time_seconds or response_time_seconds <= 0:
        return None
    
    word_count = len(text.split())
    minutes = response_time_seconds / 60.0
    wpm = word_count / minutes if minutes > 0 else 0
    
    return round(wpm, 2)

def count_filler_words(text):
    """
    Count filler words in the answer text
    """
    if not text:
        return 0
    
    lower_text = text.lower()
    filler_count = sum(lower_text.count(word) for word in FILLER_WORDS)
    return filler_count

def calculate_sentiment_score(text):
    """
    Calculate sentiment score (simplified version)
    """
    if not text:
        return 0.0
    
    # Simple sentiment analysis based on positive/negative words
    positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'perfect', 'love', 'like', 'enjoy']
    negative_words = ['bad', 'terrible', 'awful', 'horrible', 'hate', 'dislike', 'poor', 'wrong', 'difficult', 'hard']
    
    lower_text = text.lower()
    positive_count = sum(lower_text.count(word) for word in positive_words)
    negative_count = sum(lower_text.count(word) for word in negative_words)
    
    # Normalize to -1 to 1 scale
    total_sentiment_words = positive_count + negative_count
    if total_sentiment_words == 0:
        return 0.0
    
    sentiment = (positive_count - negative_count) / total_sentiment_words
    return round(sentiment, 3)

def get_qa_pairs_for_session(session_key):
    """
    Get all Q&A pairs for a session in proper chronological order
    
    Args:
        session_key: Interview session key
    
    Returns:
        QuerySet of QAConversationPair objects ordered by pdf_display_order (chronological)
    """
    try:
        session = InterviewSession.objects.get(session_key=session_key)
        qa_pairs = QAConversationPair.objects.filter(
            session=session
        ).order_by('pdf_display_order', 'timestamp')
        
        print(f"📚 Retrieved {qa_pairs.count()} Q&A pairs for session {session_key}")
        for qa in qa_pairs:
            print(f"   #{qa.question_number} ({qa.question_type}) - Order: {qa.pdf_display_order}")
        
        return qa_pairs
        
    except InterviewSession.DoesNotExist:
        print(f"❌ Session not found: {session_key}")
        return QAConversationPair.objects.none()
    except Exception as e:
        print(f"❌ Error retrieving Q&A pairs: {e}")
        return QAConversationPair.objects.none()

def get_qa_pairs_for_session_ordered(session_key):
    """
    Get Q&A pairs in proper chronological interview sequence (1, 2, 3, 4...)
    
    Args:
        session_key: Interview session key
    
    Returns:
        Dictionary with chronological sequence and type-separated views
    """
    try:
        session = InterviewSession.objects.get(session_key=session_key)
        
        # Get ALL Q&A pairs in chronological order (the actual interview sequence)
        chronological_pairs = QAConversationPair.objects.filter(
            session=session
        ).order_by('question_number', 'timestamp')
        
        # Also provide type-separated views for analysis
        ai_questions = chronological_pairs.filter(
            question_type__in=['INTRODUCTORY', 'TECHNICAL', 'FOLLOW_UP', 'CLARIFICATION', 'ELABORATION_REQUEST']
        )
        
        candidate_questions = chronological_pairs.filter(
            question_type='CANDIDATE_QUESTION'
        )
        
        print(f"📊 Retrieved {chronological_pairs.count()} total Q&A pairs in chronological order")
        print(f"🤖 AI Questions: {ai_questions.count()}")
        print(f"🗣️ Candidate Questions: {candidate_questions.count()}")
        
        # Show the actual sequence
        print("📋 Actual Interview Sequence:")
        for qa in chronological_pairs:
            question_label = "AI Question" if qa.question_type != 'CANDIDATE_QUESTION' else "Candidate Question"
            print(f"   Q#{qa.question_number}: {question_label} ({qa.question_type})")
        
        return {
            'chronological_pairs': chronological_pairs,  # The actual interview sequence
            'ai_questions': ai_questions,  # Filtered view
            'candidate_questions': candidate_questions,  # Filtered view
            'all_pairs': chronological_pairs  # Same as chronological for consistency
        }
        
    except InterviewSession.DoesNotExist:
        print(f"❌ Session not found: {session_key}")
        return {
            'chronological_pairs': QAConversationPair.objects.none(),
            'ai_questions': QAConversationPair.objects.none(),
            'candidate_questions': QAConversationPair.objects.none(),
            'all_pairs': QAConversationPair.objects.none()
        }
    except Exception as e:
        print(f"❌ Error retrieving Q&A pairs: {e}")
        return {
            'chronological_pairs': QAConversationPair.objects.none(),
            'ai_questions': QAConversationPair.objects.none(),
            'candidate_questions': QAConversationPair.objects.none(),
            'all_pairs': QAConversationPair.objects.none()
        }

def get_qa_pairs_for_pdf(session_key):
    """
    Get Q&A pairs formatted for PDF generation
    """
    qa_pairs = get_qa_pairs_for_session(session_key)
    formatted_pairs = []
    
    for qa in qa_pairs:
        if qa.included_in_pdf:
            formatted_pairs.append({
                'question_number': qa.question_number,
                'question_text': qa.question_text,
                'answer_text': qa.answer_text,
                'question_type': qa.question_type,
                'llm_score': qa.llm_score,
                'llm_analysis': qa.llm_analysis
            })
    
    return formatted_pairs

def analyze_all_unanalyzed_qa_pairs(session_key):
    """
    Analyze all Q&A pairs in a session that haven't been analyzed yet
    """
    try:
        session = InterviewSession.objects.get(session_key=session_key)
        unanalyzed_pairs = QAConversationPair.objects.filter(
            session=session,
            llm_analysis__isnull=True
        )
        
        analyzed_count = 0
        for qa_pair in unanalyzed_pairs:
            analyze_qa_with_gemini(qa_pair)
            analyzed_count += 1
        
        print(f"✅ Analyzed {analyzed_count} Q&A pairs for session {session_key}")
        return analyzed_count
        
    except InterviewSession.DoesNotExist:
        print(f"❌ Session not found: {session_key}")
        return 0
    except Exception as e:
        print(f"❌ Error analyzing Q&A pairs: {e}")
        return 0

def get_qa_summary_stats(session_key):
    """
    Get summary statistics for Q&A pairs in a session
    """
    try:
        session = InterviewSession.objects.get(session_key=session_key)
        qa_pairs = QAConversationPair.objects.filter(session=session)
        
        if not qa_pairs.exists():
            return None
        
        # Calculate statistics
        total_pairs = qa_pairs.count()
        analyzed_pairs = qa_pairs.filter(llm_analysis__isnull=False).count()
        avg_score = qa_pairs.filter(llm_score__isnull=False).aggregate(
            models.Avg('llm_score')
        )['llm_score__avg'] or 0
        
        avg_wpm = qa_pairs.filter(words_per_minute__isnull=False).aggregate(
            models.Avg('words_per_minute')
        )['words_per_minute__avg'] or 0
        
        total_filler_words = qa_pairs.aggregate(
            models.Sum('filler_word_count')
        )['filler_word_count__sum'] or 0
        
        # Question type breakdown
        question_types = qa_pairs.values('question_type').annotate(
            count=models.Count('question_type')
        ).order_by('-count')
        
        return {
            'total_pairs': total_pairs,
            'analyzed_pairs': analyzed_pairs,
            'analysis_completion': (analyzed_pairs / total_pairs * 100) if total_pairs > 0 else 0,
            'avg_score': round(avg_score, 2),
            'avg_wpm': round(avg_wpm, 2),
            'total_filler_words': total_filler_words,
            'question_types': list(question_types)
        }
        
    except InterviewSession.DoesNotExist:
        return None
    except Exception as e:
        print(f"❌ Error getting Q&A summary stats: {e}")
        return None
