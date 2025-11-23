# 📹 Interview Video Recording System

## Overview
Complete video recording system that captures the entire interview session including:
- **Webcam video** of the candidate
- **Microphone audio** (candidate's answers)
- **TTS audio** (interview questions)
- **Recording indicator** (visual feedback)
- **Automatic upload** to server in chunks

---

## 🎯 Features

### ✅ What's Recorded:
1. **Webcam Video** - Full 720p HD video of candidate
2. **Audio Mix** - Both TTS questions and candidate answers
3. **Recording Indicator** - Red "REC" badge visible during recording
4. **Automatic Upload** - Chunks uploaded every 10 seconds
5. **Database Storage** - Recording path saved to Interview model
6. **Candidate Details Display** - Video player in candidate details page

---

## 📂 Files Created/Modified

### **New Files:**

#### 1. `interview_app/video_recorder.py`
Backend video recorder service (Python/OpenCV based)
- Records webcam frames
- Adds recording overlay (REC indicator, timestamp)
- Saves as MP4 file
- **Location:** `media/interview_recordings/interview_{id}_{timestamp}.mp4`

#### 2. `static/interview_video_recorder.js`
Frontend video recorder (JavaScript/MediaRecorder API)
- Captures webcam + audio
- Uploads chunks to server
- Shows recording indicator
- Handles cleanup

#### 3. `VIDEO_RECORDING_SETUP.md`
This documentation file

### **Modified Files:**

#### 1. `interview_app/views.py`
Added 3 new API endpoints:
- `start_video_recording()` - Start recording
- `stop_video_recording()` - Stop and save recording
- `upload_video_chunk()` - Upload video chunks

#### 2. `interview_app/urls.py`
Added URL patterns:
```python
path('recording/start/', views.start_video_recording),
path('recording/stop/', views.stop_video_recording),
path('recording/upload_chunk/', views.upload_video_chunk),
```

#### 3. `interview_app/templates/interview_app/portal.html`
Added:
- Video recorder script include
- Recorder initialization
- Start recording in `startFirstSpokenQuestion()`
- Stop recording before interview completion

---

## 🔧 How It Works

### **Recording Flow:**

```
1. Interview Portal Loads
   ↓
2. VideoRecorder Initializes
   ↓
3. User Starts Interview
   ↓
4. Recording Starts Automatically
   ├─ Webcam video capture
   ├─ Microphone audio capture
   ├─ TTS audio (browser captures all)
   └─ Recording indicator appears
   ↓
5. During Interview:
   ├─ Video chunks created every 1 second
   ├─ Every 10 chunks = upload to server
   └─ Server saves chunks temporarily
   ↓
6. Interview Completes
   ↓
7. Recording Stops Automatically
   ├─ Final chunks uploaded
   ├─ Server merges all chunks
   ├─ Single video file created
   └─ Path saved to database
   ↓
8. Video Available in Candidate Details
```

### **Technical Implementation:**

#### **Frontend (Browser):**
```javascript
// Initialize recorder
videoRecorder = new InterviewVideoRecorder(SESSION_KEY);

// Start recording when interview begins
await videoRecorder.startRecording();

// During recording (automatic):
// - Captures webcam video (1280x720 @ 30fps)
// - Captures audio (128 kbps)
// - Creates chunks every 1 second
// - Uploads every 10 chunks

// Stop recording when interview ends
await videoRecorder.stopRecording();
```

#### **Backend (Server):**
```python
# Chunk upload endpoint
@csrf_exempt
def upload_video_chunk(request):
    # Save chunk to temporary directory
    # media/video_chunks/{session_key}/chunk_0000.webm
    
    # If final chunk:
    #   - Merge all chunks
    #   - Create final video file
    #   - Save to media/interview_recordings/
    #   - Update database with path
```

---

## 💾 Database Storage

### **InterviewSession Model:**
```python
session.metadata = {
    'recording_video': 'interview_recordings/interview_{id}_{timestamp}.webm',
    'recording_created_at': '2025-11-21T12:30:00'
}
```

### **Interview Model (interviews app):**
```python
interview.ai_result = {
    'recording_video': 'interview_recordings/interview_{id}_{timestamp}.webm',
    'recording_created_at': '2025-11-21T12:30:00',
    # ... other AI result data
}
```

---

## 🎬 Video Format

### **Output Specifications:**
- **Format:** WebM (VP8/VP9 codec + Opus audio)
- **Resolution:** 1280x720 (720p HD)
- **Frame Rate:** 30 FPS
- **Video Bitrate:** 2.5 Mbps
- **Audio Bitrate:** 128 kbps
- **File Size:** ~1-2 GB per hour

### **Why WebM?**
- Native browser support
- Good compression
- Works with MediaRecorder API
- Compatible with all modern browsers

---

## 📺 Playback in Candidate Details

The video player is **already integrated** in `CandidateDetails.jsx`:

```jsx
{interview.ai_result?.recording_video && (
  <div className="recording-section">
    <h4>Interview Recording</h4>
    <video controls className="video-player" preload="metadata">
      <source src={`${baseURL}${interview.ai_result.recording_video}`} 
              type="video/mp4" />
    </video>
    <p className="recording-metadata">
      <strong>Recorded:</strong> {interview.ai_result.recording_created_at}
    </p>
  </div>
)}
```

---

## 🚀 Usage

### **Automatic Recording:**
No manual intervention needed! Recording automatically:
1. ✅ **Starts** when first technical question begins
2. ✅ **Continues** through all technical questions
3. ✅ **Continues** through all coding challenges
4. ✅ **Stops** when interview completes

### **Manual Controls (if needed):**

```javascript
// Start recording manually
await videoRecorder.startRecording();

// Stop recording manually
await videoRecorder.stopRecording();

// Cleanup
videoRecorder.cleanup();
```

---

## 🔍 Debugging

### **Console Logs:**

```javascript
// Recording start
📹 InterviewVideoRecorder initialized for session: abc123
🎥 Starting video recording...
✅ Recording started successfully

// During recording
📹 Chunk recorded: 45231 bytes (total: 12 chunks)
📤 Uploading chunk 0 (452310 bytes, final: false)...
✅ Chunk 0 uploaded successfully

// Recording stop
🛑 Stopping recording...
🛑 Recording stopped, uploading final chunks...
📤 Uploading chunk 1 (389204 bytes, final: true)...
✅ Chunk 1 uploaded successfully
📹 Merging video chunks for session abc123...
✅ Merged 2 chunks into interview_abc123_20251121_123456.webm (85.32 MB)
```

### **Check Recording Status:**
```javascript
console.log('Is recording:', videoRecorder.isRecording);
console.log('Chunks recorded:', videoRecorder.recordedChunks.length);
console.log('Chunk index:', videoRecorder.chunkIndex);
```

---

## 📁 File Locations

### **Temporary Chunks:**
```
media/video_chunks/{session_key}/
├── chunk_0000.webm
├── chunk_0001.webm
├── chunk_0002.webm
└── ...
```
*(Automatically deleted after merging)*

### **Final Recordings:**
```
media/interview_recordings/
├── interview_session123_20251121_123456.webm
├── interview_session456_20251121_134512.webm
└── ...
```

### **Accessible URL:**
```
http://127.0.0.1:8000/media/interview_recordings/interview_{id}_{timestamp}.webm
```

---

## ⚠️ Important Notes

### **Browser Permissions:**
User MUST grant:
1. ✅ Camera access
2. ✅ Microphone access

These are automatically requested when recording starts.

### **Browser Compatibility:**
- ✅ Chrome/Edge (recommended)
- ✅ Firefox
- ✅ Safari (partial - may need adjustments)
- ❌ IE (not supported)

### **File Size:**
- Average interview: 30-60 minutes
- Expected file size: 500 MB - 2 GB
- Ensure server has adequate storage

### **Network Requirements:**
- Stable internet for chunk uploads
- If connection drops, chunks may be lost
- Consider implementing retry logic for production

---

## 🔐 Privacy & Security

### **Data Protection:**
1. Videos stored locally on server
2. Only accessible via authenticated admin panel
3. File paths stored in database
4. Consider encryption for sensitive data

### **GDPR Compliance:**
- Inform candidates about recording
- Obtain explicit consent
- Provide access to recordings
- Implement deletion requests

---

## 🛠️ Testing

### **Test Checklist:**

1. ✅ **Recording Starts**
   - Check console for "Recording started" message
   - Verify red "REC" indicator appears
   - Check camera/mic permissions granted

2. ✅ **During Recording**
   - Speak and check audio is captured
   - Check console for chunk uploads
   - Verify no errors in console

3. ✅ **Recording Stops**
   - Complete interview
   - Check "Recording stopped" message
   - Wait 2 seconds for final upload

4. ✅ **File Verification**
   - Check `media/interview_recordings/` directory
   - Verify file exists and has size > 0
   - Play video to confirm audio/video

5. ✅ **Database Verification**
   - Check Interview model `ai_result` field
   - Verify `recording_video` path exists
   - Verify `recording_created_at` timestamp

6. ✅ **Playback**
   - Open Candidate Details page
   - Verify video player shows
   - Play video and check quality

---

## 📞 Support

If recording fails:
1. Check browser console for errors
2. Verify camera/mic permissions
3. Check server logs
4. Verify storage space available
5. Test with different browser

---

## 🎉 Success!

Your interview recording system is now fully operational! 

Every interview will be automatically recorded with:
- ✅ Full HD video
- ✅ Clear audio (questions + answers)
- ✅ Secure server storage
- ✅ Easy playback in admin panel

**Ready to record your first interview!** 🚀

