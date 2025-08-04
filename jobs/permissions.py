from rest_framework import permissions
from utils.logger import ActionLogger


class DomainAdminOnlyPermission(permissions.BasePermission):
    """
    Permission class for domain management.
    Only admin users can create, update, and delete domains.
    All authenticated users can view domains.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Allow read operations for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Only admin users can perform write operations
        if request.user.role == "ADMIN":
            return True
        
        # Log permission denial
        ActionLogger.log_user_action(
            user=request.user,
            action='domain_management_permission_denied',
            details={
                'method': request.method,
                'view': view.__class__.__name__,
                'reason': 'Non-admin user attempted domain modification'
            },
            status='FAILED'
        )
        
        return False
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Allow read operations for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Only admin users can perform write operations
        if request.user.role == "ADMIN":
            return True
        
        # Log permission denial
        ActionLogger.log_user_action(
            user=request.user,
            action='domain_object_permission_denied',
            details={
                'method': request.method,
                'view': view.__class__.__name__,
                'domain_id': obj.id,
                'domain_name': obj.name,
                'reason': 'Non-admin user attempted domain modification'
            },
            status='FAILED'
        )
        
        return False


class JobDomainPermission(permissions.BasePermission):
    """
    Permission class for job management with domain requirements.
    Company users can create jobs but must select from existing domains.
    Admin users have full access.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Allow read operations for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Admin and company users can create jobs
        if request.method == "POST":
            return request.user.role in ["ADMIN", "COMPANY"]
        
        # Admin users can perform all operations
        if request.user.role == "ADMIN":
            return True
        
        # Company users can only create jobs
        if request.user.role == "COMPANY" and request.method == "POST":
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Allow read operations for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Admin users can perform all operations
        if request.user.role == "ADMIN":
            return True
        
        # Company users can only update/delete their own jobs
        if request.user.role == "COMPANY":
            return obj.company_name == request.user.company_name
        
        return False 