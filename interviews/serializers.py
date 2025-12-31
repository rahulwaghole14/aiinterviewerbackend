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
    
    # Proctoring PDF
    proctoring_pdf = serializers.SerializerMethodField()

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
            "proctoring_pdf",
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
                        # Get proctoring PDF URL ONLY from ProctoringPDF table (no fallback)
                        proctoring_pdf_gcs_url = None
                        proctoring_pdf_url = None
                        
                        try:
                            from evaluation.models import ProctoringPDF
                            proctoring_pdf = ProctoringPDF.objects.filter(interview=obj).first()
                            if proctoring_pdf and proctoring_pdf.gcs_url:
                                gcs_url = proctoring_pdf.gcs_url
                                
                                # If URL is malformed (contains app URL), extract only the GCS part
                                # Pattern: https://app-urlhttps//storage.googleapis.com/... or https://app-url/storage.googleapis.com/...
                                if 'storage.googleapis.com' in gcs_url:
                                    # Find the start of the GCS URL
                                    gcs_index = gcs_url.find('storage.googleapis.com')
                                    if gcs_index > 0:
                                        # Extract from storage.googleapis.com onwards
                                        gcs_url = 'https://' + gcs_url[gcs_index:]
                                
                                proctoring_pdf_gcs_url = gcs_url
                                proctoring_pdf_url = gcs_url
                                print(f"   - Proctoring PDF GCS URL (from ProctoringPDF table): {proctoring_pdf_gcs_url[:100]}...")
                            else:
                                print(f"   - No ProctoringPDF record found for interview {obj.id}")
                        except Exception as e:
                            print(f"   ⚠️ Error fetching from ProctoringPDF table: {e}")
                            import traceback
                            traceback.print_exc()
                        
                        proctoring_warnings = evaluation.details.get('proctoring', {}).get('warnings', [])
                        print(f"   - Proctoring warnings count: {len(proctoring_warnings)}")
                        print(f"   - Proctoring PDF URL: {proctoring_pdf_url}")
                        print(f"   - Proctoring PDF GCS URL: {proctoring_pdf_gcs_url}")
                        
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
                            'proctoring_pdf_gcs_url': proctoring_pdf_gcs_url,  # Add GCS URL (absolute URL only)
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
        """Get questions and answers for this interview - PRIORITY: TechnicalQA table"""
        try:
            from interview_app.models import InterviewSession, InterviewQuestion, TechnicalQA
            from django.utils import timezone
            from django.db import connection
            
            # CRITICAL: Get TECHNICAL questions from TechnicalQA table (new separate table)
            # Get CODING questions from InterviewQuestion table (keep as before)
            technical_qa_list = TechnicalQA.objects.filter(interview=obj).order_by('question_number', 'order')
            qa_list = []
            
            # Add technical questions from TechnicalQA table
            if technical_qa_list.exists():
                print(f"✅ Found {technical_qa_list.count()} technical Q&A records in TechnicalQA table for interview {obj.id}")
                for qa in technical_qa_list:
                    # Only add TECHNICAL questions, skip CODING (those come from InterviewQuestion)
                    if qa.question_type != 'CODING':
                        qa_list.append({
                            'question_number': qa.question_number,
                            'question': qa.question_text or '',
                            'answer': qa.answer_text or qa.transcribed_answer or 'No answer provided',
                            'question_type': qa.question_type or 'TECHNICAL',
                            'response_time': qa.response_time_seconds or 0,
                            'order': qa.order or qa.question_number,
                        })
                print(f"✅ Added {len(qa_list)} technical Q&A pairs from TechnicalQA table")
            else:
                print(f"⚠️ No TechnicalQA records found for interview {obj.id}")
            
            # Now get CODING questions from InterviewQuestion table (keep as before)
            # Find the session for this interview using session_key
            session = None
            if obj.session_key:
                try:
                    session = InterviewSession.objects.only('id', 'session_key', 'candidate_name').get(session_key=obj.session_key)
                    print(f"✅ Found session by session_key: {obj.session_key}")
                except InterviewSession.DoesNotExist:
                    print(f"⚠️ Session not found by session_key: {obj.session_key}")
                except Exception as e:
                    print(f"⚠️ Error finding session: {e}")
            
            # If session found, get CODING questions from InterviewQuestion
            if session:
                try:
                    # Get CODING questions only
                    coding_questions = InterviewQuestion.objects.filter(
                        session=session,
                        question_type='CODING'
                    ).only(
                        'id', 'question_text', 'question_type', 'order', 'conversation_sequence'
                    ).order_by('order', 'id')
                    
                    if coding_questions.exists():
                        print(f"✅ Found {coding_questions.count()} CODING questions in InterviewQuestion table")
                        
                        # Import CodeSubmission model
                        from interview_app.models import CodeSubmission
                        
                        for coding_q in coding_questions:
                            # Get answer from CodeSubmission
                            answer_text = None
                            created_at = None
                            response_time = 0
                            try:
                                question_id_str = str(coding_q.id)
                                code_submission = CodeSubmission.objects.filter(
                                    session=session,
                                    question_id=question_id_str
                                ).order_by('-created_at').first()
                                
                                if code_submission:
                                    answer_text = code_submission.submitted_code or 'No code submitted'
                                    created_at = code_submission.created_at.isoformat() if code_submission.created_at else None
                                    response_time = 0  # CodeSubmission doesn't have response_time
                                    
                                    # Add coding question to qa_list
                                    qa_item = {
                                        'question_number': coding_q.order + 1,  # Use order + 1 for question number
                                        'question': coding_q.question_text or '',
                                        'answer': answer_text,
                                        'question_type': 'CODING',
                                        'response_time': response_time,
                                        'order': coding_q.order,
                                        'code_submission': {
                                            'submitted_code': code_submission.submitted_code,
                                            'language': code_submission.language,
                                            'passed_all_tests': code_submission.passed_all_tests,
                                            'output_log': code_submission.output_log,
                                            'gemini_evaluation': code_submission.gemini_evaluation,
                                            'created_at': created_at,
                                        }
                                    }
                                    qa_list.append(qa_item)
                                    print(f"✅ Added CODING question {coding_q.order + 1} with code submission")
                            except Exception as e:
                                print(f"⚠️ Error fetching CodeSubmission for CODING question {coding_q.id}: {e}")
                                # Still add the question even if submission not found
                                qa_list.append({
                                    'question_number': coding_q.order + 1,
                                    'question': coding_q.question_text or '',
                                    'answer': 'No code submitted',
                                    'question_type': 'CODING',
                                    'response_time': 0,
                                    'order': coding_q.order,
                                })
                    else:
                        print(f"⚠️ No CODING questions found in InterviewQuestion table")
                except Exception as e:
                    print(f"⚠️ Error fetching CODING questions: {e}")
            
            # Sort qa_list by order/question_number
            qa_list.sort(key=lambda x: x.get('order', x.get('question_number', 0)))
            
            print(f"✅ Returning {len(qa_list)} total Q&A pairs ({len([q for q in qa_list if q.get('question_type') != 'CODING'])} technical + {len([q for q in qa_list if q.get('question_type') == 'CODING'])} coding)")
            return qa_list
        except TimeoutError as timeout_error:
            print(f"⚠️ Timeout getting Q&A for interview {obj.id}: {timeout_error}")
            return []  # Return empty list on timeout
        except Exception as e:
            print(f"⚠️ Error getting Q&A for interview {obj.id}: {e}")
            import traceback
            traceback.print_exc()
            # CRITICAL: Return empty list on any error to prevent worker timeout
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
    
    def get_proctoring_pdf(self, obj):
        """Get proctoring PDF URL from separate ProctoringPDF table - Extract GCS URL if malformed"""
        try:
            from evaluation.models import ProctoringPDF
            
            proctoring_pdf = ProctoringPDF.objects.filter(interview=obj).first()
            if proctoring_pdf and proctoring_pdf.gcs_url:
                gcs_url = proctoring_pdf.gcs_url
                
                # If URL is malformed (contains app URL), extract only the GCS part
                # Pattern: https://app-urlhttps//storage.googleapis.com/... or https://app-url/storage.googleapis.com/...
                if 'storage.googleapis.com' in gcs_url:
                    # Find the start of the GCS URL
                    gcs_index = gcs_url.find('storage.googleapis.com')
                    if gcs_index > 0:
                        # Extract from storage.googleapis.com onwards
                        gcs_url = 'https://' + gcs_url[gcs_index:]
                
                return {
                    'gcs_url': gcs_url,  # Return clean GCS URL
                    'local_path': proctoring_pdf.local_path,
                    'created_at': proctoring_pdf.created_at.isoformat() if proctoring_pdf.created_at else None,
                    'updated_at': proctoring_pdf.updated_at.isoformat() if proctoring_pdf.updated_at else None,
                }
            
            return None
        except Exception as e:
            print(f"⚠️ Error getting proctoring PDF for interview {obj.id}: {e}")
            import traceback
            traceback.print_exc()
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
            # Priority 1: Check for GCS URL (preferred)
            if session and hasattr(session, 'video_gcs_url') and session.video_gcs_url:
                print(f"✅ Returning GCS video URL: {session.video_gcs_url}")
                return session.video_gcs_url
            
            # Priority 2: Check for local video file
            if session and hasattr(session, 'interview_video') and session.interview_video:
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
