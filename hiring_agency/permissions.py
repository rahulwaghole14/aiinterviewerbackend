from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "ADMIN"
        )


class CompanyOrAdminPermission(permissions.BasePermission):
    """
    Custom permission to allow Company users to manage hiring agencies for their own company,
    and Admin users to manage all hiring agencies.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Allow read operations for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True

        # Allow write operations for ADMIN and COMPANY users
        return request.user.role in ["ADMIN", "COMPANY"]

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        # Admin can manage all hiring agencies
        if request.user.role == "ADMIN":
            return True

        # Company users can only manage hiring agencies from their own company
        if request.user.role == "COMPANY":
            return obj.company_name == request.user.company_name

        return False
