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
                        # Get proctoring PDF URL ONLY from ProctoringPDF table (no fallback)
                        proctoring_pdf_gcs_url = None
                        proctoring_pdf_url = None
                        
                        try:
                            from evaluation.models import ProctoringPDF
                            from django.db import connection

                            print(f"   - Database connection: {connection.vendor} - {connection.alias}")
                            proctoring_pdf_count = ProctoringPDF.objects.count()
                            print(f"   - Total ProctoringPDF records in database: {proctoring_pdf_count}")

                            # Robust fetching with proper error handling
                            try:
                                # Use select_related to optimize the query
                                proctoring_pdf = ProctoringPDF.objects.select_related('interview').filter(interview=obj).first()

                                if proctoring_pdf:
                                    print(f"   - ProctoringPDF record found: ID={proctoring_pdf.id}")
                                    print(f"   - Record belongs to interview: {proctoring_pdf.interview.id}")
                                    print(f"   - GCS_URL present: {'Yes' if proctoring_pdf.gcs_url else 'No'}")
                                    print(f"   - Local_Path present: {'Yes' if proctoring_pdf.local_path else 'No'}")
                                    print(f"   - Created: {proctoring_pdf.created_at}, Updated: {proctoring_pdf.updated_at}")

                                    if proctoring_pdf.gcs_url:
                                        # Get raw URL from database WITHOUT cleaning
                                        raw_gcs_url = str(proctoring_pdf.gcs_url).strip()

                                        # Print the RAW URL as-is from database
                                        print(f"   - RAW Proctoring PDF GCS URL (from ProctoringPDF table): {raw_gcs_url}")
                                        print(f"   - URL length: {len(raw_gcs_url)} characters")
                                        print(f"   - Contains 'run.app': {'run.app' in raw_gcs_url}")
                                        print(f"   - Contains 'storage.googleapis.com': {'storage.googleapis.com' in raw_gcs_url}")
                                        print(f"   - Starts with 'https://storage.googleapis.com': {raw_gcs_url.startswith('https://storage.googleapis.com')}")

                                        # Use raw URL as-is without cleaning
                                        proctoring_pdf_gcs_url = raw_gcs_url
                                        proctoring_pdf_url = raw_gcs_url

                                        print(f"   - Using RAW URL as-is: {proctoring_pdf_gcs_url[:150]}...")
                                    else:
                                        print(f"   - ProctoringPDF record exists but gcs_url is None/empty for interview {obj.id}")
                                        proctoring_pdf_gcs_url = None
                                        proctoring_pdf_url = None
                                else:
                                    print(f"   - No ProctoringPDF record found for interview {obj.id}")
                                    proctoring_pdf_gcs_url = None
                                    proctoring_pdf_url = None

                            except Exception as query_error:
                                print(f"   ⚠️ Database query error for ProctoringPDF: {query_error}")
                                proctoring_pdf_gcs_url = None
                                proctoring_pdf_url = None

                        except Exception as e:
                            print(f"   ⚠️ Error importing/accessing ProctoringPDF model: {e}")
                            import traceback
                            traceback.print_exc()
                            proctoring_pdf_gcs_url = None
                            proctoring_pdf_url = None
                        
                        proctoring_warnings = evaluation.details.get('proctoring', {}).get('warnings', [])
                        print(f"   - Proctoring warnings count: {len(proctoring_warnings)}")
                        print(f"   - Proctoring PDF GCS URL: {proctoring_pdf_gcs_url}")

                        # Note: Removed complex database operations for code submission checking
                        # Only use AI evaluation results as provided

                        # Extract coding score from AI analysis
                        coding_score = ai_analysis.get('coding_score', 0)
                        if isinstance(coding_score, str):
                            # Handle string scores like "8/10"
                            if '/' in coding_score:
                                try:
                                    coding_score = float(coding_score.split('/')[0])
                                except (ValueError, IndexError):
                                    coding_score = 0
                            else:
                                try:
                                    coding_score = float(coding_score)
                                except ValueError:
                                    coding_score = 0

                        # Ensure coding_score is a number
                        if not isinstance(coding_score, (int, float)):
                            coding_score = 0

                        print(f"   - Extracted coding_score: {coding_score} (type: {type(coding_score)})")

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
                            'ai_summary': self._build_ai_summary(ai_analysis, proctoring_pdf_gcs_url),
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
                        print(f"✅ Proctoring PDF URL in result: {proctoring_pdf_gcs_url[:100] if proctoring_pdf_gcs_url else 'None'}...")
                        print(f"✅ AI result keys: {list(result.keys())}")
                        print(f"✅ Has proctoring_pdf_gcs_url: {'proctoring_pdf_gcs_url' in result}")
                        if 'proctoring_pdf_gcs_url' in result:
                            print(f"✅ proctoring_pdf_gcs_url value: {result['proctoring_pdf_gcs_url'][:100] if result['proctoring_pdf_gcs_url'] else 'Empty'}...")
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
    
    def _build_ai_summary(self, ai_analysis, proctoring_pdf_gcs_url=None):
        """Build AI summary from analysis"""
        parts = []
        if ai_analysis.get('technical_analysis'):
            parts.append(f"Technical: {ai_analysis['technical_analysis'][:200]}")
        if ai_analysis.get('coding_analysis'):
            parts.append(f"Coding: {ai_analysis['coding_analysis'][:200]}")
        if ai_analysis.get('behavioral_analysis'):
            parts.append(f"Behavioral: {ai_analysis['behavioral_analysis'][:200]}")

        # Add proctoring PDF URL at the end if available
        if proctoring_pdf_gcs_url:
            parts.append(f"Proctoring PDF: {proctoring_pdf_gcs_url}")

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
        """Get questions and answers for this interview - SAME LOGIC AS PDF GENERATION"""
        try:
            from interview_app.models import InterviewSession, InterviewQuestion, CodeSubmission
            from django.utils import timezone
            from django.db import connection
            
            # Find the session for this interview using session_key (SAME AS PDF)
            session = None
            if obj.session_key:
                try:
                    session = InterviewSession.objects.only('id', 'session_key', 'candidate_name').get(session_key=obj.session_key)
                    print(f"✅ Found session by session_key: {obj.session_key}")
                except InterviewSession.DoesNotExist:
                    print(f"⚠️ Session not found by session_key: {obj.session_key}")
                except Exception as e:
                    print(f"⚠️ Error finding session: {e}")
            
            if not session:
                print(f"⚠️ No session found for interview {obj.id}")
                return []
            
            # Get all questions ordered by conversation_sequence and order (SAME AS PDF)
            questions = InterviewQuestion.objects.filter(
                session=session
            ).order_by(
                'conversation_sequence',
                'order',
                'id'
            )
            
            # Group questions by order to pair AI questions with Interviewee answers (SAME AS PDF)
            questions_by_order = {}
            for q in questions:
                order_key = q.order
                if order_key not in questions_by_order:
                    questions_by_order[order_key] = {'ai': None, 'interviewee': None}
                
                # Check if this is an AI question or Interviewee answer (SAME AS PDF)
                if q.role == 'AI' and q.question_text:
                    questions_by_order[order_key]['ai'] = q
                elif q.role == 'INTERVIEWEE' and (q.transcribed_answer or q.question_level == 'INTERVIEWEE_RESPONSE'):
                    if not questions_by_order[order_key]['interviewee']:
                        questions_by_order[order_key]['interviewee'] = q
                    elif q.transcribed_answer and not questions_by_order[order_key]['interviewee'].transcribed_answer:
                        # Prefer record with transcribed_answer
                        questions_by_order[order_key]['interviewee'] = q
                elif not q.role and q.question_text:
                    # Old format: question_text exists, treat as AI question
                    questions_by_order[order_key]['ai'] = q
            
            # Get coding submissions for coding questions
            coding_submissions = CodeSubmission.objects.filter(session=session).order_by('created_at')
            
            # Sort by order and create Q&A pairs (SAME AS PDF)
            sorted_orders = sorted(questions_by_order.keys())
            qa_list = []
            
            for order_key in sorted_orders:
                q_pair = questions_by_order[order_key]
                ai_q = q_pair['ai']
                interviewee_a = q_pair['interviewee']
                
                # Skip if no AI question
                if not ai_q:
                    continue
                
                # Handle CODING questions differently - get answer from CodeSubmission (SAME AS PDF)
                if ai_q.question_type == 'CODING':
                    # Get question text
                    question_text = ai_q.question_text or ''
                    if question_text.strip().startswith('Q:'):
                        question_text = question_text.replace('Q:', '').strip()
                    
                    # Find corresponding code submission
                    answer_text = 'No code submitted'
                    code_submission_data = None
                    try:
                        submission = coding_submissions.filter(
                            question_id=str(ai_q.id)
                        ).first()
                        
                        if not submission:
                            # Try without hyphens
                            question_id_no_hyphens = str(ai_q.id).replace('-', '')
                            submission = coding_submissions.filter(
                                question_id=question_id_no_hyphens
                            ).first()
                        
                        if submission and submission.submitted_code:
                            answer_text = submission.submitted_code
                            code_submission_data = {
                                'submitted_code': submission.submitted_code,
                                'language': submission.language,
                                'passed_all_tests': submission.passed_all_tests,
                                'output_log': submission.output_log,
                                'gemini_evaluation': submission.gemini_evaluation,
                                'created_at': submission.created_at.isoformat() if submission.created_at else None,
                            }
                    except Exception as e:
                        print(f"⚠️ Error finding submission for coding question {ai_q.id}: {e}")
                    
                    qa_item = {
                        'question_number': ai_q.order + 1,
                        'question': question_text,
                        'question_text': question_text,  # Also include for compatibility
                        'answer': answer_text,
                        'question_type': 'CODING',
                        'response_time': 0,
                        'order': ai_q.order,
                        'conversation_sequence': ai_q.conversation_sequence,
                    }
                    
                    if code_submission_data:
                        qa_item['code_submission'] = code_submission_data
                    
                    qa_list.append(qa_item)
                    continue  # Skip regular answer handling for coding questions
                
                # Regular technical/behavioral questions (SAME AS PDF)
                question_text = ai_q.question_text or ''
                if question_text.strip().startswith('Q:'):
                    question_text = question_text.replace('Q:', '').strip()
                
                # Answer text - use same logic as PDF
                answer_text = 'No answer provided'
                if interviewee_a:
                    answer_text = interviewee_a.transcribed_answer or ''
                    if answer_text.strip().startswith('A:'):
                        answer_text = answer_text.replace('A:', '').strip()
                
                # If no separate interviewee record, try transcribed_answer from AI question itself
                if not answer_text or answer_text == 'No answer provided':
                    if ai_q.transcribed_answer:
                        answer_text = ai_q.transcribed_answer
                        if answer_text.strip().startswith('A:'):
                            answer_text = answer_text.replace('A:', '').strip()
                
                # Format answer
                if not answer_text or answer_text.strip() == '' or answer_text.lower() == 'none':
                    answer_text = 'No answer provided'
                
                qa_item = {
                    'question_number': ai_q.order + 1,
                    'question': question_text,
                    'question_text': question_text,  # Also include for compatibility
                    'answer': answer_text,
                    'question_type': ai_q.question_type or 'TECHNICAL',
                    'response_time': interviewee_a.response_time_seconds if interviewee_a else (ai_q.response_time_seconds or 0),
                    'order': ai_q.order,
                    'conversation_sequence': ai_q.conversation_sequence,
                }
                
                qa_list.append(qa_item)
            
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
        """Get proctoring PDF URL from separate ProctoringPDF table - use URL as-is from database"""
        try:
            from evaluation.models import ProctoringPDF
            
            proctoring_pdf = ProctoringPDF.objects.filter(interview=obj).first()
            if proctoring_pdf and proctoring_pdf.gcs_url:
                # Return URL exactly as stored in database - no modification, no cleaning
                return {
                    'gcs_url': proctoring_pdf.gcs_url,  # Use URL as-is from database
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
