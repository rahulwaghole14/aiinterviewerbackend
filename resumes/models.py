import uuid
import re
from pathlib import Path

import fitz            # PyMuPDF  ➜  pip install pymupdf
import docx            # python-docx ➜ pip install python-docx
from django.db import models
from django.conf import settings

# ---------------------------------------------------------------------------
# 1.  Extract full text from PDF / DOCX
# ---------------------------------------------------------------------------

def extract_text(file_path: str) -> str:
    """
    Return plain text from a PDF or DOCX file.
    """
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        doc = fitz.open(file_path)
        return "\n".join(page.get_text() for page in doc)

    if ext in (".docx", ".doc"):
        d = docx.Document(file_path)
        return "\n".join(p.text for p in d.paragraphs)

    return ""

# ---------------------------------------------------------------------------
# 2.  Extract structured fields (name, email, phone, experience) from text
# ---------------------------------------------------------------------------

EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
PHONE_RE = re.compile(r"\+?\d[\d\-\s\(\)]{8,20}")
EXP_RE   = re.compile(r"(\d{1,2})\s*(?:\+?\s*)?(years?|yrs?)", re.I)
NAME_RE  = re.compile(r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})")

def extract_resume_fields(text: str) -> dict:
    """
    Very lightweight NLP to pull key fields from résumé text.
    Returns dict with keys: name, email, phone, work_experience
    """
    email_m = EMAIL_RE.search(text)
    phone_m = PHONE_RE.search(text)
    exp_m   = EXP_RE.search(text)

    # naive name grab: first proper-case token block before email
    name = None
    if email_m:
        before_email = text.split(email_m.group(0))[0]
        name_m = NAME_RE.search(before_email)
        if name_m:
            name = name_m.group(0)

    return {
        "name":  name,
        "email": email_m.group(0) if email_m else None,
        "phone": phone_m.group(0) if phone_m else None,
        "work_experience": int(exp_m.group(1)) if exp_m else 0,
    }

# ---------------------------------------------------------------------------
# 3.  Resume model – saves file, then auto-fills parsed_text
# ---------------------------------------------------------------------------

class Resume(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user        = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="resumes",
    )
    file        = models.FileField(upload_to="resumes/")
    parsed_text = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # ➊ save file to disk first
        super().save(*args, **kwargs)

        # ➋ now that the file exists, populate parsed_text once
        if not self.parsed_text:
            self.parsed_text = extract_text(self.file.path)
            super().save(update_fields=["parsed_text"])

    def __str__(self):
        return f"Resume {self.id}"
