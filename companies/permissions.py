from rest_framework import permissions

class AdminOnlyPermission(permissions.BasePermission):
    """
    Custom permission to only allow admin users to perform actions.
    """
    
    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return False
        
        # Only admin users can perform actions
        return request.user.role == "ADMIN"

class AdminOrReadOnlyPermission(permissions.BasePermission):
    """
    Custom permission to allow admin users to perform all actions,
    but other users can only read.
    """
    
    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return False
        
        # Allow read operations for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Only admin users can perform write operations
        return request.user.role == "ADMIN"

class CompanyOrAdminRecruiterPermission(permissions.BasePermission):
    """
    Custom permission to allow Company users to manage recruiters for their own company,
    and Admin users to manage all recruiters.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Allow read operations for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Allow write operations for ADMIN and COMPANY users
        return request.user.role in ['ADMIN', 'COMPANY']
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Admin can manage all recruiters
        if request.user.role == 'ADMIN':
            return True
        
        # Company users can only manage recruiters from their own company
        if request.user.role == 'COMPANY':
            return obj.company.name == request.user.company_name
        
        return False 