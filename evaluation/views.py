from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Evaluation, Feedback
from .serializers import EvaluationSerializer, EvaluationReportSerializer, FeedbackSerializer, EvaluationCreateUpdateSerializer
from utils.hierarchy_permissions import DataIsolationMixin
from utils.logger import ActionLogger

class EvaluationViewSet(DataIsolationMixin, ModelViewSet):
    """
    Full CRUD operations for evaluations
    """
    queryset = Evaluation.objects.select_related('interview', 'interview__candidate')
    serializer_class = EvaluationCreateUpdateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Apply data isolation based on user role"""
        queryset = super().get_queryset()
        
        # Admin users can see all evaluations
        if getattr(self.request.user, "role", "").lower() == "admin" or self.request.user.is_superuser:
            return queryset
        
        # Non-admin users see only evaluations for their candidates
        return queryset.filter(interview__candidate__recruiter=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Create a new evaluation"""
        try:
            response = super().create(request, *args, **kwargs)
            
            if response.status_code == 201:
                # Log successful evaluation creation
                ActionLogger.log_user_action(
                    user=request.user,
                    action='evaluation_create',
                    details={
                        'evaluation_id': response.data.get('id'),
                        'interview_id': response.data.get('interview'),
                        'overall_score': response.data.get('overall_score')
                    },
                    status='SUCCESS'
                )
            
            return response
            
        except Exception as e:
            # Log evaluation creation failure
            ActionLogger.log_user_action(
                user=request.user,
                action='evaluation_create',
                details={'error': str(e)},
                status='FAILED'
            )
            raise
    
    def update(self, request, *args, **kwargs):
        """Update an evaluation"""
        try:
            response = super().update(request, *args, **kwargs)
            
            if response.status_code == 200:
                # Log successful evaluation update
                ActionLogger.log_user_action(
                    user=request.user,
                    action='evaluation_update',
                    details={
                        'evaluation_id': response.data.get('id'),
                        'interview_id': response.data.get('interview'),
                        'overall_score': response.data.get('overall_score')
                    },
                    status='SUCCESS'
                )
            
            return response
            
        except Exception as e:
            # Log evaluation update failure
            ActionLogger.log_user_action(
                user=request.user,
                action='evaluation_update',
                details={'error': str(e)},
                status='FAILED'
            )
            raise
    
    def destroy(self, request, *args, **kwargs):
        """Delete an evaluation"""
        try:
            evaluation = self.get_object()
            evaluation_id = evaluation.id
            interview_id = evaluation.interview.id
            
            response = super().destroy(request, *args, **kwargs)
            
            if response.status_code == 204:
                # Log successful evaluation deletion
                ActionLogger.log_user_action(
                    user=request.user,
                    action='evaluation_delete',
                    details={
                        'evaluation_id': evaluation_id,
                        'interview_id': interview_id
                    },
                    status='SUCCESS'
                )
            
            return response
            
        except Exception as e:
            # Log evaluation deletion failure
            ActionLogger.log_user_action(
                user=request.user,
                action='evaluation_delete',
                details={'error': str(e)},
                status='FAILED'
            )
            raise

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
