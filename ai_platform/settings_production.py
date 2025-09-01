"""
Production settings for AI Interviewer backend deployed on Render
"""
import os
from .settings import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# Update allowed hosts for production
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '.onrender.com').split(',')

# Database configuration for production (PostgreSQL on Render)
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Static files configuration for production
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# CORS settings for production
CORS_ALLOW_ALL_ORIGINS = False  # Disable for production
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')
CORS_ALLOW_CREDENTIALS = True

# Security settings for production
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Update URLs for production
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'https://ai-interviewer-frontend.onrender.com')
BACKEND_URL = os.environ.get('BACKEND_URL', 'https://ai-interviewer-backend.onrender.com')

# Email configuration for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@talaro.com')

# AI Model configuration for production
AI_MODEL_NAME = os.environ.get('AI_MODEL_NAME', 'gemini-1.5-flash-latest')
AI_MODEL_VERSION = os.environ.get('AI_MODEL_VERSION', '1.0')
AI_MODEL_API_ENDPOINT = os.environ.get('AI_MODEL_API_ENDPOINT')
AI_MODEL_API_KEY = os.environ.get('AI_MODEL_API_KEY')

# Gemini API Configuration
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# Whisper Model Configuration
WHISPER_MODEL_NAME = os.environ.get('WHISPER_MODEL_NAME', 'small')

# Proctoring Configuration
PROCTORING_ENABLED = os.environ.get('PROCTORING_ENABLED', 'True') == 'True'
PROCTORING_NOISE_THRESHOLD = int(os.environ.get('PROCTORING_NOISE_THRESHOLD', 40))
PROCTORING_GRACE_PERIOD = int(os.environ.get('PROCTORING_GRACE_PERIOD', 3))

# Hugging Face Token
HF_TOKEN = os.environ.get('HF_TOKEN')

# Interview Link System Configuration
INTERVIEW_LINK_SECRET = os.environ.get('INTERVIEW_LINK_SECRET', 'your-secret-key-change-in-production')

# Logging configuration for production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/tmp/ai_interviewer.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'ai_interviewer': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'security': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
            'propagate': True,
        },
    },
}

# Cache configuration for production (optional)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Session configuration for production
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# CSRF configuration
CSRF_TRUSTED_ORIGINS = [
    'https://ai-interviewer-frontend.onrender.com',
    'https://ai-interviewer-backend.onrender.com',
]

# Add whitenoise middleware for static files
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')


