# Generated migration to migrate existing proctoring PDF URLs to ProctoringPDF table

from django.db import migrations


def migrate_existing_urls(apps, schema_editor):
    """Migrate existing proctoring PDF URLs from Evaluation.details to ProctoringPDF table"""
    Evaluation = apps.get_model('evaluation', 'Evaluation')
    ProctoringPDF = apps.get_model('evaluation', 'ProctoringPDF')
    Interview = apps.get_model('interviews', 'Interview')
    
    evaluations = Evaluation.objects.all()
    migrated_count = 0
    
    print(f"\nMigrating proctoring PDF URLs from Evaluation.details to ProctoringPDF table...")
    print(f"Total evaluations: {evaluations.count()}\n")
    
    for evaluation in evaluations:
        if not evaluation.details or not isinstance(evaluation.details, dict):
            continue
        
        # Get URL from evaluation.details
        gcs_url = evaluation.details.get('proctoring_pdf_gcs_url')
        local_path = evaluation.details.get('proctoring_pdf')
        
        if gcs_url or local_path:
            try:
                # Check if ProctoringPDF record already exists
                proctoring_pdf, created = ProctoringPDF.objects.get_or_create(
                    interview=evaluation.interview,
                    defaults={
                        'gcs_url': gcs_url,
                        'local_path': local_path,
                    }
                )
                
                # Update if record exists but URL is missing
                if not created and not proctoring_pdf.gcs_url and gcs_url:
                    proctoring_pdf.gcs_url = gcs_url
                    proctoring_pdf.local_path = local_path
                    proctoring_pdf.save()
                    print(f"  Updated ProctoringPDF for interview {evaluation.interview.id}")
                elif created:
                    print(f"  Created ProctoringPDF for interview {evaluation.interview.id}")
                    migrated_count += 1
            except Exception as e:
                print(f"  Error migrating interview {evaluation.interview.id}: {e}")
    
    print(f"\nMigrated {migrated_count} proctoring PDF URLs to ProctoringPDF table")


def reverse_migration(apps, schema_editor):
    """Reverse migration - cannot restore URLs to evaluation.details"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('evaluation', '0010_proctoringpdf'),
    ]

    operations = [
        migrations.RunPython(migrate_existing_urls, reverse_migration),
    ]

