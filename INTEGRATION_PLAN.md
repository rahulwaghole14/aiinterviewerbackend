# Complete Integration Plan: app.py → Django

## Current Issues
1. Chatbot UI shows but doesn't start asking questions
2. `/ai/start` endpoint may not be called or returning errors
3. WebSocket connection issues for Deepgram

## Key Differences Between app.py and Our Django Implementation

### 1. Session Management
**app.py:**
- Uses simple in-memory dictionary: `sessions = {}`
- Creates `InterviewSession` object with all state
- Session persists in memory during app lifetime

**Our Django:**
- Uses Django ORM `InterviewSession` model
- Uses `ChatBotManager` with in-memory sessions dict
- Need to sync between Django DB and chatbot manager

### 2. /start Endpoint
**app.py `/start`:**
```python
@app.route("/start", methods=["POST"])
def start_interview():
    data = request.get_json()
    candidate_name = data.get("name", "Candidate")
    jd_text = data.get("jd", "")
    
    # Create new session
    session_id = str(uuid.uuid4())
    session = InterviewSession(session_id, candidate_name, jd_text)
    sessions[session_id] = session
    
    # Generate introduction question
    question = generate_question(session, "introduction")
    session.add_interviewer_message(question)
    session.current_question_number += 1
    
    # Generate audio
    audio_url = text_to_speech(question, f"q{session.current_question_number}.mp3")
    
    return jsonify({
        "session_id": session_id,
        "question": question,
        "audio_url": audio_url,
        "question_number": session.current_question_number,
        "max_questions": session.max_questions
    })
```

**Our Django `/ai/start`:**
- Should work similarly but needs proper session_key handling
- Currently calls `ai_start_django` which calls `chatbot_manager.start`

### 3. Text-to-Speech
**app.py:**
- Uses Google Cloud Text-to-Speech
- Saves to `uploads/` directory
- Returns URL like `/uploads/q1.mp3`

**Our Django:**
- Also uses Google Cloud TTS
- Saves to `media/ai_uploads/`
- Should return proper media URL

### 4. Deepgram WebSocket
**app.py:**
- Uses Flask-Sock: `@sock.route('/dg_ws')`
- Synchronous WebSocket handling
- Receives config, then audio stream

**Our Django:**
- Uses Django Channels
- Has `deepgram_consumer.py` with async handling
- Should work similarly

## What Needs to be Fixed

### Priority 1: Ensure /ai/start Works
1. Add comprehensive debugging
2. Ensure session_key properly retrieves candidate name and JD from DB
3. Ensure JD is not empty or too short
4. Ensure audio file generation works
5. Return proper response format

### Priority 2: Fix Frontend Integration
1. Ensure iframe properly calls parent window SESSION_KEY
2. Ensure `/ai/start` is called with correct parameters
3. Handle response properly and play audio

### Priority 3: WebSocket for Transcription
1. Ensure Deepgram WebSocket proxy works
2. Test with regular Django runserver first
3. If needed, switch to Daphne/Channels

## Immediate Actions

1. **Add detailed console logs in iframe JavaScript**
2. **Verify /ai/start is being called** (check terminal)
3. **Check if question generation works**
4. **Check if TTS audio generation works**
5. **Test step by step**


