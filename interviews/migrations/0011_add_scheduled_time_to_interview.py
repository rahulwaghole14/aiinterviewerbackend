# Generated migration for adding scheduled_time to Interview model

from django.db import migrations, models
from django.utils import timezone


def set_scheduled_time_from_slot(apps, schema_editor):
    """Set scheduled_time from slot for existing interviews"""
    Interview = apps.get_model('interviews', 'Interview')
    InterviewSlot = apps.get_model('interviews', 'InterviewSlot')
    
    for interview in Interview.objects.filter(slot__isnull=False, scheduled_time__isnull=True):
        if interview.slot:
            slot = interview.slot
            # Manually combine date and time fields since get_full_start_datetime() method isn't available in migration
            if slot.interview_date and slot.start_time:
                from datetime import datetime, time
                from django.utils import timezone
                
                # Create naive datetime
                dt_naive = datetime.combine(slot.interview_date, slot.start_time)
                
                # Make it timezone-aware (assuming UTC for migration)
                dt_aware = timezone.make_aware(dt_naive)
                
                interview.scheduled_time = dt_aware
                interview.save(update_fields=['scheduled_time'])


class Migration(migrations.Migration):

    dependencies = [
        ('interviews', '0009_alter_interviewslot_duration_minutes_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='interview',
            name='scheduled_time',
            field=models.DateTimeField(
                blank=True,
                help_text='Exact scheduled interview time from slot',
                null=True
            ),
        ),
        
        # Update existing interviews to set scheduled_time from slot
        migrations.RunPython(
            code=set_scheduled_time_from_slot,
            reverse_code=migrations.RunPython.noop
        ),
    ]
