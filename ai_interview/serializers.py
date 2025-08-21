# ai_interview/serializers.py
from rest_framework import serializers
from .models import AIInterviewSession, AIInterviewQuestion, AIInterviewResponse, AIInterviewResult


class AIInterviewSessionSerializer(serializers.ModelSerializer):
    """Serializer for AI Interview Session"""
    
    progress_percentage = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    candidate_name = serializers.CharField(source='interview.candidate.full_name', read_only=True)
    job_title = serializers.CharField(source='interview.job.job_title', read_only=True)
    
    class Meta:
        model = AIInterviewSession
        fields = [
            'id', 'interview', 'status', 'model_name', 'model_version',
            'current_question_index', 'total_questions', 'questions_answered',
            'session_started_at', 'session_ended_at', 'session_duration',
            'response_time_avg', 'progress_percentage', 'is_active',
            'candidate_name', 'job_title', 'ai_configuration',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'session_started_at', 'session_ended_at', 'session_duration',
            'response_time_avg', 'progress_percentage', 'is_active',
            'candidate_name', 'job_title', 'created_at', 'updated_at'
        ]


class AIInterviewQuestionSerializer(serializers.ModelSerializer):
    """Serializer for AI Interview Question"""
    
    session_id = serializers.UUIDField(source='session.id', read_only=True)
    question_number = serializers.IntegerField(source='question_index', read_only=True)
    
    class Meta:
        model = AIInterviewQuestion
        fields = [
            'id', 'session', 'session_id', 'question_index', 'question_number',
            'question_type', 'difficulty', 'question_text', 'question_context',
            'ai_model_prompt', 'ai_model_response', 'question_asked_at',
            'response_received_at', 'response_time', 'is_answered', 'is_correct',
            'score', 'ai_feedback', 'human_feedback', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'session_id', 'ai_model_prompt', 'ai_model_response',
            'question_asked_at', 'response_received_at', 'response_time',
            'is_answered', 'is_correct', 'score', 'ai_feedback', 'human_feedback',
            'created_at', 'updated_at'
        ]


class AIInterviewResponseSerializer(serializers.ModelSerializer):
    """Serializer for AI Interview Response"""
    
    session_id = serializers.UUIDField(source='session.id', read_only=True)
    question_text = serializers.CharField(source='question.question_text', read_only=True)
    question_type = serializers.CharField(source='question.question_type', read_only=True)
    
    class Meta:
        model = AIInterviewResponse
        fields = [
            'id', 'question', 'session', 'session_id', 'response_text',
            'response_type', 'response_data', 'response_submitted_at',
            'response_duration', 'ai_evaluation', 'ai_score', 'ai_feedback',
            'response_length', 'confidence_score', 'question_text', 'question_type',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'session_id', 'response_submitted_at', 'ai_evaluation',
            'ai_score', 'ai_feedback', 'response_length', 'confidence_score',
            'question_text', 'question_type', 'created_at', 'updated_at'
        ]


class AIInterviewResultSerializer(serializers.ModelSerializer):
    """Serializer for AI Interview Result"""
    
    session_id = serializers.UUIDField(source='session.id', read_only=True)
    candidate_name = serializers.CharField(source='interview.candidate.full_name', read_only=True)
    job_title = serializers.CharField(source='interview.job.job_title', read_only=True)
    accuracy_percentage = serializers.ReadOnlyField()
    is_recommended_for_hire = serializers.ReadOnlyField()
    
    class Meta:
        model = AIInterviewResult
        fields = [
            'id', 'session', 'session_id', 'interview', 'total_score',
            'technical_score', 'behavioral_score', 'coding_score',
            'questions_attempted', 'questions_correct', 'average_response_time',
            'completion_time', 'ai_summary', 'ai_recommendations', 'strengths',
            'weaknesses', 'overall_rating', 'hire_recommendation', 'confidence_level',
            'human_reviewer', 'human_rating', 'human_feedback', 'reviewed_at',
            'candidate_name', 'job_title', 'accuracy_percentage', 'is_recommended_for_hire',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'session_id', 'total_score', 'technical_score', 'behavioral_score',
            'coding_score', 'questions_attempted', 'questions_correct',
            'average_response_time', 'completion_time', 'ai_summary',
            'ai_recommendations', 'strengths', 'weaknesses', 'overall_rating',
            'hire_recommendation', 'confidence_level', 'accuracy_percentage',
            'is_recommended_for_hire', 'candidate_name', 'job_title',
            'created_at', 'updated_at'
        ]


class AIInterviewSessionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating AI Interview Session"""
    
    class Meta:
        model = AIInterviewSession
        fields = ['interview', 'model_name', 'model_version', 'ai_configuration']


class AIInterviewResponseCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating AI Interview Response"""
    
    class Meta:
        model = AIInterviewResponse
        fields = ['question', 'session', 'response_text', 'response_type', 'response_data']


class AIInterviewSessionDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for AI Interview Session with related data"""
    
    questions = AIInterviewQuestionSerializer(many=True, read_only=True)
    responses = AIInterviewResponseSerializer(many=True, read_only=True)
    result = AIInterviewResultSerializer(read_only=True)
    candidate_name = serializers.CharField(source='interview.candidate.full_name', read_only=True)
    job_title = serializers.CharField(source='interview.job.job_title', read_only=True)
    progress_percentage = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    
    class Meta:
        model = AIInterviewSession
        fields = [
            'id', 'interview', 'status', 'model_name', 'model_version',
            'current_question_index', 'total_questions', 'questions_answered',
            'session_started_at', 'session_ended_at', 'session_duration',
            'response_time_avg', 'progress_percentage', 'is_active',
            'candidate_name', 'job_title', 'ai_configuration',
            'questions', 'responses', 'result', 'created_at', 'updated_at'
        ]


class AIInterviewQuestionDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for AI Interview Question with responses"""
    
    responses = AIInterviewResponseSerializer(many=True, read_only=True)
    session_id = serializers.UUIDField(source='session.id', read_only=True)
    question_number = serializers.IntegerField(source='question_index', read_only=True)
    
    class Meta:
        model = AIInterviewQuestion
        fields = [
            'id', 'session', 'session_id', 'question_index', 'question_number',
            'question_type', 'difficulty', 'question_text', 'question_context',
            'ai_model_prompt', 'ai_model_response', 'question_asked_at',
            'response_received_at', 'response_time', 'is_answered', 'is_correct',
            'score', 'ai_feedback', 'human_feedback', 'responses',
            'created_at', 'updated_at'
        ]


class AIInterviewResultDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for AI Interview Result with session data"""
    
    session = AIInterviewSessionSerializer(read_only=True)
    candidate_name = serializers.CharField(source='interview.candidate.full_name', read_only=True)
    job_title = serializers.CharField(source='interview.job.job_title', read_only=True)
    accuracy_percentage = serializers.ReadOnlyField()
    is_recommended_for_hire = serializers.ReadOnlyField()
    
    class Meta:
        model = AIInterviewResult
        fields = [
            'id', 'session', 'interview', 'total_score', 'technical_score',
            'behavioral_score', 'coding_score', 'questions_attempted',
            'questions_correct', 'average_response_time', 'completion_time',
            'ai_summary', 'ai_recommendations', 'strengths', 'weaknesses',
            'overall_rating', 'hire_recommendation', 'confidence_level',
            'human_reviewer', 'human_rating', 'human_feedback', 'reviewed_at',
            'candidate_name', 'job_title', 'accuracy_percentage',
            'is_recommended_for_hire', 'created_at', 'updated_at'
        ]


class AIInterviewStartSerializer(serializers.Serializer):
    """Serializer for starting an AI interview session"""
    
    interview_id = serializers.UUIDField()
    
    def validate_interview_id(self, value):
        """Validate that the interview exists and can be started"""
        from interviews.models import Interview
        
        try:
            interview = Interview.objects.get(id=value)
            if interview.status == 'completed':
                raise serializers.ValidationError("Interview has already been completed")
            return value
        except Interview.DoesNotExist:
            raise serializers.ValidationError("Interview not found")


class AIInterviewResponseSubmitSerializer(serializers.Serializer):
    """Serializer for submitting a response to an AI interview question"""
    
    question_id = serializers.UUIDField()
    response_text = serializers.CharField(max_length=5000)
    response_type = serializers.CharField(default='text', max_length=20)
    response_data = serializers.JSONField(required=False, default=dict)
    
    def validate_question_id(self, value):
        """Validate that the question exists and belongs to an active session"""
        try:
            question = AIInterviewQuestion.objects.get(id=value)
            if not question.session.is_active:
                raise serializers.ValidationError("Interview session is not active")
            return value
        except AIInterviewQuestion.DoesNotExist:
            raise serializers.ValidationError("Question not found")


class AIInterviewCompleteSerializer(serializers.Serializer):
    """Serializer for completing an AI interview session"""
    
    session_id = serializers.UUIDField()
    
    def validate_session_id(self, value):
        """Validate that the session exists and can be completed"""
        try:
            session = AIInterviewSession.objects.get(id=value)
            if session.status == 'completed':
                raise serializers.ValidationError("Session has already been completed")
            return value
        except AIInterviewSession.DoesNotExist:
            raise serializers.ValidationError("Session not found")


class AIInterviewHumanReviewSerializer(serializers.Serializer):
    """Serializer for human review of AI interview results"""
    
    result_id = serializers.UUIDField()
    human_rating = serializers.ChoiceField(choices=[
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('average', 'Average'),
        ('poor', 'Poor')
    ])
    human_feedback = serializers.CharField(max_length=2000)
    
    def validate_result_id(self, value):
        """Validate that the result exists"""
        try:
            result = AIInterviewResult.objects.get(id=value)
            return value
        except AIInterviewResult.DoesNotExist:
            raise serializers.ValidationError("Interview result not found")

