import re, fitz, docx
from pathlib import Path

EMAIL_PATTERN = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')
PHONE_PATTERN = re.compile(r'\+?\d[\d\s\-\(\)]{8,20}')
EXP_PATTERN   = re.compile(r'(\d{1,2})\s*(years?|yrs?)', re.I)
NAME_PATTERN  = re.compile(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})')

def extract_text(path):
    ext = Path(path).suffix.lower()
    if ext == ".pdf":
        doc = fitz.open(path)
        return "\n".join(page.get_text() for page in doc)
    elif ext in (".docx", ".doc"):
        doc = docx.Document(path)
        return "\n".join(p.text for p in doc.paragraphs)
    return ""

def extract_resume_fields(text):
    email = EMAIL_PATTERN.search(text)
    phone = PHONE_PATTERN.search(text)
    exp   = EXP_PATTERN.search(text)
    name  = None

    if email:
        before_email = text.split(email.group(0))[0]
        name_match = NAME_PATTERN.search(before_email)
        name = name_match.group(0) if name_match else None

    return {
        "name": name,
        "email": email.group(0) if email else None,
        "phone": phone.group(0) if phone else None,
        "work_experience": int(exp.group(1)) if exp else 0,
    }
