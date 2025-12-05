import logging
import json
import re
import os
from datetime import datetime
from django.utils import timezone
from django.contrib.auth import get_user_model

# Configure logging
# Ensure logs directory exists
try:
    from django.conf import settings
    log_dir = os.path.join(settings.BASE_DIR, "logs")
except Exception:
    # Fallback if Django settings not initialized
    log_dir = "logs"

# Create logs directory if it doesn't exist
try:
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, "ai_interviewer.log")
except Exception as e:
    log_file_path = None
    print(f"⚠️ Warning: Could not create logs directory: {e}")

# Create handlers
handlers = [logging.StreamHandler()]
if log_file_path:
    try:
        # Try to create file handler
        file_handler = logging.FileHandler(log_file_path)
        handlers.append(file_handler)
    except Exception as e:
        # If file handler creation fails, only use StreamHandler
        print(f"⚠️ Warning: Could not create log file handler: {e}")
        print(f"   Logging to console only")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=handlers,
)

logger = logging.getLogger("ai_interviewer")


class LogSanitizer:
    """Sanitize sensitive data from logs"""

    SENSITIVE_FIELDS = [
        "password",
        "token",
        "secret",
        "key",
        "auth",
        "credential",
        "ssn",
        "credit_card",
        "bank_account",
        "phone",
        "address",
    ]

    @staticmethod
    def sanitize_data(data):
        """Remove sensitive data from log entries"""
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                if any(
                    sensitive in key.lower()
                    for sensitive in LogSanitizer.SENSITIVE_FIELDS
                ):
                    sanitized[key] = "[REDACTED]"
                elif isinstance(value, dict):
                    sanitized[key] = LogSanitizer.sanitize_data(value)
                elif isinstance(value, list):
                    sanitized[key] = [
                        (
                            LogSanitizer.sanitize_data(item)
                            if isinstance(item, dict)
                            else item
                        )
                        for item in value
                    ]
                else:
                    sanitized[key] = value
            return sanitized
        return data


class ActionLogger:
    """
    Comprehensive action logger for tracking all user activities and system events
    """

    @staticmethod
    def log_user_action(user, action, details=None, status="SUCCESS", ip_address=None):
        """
        Log user actions with comprehensive details

        Args:
            user: User object or user ID
            action: Action being performed (e.g., 'resume_upload', 'interview_schedule')
            details: Additional details about the action
            status: Status of the action (SUCCESS, FAILED, BLOCKED)
            ip_address: IP address of the user
        """
        try:
            # Get user info
            if hasattr(user, "id"):
                user_id = user.id
                user_email = getattr(user, "email", "unknown")
                user_role = getattr(user, "role", "unknown")
            else:
                user_id = user
                user_email = "unknown"
                user_role = "unknown"

            # Create log entry
            log_entry = {
                "timestamp": timezone.now().isoformat(),
                "user_id": user_id,
                "user_email": user_email,
                "user_role": user_role,
                "action": action,
                "status": status,
                "ip_address": ip_address,
                "details": LogSanitizer.sanitize_data(details or {}),
            }

            # Log to file
            logger.info(f"USER_ACTION: {json.dumps(log_entry)}")

            # Log to console for development
            if settings.DEBUG:
                print(f"🔍 LOG: {action} by {user_email} ({user_role}) - {status}")

        except Exception as e:
            logger.error(f"Error logging user action: {e}")

    @staticmethod
    def log_security_event(event_type, user=None, details=None, severity="INFO"):
        """
        Log security-related events

        Args:
            event_type: Type of security event (LOGIN, LOGOUT, PERMISSION_DENIED, etc.)
            user: User object or user ID
            details: Additional details about the event
            severity: Severity level (INFO, WARNING, ERROR, CRITICAL)
        """
        try:
            user_info = {}
            if user:
                if hasattr(user, "id"):
                    user_info = {
                        "user_id": user.id,
                        "user_email": getattr(user, "email", "unknown"),
                        "user_role": getattr(user, "role", "unknown"),
                    }
                else:
                    user_info = {"user_id": user}

            log_entry = {
                "timestamp": timezone.now().isoformat(),
                "event_type": event_type,
                "severity": severity,
                "user": LogSanitizer.sanitize_data(user_info),
                "details": LogSanitizer.sanitize_data(details or {}),
            }

            # Log with appropriate level
            if severity == "CRITICAL":
                logger.critical(f"SECURITY_EVENT: {json.dumps(log_entry)}")
            elif severity == "ERROR":
                logger.error(f"SECURITY_EVENT: {json.dumps(log_entry)}")
            elif severity == "WARNING":
                logger.warning(f"SECURITY_EVENT: {json.dumps(log_entry)}")
            else:
                logger.info(f"SECURITY_EVENT: {json.dumps(log_entry)}")

        except Exception as e:
            logger.error(f"Error logging security event: {e}")

    @staticmethod
    def log_system_event(event_type, details=None, severity="INFO"):
        """
        Log system-level events

        Args:
            event_type: Type of system event (STARTUP, SHUTDOWN, ERROR, etc.)
            details: Additional details about the event
            severity: Severity level
        """
        try:
            log_entry = {
                "timestamp": timezone.now().isoformat(),
                "event_type": event_type,
                "severity": severity,
                "details": LogSanitizer.sanitize_data(details or {}),
            }

            if severity == "ERROR":
                logger.error(f"SYSTEM_EVENT: {json.dumps(log_entry)}")
            elif severity == "WARNING":
                logger.warning(f"SYSTEM_EVENT: {json.dumps(log_entry)}")
            else:
                logger.info(f"SYSTEM_EVENT: {json.dumps(log_entry)}")

        except Exception as e:
            logger.error(f"Error logging system event: {e}")

    @staticmethod
    def log_api_request(request, response, user=None):
        """
        Log API requests and responses

        Args:
            request: Django request object
            response: Django response object
            user: User object
        """
        try:
            # Get user info
            user_info = {}
            if user and user.is_authenticated:
                user_info = {
                    "user_id": user.id,
                    "user_email": getattr(user, "email", "unknown"),
                    "user_role": getattr(user, "role", "unknown"),
                }

            # Get request info (sanitized)
            request_info = {
                "method": request.method,
                "path": request.path,
                "ip_address": request.META.get("REMOTE_ADDR", "unknown"),
                "user_agent": request.META.get("HTTP_USER_AGENT", "unknown"),
            }

            # Get response info
            response_info = {
                "status_code": response.status_code,
                "content_type": response.get("Content-Type", "unknown"),
            }

            log_entry = {
                "timestamp": timezone.now().isoformat(),
                "request": LogSanitizer.sanitize_data(request_info),
                "response": response_info,
                "user": LogSanitizer.sanitize_data(user_info),
            }

            # Log based on status code
            if response.status_code >= 500:
                logger.error(f"API_REQUEST: {json.dumps(log_entry)}")
            elif response.status_code >= 400:
                logger.warning(f"API_REQUEST: {json.dumps(log_entry)}")
            else:
                logger.info(f"API_REQUEST: {json.dumps(log_entry)}")

        except Exception as e:
            logger.error(f"Error logging API request: {e}")


# Convenience functions for common actions
def log_resume_upload(user, resume_id, filename, status="SUCCESS", details=None):
    """Log resume upload action"""
    ActionLogger.log_user_action(
        user=user,
        action="resume_upload",
        details={"resume_id": resume_id, "filename": filename, **(details or {})},
        status=status,
    )


def log_bulk_resume_upload(
    user, file_count, success_count, failed_count, status="SUCCESS", details=None
):
    """Log bulk resume upload action"""
    ActionLogger.log_user_action(
        user=user,
        action="bulk_resume_upload",
        details={
            "file_count": file_count,
            "success_count": success_count,
            "failed_count": failed_count,
            **(details or {}),
        },
        status=status,
    )


def log_interview_schedule(
    user, interview_id, candidate_id, job_id, status="SUCCESS", details=None
):
    """Log interview scheduling action"""
    ActionLogger.log_user_action(
        user=user,
        action="interview_schedule",
        details={
            "interview_id": interview_id,
            "candidate_id": candidate_id,
            "job_id": job_id,
            **(details or {}),
        },
        status=status,
    )


def log_permission_denied(user, action, reason, ip_address=None):
    """Log permission denied events"""
    ActionLogger.log_security_event(
        event_type="PERMISSION_DENIED",
        user=user,
        details={"action": action, "reason": reason},
        severity="WARNING",
    )

    # Also log as user action
    ActionLogger.log_user_action(
        user=user,
        action=action,
        details={"reason": reason},
        status="BLOCKED",
        ip_address=ip_address,
    )


def log_user_login(user, ip_address=None):
    """Log user login"""
    ActionLogger.log_security_event(
        event_type="USER_LOGIN",
        user=user,
        details={"ip_address": ip_address},
        severity="INFO",
    )


def log_user_logout(user, ip_address=None):
    """Log user logout"""
    ActionLogger.log_security_event(
        event_type="USER_LOGOUT",
        user=user,
        details={"ip_address": ip_address},
        severity="INFO",
    )


def log_user_registration(user, ip_address=None):
    """Log user registration"""
    ActionLogger.log_security_event(
        event_type="USER_REGISTRATION",
        user=user,
        details={"ip_address": ip_address},
        severity="INFO",
    )
