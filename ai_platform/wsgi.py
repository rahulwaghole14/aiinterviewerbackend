"""
WSGI compatibility module for Render deployment
This module redirects to interview_app.wsgi to maintain backward compatibility
with old Render dashboard configurations.
"""
import sys
import os

# Add the project root to Python path if needed
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the actual WSGI application from interview_app
try:
    from interview_app.wsgi import application
    print("✅ Successfully imported WSGI application from interview_app.wsgi")
except ImportError as e:
    print(f"❌ Failed to import from interview_app.wsgi: {e}")
    raise

print("✅ ai_platform.wsgi compatibility module loaded - redirecting to interview_app.wsgi")

