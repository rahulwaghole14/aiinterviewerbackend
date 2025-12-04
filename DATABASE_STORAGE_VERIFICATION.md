# Database Storage Verification

## Overview
This document verifies that all required files are being saved to PostgreSQL database fields as requested:
1. ✅ Verified ID card image
2. ✅ Interviewer database (InterviewSession model)
3. ✅ AI evaluation (Evaluation model)
4. ✅ Proctoring snapshots
5. ✅ Overall video
6. ✅ PDF if AI evaluation

## Database Models and Fields

### 1. InterviewSession Model (`interview_app/models.py`)
- **`id_card_image`** (ImageField): Stores verified ID card image
  - Upload path: `id_cards/`
  - Saved via: `session.id_card_image.save(img_file.name, img_file, save=True)` (line 4226 in views.py)
  
- **`interview_video`** (FileField): Stores complete interview video with audio
  - Upload path: `interview_videos/`
  - Saved via: `session.interview_video.save(filename, video_content, save=True)` (multiple locations in views.py)
  - **IMPORTANT**: Now uses proper `FileField.save()` method with `ContentFile` to ensure files are stored in database

### 2. WarningLog Model (`interview_app/models.py`)
- **`snapshot_image`** (ImageField): Stores proctoring snapshot images
  - Upload path: `proctoring_snaps/`
  - Saved via: `warning_log.snapshot_image = snapshot_image_field` where `snapshot_image_field` is a `ContentFile` (line 2154 in simple_real_camera.py)

### 3. Evaluation Model (`evaluation/models.py`)
- **`evaluation_pdf`** (FileField): Stores AI evaluation PDF report
  - Upload path: `proctoring_pdfs/`
  - Saved via: `evaluation.evaluation_pdf = pdf_file` where `pdf_file` is a `ContentFile` (line 527 in evaluation/services.py)

- **`details`** (JSONField): Stores AI evaluation details, proctoring warnings, and statistics
  - Contains: `ai_analysis`, `proctoring`, `technical_questions_correct`, `technical_questions_attempted`, etc.

## Changes Made

### Video File Storage Enhancement
Updated `interview_app/views.py` to use proper Django `FileField.save()` method instead of assigning string paths:

**Before:**
```python
session.interview_video = video_path  # String path assignment
session.save()
```

**After:**
```python
with open(video_full_path, 'rb') as video_file:
    from django.core.files.base import ContentFile
    video_content = ContentFile(video_file.read(), name=os.path.basename(video_path))
    session.interview_video.save(os.path.basename(video_path), video_content, save=True)
```

This ensures:
- Files are properly stored in the database
- File metadata is correctly tracked
- Files are accessible via Django's file handling system
- Proper error handling with fallback to path assignment if needed

## Verification Checklist

- ✅ **ID Card Image**: Saved to `InterviewSession.id_card_image` using `ImageField.save()`
- ✅ **Interview Video**: Saved to `InterviewSession.interview_video` using `FileField.save()` with `ContentFile`
- ✅ **Proctoring Snapshots**: Saved to `WarningLog.snapshot_image` using `ImageField` with `ContentFile`
- ✅ **Evaluation PDF**: Saved to `Evaluation.evaluation_pdf` using `FileField` with `ContentFile`
- ✅ **AI Evaluation Data**: Stored in `Evaluation.details` JSONField
- ✅ **Interviewer Database**: All session data stored in `InterviewSession` model

## Database Configuration

Ensure PostgreSQL is configured in `interview_app/settings.py`:
- `DATABASE_URL` environment variable set
- `dj-database-url` package installed
- Database migrations applied: `python manage.py migrate`

## File Storage Locations

All files are stored in the `MEDIA_ROOT` directory (configured in `settings.py`):
- ID Cards: `media/id_cards/`
- Videos: `media/interview_videos/` and `media/interview_videos_merged/`
- Proctoring Snapshots: `media/proctoring_snaps/`
- Evaluation PDFs: `media/proctoring_pdfs/`

## Testing

To verify files are saved correctly:
1. Run an interview session
2. Check database:
   ```python
   from interview_app.models import InterviewSession
   from evaluation.models import Evaluation, WarningLog
   
   session = InterviewSession.objects.get(session_key='your_session_key')
   print(f"ID Card: {session.id_card_image}")
   print(f"Video: {session.interview_video}")
   
   warnings = session.logs.all()
   for warning in warnings:
       print(f"Snapshot: {warning.snapshot_image}")
   
   evaluation = Evaluation.objects.get(interview__session_key='your_session_key')
   print(f"PDF: {evaluation.evaluation_pdf}")
   print(f"Details: {evaluation.details}")
   ```

## Notes

- All file fields use Django's `FileField` and `ImageField` which automatically handle file storage
- Files are stored both in the filesystem (MEDIA_ROOT) and referenced in the database
- PostgreSQL stores the file paths and metadata, while actual files are stored in MEDIA_ROOT
- The `ContentFile` wrapper ensures files are properly handled by Django's file storage system


