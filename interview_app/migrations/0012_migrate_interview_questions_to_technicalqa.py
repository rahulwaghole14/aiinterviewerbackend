# Generated migration to migrate existing InterviewQuestion data to TechnicalQA table

from django.db import migrations


def migrate_interview_questions_to_technicalqa(apps, schema_editor):
    """Migrate existing InterviewQuestion data to TechnicalQA table"""
    InterviewQuestion = apps.get_model('interview_app', 'InterviewQuestion')
    TechnicalQA = apps.get_model('interview_app', 'TechnicalQA')
    InterviewSession = apps.get_model('interview_app', 'InterviewSession')
    Interview = apps.get_model('interviews', 'Interview')
    
    print(f"\nMigrating InterviewQuestion data to TechnicalQA table...")
    
    # Get all interviews that have sessions
    interviews = Interview.objects.filter(session_key__isnull=False).exclude(session_key='')
    migrated_count = 0
    skipped_count = 0
    
    for interview in interviews:
        try:
            # Find session by session_key
            session = InterviewSession.objects.filter(session_key=interview.session_key).first()
            if not session:
                skipped_count += 1
                continue
            
            # Get all MAIN questions (not follow-ups) for this session, ordered by order
            main_questions = InterviewQuestion.objects.filter(
                session=session,
                question_level='MAIN'
            ).exclude(
                question_type='CODING'  # Skip coding questions - they're handled separately
            ).order_by('order', 'id')
            
            question_number = 1
            for question in main_questions:
                # Find the corresponding answer (INTERVIEWEE response)
                answer = InterviewQuestion.objects.filter(
                    session=session,
                    order=question.order,
                    role='INTERVIEWEE',
                    question_level='INTERVIEWEE_RESPONSE'
                ).first()
                
                # Get answer text
                answer_text = None
                if answer:
                    answer_text = answer.transcribed_answer or answer.question_text
                
                # Create TechnicalQA record
                TechnicalQA.objects.update_or_create(
                    session=session,
                    question_number=question_number,
                    defaults={
                        'interview': interview,
                        'question_text': question.question_text or '',
                        'answer_text': answer_text or 'No answer provided',
                        'transcribed_answer': answer_text or 'No answer provided',
                        'question_type': question.question_type or 'TECHNICAL',
                        'order': question_number,
                        'response_time_seconds': question.response_time_seconds or (answer.response_time_seconds if answer else None),
                    }
                )
                
                question_number += 1
            
            if question_number > 1:
                migrated_count += 1
                print(f"  Migrated {question_number - 1} Q&A pairs for interview {interview.id}")
        except Exception as e:
            print(f"  Error migrating interview {interview.id}: {e}")
            skipped_count += 1
    
    print(f"\nMigration complete:")
    print(f"  Migrated: {migrated_count} interviews")
    print(f"  Skipped: {skipped_count} interviews")


def reverse_migration(apps, schema_editor):
    """Reverse migration - clear TechnicalQA data"""
    TechnicalQA = apps.get_model('interview_app', 'TechnicalQA')
    TechnicalQA.objects.all().delete()
    print("Cleared all TechnicalQA records")


class Migration(migrations.Migration):

    dependencies = [
        ('interview_app', '0011_technicalqa'),
        ('interviews', '0009_alter_interviewslot_duration_minutes_and_more'),
    ]

    operations = [
        migrations.RunPython(migrate_interview_questions_to_technicalqa, reverse_migration),
    ]

