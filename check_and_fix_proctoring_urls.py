#!/usr/bin/env python
"""
Script to check and fix proctoring PDF URLs in the database
Ensures only clean GCS URLs are stored
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_app.settings')
django.setup()

from evaluation.models import Evaluation
import re

def clean_gcs_url(url):
    """Clean malformed GCS URL"""
    if not url or not isinstance(url, str):
        return None
    
    original_url = url.strip()
    clean_url = original_url
    
    print(f"\n[CHECK] Original URL: {original_url[:100]}...")
    
    # Extract ONLY the GCS URL part (everything from storage.googleapis.com onwards)
    if 'storage.googleapis.com' in clean_url:
        gcs_index = clean_url.find('storage.googleapis.com')
        if gcs_index != -1:
            clean_url = clean_url[gcs_index:]
            print(f"[CLEAN] Extracted GCS part: {clean_url[:100]}...")
    
    # Remove ALL malformed prefixes
    clean_url = re.sub(r'^[^/]*\.(app|run|com)https?\/\/+', '', clean_url)
    clean_url = re.sub(r'^[^/]*\.(app|run|com)https?:\/\/+', '', clean_url)
    clean_url = re.sub(r'^https?\/\/+', '', clean_url)
    clean_url = re.sub(r'^https?:\/\/+', '', clean_url)
    clean_url = re.sub(r'^http:\/\/+', '', clean_url)
    
    # Ensure it starts with storage.googleapis.com
    if not clean_url.startswith('storage.googleapis.com'):
        gcs_index = clean_url.find('storage.googleapis.com')
        if gcs_index != -1:
            clean_url = clean_url[gcs_index:]
        else:
            return None
    
    # Construct clean URL with https:// prefix
    if clean_url.startswith('storage.googleapis.com'):
        clean_url = f"https://{clean_url}"
        
        # Final validation
        if clean_url.startswith('https://storage.googleapis.com/'):
            if clean_url != original_url:
                print(f"[FIX] Cleaned URL: {clean_url[:100]}...")
            return clean_url
    
    return None

def check_and_fix_urls():
    """Check all evaluations and fix malformed URLs"""
    evaluations = Evaluation.objects.all()
    total = evaluations.count()
    fixed_count = 0
    error_count = 0
    
    print(f"\n{'='*80}")
    print(f"Checking {total} evaluations for malformed proctoring PDF URLs...")
    print(f"{'='*80}\n")
    
    for idx, evaluation in enumerate(evaluations, 1):
        if not evaluation.details or not isinstance(evaluation.details, dict):
            continue
        
        updated = False
        details = evaluation.details.copy()
        
        print(f"\n[{idx}/{total}] Evaluation ID: {evaluation.id}")
        print(f"  Interview ID: {evaluation.interview.id}")
        
        # Check proctoring_pdf_gcs_url
        if 'proctoring_pdf_gcs_url' in details:
            gcs_url = details.get('proctoring_pdf_gcs_url')
            if gcs_url and isinstance(gcs_url, str):
                clean_url = clean_gcs_url(gcs_url)
                if clean_url and clean_url != gcs_url:
                    details['proctoring_pdf_gcs_url'] = clean_url
                    updated = True
                    print(f"  [FIXED] proctoring_pdf_gcs_url")
                elif clean_url:
                    print(f"  [OK] proctoring_pdf_gcs_url is clean")
                else:
                    print(f"  [ERROR] Could not clean proctoring_pdf_gcs_url")
                    error_count += 1
        
        # Check proctoring_pdf_url
        if 'proctoring_pdf_url' in details:
            pdf_url = details.get('proctoring_pdf_url')
            if pdf_url and isinstance(pdf_url, str) and 'storage.googleapis.com' in pdf_url:
                clean_url = clean_gcs_url(pdf_url)
                if clean_url and clean_url != pdf_url:
                    details['proctoring_pdf_url'] = clean_url
                    updated = True
                    print(f"  [FIXED] proctoring_pdf_url")
                elif clean_url:
                    print(f"  [OK] proctoring_pdf_url is clean")
        
        # Save if updated
        if updated:
            try:
                evaluation.details = details
                evaluation.save(update_fields=['details'])
                fixed_count += 1
                print(f"  [SAVED] Evaluation updated")
            except Exception as e:
                error_count += 1
                print(f"  [ERROR] Failed to save: {e}")
    
    print(f"\n{'='*80}")
    print(f"Summary:")
    print(f"  Total evaluations checked: {total}")
    print(f"  Fixed: {fixed_count}")
    print(f"  Errors: {error_count}")
    print(f"{'='*80}\n")

if __name__ == '__main__':
    check_and_fix_urls()

