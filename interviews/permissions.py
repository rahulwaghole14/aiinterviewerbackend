from rest_framework import permissions
from utils.logger import log_permission_denied, ActionLogger

class HiringAgencyOrRecruiterInterviewPermission(permissions.BasePermission):
    """
    Custom permission to allow only hiring agency and recruiter users to schedule interviews.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            # Log unauthenticated access attempt
            ActionLogger.log_security_event(
                event_type='UNAUTHENTICATED_ACCESS',
                user=None,
                details={
                    'action': 'interview_schedule',
                    'method': request.method,
                    'path': request.path,
                    'ip_address': request.META.get('REMOTE_ADDR')
                },
                severity='WARNING'
            )
            return False
        
        # Allow read operations for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Check if user has permission for write operations
        has_permission = request.user.role in ['HIRING_AGENCY', 'RECRUITER']
        
        if not has_permission:
            # Log permission denied
            log_permission_denied(
                user=request.user,
                action='interview_schedule',
                reason=f'User role "{request.user.role}" not allowed for interview scheduling',
                ip_address=request.META.get('REMOTE_ADDR')
            )
        
        return has_permission
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Allow read operations for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Check if user has permission for write operations
        has_permission = request.user.role in ['HIRING_AGENCY', 'RECRUITER']
        
        if not has_permission:
            # Log permission denied for object
            log_permission_denied(
                user=request.user,
                action='interview_object_access',
                reason=f'User role "{request.user.role}" not allowed for interview object operations',
                ip_address=request.META.get('REMOTE_ADDR')
            )
        
        return has_permission 