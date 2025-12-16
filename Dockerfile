# Dockerfile for Django Backend - Google Cloud Run with Cloud SQL
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies and language runtimes/compilers for coding round
# - gcc/g++       : C / C++
# - postgresql    : DB client
# - openjdk       : Java (javac/java)
# - nodejs/npm    : JavaScript (node)
# - golang        : Go (go)
# - php-cli       : PHP
# - ruby-full     : Ruby
# - dotnet-sdk    : C# (dotnet)
RUN apt-get update && apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    apt-transport-https \
    gcc \
    g++ \
    make \
    postgresql-client \
    libpq-dev \
    default-jdk-headless \
    nodejs \
    npm \
    golang-go \
    php-cli \
    ruby-full \
    && curl https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb -o /tmp/packages-microsoft-prod.deb \
    && dpkg -i /tmp/packages-microsoft-prod.deb \
    && rm /tmp/packages-microsoft-prod.deb \
    && apt-get update && apt-get install -y dotnet-sdk-8.0 \
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

# Add YOLO model files (yolov8m.pt for reference, yolov8m.onnx for runtime)
# Note: These files should be in the project root directory
# Using shell form to handle missing files gracefully
RUN if [ -f yolov8m.pt ]; then cp yolov8m.pt /app/yolov8m.pt; else echo "⚠️ yolov8m.pt not found, skipping"; fi
RUN if [ -f yolov8m.onnx ]; then cp yolov8m.onnx /app/yolov8m.onnx; else echo "⚠️ yolov8m.onnx not found, skipping"; fi

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
