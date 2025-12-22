# Generated migration to clean malformed proctoring PDF URLs with run.apphttps// pattern
# Example: https://talaroai-...run.apphttps//storage.googleapis.com/...
# Should be: https://storage.googleapis.com/...

from django.db import migrations
import re


def clean_run_app_https_urls(apps, schema_editor):
    """
    Clean malformed proctoring PDF GCS URLs in Evaluation.details JSONField
    Specifically handles pattern: run.apphttps//storage.googleapis.com/...
    """
    Evaluation = apps.get_model('evaluation', 'Evaluation')
    
    updated_count = 0
    error_count = 0
    
    print("\n[OK] Starting migration to clean run.apphttps// proctoring PDF URLs...")
    
    for evaluation in Evaluation.objects.all():
        if not evaluation.details or not isinstance(evaluation.details, dict):
            continue
        
        updated = False
        details = evaluation.details.copy()
        
        # Clean proctoring_pdf_gcs_url
        if 'proctoring_pdf_gcs_url' in details:
            gcs_url = details.get('proctoring_pdf_gcs_url')
            if gcs_url and isinstance(gcs_url, str):
                original_url = gcs_url.strip()
                
                # Extract ONLY the GCS URL part (everything from storage.googleapis.com onwards)
                clean_url = None
                if 'storage.googleapis.com' in original_url:
                    gcs_index = original_url.find('storage.googleapis.com')
                    if gcs_index != -1:
                        clean_url = original_url[gcs_index:]
                
                # Remove malformed prefixes
                if clean_url:
                    # Remove patterns like: run.apphttps//storage or run.apphttps://storage
                    clean_url = re.sub(r'^[^/]*\.(app|run|com)https?\/\/+', '', clean_url)
                    clean_url = re.sub(r'^[^/]*\.(app|run|com)https?:\/\/+', '', clean_url)
                    
                    # Remove any remaining https// or https:// prefixes
                    clean_url = re.sub(r'^https?\/\/+', '', clean_url)
                    clean_url = re.sub(r'^https?:\/\/+', '', clean_url)
                    clean_url = re.sub(r'^http:\/\/+', '', clean_url)
                    
                    # Ensure it starts with storage.googleapis.com
                    if not clean_url.startswith('storage.googleapis.com'):
                        gcs_index = clean_url.find('storage.googleapis.com')
                        if gcs_index != -1:
                            clean_url = clean_url[gcs_index:]
                
                # Construct clean URL with https:// prefix
                if clean_url and clean_url.startswith('storage.googleapis.com'):
                    clean_url = f"https://{clean_url}"
                    
                    # Final validation
                    if clean_url.startswith('https://storage.googleapis.com/'):
                        if clean_url != original_url:
                            details['proctoring_pdf_gcs_url'] = clean_url
                            updated = True
                            print(f"   [OK] Cleaned proctoring_pdf_gcs_url")
                            print(f"   [OK] Original: {original_url[:80]}...")
                            print(f"   [OK] Cleaned: {clean_url[:80]}...")
        
        # Clean proctoring_pdf_url (same logic)
        if 'proctoring_pdf_url' in details:
            pdf_url = details.get('proctoring_pdf_url')
            if pdf_url and isinstance(pdf_url, str) and 'storage.googleapis.com' in pdf_url:
                original_url = pdf_url.strip()
                
                # Extract ONLY the GCS URL part
                clean_url = None
                if 'storage.googleapis.com' in original_url:
                    gcs_index = original_url.find('storage.googleapis.com')
                    if gcs_index != -1:
                        clean_url = original_url[gcs_index:]
                
                # Remove malformed prefixes
                if clean_url:
                    clean_url = re.sub(r'^[^/]*\.(app|run|com)https?\/\/+', '', clean_url)
                    clean_url = re.sub(r'^[^/]*\.(app|run|com)https?:\/\/+', '', clean_url)
                    clean_url = re.sub(r'^https?\/\/+', '', clean_url)
                    clean_url = re.sub(r'^https?:\/\/+', '', clean_url)
                    clean_url = re.sub(r'^http:\/\/+', '', clean_url)
                    
                    if not clean_url.startswith('storage.googleapis.com'):
                        gcs_index = clean_url.find('storage.googleapis.com')
                        if gcs_index != -1:
                            clean_url = clean_url[gcs_index:]
                
                # Construct clean URL
                if clean_url and clean_url.startswith('storage.googleapis.com'):
                    clean_url = f"https://{clean_url}"
                    
                    if clean_url.startswith('https://storage.googleapis.com/'):
                        if clean_url != original_url:
                            details['proctoring_pdf_url'] = clean_url
                            updated = True
                            print(f"   [OK] Cleaned proctoring_pdf_url")
        
        # Save if updated
        if updated:
            try:
                evaluation.details = details
                evaluation.save(update_fields=['details'])
                updated_count += 1
            except Exception as e:
                error_count += 1
                print(f"   [ERROR] Failed to save evaluation {evaluation.id}: {e}")
    
    print(f"\n[OK] Migration completed:")
    print(f"   - Updated: {updated_count} evaluations")
    print(f"   - Errors: {error_count}")


def reverse_migration(apps, schema_editor):
    """Reverse migration - cannot restore original malformed URLs"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('evaluation', '0007_clean_malformed_proctoring_pdf_urls_v2'),
    ]

    operations = [
        migrations.RunPython(clean_run_app_https_urls, reverse_migration),
    ]

