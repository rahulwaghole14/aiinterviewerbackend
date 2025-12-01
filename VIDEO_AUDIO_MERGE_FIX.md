# Video and Audio Merge Functionality - Fixed

## Overview
This document describes the fixes implemented to ensure proper merging of video and audio recordings in the interview portal. The system now **only saves merged videos** (video + audio combined) and **removes unmerged videos** to prevent confusion.

## Problem Statement
Previously, the system was saving unmerged videos (video without audio) or not properly merging audio with video. This resulted in:
- Videos being saved without audio tracks
- Both merged and unmerged videos existing simultaneously
- Users downloading videos without audio

## Solution Implemented

### 1. **Backend Video Recording Merge** (`simple_real_camera.py`)
- **Location**: `stop_video_recording()` method
- **Changes**:
  - Merges video and audio using FFmpeg when audio file is provided
  - **Removes original unmerged video** after successful merge
  - Returns **relative path** of merged video (with `_with_audio.mp4` suffix)
  - Verifies merged video has audio track before returning
  - Detailed logging at each step

### 2. **Frontend Video Upload Merge** (`views.py` - `upload_interview_video`)
- **Location**: `/ai/recording/upload_video/` endpoint
- **Changes**:
  - Checks for separate audio file in `interview_audio/` directory
  - If audio found, merges with uploaded video using FFmpeg
  - **Removes original unmerged video** after merge
  - Only saves merged video to database
  - Returns status indicating if merge occurred

### 3. **Session End Merge** (`views.py` - `end_interview_session`)
- **Location**: `/ai/end_session/` endpoint
- **Changes**:
  - Verifies only merged videos (with `_with_audio` suffix) are saved
  - Checks for merged video if unmerged path is detected
  - Detailed logging of merge status
  - Verifies audio track exists in saved video

### 4. **Camera Release Merge** (`views.py` - `release_camera_for_session`)
- **Location**: Called when camera resources are released
- **Changes**:
  - Added `verify_video_has_audio()` function to check audio tracks
  - Verifies merged videos before saving to database
  - Detailed logging of merge process
  - Warns if unmerged video is detected

## Key Features

### ✅ Only Merged Videos Saved
- All video paths saved to database have `_with_audio.mp4` suffix
- Original unmerged videos are **automatically deleted** after merge
- System verifies merged videos have audio tracks

### ✅ Automatic Audio Detection
- System automatically finds audio files in `interview_audio/` directory
- Matches audio files by session key
- Supports multiple audio formats (`.webm`, `.ogg`, `.wav`)

### ✅ Detailed Logging
- Every merge operation is logged with:
  - File sizes (video and audio)
  - Merge status (success/failure)
  - Audio track verification
  - File paths (original and merged)
  - Warnings if unmerged videos are detected

### ✅ Error Handling
- Graceful fallback if FFmpeg is not available
- Continues with video-only if merge fails
- Detailed error messages for debugging

## File Structure

### Merged Video Naming
- **Format**: `{original_name}_with_audio.mp4`
- **Example**: `interview_abc123_20250101_120000_with_audio.mp4`
- **Location**: `media/interview_videos/`

### Audio File Location
- **Directory**: `media/interview_audio/`
- **Format**: `{session_key}_interview_audio.{ext}`
- **Example**: `abc123_interview_audio.webm`

## Verification Process

### 1. Merge Verification
After merging, the system:
1. Checks merged file exists and is not empty
2. Verifies audio track using FFmpeg probe
3. Removes original unmerged video
4. Logs verification results

### 2. Database Save Verification
Before saving to database:
1. Checks if path contains `_with_audio` suffix
2. Verifies file exists on disk
3. Checks file size is > 0
4. Optionally verifies audio track exists

## Usage Flow

### Scenario 1: Backend Video + Frontend Audio
```
1. Backend starts video recording (no audio)
2. Frontend starts audio recording (microphone)
3. Interview ends
4. Frontend uploads audio → /ai/recording/upload_audio/
5. Frontend calls end_interview_session with audio_file_path
6. Backend merges video + audio using FFmpeg
7. Original video deleted, merged video saved
8. Database stores merged video path
```

### Scenario 2: Frontend Video Upload (with embedded audio)
```
1. Frontend records video with MediaRecorder (video + audio)
2. Interview ends
3. Frontend uploads video → /ai/recording/upload_video/
4. System checks for separate audio file
5. If found, merges with uploaded video
6. If not found, uses uploaded video as-is (already has audio)
7. Database stores final video path
```

## Testing Checklist

- [ ] Video recording starts correctly
- [ ] Audio recording starts correctly
- [ ] Audio file is uploaded successfully
- [ ] Merge process completes without errors
- [ ] Original unmerged video is deleted
- [ ] Merged video has audio track (verified)
- [ ] Database stores merged video path
- [ ] Video playback has audio
- [ ] Download functionality works with merged video

## Debugging

### Check Merge Status
Look for these log messages:
- `✅ Video and audio merged successfully!` - Merge completed
- `✅ Verified: Merged video contains audio track` - Audio verified
- `🗑️ Removed original video without audio` - Original deleted
- `⚠️ WARNING: Attempting to save unmerged video` - Issue detected

### Common Issues

1. **FFmpeg not found**
   - Install FFmpeg at one of the paths checked by `get_ffmpeg_path()`
   - Or add FFmpeg to system PATH

2. **Audio file not found**
   - Check `media/interview_audio/` directory
   - Verify audio file naming matches session key
   - Check audio upload completed successfully

3. **Merge fails**
   - Check FFmpeg output in logs
   - Verify video and audio file formats are compatible
   - Check file permissions

## Technical Details

### FFmpeg Merge Command
```bash
ffmpeg -i video.mp4 -i audio.webm \
  -filter_complex '[0:v]setpts=PTS-STARTPTS[v];[1:a]asetpts=PTS-STARTPTS,aresample=async=1[a]' \
  -map '[v]' -map '[a]' \
  -c:v libx264 -preset medium -crf 23 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -ar 44100 -ac 2 \
  -shortest -movflags +faststart \
  -y output_with_audio.mp4
```

### Audio Track Verification
```bash
ffmpeg -i video.mp4 -hide_banner
# Checks for "Audio:" or "Stream #0:1" in output
```

## Summary

✅ **Only merged videos are saved** - Original unmerged videos are automatically deleted
✅ **Automatic audio detection** - System finds and merges audio files automatically
✅ **Comprehensive verification** - Audio tracks are verified before saving
✅ **Detailed logging** - Every step is logged for debugging
✅ **Error handling** - Graceful fallbacks if merge fails

The system now ensures that **all saved videos have audio merged**, and **unmerged videos are never saved or downloaded**.

