from rest_framework import permissions
from utils.logger import log_permission_denied, ActionLogger


class HierarchyPermission(permissions.BasePermission):
    """
    Base permission class that implements the proper hierarchy:
    ADMIN > COMPANY > HIRING_AGENCY/RECRUITER
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Allow read operations for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True

        # Check hierarchy-based permissions
        return self._check_hierarchy_permission(request.user)

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        # Allow read operations for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True

        # Check hierarchy-based object permissions
        return self._check_hierarchy_object_permission(request.user, obj)

    def _check_hierarchy_permission(self, user):
        """Check if user has permission based on hierarchy"""
        # Admin has all permissions
        if user.is_admin():
            return True

        # Company users have company-level permissions
        if user.is_company():
            return True

        # Hiring Agency and Recruiter have limited permissions
        if user.is_hiring_agency() or user.is_recruiter():
            return True

        return False

    def _check_hierarchy_object_permission(self, user, obj):
        """Check if user has permission for specific object based on hierarchy"""
        # Admin can access all objects
        if user.is_admin():
            return True

        # Company users can access objects within their company
        if user.is_company():
            return self._is_object_in_user_company(user, obj)

        # Hiring Agency and Recruiter can access objects within their company
        if user.is_hiring_agency() or user.is_recruiter():
            return self._is_object_in_user_company(user, obj)

        return False

    def _is_object_in_user_company(self, user, obj):
        """Check if object belongs to user's company"""
        user_company = user.get_company_name()

        # Check different object types
        if hasattr(obj, "user") and obj.user:
            return obj.user.get_company_name() == user_company
        elif hasattr(obj, "company_name"):
            return obj.company_name == user_company
        elif hasattr(obj, "company") and obj.company:
            return obj.company.name == user_company
        elif hasattr(obj, "created_by") and obj.created_by:
            return obj.created_by.get_company_name() == user_company
        elif hasattr(obj, "recruiter") and obj.recruiter:
            return obj.recruiter.get_company_name() == user_company

        return False


class ResumeHierarchyPermission(HierarchyPermission):
    """
    Permission for resume operations based on hierarchy
    """

    def _check_hierarchy_permission(self, user):
        """Check resume-specific permissions"""
        # Admin and Company can do everything
        if user.is_admin() or user.is_company():
            return True

        # Hiring Agency and Recruiter can upload resumes
        if user.is_hiring_agency() or user.is_recruiter():
            return True

        return False


class InterviewHierarchyPermission(HierarchyPermission):
    """
    Permission for interview operations based on hierarchy
    """

    def _check_hierarchy_permission(self, user):
        """Check interview-specific permissions"""
        # Admin and Company can do everything
        if user.is_admin() or user.is_company():
            return True

        # Hiring Agency and Recruiter can schedule interviews
        if user.is_hiring_agency() or user.is_recruiter():
            return True

        return False


class CompanyHierarchyPermission(HierarchyPermission):
    """
    Permission for company operations based on hierarchy
    """

    def _check_hierarchy_permission(self, user):
        """Check company-specific permissions"""
        # Only Admin can manage companies
        return user.is_admin()

    def _check_hierarchy_object_permission(self, user, obj):
        """Check company object permissions"""
        # Only Admin can manage companies
        return user.is_admin()


class HiringAgencyHierarchyPermission(HierarchyPermission):
    """
    Permission for hiring agency operations based on hierarchy
    """

    def _check_hierarchy_permission(self, user):
        """Check hiring agency-specific permissions"""
        # Admin can manage all hiring agencies
        if user.is_admin():
            return True

        # Company can manage hiring agencies under their company
        if user.is_company():
            return True

        return False

    def _check_hierarchy_object_permission(self, user, obj):
        """Check hiring agency object permissions"""
        # Admin can manage all hiring agencies
        if user.is_admin():
            return True

        # Company can only manage hiring agencies in their company
        if user.is_company():
            return self._is_object_in_user_company(user, obj)

        return False


class RecruiterHierarchyPermission(HierarchyPermission):
    """
    Permission for recruiter operations based on hierarchy
    """

    def _check_hierarchy_permission(self, user):
        """Check recruiter-specific permissions"""
        # Admin can manage all recruiters
        if user.is_admin():
            return True

        # Company can manage recruiters under their company
        if user.is_company():
            return True

        return False

    def _check_hierarchy_object_permission(self, user, obj):
        """Check recruiter object permissions"""
        # Admin can manage all recruiters
        if user.is_admin():
            return True

        # Company can only manage recruiters in their company
        if user.is_company():
            return self._is_object_in_user_company(user, obj)

        return False


class DataIsolationMixin:
    """
    Mixin to ensure data isolation by company
    """

    def get_queryset(self):
        """Filter queryset based on user's company"""
        queryset = super().get_queryset()
        user = self.request.user

        # Admin can see all data
        if user.is_admin():
            return queryset

        # Other users can only see data from their company
        user_company = user.get_company_name()

        # Filter based on different model structures
        if hasattr(queryset.model, "company"):
            # For models with company ForeignKey (like Recruiter)
            return queryset.filter(company__name=user_company)
        elif hasattr(queryset.model, "user") and hasattr(queryset.model, "company"):
            # For models with both user and company (like Recruiter)
            return queryset.filter(company__name=user_company)
        elif hasattr(queryset.model, "company_name"):
            return queryset.filter(company_name=user_company)
        elif hasattr(queryset.model, "created_by"):
            return queryset.filter(created_by__company_name=user_company)
        elif hasattr(queryset.model, "recruiter"):
            # For candidates, filter by recruiter's company
            return queryset.filter(recruiter__company__name=user_company)

        return queryset
