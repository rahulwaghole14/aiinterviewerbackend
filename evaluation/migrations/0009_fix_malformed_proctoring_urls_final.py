# Generated migration to fix malformed proctoring PDF URLs

from django.db import migrations
import re


def clean_gcs_url(url):
    """Clean malformed GCS URL - extract only the GCS part"""
    if not url or not isinstance(url, str):
        return None
    
    original_url = url.strip()
    
    # Extract ONLY the GCS URL part (everything from storage.googleapis.com onwards)
    if 'storage.googleapis.com' in original_url:
        gcs_index = original_url.find('storage.googleapis.com')
        if gcs_index != -1:
            clean_url = original_url[gcs_index:]
            
            # Remove any malformed prefixes
            clean_url = re.sub(r'^[^/]*\.(app|run|com)https?\/\/+', '', clean_url)
            clean_url = re.sub(r'^[^/]*\.(app|run|com)https?:\/\/+', '', clean_url)
            clean_url = re.sub(r'^https?\/\/+', '', clean_url)
            clean_url = re.sub(r'^https?:\/\/+', '', clean_url)
            
            # Ensure it starts with storage.googleapis.com
            if clean_url.startswith('storage.googleapis.com'):
                clean_url = f"https://{clean_url}"
                
                # Final validation
                if clean_url.startswith('https://storage.googleapis.com/'):
                    return clean_url
    
    return None


def fix_malformed_proctoring_urls(apps, schema_editor):
    """Fix all malformed proctoring PDF URLs in Evaluation details"""
    Evaluation = apps.get_model('evaluation', 'Evaluation')
    
    evaluations = Evaluation.objects.all()
    fixed_count = 0
    
    for evaluation in evaluations:
        if not evaluation.details or not isinstance(evaluation.details, dict):
            continue
        
        updated = False
        details = evaluation.details.copy()
        
        # Check all possible URL fields
        url_fields = ['proctoring_pdf_gcs_url', 'proctoring_pdf_url']
        
        for field_name in url_fields:
            if field_name in details:
                url_value = details.get(field_name)
                if url_value and isinstance(url_value, str):
                    url_str = str(url_value)
                    
                    # Check if URL is malformed (contains app domain before storage.googleapis.com)
                    if (('run.app' in url_str or 'talaroai' in url_str or '.apphttps' in url_str) 
                        and 'storage.googleapis.com' in url_str):
                        
                        # Clean the URL
                        clean_url = clean_gcs_url(url_str)
                        
                        if clean_url and clean_url != url_str:
                            details[field_name] = clean_url
                            updated = True
                    elif url_str and 'storage.googleapis.com' in url_str:
                        # Might be malformed, try to clean
                        clean_url = clean_gcs_url(url_str)
                        if clean_url and clean_url != url_str:
                            details[field_name] = clean_url
                            updated = True
        
        # Save if updated
        if updated:
            evaluation.details = details
            evaluation.save(update_fields=['details'])
            fixed_count += 1
    
    print(f"Fixed {fixed_count} evaluations with malformed proctoring PDF URLs")


def reverse_migration(apps, schema_editor):
    """Reverse migration - cannot restore malformed URLs"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('evaluation', '0008_clean_run_app_https_proctoring_urls'),
    ]

    operations = [
        migrations.RunPython(fix_malformed_proctoring_urls, reverse_migration),
    ]

