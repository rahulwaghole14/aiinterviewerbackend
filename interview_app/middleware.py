"""
Custom middleware to exempt API routes from CSRF protection
"""
from django.utils.deprecation import MiddlewareMixin
from django.middleware.csrf import CsrfViewMiddleware


class CsrfExemptApiMiddleware(MiddlewareMixin):
    """
    Middleware that exempts API routes from CSRF protection.
    API routes use token authentication, so CSRF is not needed.
    """
    
    def process_request(self, request):
        # Exempt all /api/ routes from CSRF
        if request.path.startswith('/api/'):
            setattr(request, '_dont_enforce_csrf_checks', True)
        return None

