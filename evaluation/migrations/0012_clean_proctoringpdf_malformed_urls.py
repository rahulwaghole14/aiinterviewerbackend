# Generated migration to clean malformed URLs in ProctoringPDF table

from django.db import migrations
import re


def clean_proctoringpdf_urls(apps, schema_editor):
    """
    Clean malformed URLs in ProctoringPDF table
    Pattern: https://talaroai-...run.apphttps//storage.googleapis.com/...
    Extract only the clean GCS URL part
    """
    ProctoringPDF = apps.get_model('evaluation', 'ProctoringPDF')
    
    cleaned_count = 0
    total_count = ProctoringPDF.objects.count()
    
    print(f"\n🔧 Cleaning malformed URLs in ProctoringPDF table...")
    print(f"   Total records: {total_count}")
    
    for proctoring_pdf in ProctoringPDF.objects.all():
        if not proctoring_pdf.gcs_url:
            continue
        
        original_url = proctoring_pdf.gcs_url.strip()
        clean_url = None
        
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
                else:
                    clean_url = None
        
        # Update if URL was cleaned
        if clean_url and clean_url != original_url and clean_url.startswith('https://storage.googleapis.com/'):
            proctoring_pdf.gcs_url = clean_url
            proctoring_pdf.save(update_fields=['gcs_url'])
            cleaned_count += 1
            print(f"  ✅ Cleaned URL for interview {proctoring_pdf.interview_id}")
            print(f"     Original: {original_url[:80]}...")
            print(f"     Cleaned: {clean_url[:80]}...")
        elif not clean_url or not clean_url.startswith('https://storage.googleapis.com/'):
            # Invalid URL - clear it
            print(f"  ⚠️ Invalid URL for interview {proctoring_pdf.interview_id}, clearing: {original_url[:80]}...")
            proctoring_pdf.gcs_url = None
            proctoring_pdf.save(update_fields=['gcs_url'])
    
    print(f"\n✅ Cleaned {cleaned_count} malformed URLs in ProctoringPDF table")


def reverse_migration(apps, schema_editor):
    """Reverse migration - cannot restore original malformed URLs"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('evaluation', '0011_migrate_existing_proctoring_urls'),
    ]

    operations = [
        migrations.RunPython(clean_proctoringpdf_urls, reverse_migration),
    ]

