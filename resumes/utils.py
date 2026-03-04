import re
from utils.gemini_resume_matcher import gemini_resume_matcher

# Email and phone regex patterns
EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
PHONE_RE = re.compile(r"\+?\d[\d\-\s\(\)]{8,20}")
EXP_RE = re.compile(r"(\d{1,2})\s*(?:\+?\s*)?(years?|yrs?)", re.I)

# Name detection patterns
NAME_TCASE = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b")
NAME_ALLCAP = re.compile(r"\b([A-Z]{3,}(?:\s+[A-Z]{3,})+)\b")


def extract_resume_fields(text: str, job_description: str = None) -> dict:
    """
    Extract structured fields (name, email, phone, experience, domain, job_role) from resume text.
    Uses Gemini AI for comprehensive extraction when available.

    Args:
        text (str): The parsed text from resume
        job_description (str): Optional job description for better context

    Returns:
        dict: Dictionary containing extracted fields
    """
    if not text:
        return {}

    # Basic regex extraction as fallback
    email_m = EMAIL_RE.search(text)
    phone_m = PHONE_RE.search(text)
    exp_m = EXP_RE.search(text)

    # Simple name detection
    lines = text.strip().splitlines()
    name_block = " ".join(lines[:15])
    name = None
    m = NAME_TCASE.search(name_block)
    if m:
        name = m.group(1)
    else:
        m = NAME_ALLCAP.search(name_block)
        if m:
            name = m.group(1).title()

    # Enhanced extraction using Gemini
    experience_years = None
    domain = None
    job_role = None
    
    try:
        # Use the comprehensive method which also extracts name, email, phone etc.
        analysis = gemini_resume_matcher.extract_resume_comprehensive(text, job_description)
        if analysis and 'extracted_info' in analysis:
            info = analysis['extracted_info']
            name = info.get('full_name', name)
            email = info.get('email', email_m.group(0) if email_m else None)
            phone = info.get('phone', phone_m.group(0).strip() if phone_m else None)
            experience_years = info.get('total_experience_years')
            domain = info.get('domain')
            job_role = info.get('job_role')
            
            print(f"✅ Gemini comprehensive extraction successful for {name}")
            
            # If we also have match scores, we can include them
            match_scores = analysis.get('match_scores', {})
            
            return {
                "name": name,
                "email": email,
                "phone": phone,
                "work_experience": experience_years,
                "domain": domain,
                "job_role": job_role,
                "match_percentage": match_scores.get('overall_match', 0),
                "skill_match": match_scores.get('skill_match', 0),
                "experience_match": match_scores.get('experience_match', 0),
                "education_match": match_scores.get('education_match', 0),
                "relevance_score": match_scores.get('relevance_score', 0),
                "resume_analysis": analysis
            }
    except Exception as e:
        print(f"⚠️ Gemini comprehensive extraction failed: {e}")

    # Fallback if Gemini fails
    if experience_years is None and exp_m:
        experience_years = int(exp_m.group(1))

    return {
        "name": name,
        "email": email_m.group(0) if email_m else None,
        "phone": phone_m.group(0).strip() if phone_m else None,
        "work_experience": experience_years,
        "domain": "Generic",
        "job_role": "Candidate"
    }


def calculate_resume_job_match(resume_text: str, job_description: str) -> dict:
    """
    Calculate match percentage between resume and job description using Gemini AI
    """
    if not resume_text or not job_description:
        return {
            "overall_match": 0.0, "skill_match": 0.0, "experience_match": 0.0,
            "education_match": 0.0, "relevance_score": 0.0
        }
    
    try:
        # Use the comprehensive method for consistency
        analysis = gemini_resume_matcher.extract_resume_comprehensive(resume_text, job_description)
        match_scores = analysis.get('match_scores', {})
        if not match_scores:
            # Fallback to old method if for some reason match_scores wasn't returned
            match_scores = gemini_resume_matcher.calculate_match_percentage(resume_text, job_description)
            
        print(f"✅ Gemini calculated match: {match_scores.get('overall_match', 0)}%")
        return match_scores
    except Exception as e:
        print(f"⚠️ Gemini match calculation failed: {e}")
        return gemini_resume_matcher._fallback_match_calculation(resume_text, job_description)


def analyze_resume_comprehensive(resume_text: str, job_description: str = None) -> dict:
    """
    Perform comprehensive resume analysis using Gemini AI
    """
    if not resume_text:
        return {}
    
    try:
        analysis = gemini_resume_matcher.extract_resume_comprehensive(resume_text, job_description)
        if analysis:
            print(f"✅ Gemini comprehensive analysis completed")
        return analysis
    except Exception as e:
        print(f"⚠️ Gemini comprehensive analysis failed: {e}")
        return {}
