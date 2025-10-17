#!/usr/bin/env python
"""
Ensure there is a single Candidate for the given email and update its full name.

Usage:
  venv\Scripts\python.exe fix_candidate_name.py "Full Name" candidate@email
"""

import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "interview_app.settings")

import django  # noqa: E402

django.setup()

from candidates.models import Candidate  # noqa: E402


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: fix_candidate_name.py \"Full Name\" email@example.com")
        raise SystemExit(1)

    full_name = sys.argv[1].strip()
    email = sys.argv[2].strip()

    qs = Candidate.objects.filter(email__iexact=email).order_by("id")
    if qs.exists():
        # Keep the first, delete duplicates
        primary = qs.first()
        for dup in qs[1:]:
            dup.delete()
        if primary.full_name != full_name:
            primary.full_name = full_name
            primary.save(update_fields=["full_name"])
        print(f"Candidate normalized: id={primary.id}, name={primary.full_name}, email={email}")
    else:
        c = Candidate.objects.create(full_name=full_name, email=email)
        print(f"Candidate created: id={c.id}, name={c.full_name}, email={email}")


if __name__ == "__main__":
    main()


