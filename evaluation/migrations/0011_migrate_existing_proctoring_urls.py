# Generated migration to migrate existing proctoring PDF URLs to ProctoringPDF table

from django.db import migrations
import re


def clean_gcs_url(url):
    """Clean malformed GCS URL - remove app URL prefixes"""
    if not url or not isinstance(url, str):
        return None
    
    original_url = url.strip()
    
    # Extract ONLY the GCS URL part (everything from storage.googleapis.com onwards)
    if 'storage.googleapis.com' in original_url:
        gcs_index = original_url.find('storage.googleapis.com')
        if gcs_index != -1:
            # Extract everything from storage.googleapis.com onwards
            clean_url = original_url[gcs_index:]
            
            # Remove any malformed prefixes
            clean_url = re.sub(r'^https?\/\/+', '', clean_url)  # Remove https// or https///
            clean_url = re.sub(r'^https?:\/\/+', '', clean_url)  # Remove https:// or https:///
            
            # Remove any app URL patterns
            clean_url = re.sub(r'^[^/]+\.(app|run|com)https?\/\/+', '', clean_url)
            clean_url = re.sub(r'^[^/]+\.(app|run|com)https?:\/\/+', '', clean_url)
            
            # Ensure it starts with storage.googleapis.com
            if not clean_url.startswith('storage.googleapis.com'):
                gcs_index = clean_url.find('storage.googleapis.com')
                if gcs_index != -1:
                    clean_url = clean_url[gcs_index:]
                else:
                    clean_url = None
            
            # Construct clean URL with https:// prefix
            if clean_url and clean_url.startswith('storage.googleapis.com'):
                clean_url = f"https://{clean_url}"
                
                # Final validation
                if clean_url.startswith('https://storage.googleapis.com/'):
                    return clean_url
    
    return None


def migrate_existing_urls(apps, schema_editor):
    """Migrate existing proctoring PDF URLs from Evaluation.details to ProctoringPDF table"""
    Evaluation = apps.get_model('evaluation', 'Evaluation')
    ProctoringPDF = apps.get_model('evaluation', 'ProctoringPDF')
    Interview = apps.get_model('interviews', 'Interview')
    
    evaluations = Evaluation.objects.all()
    migrated_count = 0
    cleaned_count = 0
    
    print(f"\nMigrating proctoring PDF URLs from Evaluation.details to ProctoringPDF table...")
    print(f"Total evaluations: {evaluations.count()}\n")
    
    for evaluation in evaluations:
        if not evaluation.details or not isinstance(evaluation.details, dict):
            continue
        
        # Get URL from evaluation.details
        gcs_url = evaluation.details.get('proctoring_pdf_gcs_url')
        local_path = evaluation.details.get('proctoring_pdf')
        
        # CRITICAL: Clean the URL before migrating
        clean_url = None
        if gcs_url:
            clean_url = clean_gcs_url(gcs_url)
            if clean_url != gcs_url:
                cleaned_count += 1
                print(f"  ⚠️ Cleaned malformed URL for interview {evaluation.interview.id}")
                print(f"     Original: {gcs_url[:80]}...")
                print(f"     Cleaned: {clean_url[:80]}...")
        
        if clean_url or local_path:
            try:
                # Check if ProctoringPDF record already exists
                proctoring_pdf, created = ProctoringPDF.objects.get_or_create(
                    interview=evaluation.interview,
                    defaults={
                        'gcs_url': clean_url,  # Use cleaned URL
                        'local_path': local_path,
                    }
                )
                
                # Update if record exists but URL is missing or malformed
                if not created:
                    if not proctoring_pdf.gcs_url and clean_url:
                        proctoring_pdf.gcs_url = clean_url
                        proctoring_pdf.local_path = local_path
                        proctoring_pdf.save()
                        print(f"  Updated ProctoringPDF for interview {evaluation.interview.id}")
                    elif proctoring_pdf.gcs_url and clean_url:
                        # Check if existing URL is malformed
                        existing_clean = clean_gcs_url(proctoring_pdf.gcs_url)
                        if existing_clean != proctoring_pdf.gcs_url:
                            proctoring_pdf.gcs_url = clean_url if clean_url else existing_clean
                            proctoring_pdf.save()
                            print(f"  Fixed malformed URL in ProctoringPDF for interview {evaluation.interview.id}")
                elif created:
                    print(f"  Created ProctoringPDF for interview {evaluation.interview.id}")
                    migrated_count += 1
            except Exception as e:
                print(f"  Error migrating interview {evaluation.interview.id}: {e}")
    
    print(f"\nMigrated {migrated_count} proctoring PDF URLs to ProctoringPDF table")
    print(f"Cleaned {cleaned_count} malformed URLs during migration")


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

