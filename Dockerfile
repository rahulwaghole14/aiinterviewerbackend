# Dockerfile for Django Backend - Google Cloud Run with Cloud SQL
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p /app/staticfiles /app/media /app/logs

# Make startup script executable
RUN chmod +x /app/start.sh

# Collect static files (non-blocking if fails)
RUN python manage.py collectstatic --noinput || true

# Expose port (Cloud Run uses PORT env variable)
EXPOSE 8080

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV DJANGO_SETTINGS_MODULE=interview_app.settings

# Health check (check if port is listening)
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD python -c "import socket, os; port=int(os.environ.get('PORT', 8080)); s=socket.socket(); s.settimeout(2); result=s.connect_ex(('localhost', port)); s.close(); exit(0 if result == 0 else 1)"

# Use startup script
CMD ["/app/start.sh"]
