from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta
import json

from .models import (
    DashboardMetric, UserActivity, DashboardWidget, SystemPerformance,
    DashboardAnalytics
)
from .serializers import (
    DashboardMetricSerializer, UserActivitySerializer, DashboardWidgetSerializer,
    SystemPerformanceSerializer, DashboardDataSerializer, DashboardFilterSerializer,
    WidgetSettingsSerializer, ActivityFilterSerializer, MetricFilterSerializer,
    DashboardSummarySerializer, ChartDataSerializer, ExportDataSerializer
)
from utils.logger import ActionLogger

class DashboardDataView(APIView):
    """Main dashboard view that returns comprehensive analytics data"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get comprehensive dashboard data for the authenticated user"""
        serializer = DashboardFilterSerializer(data=request.query_params)
        if serializer.is_valid():
            days = serializer.validated_data.get('days', 30)
            
            try:
                # Get dashboard data using the analytics utility
                dashboard_data = DashboardAnalytics.get_user_dashboard_data(
                    user=request.user,
                    days=days
                )
                
                # Log the dashboard access
                ActionLogger.log_user_action(
                    user=request.user,
                    action='dashboard_access',
                    details={'days': days, 'data_points': len(dashboard_data)},
                    status='SUCCESS'
                )
                
                return Response(dashboard_data, status=status.HTTP_200_OK)
                
            except Exception as e:
                ActionLogger.log_user_action(
                    user=request.user,
                    action='dashboard_error',
                    details={'error': str(e), 'days': days},
                    status='FAILED'
                )
                return Response(
                    {'error': 'Failed to load dashboard data'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DashboardSummaryView(APIView):
    """Get a summary of key metrics for quick overview"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get dashboard summary with key metrics"""
        try:
            # Get basic dashboard data
            dashboard_data = DashboardAnalytics.get_user_dashboard_data(
                user=request.user,
                days=30
            )
            
            # Create summary
            summary = {
                'total_resumes': dashboard_data['resume_stats']['total_uploads'],
                'total_interviews': dashboard_data['interview_stats']['total_interviews'],
                'total_candidates': dashboard_data['candidate_stats']['total_candidates'],
                'total_jobs': dashboard_data['job_stats']['total_jobs'],
                'total_activities': dashboard_data['activity_data']['total_activities'],
                'success_rate': dashboard_data['resume_stats']['success_rate'],
                'completion_rate': dashboard_data['interview_stats']['completion_rate'],
                'hiring_rate': dashboard_data['candidate_stats']['hiring_rate'],
            }
            
            ActionLogger.log_user_action(
                user=request.user,
                action='dashboard_summary',
                details=summary,
                status='SUCCESS'
            )
            
            return Response(summary, status=status.HTTP_200_OK)
            
        except Exception as e:
            ActionLogger.log_user_action(
                user=request.user,
                action='dashboard_summary_error',
                details={'error': str(e)},
                status='FAILED'
            )
            return Response(
                {'error': 'Failed to load dashboard summary'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ResumeStatsView(APIView):
    """Get detailed resume statistics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get resume upload statistics"""
        serializer = DashboardFilterSerializer(data=request.query_params)
        if serializer.is_valid():
            days = serializer.validated_data.get('days', 30)
            
            try:
                dashboard_data = DashboardAnalytics.get_user_dashboard_data(
                    user=request.user,
                    days=days
                )
                
                ActionLogger.log_user_action(
                    user=request.user,
                    action='resume_stats_view',
                    details={'days': days},
                    status='SUCCESS'
                )
                
                return Response(dashboard_data['resume_stats'], status=status.HTTP_200_OK)
                
            except Exception as e:
                ActionLogger.log_user_action(
                    user=request.user,
                    action='resume_stats_error',
                    details={'error': str(e)},
                    status='FAILED'
                )
                return Response(
                    {'error': 'Failed to load resume statistics'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class InterviewStatsView(APIView):
    """Get detailed interview statistics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get interview statistics"""
        serializer = DashboardFilterSerializer(data=request.query_params)
        if serializer.is_valid():
            days = serializer.validated_data.get('days', 30)
            
            try:
                dashboard_data = DashboardAnalytics.get_user_dashboard_data(
                    user=request.user,
                    days=days
                )
                
                ActionLogger.log_user_action(
                    user=request.user,
                    action='interview_stats_view',
                    details={'days': days},
                    status='SUCCESS'
                )
                
                return Response(dashboard_data['interview_stats'], status=status.HTTP_200_OK)
                
            except Exception as e:
                ActionLogger.log_user_action(
                    user=request.user,
                    action='interview_stats_error',
                    details={'error': str(e)},
                    status='FAILED'
                )
                return Response(
                    {'error': 'Failed to load interview statistics'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CandidateStatsView(APIView):
    """Get detailed candidate statistics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get candidate statistics"""
        serializer = DashboardFilterSerializer(data=request.query_params)
        if serializer.is_valid():
            days = serializer.validated_data.get('days', 30)
            
            try:
                dashboard_data = DashboardAnalytics.get_user_dashboard_data(
                    user=request.user,
                    days=days
                )
                
                ActionLogger.log_user_action(
                    user=request.user,
                    action='candidate_stats_view',
                    details={'days': days},
                    status='SUCCESS'
                )
                
                return Response(dashboard_data['candidate_stats'], status=status.HTTP_200_OK)
                
            except Exception as e:
                ActionLogger.log_user_action(
                    user=request.user,
                    action='candidate_stats_error',
                    details={'error': str(e)},
                    status='FAILED'
                )
                return Response(
                    {'error': 'Failed to load candidate statistics'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class JobStatsView(APIView):
    """Get detailed job statistics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get job statistics"""
        serializer = DashboardFilterSerializer(data=request.query_params)
        if serializer.is_valid():
            days = serializer.validated_data.get('days', 30)
            
            try:
                dashboard_data = DashboardAnalytics.get_user_dashboard_data(
                    user=request.user,
                    days=days
                )
                
                ActionLogger.log_user_action(
                    user=request.user,
                    action='job_stats_view',
                    details={'days': days},
                    status='SUCCESS'
                )
                
                return Response(dashboard_data['job_stats'], status=status.HTTP_200_OK)
                
            except Exception as e:
                ActionLogger.log_user_action(
                    user=request.user,
                    action='job_stats_error',
                    details={'error': str(e)},
                    status='FAILED'
                )
                return Response(
                    {'error': 'Failed to load job statistics'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserActivityListView(generics.ListAPIView):
    """List user activities with filtering"""
    serializer_class = UserActivitySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['activity_type']
    search_fields = ['details']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Get activities for the authenticated user"""
        queryset = UserActivity.objects.filter(user=self.request.user)
        
        # Apply date filters if provided
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """List activities with logging"""
        ActionLogger.log_user_action(
            user=request.user,
            action='activity_list_view',
            details={'count': self.get_queryset().count()},
            status='SUCCESS'
        )
        return super().list(request, *args, **kwargs)

class DashboardWidgetListView(generics.ListCreateAPIView):
    """List and create dashboard widgets"""
    serializer_class = DashboardWidgetSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get widgets for the authenticated user"""
        return DashboardWidget.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Create widget with user assignment"""
        serializer.save(user=self.request.user)
        ActionLogger.log_user_action(
            user=self.request.user,
            action='widget_created',
            details={'widget_type': serializer.validated_data['widget_type']},
            status='SUCCESS'
        )

class DashboardWidgetDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, and delete dashboard widgets"""
    serializer_class = DashboardWidgetSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get widgets for the authenticated user"""
        return DashboardWidget.objects.filter(user=self.request.user)
    
    def update(self, request, *args, **kwargs):
        """Update widget with logging"""
        ActionLogger.log_user_action(
            user=request.user,
            action='widget_updated',
            details={'widget_id': kwargs.get('pk')},
            status='SUCCESS'
        )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Delete widget with logging"""
        ActionLogger.log_user_action(
            user=request.user,
            action='widget_deleted',
            details={'widget_id': kwargs.get('pk')},
            status='SUCCESS'
        )
        return super().destroy(request, *args, **kwargs)

class WidgetSettingsView(APIView):
    """Update widget settings"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Update widget settings"""
        serializer = WidgetSettingsSerializer(data=request.data)
        if serializer.is_valid():
            try:
                widget, created = DashboardWidget.objects.get_or_create(
                    user=request.user,
                    widget_type=serializer.validated_data['widget_type'],
                    defaults={
                        'position': serializer.validated_data.get('position', 0),
                        'is_enabled': serializer.validated_data.get('is_enabled', True),
                        'settings': serializer.validated_data.get('settings', {})
                    }
                )
                
                if not created:
                    widget.position = serializer.validated_data.get('position', widget.position)
                    widget.is_enabled = serializer.validated_data.get('is_enabled', widget.is_enabled)
                    widget.settings = serializer.validated_data.get('settings', widget.settings)
                    widget.save()
                
                ActionLogger.log_user_action(
                    user=request.user,
                    action='widget_settings_updated',
                    details={'widget_type': serializer.validated_data['widget_type']},
                    status='SUCCESS'
                )
                
                return Response(
                    {'message': 'Widget settings updated successfully'},
                    status=status.HTTP_200_OK
                )
                
            except Exception as e:
                ActionLogger.log_user_action(
                    user=request.user,
                    action='widget_settings_error',
                    details={'error': str(e)},
                    status='FAILED'
                )
                return Response(
                    {'error': 'Failed to update widget settings'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChartDataView(APIView):
    """Get chart data for dashboard widgets"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, chart_type):
        """Get chart data based on type"""
        try:
            days = int(request.query_params.get('days', 30))
            
            if chart_type == 'resume_trend':
                chart_data = self._get_resume_trend_data(request.user, days)
            elif chart_type == 'interview_trend':
                chart_data = self._get_interview_trend_data(request.user, days)
            elif chart_type == 'candidate_distribution':
                chart_data = self._get_candidate_distribution_data(request.user, days)
            elif chart_type == 'activity_trend':
                chart_data = self._get_activity_trend_data(request.user, days)
            else:
                return Response(
                    {'error': 'Invalid chart type'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            ActionLogger.log_user_action(
                user=request.user,
                action='chart_data_requested',
                details={'chart_type': chart_type, 'days': days},
                status='SUCCESS'
            )
            
            return Response(chart_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            ActionLogger.log_user_action(
                user=request.user,
                action='chart_data_error',
                details={'error': str(e), 'chart_type': chart_type},
                status='FAILED'
            )
            return Response(
                {'error': 'Failed to load chart data'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_resume_trend_data(self, user, days):
        """Get resume upload trend data"""
        from resumes.models import Resume
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Get user's role and company
        user_role = getattr(user, 'role', '')
        company_name = getattr(user, 'company_name', '')
        
        queryset = Resume.objects.filter(created_at__date__range=[start_date, end_date])
        
        if user_role == 'COMPANY':
            queryset = queryset.filter(company_name=company_name)
        elif user_role in ['HIRING_AGENCY', 'RECRUITER']:
            queryset = queryset.filter(recruiter=user)
        
        daily_data = queryset.extra(
            select={'date': 'DATE(created_at)'}
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        labels = [item['date'].strftime('%Y-%m-%d') for item in daily_data]
        data = [item['count'] for item in daily_data]
        
        return {
            'labels': labels,
            'datasets': [{
                'label': 'Resume Uploads',
                'data': data,
                'borderColor': '#4CAF50',
                'backgroundColor': 'rgba(76, 175, 80, 0.1)',
                'tension': 0.4
            }],
            'options': {
                'responsive': True,
                'scales': {
                    'y': {'beginAtZero': True}
                }
            }
        }
    
    def _get_interview_trend_data(self, user, days):
        """Get interview trend data"""
        from interviews.models import Interview
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        user_role = getattr(user, 'role', '')
        company_name = getattr(user, 'company_name', '')
        
        queryset = Interview.objects.filter(created_at__date__range=[start_date, end_date])
        
        if user_role == 'COMPANY':
            queryset = queryset.filter(company_name=company_name)
        elif user_role in ['HIRING_AGENCY', 'RECRUITER']:
            queryset = queryset.filter(recruiter=user)
        
        daily_data = queryset.extra(
            select={'date': 'DATE(created_at)'}
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        labels = [item['date'].strftime('%Y-%m-%d') for item in daily_data]
        data = [item['count'] for item in daily_data]
        
        return {
            'labels': labels,
            'datasets': [{
                'label': 'Interviews Scheduled',
                'data': data,
                'borderColor': '#2196F3',
                'backgroundColor': 'rgba(33, 150, 243, 0.1)',
                'tension': 0.4
            }],
            'options': {
                'responsive': True,
                'scales': {
                    'y': {'beginAtZero': True}
                }
            }
        }
    
    def _get_candidate_distribution_data(self, user, days):
        """Get candidate domain distribution data"""
        from candidates.models import Candidate
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        user_role = getattr(user, 'role', '')
        company_name = getattr(user, 'company_name', '')
        
        queryset = Candidate.objects.filter(created_at__date__range=[start_date, end_date])
        
        if user_role == 'COMPANY':
            queryset = queryset.filter(company_name=company_name)
        elif user_role in ['HIRING_AGENCY', 'RECRUITER']:
            queryset = queryset.filter(recruiter=user)
        
        domain_data = queryset.values('domain').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        labels = [item['domain'] for item in domain_data]
        data = [item['count'] for item in domain_data]
        
        # Generate colors for pie chart
        colors = [
            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
            '#FF9F40', '#FF6384', '#C9CBCF', '#4BC0C0', '#FF6384'
        ]
        
        return {
            'labels': labels,
            'datasets': [{
                'label': 'Candidates by Domain',
                'data': data,
                'backgroundColor': colors[:len(data)],
                'borderWidth': 2,
                'borderColor': '#fff'
            }],
            'options': {
                'responsive': True,
                'plugins': {
                    'legend': {'position': 'bottom'}
                }
            }
        }
    
    def _get_activity_trend_data(self, user, days):
        """Get user activity trend data"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        queryset = UserActivity.objects.filter(
            user=user,
            created_at__date__range=[start_date, end_date]
        )
        
        daily_data = queryset.extra(
            select={'date': 'DATE(created_at)'}
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        labels = [item['date'].strftime('%Y-%m-%d') for item in daily_data]
        data = [item['count'] for item in daily_data]
        
        return {
            'labels': labels,
            'datasets': [{
                'label': 'User Activities',
                'data': data,
                'borderColor': '#9C27B0',
                'backgroundColor': 'rgba(156, 39, 176, 0.1)',
                'tension': 0.4
            }],
            'options': {
                'responsive': True,
                'scales': {
                    'y': {'beginAtZero': True}
                }
            }
        }

class ExportDashboardDataView(APIView):
    """Export dashboard data in various formats"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Export dashboard data"""
        serializer = ExportDataSerializer(data=request.data)
        if serializer.is_valid():
            try:
                format_type = serializer.validated_data['format']
                date_from = serializer.validated_data.get('date_from')
                date_to = serializer.validated_data.get('date_to')
                include_charts = serializer.validated_data.get('include_charts', False)
                include_details = serializer.validated_data.get('include_details', True)
                
                # Get dashboard data
                days = 30
                if date_from and date_to:
                    days = (date_to - date_from).days
                
                dashboard_data = DashboardAnalytics.get_user_dashboard_data(
                    user=request.user,
                    days=days
                )
                
                # Prepare export data
                export_data = {
                    'export_info': {
                        'user': request.user.email,
                        'export_date': timezone.now().isoformat(),
                        'format': format_type,
                        'date_range': dashboard_data['date_range']
                    },
                    'summary': {
                        'total_resumes': dashboard_data['resume_stats']['total_uploads'],
                        'total_interviews': dashboard_data['interview_stats']['total_interviews'],
                        'total_candidates': dashboard_data['candidate_stats']['total_candidates'],
                        'total_jobs': dashboard_data['job_stats']['total_jobs'],
                    }
                }
                
                if include_details:
                    export_data['details'] = dashboard_data
                
                if include_charts:
                    # Add chart data
                    export_data['charts'] = {
                        'resume_trend': self._get_resume_trend_data(request.user, days),
                        'interview_trend': self._get_interview_trend_data(request.user, days),
                        'candidate_distribution': self._get_candidate_distribution_data(request.user, days)
                    }
                
                ActionLogger.log_user_action(
                    user=request.user,
                    action='dashboard_data_exported',
                    details={'format': format_type, 'include_charts': include_charts},
                    status='SUCCESS'
                )
                
                return Response(export_data, status=status.HTTP_200_OK)
                
            except Exception as e:
                ActionLogger.log_user_action(
                    user=request.user,
                    action='dashboard_export_error',
                    details={'error': str(e)},
                    status='FAILED'
                )
                return Response(
                    {'error': 'Failed to export dashboard data'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _get_resume_trend_data(self, user, days):
        """Helper method for resume trend data"""
        from resumes.models import Resume
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        user_role = getattr(user, 'role', '')
        company_name = getattr(user, 'company_name', '')
        
        queryset = Resume.objects.filter(created_at__date__range=[start_date, end_date])
        
        if user_role == 'COMPANY':
            queryset = queryset.filter(company_name=company_name)
        elif user_role in ['HIRING_AGENCY', 'RECRUITER']:
            queryset = queryset.filter(recruiter=user)
        
        return list(queryset.extra(
            select={'date': 'DATE(created_at)'}
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date'))
    
    def _get_interview_trend_data(self, user, days):
        """Helper method for interview trend data"""
        from interviews.models import Interview
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        user_role = getattr(user, 'role', '')
        company_name = getattr(user, 'company_name', '')
        
        queryset = Interview.objects.filter(created_at__date__range=[start_date, end_date])
        
        if user_role == 'COMPANY':
            queryset = queryset.filter(company_name=company_name)
        elif user_role in ['HIRING_AGENCY', 'RECRUITER']:
            queryset = queryset.filter(recruiter=user)
        
        return list(queryset.extra(
            select={'date': 'DATE(created_at)'}
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date'))
    
    def _get_candidate_distribution_data(self, user, days):
        """Helper method for candidate distribution data"""
        from candidates.models import Candidate
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        user_role = getattr(user, 'role', '')
        company_name = getattr(user, 'company_name', '')
        
        queryset = Candidate.objects.filter(created_at__date__range=[start_date, end_date])
        
        if user_role == 'COMPANY':
            queryset = queryset.filter(company_name=company_name)
        elif user_role in ['HIRING_AGENCY', 'RECRUITER']:
            queryset = queryset.filter(recruiter=user)
        
        return list(queryset.values('domain').annotate(
            count=Count('id')
        ).order_by('-count')[:10]) 