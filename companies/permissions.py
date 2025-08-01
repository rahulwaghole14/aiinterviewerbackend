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