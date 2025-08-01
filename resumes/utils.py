import re

# Email and phone regex patterns
EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
PHONE_RE = re.compile(r"\+?\d[\d\-\s\(\)]{8,20}")
EXP_RE   = re.compile(r"(\d{1,2})\s*(?:\+?\s*)?(years?|yrs?)", re.I)

# Name detection patterns
NAME_TCASE = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b")
NAME_ALLCAP = re.compile(r"\b([A-Z]{3,}(?:\s+[A-Z]{3,})+)\b")

def extract_resume_fields(text: str) -> dict:
    """
    Extract structured fields (name, email, phone, experience) from resume text.
    
    Args:
        text (str): The parsed text from the resume
        
    Returns:
        dict: Dictionary containing extracted fields
    """
    if not text:
        return {}
    
    email_m = EMAIL_RE.search(text)
    phone_m = PHONE_RE.search(text)
    exp_m   = EXP_RE.search(text)

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

    return {
        "name": name,
        "email": email_m.group(0) if email_m else None,
        "phone": phone_m.group(0).strip() if phone_m else None,
        "work_experience": int(exp_m.group(1)) if exp_m else None,
    }
