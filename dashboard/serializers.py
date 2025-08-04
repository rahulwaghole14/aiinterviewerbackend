from rest_framework import serializers
from .models import (
    DashboardMetric, UserActivity, DashboardWidget, SystemPerformance,
    DashboardAnalytics
)

class DashboardMetricSerializer(serializers.ModelSerializer):
    metric_type_display = serializers.CharField(source='get_metric_type_display', read_only=True)
    
    class Meta:
        model = DashboardMetric
        fields = [
            'id', 'metric_type', 'metric_type_display', 'user', 'company_name',
            'value', 'data', 'date', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class UserActivitySerializer(serializers.ModelSerializer):
    activity_type_display = serializers.CharField(source='get_activity_type_display', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = UserActivity
        fields = [
            'id', 'user', 'user_email', 'activity_type', 'activity_type_display',
            'details', 'ip_address', 'user_agent', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class DashboardWidgetSerializer(serializers.ModelSerializer):
    widget_type_display = serializers.CharField(source='get_widget_type_display', read_only=True)
    
    class Meta:
        model = DashboardWidget
        fields = [
            'id', 'user', 'widget_type', 'widget_type_display', 'position',
            'is_enabled', 'settings', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class SystemPerformanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemPerformance
        fields = [
            'id', 'metric_name', 'value', 'unit', 'timestamp', 'metadata'
        ]
        read_only_fields = ['id', 'timestamp']

class DashboardDataSerializer(serializers.Serializer):
    """Serializer for comprehensive dashboard data"""
    resume_stats = serializers.DictField()
    interview_stats = serializers.DictField()
    candidate_stats = serializers.DictField()
    job_stats = serializers.DictField()
    activity_data = serializers.DictField()
    performance_data = serializers.DictField()
    date_range = serializers.DictField()

class ResumeStatsSerializer(serializers.Serializer):
    """Serializer for resume statistics"""
    total_uploads = serializers.IntegerField()
    successful_uploads = serializers.IntegerField()
    failed_uploads = serializers.IntegerField()
    success_rate = serializers.FloatField()
    daily_trend = serializers.ListField()
    recent_uploads = serializers.ListField()

class InterviewStatsSerializer(serializers.Serializer):
    """Serializer for interview statistics"""
    total_interviews = serializers.IntegerField()
    scheduled_interviews = serializers.IntegerField()
    completed_interviews = serializers.IntegerField()
    cancelled_interviews = serializers.IntegerField()
    completion_rate = serializers.FloatField()
    daily_trend = serializers.ListField()
    upcoming_interviews = serializers.ListField()

class CandidateStatsSerializer(serializers.Serializer):
    """Serializer for candidate statistics"""
    total_candidates = serializers.IntegerField()
    active_candidates = serializers.IntegerField()
    interviewed_candidates = serializers.IntegerField()
    hired_candidates = serializers.IntegerField()
    hiring_rate = serializers.FloatField()
    domain_distribution = serializers.ListField()
    recent_candidates = serializers.ListField()

class JobStatsSerializer(serializers.Serializer):
    """Serializer for job statistics"""
    total_jobs = serializers.IntegerField()
    active_jobs = serializers.IntegerField()
    closed_jobs = serializers.IntegerField()
    level_distribution = serializers.ListField()
    recent_jobs = serializers.ListField()

class ActivityDataSerializer(serializers.Serializer):
    """Serializer for activity data"""
    total_activities = serializers.IntegerField()
    activity_distribution = serializers.ListField()
    daily_trend = serializers.ListField()
    recent_activities = serializers.ListField()

class PerformanceDataSerializer(serializers.Serializer):
    """Serializer for performance data"""
    latest_metrics = serializers.DictField()
    performance_trend = serializers.ListField()

class DateRangeSerializer(serializers.Serializer):
    """Serializer for date range"""
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    days = serializers.IntegerField()

class DashboardFilterSerializer(serializers.Serializer):
    """Serializer for dashboard filters"""
    days = serializers.IntegerField(default=30, min_value=1, max_value=365)
    metric_type = serializers.CharField(required=False)
    include_charts = serializers.BooleanField(default=True)
    include_recent = serializers.BooleanField(default=True)

class WidgetSettingsSerializer(serializers.Serializer):
    """Serializer for widget settings"""
    widget_type = serializers.CharField()
    position = serializers.IntegerField(min_value=0)
    is_enabled = serializers.BooleanField()
    settings = serializers.DictField(required=False)

class ActivityFilterSerializer(serializers.Serializer):
    """Serializer for activity filtering"""
    activity_type = serializers.CharField(required=False)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    limit = serializers.IntegerField(default=50, min_value=1, max_value=1000)

class MetricFilterSerializer(serializers.Serializer):
    """Serializer for metric filtering"""
    metric_type = serializers.CharField(required=False)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    company_name = serializers.CharField(required=False)

class DashboardSummarySerializer(serializers.Serializer):
    """Serializer for dashboard summary"""
    total_resumes = serializers.IntegerField()
    total_interviews = serializers.IntegerField()
    total_candidates = serializers.IntegerField()
    total_jobs = serializers.IntegerField()
    total_activities = serializers.IntegerField()
    success_rate = serializers.FloatField()
    completion_rate = serializers.FloatField()
    hiring_rate = serializers.FloatField()

class ChartDataSerializer(serializers.Serializer):
    """Serializer for chart data"""
    labels = serializers.ListField()
    datasets = serializers.ListField()
    options = serializers.DictField(required=False)

class ExportDataSerializer(serializers.Serializer):
    """Serializer for data export"""
    format = serializers.ChoiceField(choices=['json', 'csv', 'xlsx'])
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    include_charts = serializers.BooleanField(default=False)
    include_details = serializers.BooleanField(default=True) 