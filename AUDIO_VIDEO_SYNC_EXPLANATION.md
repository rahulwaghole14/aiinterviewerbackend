# Audio-Video Synchronization Explanation

## How the System Determines Where Extra Audio Is Located

The system uses **timestamps** and **durations** to determine exactly where extra audio is located (at the start or end) and how to match it with video.

## Step-by-Step Process

### 1. **Get Timestamps** (When recordings started)
- **Video timestamp**: Recorded when `start_video_recording()` is called
- **Audio timestamp**: Recorded when `startRecording()` is called (uses video timestamp if provided)

### 2. **Calculate Start Offset** (Extra audio at START?)

```
time_diff = audio_timestamp - video_timestamp
```

**Case A: Audio started AFTER video** (`time_diff > 0`)
- Example: Video started at 10:00:00, Audio started at 10:00:02
- **Extra audio is at the START** of the audio file
- **Solution**: Skip the first 2 seconds using `-ss 2` in FFmpeg

**Case B: Audio started BEFORE video** (`time_diff < 0`)
- Example: Video started at 10:00:02, Audio started at 10:00:00
- **Extra audio is at the START** of the audio file
- **Solution**: Skip the first 2 seconds using `-ss 2` in FFmpeg

**Case C: Audio and video started together** (`time_diff ≈ 0`)
- **No extra audio at start**
- **Solution**: No trimming needed

### 3. **Calculate End Offset** (Extra audio at END?)

After trimming the start, calculate effective audio duration:

```
effective_audio_duration = total_audio_duration - start_trim
```

**Case A: Audio continues AFTER video stops**
- Example: Video = 1.29 min, Audio = 4 min (after start trim)
- **Extra audio is at the END** of the audio file
- **Solution**: Limit audio to video duration using `-t 1.29` in FFmpeg

**Case B: Audio ends BEFORE video stops**
- Example: Video = 4 min, Audio = 1.29 min (after start trim)
- **No extra audio at end**
- **Solution**: Use `-shortest` flag (video will be trimmed)

**Case C: Audio and video end together**
- **No extra audio at end**
- **Solution**: Use `-shortest` flag

## Example Scenarios

### Scenario 1: Audio started early AND continues after video
```
Video: Starts at 10:00:00, Duration: 1.29 min (ends at 10:01:17)
Audio: Starts at 09:59:58, Duration: 4 min (ends at 10:03:58)

Analysis:
- Start offset: Audio started 2 seconds BEFORE video → trim 2s from start
- After start trim: Effective audio = 4 min - 2s = 3 min 58s
- End check: 3 min 58s > 1.29 min → Extra audio at END
- Solution: Skip 2s from start (-ss 2) + Limit to 1.29 min (-t 1.29)
```

### Scenario 2: Audio started late AND continues after video
```
Video: Starts at 10:00:00, Duration: 1.29 min (ends at 10:01:17)
Audio: Starts at 10:00:02, Duration: 4 min (ends at 10:04:02)

Analysis:
- Start offset: Audio started 2 seconds AFTER video → trim 2s from start
- After start trim: Effective audio = 4 min - 2s = 3 min 58s
- End check: 3 min 58s > 1.29 min → Extra audio at END
- Solution: Skip 2s from start (-ss 2) + Limit to 1.29 min (-t 1.29)
```

### Scenario 3: Perfect synchronization
```
Video: Starts at 10:00:00, Duration: 1.29 min
Audio: Starts at 10:00:00, Duration: 1.29 min

Analysis:
- Start offset: 0 seconds → No trim needed
- End check: Durations match → No trim needed
- Solution: Direct merge with -shortest flag
```

## FFmpeg Command Structure

The final FFmpeg command looks like this:

```bash
ffmpeg \
  -i video.mp4 \                    # Video input
  -ss 2.0 -i audio.webm \          # Audio input (skip 2s from start if needed)
  -c:v copy \                       # Copy video (no re-encoding)
  -c:a aac -b:a 192k \              # Encode audio
  -t 1.29 \                         # Limit to video duration (if audio longer)
  -y output.mp4                     # Output file
```

## Key Points

1. **Start trim** (`-ss`) is determined by **timestamp difference**
   - If audio started before/after video, skip that amount from audio start

2. **End trim** (`-t`) is determined by **duration comparison**
   - If audio is longer than video (after start trim), limit to video duration

3. **Both can happen simultaneously**
   - Audio can have extra at BOTH start and end
   - System handles both cases automatically

4. **Logging shows exactly what's happening**
   - System logs where extra audio is located
   - Shows exact trim amounts
   - Explains the synchronization strategy

## Result

After merging:
- ✅ Audio and video start at the same time
- ✅ Audio and video end at the same time
- ✅ No extra audio at start or end
- ✅ Perfect synchronization throughout


