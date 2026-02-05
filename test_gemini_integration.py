#!/usr/bin/env python
"""
Test script to verify Gemini AI integration in bulk resume extraction
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aiinterviewer.settings')
django.setup()

from utils.gemini_resume_matcher import gemini_resume_matcher

def test_gemini_integration():
    print("🧪 Testing Gemini AI Integration for Resume Analysis...")
    
    # Sample resume text
    sample_resume = """
    John Doe
    Email: john.doe@email.com
    Phone: (555) 123-4567
    
    PROFESSIONAL EXPERIENCE:
    Senior Software Engineer at Tech Corp (2020-Present) - 4 years
    Software Developer at StartupXYZ (2018-2020) - 2 years
    Junior Developer at FirstCompany (2016-2018) - 2 years
    
    EDUCATION:
    Bachelor of Science in Computer Science
    University of Technology (2012-2016)
    
    SKILLS:
    Python, Django, React, PostgreSQL, AWS, Docker, Git
    """
    
    # Sample job description
    sample_jd = """
    Senior Python Developer Position
    
    Requirements:
    - 5+ years of Python development experience
    - Django framework expertise
    - React frontend experience
    - PostgreSQL database knowledge
    - AWS cloud experience
    - Bachelor's degree in Computer Science or related field
    
    Responsibilities:
    - Develop and maintain web applications using Python/Django
    - Work with React frontend
    - Design and implement database schemas
    - Deploy applications on AWS cloud infrastructure
    """
    
    print("\n📄 Sample Resume:")
    print(sample_resume[:200] + "...")
    
    print("\n💼 Sample Job Description:")
    print(sample_jd[:200] + "...")
    
    # Test experience extraction
    print("\n🔍 Testing Experience Extraction...")
    experience = gemini_resume_matcher.extract_experience_from_resume(sample_resume)
    print(f"✅ Extracted Experience: {experience} years")
    
    # Test match calculation
    print("\n🎯 Testing Match Calculation...")
    match_scores = gemini_resume_matcher.calculate_match_percentage(sample_resume, sample_jd)
    print(f"✅ Match Scores:")
    for key, value in match_scores.items():
        print(f"   - {key}: {value}%")
    
    # Test comprehensive analysis
    print("\n📊 Testing Comprehensive Analysis...")
    analysis = gemini_resume_matcher.analyze_resume_comprehensive(sample_resume, sample_jd)
    print(f"✅ Analysis Keys: {list(analysis.keys())}")
    
    if 'extracted_info' in analysis:
        extracted = analysis['extracted_info']
        print(f"   - Name: {extracted.get('full_name', 'N/A')}")
        print(f"   - Email: {extracted.get('email', 'N/A')}")
        print(f"   - Experience: {extracted.get('total_experience_years', 'N/A')} years")
        print(f"   - Key Skills: {extracted.get('key_skills', [])[:3]}...")
    
    if 'analysis' in analysis:
        analysis_data = analysis['analysis']
        print(f"   - Career Level: {analysis_data.get('career_level', 'N/A')}")
        print(f"   - Industry Focus: {analysis_data.get('industry_focus', 'N/A')}")
    
    print("\n🎉 Gemini AI Integration Test Completed Successfully!")
    print("\n📋 Expected Fields in Parsed Resume Data:")
    print("   - work_experience: [extracted years]")
    print("   - match_percentage: [overall match %]")
    print("   - skill_match: [skill match %]")
    print("   - experience_match: [experience match %]")
    print("   - education_match: [education match %]")
    print("   - relevance_score: [relevance score %]")
    print("   - resume_analysis: [comprehensive analysis JSON]")

if __name__ == "__main__":
    test_gemini_integration()
