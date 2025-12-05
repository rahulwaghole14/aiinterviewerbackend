#!/bin/bash
# Startup script for Render deployment
# This ensures the correct WSGI application is used

echo "🚀 Starting Django application..."
echo "WSGI Module: interview_app.wsgi:application"
echo "Settings Module: interview_app.settings"

# Ensure we're using the correct WSGI application
exec gunicorn interview_app.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120

