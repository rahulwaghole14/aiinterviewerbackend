from pathlib import Path
import os

# Load environment variables from .env if present
try:
    from dotenv import load_dotenv  # type: ignore
except Exception:
    load_dotenv = None

# Base directory of the project (repository root)
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env from project root if python-dotenv is available
if load_dotenv is not None:
    load_dotenv(BASE_DIR / ".env")

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-secret-key-change-me")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

ALLOWED_HOSTS = ["*"]

# Cloud Run proxy settings - trust X-Forwarded-* headers
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "corsheaders",
    "rest_framework",
    "rest_framework.authtoken",
    "channels",

    # Project apps (add more here as needed)
    "authapp",
    "candidates",
    "companies",
    "dashboard",
    "evaluation",
    "file_management.apps.FileManagementConfig",
    "hiring_agency",
    "interview_app",  # app containing urls/templates
    "interviews",
    "jobs",
    "notifications",
    "resumes",
    "users",
]

MIDDLEWARE = [
    # CORS must be first to ensure headers on responses incl. preflight
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise must be after SecurityMiddleware but before other middleware
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    # Custom middleware to disable CSRF for API endpoints (must be before CsrfViewMiddleware)
    "interview_app.middleware.DisableCSRFForAPI",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "interview_app.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "interview_app.wsgi.application"
ASGI_APPLICATION = "interview_app.asgi.application"
# Channels layer (in-memory for dev)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}


# Database
# Using SQLite for local development
# PostgreSQL database is paused - will use SQLite until PostgreSQL is resumed
DATABASE_URL = os.environ.get("DATABASE_URL", "")

# PostgreSQL is now enabled - using new database
# To use SQLite for local development, set USE_POSTGRESQL = False
# Force SQLite for local development
USE_POSTGRESQL = False

if USE_POSTGRESQL and DATABASE_URL:
    # PostgreSQL configuration
    # Supports both Cloud SQL Unix socket and regular TCP connections
    try:
        # Try using dj-database-url if available
        try:
            import dj_database_url
            # Configure database with SSL support
            db_config = dj_database_url.config(
                default=DATABASE_URL, 
                conn_max_age=600,
                conn_health_checks=True
            )
            
            # Cloud SQL Unix socket connection (format: postgresql://user:password@/dbname?host=/cloudsql/...)
            if '/cloudsql/' in DATABASE_URL:
                # Cloud SQL via Unix socket - no SSL needed
                if 'OPTIONS' not in db_config:
                    db_config['OPTIONS'] = {}
                # Remove SSL for Unix socket connections
                db_config['OPTIONS'].pop('sslmode', None)
                print("[OK] Using Cloud SQL via Unix socket")
            # Render.com or other cloud databases
            elif 'render.com' in DATABASE_URL.lower():
                if 'OPTIONS' not in db_config:
                    db_config['OPTIONS'] = {}
                # Render.com requires SSL
                db_config['OPTIONS']['sslmode'] = 'require'
                print("[OK] Using PostgreSQL database from DATABASE_URL (Render.com)")
            else:
                print("[OK] Using PostgreSQL database from DATABASE_URL (dj-database-url)")
            
            DATABASES = {
                "default": db_config
            }
        except ImportError:
            # Fallback: Parse DATABASE_URL manually
            from urllib.parse import urlparse, parse_qs
            db_url = urlparse(DATABASE_URL)
            
            # Parse query parameters (e.g., sslmode=require)
            query_params = parse_qs(db_url.query)
            sslmode = query_params.get('sslmode', ['require'])[0] if query_params else 'require'
            
            # Configure SSL options for Render.com and other cloud databases
            ssl_options = {}
            if sslmode == 'require' or sslmode == 'prefer':
                # For Render.com and most cloud databases, we need SSL but can skip verification
                ssl_options = {
                    'sslmode': 'require',
                    'sslcert': None,
                    'sslkey': None,
                    'sslrootcert': None,
                }
            
            # For Render.com and cloud databases, configure SSL properly
            # Render.com requires SSL but may need specific settings
            database_options = {
                "connect_timeout": 10,
            }
            
            # Cloud SQL Unix socket connection (no SSL needed)
            if '/cloudsql/' in DATABASE_URL:
                # Cloud SQL via Unix socket - no SSL
                print("[OK] Using Cloud SQL via Unix socket (manual parsing)")
            # Add SSL configuration for other cloud databases
            elif 'sslmode' in db_url.query.lower() or 'render.com' in (db_url.hostname or '').lower():
                # Render.com and most cloud providers require SSL
                database_options.update({
                    'sslmode': 'require',
                })
                print("[OK] Using PostgreSQL with SSL (manual parsing)")
            
            DATABASES = {
                "default": {
                    "ENGINE": "django.db.backends.postgresql",
                    "NAME": db_url.path[1:],  # Remove leading '/'
                    "USER": db_url.username,
                    "PASSWORD": db_url.password,
                    "HOST": db_url.hostname,
                    "PORT": db_url.port or 5432,
                    "OPTIONS": database_options,
                }
            }
            print("[OK] Using PostgreSQL database from DATABASE_URL (manual parsing)")
    except Exception as e:
        print(f"[WARNING] Error parsing DATABASE_URL: {e}")
        print("[WARNING] Falling back to SQLite")
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": str(BASE_DIR / "db.sqlite3"),
            }
        }
else:
    # Using SQLite for local development (PostgreSQL is paused)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": str(BASE_DIR / "db.sqlite3"),
        }
    }
    if DATABASE_URL:
        print("[INFO] Using SQLite database (PostgreSQL is paused - set USE_POSTGRESQL=True to enable)")
    else:
        print("[INFO] Using SQLite database (DATABASE_URL not set)")


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
    BASE_DIR / "static_frontend_dist",  # Include frontend build output (copied dist folder)
    BASE_DIR / "frontend" / "dist",  # Include frontend build output (if submodule is checked out)
]

# WhiteNoise configuration for serving static files in production
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Google Cloud Storage configuration
GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME", None)  # e.g., "your-project-pdfs"
GCS_USE_SIGNED_URLS = os.environ.get("GCS_USE_SIGNED_URLS", "false").lower() == "true"  # Use signed URLs for private access


# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Use the custom user model defined in authapp
AUTH_USER_MODEL = "authapp.CustomUser"

# Enable email-based authentication
AUTHENTICATION_BACKENDS = [
    "authapp.backends.EmailBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# DRF global configuration: accept Token auth by default
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    # Disable CSRF for API endpoints (using Token auth instead)
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}

# Disable CSRF for API endpoints - they use token authentication
CSRF_TRUSTED_ORIGINS = [
    "https://aiinterviewerbackend-2.onrender.com",
    "https://*.onrender.com",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# CORS settings to allow Vite dev server and Render frontend
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://aiinterviewerbackend-2.onrender.com",  # Backend serving frontend
    "https://aiinterviewerbackend-3.onrender.com",  # Separate frontend service (if deployed)
]

# Allow any localhost port (when Vite picks alternate ports)
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^http://localhost:\d+$", 
    r"^http://127\.0\.0\.1:\d+$",
    r"^https://.*\.onrender\.com$",  # Allow all Render subdomains
]

# CSRF trusted origins - required for CSRF exemption to work properly
CSRF_TRUSTED_ORIGINS = [
    "https://aiinterviewerbackend-2.onrender.com",
    "https://*.onrender.com",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# Email configuration (reads from environment; falls back to console backend in dev)
# Email Configuration - Support both SendGrid and SMTP
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
USE_SENDGRID = os.environ.get("USE_SENDGRID", "False").lower() == "true"

if USE_SENDGRID and SENDGRID_API_KEY:
    # Use SendGrid API for email sending
    EMAIL_BACKEND = "sgbackend.SendGridBackend"
    SENDGRID_API_KEY = SENDGRID_API_KEY  # Set for sendgrid-django package
    SENDGRID_SANDBOX_MODE_IN_DEBUG = False
    # Disable click tracking to prevent SendGrid from wrapping interview links
    SENDGRID_DISABLE_CLICK_TRACKING = True
    DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@example.com")
    # SendGrid uses API key, not SMTP credentials
    EMAIL_HOST = ""
    EMAIL_PORT = 587
    EMAIL_HOST_USER = ""
    EMAIL_HOST_PASSWORD = ""
    EMAIL_USE_TLS = False
    EMAIL_USE_SSL = False
else:
    # Fallback to SMTP (Gmail, etc.)
    EMAIL_BACKEND = os.environ.get(
        "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
    )
    EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "465"))
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
    EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "False").lower() == "true"
    EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", "False").lower() == "true"
    DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@example.com")

# Allow credentials if needed (tokens/cookies)
CORS_ALLOW_CREDENTIALS = True

# Permit common headers used by fetch/axios
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

# Allow iframe embedding for chatbot integration
X_FRAME_OPTIONS = 'SAMEORIGIN'

# Gemini / AI configuration
# IMPORTANT: Never hardcode API keys in source code!
# Set GEMINI_API_KEY or GOOGLE_API_KEY in your .env file
GEMINI_API_KEY = os.environ.get(
    "GEMINI_API_KEY",
    os.environ.get("GOOGLE_API_KEY", ""),  # Empty string if not set - will fail gracefully
)

# Deepgram configuration
# IMPORTANT: Set DEEPGRAM_API_KEY in your .env file for security
DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY", "")
if not DEEPGRAM_API_KEY:
    print("⚠️ WARNING: DEEPGRAM_API_KEY not set in environment. Deepgram features will be disabled.")

# Backend URL for generating interview links (used in emails)
# For Render: Set this to your Render backend service URL
# Example: https://aiinterviewerbackend-2.onrender.com
BACKEND_URL = os.environ.get(
    "BACKEND_URL",
    "http://localhost:8000"  # Default for local development
)

