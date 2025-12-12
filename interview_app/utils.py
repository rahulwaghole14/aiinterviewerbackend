"""
Utility functions for interview URL generation
"""
import os
from django.conf import settings


def get_backend_url(request=None):
    """
    Get the backend URL for generating interview links.
    Prioritizes Cloud Run detection, then request, then environment variables.
    
    Args:
        request: Django request object (optional)
    
    Returns:
        str: Backend URL (e.g., https://talaroai-310576915040.asia-southeast1.run.app)
    """
    # First, try to get from request if available
    if request:
        base_url = request.build_absolute_uri('/').rstrip('/')
        # If request gives us localhost, ignore it and use Cloud Run detection
        if 'localhost' not in base_url.lower() and '127.0.0.1' not in base_url.lower():
            return base_url
    
    # Try BACKEND_URL from settings
    base_url = getattr(settings, "BACKEND_URL", None)
    if base_url and "localhost" not in str(base_url).lower():
        return base_url.rstrip('/')
    
    # Try environment variable
    base_url = os.environ.get("BACKEND_URL", None)
    if base_url and "localhost" not in str(base_url).lower():
        return base_url.rstrip('/')
    
    # Try to detect from Cloud Run environment variables
    service_name = os.environ.get("K_SERVICE")
    if service_name:
        region = os.environ.get("GOOGLE_CLOUD_REGION", "asia-southeast1")
        project_number = os.environ.get("GOOGLE_CLOUD_PROJECT_NUMBER", "310576915040")
        base_url = f"https://{service_name}-{project_number}.{region}.run.app"
        return base_url
    
    # Final fallback
    return "http://localhost:8000"


def get_interview_url(session_key, request=None):
    """
    Generate interview URL with session_key.
    Uses /interview/ route which serves the Django interview portal.
    
    Args:
        session_key: Interview session key
        request: Django request object (optional)
    
    Returns:
        str: Full interview URL
    """
    base_url = get_backend_url(request)
    # Use /interview/ route (not root /) to access Django interview portal
    return f"{base_url}/interview/?session_key={session_key}"

