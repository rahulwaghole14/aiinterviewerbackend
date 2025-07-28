from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from .models import Evaluation, Feedback
from .serializers import EvaluationSerializer, EvaluationReportSerializer, FeedbackSerializer

class EvaluationSummaryView(APIView):
    def get(self, request, interview_id):
        try:
            evaluation = Evaluation.objects.get(interview_id=interview_id)
        except Evaluation.DoesNotExist:
            return Response({"error": "Evaluation not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = EvaluationSerializer(evaluation)
        return Response(serializer.data)

class EvaluationReportView(APIView):
    def get(self, request, interview_id):
        try:
            evaluation = Evaluation.objects.get(interview_id=interview_id)
        except Evaluation.DoesNotExist:
            return Response({"error": "Evaluation not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = EvaluationReportSerializer(evaluation)
        return Response(serializer.data)

class SubmitFeedbackView(generics.CreateAPIView):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer

class AllFeedbacksView(generics.ListAPIView):
    serializer_class = FeedbackSerializer

    def get_queryset(self):
        candidate_id = self.kwargs.get("candidate_id")
        return Feedback.objects.filter(candidate_id=candidate_id).order_by("-submitted_at")
