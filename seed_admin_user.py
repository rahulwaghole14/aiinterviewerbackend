#!/usr/bin/env python
"""
Seed or update an admin user for local development.

Usage (from project root):
  venv\Scripts\python.exe seed_admin_user.py
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "interview_app.settings")
django.setup()

from django.contrib.auth import get_user_model  # noqa: E402


def main() -> None:
    User = get_user_model()
    email = "admin@example.com"
    password = "admin@123"

    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            "username": email,
            "full_name": "Admin User",
            "role": "ADMIN",
            "is_active": True,
        },
    )

    if not created:
        user.username = email
        if not getattr(user, "full_name", None):
            user.full_name = "Admin User"
        user.role = "ADMIN"
        user.is_active = True

    user.set_password(password)
    user.save()

    print(f"{'Created' if created else 'Updated'} {email} with password {password}")


if __name__ == "__main__":
    main()


