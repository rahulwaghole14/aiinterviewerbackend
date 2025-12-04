# Video-Audio Merge Fix Summary

## Problem
- Video and audio files were being saved but not merged
- Video path was `None` when trying to merge, causing merge failures
- No clear separation between raw videos (without audio) and merged videos (with audio)

## Solution

### 1. Created Two Separate Folders
- **`interview_videos_raw/`**: Stores raw videos without audio
- **`interview_videos_merged/`**: Stores merged videos with audio

### 2. Enhanced Video Path Lookup
The system now searches for video files in multiple ways:
1. **Filesystem search** in `interview_videos_raw/` and `interview_videos/` (old folder)
2. **Database lookup** by session_id (UUID) or session_key
3. **Comprehensive search** across all video directories if initial searches fail

### 3. Improved Merge Process
- Raw videos are saved to `interview_videos_raw/` during recording
- When audio is available, videos are merged and saved to `interview_videos_merged/`
- Only merged videos (with `_with_audio` suffix or in `interview_videos_merged/`) are returned and saved to database
- Original raw videos are removed after successful merge

### 4. Key Changes

#### `interview_app/simple_real_camera.py`
- `start_video_recording()`: Saves raw videos to `interview_videos_raw/`
- `stop_video_recording()`: 
  - Enhanced video path lookup (filesystem + database)
  - Merges audio and saves to `interview_videos_merged/`
  - Only returns merged video paths
  - Removes original raw video after merge

#### `interview_app/views.py`
- `end_interview_session()`: 
  - Searches filesystem for videos if not in database
  - Sets video path in camera object before merging
  - Ensures only merged videos are saved to database

## File Structure
```
media/
├── interview_videos_raw/      # Raw videos without audio
│   └── {session_id}_{timestamp}.mp4
├── interview_videos_merged/    # Merged videos with audio
│   └── {session_id}_{timestamp}_with_audio.mp4
└── interview_audio/            # Audio files
    └── {session_key}_interview_audio_converted.wav
```

## Verification
- ✅ Raw videos saved to `interview_videos_raw/`
- ✅ Merged videos saved to `interview_videos_merged/`
- ✅ Only merged videos saved to database
- ✅ Original raw videos removed after merge
- ✅ Video path lookup works even if video not in database yet






