from django.db import migrations

def create_default_templates(apps, schema_editor):
    NotificationTemplate = apps.get_model('notifications', 'NotificationTemplate')
    
    templates = [
        {
            'name': 'interview_scheduled',
            'notification_type': 'interview_scheduled',
            'title_template': 'Interview Scheduled for {{candidate_name}}',
            'message_template': 'An interview has been scheduled for {{candidate_name}} for the position of {{job_title}} at {{company_name}} on {{interview_date}}. Please review the details and prepare accordingly.',
            'channels': ['email', 'in_app'],
            'priority': 'high'
        },
        {
            'name': 'interview_reminder',
            'notification_type': 'interview_reminder',
            'title_template': 'Interview Reminder: {{candidate_name}}',
            'message_template': 'Reminder: You have an upcoming interview with {{candidate_name}} for {{job_title}} on {{interview_date}}. Please ensure you are prepared.',
            'channels': ['email', 'in_app'],
            'priority': 'high'
        },
        {
            'name': 'resume_processed',
            'notification_type': 'resume_processed',
            'title_template': 'Resume Processed: {{filename}}',
            'message_template': 'Your resume file "{{filename}}" has been successfully processed. Extracted data: {{extracted_data}}',
            'channels': ['email', 'in_app'],
            'priority': 'medium'
        },
        {
            'name': 'bulk_upload_completed',
            'notification_type': 'bulk_upload_completed',
            'title_template': 'Bulk Upload Completed',
            'message_template': 'Bulk resume upload completed. Total files: {{total_files}}, Successful: {{successful}}, Failed: {{failed}}.',
            'channels': ['email', 'in_app'],
            'priority': 'medium'
        },
        {
            'name': 'candidate_added',
            'notification_type': 'candidate_added',
            'title_template': 'New Candidate Added: {{candidate_name}}',
            'message_template': 'A new candidate {{candidate_name}} ({{candidate_email}}) has been added to the system for {{domain}} position.',
            'channels': ['email', 'in_app'],
            'priority': 'medium'
        },
        {
            'name': 'job_created',
            'notification_type': 'job_created',
            'title_template': 'New Job Posted: {{job_title}}',
            'message_template': 'A new job "{{job_title}}" has been posted at {{company_name}} for {{position_level}} level. Number of positions: {{number_to_hire}}.',
            'channels': ['email', 'in_app'],
            'priority': 'medium'
        },
        {
            'name': 'evaluation_completed',
            'notification_type': 'evaluation_completed',
            'title_template': 'Interview Evaluation Completed',
            'message_template': 'The evaluation for the interview has been completed and is ready for review.',
            'channels': ['email', 'in_app'],
            'priority': 'medium'
        },
        {
            'name': 'system_alert',
            'notification_type': 'system_alert',
            'title_template': 'System Alert',
            'message_template': 'A system alert has been generated. Please check the details.',
            'channels': ['email', 'in_app'],
            'priority': 'high'
        }
    ]
    
    for template_data in templates:
        NotificationTemplate.objects.get_or_create(
            name=template_data['name'],
            defaults=template_data
        )

def remove_default_templates(apps, schema_editor):
    NotificationTemplate = apps.get_model('notifications', 'NotificationTemplate')
    template_names = [
        'interview_scheduled', 'interview_reminder', 'resume_processed',
        'bulk_upload_completed', 'candidate_added', 'job_created',
        'evaluation_completed', 'system_alert'
    ]
    NotificationTemplate.objects.filter(name__in=template_names).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('notifications', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_templates, remove_default_templates),
    ] 