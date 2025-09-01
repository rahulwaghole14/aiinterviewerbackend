import os
from pathlib import Path
from decouple import config
import dj_database_url

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Security key and debug flag from .env
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', cast=bool, default=False)
# My secret key is: django-insecure-%knt0&8&-)qlgkgu#c&o-_4_t(g3j_soqwk)z4o1f_l)^%rpwt

# Allowed hosts
ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'corsheaders',

    # third-party apps
    'rest_framework',
    'rest_framework.authtoken',

    # your custom apps
    'authapp',
    'hiring_agency',
    'candidates',
    'jobs',
    'resumes',
    'interviews',
    'companies',
    'evaluation',
    'notifications',
    'dashboard',
    'ai_interview',
    'ai_platform.interview_app.apps.InterviewAppConfig',
]

# Django REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ]
}


MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # CORS middleware must come first
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'utils.middleware.LoggingMiddleware',  # Commented out - middleware file was deleted
]

ROOT_URLCONF = 'ai_platform.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ai_platform.wsgi.application'

# Database configuration - Force local SQLite for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Custom user model
AUTH_USER_MODEL = 'authapp.CustomUser'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# Static and media files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default auto field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS Configuration
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "https://aiinterviewerfrontend.onrender.com",
    "https://aiinterviewerfrontend-2.onrender.com",
    "https://aiinterviewerbackend-3.onrender.com",
]
CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
CORS_ALLOWED_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@talaro.com')

# Interview Link System Configuration
INTERVIEW_LINK_SECRET = config('INTERVIEW_LINK_SECRET', default='your-secret-key-change-in-production')
# Use deployed defaults to avoid localhost links in production if env var is missing
FRONTEND_URL = config('FRONTEND_URL', default='https://aiinterviewerbackend-3.onrender.com')
BACKEND_URL = config('BACKEND_URL', default='https://aiinterviewerbackend-2.onrender.com')

# AI Interview Model Configuration
AI_MODEL_NAME = config('AI_MODEL_NAME', default='gemini-1.5-flash-latest')
AI_MODEL_VERSION = config('AI_MODEL_VERSION', default='1.0')
AI_MODEL_API_ENDPOINT = config('AI_MODEL_API_ENDPOINT', default=None)
AI_MODEL_API_KEY = config('AI_MODEL_API_KEY', default=None)

# Gemini API Configuration
GEMINI_API_KEY = config('GEMINI_API_KEY', default=None)

# Whisper Model Configuration
WHISPER_MODEL_NAME = config('WHISPER_MODEL_NAME', default='small')

# Proctoring Configuration
PROCTORING_ENABLED = config('PROCTORING_ENABLED', default=True, cast=bool)
PROCTORING_NOISE_THRESHOLD = config('PROCTORING_NOISE_THRESHOLD', default=40, cast=int)
PROCTORING_GRACE_PERIOD = config('PROCTORING_GRACE_PERIOD', default=3, cast=int)

# Hugging Face Token for Speaker Detection
HF_TOKEN = config('HF_TOKEN', default=None)

AUTHENTICATION_BACKENDS = [
    'authapp.backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',  
]

# Logging Configuration
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
        'json': {
            'format': '{message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/ai_interviewer.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': 'logs/security.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'ai_interviewer': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'security': {
            'handlers': ['security_file', 'console'],
            'level': 'WARNING',
            'propagate': True,
        },
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}