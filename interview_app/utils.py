"""
Utility functions for interview URL generation
"""
import os
from django.conf import settings


def get_backend_url(request=None):
    """
    Get the backend URL for generating interview links.
    For local development, always use localhost.
    """
    # For local development, always use localhost
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

