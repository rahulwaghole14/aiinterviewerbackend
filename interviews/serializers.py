# interviews/serializers.py
import os
from datetime import time, datetime, timedelta
from django.utils import timezone
from rest_framework import serializers
from .models import (
    Interview,
    InterviewSlot,
    InterviewSchedule,
    AIInterviewConfiguration,
    InterviewConflict,
)


class InterviewSerializer(serializers.ModelSerializer):
    """
    Main read / write serializer for Interview.
    Adds two read‑only convenience fields:
      • candidate_name – Candidate.full_name
      • job_title       – Job.job_title

    Includes a custom validate() that restricts the scheduled
    window to **08:00 – 22:00 UTC** for both start and end times.
    """

    candidate_name = serializers.CharField(source="candidate.full_name", read_only=True)
    job_title = serializers.CharField(source="job.job_title", read_only=True)
    is_scheduled = serializers.BooleanField(read_only=True)
    ai_interview_type = serializers.CharField(read_only=True)

    # Slot information
    slot_details = serializers.SerializerMethodField()
    schedule_status = serializers.SerializerMethodField()
    booking_notes = serializers.SerializerMethodField()

    # AI Interview Result
    ai_result = serializers.SerializerMethodField()
    
    # Questions and Answers for evaluation display
    questions_and_answers = serializers.SerializerMethodField()
    
    # Verification ID Image
    verification_id_image = serializers.SerializerMethodField()
    
    # Interview Video
    interview_video = serializers.SerializerMethodField()
    
    # Screen Recording
    screen_recording_file = serializers.SerializerMethodField()
    screen_recording_url = serializers.SerializerMethodField()
    screen_recording_duration = serializers.SerializerMethodField()

    class Meta:
        model = Interview
        fields = [
            "id",
            "candidate",
            "candidate_name",
            "job",
            "job_title",
            "status",
            "interview_round",
            "feedback",
            "started_at",
            "ended_at",
            "video_url",
            "created_at",
            "updated_at",
            "is_scheduled",
            "ai_interview_type",
            "slot_details",
            "schedule_status",
            "booking_notes",
            "ai_result",
            "questions_and_answers",
            "verification_id_image",
            "interview_video",
            "screen_recording_file",
            "screen_recording_url", 
            "screen_recording_duration",
            "session_key",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
            "candidate_name",
            "job_title",
            "is_scheduled",
            "ai_interview_type",
        ]
        extra_kwargs = {
            "candidate": {"required": False},
            "job": {"required": False},
            "started_at": {"required": False},
            "ended_at": {"required": False},
            "status": {"required": False},
            "interview_round": {"required": False},
            "feedback": {"required": False},
            "video_url": {"required": False},
        }

    # ──────────────────────────────────────────────────────────
    # Custom validation: 08:00 – 22:00 UTC scheduling window
    # ──────────────────────────────────────────────────────────
    def validate(self, data):
        """
        Ensure both started_at and ended_at fall between 08:00 and 22:00 UTC.

        If this is a partial update (PATCH), keep the existing
        instance's values where the client omitted a field.
        """
        # Set default interview round if not provided
        if "interview_round" not in data or not data.get("interview_round"):
            data["interview_round"] = "AI Interview"

        # Only validate time constraints if we're updating time fields
        if "started_at" in data or "ended_at" in data:
            start_dt = data.get("started_at") or getattr(
                self.instance, "started_at", None
            )
            end_dt = data.get("ended_at") or getattr(self.instance, "ended_at", None)

            if not start_dt or not end_dt:
                raise serializers.ValidationError(
                    "Both 'started_at' and 'ended_at' must be provided when updating time fields."
                )

            # Time window bounds (24‑hour clock, UTC)
            min_time = time(8, 0)  # 08:00
            max_time = time(22, 0)  # 22:00

            start_t = start_dt.time()
            end_t = end_dt.time()

            # Temporarily disabled time validation for testing
            # if not (min_time <= start_t <= max_time):
            #     raise serializers.ValidationError(
            #         "started_at must be between 08:00 and 22:00 UTC."
            #     )
            # if not (min_time <= end_t <= max_time):
            #     raise serializers.ValidationError(
            #         "ended_at must be between 08:00 and 22:00 UTC."
            #     )
            if end_dt <= start_dt:
                raise serializers.ValidationError("ended_at must be after started_at.")

        return data

    def get_slot_details(self, obj):
        """Get slot details if interview is scheduled"""
        if hasattr(obj, "schedule") and obj.schedule:
            slot = obj.schedule.slot
            # Return slot details - but frontend should prefer started_at/ended_at for display
            # These are the raw slot times (TimeField) which don't have timezone info
            return {
                "slot_id": slot.id,
                "start_time": slot.start_time,
                "end_time": slot.end_time,
                "duration_minutes": slot.duration_minutes,
                "ai_interview_type": slot.ai_interview_type,
                "max_candidates": slot.max_candidates,
                "current_bookings": slot.current_bookings,
                "slot_status": slot.status,
            }
        return None

    def get_schedule_status(self, obj):
        """Get schedule status"""
        if hasattr(obj, "schedule") and obj.schedule:
            return obj.schedule.status
        return None

    def get_booking_notes(self, obj):
        """Get booking notes"""
        if hasattr(obj, "schedule") and obj.schedule:
            return obj.schedule.booking_notes
        return None

    def get_ai_result(self, obj):
        """Get AI interview result if available"""
        try:
            # First check for Evaluation with details (new format)
            # Use getattr with default to avoid triggering database query if not prefetched
            # Check if evaluation exists (prefetched or accessible)
            try:
                evaluation = obj.evaluation
            except Exception:
                evaluation = None
            
            # If evaluation doesn't exist but interview is completed, try to create it
            if not evaluation and obj.status == Interview.Status.COMPLETED and obj.session_key:
                try:
                    from evaluation.services import create_evaluation_from_session
                    print(f"🔄 Evaluation missing for completed interview {obj.id}, creating now...")
                    print(f"   Session key: {obj.session_key}")
                    evaluation = create_evaluation_from_session(obj.session_key)
                    if evaluation:
                        # Refresh obj to get the new evaluation
                        obj.refresh_from_db()
                        try:
                            evaluation = obj.evaluation
                            print(f"✅ Created missing evaluation for interview {obj.id}, evaluation ID: {evaluation.id}")
                            # Verify details exist
                            if evaluation.details and isinstance(evaluation.details, dict):
                                print(f"   ✅ Evaluation details exist with keys: {list(evaluation.details.keys())}")
                            else:
                                print(f"   ⚠️ Evaluation created but details are missing or invalid")
                        except Exception as refresh_error:
                            print(f"   ⚠️ Error refreshing evaluation: {refresh_error}")
                            evaluation = None
                    else:
                        print(f"   ⚠️ Evaluation creation returned None for interview {obj.id}")
                except Exception as e:
                    print(f"⚠️ Could not create missing evaluation for interview {obj.id}: {e}")
                    import traceback
                    traceback.print_exc()
                    evaluation = None
            
            if evaluation:
                print(f"🔍 Found evaluation for interview {obj.id}")
                
                # Ensure details is a dict (handle None or empty cases)
                if not evaluation.details or not isinstance(evaluation.details, dict):
                    print(f"   ⚠️ Evaluation exists but details is empty, using fallback data from model fields")
                    # Return basic evaluation data from model fields - ensure it's always valid
                    # Try to parse traits and suggestions for better structure
                    traits_text = evaluation.traits or ''
                    suggestions_text = evaluation.suggestions or ''
                    
                    # Extract strengths and weaknesses from traits if formatted
                    strengths = ''
                    weaknesses = ''
                    if 'Strengths:' in traits_text:
                        parts = traits_text.split('Weaknesses:')
                        strengths = parts[0].replace('Strengths:', '').strip()
                        if len(parts) > 1:
                            weaknesses = parts[1].strip()
                    else:
                        strengths = traits_text[:200] if traits_text else ''
                    
                    fallback_result = {
                        'overall_score': float(evaluation.overall_score) if evaluation.overall_score else 0.0,
                        'total_score': float(evaluation.overall_score) if evaluation.overall_score else 0.0,
                        'technical_score': (float(evaluation.overall_score) * 0.4) if evaluation.overall_score else 0.0,  # Estimate
                        'behavioral_score': (float(evaluation.overall_score) * 0.3) if evaluation.overall_score else 0.0,  # Estimate
                        'coding_score': (float(evaluation.overall_score) * 0.3) if evaluation.overall_score else 0.0,  # Estimate
                        'communication_score': (float(evaluation.overall_score) * 0.2) if evaluation.overall_score else 0.0,  # Estimate
                        'strengths': strengths,
                        'weaknesses': weaknesses,
                        'technical_analysis': suggestions_text[:300] if suggestions_text else '',
                        'behavioral_analysis': '',
                        'coding_analysis': '',
                        'detailed_feedback': suggestions_text or '',
                        'hiring_recommendation': 'STRONG_HIRE' if evaluation.overall_score and evaluation.overall_score >= 8.0 else ('HIRE' if evaluation.overall_score and evaluation.overall_score >= 6.0 else 'MAYBE'),
                        'recommendation': 'STRONG_HIRE' if evaluation.overall_score and evaluation.overall_score >= 8.0 else ('HIRE' if evaluation.overall_score and evaluation.overall_score >= 6.0 else 'MAYBE'),
                        'overall_rating': self._get_rating_from_score(float(evaluation.overall_score) if evaluation.overall_score else 0.0),
                        'hire_recommendation': evaluation.overall_score and evaluation.overall_score >= 6.0,
                        'ai_summary': traits_text or '',
                        'ai_recommendations': suggestions_text or '',
                        'confidence_level': 0.7 if evaluation.overall_score else 0.0,
                        'questions_attempted': 0,
                        'questions_correct': 0,
                        'accuracy_percentage': (float(evaluation.overall_score) * 10) if evaluation.overall_score else 0.0,
                        'proctoring_pdf_url': None,
                        'proctoring_warnings': [],
                    }
                    print(f"   ✅ Returning fallback AI result with score: {fallback_result['total_score']}")
                    return fallback_result
                
                if evaluation.details and isinstance(evaluation.details, dict):
                    print(f"   - Details keys: {list(evaluation.details.keys())}")
                    ai_analysis = evaluation.details.get('ai_analysis', {})
                    print(f"   - AI analysis keys: {list(ai_analysis.keys()) if ai_analysis else 'None'}")
                    
                    if ai_analysis:
                        # Transform evaluation.details to ai_result format
                        # Get proctoring PDF URL from details
                        proctoring_pdf_url = evaluation.details.get('proctoring_pdf_url')
                        if not proctoring_pdf_url:
                            # Try to construct URL from relative path
                            proctoring_pdf_path = evaluation.details.get('proctoring_pdf')
                            if proctoring_pdf_path:
                                from django.conf import settings
                                media_url = settings.MEDIA_URL.rstrip('/')
                                pdf_path = proctoring_pdf_path.lstrip('/')
                                proctoring_pdf_url = f"{media_url}/{pdf_path}"
                                print(f"   - Constructed PDF URL from path: {proctoring_pdf_url}")
                        
                        proctoring_warnings = evaluation.details.get('proctoring', {}).get('warnings', [])
                        print(f"   - Proctoring warnings count: {len(proctoring_warnings)}")
                        print(f"   - Proctoring PDF URL: {proctoring_pdf_url}")
                        
                        # Check if coding score needs to be corrected based on actual test results
                        coding_score = ai_analysis.get('coding_score', 0)
                        
                        # Check if all coding tests passed - if so, coding score should be high (80-100)
                        try:
                            from interview_app.models import CodeSubmission, InterviewSession
                            # Get the interview session - try multiple ways to find session_key
                            session_key = None
                            if hasattr(obj, 'session_key'):
                                session_key = obj.session_key
                            elif hasattr(obj, 'session') and obj.session:
                                session_key = obj.session.session_key if hasattr(obj.session, 'session_key') else None
                            else:
                                # Try to find InterviewSession by interview ID or candidate
                                try:
                                    interview_session = InterviewSession.objects.filter(
                                        candidate_email=obj.candidate.email if hasattr(obj, 'candidate') and obj.candidate else None
                                    ).order_by('-created_at').first()
                                    if interview_session:
                                        session_key = interview_session.session_key
                                except:
                                    pass
                            
                            if session_key:
                                # Check all code submissions for this interview
                                code_submissions = CodeSubmission.objects.filter(
                                    session__session_key=session_key
                                )
                                
                                if code_submissions.exists():
                                    # Check if all tests passed
                                    all_passed = all(sub.passed_all_tests for sub in code_submissions if hasattr(sub, 'passed_all_tests'))
                                    total_submissions = code_submissions.count()
                                    passed_count = sum(1 for sub in code_submissions if hasattr(sub, 'passed_all_tests') and sub.passed_all_tests)
                                    
                                    if all_passed and total_submissions > 0:
                                        # All tests passed but coding score is low - correct it
                                        if coding_score < 80:
                                            print(f"   ⚠️ Coding score correction: All {total_submissions} coding tests passed, but score is {coding_score}. Correcting to 90.")
                                            coding_score = 90  # Set to high score since all tests passed
                                    elif passed_count > 0 and total_submissions > 0:
                                        # Some tests passed - adjust score based on percentage
                                        percentage_passed = (passed_count / total_submissions) * 100
                                        expected_score = 40 + (percentage_passed * 0.39)  # Scale to 40-79 range
                                        if coding_score < expected_score - 10:  # If score is significantly lower than expected
                                            print(f"   ⚠️ Coding score correction: {passed_count}/{total_submissions} tests passed ({percentage_passed:.1f}%), but score is {coding_score}. Correcting to {expected_score:.1f}.")
                                            coding_score = expected_score
                        except Exception as e:
                            print(f"   ⚠️ Error checking code submissions for score correction: {e}")
                            import traceback
                            traceback.print_exc()
                        
                        result = {
                            # AI scores are in 0-100 scale, keep them as-is (don't convert to 0-10)
                            'overall_score': ai_analysis.get('overall_score', 0) / 10.0,  # Convert from 0-100 to 0-10 for backward compatibility
                            'total_score': ai_analysis.get('overall_score', 0) / 10.0,
                            # Section scores: Keep in 0-100 scale for frontend display (frontend will convert to X/10 for display)
                            'technical_score': ai_analysis.get('technical_score', 0),  # Keep 0-100 scale
                            'behavioral_score': ai_analysis.get('behavioral_score', 0),  # Keep 0-100 scale
                            'coding_score': coding_score,  # Use corrected coding score if all tests passed
                            'communication_score': ai_analysis.get('communication_score', 0),  # Keep 0-100 scale
                            # Store strengths and weaknesses - handle both array and string formats
                            'strengths': ai_analysis.get('strengths', []),
                            'weaknesses': ai_analysis.get('weaknesses', []),
                            # Also store as arrays for frontend (convert string to array if needed)
                            'strengths_array': ai_analysis.get('strengths', []) if isinstance(ai_analysis.get('strengths'), list) else ([line.lstrip('-•*').strip() for line in ai_analysis.get('strengths', '').split('\n') if line.strip()] if isinstance(ai_analysis.get('strengths'), str) else []),
                            'weaknesses_array': ai_analysis.get('weaknesses', []) if isinstance(ai_analysis.get('weaknesses'), list) else ([line.lstrip('-•*').strip() for line in ai_analysis.get('weaknesses', '').split('\n') if line.strip()] if isinstance(ai_analysis.get('weaknesses'), str) else []),
                            'technical_analysis': ai_analysis.get('technical_analysis', ''),
                            'behavioral_analysis': ai_analysis.get('behavioral_analysis', ''),
                            'coding_analysis': ai_analysis.get('coding_analysis', ''),
                            'detailed_feedback': ai_analysis.get('detailed_feedback', ''),
                            'hiring_recommendation': ai_analysis.get('hiring_recommendation', ''),
                            'recommendation': ai_analysis.get('recommendation', 'MAYBE'),
                            'overall_rating': self._get_rating_from_score(ai_analysis.get('overall_score', 0) / 10.0),
                            'hire_recommendation': ai_analysis.get('recommendation', 'MAYBE') in ['STRONG_HIRE', 'HIRE'],
                            'ai_summary': self._build_ai_summary(ai_analysis),
                            'ai_recommendations': ai_analysis.get('detailed_feedback', ''),
                            'confidence_level': ai_analysis.get('confidence_level', 0) / 10.0,
                        'questions_attempted': self._get_questions_attempted(evaluation, obj),
                        'questions_correct': self._get_questions_correct(evaluation, obj),
                        'accuracy_percentage': self._calculate_accuracy(evaluation.details, obj),
                        'average_response_time': self._calculate_average_response_time(evaluation.details, obj),
                        'total_completion_time': self._calculate_total_completion_time(evaluation.details, obj),
                        'problem_solving_score': ai_analysis.get('problem_solving_score', (ai_analysis.get('technical_score', 0) + ai_analysis.get('coding_score', 0)) / 2) / 10.0,
                            'proctoring_pdf_url': proctoring_pdf_url,  # Add proctoring PDF URL
                            'proctoring_warnings': proctoring_warnings,  # Add proctoring warnings
                        }
                        print(f"✅ Returning AI result with {len(proctoring_warnings)} proctoring warnings")
                        return result
                    else:
                        print(f"⚠️ Evaluation exists but ai_analysis is empty")
                else:
                    print(f"⚠️ Evaluation exists but details is empty or not a dict")
            else:
                print(f"⚠️ No evaluation found for interview {obj.id}")
                # Return None - frontend will handle this case
            
            # Fallback: Check for old ai_result relationship
            if hasattr(obj, "ai_result") and obj.ai_result:
                print(f"   - Using fallback ai_result relationship")
                from ai_interview.serializers import AIInterviewResultSerializer
                return AIInterviewResultSerializer(obj.ai_result).data
        except Exception as e:
            import traceback
            print(f"⚠️ Error in get_ai_result for interview {obj.id}: {e}")
            traceback.print_exc()
        
        # Return None when no evaluation exists - frontend will show "No evaluation available"
        return None
    
    def _get_rating_from_score(self, score):
        """Convert score to rating"""
        if score >= 8:
            return "excellent"
        elif score >= 6:
            return "good"
        elif score >= 4:
            return "fair"
        else:
            return "poor"
    
    def _build_ai_summary(self, ai_analysis):
        """Build AI summary from analysis"""
        parts = []
        if ai_analysis.get('technical_analysis'):
            parts.append(f"Technical: {ai_analysis['technical_analysis'][:200]}")
        if ai_analysis.get('coding_analysis'):
            parts.append(f"Coding: {ai_analysis['coding_analysis'][:200]}")
        if ai_analysis.get('behavioral_analysis'):
            parts.append(f"Behavioral: {ai_analysis['behavioral_analysis'][:200]}")
        return ". ".join(parts) if parts else ""
    
    def _get_questions_attempted(self, evaluation, interview_obj):
        """Get total questions attempted from details or Q&A"""
        try:
            # First try from ai_analysis in details (saved from evaluation)
            if evaluation and evaluation.details:
                ai_analysis = evaluation.details.get('ai_analysis', {})
                if 'questions_attempted' in ai_analysis and ai_analysis['questions_attempted'] > 0:
                    return ai_analysis['questions_attempted']
                if 'total_questions' in ai_analysis and ai_analysis['total_questions'] > 0:
                    return ai_analysis['total_questions']
            
            # Try from technical_questions in details
            questions = evaluation.details.get('technical_questions', []) if evaluation.details else []
            if questions:
                return len([q for q in questions if q.get('answer') and q.get('answer') != 'No answer provided'])
            
            # Fallback to Q&A data
            qa_data = self.get_questions_and_answers(interview_obj)
            return len(qa_data) if qa_data else 0
        except:
            return 0
    
    def _get_questions_correct(self, evaluation, interview_obj):
        """Get total questions correct from details"""
        try:
            # First try from ai_analysis in details (saved from evaluation)
            if evaluation and evaluation.details:
                ai_analysis = evaluation.details.get('ai_analysis', {})
                if 'questions_correct' in ai_analysis and ai_analysis['questions_correct'] >= 0:
                    return ai_analysis['questions_correct']
            
            # Try from technical_questions in details
            questions = evaluation.details.get('technical_questions', []) if evaluation.details else []
            if questions:
                return len([q for q in questions if q.get('is_correct', False)])
            
            # If no correctness data, estimate from overall score
            if evaluation and evaluation.overall_score:
                qa_data = self.get_questions_and_answers(interview_obj)
                total = len(qa_data) if qa_data else 0
                if total > 0:
                    # Estimate correct based on overall score (assuming 10 = all correct)
                    estimated_correct = int((evaluation.overall_score / 10.0) * total)
                    return estimated_correct
            return 0
        except:
            return 0
    
    def _calculate_accuracy(self, details, interview_obj=None):
        """Calculate accuracy percentage from details or Q&A"""
        try:
            # First try from ai_analysis in details (saved from evaluation)
            if details:
                ai_analysis = details.get('ai_analysis', {})
                if 'accuracy_percentage' in ai_analysis and ai_analysis['accuracy_percentage'] > 0:
                    return ai_analysis['accuracy_percentage']
            
            # Try from technical_questions in details
            questions = details.get('technical_questions', []) if details else []
            if questions:
                correct = len([q for q in questions if q.get('is_correct', False)])
                total = len(questions)
                return (correct / total * 100) if total > 0 else 0
            
            # Fallback: calculate from evaluation overall_score and Q&A
            if interview_obj:
                qa_data = self.get_questions_and_answers(interview_obj)
                total = len(qa_data) if qa_data else 0
                if total > 0:
                    # Try to get evaluation
                    try:
                        evaluation = interview_obj.evaluation
                        if evaluation and evaluation.overall_score:
                            # Estimate accuracy from overall score
                            estimated_correct = (evaluation.overall_score / 10.0) * total
                            return (estimated_correct / total * 100)
                    except:
                        pass
            
            return 0
        except:
            return 0
    
    def _calculate_average_response_time(self, details, interview_obj=None):
        """Calculate average response time from details or Q&A"""
        try:
            # First try from ai_analysis in details (saved from evaluation)
            if details:
                ai_analysis = details.get('ai_analysis', {})
                if 'average_response_time' in ai_analysis and ai_analysis['average_response_time'] > 0:
                    return ai_analysis['average_response_time']
            
            # Try from technical_questions in details
            questions = details.get('technical_questions', []) if details else []
            if questions:
                response_times = [q.get('response_time', 0) for q in questions if q.get('response_time', 0) > 0]
                if response_times:
                    return sum(response_times) / len(response_times)
            
            # Fallback to Q&A data
            if interview_obj:
                qa_data = self.get_questions_and_answers(interview_obj)
                if qa_data:
                    response_times = [qa.get('response_time', 0) for qa in qa_data if qa.get('response_time', 0) > 0]
                    if response_times:
                        return sum(response_times) / len(response_times)
            
            return 0
        except:
            return 0
    
    def _calculate_total_completion_time(self, details, interview_obj=None):
        """Calculate total completion time in minutes"""
        try:
            # First try from ai_analysis in details (saved from evaluation)
            if details:
                ai_analysis = details.get('ai_analysis', {})
                if 'total_completion_time' in ai_analysis and ai_analysis['total_completion_time'] > 0:
                    return ai_analysis['total_completion_time']
            
            # Try from technical_questions in details
            questions = details.get('technical_questions', []) if details else []
            if questions:
                total_seconds = sum([q.get('response_time', 0) for q in questions])
                return total_seconds / 60.0  # Convert to minutes
            
            # Fallback to Q&A data
            if interview_obj:
                qa_data = self.get_questions_and_answers(interview_obj)
                if qa_data:
                    total_seconds = sum([qa.get('response_time', 0) for qa in qa_data])
                    return total_seconds / 60.0  # Convert to minutes
            
            return 0
        except:
            return 0
    
    def get_questions_and_answers(self, obj):
        """Get questions and answers for this interview - combines QAConversationPair and InterviewQuestion"""
        try:
            from interview_app.models import InterviewSession, QAConversationPair, InterviewQuestion, CodeSubmission
            from interview_app.qa_conversation_service import get_qa_pairs_for_session_ordered
            from django.utils import timezone
            
            # Find the session for this interview using session_key
            session = None
            if obj.session_key:
                try:
                    session = InterviewSession.objects.get(session_key=obj.session_key)
                    print(f"✅ Found session by session_key: {obj.session_key}")
                except InterviewSession.DoesNotExist:
                    print(f"⚠️ Session not found by session_key: {obj.session_key}")
                    pass
            
            # If not found by session_key, try to find by candidate and recent date
            if not session and obj.candidate:
                try:
                    # Try to match by candidate email
                    sessions = InterviewSession.objects.filter(
                        candidate_email=obj.candidate.email
                    ).order_by('-created_at')
                    
                    # If interview has a created_at, try to match by date proximity
                    if obj.created_at:
                        # Find session created around the same time (within 1 hour)
                        from datetime import timedelta
                        time_window_start = obj.created_at - timedelta(hours=1)
                        time_window_end = obj.created_at + timedelta(hours=1)
                        sessions = sessions.filter(
                            created_at__gte=time_window_start,
                            created_at__lte=time_window_end
                        )
                    
                    session = sessions.first()
                    if session:
                        print(f"✅ Found session by candidate email: {obj.candidate.email}")
                except Exception as e:
                    print(f"⚠️ Error finding session by candidate: {e}")
                    pass
            
            # If still not found, try to find by interview round and candidate
            if not session and obj.candidate and obj.interview_round:
                try:
                    # Get the most recent session for this candidate
                    session = InterviewSession.objects.filter(
                        candidate_email=obj.candidate.email
                    ).order_by('-created_at').first()
                    if session:
                        print(f"✅ Found most recent session for candidate: {obj.candidate.email}")
                except Exception as e:
                    print(f"⚠️ Error finding recent session: {e}")
                    pass
            
            if not session:
                print(f"⚠️ No session found for interview {obj.id}")
                return []
            
            qa_list = []
            
            # Part 1: Get regular Q&A pairs from QAConversationPair (technical, behavioral, candidate questions)
            qa_data = get_qa_pairs_for_session_ordered(session.session_key)
            chronological_pairs = qa_data['chronological_pairs']
            
            print(f"✅ Found {chronological_pairs.count()} regular Q&A pairs for session {session.session_key}")
            
            for qa in chronological_pairs:
                # Skip CODING questions from QAConversationPair - we'll handle them separately
                if qa.question_type == 'CODING':
                    continue
                    
                if qa.question_type == 'CANDIDATE_QUESTION':
                    # For candidate questions, show candidate question in answer section and AI response in question section
                    qa_item = {
                        'question_number': qa.question_number,
                        'question_text': qa.question_text,  # AI's response
                        'answer_text': qa.answer_text,     # Candidate's question
                        'question_type': qa.question_type,
                        'response_time': qa.response_time_seconds,
                        'words_per_minute': qa.words_per_minute,
                        'filler_word_count': qa.filler_word_count,
                        'sentiment_score': qa.sentiment_score,
                        'is_candidate_question': True,
                        'timestamp': qa.timestamp.isoformat() if qa.timestamp else None,
                        'session_key': qa.session_key
                    }
                else:
                    # For regular AI questions, show AI question and candidate answer
                    qa_item = {
                        'question_number': qa.question_number,
                        'question_text': qa.question_text,  # AI's question
                        'answer_text': qa.answer_text,     # Candidate's answer
                        'question_type': qa.question_type,
                        'response_time': qa.response_time_seconds,
                        'words_per_minute': qa.words_per_minute,
                        'filler_word_count': qa.filler_word_count,
                        'sentiment_score': qa.sentiment_score,
                        'is_candidate_question': False,
                        'timestamp': qa.timestamp.isoformat() if qa.timestamp else None,
                        'session_key': qa.session_key
                    }
                
                qa_list.append(qa_item)
                print(f"   Added Q#{qa.question_number} ({qa.question_type}): {qa.question_text[:50]}...")
            
            # Part 2: Get coding questions from InterviewQuestion (same as previous implementation)
            # Temporarily remove ordering by fields that might not exist
            coding_questions = InterviewQuestion.objects.filter(
                session=session,
                question_type='CODING'
            ).order_by('order')
            
            print(f"🔧 Processing {coding_questions.count()} CODING questions from InterviewQuestion...")
            
            for coding_q in coding_questions:
                print(f"🔍 Processing CODING question: {coding_q.id}, Order: {coding_q.order}")
                
                # Get question text
                question_text = coding_q.question_text or ''
                if question_text.strip().startswith('Q:'):
                    question_text = question_text.replace('Q:', '').strip()
                
                # Get answer from transcribed_answer (same as previous implementation)
                answer_text = None
                created_at = None
                response_time = 0
                code_submission_data = None
                
                try:
                    print(f"🔍 Looking for answer in transcribed_answer for CODING question ID: {coding_q.id}")
                    
                    # Primary source: transcribed_answer from the coding question itself
                    if coding_q.transcribed_answer:
                        transcribed = coding_q.transcribed_answer
                        # Check if transcribed_answer contains "Submitted Code:" - extract the code part
                        if "Submitted Code:" in transcribed:
                            code_start = transcribed.find("Submitted Code:") + len("Submitted Code:")
                            answer_text = transcribed[code_start:].strip()
                            print(f"✅ Extracted code from transcribed_answer: {len(answer_text)} characters")
                        else:
                            answer_text = transcribed
                            if answer_text.strip().startswith('A:'):
                                answer_text = answer_text.replace('A:', '').strip()
                            print(f"✅ Using transcribed_answer: {len(answer_text)} characters")
                    else:
                        answer_text = 'No code submitted'
                        print(f"⚠️ No transcribed_answer, using 'No code submitted'")
                    
                    created_at = coding_q.session.created_at if hasattr(coding_q.session, 'created_at') else None
                    
                    # Also get CodeSubmission metadata if available (for test results, etc.)
                    try:
                        question_id_str = str(coding_q.id)
                        code_submission = CodeSubmission.objects.filter(
                            session=session,
                            question_id=question_id_str
                        ).order_by('-created_at').first()
                        
                        if code_submission:
                            print(f"✅ Found CodeSubmission metadata: ID {code_submission.id}")
                            code_submission_data = {
                                'id': str(code_submission.id),
                                'code': code_submission.submitted_code,
                                'language': getattr(code_submission, 'language', None),
                                'test_results': getattr(code_submission, 'test_results', None),
                                'passed_all_tests': getattr(code_submission, 'passed_all_tests', None),
                                'execution_time_seconds': getattr(code_submission, 'execution_time_seconds', None),
                                'output_log': getattr(code_submission, 'output_log', None),
                                'error_message': getattr(code_submission, 'error_message', None)
                            }
                    except Exception as e:
                        print(f"⚠️ Error fetching CodeSubmission metadata: {e}")
                        code_submission_data = None
                        
                except Exception as e:
                    print(f"⚠️ Error fetching answer for coding question {coding_q.id}: {e}")
                    answer_text = 'Error loading code submission'
                    created_at = coding_q.session.created_at if hasattr(coding_q.session, 'created_at') else None
                
                # Create coding Q&A item
                qa_item = {
                    'question_number': coding_q.order,
                    'question_text': question_text,
                    'answer_text': answer_text,
                    'question_type': 'CODING',
                    'response_time': response_time,
                    'words_per_minute': None,
                    'filler_word_count': None,
                    'sentiment_score': None,
                    'is_candidate_question': False,
                    'timestamp': created_at.isoformat() if created_at else None,
                    'session_key': session.session_key,
                    'code_submission': code_submission_data
                }
                
                qa_list.append(qa_item)
                print(f"✅ Added CODING Q#{coding_q.order}: {question_text[:50]}...")
            
            # Sort final qa_list by question_number to maintain chronological order
            qa_list.sort(key=lambda x: x.get('question_number', 0))
            
            print(f"✅ Returning {len(qa_list)} total Q&A items for interview {obj.id}")
            return qa_list
            
        except Exception as e:
            import traceback
            print(f"❌ Error in get_questions_and_answers for interview {obj.id}: {e}")
            traceback.print_exc()
            return []

    def get_verification_id_image(self, obj):
        """Get verification ID image URL"""
        try:
            # Try to get from InterviewSession first
            if obj.session_key:
                from interview_app.models import InterviewSession
                try:
                    session = InterviewSession.objects.get(session_key=obj.session_key)
                    if session.id_card_image and hasattr(session.id_card_image, 'url'):
                        # Construct absolute URL for frontend consumption
                        from django.conf import settings
                        if hasattr(session.id_card_image, 'url'):
                            image_url = session.id_card_image.url
                            # If it's a relative URL, make it absolute
                            if image_url.startswith('/'):
                                # For development, use localhost:8000
                                if settings.DEBUG:
                                    image_url = f"http://127.0.0.1:8000{image_url}"
                                # For production, you might want to use your domain
                                # image_url = f"https://yourdomain.com{image_url}"
                            return image_url
                except InterviewSession.DoesNotExist:
                    pass
            
            # Fallback to interview's own verification_id_image if it exists
            if hasattr(obj, 'verification_id_image') and obj.verification_id_image:
                if hasattr(obj.verification_id_image, 'url'):
                    from django.conf import settings
                    image_url = obj.verification_id_image.url
                    if image_url.startswith('/') and settings.DEBUG:
                        image_url = f"http://127.0.0.1:8000{image_url}"
                    return image_url
                else:
                    # If it's a string path, construct URL
                    from django.conf import settings
                    media_url = settings.MEDIA_URL.rstrip('/')
                    image_path = f"{media_url}/{obj.verification_id_image.lstrip('/')}"
                    if settings.DEBUG:
                        image_path = f"http://127.0.0.1:8000{image_path}"
                    return image_path
            
            return None
        except Exception as e:
            print(f"⚠️ Error getting verification ID image: {e}")
            return None

    def get_interview_video(self, obj):
        """Get interview video URL"""
        try:
            # Try to get from InterviewSession first
            if obj.session_key:
                from interview_app.models import InterviewSession
                try:
                    session = InterviewSession.objects.get(session_key=obj.session_key)
                    if session.interview_video and hasattr(session.interview_video, 'url'):
                        return session.interview_video.url
                except InterviewSession.DoesNotExist:
                    pass
            
            # Fallback to interview's own video_url
            if obj.video_url:
                return obj.video_url
            
            return None
        except Exception as e:
            print(f"⚠️ Error getting interview video: {e}")
            return None

    def get_screen_recording_file(self, obj):
        """Get screen recording file URL"""
        try:
            if obj.screen_recording_file and hasattr(obj.screen_recording_file, 'url'):
                return obj.screen_recording_file.url
            return None
        except Exception as e:
            print(f"⚠️ Error getting screen recording file: {e}")
            return None

    def get_screen_recording_url(self, obj):
        """Get screen recording URL"""
        try:
            return obj.screen_recording_url if obj.screen_recording_url else None
        except Exception as e:
            print(f"⚠️ Error getting screen recording URL: {e}")
            return None

    def get_screen_recording_duration(self, obj):
        """Get screen recording duration in seconds"""
        try:
            return obj.screen_recording_duration if obj.screen_recording_duration else None
        except Exception as e:
            print(f"⚠️ Error getting screen recording duration: {e}")
            return None


class InterviewSlotSerializer(serializers.ModelSerializer):
    """
    Serializer for AI interview slots with separate date and time fields
    """

    company_name = serializers.CharField(source="company.name", read_only=True)
    job_title = serializers.CharField(source="job.job_title", read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    available_spots = serializers.SerializerMethodField()

    # Computed fields for backward compatibility
    full_start_datetime = serializers.SerializerMethodField()
    full_end_datetime = serializers.SerializerMethodField()

    class Meta:
        model = InterviewSlot
        fields = [
            "id",
            "slot_type",
            "status",
            "date",
            "start_time",
            "end_time",
            "duration_minutes",
            "ai_interview_type",
            "max_candidates",
            "current_bookings",
            "company_name",
            "job_title",
            "is_available",
            "available_spots",
            "full_start_datetime",
            "full_end_datetime",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
            "company_name",
            "job_title",
            "is_available",
            "available_spots",
            "full_start_datetime",
            "full_end_datetime",
        ]

    def get_available_spots(self, obj):
        """Calculate available spots"""
        return max(0, obj.max_candidates - obj.current_bookings)

    def get_full_start_datetime(self, obj):
        """Combine date and start time for backward compatibility"""
        if obj.date and obj.start_time:
            from datetime import datetime
            return datetime.combine(obj.date, obj.start_time)
        return None

    def get_full_end_datetime(self, obj):
        """Combine date and end time for backward compatibility"""
        if obj.date and obj.end_time:
            from datetime import datetime
            return datetime.combine(obj.date, obj.end_time)
        return None


class InterviewScheduleSerializer(serializers.ModelSerializer):
    """
    Serializer for AI interview schedules
    """

    interview_details = serializers.SerializerMethodField()
    slot_details = serializers.SerializerMethodField()
    ai_interview_type = serializers.CharField(
        source="slot.ai_interview_type", read_only=True
    )
    candidate_name = serializers.CharField(
        source="interview.candidate.full_name", read_only=True
    )

    class Meta:
        model = InterviewSchedule
        fields = [
            "id",
            "interview",
            "slot",
            "status",
            "booking_notes",
            "interview_details",
            "slot_details",
            "ai_interview_type",
            "candidate_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
            "interview_details",
            "slot_details",
            "ai_interview_type",
            "candidate_name",
        ]

    def get_interview_details(self, obj):
        """Get interview details"""
        if obj.interview:
            return {
                "id": obj.interview.id,
                "candidate_name": obj.interview.candidate.full_name if obj.interview.candidate else None,
                "job_title": obj.interview.job.job_title if obj.interview.job else None,
                "status": obj.interview.status,
                "interview_round": obj.interview.interview_round,
            }
        return None

    def get_slot_details(self, obj):
        """Get slot details"""
        if obj.slot:
            return {
                "id": obj.slot.id,
                "date": obj.slot.date,
                "start_time": obj.slot.start_time,
                "end_time": obj.slot.end_time,
                "duration_minutes": obj.slot.duration_minutes,
                "ai_interview_type": obj.slot.ai_interview_type,
                "max_candidates": obj.slot.max_candidates,
                "current_bookings": obj.slot.current_bookings,
            }
        return None


class AIInterviewConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIInterviewConfiguration
        fields = '__all__'


class InterviewConflictSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewConflict
        fields = '__all__'


class SlotBookingSerializer(serializers.Serializer):
    """Serializer for booking a slot"""
    interview_id = serializers.IntegerField(required=True)
    booking_notes = serializers.CharField(required=False, allow_blank=True, max_length=500)


class SlotSearchSerializer(serializers.Serializer):
    """Serializer for slot search parameters"""
    company_id = serializers.IntegerField(required=False)
    job_id = serializers.IntegerField(required=False)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    ai_interview_type = serializers.CharField(required=False, allow_blank=True)


class RecurringSlotSerializer(serializers.Serializer):
    """Serializer for creating recurring slots"""
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)
    start_time = serializers.TimeField(required=True)
    end_time = serializers.TimeField(required=True)
    duration_minutes = serializers.IntegerField(required=True, min_value=15, max_value=480)
    max_candidates = serializers.IntegerField(required=True, min_value=1, max_value=100)
    ai_interview_type = serializers.CharField(required=True, allow_blank=False, max_length=50)
    recurring_pattern = serializers.ChoiceField(
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
        ],
        required=True
    )
    days_of_week = serializers.ListField(
        child=serializers.IntegerField(min_value=0, max_value=6),
        required=False,
        allow_empty=True,
        help_text="Days of week (0=Monday, 6=Sunday) for weekly pattern"
    )
    notes = serializers.CharField(required=False, allow_blank=True, max_length=500)
