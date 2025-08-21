# ai_interview/models.py
import uuid
from django.db import models
from django.utils import timezone
from interviews.models import Interview


class AIInterviewSession(models.Model):
    """
    Represents an active AI interview session
    """
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        COMPLETED = "completed", "Completed"
        ERROR = "error", "Error"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    interview = models.OneToOneField(Interview, on_delete=models.CASCADE, related_name='ai_session')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    
    # AI Model Configuration
    model_name = models.CharField(max_length=100, default='default_ai_model')
    model_version = models.CharField(max_length=50, default='1.0')
    ai_configuration = models.JSONField(default=dict, help_text="AI model configuration parameters")
    
    # Session Tracking
    current_question_index = models.PositiveIntegerField(default=0)
    total_questions = models.PositiveIntegerField(default=0)
    session_started_at = models.DateTimeField(default=timezone.now)
    session_ended_at = models.DateTimeField(null=True, blank=True)
    
    # Performance Metrics
    response_time_avg = models.FloatField(default=0.0, help_text="Average response time in seconds")
    questions_answered = models.PositiveIntegerField(default=0)
    session_duration = models.PositiveIntegerField(default=0, help_text="Session duration in seconds")
    
    # Error Handling
    error_message = models.TextField(blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ai_interview_session'
        indexes = [
            models.Index(fields=['status', 'session_started_at']),
            models.Index(fields=['interview', 'status']),
        ]

    def __str__(self):
        return f"AI Session - {self.interview.candidate.full_name} ({self.status})"

    @property
    def is_active(self):
        return self.status == self.Status.ACTIVE

    @property
    def progress_percentage(self):
        if self.total_questions > 0:
            return (self.current_question_index / self.total_questions) * 100
        return 0

    def complete_session(self):
        """Mark session as completed"""
        self.status = self.Status.COMPLETED
        self.session_ended_at = timezone.now()
        if self.session_started_at:
            self.session_duration = int((self.session_ended_at - self.session_started_at).total_seconds())
        self.save()


class AIInterviewQuestion(models.Model):
    """
    Represents individual questions in an AI interview session
    """
    class QuestionType(models.TextChoices):
        TECHNICAL = "technical", "Technical Question"
        BEHAVIORAL = "behavioral", "Behavioral Question"
        CODING = "coding", "Coding Question"
        SYSTEM_DESIGN = "system_design", "System Design Question"
        GENERAL = "general", "General Question"

    class Difficulty(models.TextChoices):
        EASY = "easy", "Easy"
        MEDIUM = "medium", "Medium"
        HARD = "hard", "Hard"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(AIInterviewSession, on_delete=models.CASCADE, related_name='questions')
    question_index = models.PositiveIntegerField()
    question_type = models.CharField(max_length=20, choices=QuestionType.choices)
    difficulty = models.CharField(max_length=10, choices=Difficulty.choices, default=Difficulty.MEDIUM)
    
    # Question Content
    question_text = models.TextField()
    question_context = models.JSONField(default=dict, help_text="Additional context for the question")
    audio_url = models.URLField(max_length=500, null=True, blank=True, help_text="URL to the audio file for this question")
    
    # AI Model Data
    ai_model_prompt = models.TextField(blank=True, help_text="Prompt sent to AI model")
    ai_model_response = models.TextField(blank=True, help_text="Response from AI model")
    
    # Timing
    question_asked_at = models.DateTimeField(default=timezone.now)
    response_received_at = models.DateTimeField(null=True, blank=True)
    response_time = models.FloatField(null=True, blank=True, help_text="Response time in seconds")
    
    # Status
    is_answered = models.BooleanField(default=False)
    is_correct = models.BooleanField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True, help_text="Score for this question (0-100)")
    
    # Feedback
    ai_feedback = models.TextField(blank=True, help_text="AI feedback on the answer")
    human_feedback = models.TextField(blank=True, help_text="Human reviewer feedback")
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ai_interview_question'
        unique_together = ['session', 'question_index']
        indexes = [
            models.Index(fields=['session', 'question_index']),
            models.Index(fields=['question_type', 'difficulty']),
        ]
        ordering = ['session', 'question_index']

    def __str__(self):
        return f"Q{self.question_index}: {self.question_text[:50]}..."

    def mark_answered(self, ai_response, response_time=None):
        """Mark question as answered with AI response"""
        self.ai_model_response = ai_response
        self.is_answered = True
        self.response_received_at = timezone.now()
        if response_time:
            self.response_time = response_time
        elif self.question_asked_at:
            self.response_time = (self.response_received_at - self.question_asked_at).total_seconds()
        self.save()


class AIInterviewResponse(models.Model):
    """
    Represents candidate responses to AI interview questions
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(AIInterviewQuestion, on_delete=models.CASCADE, related_name='responses')
    session = models.ForeignKey(AIInterviewSession, on_delete=models.CASCADE, related_name='responses')
    
    # Response Content
    response_text = models.TextField()
    response_type = models.CharField(max_length=20, default='text', help_text="text, audio, video, code")
    response_data = models.JSONField(default=dict, help_text="Additional response data (audio/video URLs, code files, etc.)")
    
    # Timing
    response_submitted_at = models.DateTimeField(default=timezone.now)
    response_duration = models.PositiveIntegerField(default=0, help_text="Time taken to respond in seconds")
    
    # AI Evaluation
    ai_evaluation = models.JSONField(default=dict, help_text="AI evaluation of the response")
    ai_score = models.FloatField(null=True, blank=True, help_text="AI score for this response (0-100)")
    ai_feedback = models.TextField(blank=True, help_text="AI feedback on the response")
    
    # Quality Metrics
    response_length = models.PositiveIntegerField(default=0, help_text="Length of response in characters")
    confidence_score = models.FloatField(null=True, blank=True, help_text="AI confidence in evaluation")
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ai_interview_response'
        indexes = [
            models.Index(fields=['session', 'response_submitted_at']),
            models.Index(fields=['question', 'response_submitted_at']),
        ]

    def __str__(self):
        return f"Response to Q{self.question.question_index}: {self.response_text[:50]}..."

    def save(self, *args, **kwargs):
        # Auto-calculate response length
        if self.response_text:
            self.response_length = len(self.response_text)
        super().save(*args, **kwargs)


class AIInterviewResult(models.Model):
    """
    Represents the final results of an AI interview session
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.OneToOneField(AIInterviewSession, on_delete=models.CASCADE, related_name='result')
    interview = models.OneToOneField(Interview, on_delete=models.CASCADE, related_name='ai_result')
    
    # Overall Scores
    total_score = models.FloatField(default=0.0, help_text="Overall interview score (0-100)")
    technical_score = models.FloatField(default=0.0, help_text="Technical questions score (0-100)")
    behavioral_score = models.FloatField(default=0.0, help_text="Behavioral questions score (0-100)")
    coding_score = models.FloatField(default=0.0, help_text="Coding questions score (0-100)")
    
    # Performance Metrics
    questions_attempted = models.PositiveIntegerField(default=0)
    questions_correct = models.PositiveIntegerField(default=0)
    average_response_time = models.FloatField(default=0.0, help_text="Average response time in seconds")
    completion_time = models.PositiveIntegerField(default=0, help_text="Total completion time in seconds")
    
    # AI Analysis
    ai_summary = models.TextField(blank=True, help_text="AI-generated interview summary")
    ai_recommendations = models.TextField(blank=True, help_text="AI recommendations")
    strengths = models.JSONField(default=list, help_text="Candidate strengths identified")
    weaknesses = models.JSONField(default=list, help_text="Areas for improvement")
    
    # Evaluation
    overall_rating = models.CharField(max_length=20, default='pending', help_text="excellent, good, average, poor, pending")
    hire_recommendation = models.BooleanField(null=True, blank=True, help_text="AI recommendation to hire")
    confidence_level = models.FloatField(default=0.0, help_text="AI confidence in evaluation (0-100)")
    
    # Human Review
    human_reviewer = models.ForeignKey('authapp.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='ai_interview_reviews')
    human_rating = models.CharField(max_length=20, blank=True, help_text="Human reviewer rating")
    human_feedback = models.TextField(blank=True, help_text="Human reviewer feedback")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ai_interview_result'
        indexes = [
            models.Index(fields=['total_score', 'overall_rating']),
            models.Index(fields=['interview', 'overall_rating']),
        ]

    def __str__(self):
        return f"AI Result - {self.interview.candidate.full_name} (Score: {self.total_score})"

    @property
    def accuracy_percentage(self):
        if self.questions_attempted > 0:
            return (self.questions_correct / self.questions_attempted) * 100
        return 0

    @property
    def is_recommended_for_hire(self):
        return self.hire_recommendation is True

    def calculate_scores(self):
        """Calculate scores based on question responses"""
        questions = self.session.questions.all()
        if not questions:
            return
        
        total_score = 0
        technical_score = 0
        behavioral_score = 0
        coding_score = 0
        technical_count = 0
        behavioral_count = 0
        coding_count = 0
        
        for question in questions:
            if question.score is not None:
                total_score += question.score
                
                if question.question_type == 'technical':
                    technical_score += question.score
                    technical_count += 1
                elif question.question_type == 'behavioral':
                    behavioral_score += question.score
                    behavioral_count += 1
                elif question.question_type == 'coding':
                    coding_score += question.score
                    coding_count += 1
        
        # Calculate averages
        if questions.count() > 0:
            self.total_score = total_score / questions.count()
        
        if technical_count > 0:
            self.technical_score = technical_score / technical_count
        
        if behavioral_count > 0:
            self.behavioral_score = behavioral_score / behavioral_count
        
        if coding_count > 0:
            self.coding_score = coding_score / coding_count
        
        self.save()
