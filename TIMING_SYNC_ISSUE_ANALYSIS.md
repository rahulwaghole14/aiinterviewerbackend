# Video-Audio Timing Synchronization Issue Analysis

## Root Cause: Why Video and Audio Don't Start at the Exact Same Time

### The Problem

Video and audio recordings start at **different times** because they run on **two separate systems** with **multiple delays**:

### 1. **Video Recording Timeline (Backend Python)**

```
T0: start_video_recording() called
    ↓ (timestamp recorded here: line 386)
T1: VideoWriter created (lines 414-446)
    ↓ (up to 0.2 seconds delay)
T2: First frame actually written (line 1267 in capture loop)
```

**Issue**: Timestamp is recorded at T0, but first frame is written at T2 (up to 0.2s later)

### 2. **Audio Recording Timeline (Frontend JavaScript)**

```
T0: Backend records video timestamp
    ↓ (network delay: 10-100ms)
T1: Frontend receives timestamp via API
    ↓ (JavaScript execution: 5-20ms)
T2: startAudioRecording() called
    ↓ (getUserMedia() async: 50-200ms)
T3: Microphone permission granted
    ↓ (AudioContext creation: 10-50ms)
T4: AudioContext initialized
    ↓ (MediaRecorder setup: 10-30ms)
T5: MediaRecorder.start() called
    ↓ (MediaRecorder initialization: 10-50ms)
T6: Audio actually starts recording
```

**Total delay from T0 to T6: 95-450ms**

### 3. **The Mismatch**

- **Video timestamp**: Recorded when `start_video_recording()` is called (T0)
- **Video actual start**: First frame written (T0 + up to 200ms)
- **Audio timestamp**: Recorded when `startRecording()` is called (T2)
- **Audio actual start**: MediaRecorder actually starts (T6 = T0 + 95-450ms)

**Result**: Audio starts 95-450ms AFTER video timestamp, but video frames might not start until 200ms after timestamp.

### 4. **Stopping Mismatch**

- **Video stops**: When `stop_video_recording()` is called
- **Audio stops**: When user ends interview or `stopRecording()` is called
- These happen at **different times** (can be seconds apart)

## Solutions

### Solution 1: Record Video Timestamp When First Frame is Written (RECOMMENDED)

Change video timestamp to be recorded when the **first frame is actually written**, not when the function is called.

### Solution 2: Pre-buffer Audio and Trim

Start audio recording immediately, buffer the audio, then trim from the beginning to match video start time during merge.

### Solution 3: Use WebSocket for Synchronized Start

Use WebSocket to signal both systems to start at the exact same moment (requires architectural changes).

### Solution 4: Use Video Duration as Authoritative (CURRENT APPROACH)

Use video duration as the authoritative length and trim audio to match during merge. This is what we're doing now, but it doesn't solve the start time mismatch.

## Recommended Fix

**Implement Solution 1 + Solution 2**:
1. Record video timestamp when first frame is written
2. Start audio recording immediately (before video timestamp is received)
3. During merge, trim audio from the beginning to match video start time

This ensures both recordings start as close as possible and are perfectly aligned during merge.




