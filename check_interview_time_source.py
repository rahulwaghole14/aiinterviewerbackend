#!/usr/bin/env python
"""
Check where interview times are coming from - database investigation
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

from interviews.models import Interview, InterviewSchedule
from datetime import datetime
import pytz

def check_latest_interview():
    """Check the most recent scheduled interview"""
    print("\n" + "=" * 70)
    print("  Interview Time Source Investigation")
    print("=" * 70 + "\n")
    
    # Get most recent scheduled interview
    interview = Interview.objects.filter(
        schedule__isnull=False,
        status='scheduled'
    ).order_by('-updated_at').first()
    
    if not interview:
        print("No scheduled interviews found")
        return
    
    print(f"Interview ID: {interview.id}")
    print(f"Candidate: {interview.candidate.full_name}")
    print(f"Status: {interview.status}")
    print(f"Created: {interview.created_at}")
    print(f"Updated: {interview.updated_at}")
    print()
    
    print("=== TIME SOURCE 1: interview.started_at/ended_at ===")
    print(f"started_at (DB value): {interview.started_at}")
    print(f"ended_at (DB value): {interview.ended_at}")
    
    if interview.started_at and interview.ended_at:
        ist = pytz.timezone('Asia/Kolkata')
        start_ist = interview.started_at.astimezone(ist)
        end_ist = interview.ended_at.astimezone(ist)
        print(f"\n  Converted to IST:")
        print(f"  started_at: {start_ist.strftime('%I:%M %p')} IST")
        print(f"  ended_at: {end_ist.strftime('%I:%M %p')} IST")
    
    print()
    print("=== TIME SOURCE 2: schedule.slot.start_time/end_time ===")
    if hasattr(interview, 'schedule') and interview.schedule:
        schedule = interview.schedule
        slot = schedule.slot
        
        print(f"Schedule ID: {schedule.id}")
        print(f"Slot ID: {slot.id}")
        print(f"Slot Date: {slot.interview_date}")
        print(f"Slot Start Time (raw TimeField): {slot.start_time}")
        print(f"Slot End Time (raw TimeField): {slot.end_time}")
        
        # What should be stored based on slot
        if slot.interview_date and slot.start_time and slot.end_time:
            ist = pytz.timezone('Asia/Kolkata')
            start_dt = ist.localize(datetime.combine(slot.interview_date, slot.start_time))
            end_dt = ist.localize(datetime.combine(slot.interview_date, slot.end_time))
            
            start_utc = start_dt.astimezone(pytz.UTC)
            end_utc = end_dt.astimezone(pytz.UTC)
            
            print(f"\n  What SHOULD be in started_at/ended_at:")
            print(f"  Should be: {start_utc} UTC")
            print(f"  Actually is: {interview.started_at} UTC")
            print(f"  Match: {interview.started_at == start_utc}")
            
            print(f"\n  Slot time in IST: {slot.start_time.strftime('%I:%M %p')} IST")
            if interview.started_at:
                print(f"  Interview time in IST: {interview.started_at.astimezone(ist).strftime('%I:%M %p')} IST")
                diff = abs((interview.started_at - start_utc).total_seconds())
                print(f"  Time difference: {diff/3600:.2f} hours")
    else:
        print("  No schedule found")
    
    print()
    print("=" * 70)

if __name__ == "__main__":
    check_latest_interview()

