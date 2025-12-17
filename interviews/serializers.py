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
        """Get questions and answers for this interview"""
        try:
            from interview_app.models import InterviewSession, InterviewQuestion
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
            
            # Get all conversation items (AI and Interviewee responses) in sequential order
            # Order by 'conversation_sequence' if available (new format), otherwise by 'order' and 'id' (old format)
            # IMPORTANT: Use conversation_sequence for proper sequential ordering of AI/Interviewee conversation
            questions = InterviewQuestion.objects.filter(
                session=session
            ).order_by(
                'conversation_sequence',  # Primary: Use conversation_sequence for sequential ordering
                'order',  # Secondary: Fallback to order if conversation_sequence is null
                'id'  # Tertiary: Use id for consistency when both are same
            )
            
            # Additional validation: Ensure order values are sequential and fix any gaps
            # This helps catch any ordering issues
            question_list = list(questions)
            if question_list:
                orders = [q.order for q in question_list]
                if len(set(orders)) != len(orders):
                    print(f"⚠️ WARNING: Duplicate order values detected! Orders: {orders}")
                # Log order sequence for debugging
                print(f"📋 Question order sequence: {[f'Q{q.order}({q.question_level})' for q in question_list]}")
            
            print(f"✅ Found {questions.count()} questions for session {session.session_key}")
            # Debug: Print all questions with their order, role, conversation_sequence, and answers
            for q in questions:
                answer_display = q.transcribed_answer[:50] if q.transcribed_answer else '(NULL)'
                role_display = q.role or '(no role)'
                seq_display = q.conversation_sequence if q.conversation_sequence is not None else '(no seq)'
                print(f"   Q{q.order} (seq:{seq_display}, role:{role_display}): {q.question_text[:50] if q.question_text else '(no text)'}... | Answer: {answer_display}... | Type: {q.question_type} | Level: {q.question_level}")
            
            # Also log all INTERVIEWEE records separately for debugging
            interviewee_records = InterviewQuestion.objects.filter(
                session=session,
                role='INTERVIEWEE'
            ).order_by('order', 'conversation_sequence')
            print(f"📋 Found {interviewee_records.count()} INTERVIEWEE records:")
            for ir in interviewee_records:
                answer_display = ir.transcribed_answer[:50] if ir.transcribed_answer else '(NULL)'
                print(f"   INTERVIEWEE Order {ir.order} (seq:{ir.conversation_sequence}, level:{ir.question_level}): Answer: {answer_display}...")
            
            # Import CodeSubmission model
            from interview_app.models import CodeSubmission
            
            qa_list = []
            # Process questions sequentially (already sorted by conversation_sequence, order, id)
            # IMPORTANT: For CODING questions, we need to handle them separately since answers come from CodeSubmission
            coding_questions_list = []  # Track coding questions separately
            questions_by_order = {}  # Group non-coding questions by order for pairing AI with Interviewee
            
            # First pass: Separate CODING questions and group non-coding questions
            for q in questions:
                question_type = (q.question_type or '').upper()
                
                # For CODING questions, track them separately
                if question_type == 'CODING' or question_type == 'CODING CHALLENGE':
                    if q.question_text and q.question_text.strip():
                        coding_questions_list.append(q)
                        print(f"✅ Added CODING question to separate list: ConvSeq {q.conversation_sequence}, Order {q.order}, ID {q.id}, Type: {q.question_type}, Question: {q.question_text[:50]}...")
                    continue
                
                # For non-coding questions, group by order (they may share same order if AI and Interviewee)
                order_key = q.order
                if order_key not in questions_by_order:
                    questions_by_order[order_key] = {'ai': None, 'interviewee': None, 'conversation_sequence': None, 'order': order_key}
                
                # Update conversation_sequence if available (use the AI question's sequence)
                if q.conversation_sequence is not None:
                    if questions_by_order[order_key]['conversation_sequence'] is None:
                        questions_by_order[order_key]['conversation_sequence'] = q.conversation_sequence
                    elif q.role and q.role.upper() == 'AI':
                        # Prefer AI question's conversation_sequence for ordering
                        questions_by_order[order_key]['conversation_sequence'] = q.conversation_sequence
                
                # Check if this is an AI question/response or Interviewee answer/question
                has_role = q.role is not None and q.role.strip()
                if has_role:
                    if q.role.upper() == 'AI' and q.question_text:
                        # AI question or AI response to candidate question
                        # IMPORTANT: Only add if it's not a candidate question incorrectly saved
                        if q.question_level != 'CANDIDATE_QUESTION':
                            questions_by_order[order_key]['ai'] = q
                        else:
                            # This shouldn't happen, but if AI record has CANDIDATE_QUESTION level, skip it
                            print(f"⚠️ Skipping AI record with CANDIDATE_QUESTION level: {q.id}")
                    elif q.role.upper() == 'INTERVIEWEE':
                        if q.question_level == 'CANDIDATE_QUESTION':
                            # Candidate asked a question - this should be shown in answer section
                            # The AI's response (if exists) should be in question section
                            # IMPORTANT: Candidate questions should have empty question_text and text in transcribed_answer
                            if not q.question_text or not q.question_text.strip():
                                questions_by_order[order_key]['interviewee'] = q
                            else:
                                # Candidate question incorrectly has question_text - move it to transcribed_answer
                                print(f"⚠️ Candidate question {q.id} has question_text, should be in transcribed_answer")
                                if not q.transcribed_answer:
                                    q.transcribed_answer = q.question_text
                                    q.question_text = ''
                                    q.save(update_fields=['question_text', 'transcribed_answer'])
                                questions_by_order[order_key]['interviewee'] = q
                        elif q.transcribed_answer or q.question_level == 'INTERVIEWEE_RESPONSE':
                            # Regular candidate answer (including "No answer provided")
                            # IMPORTANT: Include all INTERVIEWEE_RESPONSE records, even if transcribed_answer is empty
                            # This ensures all questions have corresponding answers displayed
                            if not questions_by_order[order_key]['interviewee']:
                                questions_by_order[order_key]['interviewee'] = q
                                print(f"✅ Added INTERVIEWEE record to order {order_key}: {q.transcribed_answer[:50] if q.transcribed_answer else 'No answer'}...")
                            else:
                                # If there's already an interviewee record, prefer the one with transcribed_answer
                                if q.transcribed_answer and not questions_by_order[order_key]['interviewee'].transcribed_answer:
                                    questions_by_order[order_key]['interviewee'] = q
                                    print(f"✅ Replaced INTERVIEWEE record for order {order_key} with one that has answer: {q.transcribed_answer[:50]}...")
                                elif q.transcribed_answer and len(q.transcribed_answer) > len(questions_by_order[order_key]['interviewee'].transcribed_answer or ''):
                                    # Prefer longer answer if both have answers
                                    questions_by_order[order_key]['interviewee'] = q
                                    print(f"✅ Replaced INTERVIEWEE record for order {order_key} with longer answer: {q.transcribed_answer[:50]}...")
                elif q.question_text and q.question_text.strip():
                    # Old format: question_text exists, treat as AI question
                    # But check role first - if role is INTERVIEWEE, it's a candidate question
                    if q.role and q.role.upper() == 'INTERVIEWEE':
                        # This is a candidate question in old format - move to interviewee
                        if q.question_level == 'CANDIDATE_QUESTION':
                            questions_by_order[order_key]['interviewee'] = q
                        else:
                            questions_by_order[order_key]['ai'] = q
                    else:
                        questions_by_order[order_key]['ai'] = q
            
            # Now create Q&A pairs from grouped questions - sort by conversation_sequence first, then order
            sorted_order_keys = sorted(questions_by_order.keys(), key=lambda k: (
                questions_by_order[k].get('conversation_sequence') if questions_by_order[k].get('conversation_sequence') is not None else 999999,
                questions_by_order[k].get('order', 0)
            ))
            
            # Before processing, check for any AI questions without interviewee answers
            # and try to find their corresponding interviewee responses
            for order_key in sorted_order_keys:
                q_pair = questions_by_order[order_key]
                if q_pair['ai'] and not q_pair['interviewee']:
                    # Try to find interviewee response for this order
                    try:
                        missed_interviewee = InterviewQuestion.objects.filter(
                            session=session,
                            order=order_key,
                            role='INTERVIEWEE',
                            question_level='INTERVIEWEE_RESPONSE'
                        ).first()
                        if missed_interviewee:
                            q_pair['interviewee'] = missed_interviewee
                            print(f"✅ Found missed interviewee response for order {order_key} during pairing: {missed_interviewee.transcribed_answer[:50] if missed_interviewee.transcribed_answer else 'No answer'}...")
                    except Exception as e:
                        print(f"⚠️ Error finding missed interviewee response for order {order_key}: {e}")
            
            for order_key in sorted_order_keys:
                q_pair = questions_by_order[order_key]
                ai_q = q_pair['ai']
                interviewee_a = q_pair['interviewee']
                
                # Handle candidate questions: if no AI question but there's an interviewee with CANDIDATE_QUESTION
                if not ai_q and interviewee_a and interviewee_a.question_level == 'CANDIDATE_QUESTION':
                    # Candidate asked a question - look for AI response in next order
                    next_order = order_key + 1
                    if next_order in questions_by_order and questions_by_order[next_order]['ai']:
                        ai_response = questions_by_order[next_order]['ai']
                        if ai_response.question_level == 'AI_RESPONSE':
                            # Use AI response as question, candidate question as answer
                            ai_q = ai_response
                            # Don't process the AI response again when we get to its order
                            questions_by_order[next_order]['processed'] = True
                            print(f"✅ Paired candidate question (order {order_key}) with AI response (order {next_order})")
                    else:
                        # No AI response found yet - skip this for now, it will be processed when AI response is created
                        print(f"⚠️ Candidate question at order {order_key} has no AI response yet, skipping")
                        continue
                
                # Skip if no AI question (after trying to find AI response for candidate questions)
                if not ai_q:
                    continue
                
                # Skip if already processed (as part of candidate question handling)
                if questions_by_order[order_key].get('processed'):
                    continue
                
                # Determine question type (case-insensitive)
                # IMPORTANT: Use the original question_type from database, then uppercase for comparison
                original_question_type = ai_q.question_type or 'TECHNICAL'
                question_type = original_question_type.upper()
                
                # Get question text - always from AI (role='AI', question_text field)
                question_text = ai_q.question_text or ''
                if question_text.strip().startswith('Q:'):
                    question_text = question_text.replace('Q:', '').strip()
                
                # Special handling: If AI response is to a candidate question, get candidate question as answer
                # IMPORTANT: For candidate questions, the question_text should be AI's response, 
                # and the answer should be the candidate's question
                if ai_q.question_level == 'AI_RESPONSE':
                    # This is AI responding to a candidate question
                    # Question section: AI's response (already in question_text from ai_q.question_text)
                    # Answer section: Need to find the candidate's question
                    # Look for interviewee record with CANDIDATE_QUESTION at current or previous order
                    if not interviewee_a or interviewee_a.question_level != 'CANDIDATE_QUESTION':
                        # Try to find candidate question at previous order
                        prev_order = order_key - 1
                        if prev_order in questions_by_order:
                            prev_pair = questions_by_order[prev_order]
                            if prev_pair.get('interviewee') and prev_pair['interviewee'].question_level == 'CANDIDATE_QUESTION':
                                interviewee_a = prev_pair['interviewee']
                                print(f"✅ Found candidate question at previous order {prev_order}")
                elif interviewee_a and interviewee_a.question_level == 'CANDIDATE_QUESTION':
                    # Candidate question is at same order as AI response
                    # This is correct - will be handled in answer section below
                    pass
                
                # Get answer based on question type
                # Handle both 'CODING' and 'CODING CHALLENGE' types
                if question_type == 'CODING' or question_type == 'CODING CHALLENGE':
                    # For CODING questions, get answer from CodeSubmission
                    answer_text = None
                    created_at = None
                    response_time = 0
                    try:
                        print(f"🔍 Looking for CodeSubmission for CODING question ID: {ai_q.id} (as string: {str(ai_q.id)}, UUID: {ai_q.id})")
                        
                        # Try multiple ways to find the CodeSubmission
                        # First: exact match by session and question_id (try both UUID string and direct UUID)
                        question_id_str = str(ai_q.id)
                        code_submission = CodeSubmission.objects.filter(
                            session=session,
                            question_id=question_id_str
                        ).order_by('-created_at').first()
                        
                        # Also try without hyphens (in case UUID is stored differently)
                        if not code_submission:
                            question_id_no_hyphens = question_id_str.replace('-', '')
                            code_submission = CodeSubmission.objects.filter(
                                session=session,
                                question_id=question_id_no_hyphens
                            ).order_by('-created_at').first()
                        
                        if code_submission:
                            print(f"✅ Found CodeSubmission by exact match: ID {code_submission.id}, Question ID: {code_submission.question_id}")
                        else:
                            # Second: try by session only (get the most recent one)
                            print(f"⚠️ No exact match found, trying by session only...")
                            code_submission = CodeSubmission.objects.filter(
                                session=session
                            ).order_by('-created_at').first()
                            
                            if code_submission:
                                print(f"✅ Found CodeSubmission by session: ID {code_submission.id}, Question ID: {code_submission.question_id} (expected: {str(ai_q.id)})")
                            else:
                                # Third: try any CodeSubmission for this question ID (across all sessions)
                                print(f"⚠️ No match by session, trying by question_id only...")
                                code_submission = CodeSubmission.objects.filter(
                                    question_id=str(ai_q.id)
                                ).order_by('-created_at').first()
                                
                                if code_submission:
                                    print(f"✅ Found CodeSubmission by question_id only: ID {code_submission.id}")
                        
                        if code_submission and code_submission.submitted_code:
                            answer_text = code_submission.submitted_code
                            created_at = code_submission.created_at
                            print(f"✅ Using CodeSubmission answer: {len(answer_text)} characters")
                        else:
                            # Check if there's a transcribed_answer as fallback
                            # The transcribed_answer might contain the code if CodeSubmission lookup failed
                            if ai_q.transcribed_answer:
                                transcribed = ai_q.transcribed_answer
                                # Check if transcribed_answer contains "Submitted Code:" - extract the code part
                                if "Submitted Code:" in transcribed:
                                    # Extract code after "Submitted Code:"
                                    code_start = transcribed.find("Submitted Code:") + len("Submitted Code:")
                                    answer_text = transcribed[code_start:].strip()
                                    print(f"⚠️ No CodeSubmission found, extracted code from transcribed_answer: {len(answer_text)} characters")
                                else:
                                    # Use transcribed_answer as-is, but remove A: prefix if present
                                    answer_text = transcribed
                                    if answer_text.strip().startswith('A:'):
                                        answer_text = answer_text.replace('A:', '').strip()
                                    print(f"⚠️ No CodeSubmission found, using transcribed_answer: {len(answer_text)} characters")
                            else:
                                answer_text = 'No code submitted'
                                print(f"⚠️ No CodeSubmission and no transcribed_answer, using 'No code submitted'")
                            created_at = ai_q.session.created_at if hasattr(ai_q.session, 'created_at') else None
                    except Exception as e:
                        print(f"⚠️ Error fetching CodeSubmission for question {ai_q.id}: {e}")
                        import traceback
                        traceback.print_exc()
                        # Fallback to transcribed_answer if available
                        if ai_q.transcribed_answer:
                            transcribed = ai_q.transcribed_answer
                            # Check if transcribed_answer contains "Submitted Code:" - extract the code part
                            if "Submitted Code:" in transcribed:
                                # Extract code after "Submitted Code:"
                                code_start = transcribed.find("Submitted Code:") + len("Submitted Code:")
                                answer_text = transcribed[code_start:].strip()
                            else:
                                answer_text = transcribed
                                if answer_text.strip().startswith('A:'):
                                    answer_text = answer_text.replace('A:', '').strip()
                        else:
                            answer_text = 'No code submitted'
                        created_at = ai_q.session.created_at if hasattr(ai_q.session, 'created_at') else None
                else:
                    # For TECHNICAL and BEHAVIORAL questions
                    # Initialize answer_text to avoid UnboundLocalError
                    answer_text = None
                    created_at = None
                    response_time = 0
                    
                    # CRITICAL: Try multiple methods to find the answer
                    # Method 1: Use the paired interviewee_a if available
                    if interviewee_a:
                        # Use the separate Interviewee record
                        answer_text = interviewee_a.transcribed_answer or ''
                        if answer_text.strip().startswith('A:'):
                            answer_text = answer_text.replace('A:', '').strip()
                        
                        # IMPORTANT: If this is a candidate question (question_level='CANDIDATE_QUESTION'),
                        # the transcribed_answer contains the candidate's question, which should be shown in answer section
                        if interviewee_a.question_level == 'CANDIDATE_QUESTION':
                            # Candidate asked a question - show it in answer section
                            # The answer_text already contains the candidate's question from transcribed_answer
                            answer_text = answer_text.strip() if answer_text else 'No question provided'
                            print(f"✅ Using candidate question as answer: {answer_text[:50]}...")
                        
                        created_at = interviewee_a.session.created_at if hasattr(interviewee_a.session, 'created_at') else None
                        response_time = interviewee_a.response_time_seconds or 0
                        print(f"✅ Found answer from paired interviewee_a for order {ai_q.order}: {answer_text[:50] if answer_text else 'No answer'}...")
                    
                    # Method 2: Try to find interviewee response by order, role, and question_level
                    if not answer_text or (answer_text and answer_text.strip() == ''):
                        try:
                            # First try: exact match by order, role, and question_level
                            missed_interviewee = InterviewQuestion.objects.filter(
                                session=session,
                                order=ai_q.order,
                                role='INTERVIEWEE',
                                question_level='INTERVIEWEE_RESPONSE'
                            ).first()
                            
                            # Second try: if not found, try by order and role only (ignore question_level)
                            if not missed_interviewee:
                                missed_interviewee = InterviewQuestion.objects.filter(
                                    session=session,
                                    order=ai_q.order,
                                    role='INTERVIEWEE'
                                ).exclude(
                                    question_level='CANDIDATE_QUESTION'  # Exclude candidate questions
                                ).first()
                            
                            # Third try: if still not found, try by conversation_sequence (even sequence = interviewee)
                            if not missed_interviewee and ai_q.conversation_sequence is not None:
                                # Interviewee responses have even conversation_sequence (2, 4, 6...)
                                # AI questions have odd conversation_sequence (1, 3, 5...)
                                interviewee_sequence = ai_q.conversation_sequence + 1
                                missed_interviewee = InterviewQuestion.objects.filter(
                                    session=session,
                                    conversation_sequence=interviewee_sequence,
                                    role='INTERVIEWEE'
                                ).first()
                            
                            if missed_interviewee:
                                answer_text = missed_interviewee.transcribed_answer or ''
                                if answer_text.strip().startswith('A:'):
                                    answer_text = answer_text.replace('A:', '').strip()
                                created_at = missed_interviewee.session.created_at if hasattr(missed_interviewee.session, 'created_at') else None
                                response_time = missed_interviewee.response_time_seconds or 0
                                print(f"✅ Found missed interviewee response for order {ai_q.order} (sequence {missed_interviewee.conversation_sequence}): {answer_text[:50] if answer_text else 'No answer'}...")
                        except Exception as e:
                            print(f"⚠️ Error looking for missed interviewee response: {e}")
                            import traceback
                            traceback.print_exc()
                    
                    # Method 3: Final fallback - use transcribed_answer from the AI question record itself
                    if not answer_text or (answer_text and answer_text.strip() == ''):
                        if ai_q.transcribed_answer is not None and ai_q.transcribed_answer.strip():
                            answer_text = ai_q.transcribed_answer
                            if answer_text.strip().startswith('A:'):
                                answer_text = answer_text.replace('A:', '').strip()
                            if answer_text == "None" or answer_text.lower() == "none":
                                answer_text = ''
                            print(f"✅ Using transcribed_answer from AI question record for order {ai_q.order}: {answer_text[:50] if answer_text else 'No answer'}...")
                        else:
                            # Ultimate fallback: no answer available
                            answer_text = ''
                            print(f"⚠️ No answer found for order {ai_q.order}, question ID {ai_q.id}")
                    
                    # Set created_at and response_time if not already set
                    if created_at is None:
                        created_at = ai_q.session.created_at if hasattr(ai_q.session, 'created_at') else None
                    if response_time == 0:
                        response_time = ai_q.response_time_seconds or 0
                    
                    # Format the answer - ensure we always have something to display
                    if answer_text is None:
                        answer_text = 'No answer provided'
                    elif isinstance(answer_text, str):
                        stripped = answer_text.strip()
                        if stripped == '' or stripped.lower() == 'none':
                            answer_text = 'No answer provided'
                        # Remove any "A:" prefix that might be left
                        if answer_text.startswith('A:'):
                            answer_text = answer_text[2:].strip()
                    
                    # CRITICAL: If answer_text is still empty after all fallbacks, log a warning
                    if not answer_text or answer_text.strip() == '':
                        print(f"⚠️ WARNING: No answer found for question order {ai_q.order}, ID {ai_q.id}, question: {ai_q.question_text[:50]}...")
                        print(f"   - AI question transcribed_answer: {ai_q.transcribed_answer[:50] if ai_q.transcribed_answer else '(NULL)'}")
                        print(f"   - Interviewee record exists: {bool(interviewee_a)}")
                        if interviewee_a:
                            print(f"   - Interviewee transcribed_answer: {interviewee_a.transcribed_answer[:50] if interviewee_a.transcribed_answer else '(NULL)'}")
                        answer_text = 'No answer provided'  # Final fallback
                
                # Create Q&A item in old format (question_text and answer together)
                # IMPORTANT: Preserve the original question_type from database (not the uppercased version)
                original_question_type = ai_q.question_type or 'TECHNICAL'
                
                # Get conversation_sequence and order for proper ordering
                conversation_seq = ai_q.conversation_sequence if hasattr(ai_q, 'conversation_sequence') and ai_q.conversation_sequence is not None else None
                order_value = ai_q.order if hasattr(ai_q, 'order') else order_key
                
                qa_item = {
                    'id': str(ai_q.id),
                    'order': order_value,
                    'conversation_sequence': conversation_seq,  # Add conversation_sequence for proper ordering
                    'question_text': question_text,
                    'question_type': original_question_type,  # Use original case from database
                    'answer': answer_text,
                    'response_time': response_time if (question_type != 'CODING' and question_type != 'CODING CHALLENGE') else (interviewee_a.response_time_seconds if interviewee_a else 0),
                    'answered_at': created_at,
                    'question_level': ai_q.question_level or 'MAIN',
                    # Add role information for sequential display (like PDF)
                    'role': 'interviewer',  # AI questions are from interviewer
                    'text': question_text,  # For sequential format compatibility
                }
                
                # For CODING questions, also include code submission metadata
                if question_type == 'CODING':
                    try:
                        code_submission = CodeSubmission.objects.filter(
                            session=session,
                            question_id=str(ai_q.id)
                        ).order_by('-created_at').first()
                        
                        if code_submission:
                            qa_item['code_submission'] = {
                                'id': str(code_submission.id),
                                'passed_all_tests': code_submission.passed_all_tests,
                                'language': code_submission.language,
                                'output_log': code_submission.output_log,
                                'created_at': code_submission.created_at.isoformat() if code_submission.created_at else None,
                            }
                            # Also add is_correct flag based on test results
                            qa_item['is_correct'] = code_submission.passed_all_tests
                            print(f"✅ Added code_submission metadata to CODING Q&A item: ID {ai_q.id}, Passed: {code_submission.passed_all_tests}")
                    except Exception as e:
                        print(f"⚠️ Error adding code_submission metadata: {e}")
                
                qa_list.append(qa_item)
                
                # Debug: Log coding questions being added
                if question_type == 'CODING' or question_type == 'CODING CHALLENGE':
                    print(f"✅ Added CODING Q&A item: Order {order_key}, ID {ai_q.id}, Type: {original_question_type}, Has Answer: {bool(answer_text and answer_text != 'No code submitted')}")
            
            # Now process CODING questions separately and add them to qa_list
            # This ensures they're included even if they share the same order as TECHNICAL questions
            print(f"🔍 Processing {len(coding_questions_list)} CODING questions separately...")
            for coding_q in coding_questions_list:
                order_key = coding_q.order
                original_question_type = coding_q.question_type or 'CODING'
                question_type = original_question_type.upper()
                
                # Get question text
                question_text = coding_q.question_text or ''
                if question_text.strip().startswith('Q:'):
                    question_text = question_text.replace('Q:', '').strip()
                
                # Get answer from CodeSubmission
                answer_text = None
                created_at = None
                response_time = 0
                try:
                    print(f"🔍 Looking for CodeSubmission for CODING question ID: {coding_q.id} (as string: {str(coding_q.id)}, UUID: {coding_q.id})")
                    
                    # Try multiple ways to find the CodeSubmission
                    question_id_str = str(coding_q.id)
                    code_submission = CodeSubmission.objects.filter(
                        session=session,
                        question_id=question_id_str
                    ).order_by('-created_at').first()
                    
                    # Also try without hyphens (in case UUID is stored differently)
                    if not code_submission:
                        question_id_no_hyphens = question_id_str.replace('-', '')
                        code_submission = CodeSubmission.objects.filter(
                            session=session,
                            question_id=question_id_no_hyphens
                        ).order_by('-created_at').first()
                    
                    if code_submission:
                        print(f"✅ Found CodeSubmission by exact match: ID {code_submission.id}, Question ID: {code_submission.question_id}")
                    else:
                        # Second: try by session only (get the most recent one)
                        print(f"⚠️ No exact match found, trying by session only...")
                        code_submission = CodeSubmission.objects.filter(
                            session=session
                        ).order_by('-created_at').first()
                        
                        if code_submission:
                            print(f"✅ Found CodeSubmission by session: ID {code_submission.id}, Question ID: {code_submission.question_id} (expected: {question_id_str})")
                        else:
                            # Third: try any CodeSubmission for this question ID (across all sessions)
                            print(f"⚠️ No match by session, trying by question_id only...")
                            code_submission = CodeSubmission.objects.filter(
                                question_id=question_id_str
                            ).order_by('-created_at').first()
                            
                            if code_submission:
                                print(f"✅ Found CodeSubmission by question_id only: ID {code_submission.id}")
                    
                    if code_submission and code_submission.submitted_code:
                        answer_text = code_submission.submitted_code
                        created_at = code_submission.created_at
                        print(f"✅ Using CodeSubmission answer: {len(answer_text)} characters")
                    else:
                        # Check if there's a transcribed_answer as fallback
                        if coding_q.transcribed_answer:
                            transcribed = coding_q.transcribed_answer
                            # Check if transcribed_answer contains "Submitted Code:" - extract the code part
                            if "Submitted Code:" in transcribed:
                                code_start = transcribed.find("Submitted Code:") + len("Submitted Code:")
                                answer_text = transcribed[code_start:].strip()
                                print(f"⚠️ No CodeSubmission found, extracted code from transcribed_answer: {len(answer_text)} characters")
                            else:
                                answer_text = transcribed
                                if answer_text.strip().startswith('A:'):
                                    answer_text = answer_text.replace('A:', '').strip()
                                print(f"⚠️ No CodeSubmission found, using transcribed_answer: {len(answer_text)} characters")
                        else:
                            answer_text = 'No code submitted'
                            print(f"⚠️ No CodeSubmission and no transcribed_answer, using 'No code submitted'")
                        created_at = coding_q.session.created_at if hasattr(coding_q.session, 'created_at') else None
                except Exception as e:
                    print(f"⚠️ Error fetching CodeSubmission for question {coding_q.id}: {e}")
                    import traceback
                    traceback.print_exc()
                    # Fallback to transcribed_answer if available
                    if coding_q.transcribed_answer:
                        transcribed = coding_q.transcribed_answer
                        if "Submitted Code:" in transcribed:
                            code_start = transcribed.find("Submitted Code:") + len("Submitted Code:")
                            answer_text = transcribed[code_start:].strip()
                        else:
                            answer_text = transcribed
                            if answer_text.strip().startswith('A:'):
                                answer_text = answer_text.replace('A:', '').strip()
                    else:
                        answer_text = 'No code submitted'
                    created_at = coding_q.session.created_at if hasattr(coding_q.session, 'created_at') else None
                
                # Create Q&A item for CODING question
                # Get conversation_sequence for proper ordering
                conversation_seq = coding_q.conversation_sequence if hasattr(coding_q, 'conversation_sequence') and coding_q.conversation_sequence is not None else None
                
                qa_item = {
                    'id': str(coding_q.id),
                    'order': order_key,
                    'conversation_sequence': conversation_seq,  # Add conversation_sequence for proper ordering
                    'question_text': question_text,
                    'question_type': original_question_type,
                    'answer': answer_text,
                    'response_time': 0,
                    'answered_at': created_at,
                    'question_level': coding_q.question_level or 'MAIN',
                }
                
                # Add code submission metadata
                try:
                    if code_submission:
                        qa_item['code_submission'] = {
                            'id': str(code_submission.id),
                            'passed_all_tests': code_submission.passed_all_tests,
                            'language': code_submission.language,
                            'output_log': code_submission.output_log,
                            'created_at': code_submission.created_at.isoformat() if code_submission.created_at else None,
                        }
                        qa_item['is_correct'] = code_submission.passed_all_tests
                        print(f"✅ Added code_submission metadata to CODING Q&A item: ID {coding_q.id}, Passed: {code_submission.passed_all_tests}")
                except Exception as e:
                    print(f"⚠️ Error adding code_submission metadata: {e}")
                
                qa_list.append(qa_item)
                print(f"✅ Added CODING Q&A item to list: Order {order_key}, ID {coding_q.id}, Has Answer: {bool(answer_text and answer_text != 'No code submitted')}")
            
            # Sort by conversation_sequence first (if available), then by order, then by id
            # This ensures proper sequential ordering of questions
            qa_list.sort(key=lambda x: (
                x.get('conversation_sequence') if x.get('conversation_sequence') is not None else 999999,  # Use conversation_sequence if available
                x.get('order', 0),  # Fallback to order
                x.get('id', '')  # Final fallback to id
            ))
            
            # CRITICAL: Also create a sequential conversation format (like PDF) for proper script display
            # This ensures all conversation turns are shown in order, matching the PDF format
            sequential_conversation = []
            
            # Get all questions in sequential order (by conversation_sequence)
            all_sequential_questions = InterviewQuestion.objects.filter(
                session=session
            ).exclude(
                # Exclude CODING questions from sequential conversation (they're handled separately)
                question_type='CODING'
            ).order_by(
                'conversation_sequence',
                'order',
                'id'
            )
            
            # Build sequential conversation list
            for q in all_sequential_questions:
                # Skip empty records
                if not q.question_text and not q.transcribed_answer:
                    continue
                
                # Determine role based on question record
                if q.role and q.role.upper() == 'AI':
                    # AI/Interviewer message
                    text = q.question_text or ''
                    if text.strip():
                        sequential_conversation.append({
                            'role': 'interviewer',
                            'text': text,
                            'conversation_sequence': q.conversation_sequence,
                            'order': q.order,
                            'question_level': q.question_level or 'MAIN',
                            'question_type': q.question_type or 'TECHNICAL'
                        })
                
                if q.role and q.role.upper() == 'INTERVIEWEE':
                    # Candidate message
                    text = q.transcribed_answer or ''
                    if text.strip():
                        # Remove A: prefix if present
                        if text.strip().startswith('A:'):
                            text = text.replace('A:', '').strip()
                        if text.strip():
                            sequential_conversation.append({
                                'role': 'candidate',
                                'text': text,
                                'conversation_sequence': q.conversation_sequence,
                                'order': q.order,
                                'question_level': q.question_level or 'INTERVIEWEE_RESPONSE',
                                'question_type': q.question_type or 'TECHNICAL'
                            })
                elif not q.role and q.question_text:
                    # Old format - question_text exists, treat as AI
                    text = q.question_text or ''
                    if text.strip():
                        sequential_conversation.append({
                            'role': 'interviewer',
                            'text': text,
                            'conversation_sequence': q.conversation_sequence,
                            'order': q.order,
                            'question_level': q.question_level or 'MAIN',
                            'question_type': q.question_type or 'TECHNICAL'
                        })
                    # Also add answer if exists
                    if q.transcribed_answer:
                        text = q.transcribed_answer
                        if text.strip().startswith('A:'):
                            text = text.replace('A:', '').strip()
                        if text.strip():
                            sequential_conversation.append({
                                'role': 'candidate',
                                'text': text,
                                'conversation_sequence': (q.conversation_sequence or 0) + 1,  # Candidate comes after AI
                                'order': q.order,
                                'question_level': 'INTERVIEWEE_RESPONSE',
                                'question_type': q.question_type or 'TECHNICAL'
                            })
            
            # Sort sequential conversation by conversation_sequence
            sequential_conversation.sort(key=lambda x: (
                x.get('conversation_sequence') if x.get('conversation_sequence') is not None else 999999,
                x.get('order', 0),
            ))
            
            print(f"✅ Returning {len(qa_list)} Q&A items for interview {obj.id} in sequential order")
            print(f"✅ Also created {len(sequential_conversation)} sequential conversation items (like PDF format)")
            
            # Debug: Print final Q&A list with conversation_sequence for ordering verification
            coding_count = 0
            technical_count = 0
            for idx, qa in enumerate(qa_list):
                q_preview = qa.get('question_text', '')[:50] if qa.get('question_text') else 'None'
                a_preview = qa.get('answer', '')[:50] if qa.get('answer') else 'None'
                q_type = qa.get('question_type', 'UNKNOWN')
                order = qa.get('order', 'N/A')
                conv_seq = qa.get('conversation_sequence', 'N/A')
                print(f"   [{idx+1}] ConvSeq={conv_seq}, Order={order}: Type={q_type}, Q: {q_preview}... | A: {a_preview}...")
                if (q_type or '').upper() == 'CODING':
                    coding_count += 1
                    print(f"      ⭐ CODING question found! ID: {qa.get('id')}, Has Answer: {bool(qa.get('answer') and qa.get('answer') != 'No code submitted')}")
                else:
                    technical_count += 1
            print(f"📊 Summary: {coding_count} CODING questions, {technical_count} TECHNICAL/BEHAVIORAL questions")
            
            # Store sequential_conversation separately for frontend use
            # This allows frontend to display the complete conversation script like PDF
            # We'll add it as metadata to the first item for easy access
            if qa_list:
                qa_list[0]['_sequential_conversation'] = sequential_conversation
            
            if coding_count == 0:
                print(f"⚠️ WARNING: No CODING questions found in Q&A list! Check if coding questions exist in database.")
                # Debug: Check if any coding questions exist in the database
                coding_in_db = InterviewQuestion.objects.filter(session=session, question_type='CODING').count()
                print(f"   Database check: {coding_in_db} CODING questions found in InterviewQuestion table")
                if coding_in_db > 0:
                    db_coding = InterviewQuestion.objects.filter(session=session, question_type='CODING')
                    for db_q in db_coding:
                        print(f"      DB CODING Q: Order {db_q.order}, ID {db_q.id}, Text: {db_q.question_text[:50]}...")
            return qa_list
        except Exception as e:
            print(f"⚠️ Error getting Q&A for interview {obj.id}: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_verification_id_image(self, obj):
        """Get verification ID image URL from InterviewSession if verification was successful"""
        try:
            from interview_app.models import InterviewSession
            from django.conf import settings
            
            # Find the session for this interview using session_key
            session = None
            if obj.session_key:
                try:
                    session = InterviewSession.objects.get(session_key=obj.session_key)
                except InterviewSession.DoesNotExist:
                    pass
            
            # If not found by session_key, try to find by candidate and recent date
            if not session and obj.candidate:
                try:
                    sessions = InterviewSession.objects.filter(
                        candidate_email=obj.candidate.email
                    ).order_by('-created_at')
                    
                    # If interview has a created_at, try to match by date proximity
                    if obj.created_at:
                        from datetime import timedelta
                        time_window_start = obj.created_at - timedelta(hours=1)
                        time_window_end = obj.created_at + timedelta(hours=1)
                        sessions = sessions.filter(
                            created_at__gte=time_window_start,
                            created_at__lte=time_window_end
                        )
                    
                    session = sessions.first()
                except Exception:
                    pass
            
            # If still not found, try to find by interview round and candidate
            if not session and obj.candidate and obj.interview_round:
                try:
                    session = InterviewSession.objects.filter(
                        candidate_email=obj.candidate.email
                    ).order_by('-created_at').first()
                except Exception:
                    pass
            
            # Return image URL if session exists, has id_card_image, and verification was successful
            if session and session.id_card_image and session.id_verification_status == 'Verified':
                if session.id_card_image:
                    request = self.context.get('request')
                    if request:
                        return request.build_absolute_uri(session.id_card_image.url)
                    else:
                        # Fallback: construct URL manually
                        media_url = settings.MEDIA_URL.rstrip('/')
                        image_url = session.id_card_image.url.lstrip('/')
                        return f"{media_url}/{image_url}"
            
            return None
        except Exception as e:
            print(f"⚠️ Error getting verification ID image for interview {obj.id}: {e}")
            return None
    
    def get_interview_video(self, obj):
        """Get interview video URL from InterviewSession if available"""
        try:
            from interview_app.models import InterviewSession
            from django.conf import settings
            
            # Find the session for this interview using session_key
            session = None
            if obj.session_key:
                try:
                    session = InterviewSession.objects.get(session_key=obj.session_key)
                except InterviewSession.DoesNotExist:
                    pass
            
            # If not found by session_key, try to find by candidate and recent date
            if not session and obj.candidate:
                try:
                    sessions = InterviewSession.objects.filter(
                        candidate_email=obj.candidate.email
                    ).order_by('-created_at')
                    
                    if obj.created_at:
                        from datetime import timedelta
                        time_window_start = obj.created_at - timedelta(hours=1)
                        time_window_end = obj.created_at + timedelta(hours=1)
                        sessions = sessions.filter(
                            created_at__gte=time_window_start,
                            created_at__lte=time_window_end
                        )
                    
                    session = sessions.first()
                except Exception:
                    pass
            
            # Return video URL if session exists and has video
            if session and session.interview_video:
                # Verify the video file actually exists and is a merged video
                try:
                    video_file_path = session.interview_video.path
                    video_path_str = str(session.interview_video)
                    
                    # CRITICAL: Only return merged videos (from interview_videos_merged/ or with _with_audio suffix)
                    is_merged = 'interview_videos_merged' in video_path_str or '_with_audio' in video_path_str
                    
                    if not is_merged:
                        print(f"⚠️ Video in database is not merged: {video_path_str}")
                        print(f"   Searching for merged version in interview_videos_merged/...")
                        
                        # Try to find merged version in interview_videos_merged/ folder
                        merged_video_dir = os.path.join(settings.MEDIA_ROOT, 'interview_videos_merged')
                        if os.path.exists(merged_video_dir):
                            # Extract base filename from video path
                            video_basename = os.path.basename(video_file_path)
                            base_name = os.path.splitext(video_basename)[0]
                            # Remove any suffixes like _converted
                            if '_converted' in base_name:
                                base_name = base_name.replace('_converted', '')
                            
                            # Look for merged video
                            merged_filename = f"{base_name}_with_audio.mp4"
                            merged_path = os.path.join(merged_video_dir, merged_filename)
                            
                            if os.path.exists(merged_path):
                                print(f"✅ Found merged video: {merged_path}")
                                video_file_path = merged_path
                                # Update the path string for URL construction
                                video_path_str = os.path.relpath(merged_path, settings.MEDIA_ROOT).replace('\\', '/')
                                is_merged = True
                            else:
                                # Try to find any video with session_id in merged folder
                                session_id_str = str(session.id)
                                for filename in os.listdir(merged_video_dir):
                                    if filename.startswith(session_id_str) and filename.endswith('.mp4'):
                                        if '_with_audio' in filename or 'interview_videos_merged' in filename:
                                            merged_path = os.path.join(merged_video_dir, filename)
                                            if os.path.exists(merged_path):
                                                print(f"✅ Found merged video by session_id: {merged_path}")
                                                video_file_path = merged_path
                                                video_path_str = os.path.relpath(merged_path, settings.MEDIA_ROOT).replace('\\', '/')
                                                is_merged = True
                                                break
                    
                    if not is_merged:
                        print(f"❌ No merged video found for session {session.id}")
                        print(f"   Only merged videos (from interview_videos_merged/) should be shown in candidate details")
                        return None
                    
                    if not os.path.exists(video_file_path):
                        print(f"⚠️ Merged video file does not exist at path: {video_file_path}")
                        return None
                    if os.path.getsize(video_file_path) == 0:
                        print(f"⚠️ Merged video file is empty: {video_file_path}")
                        return None
                    
                    print(f"✅ Verified merged video exists: {video_file_path}")
                    print(f"   File size: {os.path.getsize(video_file_path) / 1024 / 1024:.2f} MB")
                    
                except Exception as e:
                    print(f"⚠️ Error checking merged video file: {e}")
                    import traceback
                    traceback.print_exc()
                    return None
                
                # Construct URL for merged video
                request = self.context.get('request')
                if request:
                    # Build URL from the merged video path
                    if video_path_str.startswith('interview_videos_merged/'):
                        video_url = f"/media/{video_path_str}"
                    elif video_path_str.startswith('/media/'):
                        video_url = video_path_str
                    else:
                        video_url = f"/media/{video_path_str}"
                    
                    absolute_url = request.build_absolute_uri(video_url)
                    print(f"✅ Returning merged video URL: {absolute_url}")
                    print(f"   Video file path: {video_file_path}")
                    return absolute_url
                else:
                    # Fallback: return relative URL that frontend can handle
                    if video_path_str.startswith('interview_videos_merged/'):
                        video_url = f"/media/{video_path_str}"
                    elif video_path_str.startswith('/media/'):
                        video_url = video_path_str
                    else:
                        video_url = f"/media/{video_path_str}"
                    
                    print(f"✅ Returning merged video URL (fallback, relative): {video_url}")
                    print(f"   Video file path: {video_file_path}")
                    return video_url
            
            return None
        except Exception as e:
            print(f"⚠️ Error getting interview video for interview {obj.id}: {e}")
            return None


class InterviewFeedbackSerializer(serializers.ModelSerializer):
    """
    Serializer for updating interview feedback
    """

    class Meta:
        model = Interview
        fields = ["interview_round", "feedback"]


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
            "interview_date",
            "start_time",
            "end_time",
            "duration_minutes",
            "ai_interview_type",
            "ai_configuration",
            "company",
            "company_name",
            "job",
            "job_title",
            "is_recurring",
            "recurring_pattern",
            "notes",
            "max_candidates",
            "current_bookings",
            "is_available",
            "available_spots",
            "full_start_datetime",
            "full_end_datetime",
            "legacy_start_datetime",
            "legacy_end_datetime",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "is_available",
            "available_spots",
            "full_start_datetime",
            "full_end_datetime",
        ]

    def get_available_spots(self, obj):
        return max(0, obj.max_candidates - obj.current_bookings)

    def get_full_start_datetime(self, obj):
        """Return combined datetime for frontend compatibility"""
        return obj.get_full_start_datetime()

    def get_full_end_datetime(self, obj):
        """Return combined datetime for frontend compatibility"""
        return obj.get_full_end_datetime()

    def validate(self, data):
        if data.get("start_time") and data.get("end_time"):
            if data["start_time"] >= data["end_time"]:
                raise serializers.ValidationError("End time must be after start time")

        return data


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
            "booked_at",
            "confirmed_at",
            "cancelled_at",
            "cancellation_reason",
            "cancelled_by",
            "interview_details",
            "slot_details",
            "ai_interview_type",
            "candidate_name",
        ]
        read_only_fields = [
            "id",
            "booked_at",
            "confirmed_at",
            "cancelled_at",
            "cancelled_by",
        ]

    def get_interview_details(self, obj):
        return {
            "id": obj.interview.id,
            "candidate_name": obj.interview.candidate.full_name,
            "status": obj.interview.status,
            "started_at": obj.interview.started_at,
            "ended_at": obj.interview.ended_at,
        }

    def get_slot_details(self, obj):
        return {
            "id": obj.slot.id,
            "ai_interview_type": obj.slot.ai_interview_type,
            "start_time": obj.slot.start_time,
            "end_time": obj.slot.end_time,
            "duration_minutes": obj.slot.duration_minutes,
            "company_name": obj.slot.company.name,
        }

    def validate(self, data):
        # Check if slot is available
        if "slot" in data:
            slot = data["slot"]
            if not slot.is_available():
                raise serializers.ValidationError(
                    "Selected slot is not available for booking"
                )

            # Check if interview is already scheduled
            if "interview" in data:
                interview = data["interview"]
                if hasattr(interview, "schedule") and interview.schedule:
                    raise serializers.ValidationError("Interview is already scheduled")

        return data


class AIInterviewConfigurationSerializer(serializers.ModelSerializer):
    """
    Serializer for AI interview configuration patterns
    """

    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = AIInterviewConfiguration
        fields = [
            "id",
            "company",
            "company_name",
            "interview_type",
            "day_of_week",
            "start_time",
            "end_time",
            "slot_duration",
            "break_duration",
            "ai_settings",
            "valid_from",
            "valid_until",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, data):
        if data.get("start_time") and data.get("end_time"):
            if data["start_time"] >= data["end_time"]:
                raise serializers.ValidationError("End time must be after start time")
        return data


class InterviewConflictSerializer(serializers.ModelSerializer):
    """
    Serializer for interview conflicts
    """

    primary_interview_details = serializers.SerializerMethodField()
    conflicting_interview_details = serializers.SerializerMethodField()
    resolved_by_name = serializers.CharField(
        source="resolved_by.full_name", read_only=True
    )

    class Meta:
        model = InterviewConflict
        fields = [
            "id",
            "conflict_type",
            "resolution",
            "primary_interview",
            "conflicting_interview",
            "conflict_details",
            "resolution_notes",
            "detected_at",
            "resolved_at",
            "resolved_by",
            "primary_interview_details",
            "conflicting_interview_details",
            "resolved_by_name",
        ]
        read_only_fields = ["id", "detected_at", "resolved_at", "resolved_by"]

    def get_primary_interview_details(self, obj):
        return {
            "id": obj.primary_interview.id,
            "candidate_name": obj.primary_interview.candidate.full_name,
            "status": obj.primary_interview.status,
            "started_at": obj.primary_interview.started_at,
            "ended_at": obj.primary_interview.ended_at,
        }

    def get_conflicting_interview_details(self, obj):
        if obj.conflicting_interview:
            return {
                "id": obj.conflicting_interview.id,
                "candidate_name": obj.conflicting_interview.candidate.full_name,
                "status": obj.conflicting_interview.status,
                "started_at": obj.conflicting_interview.started_at,
                "ended_at": obj.conflicting_interview.ended_at,
            }
        return None


class SlotBookingSerializer(serializers.Serializer):
    """
    Serializer for booking a slot for an interview
    """

    interview_id = serializers.UUIDField()
    slot_id = serializers.UUIDField()
    booking_notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        from .models import Interview, InterviewSlot

        # Validate interview exists
        try:
            interview = Interview.objects.get(id=data["interview_id"])
            data["interview"] = interview
        except Interview.DoesNotExist:
            raise serializers.ValidationError("Interview not found")

        # Validate slot exists and is available
        try:
            slot = InterviewSlot.objects.get(id=data["slot_id"])
            data["slot"] = slot
        except InterviewSlot.DoesNotExist:
            raise serializers.ValidationError("Slot not found")

        if not slot.is_available():
            raise serializers.ValidationError("Slot is not available for booking")

        # Check if interview is already scheduled
        if hasattr(interview, "schedule") and interview.schedule:
            raise serializers.ValidationError("Interview is already scheduled")

        return data


class SlotSearchSerializer(serializers.Serializer):
    """
    Serializer for searching available slots
    """

    company_id = serializers.IntegerField(required=False)
    ai_interview_type = serializers.CharField(required=False)
    job_id = serializers.IntegerField(required=False)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    start_time = serializers.TimeField(required=False)
    end_time = serializers.TimeField(required=False)
    duration_minutes = serializers.IntegerField(required=False, default=60)

    def validate(self, data):
        if data["start_date"] > data["end_date"]:
            raise serializers.ValidationError(
                "Start date must be before or equal to end date"
            )
        return data


class RecurringSlotSerializer(serializers.Serializer):
    """
    Serializer for creating recurring slots
    """

    company_id = serializers.IntegerField()
    ai_interview_type = serializers.CharField(default="general")
    job_id = serializers.IntegerField(required=False)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    days_of_week = serializers.ListField(
        child=serializers.IntegerField(min_value=1, max_value=7), min_length=1
    )
    slot_duration = serializers.IntegerField(default=60, min_value=15, max_value=480)
    break_duration = serializers.IntegerField(default=15, min_value=0, max_value=60)
    max_candidates_per_slot = serializers.IntegerField(
        default=1, min_value=1, max_value=10
    )
    ai_configuration = serializers.JSONField(required=False, default=dict)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if data["start_date"] > data["end_date"]:
            raise serializers.ValidationError(
                "Start date must be before or equal to end date"
            )
        if data["start_time"] >= data["end_time"]:
            raise serializers.ValidationError("End time must be after start time")
        return data
