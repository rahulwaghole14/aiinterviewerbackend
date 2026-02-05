import re
from utils.gemini_resume_matcher import gemini_resume_matcher

# Email and phone regex patterns
EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
PHONE_RE = re.compile(r"\+?\d[\d\-\s\(\)]{8,20}")
EXP_RE = re.compile(r"(\d{1,2})\s*(?:\+?\s*)?(years?|yrs?)", re.I)

# Name detection patterns
NAME_TCASE = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b")
NAME_ALLCAP = re.compile(r"\b([A-Z]{3,}(?:\s+[A-Z]{3,})+)\b")


def extract_resume_fields(text: str) -> dict:
    """
    Extract structured fields (name, email, phone, experience) from resume text.
    Uses Gemini AI for enhanced experience extraction when available.

    Args:
        text (str): The parsed text from resume

    Returns:
        dict: Dictionary containing extracted fields
    """
    if not text:
        return {}

    email_m = EMAIL_RE.search(text)
    phone_m = PHONE_RE.search(text)
    exp_m = EXP_RE.search(text)

    # Join first 15 lines for multiline name detection
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

    # Use Gemini AI for enhanced experience extraction
    experience_years = None
    try:
        gemini_experience = gemini_resume_matcher.extract_experience_from_resume(text)
        if gemini_experience is not None:
            experience_years = gemini_experience
            print(f"✅ Gemini extracted experience: {experience_years} years")
    except Exception as e:
        print(f"⚠️ Gemini experience extraction failed: {e}")

    # Fallback to regex if Gemini fails
    if experience_years is None and exp_m:
        experience_years = int(exp_m.group(1))

    return {
        "name": name,
        "email": email_m.group(0) if email_m else None,
        "phone": phone_m.group(0).strip() if phone_m else None,
        "work_experience": experience_years,
    }


def calculate_resume_job_match(resume_text: str, job_description: str) -> dict:
    """
    Calculate match percentage between resume and job description using Gemini AI
    
    Args:
        resume_text (str): The parsed resume text
        job_description (str): The job description
        
    Returns:
        dict: Dictionary containing match percentages
    """
    if not resume_text or not job_description:
        return {
            "overall_match": 0.0,
            "skill_match": 0.0,
            "experience_match": 0.0,
            "education_match": 0.0,
            "relevance_score": 0.0
        }
    
    try:
        match_scores = gemini_resume_matcher.calculate_match_percentage(resume_text, job_description)
        print(f"✅ Gemini calculated match: {match_scores.get('overall_match', 0)}%")
        return match_scores
    except Exception as e:
        print(f"⚠️ Gemini match calculation failed: {e}")
        return {
            "overall_match": 0.0,
            "skill_match": 0.0,
            "experience_match": 0.0,
            "education_match": 0.0,
            "relevance_score": 0.0
        }


def analyze_resume_comprehensive(resume_text: str, job_description: str = None) -> dict:
    """
    Perform comprehensive resume analysis using Gemini AI
    
    Args:
        resume_text (str): The parsed resume text
        job_description (str): Optional job description for context
        
    Returns:
        dict: Dictionary containing comprehensive analysis
    """
    if not resume_text:
        return {}
    
    try:
        analysis = gemini_resume_matcher.analyze_resume_comprehensive(resume_text, job_description)
        if analysis:
            print(f"✅ Gemini comprehensive analysis completed")
        return analysis
    except Exception as e:
        print(f"⚠️ Gemini comprehensive analysis failed: {e}")
        return {}
