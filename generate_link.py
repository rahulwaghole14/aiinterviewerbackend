#!/usr/bin/env python
"""
Generate a valid interview link for a candidate and print the URL.

Usage:
  venv\Scripts\python.exe generate_link.py "Dhananjay Paturkar" [candidate_email]
If no args provided, defaults to name contains 'Dhananjay'.
"""

import os
import sys
import uuid
import base64
import hmac
import hashlib
from datetime import timedelta, datetime, time as dtime, date as ddate
import pytz

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "interview_app.settings")
import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402
from django.utils import timezone  # noqa: E402
from candidates.models import Candidate  # noqa: E402
from interviews.models import Interview  # noqa: E402


def get_candidate(name_arg: str | None, email_arg: str | None) -> Candidate:
    qs = Candidate.objects.all()
    if email_arg:
        cand = qs.filter(email__iexact=email_arg).first()
        if cand:
            return cand
    if name_arg:
        cand = qs.filter(full_name__icontains=name_arg).first()
        if cand:
            return cand
    # Fallback: just take any candidate
    cand = qs.first()
    if not cand:
        raise SystemExit("No candidates found to generate link for.")
    return cand


def next_occurrence_ist(hhmm: str) -> datetime:
    """Return next occurrence of hh:mm in Asia/Kolkata timezone (aware)."""
    ist = pytz.timezone("Asia/Kolkata")
    now_ist = timezone.now().astimezone(ist)
    hour, minute = map(int, hhmm.split(":"))
    target_ist = ist.localize(datetime(now_ist.year, now_ist.month, now_ist.day, hour, minute, 0))
    if target_ist <= now_ist:
        target_ist = target_ist + timedelta(days=1)
    return target_ist


def generate_link_for_candidate(cand: Candidate, at_time: str | None = None) -> str:
    interview, _ = Interview.objects.get_or_create(candidate=cand)

    if at_time:
        start_dt = next_occurrence_ist(at_time)
    else:
        start_dt = timezone.now()
    end_dt = start_dt + timedelta(minutes=10)

    interview.started_at = start_dt
    interview.ended_at = end_dt

    token_data = f"{interview.id}:{cand.email}:{interview.started_at.isoformat()}"
    secret_key = getattr(settings, "INTERVIEW_LINK_SECRET", "default-secret-key")
    signature = hmac.new(secret_key.encode("utf-8"), token_data.encode("utf-8"), hashlib.sha256).hexdigest()
    link_token = base64.urlsafe_b64encode(f"{interview.id}:{signature}".encode("utf-8")).decode("utf-8")

    interview.session_key = uuid.uuid4().hex
    interview.interview_link = link_token
    interview.save(update_fields=["started_at", "ended_at", "session_key", "interview_link", "updated_at"])

    # Ensure an InterviewSession is created/updated (also sets expiries)
    try:
        interview.generate_interview_link()
    except Exception as e:
        print("WARN: generate_interview_link failed to create session:", e)

    # Use the central URL generator to ensure correct path
    return interview.get_interview_url()


def main() -> None:
    name_arg = sys.argv[1] if len(sys.argv) > 1 else "Dhananjay"
    email_arg = sys.argv[2] if len(sys.argv) > 2 else None
    time_arg = sys.argv[3] if len(sys.argv) > 3 else None  # format "HH:MM"
    cand = get_candidate(name_arg, email_arg)
    url = generate_link_for_candidate(cand, time_arg)
    print(url)


if __name__ == "__main__":
    main()


