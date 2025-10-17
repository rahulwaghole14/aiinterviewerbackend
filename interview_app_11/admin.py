from django.contrib import admin
from .models import InterviewSession, InterviewQuestion, WarningLog, TestCase, CodeSubmission

@admin.register(InterviewSession)
class InterviewSessionAdmin(admin.ModelAdmin):
    list_display = (
        'session_key', 
        'candidate_name', 
        'candidate_email', 
        'status', 
        'scheduled_at', 
        'created_at',
        'is_evaluated'
    )
    list_filter = ('status', 'is_evaluated', 'created_at', 'scheduled_at')
    search_fields = ('session_key', 'candidate_name', 'candidate_email')
    readonly_fields = ('session_key', 'created_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Session Information', {
            'fields': ('session_key', 'status', 'scheduled_at', 'created_at')
        }),
        ('Candidate Information', {
            'fields': ('candidate_name', 'candidate_email', 'language_code', 'accent_tld')
        }),
        ('Interview Content', {
            'fields': ('job_description', 'resume_text', 'resume_summary'),
            'classes': ('collapse',)
        }),
        ('Evaluation Results', {
            'fields': (
                'is_evaluated', 'answers_feedback', 'answers_score', 
                'resume_feedback', 'resume_score', 'keyword_analysis',
                'overall_performance_feedback', 'overall_performance_score',
                'behavioral_analysis'
            ),
            'classes': ('collapse',)
        }),
        ('ID Verification', {
            'fields': ('id_verification_status', 'id_card_image', 'extracted_id_details'),
            'classes': ('collapse',)
        }),
    )

@admin.register(InterviewQuestion)
class InterviewQuestionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'session', 
        'question_type', 
        'question_level', 
        'order', 
        'coding_language'
    )
    list_filter = ('question_type', 'question_level', 'coding_language', 'order')
    search_fields = ('question_text', 'session__candidate_name')
    ordering = ('session', 'order')
    
    fieldsets = (
        ('Question Information', {
            'fields': ('session', 'question_text', 'question_type', 'question_level', 'order')
        }),
        ('Coding Question Details', {
            'fields': ('coding_language',),
            'classes': ('collapse',)
        }),
        ('Audio and Response', {
            'fields': ('audio_url', 'transcribed_answer', 'response_time_seconds'),
            'classes': ('collapse',)
        }),
        ('Analysis', {
            'fields': ('words_per_minute', 'filler_word_count'),
            'classes': ('collapse',)
        }),
        ('Question Hierarchy', {
            'fields': ('parent_question',),
            'classes': ('collapse',)
        }),
    )

@admin.register(WarningLog)
class WarningLogAdmin(admin.ModelAdmin):
    list_display = ('session', 'warning_type', 'timestamp')
    list_filter = ('warning_type', 'timestamp')
    search_fields = ('session__candidate_name',)
    ordering = ('-timestamp',)

@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    list_display = ('question', 'input_data', 'expected_output', 'is_hidden')
    list_filter = ('is_hidden',)
    search_fields = ('question__question_text', 'input_data', 'expected_output')

@admin.register(CodeSubmission)
class CodeSubmissionAdmin(admin.ModelAdmin):
    list_display = ('session', 'question_id', 'submitted_code', 'passed_all_tests', 'created_at')
    list_filter = ('passed_all_tests', 'created_at')
    search_fields = ('session__candidate_name', 'submitted_code')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Submission Information', {
            'fields': ('session', 'question_id', 'created_at')
        }),
        ('Code and Results', {
            'fields': ('submitted_code', 'language', 'passed_all_tests', 'output_log')
        }),
    )
