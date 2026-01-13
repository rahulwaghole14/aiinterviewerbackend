from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Evaluation, Feedback, ProctoringPDF
from .serializers import (
    EvaluationSerializer,
    EvaluationReportSerializer,
    FeedbackSerializer,
    EvaluationCreateUpdateSerializer,
)
from utils.hierarchy_permissions import DataIsolationMixin
from utils.logger import ActionLogger
from interviews.models import Interview


class EvaluationViewSet(DataIsolationMixin, ModelViewSet):
    """
    Full CRUD operations for evaluations

    Query Parameters:
    - candidate_id: Filter evaluations by candidate ID
    """

    queryset = Evaluation.objects.select_related("interview", "interview__candidate")
    serializer_class = EvaluationCreateUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Apply data isolation based on user role and candidate_id filtering"""
        queryset = super().get_queryset()

        # Admin users can see all evaluations
        if (
            getattr(self.request.user, "role", "").lower() == "admin"
            or self.request.user.is_superuser
        ):
            pass  # Admin sees all evaluations
        else:
            # Non-admin users see only evaluations for their candidates
            queryset = queryset.filter(
                interview__candidate__recruiter=self.request.user
            )

        # Apply candidate_id filtering if provided
        candidate_id = self.request.query_params.get("candidate_id")
        if candidate_id:
            try:
                candidate_id = int(candidate_id)
                queryset = queryset.filter(interview__candidate_id=candidate_id)
            except (ValueError, TypeError):
                # If candidate_id is not a valid integer, return empty queryset
                queryset = Evaluation.objects.none()

        return queryset

    def create(self, request, *args, **kwargs):
        """Create a new evaluation"""
        try:
            response = super().create(request, *args, **kwargs)

            if response.status_code == 201:
                # Log successful evaluation creation
                ActionLogger.log_user_action(
                    user=request.user,
                    action="evaluation_create",
                    details={
                        "evaluation_id": response.data.get("id"),
                        "interview_id": response.data.get("interview"),
                        "overall_score": response.data.get("overall_score"),
                    },
                    status="SUCCESS",
                )

            return response

        except Exception as e:
            # Log evaluation creation failure
            ActionLogger.log_user_action(
                user=request.user,
                action="evaluation_create",
                details={"error": str(e)},
                status="FAILED",
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
                    action="evaluation_update",
                    details={
                        "evaluation_id": response.data.get("id"),
                        "interview_id": response.data.get("interview"),
                        "overall_score": response.data.get("overall_score"),
                    },
                    status="SUCCESS",
                )

            return response

        except Exception as e:
            # Log evaluation update failure
            ActionLogger.log_user_action(
                user=request.user,
                action="evaluation_update",
                details={"error": str(e)},
                status="FAILED",
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
                    action="evaluation_delete",
                    details={
                        "evaluation_id": evaluation_id,
                        "interview_id": interview_id,
                    },
                    status="SUCCESS",
                )

            return response

        except Exception as e:
            # Log evaluation deletion failure
            ActionLogger.log_user_action(
                user=request.user,
                action="evaluation_delete",
                details={"error": str(e)},
                status="FAILED",
            )
            raise


class EvaluationSummaryView(APIView):
    def get(self, request, interview_id):
        try:
            evaluation = Evaluation.objects.get(interview_id=interview_id)
        except Evaluation.DoesNotExist:
            return Response(
                {"error": "Evaluation not found."}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = EvaluationSerializer(evaluation)
        return Response(serializer.data)


class EvaluationReportView(APIView):
    def get(self, request, interview_id):
        try:
            evaluation = Evaluation.objects.get(interview_id=interview_id)
        except Evaluation.DoesNotExist:
            return Response(
                {"error": "Evaluation not found."}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = EvaluationReportSerializer(evaluation)
        return Response(serializer.data)


class SubmitFeedbackView(generics.CreateAPIView):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer


class AllFeedbacksView(generics.ListAPIView):
    """
    Get all feedbacks for a candidate

    Query Parameters:
    - candidate_id: Filter feedbacks by candidate ID
    """

    serializer_class = FeedbackSerializer

    def get_queryset(self):
        # Support both URL parameter and query parameter for candidate_id
        candidate_id = self.kwargs.get("candidate_id") or self.request.query_params.get(
            "candidate_id"
        )

        if candidate_id:
            try:
                candidate_id = int(candidate_id)
                return Feedback.objects.filter(candidate_id=candidate_id).order_by(
                    "-submitted_at"
                )
            except (ValueError, TypeError):
                # If candidate_id is not a valid integer, return empty queryset
                return Feedback.objects.none()

        # If no candidate_id provided, return empty queryset
        return Feedback.objects.none()


def clean_proctoring_pdf_url(gcs_url):
    """
    Clean and validate ProctoringPDF GCS URL

    Args:
        gcs_url: Raw URL from database

    Returns:
        Clean GCS URL or None if invalid
    """
    if not gcs_url or not isinstance(gcs_url, str):
        return None

    gcs_url = gcs_url.strip()
    original_url = gcs_url

    # If already a clean GCS URL, return as-is
    if gcs_url.startswith('https://storage.googleapis.com/'):
        return gcs_url

    # Handle the specific malformed pattern: run.apphttps//storage.googleapis.com
    if 'run.apphttps//' in gcs_url and 'storage.googleapis.com' in gcs_url:
        storage_index = gcs_url.find('storage.googleapis.com')
        if storage_index != -1:
            return 'https://' + gcs_url[storage_index:]

    # Handle any app/run domain followed by malformed protocol + storage
    import re
    if re.search(r'\.(app|run|com)https?//?storage\.googleapis\.com', gcs_url):
        storage_index = gcs_url.find('storage.googleapis.com')
        if storage_index != -1:
            return 'https://' + gcs_url[storage_index:]

    # Handle any URL that has storage.googleapis.com but doesn't start with https://
    if 'storage.googleapis.com' in gcs_url and not gcs_url.startswith('https://storage.googleapis.com'):
        storage_index = gcs_url.find('storage.googleapis.com')
        if storage_index != -1:
            return 'https://' + gcs_url[storage_index:]

    # If URL doesn't contain storage.googleapis.com, it's invalid
    if 'storage.googleapis.com' not in gcs_url:
        return None

    return gcs_url


class GetProctoringPDFURLView(APIView):
    """
    Get proctoring PDF GCS URL from ProctoringPDF table for a given interview

    Query Parameters:
    - interview_id: UUID of the interview (optional)
    - session_key: String session key (optional)

    Returns:
    - success: boolean
    - gcs_url: string (clean GCS URL from ProctoringPDF table)
    - interview_id: string (interview ID for verification)
    - proctoring_pdf_id: integer (ProctoringPDF record ID)
    - error: string (if error occurred)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            interview_id = request.query_params.get('interview_id')
            session_key = request.query_params.get('session_key')

            # Get interview by ID or session_key
            interview = None
            if interview_id:
                try:
                    interview = Interview.objects.get(id=interview_id)
                except Interview.DoesNotExist:
                    pass
            elif session_key:
                try:
                    interview = Interview.objects.get(session_key=session_key)
                except Interview.DoesNotExist:
                    pass

            if not interview:
                return Response(
                    {'success': False, 'error': 'Interview not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Get ProctoringPDF record with robust database connection
            try:
                from django.db import connection
                print(f"[GetProctoringPDFURLView] ========== NEW REQUEST ==========")
                print(f"[GetProctoringPDFURLView] Database connection: {connection.vendor} - {connection.alias}")
                print(f"[GetProctoringPDFURLView] Looking for ProctoringPDF record for interview {interview.id}")

                # Check for multiple records (shouldn't happen due to OneToOneField, but check anyway)
                proctoring_pdfs = ProctoringPDF.objects.filter(interview=interview)
                record_count = proctoring_pdfs.count()

                print(f"[GetProctoringPDFURLView] Found {record_count} ProctoringPDF records for interview {interview.id}")

                if record_count == 0:
                    print(f"[GetProctoringPDFURLView] No ProctoringPDF record found for interview {interview.id}")
                    return Response(
                        {'success': False, 'error': 'Proctoring PDF not found for this interview'},
                        status=status.HTTP_404_NOT_FOUND
                    )
                elif record_count > 1:
                    print(f"[GetProctoringPDFURLView] WARNING: Multiple ProctoringPDF records found for interview {interview.id}")
                    # Get the most recent one by created_at
                    proctoring_pdf = proctoring_pdfs.order_by('-created_at').first()
                    print(f"[GetProctoringPDFURLView] Using most recent record (created_at: {proctoring_pdf.created_at})")
                else:
                    proctoring_pdf = proctoring_pdfs.first()

                # Validate the record
                if not proctoring_pdf:
                    print(f"[GetProctoringPDFURLView] ERROR: proctoring_pdf is None after query")
                    return Response(
                        {'success': False, 'error': 'Database error retrieving proctoring PDF'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

                gcs_url = proctoring_pdf.gcs_url
                print(f"[GetProctoringPDFURLView] Retrieved ProctoringPDF record ID: {proctoring_pdf.id}")
                print(f"[GetProctoringPDFURLView] Raw gcs_url from database: {gcs_url}")
                print(f"[GetProctoringPDFURLView] Record created_at: {proctoring_pdf.created_at}")
                print(f"[GetProctoringPDFURLView] Record updated_at: {proctoring_pdf.updated_at}")

                if not gcs_url:
                    print(f"[GetProctoringPDFURLView] No GCS URL available for interview {interview.id}")
                    return Response(
                        {'success': False, 'error': 'No GCS URL available'},
                        status=status.HTTP_404_NOT_FOUND
                    )

                # Print RAW URL from database without cleaning
                raw_gcs_url = str(gcs_url).strip()
                print(f"[GetProctoringPDFURLView] RAW GCS URL from database: {raw_gcs_url}")
                print(f"[GetProctoringPDFURLView] Raw URL length: {len(raw_gcs_url)} characters")
                print(f"[GetProctoringPDFURLView] Raw URL contains 'run.app': {'run.app' in raw_gcs_url}")
                print(f"[GetProctoringPDFURLView] Raw URL contains 'storage.googleapis.com': {'storage.googleapis.com' in raw_gcs_url}")
                print(f"[GetProctoringPDFURLView] Raw URL starts with 'https://storage.googleapis.com': {raw_gcs_url.startswith('https://storage.googleapis.com')}")

                # CRITICAL: Check if the URL is malformed and fix it
                if raw_gcs_url and 'run.app' in raw_gcs_url and 'storage.googleapis.com' in raw_gcs_url:
                    print(f"[GetProctoringPDFURLView] ALERT: URL is malformed - contains both run.app and storage.googleapis.com")
                    print(f"[GetProctoringPDFURLView] Attempting to clean the malformed URL...")

                    # Extract clean GCS URL by finding storage.googleapis.com and taking everything after it
                    if 'storage.googleapis.com' in raw_gcs_url:
                        storage_index = raw_gcs_url.find('storage.googleapis.com')
                        if storage_index != -1:
                            clean_url = 'https://' + raw_gcs_url[storage_index:]
                            print(f"[GetProctoringPDFURLView] Successfully cleaned malformed URL: {raw_gcs_url} -> {clean_url}")

                            # Update the database with the cleaned URL
                            proctoring_pdf.gcs_url = clean_url
                            proctoring_pdf.save(update_fields=['gcs_url', 'updated_at'])
                            print(f"[GetProctoringPDFURLView] Database updated with cleaned URL")

                            gcs_url = clean_url
                        else:
                            print(f"[GetProctoringPDFURLView] ERROR: Could not find storage.googleapis.com in malformed URL")
                            gcs_url = raw_gcs_url  # Keep original if cleaning fails
                    else:
                        print(f"[GetProctoringPDFURLView] ERROR: Malformed URL doesn't contain storage.googleapis.com")
                        gcs_url = raw_gcs_url
                else:
                    # URL is already clean
                    gcs_url = raw_gcs_url
                    print(f"[GetProctoringPDFURLView] URL appears to be clean, using as-is")

                print(f"[GetProctoringPDFURLView] Returning final gcs_url: {gcs_url}")
                print(f"[GetProctoringPDFURLView] ========== END REQUEST ==========")

                return Response({
                    'success': True,
                    'gcs_url': gcs_url,
                    'interview_id': str(interview.id),
                    'proctoring_pdf_id': proctoring_pdf.id,
                    'url_was_cleaned': gcs_url != raw_gcs_url
                }, status=status.HTTP_200_OK)

            except ProctoringPDF.DoesNotExist:
                return Response(
                    {'success': False, 'error': 'Proctoring PDF not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

        except Exception as e:
            return Response(
                {'success': False, 'error': f'Error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
