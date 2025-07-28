from rest_framework import serializers
from .models import Evaluation, Feedback

class EvaluationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evaluation
        fields = ['interview', 'overall_score', 'traits']

class EvaluationReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evaluation
        fields = ['interview', 'overall_score', 'traits', 'suggestions', 'created_at']

class FeedbackSerializer(serializers.ModelSerializer):
    reviewer = serializers.CharField(source='reviewer_name')
    feedback_text = serializers.CharField(source='comments')
    created_at = serializers.DateTimeField(source='submitted_at', read_only=True)

    class Meta:
        model = Feedback
        fields = ['id', 'interview', 'reviewer', 'feedback_text', 'created_at']
