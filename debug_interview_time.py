#!/usr/bin/env python
"""
Debug script to check a specific interview's time data
Usage: python debug_interview_time.py <interview_id>
"""

import os
import sys
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "interview_app.settings")

try:
    django.setup()
except Exception as e:
    print(f"Failed to setup Django: {e}")
    sys.exit(1)

from interviews.models import Interview
from datetime import datetime
import pytz

def debug_interview(interview_id):
    """Debug interview time information"""
    try:
        interview = Interview.objects.get(id=interview_id)
    except Interview.DoesNotExist:
        print(f"Interview {interview_id} not found")
        return
    
    print("\n" + "=" * 70)
    print(f"  Interview Debug: {interview_id}")
    print("=" * 70 + "\n")
    
    print(f"Candidate: {interview.candidate.full_name}")
    print(f"Status: {interview.status}")
    print()
    
    # Check started_at/ended_at
    print("Interview Times (stored as UTC in database):")
    print(f"  started_at: {interview.started_at}")
    print(f"  ended_at: {interview.ended_at}")
    
    if interview.started_at and interview.ended_at:
        ist = pytz.timezone('Asia/Kolkata')
        start_ist = interview.started_at.astimezone(ist)
        end_ist = interview.ended_at.astimezone(ist)
        print(f"\n  In IST:")
        print(f"    started_at: {start_ist.strftime('%I:%M %p')} IST")
        print(f"    ended_at: {end_ist.strftime('%I:%M %p')} IST")
    
    # Check schedule
    print("\nSchedule Information:")
    if hasattr(interview, 'schedule') and interview.schedule:
        schedule = interview.schedule
        slot = schedule.slot
        
        print(f"  Schedule ID: {schedule.id}")
        print(f"  Slot ID: {slot.id}")
        print(f"  Slot Date: {slot.interview_date}")
        print(f"  Slot Start Time (raw): {slot.start_time}")
        print(f"  Slot End Time (raw): {slot.end_time}")
        print(f"  Slot Status: {slot.status}")
        
        # Show what should be stored
        if slot.interview_date and slot.start_time and slot.end_time:
            ist = pytz.timezone('Asia/Kolkata')
            start_dt = ist.localize(datetime.combine(slot.interview_date, slot.start_time))
            end_dt = ist.localize(datetime.combine(slot.interview_date, slot.end_time))
            
            start_utc = start_dt.astimezone(pytz.UTC)
            end_utc = end_dt.astimezone(pytz.UTC)
            
            print(f"\n  Expected stored times (IST to UTC):")
            print(f"    Slot time IST: {slot.start_time.strftime('%I:%M %p')} IST")
            print(f"    Should be stored as: {start_utc} UTC")
            print(f"    Actually stored as: {interview.started_at} UTC")
            
            if interview.started_at != start_utc:
                print(f"\n  [MISMATCH] Interview times don't match slot times!")
                print(f"    Difference: {interview.started_at} vs {start_utc}")
            else:
                print(f"\n  [OK] Interview times match slot times")
    else:
        print("  No schedule found")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        interview_id = sys.argv[1]
        debug_interview(interview_id)
    else:
        # Debug most recent interview
        latest = Interview.objects.filter(
            schedule__isnull=False
        ).order_by('-created_at').first()
        
        if latest:
            print(f"Debugging most recent interview: {latest.id}")
            debug_interview(latest.id)
        else:
            print("No interviews with schedules found")

