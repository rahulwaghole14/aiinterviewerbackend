import uuid
from django.db import models

class InterviewSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_key = models.CharField(max_length=40, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    candidate_name = models.CharField(max_length=100, default="N/A")
    candidate_email = models.EmailField(null=True, blank=True)
    job_description = models.TextField(null=True, blank=True)
    resume_text = models.TextField(null=True, blank=True)
    STATUS_CHOICES = [('SCHEDULED', 'Scheduled'), ('COMPLETED', 'Completed'), ('EXPIRED', 'Expired')]
    scheduled_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    language_code = models.CharField(max_length=10, default='en')
    accent_tld = models.CharField(max_length=10, default='com')
    is_evaluated = models.BooleanField(default=False)
    resume_summary = models.TextField(null=True, blank=True)
    answers_feedback = models.TextField(null=True, blank=True)
    answers_score = models.FloatField(null=True, blank=True)
    resume_feedback = models.TextField(null=True, blank=True)
    resume_score = models.FloatField(null=True, blank=True)
    keyword_analysis = models.TextField(null=True, blank=True)
    overall_performance_feedback = models.TextField(null=True, blank=True)
    overall_performance_score = models.FloatField(null=True, blank=True)
    behavioral_analysis = models.TextField(null=True, blank=True)
    id_verification_status = models.CharField(max_length=50, default='Pending')
    id_card_image = models.ImageField(upload_to='id_cards/', null=True, blank=True)
    extracted_id_details = models.TextField(null=True, blank=True)
    interview_video = models.FileField(upload_to='interview_videos/', null=True, blank=True, help_text="Complete interview video with camera, TTS questions, and candidate speech")
    technical_interview_started_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when technical interview started")
    coding_round_completed_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when coding round was completed")
    total_completion_time_minutes = models.FloatField(null=True, blank=True, help_text="Total time from technical interview start to coding round completion (in minutes)")

    def save(self, *args, **kwargs):
        if not self.session_key:
            self.session_key = uuid.uuid4().hex
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Interview for {self.candidate_name} on {self.created_at.strftime('%Y-%m-%d')}"

class WarningLog(models.Model):
    session = models.ForeignKey(InterviewSession, related_name='logs', on_delete=models.CASCADE)
    warning_type = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)
    snapshot = models.CharField(max_length=255, null=True, blank=True, help_text="Filename of the snapshot image captured when warning occurred")
    snapshot_image = models.ImageField(upload_to='proctoring_snaps/', null=True, blank=True, help_text="Snapshot image stored in database")

    def __str__(self):
        return f"Warning ({self.warning_type}) for {self.session.candidate_name}"

class InterviewQuestion(models.Model):
    session = models.ForeignKey(InterviewSession, related_name='questions', on_delete=models.CASCADE)
    question_text = models.TextField()
    
    QUESTION_TYPE_CHOICES = [
        ('INTRODUCTION', 'Introduction'),
        ('TECHNICAL', 'Technical'),
        ('BEHAVIORAL', 'Behavioral'),
        ('CODING', 'Coding Challenge'),
        ('PRECLOSING', 'Pre-closing'),
        ('CLOSING', 'Closing'),
    ]
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES, default='TECHNICAL')
    
    QUESTION_LEVEL_CHOICES = [
        ('INTRO', 'Introduction'),
        ('MAIN', 'Main'),
        ('FOLLOWUP', 'Follow-up'),
        ('PRECLOSE', 'Pre-close'),
        ('CLOSE', 'Close'),
    ]
    question_level = models.CharField(max_length=10, choices=QUESTION_LEVEL_CHOICES, default='MAIN')
    
    audio_url = models.URLField(max_length=500, null=True, blank=True)
    
    parent_question = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='follow_ups')
    
    transcribed_answer = models.TextField(null=True, blank=True, help_text="Transcribed answer from interviewee")
    
    order = models.PositiveIntegerField(help_text="Question order in the interview")
    conversation_sequence = models.PositiveIntegerField(null=True, blank=True, help_text="Sequential index for conversation flow")
    
    words_per_minute = models.IntegerField(null=True, blank=True)
    filler_word_count = models.IntegerField(null=True, blank=True)
    response_time_seconds = models.FloatField(null=True, blank=True)
    
    ROLE_CHOICES = [
        ('AI', 'AI Interviewer'),
        ('INTERVIEWEE', 'Interviewee'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='AI', help_text="Role: AI or INTERVIEWEE")
    
    LANGUAGE_CHOICES = [
        ('PYTHON', 'Python'),
        ('JAVASCRIPT', 'JavaScript'),
        ('JAVA', 'Java'),
        ('C', 'C'),
        ('CPP', 'C++'),
        ('GO', 'Go'),
        ('HTML', 'HTML'),
        ('PHP', 'PHP'),
        ('RUBY', 'Ruby'),
        ('CSHARP', 'C#'),
        ('SQL', 'SQL'),
    ]
    coding_language = models.CharField(
        max_length=20,
        choices=LANGUAGE_CHOICES,
        null=True,
        blank=True,
        help_text="Programming language for coding questions"
    )
    
    asked_at = models.DateTimeField(null=True, blank=True, help_text="When the question was asked")
    answered_at = models.DateTimeField(null=True, blank=True, help_text="When the answer was received")
    
    is_follow_up = models.BooleanField(default=False, help_text="Whether this is a follow-up question")
    question_category = models.CharField(max_length=50, null=True, blank=True, help_text="Category of the question (e.g., 'algorithms', 'communication')")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'conversation_sequence']
        indexes = [
            models.Index(fields=['session', 'order']),
            models.Index(fields=['session', 'question_type']),
            models.Index(fields=['conversation_sequence']),
        ]

    def save(self, *args, **kwargs):
        if self.conversation_sequence is None:
            last_question = InterviewQuestion.objects.filter(session=self.session).order_by('-conversation_sequence').first()
            if last_question:
                self.conversation_sequence = last_question.conversation_sequence + 1
            else:
                self.conversation_sequence = 1
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Q{self.order + 1} ({self.question_type}) for {self.session.candidate_name}"

class TestCase(models.Model):
    question = models.ForeignKey(InterviewQuestion, related_name='test_cases', on_delete=models.CASCADE, to_field='id')
    input_data = models.TextField(help_text="Input for the function, e.g., '5' for factorial(5)")
    expected_output = models.TextField(help_text="Expected result, e.g., '120'")
    is_hidden = models.BooleanField(default=False, help_text="Hidden tests are not shown to the candidate but are used for final scoring.")

    def __str__(self):
        return f"Test case for Q: {self.question.id}"

class InterviewQA(models.Model):
    """
    Simplified model for storing interview questions and answers in the same record.
    Each record contains one question and its corresponding answer.
    """
    session = models.ForeignKey(InterviewSession, related_name='qa_pairs', on_delete=models.CASCADE)
    question_number = models.PositiveIntegerField(help_text="Sequential question number (1, 2, 3...)")
    question_text = models.TextField(help_text="The question asked by AI")
    answer_text = models.TextField(null=True, blank=True, help_text="Candidate's answer to the question")
    question_type = models.CharField(max_length=20, default='TECHNICAL', 
        choices=[('INTRODUCTION', 'Introduction'), ('TECHNICAL', 'Technical'), 
                ('BEHAVIORAL', 'Behavioral'), ('CODING', 'Coding'),
                ('CLOSING', 'Closing')])
    audio_url = models.URLField(max_length=500, null=True, blank=True, help_text="Audio file for the question")
    asked_at = models.DateTimeField(null=True, blank=True, help_text="When question was asked")
    answered_at = models.DateTimeField(null=True, blank=True, help_text="When answer was received")
    response_time_seconds = models.FloatField(null=True, blank=True, help_text="Time taken to answer in seconds")
    words_per_minute = models.IntegerField(null=True, blank=True, help_text="Speaking rate calculation")
    filler_word_count = models.IntegerField(null=True, blank=True, help_text="Filler words detected")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['question_number']
        indexes = [
            models.Index(fields=['session', 'question_number']),
        ]
    
    def __str__(self):
        return f"Q{self.question_number} for {self.session.candidate_name}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate response time if both timestamps are available
        if self.asked_at and self.answered_at:
            time_diff = self.answered_at - self.asked_at
            self.response_time_seconds = time_diff.total_seconds()
        
        # Auto-calculate words per minute if answer and response time available
        if self.answer_text and self.response_time_seconds and self.response_time_seconds > 0:
            word_count = len(self.answer_text.split())
            minutes = self.response_time_seconds / 60
            if minutes > 0:
                self.words_per_minute = int(word_count / minutes)
        
        super().save(*args, **kwargs)

class CodeSubmission(models.Model):
    session = models.ForeignKey(InterviewSession, related_name='code_submissions', on_delete=models.CASCADE)
    question_id = models.CharField(max_length=36, help_text="Question ID (can be UUID or integer)")
    submitted_code = models.TextField()
    language = models.CharField(max_length=20, default='PYTHON')
    passed_all_tests = models.BooleanField(default=False)
    output_log = models.TextField(null=True, blank=True, help_text="Stores the results of running against all test cases.")
    gemini_evaluation = models.JSONField(null=True, blank=True, help_text="Stores Gemini API evaluation results")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Code submission by {self.session.candidate_name} for Q: {self.question_id}"