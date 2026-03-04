import uuid
from django.db import models
from django.utils import timezone

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
    video_gcs_url = models.URLField(max_length=500, null=True, blank=True, help_text="Google Cloud Storage URL for the interview video")
    screen_recording = models.FileField(upload_to='screen_recordings/', null=True, blank=True, help_text="Screen recording of the candidate during the interview")
    screen_recording_gcs_url = models.URLField(max_length=500, null=True, blank=True, help_text="Google Cloud Storage URL for the screen recording")
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
    
    # --- MODIFIED FIELD: Added 'CODING' choice ---
    QUESTION_TYPE_CHOICES = [
        ('TECHNICAL', 'Technical'),
        ('BEHAVIORAL', 'Behavioral'),
        ('CODING', 'Coding Challenge')
    ]
    question_type = models.CharField(max_length=50, choices=QUESTION_TYPE_CHOICES, default='TECHNICAL')
    
    audio_url = models.URLField(max_length=500, null=True, blank=True)
    question_level = models.CharField(max_length=10, default='MAIN')
    parent_question = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='follow_ups')
    transcribed_answer = models.TextField(null=True, blank=True)
    order = models.PositiveIntegerField()
    words_per_minute = models.IntegerField(null=True, blank=True)
    filler_word_count = models.IntegerField(null=True, blank=True)
    response_time_seconds = models.FloatField(null=True, blank=True)

    # --- NEW FIELDS: For conversation sequence tracking ---
    # conversation_sequence: Sequential index for conversation flow (0, 1, 2, 3...)
    # AI responses get odd sequences (1, 3, 5...), Interviewee responses get even sequences (2, 4, 6...)
    conversation_sequence = models.PositiveIntegerField(null=True, blank=True, help_text="Sequential index for conversation flow")
    # role: 'AI' for AI-generated content, 'INTERVIEWEE' for candidate responses
    role = models.CharField(max_length=20, null=True, blank=True, help_text="Role: AI or INTERVIEWEE")

    # --- NEW FIELD: To specify the language for a coding question ---
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
        ('SWIFT', 'Swift'),  # Added 'SWIFT' to LANGUAGE_CHOICES
    ]
    coding_language = models.CharField(
        max_length=20,
        choices=LANGUAGE_CHOICES,
        null=True, # Important: Allow this to be null for non-coding questions
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Q{self.order + 1} ({self.question_level}) for {self.session.candidate_name}"

# --- NEW MODEL: For storing test cases for coding questions ---
class TestCase(models.Model):
    question = models.ForeignKey(InterviewQuestion, related_name='test_cases', on_delete=models.CASCADE, to_field='id')
    input_data = models.TextField(help_text="Input for the function, e.g., '5' for factorial(5)")
    expected_output = models.TextField(help_text="Expected result, e.g., '120'")
    is_hidden = models.BooleanField(default=False, help_text="Hidden tests are not shown to the candidate but are used for final scoring.")

    def __str__(self):
        return f"Test case for Q: {self.question.id}"

# --- NEW MODEL: For storing a candidate's code submission ---
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

# --- NEW MODEL: For storing separate question answer for technical interview ---
class TechnicalInterviewQA(models.Model):
    session = models.ForeignKey(InterviewSession, related_name='technical_qa', on_delete=models.CASCADE)
    overall_qa = models.TextField(help_text="Stores the full QA interaction in a single continuous format: 'AI Interviewer: <Q> | Interviewee: <A>'")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"QA for {self.session.id} - {self.created_at}"

# --- COMPREHENSIVE Q&A CONVERSATION MODEL ---
class QAConversationPair(models.Model):
    """Model to save all question-answer pairs during interview"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(InterviewSession, related_name='qa_conversation_pairs', on_delete=models.CASCADE)
    session_key = models.CharField(max_length=255, db_index=True, null=True, blank=True, help_text="Session key for easy identification and filtering")
    question_text = models.TextField(help_text="Question asked by AI (introductory, technical, follow-up, or clarification)")
    answer_text = models.TextField(help_text="Answer given by candidate or question asked by candidate")
    question_type = models.CharField(max_length=20, choices=[
        ('INTRODUCTORY', 'Introductory'),
        ('TECHNICAL', 'Technical'),
        ('FOLLOW_UP', 'Follow-up'),
        ('CLARIFICATION', 'Clarification'),
        ('CANDIDATE_QUESTION', 'Candidate Question'),
        ('ELABORATION_REQUEST', 'Elaboration Request'),
    ], default='TECHNICAL')
    question_number = models.IntegerField(help_text="Sequential number of the question in the interview (positive for AI questions, negative for candidate questions)")
    timestamp = models.DateTimeField(auto_now_add=True)
    response_time_seconds = models.FloatField(null=True, blank=True, help_text="Time taken to respond in seconds")
    words_per_minute = models.FloatField(null=True, blank=True, help_text="Speaking rate calculated from answer")
    filler_word_count = models.PositiveIntegerField(default=0, help_text="Count of filler words in answer")
    sentiment_score = models.FloatField(null=True, blank=True, help_text="Sentiment analysis score of the answer")
    
    # LLM Analysis fields
    llm_analysis = models.TextField(null=True, blank=True, help_text="Gemini analysis of this Q&A pair")
    llm_score = models.FloatField(null=True, blank=True, help_text="Score given by LLM for this Q&A")
    analysis_timestamp = models.DateTimeField(null=True, blank=True, help_text="When LLM analysis was performed")
    
    # PDF generation flags
    included_in_pdf = models.BooleanField(default=True, help_text="Whether this Q&A should be included in PDF report")
    pdf_display_order = models.PositiveIntegerField(default=0, help_text="Order for displaying in PDF")
    
    class Meta:
        ordering = ['question_number', 'timestamp']
        indexes = [
            models.Index(fields=['session', 'question_number']),
            models.Index(fields=['session', 'question_type']),
            models.Index(fields=['session_key']),  # Add index for session_key
        ]
    
    def __str__(self):
        return f"Q{self.question_number}: {self.question_text[:50]}... - {self.session.candidate_name} ({self.session_key})"