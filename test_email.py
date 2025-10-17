#!/usr/bin/env python
"""
Simple SMTP email test using current Django settings.

Run:
  venv\Scripts\python.exe test_email.py
"""

import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "interview_app.settings")

try:
    import django
    django.setup()
except Exception as e:
    print("Failed to setup Django:", e)
    sys.exit(1)

from django.core.mail import send_mail, get_connection, EmailMessage  # noqa: E402
from django.conf import settings  # noqa: E402


def main() -> None:
    to_email = "paturkardhananjay4321@gmail.com"
    subject = "SMTP TEST - AI Interview Platform"
    body = (
        "This is a manual SMTP test email from AI Interview Platform.\n\n"
        "If you received this, SMTP is configured correctly."
    )

    print("EMAIL_HOST:", settings.EMAIL_HOST)
    print("DEFAULT_FROM_EMAIL:", settings.DEFAULT_FROM_EMAIL)

    # Try forced SMTP connection regardless of settings.EMAIL_BACKEND
    try:
        conn = get_connection(
            backend="django.core.mail.backends.smtp.EmailBackend",
            host=settings.EMAIL_HOST,
            port=getattr(settings, "EMAIL_PORT", 587),
            username=getattr(settings, "EMAIL_HOST_USER", ""),
            password=getattr(settings, "EMAIL_HOST_PASSWORD", ""),
            use_tls=getattr(settings, "EMAIL_USE_TLS", True),
            use_ssl=getattr(settings, "EMAIL_USE_SSL", False),
            fail_silently=False,
        )
        msg = EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, [to_email], connection=conn)
        sent = msg.send()
        print("Sent via forced SMTP:", sent)
    except Exception as e:
        print("Forced SMTP send failed:", e)
        # Fallback to configured backend
        sent = send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [to_email],
            fail_silently=False,
        )
        print("Sent via configured backend:", sent)
    print("OK")


if __name__ == "__main__":
    main()


