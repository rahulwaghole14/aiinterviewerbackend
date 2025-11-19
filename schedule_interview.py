#!/usr/bin/env python
"""
Schedule an AI interview and send the candidate email using current SMTP settings.

Usage:
  venv\Scripts\python.exe schedule_interview.py "Candidate Name" candidate@email "Data Scientist" "00:30"

Defaults in this script:
  - Company: first existing Company or creates "Demo Company"
  - Domain: creates/uses "Data Science"
  - Slot duration: 10 minutes
  - Date: next occurrence of the provided HH:MM (today if still upcoming, else tomorrow)
"""

import os
import sys
from datetime import datetime, time, timedelta, date

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "interview_app.settings")
import django  # noqa: E402

django.setup()

from django.utils import timezone  # noqa: E402
from companies.models import Company  # noqa: E402
from jobs.models import Job, Domain  # noqa: E402
from candidates.models import Candidate  # noqa: E402
from interviews.models import Interview, InterviewSlot, InterviewSchedule  # noqa: E402
from notifications.services import NotificationService  # noqa: E402
import pytz  # noqa: E402


def get_next_occurrence(hhmm: str) -> date:
    now = timezone.localtime()
    target_hour, target_minute = map(int, hhmm.split(":"))
    target_today = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
    if target_today > now:
        return target_today.date()
    return (target_today + timedelta(days=1)).date()


def parse_args():
    # Args: name, email, job_title, hh:mm
    name = sys.argv[1] if len(sys.argv) > 1 else "Dhananjay Paturkar"
    email = sys.argv[2] if len(sys.argv) > 2 else "paturkardhananjay4321@gmail.com"
    job_title = sys.argv[3] if len(sys.argv) > 3 else "Data Scientist"
    hhmm = sys.argv[4] if len(sys.argv) > 4 else "00:30"
    return name, email, job_title, hhmm


def main() -> None:
    name, email, job_title, hhmm = parse_args()

    # Company
    company = Company.objects.first()
    if not company:
        company = Company.objects.create(name="Demo Company", email="noreply@example.com")

    # Domain
    domain, _ = Domain.objects.get_or_create(name="Data Science", defaults={"description": "Data Science"})

    # Job
    job, _ = Job.objects.get_or_create(
        job_title=job_title,
        company_name=company.name,
        defaults={
            "domain": domain,
            "spoc_email": os.environ.get("DEFAULT_FROM_EMAIL", "noreply@example.com"),
            "hiring_manager_email": os.environ.get("DEFAULT_FROM_EMAIL", "noreply@example.com"),
            "current_team_size_info": "",
            "number_to_hire": 1,
            "position_level": Job.PositionLevel.IC,
            "current_process": "",
            "tech_stack_details": "Python, ML, Data",
            "job_description": "Data Scientist position",
        },
    )

    # Candidate
    candidate, _ = Candidate.objects.get_or_create(
        email=email,
        defaults={
            "full_name": name,
            "domain": domain.name,
            "status": Candidate.Status.NEW,
        },
    )
    if not candidate.full_name:
        candidate.full_name = name
        candidate.save(update_fields=["full_name"])

    # Interview
    interview, _ = Interview.objects.get_or_create(candidate=candidate, job=job)

    # Next occurrence date for provided time
    target_date = get_next_occurrence(hhmm)
    hour, minute = map(int, hhmm.split(":"))
    start_time = time(hour, minute)
    end_dt = (datetime.combine(date.today(), start_time) + timedelta(minutes=10)).time()
    end_time = end_dt

    # Slot (ensure available)
    slot, created = InterviewSlot.objects.get_or_create(
        company=company,
        job=job,
        interview_date=target_date,
        start_time=start_time,
        defaults={
            "end_time": end_time,
            "duration_minutes": 10,
            "status": InterviewSlot.Status.AVAILABLE,
            "max_candidates": 1,
            "current_bookings": 0,
        },
    )
    if not created:
        # Ensure it is available and with correct end time/duration
        slot.end_time = end_time
        slot.duration_minutes = 10
        slot.status = InterviewSlot.Status.AVAILABLE
        slot.current_bookings = 0
        slot.max_candidates = max(slot.max_candidates, 1)
        slot.save()

    # Schedule - Check if interview already has a schedule
    existing_schedule = InterviewSchedule.objects.filter(interview=interview).first()
    if existing_schedule:
        # Unbook the old slot if it exists and is different
        old_slot = existing_schedule.slot
        if old_slot and old_slot != slot:
            # Decrement bookings on old slot
            old_slot.current_bookings = max(0, old_slot.current_bookings - 1)
            if old_slot.current_bookings < old_slot.max_candidates:
                old_slot.status = InterviewSlot.Status.AVAILABLE
            old_slot.save()
        
        # Update existing schedule to point to new slot
        existing_schedule.slot = slot
        existing_schedule.status = InterviewSchedule.ScheduleStatus.PENDING
        existing_schedule.booking_notes = "Auto-scheduled"
        existing_schedule.save()
        schedule = existing_schedule
    else:
        # Create new schedule
        schedule, _ = InterviewSchedule.objects.get_or_create(
            interview=interview,
            slot=slot,
            defaults={"status": InterviewSchedule.ScheduleStatus.PENDING, "booking_notes": "Auto-scheduled"},
        )

    # Book the slot and persist
    slot.book_slot()

    # IMPORTANT: ALWAYS update interview started_at and ended_at from slot date + time
    # This ensures times match the slot even if interview was created with different times
    # Combine slot.interview_date with slot.start_time and slot.end_time to create proper DateTime objects
    # IMPORTANT: Interpret slot times in IST (Asia/Kolkata) since that's likely where users are
    if slot.interview_date and slot.start_time and slot.end_time:
        # Combine date and time - assume slot times are in IST (India Standard Time)
        ist = pytz.timezone('Asia/Kolkata')
        start_datetime_naive = datetime.combine(slot.interview_date, slot.start_time)
        end_datetime_naive = datetime.combine(slot.interview_date, slot.end_time)
        
        # Localize to IST (treat slot times as IST)
        start_datetime = ist.localize(start_datetime_naive)
        end_datetime = ist.localize(end_datetime_naive)
        
        # Convert to UTC for storage (Django stores in UTC)
        start_datetime_utc = start_datetime.astimezone(pytz.UTC)
        end_datetime_utc = end_datetime.astimezone(pytz.UTC)
        
        # ALWAYS update interview times to match slot (stored in UTC) - overwrite any existing values
        interview.started_at = start_datetime_utc
        interview.ended_at = end_datetime_utc
        interview.status = Interview.Status.SCHEDULED
        
        # Update link expiration to 2 hours after interview end time
        interview.link_expires_at = end_datetime_utc + timedelta(hours=2)
        
        interview.save(update_fields=["started_at", "ended_at", "status", "link_expires_at"])
        
        # Regenerate interview link and session key to ensure they're valid
        # This also creates/updates the InterviewSession
        try:
            interview.generate_interview_link()
            # Update InterviewSession scheduled_at if it exists
            from interview_app.models import InterviewSession
            if interview.session_key:
                try:
                    session = InterviewSession.objects.get(session_key=interview.session_key)
                    session.scheduled_at = start_datetime_utc
                    session.status = "SCHEDULED"
                    session.save(update_fields=["scheduled_at", "status"])
                except InterviewSession.DoesNotExist:
                    pass
        except Exception as e:
            print(f"Warning: Could not regenerate interview link: {e}")

    # Send email notification to candidate (generates link if needed)
    NotificationService.send_candidate_interview_scheduled_notification(interview)

    # Print summary
    print("✅ Interview scheduled")
    print(f"Candidate: {candidate.full_name} <{candidate.email}>")
    print(f"Job: {job.job_title} at {job.company_name}")
    print(f"When: {target_date} {hhmm} ({slot.duration_minutes} min)")
    try:
        url = interview.get_interview_url()
        print(f"Interview URL: {url}")
    except Exception:
        pass


if __name__ == "__main__":
    main()


