from rest_framework import serializers
from .models import Evaluation, Feedback


class EvaluationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evaluation
        fields = ["id", "interview", "overall_score", "traits", "created_at"]
        read_only_fields = ["id", "created_at"]


class EvaluationReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evaluation
        fields = [
            "id",
            "interview",
            "overall_score",
            "traits",
            "suggestions",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class EvaluationCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating evaluations
    """

    class Meta:
        model = Evaluation
        fields = [
            "id",
            "interview",
            "overall_score",
            "traits",
            "suggestions",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
        extra_kwargs = {"interview": {"required": False}}

    def validate_overall_score(self, value):
        """Validate overall score is between 0 and 10"""
        if value < 0 or value > 10:
            raise serializers.ValidationError("Overall score must be between 0 and 10.")
        return value

    def validate_interview(self, value):
        """Validate that the interview exists and is completed"""
        if value.status != "completed":
            raise serializers.ValidationError(
                "Evaluation can only be created for completed interviews."
            )
        return value

    def validate(self, data):
        """Additional validation for the entire evaluation"""
        # Check if evaluation already exists for this interview
        interview = data.get("interview")
        if interview:
            existing_evaluation = Evaluation.objects.filter(interview=interview).first()
            if self.instance:  # Update operation
                if existing_evaluation and existing_evaluation.id != self.instance.id:
                    raise serializers.ValidationError(
                        "An evaluation already exists for this interview."
                    )
            else:  # Create operation
                if existing_evaluation:
                    raise serializers.ValidationError(
                        "An evaluation already exists for this interview."
                    )

        return data


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = [
            "id",
            "candidate",
            "interview",
            "reviewer_name",
            "comments",
            "submitted_at",
        ]
        read_only_fields = ["id", "submitted_at"]
