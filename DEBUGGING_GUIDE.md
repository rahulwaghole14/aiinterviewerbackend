# 🔍 Debugging Guide for AI Interview Bot

## Current Status
✅ **Server is running** (HTTP 200 response)  
✅ **Daphne WebSocket server** is running  
✅ **Complete app.py integration** is done  
✅ **Enhanced debugging** is added  

## 🧪 Test Link (NEW)
```
http://127.0.0.1:8000/?session_key=52f2ea4fb9a74f489d173286acce3691
```

## 🔍 What to Look For

### 1. Browser Console (F12) - After ID Verification

**Expected logs:**
```
🚀 Auto-starting chatbot in iframe...
=== STARTING CHATBOT ===
📍 Debug: window.parent exists: true
📍 Debug: window.parent.SESSION_KEY: 52f2ea4fb9a74f489d173286acce3691
📍 Step 1: Got session_key from parent: 52f2ea4fb9a74f489d173286acce3691
📍 Step 2: Calling /ai/start API...
📍 Step 3: Received response: {session_id: "...", question: "...", audio_url: "..."}
✅ Success! Session ID: ...
✅ Question: ...
✅ Audio URL: ...
📍 Step 4: Playing audio...
✅ Audio playing successfully
📍 Step 5: Audio ended, starting recording...
```

**If you see errors:**
- ❌ `No session_key available!` → SESSION_KEY not passed to iframe
- ❌ `Failed to start chatbot:` → Iframe start() function failed
- ❌ `ERROR from /ai/start:` → Backend API error

### 2. Django Terminal - When /ai/start is Called

**Expected logs:**
```
🎯 AI_START called with session_key: 52f2ea4fb9a74f489d173286acce3691
🔍 Retrieved session: <InterviewSession object>
✅ Candidate name: Dhananjay Suhas PAturkar
✅ JD length: 1234 characters
✅ Generated question: Hello Dhananjay! Can you tell me about your experience with...
✅ Generated audio: /media/audio/q1.mp3
```

**If you see errors:**
- ❌ `Session not found` → Database issue
- ❌ `Error generating question` → Gemini API issue
- ❌ `Error generating audio` → Google TTS issue

### 3. WebSocket Connection - When Recording Starts

**Expected logs:**
```
🔌 Deepgram WebSocket consumer connecting... API key present: True
✅ WebSocket connection accepted
📡 Received config from browser: {"sample_rate":48000,"model":"nova-2-meeting","language":"en"}
🔧 Opening Deepgram connection: model=nova-2-meeting, sample_rate=48000
🔗 Connecting to Deepgram at: wss://api.deepgram.com/v2/listen?...
✅ Connected to Deepgram!
✅ Sent start config to Deepgram
📨 Received message #1 from Deepgram
```

## 🚨 Common Issues & Solutions

### Issue 1: "Proctor-only mode; skipping auto-start"
**Cause:** PROCTOR_ONLY flag is set to true  
**Solution:** This is expected behavior - the chatbot should still start via iframe

### Issue 2: "No session_key available!"
**Cause:** SESSION_KEY not accessible from iframe  
**Solution:** Check if SESSION_KEY is set in parent window

### Issue 3: "/ai/start API error"
**Cause:** Backend not responding or database issue  
**Solution:** Check Django terminal for detailed error logs

### Issue 4: "Audio play failed"
**Cause:** Audio file not generated or path issue  
**Solution:** Check if Google TTS is working

### Issue 5: "WebSocket connection failed"
**Cause:** Deepgram API key or network issue  
**Solution:** Check Deepgram API key and network connectivity

## 📋 Testing Checklist

- [ ] Open test link in browser
- [ ] Complete camera verification
- [ ] Complete ID card verification  
- [ ] Open browser console (F12)
- [ ] Look for "🚀 Auto-starting chatbot in iframe..."
- [ ] Look for "=== STARTING CHATBOT ==="
- [ ] Check if SESSION_KEY is retrieved
- [ ] Check if /ai/start API is called
- [ ] Check if question is generated
- [ ] Check if audio plays
- [ ] Check if recording starts
- [ ] Check if WebSocket connects to Deepgram
- [ ] Check if live transcription works

## 🎯 Expected Flow

1. **ID Verification** → Shows "Verification successful!"
2. **Chatbot Auto-Start** → Iframe loads with chatbot UI
3. **API Call** → /ai/start called with session_key
4. **Question Generation** → Gemini generates first question
5. **Audio Generation** → Google TTS creates audio file
6. **Audio Playback** → Question audio plays
7. **Recording Start** → Microphone starts recording
8. **WebSocket Connection** → Connects to Deepgram
9. **Live Transcription** → Real-time speech-to-text
10. **Answer Processing** → After 4-5s silence, processes answer
11. **Next Question** → Generates and plays next question
12. **Repeat** → Continues for 8 questions total

## 📞 If Still Not Working

Please share:
1. **Browser console logs** (copy all colored text)
2. **Django terminal logs** (any new messages)
3. **Screenshot** of the current state
4. **Specific error messages** you see

The system now has complete debugging - we can pinpoint exactly where it's failing!

