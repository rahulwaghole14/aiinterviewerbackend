#!/usr/bin/env python
"""
Migration script to populate existing candidates with Gemini AI analysis
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aiinterviewer.settings')
django.setup()

from candidates.models import Candidate
from resumes.models import Resume
from utils.gemini_resume_matcher import gemini_resume_matcher

def populate_gemini_analysis():
    """Populate existing candidates with Gemini AI analysis"""
    print("🔄 Starting Gemini AI analysis for existing candidates...")
    
    # Get candidates that don't have Gemini AI analysis but have resume and job
    candidates_to_update = Candidate.objects.filter(
        match_percentage__isnull=True,
        resume__isnull=False,
        job__isnull=False
    ).select_related('resume', 'job')
    
    print(f"📊 Found {candidates_to_update.count()} candidates to update")
    
    updated_count = 0
    failed_count = 0
    
    for candidate in candidates_to_update:
        try:
            print(f"🔍 Processing: {candidate.full_name}")
            
            # Get resume text
            resume_text = ""
            if candidate.resume and candidate.resume.parsed_text:
                resume_text = candidate.resume.parsed_text
            elif candidate.resume and candidate.resume.file:
                # Extract text if not already parsed
                from resumes.models import extract_text
                resume_text = extract_text(candidate.resume.file.path)
            
            # Get job description
            job_description = ""
            if candidate.job and candidate.job.job_description:
                job_description = candidate.job.job_description
            
            if resume_text and job_description:
                # Calculate Gemini AI match scores
                match_scores = gemini_resume_matcher.calculate_match_percentage(resume_text, job_description)
                
                # Extract experience
                experience = gemini_resume_matcher.extract_experience_from_resume(resume_text)
                
                # Get comprehensive analysis
                comprehensive_analysis = gemini_resume_matcher.analyze_resume_comprehensive(resume_text, job_description)
                
                # Update candidate with Gemini AI data
                candidate.match_percentage = match_scores.get('overall_match')
                candidate.skill_match = match_scores.get('skill_match')
                candidate.experience_match = match_scores.get('experience_match')
                candidate.education_match = match_scores.get('education_match')
                candidate.relevance_score = match_scores.get('relevance_score')
                candidate.resume_analysis = comprehensive_analysis
                
                # Update work_experience if not already set
                if experience is not None and not candidate.work_experience:
                    candidate.work_experience = experience
                
                candidate.save(update_fields=[
                    'match_percentage', 'skill_match', 'experience_match', 
                    'education_match', 'relevance_score', 'resume_analysis',
                    'work_experience'
                ])
                
                print(f"✅ Updated: {candidate.full_name} (Match: {candidate.match_percentage}%)")
                updated_count += 1
            else:
                print(f"⚠️ Skipping {candidate.full_name}: No resume text or job description")
                failed_count += 1
                
        except Exception as e:
            print(f"❌ Failed to update {candidate.full_name}: {e}")
            failed_count += 1
    
    print(f"\n🎉 Migration Complete!")
    print(f"✅ Successfully updated: {updated_count} candidates")
    print(f"❌ Failed to update: {failed_count} candidates")
    print(f"📊 Total processed: {updated_count + failed_count} candidates")

if __name__ == "__main__":
    populate_gemini_analysis()
