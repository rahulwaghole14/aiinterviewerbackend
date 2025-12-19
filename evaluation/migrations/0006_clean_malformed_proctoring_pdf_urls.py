# Generated migration to clean malformed proctoring PDF GCS URLs
# This migration fixes URLs that have app URL prefixes concatenated incorrectly
# Example: https://talaroai-...run.apphttps//storage.googleapis.com/... 
# Should be: https://storage.googleapis.com/...

from django.db import migrations
import re


def clean_proctoring_pdf_urls(apps, schema_editor):
    """
    Clean malformed proctoring PDF GCS URLs in Evaluation.details JSONField
    """
    Evaluation = apps.get_model('evaluation', 'Evaluation')
    
    updated_count = 0
    error_count = 0
    
    for evaluation in Evaluation.objects.all():
        if not evaluation.details or not isinstance(evaluation.details, dict):
            continue
        
        updated = False
        details = evaluation.details.copy()
        
        # Clean proctoring_pdf_gcs_url
        if 'proctoring_pdf_gcs_url' in details:
            gcs_url = details.get('proctoring_pdf_gcs_url')
            if gcs_url and isinstance(gcs_url, str):
                original_url = gcs_url
                clean_url = gcs_url.strip()
                
                # Extract only the GCS URL part if malformed (contains app URL prefix)
                if 'storage.googleapis.com' in clean_url:
                    gcs_index = clean_url.find('storage.googleapis.com')
                    if gcs_index != -1:
                        clean_url = clean_url[gcs_index:]
                
                # Remove malformed prefixes (https//, https://https://, etc.)
                clean_url = re.sub(r'^https?\/\/+', 'https://', clean_url)
                clean_url = re.sub(r'^https?://https?://', 'https://', clean_url)
                clean_url = re.sub(r'^https?://+', 'https://', clean_url)
                
                # Ensure it starts with https://
                if not clean_url.startswith('https://'):
                    if clean_url.startswith('storage.googleapis.com'):
                        clean_url = f"https://{clean_url}"
                    elif clean_url.startswith('//storage.googleapis.com'):
                        clean_url = f"https:{clean_url}"
                
                # Final validation: Must be a clean GCS URL
                if clean_url.startswith('https://storage.googleapis.com/'):
                    if clean_url != original_url:
                        details['proctoring_pdf_gcs_url'] = clean_url
                        updated = True
                        print(f"   [CLEAN] Evaluation {evaluation.id}: Cleaned GCS URL")
                        print(f"   [CLEAN]   Original: {original_url[:100]}...")
                        print(f"   [CLEAN]   Cleaned: {clean_url[:100]}...")
        
        # Clean proctoring_pdf_url (if it's a GCS URL)
        if 'proctoring_pdf_url' in details:
            pdf_url = details.get('proctoring_pdf_url')
            if pdf_url and isinstance(pdf_url, str) and 'storage.googleapis.com' in pdf_url:
                original_url = pdf_url
                clean_url = pdf_url.strip()
                
                # Extract only the GCS URL part if malformed
                if 'storage.googleapis.com' in clean_url:
                    gcs_index = clean_url.find('storage.googleapis.com')
                    if gcs_index != -1:
                        clean_url = clean_url[gcs_index:]
                
                # Remove malformed prefixes
                clean_url = re.sub(r'^https?\/\/+', 'https://', clean_url)
                clean_url = re.sub(r'^https?://https?://', 'https://', clean_url)
                clean_url = re.sub(r'^https?://+', 'https://', clean_url)
                
                # Ensure it starts with https://
                if not clean_url.startswith('https://'):
                    if clean_url.startswith('storage.googleapis.com'):
                        clean_url = f"https://{clean_url}"
                    elif clean_url.startswith('//storage.googleapis.com'):
                        clean_url = f"https:{clean_url}"
                
                # Final validation
                if clean_url.startswith('https://storage.googleapis.com/'):
                    if clean_url != original_url:
                        details['proctoring_pdf_url'] = clean_url
                        updated = True
                        print(f"   [CLEAN] Evaluation {evaluation.id}: Cleaned PDF URL")
                        print(f"   [CLEAN]   Original: {original_url[:100]}...")
                        print(f"   [CLEAN]   Cleaned: {clean_url[:100]}...")
        
        # Save if updated
        if updated:
            try:
                evaluation.details = details
                evaluation.save(update_fields=['details'])
                updated_count += 1
            except Exception as e:
                error_count += 1
                print(f"   [ERROR] Failed to update Evaluation {evaluation.id}: {e}")
    
    print(f"\n✅ Migration completed:")
    print(f"   - Updated: {updated_count} evaluations")
    print(f"   - Errors: {error_count}")


def reverse_clean_proctoring_pdf_urls(apps, schema_editor):
    """
    Reverse migration - cannot restore original malformed URLs
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('evaluation', '0005_add_database_storage_fields'),
    ]

    operations = [
        migrations.RunPython(clean_proctoring_pdf_urls, reverse_clean_proctoring_pdf_urls),
    ]

