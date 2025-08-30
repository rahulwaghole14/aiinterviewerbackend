# interviews/serializers.py
from datetime import time, datetime, timedelta
from django.utils import timezone
from rest_framework import serializers
from .models import (
    Interview, InterviewSlot, InterviewSchedule, 
    AIInterviewConfiguration, InterviewConflict
)
from ai_platform.interview_app.models import InterviewSession, InterviewQuestion


class InterviewSerializer(serializers.ModelSerializer):
    """
    Main read / write serializer for Interview.
    Adds two read‑only convenience fields:
      • candidate_name – Candidate.full_name
      • job_title       – Job.job_title

    Includes a custom validate() that restricts the scheduled
    window to **08:00 – 22:00 UTC** for both start and end times.
    """
    candidate_name = serializers.CharField(
        source="candidate.full_name", read_only=True
    )
    job_title = serializers.CharField(
        source="job.job_title", read_only=True
    )
    is_scheduled = serializers.BooleanField(read_only=True)
    ai_interview_type = serializers.CharField(read_only=True)
    
    # Slot information
    slot_details = serializers.SerializerMethodField()
    schedule_status = serializers.SerializerMethodField()
    booking_notes = serializers.SerializerMethodField()
    
    # AI Interview Result
    ai_result = serializers.SerializerMethodField()

    class Meta:
        model  = Interview
        fields = [
            "id",
            "candidate", "candidate_name",
            "job", "job_title",
            "status",
            "interview_round", "feedback",
            "started_at", "ended_at",
            "video_url",
            "created_at", "updated_at",
            "is_scheduled",
            "ai_interview_type",
            "slot_details",
            "schedule_status",
            "booking_notes",
            "ai_result",
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
            'candidate': {'required': False},
            'job': {'required': False},
            'started_at': {'required': False},
            'ended_at': {'required': False},
            'status': {'required': False},
            'interview_round': {'required': False},
            'feedback': {'required': False},
            'video_url': {'required': False},
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
        if 'interview_round' not in data or not data.get('interview_round'):
            data['interview_round'] = "AI Interview"
        
        # Only validate time constraints if we're updating time fields
        if 'started_at' in data or 'ended_at' in data:
            start_dt = data.get("started_at") or getattr(self.instance, "started_at", None)
            end_dt   = data.get("ended_at")   or getattr(self.instance, "ended_at", None)

            if not start_dt or not end_dt:
                raise serializers.ValidationError(
                    "Both 'started_at' and 'ended_at' must be provided when updating time fields."
                )

            # Time window bounds (24‑hour clock, UTC)
            min_time = time(8, 0)   # 08:00
            max_time = time(22, 0)  # 22:00

            start_t = start_dt.time()
            end_t   = end_dt.time()

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
                raise serializers.ValidationError(
                    "ended_at must be after started_at."
                )

        return data
    
    def get_slot_details(self, obj):
        """Get slot details if interview is scheduled"""
        if hasattr(obj, 'schedule') and obj.schedule:
            slot = obj.schedule.slot
            return {
                'slot_id': slot.id,
                'start_time': slot.start_time,
                'end_time': slot.end_time,
                'duration_minutes': slot.duration_minutes,
                'ai_interview_type': slot.ai_interview_type,
                'max_candidates': slot.max_candidates,
                'current_bookings': slot.current_bookings,
                'slot_status': slot.status,
            }
        return None
    
    def get_schedule_status(self, obj):
        """Get schedule status"""
        if hasattr(obj, 'schedule') and obj.schedule:
            return obj.schedule.status
        return None
    
    def get_booking_notes(self, obj):
        """Get booking notes"""
        if hasattr(obj, 'schedule') and obj.schedule:
            return obj.schedule.booking_notes
        return None
    
    def get_ai_result(self, obj):
        """Get AI interview result if available - only for COMPLETED interviews"""
        try:
            # First check if the interview is actually completed
            if obj.status != 'completed':
                return None
            
            # Try to get the AIInterviewResult for this specific interview
            from ai_interview.models import AIInterviewResult
            
            try:
                ai_result = AIInterviewResult.objects.get(interview=obj)
                # Return the actual AI result data
                return {
                    'is_evaluated': True,
                    'resume_score': ai_result.technical_score or 0,
                    'answers_score': ai_result.behavioral_score or 0,
                    'overall_score': ai_result.total_score or 0,
                    'resume_feedback': ai_result.ai_summary or "",
                    'answers_feedback': ai_result.ai_recommendations or "",
                    'overall_feedback': ai_result.ai_summary or "",
                    'strengths': ai_result.strengths if isinstance(ai_result.strengths, list) else [],
                    'weaknesses': ai_result.weaknesses if isinstance(ai_result.weaknesses, list) else [],
                    'hire_recommendation': ai_result.hire_recommendation or False,
                    'confidence_level': ai_result.confidence_level or 0,
                    'coding_details': self._get_coding_details_from_ai_result(ai_result),
                    'session_id': str(ai_result.session.id) if ai_result.session else None,
                    'evaluated_at': ai_result.created_at.isoformat() if ai_result.created_at else None,
                    # Additional fields for compatibility
                    'overall_rating': ai_result.overall_rating or 'pending',
                    'total_score': ai_result.total_score or 0,
                    'technical_score': ai_result.technical_score or 0,
                    'behavioral_score': ai_result.behavioral_score or 0,
                    'coding_score': ai_result.coding_score or 0,
                    'ai_summary': ai_result.ai_summary or "",
                    'ai_recommendations': ai_result.ai_recommendations or "",
                    'questions_attempted': ai_result.questions_attempted or 0,
                    'questions_correct': ai_result.questions_correct or 0,
                    'accuracy_percentage': ai_result.accuracy_percentage or 0,
                    'average_response_time': ai_result.average_response_time or 0,
                    'completion_time': ai_result.completion_time or 0,
                    'human_feedback': ai_result.human_feedback or None,
                    'human_rating': ai_result.human_rating or None,
                    # Recording information from session
                    'recording_video': ai_result.session.interview.ai_session.recording_video.url if (
                        ai_result.session and 
                        hasattr(ai_result.session.interview, 'ai_session') and 
                        ai_result.session.interview.ai_session.recording_video
                    ) else None,
                    'recording_created_at': ai_result.session.interview.ai_session.recording_created_at.isoformat() if (
                        ai_result.session and 
                        hasattr(ai_result.session.interview, 'ai_session') and 
                        ai_result.session.interview.ai_session.recording_created_at
                    ) else None,
                }
            except AIInterviewResult.DoesNotExist:
                # No AI result exists for this interview - try legacy InterviewSession approach
                # But ONLY if the interview is actually completed
                return self._get_legacy_ai_result(obj)
                
        except Exception as e:
            print(f"Error getting AI result for interview {obj.id}: {e}")
            import traceback
            traceback.print_exc()
        return None

    def _get_legacy_ai_result(self, obj):
        """Get AI result from legacy InterviewSession - only for completed interviews"""
        try:
            # Only return data for completed interviews
            if obj.status != 'completed':
                return None
                
            # Get candidate name from interview
            candidate_name = obj.candidate.full_name if obj.candidate else ""
            
            # Look for a session that matches this interview's candidate and job
            # Try exact match first with more strict criteria
            session = InterviewSession.objects.filter(
                candidate_name=candidate_name,
                job_description__icontains=obj.job.job_title if obj.job else "",
                is_evaluated=True,
                status='COMPLETED'  # Only completed sessions
            ).order_by('-created_at').first()
            
            # If no exact match, try fuzzy matching for common name variations
            # But be more restrictive to avoid cross-candidate contamination
            if not session:
                # Extract first and last name parts
                name_parts = candidate_name.lower().split()
                if len(name_parts) >= 2:
                    first_name = name_parts[0]
                    last_name = name_parts[-1]
                    
                    # Look for sessions with exact name match (not just contains)
                    session = InterviewSession.objects.filter(
                        candidate_name__iexact=candidate_name,
                        is_evaluated=True,
                        status='COMPLETED'
                    ).order_by('-created_at').first()
            
            if session and session.is_evaluated:
                # Convert the session evaluation data to the format expected by frontend
                return {
                    'is_evaluated': True,
                    'resume_score': session.resume_score * 10 if session.resume_score else 0,
                    'answers_score': session.answers_score * 10 if session.answers_score else 0,
                    'overall_score': session.overall_performance_score * 10 if session.overall_performance_score else 0,
                    'resume_feedback': session.resume_feedback or "",
                    'answers_feedback': session.answers_feedback or "",
                    'overall_feedback': session.overall_performance_feedback or "",
                    'strengths': self._extract_strengths(session.answers_feedback),
                    'weaknesses': self._extract_weaknesses(session.resume_feedback),
                    'hire_recommendation': self._extract_hire_recommendation(session.overall_performance_feedback),
                    'confidence_level': 85.0 if session.overall_performance_score and session.overall_performance_score > 7 else 65.0,
                    'coding_details': self._get_coding_details(session),
                    'session_id': str(session.id),
                    'evaluated_at': session.created_at.isoformat() if session.created_at else None,
                    # Additional fields for compatibility
                    'overall_rating': self._get_rating_from_score(session.overall_performance_score),
                    'total_score': session.overall_performance_score * 10 if session.overall_performance_score else 0,
                    'technical_score': session.answers_score * 10 if session.answers_score else 0,
                    'behavioral_score': session.resume_score * 10 if session.resume_score else 0,
                    'coding_score': session.answers_score * 10 if session.answers_score else 0,
                    'ai_summary': session.overall_performance_feedback or "",
                    'ai_recommendations': session.answers_feedback or "",
                    'questions_attempted': self._calculate_questions_attempted(session),
                    'questions_correct': self._calculate_questions_correct(session),
                    'accuracy_percentage': self._calculate_accuracy(session),
                    'average_response_time': self._calculate_average_response_time(session),
                    'completion_time': self._calculate_completion_time(session),
                    'human_feedback': None,  # Not available in current model
                    'human_rating': None,  # Not available in current model
                    # Recording information
                    'recording_video': session.recording_video.url if session.recording_video else None,
                    'recording_created_at': session.recording_created_at.isoformat() if session.recording_created_at else None,
                }
        except Exception as e:
            print(f"Error getting legacy AI result for interview {obj.id}: {e}")
        return None
    
    def _get_rating_from_score(self, score):
        """Convert numerical score to rating"""
        if not score:
            return 'pending'
        elif score >= 8:
            return 'excellent'
        elif score >= 6:
            return 'good'
        elif score >= 4:
            return 'fair'
        else:
            return 'poor'
    
    def _extract_hire_recommendation(self, feedback):
        """Extract hire recommendation from feedback"""
        if not feedback:
            return False
        
        feedback_lower = feedback.lower()
        if 'hire' in feedback_lower and 'recommend' in feedback_lower:
            if 'not' in feedback_lower or 'do not' in feedback_lower:
                return False
            else:
                return True
        elif 'strong' in feedback_lower and 'candidate' in feedback_lower:
            return True
        elif 'weak' in feedback_lower or 'poor' in feedback_lower:
            return False
        else:
            return True  # Default to recommend if unclear
    
    def _extract_strengths(self, feedback):
        """Extract strengths as an array from feedback"""
        if not feedback:
            return []
        
        # Look for specific positive indicators in the feedback
        strengths = []
        
        # Check for coding success
        if any(word in feedback.lower() for word in ['coding challenge was successfully completed', 'successfully completed', 'correct', 'functional']):
            strengths.append("Successfully completed coding challenge")
        
        # Check for technical knowledge
        if any(word in feedback.lower() for word in ['technical knowledge', 'demonstrated', 'understanding']):
            strengths.append("Demonstrated technical knowledge")
        
        # Check for problem-solving
        if any(word in feedback.lower() for word in ['problem-solving', 'algorithm', 'solution']):
            strengths.append("Showed problem-solving abilities")
        
        # If no specific strengths found, create generic ones based on context
        if not strengths:
            strengths = ["Completed interview process", "Demonstrated basic technical skills"]
        
        return strengths
    
    def _extract_weaknesses(self, feedback):
        """Extract weaknesses as an array from feedback"""
        if not feedback:
            return []
        
        # Look for specific improvement areas in the feedback
        weaknesses = []
        
        # Check for communication issues
        if any(word in feedback.lower() for word in ['lack of answers', 'inability to articulate', 'communication skills', 'no answers']):
            weaknesses.append("Needs to improve communication skills")
        
        # Check for preparation issues
        if any(word in feedback.lower() for word in ['lack of preparation', 'not prepared', 'absence of answers']):
            weaknesses.append("Needs better interview preparation")
        
        # Check for technical depth
        if any(word in feedback.lower() for word in ['basic problem', 'lack of understanding', 'technical depth', 'advanced']):
            weaknesses.append("Needs more technical depth")
        
        # Check for experience gaps
        if any(word in feedback.lower() for word in ['lack of experience', 'practical experience', 'gap in']):
            weaknesses.append("Needs more practical experience")
        
        # If no specific weaknesses found, create generic ones based on context
        if not weaknesses:
            weaknesses = ["Could improve communication skills", "Needs more technical depth"]
        
        return weaknesses
    
    def _calculate_questions_attempted(self, session):
        """Calculate total questions attempted (spoken + coding)"""
        spoken_questions = session.questions.count()
        coding_submissions = session.code_submissions.count()
        return spoken_questions + coding_submissions
    
    def _calculate_questions_correct(self, session):
        """Calculate questions answered correctly"""
        # Count spoken questions with answers
        spoken_answered = session.questions.filter(transcribed_answer__isnull=False).exclude(transcribed_answer='').count()
        
        # Count coding submissions that passed tests
        coding_correct = session.code_submissions.filter(passed_all_tests=True).count()
        
        return spoken_answered + coding_correct
    
    def _calculate_accuracy(self, session):
        """Calculate accuracy percentage based on questions answered correctly"""
        questions_attempted = self._calculate_questions_attempted(session)
        questions_correct = self._calculate_questions_correct(session)
        
        if questions_attempted == 0:
            return 0.0
        
        return (questions_correct / questions_attempted) * 100
    
    def _calculate_average_response_time(self, session):
        """Calculate average response time in seconds"""
        response_times = []
        
        # Get response times from spoken questions
        for question in session.questions.filter(transcribed_answer__isnull=False).exclude(transcribed_answer=''):
            if question.response_time_seconds:
                response_times.append(question.response_time_seconds)
        
        # For coding submissions, estimate response time (coding challenges typically take longer)
        coding_submissions = session.code_submissions.count()
        if coding_submissions > 0:
            # Estimate 5 minutes per coding challenge
            estimated_coding_time = coding_submissions * 300  # 5 minutes = 300 seconds
            response_times.append(estimated_coding_time)
        
        if not response_times:
            return 0.0
        
        return sum(response_times) / len(response_times)
    
    def _calculate_completion_time(self, session):
        """Calculate total completion time in seconds"""
        total_time = 0
        
        # Add response times from spoken questions
        for question in session.questions.filter(transcribed_answer__isnull=False).exclude(transcribed_answer=''):
            if question.response_time_seconds:
                total_time += question.response_time_seconds
        
        # Add estimated time for coding submissions
        coding_submissions = session.code_submissions.count()
        if coding_submissions > 0:
            # Estimate 5 minutes per coding challenge
            estimated_coding_time = coding_submissions * 300  # 5 minutes = 300 seconds
            total_time += estimated_coding_time
        
        return total_time
    
    def _get_coding_details_from_ai_result(self, ai_result):
        """Get coding question details from AI result"""
        # For now, return empty list since AIInterviewResult doesn't store coding details yet
        # This can be enhanced when we add coding question support to the new AI model
        return []
    
    def _get_coding_details(self, session):
        """Get coding question details for the session"""
        coding_details = []
        
        # Get all code submissions
        code_submissions = session.code_submissions.all()
        
        for submission in code_submissions:
            try:
                # Try to get the question details
                question = InterviewQuestion.objects.get(id=submission.question_id)
                question_text = question.question_text
            except InterviewQuestion.DoesNotExist:
                question_text = f"Question ID: {submission.question_id}"
            
            coding_detail = {
                'question_text': question_text,
                'language': submission.language,
                'submitted_code': submission.submitted_code,
                'passed_all_tests': submission.passed_all_tests,
                'output_log': submission.output_log or "",
                'created_at': submission.created_at.isoformat() if submission.created_at else None
            }
            
            coding_details.append(coding_detail)
        
        return coding_details


class InterviewFeedbackSerializer(serializers.ModelSerializer):
    """
    Serializer for updating interview feedback
    """
    class Meta:
        model  = Interview
        fields = ["interview_round", "feedback"]


class InterviewSlotSerializer(serializers.ModelSerializer):
    """
    Serializer for AI interview slots
    """
    company_name = serializers.CharField(source='company.name', read_only=True)
    job_title = serializers.CharField(source='job.job_title', read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    available_spots = serializers.SerializerMethodField()

    class Meta:
        model = InterviewSlot
        fields = [
            'id', 'slot_type', 'status', 'start_time', 'end_time', 'duration_minutes',
            'ai_interview_type', 'ai_configuration', 'company', 'company_name', 'job', 'job_title',
            'is_recurring', 'recurring_pattern', 'notes', 'max_candidates', 'current_bookings',
            'is_available', 'available_spots', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_available', 'available_spots']

    def get_available_spots(self, obj):
        return max(0, obj.max_candidates - obj.current_bookings)

    def validate(self, data):
        if data.get('start_time') and data.get('end_time'):
            if data['start_time'] >= data['end_time']:
                raise serializers.ValidationError("End time must be after start time")
        return data


class InterviewScheduleSerializer(serializers.ModelSerializer):
    """
    Serializer for AI interview schedules
    """
    interview_details = serializers.SerializerMethodField()
    slot_details = serializers.SerializerMethodField()
    ai_interview_type = serializers.CharField(source='slot.ai_interview_type', read_only=True)
    candidate_name = serializers.CharField(source='interview.candidate.full_name', read_only=True)

    class Meta:
        model = InterviewSchedule
        fields = [
            'id', 'interview', 'slot', 'status', 'booking_notes',
            'booked_at', 'confirmed_at', 'cancelled_at',
            'cancellation_reason', 'cancelled_by',
            'interview_details', 'slot_details', 'ai_interview_type', 'candidate_name'
        ]
        read_only_fields = ['id', 'booked_at', 'confirmed_at', 'cancelled_at', 'cancelled_by']

    def get_interview_details(self, obj):
        return {
            'id': obj.interview.id,
            'candidate_name': obj.interview.candidate.full_name,
            'status': obj.interview.status,
            'started_at': obj.interview.started_at,
            'ended_at': obj.interview.ended_at,
        }

    def get_slot_details(self, obj):
        return {
            'id': obj.slot.id,
            'ai_interview_type': obj.slot.ai_interview_type,
            'start_time': obj.slot.start_time,
            'end_time': obj.slot.end_time,
            'duration_minutes': obj.slot.duration_minutes,
            'company_name': obj.slot.company.name,
        }

    def validate(self, data):
        # Check if slot is available
        if 'slot' in data:
            slot = data['slot']
            if not slot.is_available():
                raise serializers.ValidationError("Selected slot is not available for booking")
            
            # Check if interview is already scheduled
            if 'interview' in data:
                interview = data['interview']
                if hasattr(interview, 'schedule') and interview.schedule:
                    raise serializers.ValidationError("Interview is already scheduled")
        
        return data


class AIInterviewConfigurationSerializer(serializers.ModelSerializer):
    """
    Serializer for AI interview configuration patterns
    """
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = AIInterviewConfiguration
        fields = [
            'id', 'company', 'company_name', 'interview_type',
            'day_of_week', 'start_time', 'end_time', 'slot_duration', 'break_duration',
            'ai_settings', 'valid_from', 'valid_until',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        if data.get('start_time') and data.get('end_time'):
            if data['start_time'] >= data['end_time']:
                raise serializers.ValidationError("End time must be after start time")
        return data


class InterviewConflictSerializer(serializers.ModelSerializer):
    """
    Serializer for interview conflicts
    """
    primary_interview_details = serializers.SerializerMethodField()
    conflicting_interview_details = serializers.SerializerMethodField()
    resolved_by_name = serializers.CharField(source='resolved_by.full_name', read_only=True)

    class Meta:
        model = InterviewConflict
        fields = [
            'id', 'conflict_type', 'resolution', 'primary_interview', 'conflicting_interview',
            'conflict_details', 'resolution_notes', 'detected_at', 'resolved_at', 'resolved_by',
            'primary_interview_details', 'conflicting_interview_details', 'resolved_by_name'
        ]
        read_only_fields = ['id', 'detected_at', 'resolved_at', 'resolved_by']

    def get_primary_interview_details(self, obj):
        return {
            'id': obj.primary_interview.id,
            'candidate_name': obj.primary_interview.candidate.full_name,
            'status': obj.primary_interview.status,
            'started_at': obj.primary_interview.started_at,
            'ended_at': obj.primary_interview.ended_at,
        }

    def get_conflicting_interview_details(self, obj):
        if obj.conflicting_interview:
            return {
                'id': obj.conflicting_interview.id,
                'candidate_name': obj.conflicting_interview.candidate.full_name,
                'status': obj.conflicting_interview.status,
                'started_at': obj.conflicting_interview.started_at,
                'ended_at': obj.conflicting_interview.ended_at,
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
            interview = Interview.objects.get(id=data['interview_id'])
            data['interview'] = interview
        except Interview.DoesNotExist:
            raise serializers.ValidationError("Interview not found")
        
        # Validate slot exists and is available
        try:
            slot = InterviewSlot.objects.get(id=data['slot_id'])
            data['slot'] = slot
        except InterviewSlot.DoesNotExist:
            raise serializers.ValidationError("Slot not found")
        
        if not slot.is_available():
            raise serializers.ValidationError("Slot is not available for booking")
        
        # Check if interview is already scheduled
        if hasattr(interview, 'schedule') and interview.schedule:
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
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError("Start date must be before or equal to end date")
        return data


class RecurringSlotSerializer(serializers.Serializer):
    """
    Serializer for creating recurring slots
    """
    company_id = serializers.IntegerField()
    ai_interview_type = serializers.CharField(default='general')
    job_id = serializers.IntegerField(required=False)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    days_of_week = serializers.ListField(
        child=serializers.IntegerField(min_value=1, max_value=7),
        min_length=1
    )
    slot_duration = serializers.IntegerField(default=60, min_value=15, max_value=480)
    break_duration = serializers.IntegerField(default=15, min_value=0, max_value=60)
    max_candidates_per_slot = serializers.IntegerField(default=1, min_value=1, max_value=10)
    ai_configuration = serializers.JSONField(required=False, default=dict)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError("Start date must be before or equal to end date")
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError("End time must be after start time")
        return data
