# 📨 Complete Guide: Message Processing and Answer Handling Flow

## 🎯 **Overview**

This document explains in detail how messages are processed from Deepgram API, how answers are handled, and how the system generates responses.

---

## 🔄 **COMPLETE FLOW DIAGRAM**

```
[User Speaks]
    ↓
[Microphone Captures Audio]
    ↓
[Audio Sent to Deepgram WebSocket]
    ↓
[Deepgram Processes Audio]
    ↓
[Deepgram Sends Messages (Interim/Final)]
    ↓
[handleDeepgramMessage() Processes Message]
    ↓
[Transcript Accumulated & Displayed]
    ↓
[User Clicks "Done" or Time Expires]
    ↓
[moveToReviewPhase() Called]
    ↓
[sendAudioToServer() Submits Answer]
    ↓
[Backend: transcribe_audio() or ai_upload_answer()]
    ↓
[Backend: upload_answer() Processes Answer]
    ↓
[LLM Generates Next Question/Response]
    ↓
[Response Sent Back to Frontend]
    ↓
[Next Question Displayed]
```

---

## 📥 **PHASE 1: DEEPGRAM MESSAGE RECEPTION**

### **1.1 WebSocket Connection**

**Location:** `portal.html` - `connectDeepgram()` function

```javascript
deepgramWS.onmessage = (event) => {
    handleDeepgramMessage(event);  // Process incoming message
};
```

**What Happens:**
- Deepgram WebSocket receives audio chunks continuously
- Deepgram processes audio and sends JSON messages
- Messages contain either **interim** (partial) or **final** (complete) transcripts

### **1.2 Message Structure**

**Deepgram Message Format:**
```json
{
    "type": "Results",
    "channel": {
        "alternatives": [{
            "transcript": "Hello my name is",
            "confidence": 0.95
        }]
    },
    "is_final": false  // or true for final results
}
```

---

## 🔍 **PHASE 2: MESSAGE PROCESSING (`handleDeepgramMessage`)**

### **2.1 Function Location**

**File:** `portal.html`  
**Function:** `handleDeepgramMessage(event)` (Line 1778)

### **2.2 Step-by-Step Processing**

#### **Step 1: Parse Message**
```javascript
const data = JSON.parse(event.data);
const result = data.channel.alternatives[0];
const transcript = result.transcript || '';
const isFinal = !!data.is_final;
```

**What Happens:**
- Extracts transcript text from Deepgram message
- Determines if it's final (`is_final: true`) or interim (`is_final: false`)

#### **Step 2: Check for Valid Transcript**
```javascript
if (transcript.trim()) {
    lastUpdateTime = Date.now();
    hasEverReceivedText = true;
    
    // Auto-start answering phase if first transcript
    if (!hasStartedSpeaking && transcript.trim().length > 0) {
        startAnsweringPhase();
    }
}
```

**What Happens:**
- Updates last activity timestamp
- Marks that text has been received
- Automatically starts answering phase on first transcript

#### **Step 3A: Handle FINAL Transcript**
```javascript
if (isFinal) {
    console.log(`✅ FINAL: "${transcript}"`);
    
    // Append to accumulated (never replace)
    if (!accumulatedTranscript.includes(transcript)) {
        accumulatedTranscript = accumulatedTranscript 
            ? `${accumulatedTranscript} ${transcript}`.trim()
            : transcript;
    }
    
    // Sync all variables
    syncTranscriptVariables();
    
    // Update display
    updateDisplay(accumulatedTranscript);
}
```

**What Happens:**
- Final transcript is **appended** to `accumulatedTranscript`
- Duplicate detection prevents adding same text twice
- All legacy variables are synced
- UI is updated with complete transcript

**Key Points:**
- Final transcripts are **permanent** (saved to `accumulatedTranscript`)
- Never replaces existing text, only appends
- Triggers after 10 seconds of silence (based on `endpointing: 10000`)

#### **Step 3B: Handle INTERIM Transcript**
```javascript
else {
    console.log(`📝 INTERIM: "${transcript}"`);
    
    // Display: accumulated + new interim (without duplicating)
    const displayText = accumulatedTranscript
        ? `${accumulatedTranscript} ${transcript}`.trim()
        : transcript;
    
    // Store current interim for display
    currentUtterance = transcript;
    
    // Sync variables
    syncTranscriptVariables();
    
    // Update display with combined text
    updateDisplay(displayText);
    return; // Don't update accumulated yet (wait for final)
}
```

**What Happens:**
- Interim transcript is **displayed** but not saved to `accumulatedTranscript`
- Shows: `accumulatedTranscript + currentUtterance`
- `currentUtterance` is temporary (only for display)
- UI updates in real-time as user speaks

**Key Points:**
- Interim transcripts are **temporary** (not saved yet)
- Displayed for real-time feedback
- Replaced by final transcript when available

#### **Step 4: Handle Empty Transcript**
```javascript
// ✅ CRITICAL: Empty transcript = do nothing (preserve existing)
if (!transcript.trim()) {
    // Do nothing - preserve existing transcript
    // This prevents erasure during pauses
}
```

**What Happens:**
- Empty transcripts are **ignored**
- Existing transcript is **preserved**
- No UI update occurs (prevents flickering)

---

## 📤 **PHASE 3: ANSWER SUBMISSION (`sendAudioToServer`)**

### **3.1 Function Location**

**File:** `portal.html`  
**Function:** `sendAudioToServer()` (Line 1924)

### **3.2 Trigger Points**

**When `sendAudioToServer()` is called:**
1. User clicks "Done" button
2. Answering time expires (60 seconds)
3. `moveToReviewPhase()` is called

### **3.3 Step-by-Step Submission**

#### **Step 1: Prepare FormData**
```javascript
const fd = new FormData();
fd.append('session_id', INTERVIEW_SESSION_ID);
fd.append('question_id', currentQuestion.id);
fd.append('response_time', responseTime);
```

**What Happens:**
- Creates FormData object
- Adds session ID, question ID, and response time
- Prepares data for backend submission

#### **Step 2: Get Full Transcript**
```javascript
let answerText = getFullTranscript();  // Returns accumulatedTranscript

if (!answerText.trim()) {
    console.log('⏳ Waiting for final transcript...');
    await new Promise(resolve => setTimeout(resolve, 1000));
    answerText = getFullTranscript();
}
```

**What Happens:**
- Gets complete transcript from `accumulatedTranscript`
- Waits 1 second if no transcript (allows Deepgram to finalize)
- Checks again after wait

#### **Step 3: Handle Empty Transcript**
```javascript
if (!answerText.trim()) {
    answerText = 'No speech was detected.';
    console.log('⚠️ No transcript available after wait');
}
```

**What Happens:**
- If still no transcript after wait, uses fallback message
- This ensures backend always receives something

#### **Step 4: Add Transcript to FormData**
```javascript
fd.append('transcript', answerText);
fd.append('transcribed_answer', answerText);
```

**What Happens:**
- Adds transcript to FormData
- Both `transcript` and `transcribed_answer` fields are set

#### **Step 5: Update UI**
```javascript
const transcriptText = answerText
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/&/g, '&amp;');
box.innerHTML = `<span class='status-indicator status-success'></span><strong>Your Answer:</strong> <span style="color: var(--text-primary) !important;">${transcriptText}</span>`;
```

**What Happens:**
- Escapes HTML to prevent XSS
- Displays final transcript in UI
- Shows success indicator

#### **Step 6: Send to Backend**
```javascript
const res = await fetch("{% url 'transcribe_audio' %}", { 
    method: 'POST', 
    body: fd 
});
const result = await res.json();
```

**What Happens:**
- Sends POST request to `/transcribe_audio/` endpoint
- Waits for response
- Parses JSON response

#### **Step 7: Handle Response**
```javascript
if (result.follow_up_question) {
    spokenQuestions.splice(currentSpokenQuestionIndex + 1, 0, result.follow_up_question);
}
```

**What Happens:**
- If backend returns follow-up question, adds it to question list
- Inserts it after current question

---

## 🖥️ **PHASE 4: BACKEND PROCESSING**

### **4.1 Endpoint: `transcribe_audio`**

**File:** `views.py`  
**Function:** `transcribe_audio(request)` (Line 2235)

#### **Step 1: Extract Data**
```python
session_id = request.POST.get('session_id')
question_id = request.POST.get('question_id')
transcribed_text = request.POST.get('transcript') or request.POST.get('transcribed_answer')
response_time = request.POST.get('response_time')
```

**What Happens:**
- Extracts session ID, question ID, transcript, and response time
- Gets transcript from either `transcript` or `transcribed_answer` field

#### **Step 2: Save to Database**
```python
question_to_update = InterviewQuestion.objects.get(id=question_id, session_id=session_id)
answer_text = transcribed_text.strip()
if not answer_text.startswith('A:'):
    answer_text = f'A: {answer_text}'

question_to_update.transcribed_answer = answer_text
question_to_update.response_time_seconds = float(response_time)
question_to_update.save()
```

**What Happens:**
- Finds the question in database
- Formats answer with "A:" prefix if needed
- Saves transcript and response time
- Updates database record

#### **Step 3: Generate Follow-up (if applicable)**
```python
if transcribed_text and transcribed_text.strip() and question_to_update.question_level == 'MAIN':
    follow_up_data = generate_and_save_follow_up(
        session=question_to_update.session,
        parent_question=question_to_update,
        transcribed_answer=transcribed_text
    )
```

**What Happens:**
- If question is MAIN level, generates follow-up question
- Uses LLM to create follow-up based on answer
- Saves follow-up to database

#### **Step 4: Return Response**
```python
return JsonResponse({
    'text': transcribed_text, 
    'follow_up_question': follow_up_data
})
```

**What Happens:**
- Returns JSON response with transcript
- Includes follow-up question if generated

### **4.2 Endpoint: `ai_upload_answer` (Alternative)**

**File:** `views.py`  
**Function:** `ai_upload_answer(request)` (Line 2940)

#### **Step 1: Extract Data**
```python
session_id = request.POST.get('session_id')
transcript = request.POST.get('transcript', '').strip()
silence_flag = request.POST.get('silence_flag', 'false').lower() == 'true'
had_voice_flag = request.POST.get('had_voice_flag', 'false').lower() == 'true'
```

**What Happens:**
- Extracts session ID and transcript
- Gets silence and voice flags from frontend

#### **Step 2: Call AI Bot**
```python
from .complete_ai_bot import upload_answer

result = upload_answer(
    session_id=session_id,
    transcript=transcript,
    silence_flag=silence_flag,
    had_voice_flag=had_voice_flag
)
```

**What Happens:**
- Calls `upload_answer()` function from `complete_ai_bot.py`
- Passes transcript and flags
- Gets AI-generated response

#### **Step 3: Save to Database**
```python
# Save AI question and interviewee answer to database
# Creates InterviewQuestion records with role='AI' and role='INTERVIEWEE'
```

**What Happens:**
- Saves AI questions with `role='AI'` and `conversation_sequence` (odd numbers)
- Saves interviewee answers with `role='INTERVIEWEE'` and `conversation_sequence` (even numbers)
- Maintains sequential conversation flow

#### **Step 4: Return Response**
```python
return JsonResponse(result)
```

**What Happens:**
- Returns AI-generated response
- Includes next question, audio URL, completion status, etc.

---

## 🤖 **PHASE 5: AI PROCESSING (`upload_answer`)**

### **5.1 Function Location**

**File:** `complete_ai_bot.py`  
**Function:** `upload_answer(session_id, transcript, silence_flag, had_voice_flag)` (Line 1070)

### **5.2 Step-by-Step Processing**

#### **Step 1: Validate Session**
```python
if not session_id or session_id not in sessions:
    return {"error": "Invalid session ID"}

session = sessions[session_id]

if session.is_completed:
    return {"completed": True, "message": "Interview completed"}
```

**What Happens:**
- Validates session ID exists
- Checks if interview is already completed
- Returns error if invalid

#### **Step 2: Process Transcript**
```python
transcript = (transcript or "").strip()
session.add_candidate_message(transcript if transcript else "")

if transcript.strip() and not transcript.startswith("["):
    session.awaiting_answer = False
```

**What Happens:**
- Keeps transcript as-is (empty if no speech)
- Adds to conversation history
- Marks that answer was received

#### **Step 3: Check for Empty Transcript**
```python
is_empty_transcript = not transcript.strip() or transcript.startswith("[No speech detected")

if is_empty_transcript:
    # Send empty transcript to LLM to generate appropriate response
    llm_prompt = (
        f"You are a professional technical interviewer..."
        f"The candidate's response was empty or not detected..."
        f"Generate a brief, professional response..."
    )
    
    llm_response = gemini_generate(llm_prompt, max_retries=3)
```

**What Happens:**
- Detects empty transcript
- Sends to LLM with full context
- LLM decides: ask again or move to next question

#### **Step 4: Handle LLM Decision**
```python
move_to_next = any(phrase in llm_response.lower() for phrase in [
    "next question", "move on", "let's continue", "proceed"
])

if move_to_next:
    # Generate next question
    next_question = generate_question(session, "regular", last_answer_text="")
    session.current_question_number += 1
    return {
        "next_question": f"{llm_response} {next_question}",
        "audio_url": text_to_speech(...),
        "question_number": session.current_question_number
    }
else:
    # Ask again
    return {
        "acknowledge": True,
        "message": llm_response,
        "audio_url": text_to_speech(...)
    }
```

**What Happens:**
- Checks if LLM wants to move to next question
- If yes: generates next question and increments counter
- If no: returns acknowledgment to ask again

#### **Step 5: Process Valid Transcript**
```python
# Check for repeat requests
is_repeat = is_repeat_request_via_llm(session, transcript, last_question)

if is_repeat:
    # Generate repeat response
    repeat_response = generate_repeat_question_response(session, last_question)
    return {"next_question": repeat_response, ...}

# Check for skip commands
if any(phrase in transcript_lower for phrase in ["skip", "next question"]):
    # Generate next question
    next_question = generate_question(session, "regular", last_answer_text=transcript)
    return {"next_question": next_question, ...}

# Normal answer processing
# Generate next question based on answer
should_follow_up = should_ask_follow_up(session, transcript)
if should_follow_up:
    next_question = generate_question(session, "follow_up", last_answer_text=transcript)
else:
    next_question = generate_question(session, "regular", last_answer_text=transcript)
```

**What Happens:**
- Checks for repeat requests (using LLM)
- Checks for skip commands
- Decides if follow-up is needed
- Generates appropriate next question

#### **Step 6: Generate Response**
```python
session.add_interviewer_message(next_question)
session.current_question_number += 1
session.awaiting_answer = True
session.last_active_question_text = next_question

audio_url = text_to_speech(next_question, f"q{session.current_question_number}.mp3")

return {
    "transcript": transcript,
    "completed": False,
    "next_question": next_question,
    "audio_url": audio_url,
    "question_number": session.current_question_number,
    "max_questions": session.max_questions,
    "continuous": True
}
```

**What Happens:**
- Adds question to conversation history
- Increments question number
- Generates TTS audio for question
- Returns complete response to frontend

---

## 📊 **DATA FLOW SUMMARY**

### **Frontend → Backend**

```
1. User speaks → Deepgram captures audio
2. Deepgram sends messages → handleDeepgramMessage() processes
3. Transcript accumulated → accumulatedTranscript updated
4. User clicks "Done" → sendAudioToServer() called
5. FormData created → Contains: session_id, question_id, transcript, response_time
6. POST to /transcribe_audio/ → Backend receives data
7. Backend saves to database → InterviewQuestion.transcribed_answer updated
8. Backend generates follow-up (if needed) → LLM creates follow-up question
9. Backend returns response → JSON with transcript and follow-up
```

### **Backend → Frontend**

```
1. Backend processes answer → upload_answer() called
2. LLM analyzes answer → Generates next question or acknowledgment
3. TTS audio generated → Google Cloud TTS creates audio file
4. Response created → Contains: next_question, audio_url, question_number
5. JSON response sent → Frontend receives data
6. Frontend displays question → Shows next question text
7. Frontend plays audio → Plays TTS audio of question
8. Cycle repeats → User answers next question
```

---

## 🔑 **KEY FUNCTIONS AND THEIR ROLES**

| Function | Location | Purpose |
|----------|----------|---------|
| **`handleDeepgramMessage()`** | `portal.html:1778` | Processes Deepgram WebSocket messages, accumulates transcripts |
| **`updateDisplay()`** | `portal.html:1843` | Updates UI with transcript text (HTML escaped) |
| **`getFullTranscript()`** | `portal.html:717` | Returns complete accumulated transcript |
| **`sendAudioToServer()`** | `portal.html:1924` | Submits answer to backend, handles response |
| **`moveToReviewPhase()`** | `portal.html:1548` | Moves from answering to review phase, triggers submission |
| **`transcribe_audio()`** | `views.py:2235` | Backend endpoint: saves transcript, generates follow-up |
| **`ai_upload_answer()`** | `views.py:2940` | Backend endpoint: processes answer via AI bot |
| **`upload_answer()`** | `complete_ai_bot.py:1070` | AI bot: analyzes answer, generates next question |

---

## 📋 **MESSAGE TYPES**

### **1. Interim Messages (Real-time)**
- **Type:** `is_final: false`
- **Purpose:** Show live transcription as user speaks
- **Handling:** Displayed but not saved to `accumulatedTranscript`
- **Frequency:** Multiple per second as user speaks

### **2. Final Messages (Complete)**
- **Type:** `is_final: true`
- **Purpose:** Mark utterance as complete
- **Handling:** Appended to `accumulatedTranscript` permanently
- **Frequency:** After 10 seconds of silence (based on `endpointing: 10000`)

### **3. Empty Messages**
- **Type:** `transcript: ""` or empty
- **Purpose:** Indicate pause or silence
- **Handling:** Ignored, existing transcript preserved
- **Frequency:** During pauses in speech

---

## 🎯 **ANSWER PROCESSING DECISIONS**

### **Decision Tree:**

```
Empty Transcript?
    ├─ YES → Send to LLM
    │   ├─ LLM decides: Ask again → Return acknowledgment
    │   └─ LLM decides: Move on → Generate next question
    │
    └─ NO → Process transcript
        ├─ Repeat request? → Generate repeat response
        ├─ Skip command? → Generate next question
        ├─ Valid answer? → Analyze answer
        │   ├─ Needs follow-up? → Generate follow-up question
        │   └─ No follow-up? → Generate regular question
        └─ Closing phase? → Handle closing Q&A
```

---

## ⚙️ **STATE MANAGEMENT**

### **Frontend State Variables:**

```javascript
accumulatedTranscript = '';  // All finalized text (permanent)
currentUtterance = '';       // Current interim (temporary)
lastUpdateTime = Date.now(); // Last activity timestamp
hasEverReceivedText = false; // Whether any text received
isRecordingActive = false;   // Recording state
```

### **Backend State Variables:**

```python
session.awaiting_answer = True/False
session.current_question_number = 1, 2, 3...
session.last_active_question_text = "..."
session.conversation_history = [...]
```

---

## 🔄 **COMPLETE EXAMPLE FLOW**

### **Scenario: User Answers "What is machine learning?"**

```
1. [0ms] User starts speaking: "Machine learning is..."
   → Deepgram sends INTERIM: "Machine learning is"
   → handleDeepgramMessage() receives message
   → currentUtterance = "Machine learning is"
   → Display: "Machine learning is" (interim)

2. [500ms] User continues: "Machine learning is a subset..."
   → Deepgram sends INTERIM: "Machine learning is a subset"
   → currentUtterance = "Machine learning is a subset"
   → Display: "Machine learning is a subset" (interim)

3. [2000ms] User pauses (thinking)
   → Deepgram sends INTERIM: "Machine learning is a subset" (same)
   → Display: "Machine learning is a subset" (preserved)

4. [3000ms] User continues: "Machine learning is a subset of artificial intelligence"
   → Deepgram sends INTERIM: "Machine learning is a subset of artificial intelligence"
   → currentUtterance = "Machine learning is a subset of artificial intelligence"
   → Display: "Machine learning is a subset of artificial intelligence" (interim)

5. [5000ms] User stops speaking
   → [15000ms] 10 seconds of silence passes
   → Deepgram sends FINAL: "Machine learning is a subset of artificial intelligence"
   → accumulatedTranscript = "Machine learning is a subset of artificial intelligence"
   → currentUtterance = '' (cleared)
   → Display: "Machine learning is a subset of artificial intelligence" (final)

6. [16000ms] User clicks "Done" button
   → moveToReviewPhase() called
   → stopRecordingAndProcessing() called
   → sendAudioToServer() called
   → answerText = "Machine learning is a subset of artificial intelligence"
   → POST to /transcribe_audio/ with transcript

7. [16050ms] Backend receives request
   → transcribe_audio() extracts data
   → Saves to InterviewQuestion.transcribed_answer
   → Generates follow-up question (if MAIN question)
   → Returns JSON response

8. [16100ms] Frontend receives response
   → Displays follow-up question (if any)
   → Starts review timer
   → After 10 seconds, moves to next question
```

---

## 📝 **KEY POINTS TO REMEMBER**

1. **Interim transcripts are temporary** - Only displayed, not saved
2. **Final transcripts are permanent** - Saved to `accumulatedTranscript`
3. **Empty transcripts are ignored** - Existing transcript preserved
4. **Submission waits 1 second** - Allows Deepgram to finalize
5. **Backend processes empty transcripts** - Sends to LLM for decision
6. **LLM decides next action** - Ask again or move to next question
7. **All transcripts preserved** - Never erased during recording
8. **Sequential conversation flow** - AI and Interviewee messages tracked separately

---

## 🔧 **TROUBLESHOOTING**

### **Issue: Transcript not appearing**
- Check: `handleDeepgramMessage()` is receiving messages
- Check: `isFinal` flag is being processed correctly
- Check: `updateDisplay()` is being called

### **Issue: Transcript lost during submission**
- Check: `getFullTranscript()` returns `accumulatedTranscript`
- Check: Wait time (1 second) is sufficient
- Check: `accumulatedTranscript` is not being cleared

### **Issue: Backend not receiving transcript**
- Check: `sendAudioToServer()` is creating FormData correctly
- Check: Network request is successful
- Check: Backend endpoint is accessible

### **Issue: LLM not generating response**
- Check: Empty transcript is being sent correctly
- Check: LLM prompt includes all necessary context
- Check: Gemini API is accessible and has quota

---

This completes the detailed explanation of message processing and answer handling flow.

