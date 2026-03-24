"""
Voice Analysis Models for Interview App
Contains models for voice activity detection, speaker diarization, and answer voice analysis
"""

import uuid
from django.db import models
from django.utils import timezone


class VoiceActivityDetection(models.Model):
    """
    Stores voice activity detection results for interview sessions and questions
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey('InterviewSession', on_delete=models.CASCADE, related_name='voice_activities')
    question = models.ForeignKey('InterviewQuestion', on_delete=models.CASCADE, null=True, blank=True, related_name='voice_activities')
    
    # VAD metrics
    pause_duration = models.FloatField(help_text="Total pause duration in seconds")
    total_speech_time = models.FloatField(help_text="Total speech time in seconds")
    speech_percentage = models.FloatField(help_text="Percentage of time spent speaking")
    silence_percentage = models.FloatField(help_text="Percentage of time spent in silence")
    
    # Response timing
    response_delay_start = models.DateTimeField(null=True, blank=True, help_text="When question ended")
    response_delay_end = models.DateTimeField(null=True, blank=True, help_text="When candidate started responding")
    response_delay_seconds = models.FloatField(null=True, blank=True, help_text="Response delay in seconds")
    
    # Raw VAD segments data
    vad_segments = models.JSONField(default=list, help_text="Raw VAD segment data")
    
    # Analysis timestamps
    analysis_start_time = models.DateTimeField(auto_now_add=True)
    analysis_end_time = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['analysis_start_time']
        indexes = [
            models.Index(fields=['session', 'question']),
            models.Index(fields=['analysis_start_time']),
        ]
    
    def __str__(self):
        question_info = f"Q{self.question.order}" if self.question else "Overall"
        return f"VAD - {self.session.candidate_name} ({question_info})"


class SpeakerDiarization(models.Model):
    """
    Stores speaker diarization results for interview sessions and questions
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey('InterviewSession', on_delete=models.CASCADE, related_name='speaker_diarizations')
    question = models.ForeignKey('InterviewQuestion', on_delete=models.CASCADE, null=True, blank=True, related_name='speaker_diarizations')
    
    # Speaker metrics
    speaker_changes = models.IntegerField(help_text="Number of speaker changes detected")
    speaker_change_timestamps = models.JSONField(default=list, help_text="Timestamps when speaker changes occurred")
    num_speakers = models.IntegerField(help_text="Number of distinct speakers detected")
    speaker_labels = models.JSONField(default=dict, help_text="Speaker label information")
    candidate_speech_percentage = models.FloatField(help_text="Percentage of time candidate spoke")
    interviewer_speech_percentage = models.FloatField(help_text="Percentage of time interviewer spoke")
    
    # Diarization segments
    diarization_segments = models.JSONField(default=list, help_text="Raw diarization segment data")
    
    # Analysis timestamps
    analysis_start_time = models.DateTimeField(auto_now_add=True)
    analysis_end_time = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['analysis_start_time']
        indexes = [
            models.Index(fields=['session', 'question']),
            models.Index(fields=['analysis_start_time']),
        ]
    
    def __str__(self):
        question_info = f"Q{self.question.order}" if self.question else "Overall"
        return f"Speaker Diarization - {self.session.candidate_name} ({question_info})"


class AnswerVoiceAnalysis(models.Model):
    """
    Stores detailed voice analysis for individual answers
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey('InterviewSession', on_delete=models.CASCADE, related_name='answer_analyses')
    question = models.ForeignKey('InterviewQuestion', on_delete=models.CASCADE, null=True, blank=True, related_name='answer_analyses')
    
    # Answer identification
    answer_number = models.IntegerField(help_text="Answer number in the interview")
    
    # Timing metrics
    segment_start_time = models.FloatField(help_text="Start time of answer segment in seconds")
    segment_end_time = models.FloatField(help_text="End time of answer segment in seconds")
    segment_duration = models.FloatField(help_text="Duration of answer segment in seconds")
    
    # Speech quality metrics
    speech_percentage = models.FloatField(help_text="Percentage of segment with speech")
    silence_percentage = models.FloatField(help_text="Percentage of segment with silence")
    words_per_minute = models.FloatField(help_text="Speaking rate in words per minute")
    filler_word_count = models.IntegerField(help_text="Number of filler words detected")
    response_delay_seconds = models.FloatField(help_text="Delay before starting response")
    
    # Speaker analysis
    multiple_speakers_detected = models.BooleanField(default=False, help_text="Multiple speakers detected in answer")
    speaker_confidence_score = models.FloatField(help_text="Confidence score for speaker identification")
    audio_quality_score = models.FloatField(help_text="Overall audio quality score")
    
    # Analysis insights (JSON)
    insights = models.JSONField(default=dict, help_text="Detailed insights about the answer")
    
    # Analysis timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['answer_number']
        indexes = [
            models.Index(fields=['session', 'answer_number']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Answer Analysis - {self.session.candidate_name} (Answer {self.answer_number})"
