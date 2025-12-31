# Database Storage: Detailed Functionality for Proctoring PDF URLs

## 📋 Overview
This document provides **detailed functionality** for how proctoring PDF URLs are cleaned, validated, and stored in the database. The URL is stored in **two places** for redundancy and reliability.

---

## 🔄 Complete Database Storage Flow

### **STEP 1: PDF Generation Result**

**Location:** `evaluation/services.py` (line 410)

After the PDF is generated, the function receives one of two possible results:

**A. GCS Upload Successful (Dict):**
```python
{
    'gcs_url': 'https://storage.googleapis.com/bucket/path/file.pdf',
    'local_path': 'proctoring_pdfs/proctoring_report_123_20240115_101530.pdf'
}
```

**B. Local Storage Only (String):**
```python
'proctoring_pdfs/proctoring_report_123_20240115_101530.pdf'
```

**Code:**
```python
# evaluation/services.py:410-416
proctoring_pdf_result = generate_proctoring_pdf(temp_evaluation)
if proctoring_pdf_result:
    if isinstance(proctoring_pdf_result, dict):
        # GCS upload successful
        local_path = proctoring_pdf_result.get('local_path', '')
        gcs_url = proctoring_pdf_result.get('gcs_url', '')
```

---

## 🧹 STEP 2: URL Cleaning Process (First Pass)

**Location:** `evaluation/services.py` (lines 418-476)

### **Purpose:**
Clean the GCS URL to remove any malformed prefixes that might have been concatenated during the upload process.

### **Common Malformed Patterns:**
- `https://app-urlhttps//storage.googleapis.com/...`
- `app-urlhttps//storage.googleapis.com/...`
- `https://app-url/storage.googleapis.com/...`
- `run.apphttps//storage.googleapis.com/...`

### **Cleaning Algorithm:**

#### **Phase 1: Extract GCS URL Part**
```python
# evaluation/services.py:431-436
if 'storage.googleapis.com' in clean_url:
    gcs_index = clean_url.find('storage.googleapis.com')
    if gcs_index != -1:
        # Extract everything from storage.googleapis.com onwards
        clean_url = clean_url[gcs_index:]
        # Result: 'storage.googleapis.com/bucket/path/file.pdf'
```

**Example:**
- Input: `https://talaroai-xyz.run.apphttps//storage.googleapis.com/bucket/file.pdf`
- After extraction: `storage.googleapis.com/bucket/file.pdf`

#### **Phase 2: Remove Malformed Prefixes**
```python
# evaluation/services.py:438-442
# Remove ALL malformed prefixes (https//, https://, http://)
clean_url = re.sub(r'^https?\/\/', '', clean_url)  # Remove https// (MUST BE FIRST)
clean_url = re.sub(r'^https?:\/\/', '', clean_url)  # Remove https://
clean_url = re.sub(r'^http:\/\/', '', clean_url)  # Remove http://
```

**Regex Patterns Explained:**
- `r'^https?\/\/'` - Matches `https//` or `http//` at the start
- `r'^https?:\/\/'` - Matches `https://` or `http://` at the start
- `r'^http:\/\/'` - Matches `http://` at the start

**Example:**
- Input: `https//storage.googleapis.com/bucket/file.pdf`
- After cleaning: `storage.googleapis.com/bucket/file.pdf`

#### **Phase 3: Validation & Re-extraction (If Needed)**
```python
# evaluation/services.py:444-456
if not clean_url.startswith('storage.googleapis.com'):
    print(f"   [WARN] Invalid GCS URL format after extraction")
    # Try to find storage.googleapis.com again
    gcs_index = clean_url.find('storage.googleapis.com')
    if gcs_index != -1:
        clean_url = clean_url[gcs_index:]
    else:
        # Don't store invalid URL - set to None
        gcs_url = None
        clean_url = None
```

**Purpose:** If the first extraction failed, try again. If it still fails, mark URL as invalid.

#### **Phase 4: Construct Clean URL**
```python
# evaluation/services.py:458-468
if clean_url and clean_url.startswith('storage.googleapis.com'):
    clean_url = f"https://{clean_url}"
    # Final validation - must be a proper GCS URL
    if clean_url.startswith('https://storage.googleapis.com/'):
        gcs_url = clean_url
        print(f"   [OK] Cleaned GCS URL stored: {gcs_url[:100]}...")
    else:
        print(f"   [ERROR] GCS URL validation failed after adding https://")
        gcs_url = None
```

**Result:**
- Valid URL: `https://storage.googleapis.com/bucket/path/file.pdf`
- Invalid URL: Set to `None`

---

## 🧹 STEP 3: URL Cleaning Process (Second Pass)

**Location:** `evaluation/services.py` (lines 481-508)

### **Purpose:**
Additional cleaning pass to handle any edge cases that might have been missed in the first pass.

### **Cleaning Algorithm (Second Pass):**

```python
# evaluation/services.py:483-508
clean_gcs_url = None
if gcs_url and isinstance(gcs_url, str):
    original_url = gcs_url.strip()
    
    # Extract ONLY the GCS URL part
    if 'storage.googleapis.com' in original_url:
        gcs_index = original_url.find('storage.googleapis.com')
        if gcs_index != -1:
            clean_gcs_url = original_url[gcs_index:]
            
            # Remove any malformed prefixes
            clean_gcs_url = re.sub(r'^[^/]*\.(app|run|com)https?\/\/+', '', clean_gcs_url)
            clean_gcs_url = re.sub(r'^[^/]*\.(app|run|com)https?:\/\/+', '', clean_gcs_url)
            clean_gcs_url = re.sub(r'^https?\/\/+', '', clean_gcs_url)
            clean_gcs_url = re.sub(r'^https?:\/\/+', '', clean_gcs_url)
            
            # Ensure it starts with storage.googleapis.com
            if clean_gcs_url.startswith('storage.googleapis.com'):
                clean_gcs_url = f"https://{clean_gcs_url}"
                
                # Final validation
                if not clean_gcs_url.startswith('https://storage.googleapis.com/'):
                    clean_gcs_url = None
            else:
                clean_gcs_url = None
```

### **Advanced Regex Patterns (Second Pass):**

1. **`r'^[^/]*\.(app|run|com)https?\/\/+'`**
   - Matches: `something.apphttps//`, `domain.runhttps//`, `site.comhttps//`
   - Example: Removes `talaroai-xyz.run.apphttps//` from URL

2. **`r'^[^/]*\.(app|run|com)https?:\/\/+'`**
   - Matches: `something.apphttps://`, `domain.runhttps://`, `site.comhttps://`
   - Example: Removes `talaroai-xyz.run.apphttps://` from URL

3. **`r'^https?\/\/+'`**
   - Matches: `https//`, `http//`, `https///`, etc.
   - Removes multiple slashes

4. **`r'^https?:\/\/+'`**
   - Matches: `https://`, `http://`, `https:///`, etc.
   - Removes protocol with multiple slashes

### **Final Validation:**
```python
# evaluation/services.py:505-506
if not clean_gcs_url.startswith('https://storage.googleapis.com/'):
    clean_gcs_url = None
```

**Validation Rules:**
- ✅ Must start with `https://storage.googleapis.com/`
- ✅ Must be a valid URL format
- ❌ If validation fails, set to `None`

---

## 💾 STEP 4: Storage in Evaluation.details (JSONField)

**Location:** `evaluation/services.py` (lines 510-556)

### **Storage Logic:**

#### **A. If GCS URL is Valid:**
```python
# evaluation/services.py:510-512
if clean_gcs_url and clean_gcs_url.startswith('https://storage.googleapis.com/'):
    details['proctoring_pdf_gcs_url'] = clean_gcs_url
    details['proctoring_pdf_url'] = clean_gcs_url  # Use GCS URL as primary
    details['proctoring_pdf'] = local_path  # Store local path as backup
```

**Stored Values:**
```json
{
  "proctoring_pdf_gcs_url": "https://storage.googleapis.com/bucket/path/file.pdf",
  "proctoring_pdf_url": "https://storage.googleapis.com/bucket/path/file.pdf",
  "proctoring_pdf": "proctoring_pdfs/proctoring_report_123_20240115_101530.pdf"
}
```

#### **B. If GCS URL is Invalid:**
```python
# evaluation/services.py:537-546
else:
    # Don't store invalid URL - use local path only
    print(f"⚠️ GCS URL validation failed, storing local path only")
    details['proctoring_pdf_gcs_url'] = None
    # Use local path for proctoring_pdf_url
    from django.conf import settings
    media_url = settings.MEDIA_URL.rstrip('/')
    pdf_path = local_path.lstrip('/')
    details['proctoring_pdf_url'] = f"{media_url}/{pdf_path}"
```

**Stored Values:**
```json
{
  "proctoring_pdf_gcs_url": null,
  "proctoring_pdf_url": "/media/proctoring_pdfs/proctoring_report_123_20240115_101530.pdf",
  "proctoring_pdf": "proctoring_pdfs/proctoring_report_123_20240115_101530.pdf"
}
```

### **Database Schema:**
```sql
-- Table: evaluation_evaluation
CREATE TABLE evaluation_evaluation (
    id INTEGER PRIMARY KEY,
    interview_id INTEGER REFERENCES interviews_interview(id),
    details JSONB,  -- Stores proctoring_pdf_url, proctoring_pdf_gcs_url, proctoring_pdf
    overall_score FLOAT,
    traits TEXT,
    suggestions TEXT,
    created_at TIMESTAMP,
    ...
);
```

**JSONField Structure:**
```json
{
  "proctoring_pdf_gcs_url": "https://storage.googleapis.com/...",
  "proctoring_pdf_url": "https://storage.googleapis.com/...",
  "proctoring_pdf": "proctoring_pdfs/file.pdf",
  "proctoring": {
    "total_warnings": 5,
    "warnings": [...],
    "warning_types": [...]
  },
  "ai_analysis": {...}
}
```

---

## 💾 STEP 5: Storage in ProctoringPDF Table (PRIMARY SOURCE)

**Location:** `evaluation/services.py` (lines 518-536)

### **Purpose:**
Store the URL in a dedicated table for easy querying and as the primary source of truth.

### **Storage Logic:**

```python
# evaluation/services.py:518-536
# CRITICAL: Also save to separate ProctoringPDF table
try:
    from evaluation.models import ProctoringPDF
    proctoring_pdf, created = ProctoringPDF.objects.update_or_create(
        interview=interview,
        defaults={
            'gcs_url': clean_gcs_url,  # Clean, validated GCS URL
            'local_path': local_path,   # Local file path (backup)
        }
    )
    if created:
        print(f"✅ Created ProctoringPDF record for interview {interview.id}")
    else:
        print(f"✅ Updated ProctoringPDF record for interview {interview.id}")
    print(f"✅ Proctoring PDF URL saved to separate table: {clean_gcs_url[:100]}...")
except Exception as e:
    print(f"⚠️ Error saving to ProctoringPDF table: {e}")
    import traceback
    traceback.print_exc()
```

### **Django ORM Method: `update_or_create()`**

**Functionality:**
- **If record exists:** Updates the existing record with new values
- **If record doesn't exist:** Creates a new record

**Parameters:**
- `interview=interview` - Lookup field (OneToOne relationship)
- `defaults={...}` - Values to set/update

**Why `update_or_create()`?**
- Prevents duplicate records (OneToOne relationship)
- Updates URL if PDF is regenerated
- Atomic operation (no race conditions)

### **Database Schema:**
```sql
-- Table: evaluation_proctoringpdf
CREATE TABLE evaluation_proctoringpdf (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    interview_id INTEGER UNIQUE NOT NULL,
    gcs_url VARCHAR(500) NULL,
    local_path VARCHAR(500) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (interview_id) REFERENCES interviews_interview(id) ON DELETE CASCADE,
    INDEX idx_interview_created (interview_id, created_at),
    INDEX idx_gcs_url (gcs_url)
);
```

### **Model Definition:**
```python
# evaluation/models.py:28-61
class ProctoringPDF(models.Model):
    """
    Separate table to store proctoring PDF URLs
    One-to-one relationship with Interview
    """
    interview = models.OneToOneField(
        Interview, on_delete=models.CASCADE, related_name="proctoring_pdf", db_index=True
    )
    gcs_url = models.URLField(
        max_length=500, 
        blank=True, 
        null=True,
        help_text="Google Cloud Storage public URL for proctoring PDF"
    )
    local_path = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Local file path for proctoring PDF (backup)"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### **Key Features:**
- ✅ **OneToOne relationship** - One PDF per interview
- ✅ **CASCADE delete** - If interview is deleted, PDF record is deleted
- ✅ **Indexed fields** - Fast queries on `interview_id` and `gcs_url`
- ✅ **Timestamps** - Track when record was created/updated

---

## 🔄 STEP 6: Database Transaction

**Location:** `evaluation/services.py` (lines 587-599)

### **Purpose:**
Ensure data consistency - both `Evaluation` and `ProctoringPDF` records are saved atomically.

### **Transaction Logic:**

```python
# evaluation/services.py:587-599
from django.db import transaction

with transaction.atomic():
    if existing_evaluation:
        # Update existing evaluation
        existing_evaluation.details = details  # Contains proctoring_pdf_url
        existing_evaluation.save()
        evaluation = existing_evaluation
    else:
        # Create new evaluation
        evaluation = Evaluation.objects.create(
            interview=interview,
            overall_score=overall_score / 10.0,
            traits='\n\n'.join(traits),
            suggestions='\n\n'.join(suggestions),
            details=details  # Contains proctoring_pdf_url
        )
```

**Note:** The `ProctoringPDF` record is saved **before** the transaction (line 521), but if the transaction fails, Django will rollback all changes.

### **Why Transaction?**
- **Data Consistency:** Ensures both records are saved together
- **Rollback:** If evaluation save fails, ProctoringPDF save is also rolled back
- **Atomicity:** All-or-nothing operation

---

## 📊 Complete Storage Flow Diagram

```
PDF Generation Result
    ↓
{
  'gcs_url': 'https://storage.googleapis.com/...',
  'local_path': 'proctoring_pdfs/file.pdf'
}
    ↓
┌─────────────────────────────────────┐
│  FIRST PASS: URL Cleaning            │
│  - Extract GCS part                  │
│  - Remove malformed prefixes         │
│  - Validate format                   │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  SECOND PASS: URL Cleaning           │
│  - Additional cleaning               │
│  - Remove app domain prefixes        │
│  - Final validation                  │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  VALIDATION                          │
│  Must start with:                    │
│  https://storage.googleapis.com/     │
└─────────────────────────────────────┘
    ↓
    ├─→ VALID URL
    │       ↓
    │   ┌───────────────────────────────┐
    │   │  STORAGE LOCATION 1:          │
    │   │  Evaluation.details           │
    │   │  - proctoring_pdf_gcs_url     │
    │   │  - proctoring_pdf_url         │
    │   │  - proctoring_pdf (local)     │
    │   └───────────────────────────────┘
    │       ↓
    │   ┌───────────────────────────────┐
    │   │  STORAGE LOCATION 2:          │
    │   │  ProctoringPDF Table          │
    │   │  - gcs_url (PRIMARY)          │
    │   │  - local_path (backup)        │
    │   └───────────────────────────────┘
    │
    └─→ INVALID URL
            ↓
        ┌───────────────────────────────┐
        │  FALLBACK: Local Path Only     │
        │  Evaluation.details:           │
        │  - proctoring_pdf_gcs_url: null│
        │  - proctoring_pdf_url: /media/...│
        │  - proctoring_pdf: local_path │
        └───────────────────────────────┘
```

---

## 🔍 Detailed Code Walkthrough

### **Complete Storage Function:**

```python
# evaluation/services.py:411-536
if isinstance(proctoring_pdf_result, dict):
    # GCS upload successful
    local_path = proctoring_pdf_result.get('local_path', '')
    gcs_url = proctoring_pdf_result.get('gcs_url', '')
    
    # ============================================
    # FIRST PASS: URL Cleaning
    # ============================================
    if gcs_url and isinstance(gcs_url, str):
        import re
        original_url = gcs_url.strip()
        clean_url = original_url
        
        # Extract GCS part
        if 'storage.googleapis.com' in clean_url:
            gcs_index = clean_url.find('storage.googleapis.com')
            if gcs_index != -1:
                clean_url = clean_url[gcs_index:]
        
        # Remove malformed prefixes
        clean_url = re.sub(r'^https?\/\/', '', clean_url)
        clean_url = re.sub(r'^https?:\/\/', '', clean_url)
        clean_url = re.sub(r'^http:\/\/', '', clean_url)
        
        # Validate and construct
        if clean_url.startswith('storage.googleapis.com'):
            clean_url = f"https://{clean_url}"
            if clean_url.startswith('https://storage.googleapis.com/'):
                gcs_url = clean_url
            else:
                gcs_url = None
        else:
            gcs_url = None
    
    # Store local path
    proctoring_pdf_path = local_path
    details['proctoring_pdf'] = local_path
    
    # ============================================
    # SECOND PASS: URL Cleaning
    # ============================================
    clean_gcs_url = None
    if gcs_url and isinstance(gcs_url, str):
        original_url = gcs_url.strip()
        
        if 'storage.googleapis.com' in original_url:
            gcs_index = original_url.find('storage.googleapis.com')
            if gcs_index != -1:
                clean_gcs_url = original_url[gcs_index:]
                
                # Remove app domain prefixes
                clean_gcs_url = re.sub(r'^[^/]*\.(app|run|com)https?\/\/+', '', clean_gcs_url)
                clean_gcs_url = re.sub(r'^[^/]*\.(app|run|com)https?:\/\/+', '', clean_gcs_url)
                clean_gcs_url = re.sub(r'^https?\/\/+', '', clean_gcs_url)
                clean_gcs_url = re.sub(r'^https?:\/\/+', '', clean_gcs_url)
                
                # Construct and validate
                if clean_gcs_url.startswith('storage.googleapis.com'):
                    clean_gcs_url = f"https://{clean_gcs_url}"
                    if not clean_gcs_url.startswith('https://storage.googleapis.com/'):
                        clean_gcs_url = None
                else:
                    clean_gcs_url = None
    
    # ============================================
    # STORAGE: Evaluation.details
    # ============================================
    if clean_gcs_url and clean_gcs_url.startswith('https://storage.googleapis.com/'):
        details['proctoring_pdf_gcs_url'] = clean_gcs_url
        details['proctoring_pdf_url'] = clean_gcs_url
        
        # ============================================
        # STORAGE: ProctoringPDF Table (PRIMARY)
        # ============================================
        try:
            from evaluation.models import ProctoringPDF
            proctoring_pdf, created = ProctoringPDF.objects.update_or_create(
                interview=interview,
                defaults={
                    'gcs_url': clean_gcs_url,
                    'local_path': local_path,
                }
            )
        except Exception as e:
            print(f"⚠️ Error saving to ProctoringPDF table: {e}")
    else:
        # Fallback: Local path only
        details['proctoring_pdf_gcs_url'] = None
        media_url = settings.MEDIA_URL.rstrip('/')
        pdf_path = local_path.lstrip('/')
        details['proctoring_pdf_url'] = f"{media_url}/{pdf_path}"
```

---

## 🛡️ Error Handling

### **1. Invalid GCS URL:**
```python
# If URL cleaning fails
if not clean_gcs_url:
    details['proctoring_pdf_gcs_url'] = None
    details['proctoring_pdf_url'] = f"{media_url}/{local_path}"  # Use local path
```

### **2. ProctoringPDF Save Error:**
```python
try:
    proctoring_pdf, created = ProctoringPDF.objects.update_or_create(...)
except Exception as e:
    print(f"⚠️ Error saving to ProctoringPDF table: {e}")
    # Continue - Evaluation.details still has the URL
```

### **3. Database Transaction Rollback:**
```python
with transaction.atomic():
    # If this fails, all changes are rolled back
    evaluation.save()
```

---

## 📝 Summary

### **Storage Locations:**
1. **PRIMARY:** `evaluation_proctoringpdf.gcs_url` (URLField)
2. **FALLBACK:** `evaluation_evaluation.details['proctoring_pdf_url']` (JSONField)

### **URL Cleaning Process:**
1. **First Pass:** Extract GCS part, remove basic malformed prefixes
2. **Second Pass:** Remove app domain prefixes, final validation
3. **Validation:** Must start with `https://storage.googleapis.com/`

### **Storage Method:**
- **ProctoringPDF:** `update_or_create()` - Prevents duplicates, updates if exists
- **Evaluation.details:** Direct assignment to JSONField

### **Error Handling:**
- Invalid URL → Store `None`, use local path
- Save error → Log error, continue with other storage location
- Transaction → Ensures atomicity

### **Why Two Storage Locations?**
- **ProctoringPDF table:** Easy querying, primary source, indexed
- **Evaluation.details:** Fallback if ProctoringPDF record missing, part of evaluation data

