#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aiinterviewer.settings')
django.setup()

from candidates.models import Candidate
from resumes.models import Resume

print('🔍 Checking resume files and content...')

candidates = Candidate.objects.all()[:3]
for candidate in candidates:
    print(f'\n📋 Candidate: {candidate.full_name}')
    print(f'   Resume ID: {candidate.resume.id if candidate.resume else None}')
    
    if candidate.resume:
        print(f'   Parsed Text: {candidate.resume.parsed_text[:100] if candidate.resume.parsed_text else None}...')
        
        if candidate.resume.file:
            try:
                file_path = candidate.resume.file.path
                print(f'   File Exists: {os.path.exists(file_path)}')
                if os.path.exists(file_path):
                    print(f'   File Size: {os.path.getsize(file_path)} bytes')
            except Exception as e:
                print(f'   File Error: {e}')

print('\n📊 Resume Statistics:')
total_resumes = Resume.objects.count()
print(f'   Total Resumes: {total_resumes}')
print(f'   Resumes with Parsed Text: {Resume.objects.exclude(parsed_text="").count()}')
print(f'   Resumes with Files: {Resume.objects.exclude(file__isnull=True).count()}')

# Check if we need to extract text from files
print('\n🔧 Checking text extraction needs...')
resumes_without_text = Resume.objects.filter(parsed_text__in=["", None])
print(f'   Resumes needing text extraction: {resumes_without_text.count()}')

for resume in resumes_without_text[:2]:
    print(f'   - Resume {resume.id}: {resume.file.name if resume.file else "No file"}')
