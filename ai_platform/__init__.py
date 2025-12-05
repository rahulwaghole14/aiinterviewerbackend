"""
Compatibility package for Render deployment
This package redirects to interview_app to maintain backward compatibility
with old Render dashboard configurations.
"""
import sys
import os

# Add the project root to Python path if needed
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print("✅ ai_platform compatibility package loaded")

