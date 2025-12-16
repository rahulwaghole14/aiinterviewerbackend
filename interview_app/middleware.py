"""
Custom middleware to exempt API endpoints from CSRF protection.
This is needed because API endpoints use token authentication, not session-based auth.
"""
from django.utils.deprecation import MiddlewareMixin
from django.views.decorators.csrf import csrf_exempt


class DisableCSRFForAPI(MiddlewareMixin):
    """
    Middleware to disable CSRF protection for all /api/ endpoints.
    API endpoints use token authentication, so CSRF is not needed.
    """
    
    def process_request(self, request):
        # Exempt all API endpoints from CSRF
        if request.path.startswith('/api/'):
            setattr(request, '_dont_enforce_csrf_checks', True)
        return None



