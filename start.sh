#!/bin/bash

# Get port from environment variable (Cloud Run sets this)
PORT="${PORT:-8080}"

echo "🚀 Starting Django Backend on port $PORT"
echo "📋 Environment check:"
echo "   PORT=$PORT"
echo "   DATABASE_URL=${DATABASE_URL:0:50}..." # Show first 50 chars only

# Run migrations (non-blocking - continue even if some fail)
echo "📊 Running database migrations..."
if python manage.py migrate --noinput; then
    echo "✅ Migrations completed successfully"
else
    echo "⚠️ Warning: Some migrations failed, but continuing..."
fi

# Start Gunicorn
echo "🌐 Starting Gunicorn server on 0.0.0.0:$PORT"
exec gunicorn interview_app.wsgi:application \
    --bind "0.0.0.0:$PORT" \
    --workers 2 \
    --timeout 120 \
    --worker-class sync \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --preload
