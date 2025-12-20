# Generated migration to clean malformed proctoring PDF GCS URLs
# This migration fixes URLs that have app URL prefixes concatenated incorrectly
# Example: https://talaroai-...run.apphttps//storage.googleapis.com/... 
# Should be: https://storage.googleapis.com/...

from django.db import migrations
import re


def clean_proctoring_pdf_urls_v2(apps, schema_editor):
    """
    Clean malformed proctoring PDF GCS URLs in Evaluation.details JSONField
    Handles pattern: https://app-urlhttps//storage.googleapis.com/...
    """
    Evaluation = apps.get_model('evaluation', 'Evaluation')
    
    updated_count = 0
    error_count = 0
    
    print("\n[OK] Starting migration to clean malformed proctoring PDF URLs (v2)...")
    
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
                
                # CRITICAL: Handle pattern like: https://talaroai-...run.apphttps//storage.googleapis.com/...
                # Extract only the GCS URL part (everything from storage.googleapis.com onwards)
                if 'storage.googleapis.com' in clean_url:
                    gcs_index = clean_url.find('storage.googleapis.com')
                    if gcs_index != -1:
                        clean_url = clean_url[gcs_index:]
                        print(f"   [CLEAN] Extracted GCS part from: {original_url[:80]}...")
                
                # Remove malformed prefixes (https//, https://https://, http://, etc.)
                clean_url = re.sub(r'^https?\/\/+', 'https://', clean_url)  # https// -> https://
                clean_url = re.sub(r'^https?://https?://', 'https://', clean_url)  # https://https:// -> https://
                clean_url = re.sub(r'^https?://+', 'https://', clean_url)  # https://// -> https://
                clean_url = re.sub(r'^http://', 'https://', clean_url)  # http:// -> https://
                
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
                        print(f"   [OK] Evaluation {evaluation.id}: Cleaned GCS URL")
                        print(f"   [OK]   Original: {original_url[:100]}")
                        print(f"   [OK]   Cleaned: {clean_url[:100]}")
                else:
                    print(f"   [WARN] Evaluation {evaluation.id}: Invalid GCS URL format, skipping")
                    print(f"   [WARN]   URL: {clean_url[:100]}")
        
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
                clean_url = re.sub(r'^http://', 'https://', clean_url)
                
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
                        print(f"   [OK] Evaluation {evaluation.id}: Cleaned PDF URL")
                        print(f"   [OK]   Original: {original_url[:100]}")
                        print(f"   [OK]   Cleaned: {clean_url[:100]}")
        
        # Save if updated
        if updated:
            try:
                evaluation.details = details
                evaluation.save(update_fields=['details'])
                updated_count += 1
            except Exception as e:
                error_count += 1
                print(f"   [ERROR] Failed to update Evaluation {evaluation.id}: {e}")
    
    print(f"\n[OK] Migration completed:")
    print(f"   - Updated: {updated_count} evaluations")
    print(f"   - Errors: {error_count}")


def reverse_clean_proctoring_pdf_urls_v2(apps, schema_editor):
    """
    Reverse migration - cannot restore original malformed URLs
    """
    print("\n[WARN] Reverse migration for cleaning proctoring PDF URLs is not implemented.")
    print("       Reverting this migration will not restore malformed URLs.")


class Migration(migrations.Migration):

    dependencies = [
        ('evaluation', '0006_clean_malformed_proctoring_pdf_urls'),
    ]

    operations = [
        migrations.RunPython(clean_proctoring_pdf_urls_v2, reverse_clean_proctoring_pdf_urls_v2),
    ]
