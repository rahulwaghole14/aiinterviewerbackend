#!/usr/bin/env python
"""
Script to fix existing interview times to match their scheduled slots.
This updates started_at and ended_at for all interviews that have schedules.

Run: python fix_existing_interview_times.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "interview_app.settings")

try:
    django.setup()
except Exception as e:
    print(f"❌ Failed to setup Django: {e}")
    sys.exit(1)

from interviews.models import Interview, InterviewSchedule
from datetime import datetime
import pytz


def fix_interview_times():
    """Fix interview times for all interviews with schedules"""
    print("\n" + "=" * 70)
    print("  Fixing Interview Times from Scheduled Slots")
    print("=" * 70 + "\n")
    
    # Get all interviews that have schedules
    interviews_with_schedules = Interview.objects.filter(
        schedule__isnull=False
    ).select_related('schedule', 'schedule__slot')
    
    total = interviews_with_schedules.count()
    print(f"Found {total} interview(s) with schedules\n")
    
    if total == 0:
        print("No interviews with schedules found. Nothing to fix.")
        return
    
    fixed_count = 0
    error_count = 0
    
    ist = pytz.timezone('Asia/Kolkata')
    
    for interview in interviews_with_schedules:
        try:
            schedule = interview.schedule
            slot = schedule.slot
            
            if not (slot.interview_date and slot.start_time and slot.end_time):
                print(f"[WARNING] Interview {interview.id}: Slot missing date/time data")
                continue
            
            # Combine date and time - assume slot times are in IST
            start_datetime_naive = datetime.combine(slot.interview_date, slot.start_time)
            end_datetime_naive = datetime.combine(slot.interview_date, slot.end_time)
            
            # Localize to IST
            start_datetime = ist.localize(start_datetime_naive)
            end_datetime = ist.localize(end_datetime_naive)
            
            # Convert to UTC for storage
            start_datetime_utc = start_datetime.astimezone(pytz.UTC)
            end_datetime_utc = end_datetime.astimezone(pytz.UTC)
            
            # Check if times need updating
            if interview.started_at != start_datetime_utc or interview.ended_at != end_datetime_utc:
                old_start = interview.started_at
                old_end = interview.ended_at
                
                # Update interview times
                interview.started_at = start_datetime_utc
                interview.ended_at = end_datetime_utc
                interview.save(update_fields=["started_at", "ended_at"])
                
                print(f"[FIXED] Interview {interview.id} ({interview.candidate.full_name})")
                print(f"   Slot: {slot.start_time.strftime('%I:%M %p')} - {slot.end_time.strftime('%I:%M %p')} IST")
                if old_start:
                    print(f"   Old: {old_start.astimezone(ist).strftime('%I:%M %p')} IST")
                print(f"   New: {start_datetime.strftime('%I:%M %p')} IST")
                print()
                fixed_count += 1
            else:
                print(f"[OK] Interview {interview.id}: Times already correct")
                
        except Exception as e:
            print(f"[ERROR] Error fixing interview {interview.id}: {e}")
            error_count += 1
    
    print("=" * 70)
    print(f"\nSummary:")
    print(f"  Total interviews: {total}")
    print(f"  Fixed: {fixed_count}")
    print(f"  Already correct: {total - fixed_count - error_count}")
    print(f"  Errors: {error_count}")
    print()


if __name__ == "__main__":
    try:
        print("This will update started_at and ended_at for all interviews with schedules.")
        print("Running automatically...\n")
        fix_interview_times()
        print("[SUCCESS] Done!")
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] An error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

