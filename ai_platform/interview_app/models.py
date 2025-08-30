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
    
    # Video recording fields
    recording_video = models.FileField(upload_to='interview_recordings/', null=True, blank=True, help_text="Recorded video of the interview session")
    recording_created_at = models.DateTimeField(null=True, blank=True, help_text="When the recording was created")

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

    # --- NEW FIELD: To specify the language for a coding question ---
    LANGUAGE_CHOICES = [
        ('PYTHON', 'Python'),
        ('JAVASCRIPT', 'JavaScript'),
        ('JAVA', 'Java'),
        ('CSHARP', 'C#'),
        ('PHP', 'PHP'),
        ('RUBY', 'Ruby'),
        ('SQL', 'SQL'),
    ]
    coding_language = models.CharField(
        max_length=20,
        choices=LANGUAGE_CHOICES,
        null=True, # Important: Allow this to be null for non-coding questions
        blank=True
    )

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
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Code submission by {self.session.candidate_name} for Q: {self.question_id}"