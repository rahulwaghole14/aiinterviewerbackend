# 🎥 Video Recording - Complete Troubleshooting Guide

## ✅ Latest Updates Applied

I've added **comprehensive debugging** to the video recording system. Here's what changed:

### **1. Enhanced Initialization Logging**
When portal loads, you'll now see in console:
```
🔍 Checking InterviewVideoRecorder class: function
🔍 SESSION_KEY: abc123...
✅ Video recorder initialized successfully
📹 Recorder object: InterviewVideoRecorder {sessionKey: "...", ...}
🎥 VIDEO RECORDING ENABLED
```

### **2. Enhanced Recording Start Logging**
When interview starts, you'll see:
```
🎬 ATTEMPTING TO START VIDEO RECORDING
videoRecorder exists: true
videoRecorder: InterviewVideoRecorder {...}
📹 Calling startRecording()...
🎥 Starting video recording...
✅ Recording started successfully!
✅ VIDEO RECORDING STARTED!
📹 You should see a red "RECORDING" indicator in top-right corner
```

### **3. Global Variables for Debugging**
You can now access these in console:
```javascript
window.videoRecorder      // The recorder instance
window.InterviewVideoRecorder  // The class
```

---

## 🧪 TESTING STEPS (Do This Now!)

### **Test 1: Simple Recording Test Page**

1. **Open test page:**
   ```
   http://127.0.0.1:8000/static/test_video_recording.html
   ```

2. **Click buttons in order:**
   - "1. Test Camera Permissions" → Should show preview
   - "2. Start Recording" → Should see "Recording in progress"
   - Speak for 10 seconds
   - "3. Stop Recording" → Should create download link

3. **Download and play the video** to verify it works

**If this test fails:**
→ Browser/camera issue (not our code issue)
→ Grant permissions and try again

**If this test succeeds:**
→ Recording works! Issue is with portal integration

---

### **Test 2: Interview Portal Recording**

1. **Start Django server** (restart if running):
   ```bash
   python manage.py runserver
   ```

2. **Start a new interview:**
   ```
   http://127.0.0.1:8000/ai/?session_key=test123
   ```

3. **Open Browser Console (F12)** IMMEDIATELY

4. **Look for these messages:**
   ```
   🔍 Checking InterviewVideoRecorder class: function
   ✅ Video recorder initialized successfully
   ```

5. **When interview starts, look for:**
   ```
   🎬 ATTEMPTING TO START VIDEO RECORDING
   📹 Calling startRecording()...
   ✅ VIDEO RECORDING STARTED!
   ```

6. **You MUST see:**
   - Red "RECORDING" badge in top-right corner
   - Browser asking for camera/microphone permissions (if first time)

7. **In console, type:**
   ```javascript
   videoRecorder.isRecording
   ```
   Should return: `true`

8. **Complete the interview** (answer 1-2 questions)

9. **Check for chunks uploaded:**
   Look for console messages:
   ```
   📹 Chunk recorded: 45231 bytes (total: 1)
   📤 Uploading chunk 0 (452310 bytes, final: false)...
   ✅ Chunk 0 uploaded successfully
   ```

10. **After interview ends, check files:**
    ```powershell
    dir "media\interview_recordings\*.webm"
    ```

---

## 🔍 Console Diagnostics (Run During Interview)

Copy-paste this into browser console:

```javascript
console.log('=== VIDEO RECORDING STATUS ===');
console.log('1. Class defined:', typeof InterviewVideoRecorder);
console.log('2. Recorder exists:', typeof videoRecorder);
console.log('3. Recorder:', videoRecorder);

if (videoRecorder) {
    console.log('4. Is recording:', videoRecorder.isRecording);
    console.log('5. Session key:', videoRecorder.sessionKey);
    console.log('6. Chunks count:', videoRecorder.recordedChunks?.length || 0);
    console.log('7. Chunk index:', videoRecorder.chunkIndex);
    console.log('8. Media recorder state:', videoRecorder.mediaRecorder?.state);
}

// Test camera permissions
navigator.mediaDevices.getUserMedia({video: true, audio: true})
    .then(() => console.log('9. ✅ Permissions: GRANTED'))
    .catch(err => console.error('9. ❌ Permissions: DENIED -', err.message));

console.log('=== END STATUS ===');
```

**Expected Good Output:**
```
1. Class defined: function
2. Recorder exists: object
3. Recorder: InterviewVideoRecorder {sessionKey: "test123", ...}
4. Is recording: true
5. Session key: test123
6. Chunks count: 3
7. Chunk index: 0
8. Media recorder state: recording
9. ✅ Permissions: GRANTED
```

---

## 🚨 Common Issues & Solutions

### **Issue 1: "Class defined: undefined"**

**Problem:** Script didn't load

**Solution:**
1. Hard refresh: `Ctrl + Shift + R`
2. Clear browser cache
3. Restart Django server
4. Check portal.html has the embedded script (line 610)

---

### **Issue 2: "Recorder exists: undefined"**

**Problem:** Initialization failed

**Look for earlier console error:**
```
❌ Error initializing video recorder: ...
```

**Solution:**
- Check SESSION_KEY is valid
- Restart browser
- Try incognito mode

---

### **Issue 3: "Permissions: DENIED"**

**Problem:** Camera/mic blocked

**Solution:**
1. Click camera icon in address bar
2. Change to "Allow"
3. Refresh page
4. Or go to: `chrome://settings/content/camera`

---

### **Issue 4: Recording starts but no chunks**

**Problem:** MediaRecorder not capturing

**Check:**
```javascript
videoRecorder.mediaRecorder.state
```

Should be: `"recording"`

If `"inactive"`:
→ Recording stopped prematurely
→ Check for errors in console

---

### **Issue 5: Chunks recorded but not uploaded**

**Problem:** Network/server issue

**Check Network tab (F12 → Network):**
- Filter: `/recording/upload_chunk/`
- Look for POST requests
- If RED → Click and check Response tab for error
- If 404 → URL not registered (restart server)
- If 403 → CSRF issue

---

## 💡 Manual Recording Test

If nothing works, test manually:

```javascript
// 1. Create recorder
const recorder = new InterviewVideoRecorder('manual-test');

// 2. Start recording
recorder.startRecording().then(() => {
    console.log('Recording started!');
    
    // 3. Speak for 10 seconds
    
    // 4. Stop after 10 seconds
    setTimeout(() => {
        recorder.stopRecording();
        console.log('Recording stopped! Check media/interview_recordings/');
    }, 10000);
});
```

---

## 📊 Expected File Output

After completing interview, you should have:

### **1. Temporary Chunks (deleted after merge):**
```
media/video_chunks/test123/
├── chunk_0000.webm
├── chunk_0001.webm
└── chunk_0002.webm
```

### **2. Final Recording:**
```
media/interview_recordings/
└── interview_test123_20251121_153045.webm
```

### **3. Database Entry:**
```json
{
  "ai_result": {
    "recording_video": "interview_recordings/interview_test123_20251121_153045.webm",
    "recording_created_at": "2025-11-21T15:30:45"
  }
}
```

---

## 🎯 Action Plan (Do This in Order)

### **Step 1: Test Basic Recording**
→ Open `http://127.0.0.1:8000/static/test_video_recording.html`
→ Follow the 3 buttons
→ **Result:** If this works, your browser/camera is fine

### **Step 2: Test Portal Recording**
→ Start new interview
→ Open console (F12)
→ Look for "🎥 VIDEO RECORDING ENABLED" message
→ **Result:** If you see this, initialization works

### **Step 3: Check Recording Starts**
→ Interview begins
→ Look for "✅ VIDEO RECORDING STARTED!" message
→ Look for red "RECORDING" badge
→ **Result:** If badge appears, recording is active

### **Step 4: Run Diagnostics**
→ Copy-paste diagnostic script (from above)
→ Share the output with me
→ **Result:** I'll tell you exactly what's wrong

### **Step 5: Complete Interview**
→ Answer 1-2 questions
→ Let interview complete
→ Check for video file:
   ```powershell
   dir "media\interview_recordings"
   ```
→ **Result:** File should exist

---

## 📞 Still Not Working?

**Share these with me:**

1. **Console output** from diagnostics script
2. **Any error messages** (red text in console)
3. **Network tab** screenshot (if chunks uploading)
4. **Result of:**
   ```javascript
   videoRecorder
   videoRecorder.isRecording
   videoRecorder.mediaRecorder?.state
   ```

I'll identify the exact problem! 🎯

---

## 🎉 Success Indicators

You'll know it's working when you see:

1. ✅ Console: "🎥 VIDEO RECORDING ENABLED"
2. ✅ Console: "✅ VIDEO RECORDING STARTED!"
3. ✅ Screen: Red "RECORDING" badge (top-right)
4. ✅ Console: "📹 Chunk recorded: ... bytes"
5. ✅ Console: "✅ Chunk uploaded successfully"
6. ✅ File: `media/interview_recordings/interview_*.webm`
7. ✅ Database: `ai_result.recording_video` field populated

**All 7 must be true for complete success!**

