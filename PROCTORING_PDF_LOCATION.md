# 📄 Proctoring PDF Location Guide

## 📁 File Location

### Physical Location on Disk:
```
C:\Users\ADMIN\Downloads\ai interview portal (1)\media\proctoring_pdfs\
```

### Full Path Structure:
```
{BASE_DIR}/media/proctoring_pdfs/proctoring_report_{interview_id}_{YYYYMMDD_HHMMSS}.pdf
```

**Example:**
```
media/proctoring_pdfs/proctoring_report_123_20251104_143022.pdf
```

---

## 🔍 How to Find the PDF

### Method 1: Direct File System Access
1. Navigate to: `C:\Users\ADMIN\Downloads\ai interview portal (1)\media\proctoring_pdfs\`
2. Look for files named: `proctoring_report_*.pdf`

### Method 2: Via Django Admin or API
The PDF URL is stored in the `Evaluation` model's `details` field:
```json
{
  "proctoring_pdf": "proctoring_pdfs/proctoring_report_123_20251104_143022.pdf",
  "proctoring_pdf_url": "/media/proctoring_pdfs/proctoring_report_123_20251104_143022.pdf"
}
```

### Method 3: Check Database
```python
from evaluation.models import Evaluation

# Get evaluation for a specific interview
evaluation = Evaluation.objects.get(interview_id=123)
if evaluation.details and 'proctoring_pdf' in evaluation.details:
    pdf_path = evaluation.details['proctoring_pdf']
    print(f"PDF Path: {pdf_path}")
    print(f"Full URL: {evaluation.details.get('proctoring_pdf_url')}")
```

---

## 📋 PDF Naming Convention

**Format:** `proctoring_report_{interview_id}_{YYYYMMDD_HHMMSS}.pdf`

**Example:** `proctoring_report_5_20251104_143022.pdf`
- `5` = Interview ID
- `20251104` = Date (November 4, 2025)
- `143022` = Time (14:30:22)

---

## 🌐 Accessing via Web URL

Once the PDF is generated, it's accessible via:
```
http://127.0.0.1:8000/media/proctoring_pdfs/proctoring_report_{interview_id}_{timestamp}.pdf
```

**Note:** Make sure `MEDIA_URL` is properly configured in `settings.py` and media files are served (already configured in `urls.py`).

---

## 🔧 Code Reference

### PDF Generation Location:
**File:** `evaluation/proctoring_pdf.py`
**Lines:** 177-183

```python
# Generate output filename
if output_path is None:
    pdf_dir = os.path.join(settings.MEDIA_ROOT, 'proctoring_pdfs')
    os.makedirs(pdf_dir, exist_ok=True)
    interview_id = evaluation.interview.id if evaluation.interview else 'unknown'
    filename = f"proctoring_report_{interview_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    output_path = os.path.join(pdf_dir, filename)
```

### Settings Configuration:
**File:** `interview_app/settings.py`
**Lines:** 132-133

```python
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
```

---

## ✅ Quick Check Commands

### Check if directory exists:
```bash
dir "C:\Users\ADMIN\Downloads\ai interview portal (1)\media\proctoring_pdfs"
```

### List all PDFs:
```bash
dir "C:\Users\ADMIN\Downloads\ai interview portal (1)\media\proctoring_pdfs\*.pdf"
```

### Python check:
```python
import os
from django.conf import settings

pdf_dir = os.path.join(settings.MEDIA_ROOT, 'proctoring_pdfs')
if os.path.exists(pdf_dir):
    pdfs = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
    print(f"Found {len(pdfs)} PDF(s):")
    for pdf in pdfs:
        print(f"  - {pdf}")
else:
    print(f"Directory does not exist: {pdf_dir}")
```

---

## 📝 Notes

1. **Directory Creation:** The directory is automatically created if it doesn't exist when the PDF is generated.

2. **PDF Contents:**
   - Header with candidate name and interview date
   - Total warnings count
   - Warnings grouped by type (Multiple People, Phone Detected, etc.)
   - Images with timestamps below each image
   - Proper alignment and formatting

3. **Storage:** PDFs are stored locally on the server. For production, consider:
   - Using cloud storage (AWS S3, Google Cloud Storage, etc.)
   - Implementing a cleanup script for old PDFs
   - Adding file size limits

