# 🐛 Video Recording Debug Guide

## Current Status: ❌ Recording NOT saving

### What I Found:
- ✅ Directories created: `media/interview_recordings/` and `media/video_chunks/`
- ❌ **NO video files exist** (only TTS .mp3 files)
- ❌ Recording is NOT being triggered or chunks aren't uploading

---

## 🔍 Step-by-Step Debug Process

### **STEP 1: Test Browser Recording (Most Important)**

Open browser console (F12) during interview and run these commands:

```javascript
// 1. Check if recorder exists
console.log('Recorder:', videoRecorder);
console.log('Recorder type:', typeof videoRecorder);

// 2. Check if it's defined
if (typeof videoRecorder === 'undefined') {
    console.error('❌ videoRecorder is UNDEFINED!');
} else {
    console.log('✅ videoRecorder exists');
}

// 3. Check recording status
if (videoRecorder) {
    console.log('Is recording:', videoRecorder.isRecording);
    console.log('Session key:', videoRecorder.sessionKey);
}

// 4. Try to manually start recording
if (videoRecorder && !videoRecorder.isRecording) {
    console.log('Attempting to start recording...');
    videoRecorder.startRecording().then(result => {
        console.log('Start result:', result);
    }).catch(err => {
        console.error('Start error:', err);
    });
}
```

**What to look for:**
- If "videoRecorder is UNDEFINED" → Script didn't load
- If "Permission denied" → Camera/mic access blocked
- If "Start result: true" → Recording started successfully!

---

### **STEP 2: Check Console During Interview**

When you start an interview, you MUST see these messages in console:

```
📹 Video recorder initialized
🎥 Starting video recording...
✅ Recording started successfully
📹 Chunk recorded: 45231 bytes (total: 1)
📹 Chunk recorded: 52145 bytes (total: 2)
```

**If you DON'T see these messages:**
→ Recording never started → Fix: Grant camera/mic permissions

---

### **STEP 3: Test Upload Endpoint**

Check if the upload endpoint works:

```javascript
// Test upload endpoint
fetch('/ai/recording/upload_chunk/', {
    method: 'POST',
    body: new FormData()
}).then(r => r.json()).then(console.log).catch(console.error);
```

**Expected response:**
```json
{"error": "session_key and video_chunk required"}
```

**If you get 404 error:**
→ URL endpoint not registered → Server restart needed

---

### **STEP 4: Check Server Logs**

Look at your Django console for these messages when interview completes:

```
📹 Chunk 0 uploaded successfully
📹 Merging video chunks for session abc123...
✅ Merged 2 chunks into interview_abc123_20251121_123456.webm (85.32 MB)
✅ Saved recording to Interview model: interview_recordings/...
```

**If you DON'T see these:**
→ Chunks never reached server → Check network tab (F12)

---

## 🚨 Common Problems & Solutions

### **Problem 1: "videoRecorder is undefined"**

**Cause:** Script didn't load properly

**Solution:**
```javascript
// Check if InterviewVideoRecorder class exists
console.log('Class exists:', typeof InterviewVideoRecorder);

// If undefined, the embedded script in portal.html isn't loaded
// → Hard refresh browser: Ctrl + Shift + R
// → Clear cache and reload
```

---

### **Problem 2: "Permission denied" when starting**

**Cause:** Camera/microphone permissions blocked

**Solution:**
1. Click camera icon in browser address bar
2. Change to "Allow" for both camera and microphone
3. Refresh page and try again

---

### **Problem 3: Recording starts but no chunks uploaded**

**Cause:** Network error or CSRF token issue

**Solution:**
Check browser Network tab (F12 → Network):
- Look for POST requests to `/ai/recording/upload_chunk/`
- If RED (failed) → Click it and check error
- If 403 Forbidden → CSRF token issue
- If 404 Not Found → URL not registered

---

### **Problem 4: Chunks uploaded but not in candidate details**

**Cause:** Database not updated

**Solution:**
Check database manually:

```python
# Django shell
python manage.py shell

from interviews.models import Interview

# Get latest interview
interview = Interview.objects.latest('created_at')

# Check ai_result
print(interview.ai_result)

# Should contain:
# {'recording_video': 'interview_recordings/...', ...}
```

---

## 🔧 Quick Fix Script

Run this in browser console DURING interview to force recording:

```javascript
// Force start recording
if (!window.videoRecorder) {
    console.log('Creating recorder...');
    window.videoRecorder = new InterviewVideoRecorder(SESSION_KEY);
}

videoRecorder.startRecording().then(success => {
    if (success) {
        console.log('✅ Recording started!');
        console.log('📹 Speak now for 10 seconds...');
        
        // Auto-stop after 10 seconds for testing
        setTimeout(() => {
            console.log('🛑 Stopping test recording...');
            videoRecorder.stopRecording();
        }, 10000);
    } else {
        console.error('❌ Failed to start');
    }
}).catch(err => {
    console.error('❌ Error:', err);
    alert('Recording error: ' + err.message);
});
```

---

## 📊 Full Diagnostic Script

Copy-paste this into browser console for complete diagnostic:

```javascript
console.log('=== VIDEO RECORDING DIAGNOSTICS ===');

// 1. Check class
console.log('1. InterviewVideoRecorder class:', typeof InterviewVideoRecorder);

// 2. Check instance
console.log('2. videoRecorder instance:', typeof videoRecorder);

// 3. Check session key
console.log('3. SESSION_KEY:', SESSION_KEY);

// 4. Check if recording
if (videoRecorder) {
    console.log('4. Is recording:', videoRecorder.isRecording);
    console.log('   Recorded chunks:', videoRecorder.recordedChunks?.length || 0);
    console.log('   Chunk index:', videoRecorder.chunkIndex);
}

// 5. Test camera permissions
navigator.mediaDevices.getUserMedia({video: true, audio: true})
    .then(() => console.log('5. ✅ Camera/Mic permissions: GRANTED'))
    .catch(err => console.error('5. ❌ Camera/Mic permissions: DENIED -', err.message));

// 6. Test upload endpoint
fetch('/ai/recording/upload_chunk/', {method: 'HEAD'})
    .then(r => console.log('6. ✅ Upload endpoint exists (status:', r.status, ')'))
    .catch(err => console.error('6. ❌ Upload endpoint error:', err.message));

console.log('=== END DIAGNOSTICS ===');
```

---

## 🎯 Action Plan

Based on diagnostics, follow this order:

1. **If "videoRecorder is undefined":**
   - Hard refresh browser (Ctrl+Shift+R)
   - Check portal.html has the embedded script
   - Restart Django server

2. **If permissions denied:**
   - Grant camera/mic access in browser
   - Test with test_video_recording.html first

3. **If recording but not saving:**
   - Check Django console for upload messages
   - Check Network tab for failed requests
   - Verify media directory permissions

4. **If saved but not in candidate details:**
   - Check Interview model ai_result field
   - Verify CandidateDetails.jsx is checking recording_video
   - Hard refresh React app

---

## 💡 Most Likely Issue

Based on empty recordings folder, the most likely cause is:

**Recording is NOT starting in the browser**

This is usually because:
1. ❌ Camera/microphone permissions not granted
2. ❌ videoRecorder not initialized
3. ❌ startRecording() never called

**Quick test:**
Open interview portal → F12 console → Type:
```javascript
videoRecorder
```

If you see: `undefined` → Script didn't load
If you see: `InterviewVideoRecorder {sessionKey: "...", ...}` → Good!

Then type:
```javascript
videoRecorder.startRecording()
```

Should see: Red "RECORDING" badge appear

---

## 📞 Next Steps

1. **DO THIS NOW:** Open an interview in browser
2. **Open console** (F12)
3. **Run diagnostic script** (from above)
4. **Share the console output** with me

I'll tell you exactly what's wrong! 🎯

