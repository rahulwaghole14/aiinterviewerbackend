# Question and Answer Storage & Display - Complete Flow Documentation

## Overview
This document provides a comprehensive explanation of how AI questions and candidate answers are stored in the database and displayed in the Candidate Details UI.

---

## 📊 Database Structure

### 1. Primary Model: `InterviewQuestion`

**Location**: `interview_app/models.py`

**Key Fields**:
```python
class InterviewQuestion(models.Model):
    session = models.ForeignKey(InterviewSession, related_name='questions', on_delete=models.CASCADE)
    question_text = models.TextField()  # Stores AI question text
    question_type = models.CharField(max_length=50)  # TECHNICAL, BEHAVIAL, CODING
    transcribed_answer = models.TextField(null=True, blank=True)  # Stores candidate answer
    order = models.PositiveIntegerField()  # Order in interview (0, 1, 2, 3...)
    question_level = models.CharField(max_length=30)  # MAIN, INTERVIEWEE_RESPONSE, CANDIDATE_QUESTION, AI_RESPONSE
    conversation_sequence = models.PositiveIntegerField(null=True, blank=True)  # Sequential index (1, 2, 3, 4...)
    role = models.CharField(max_length=20)  # 'AI' or 'INTERVIEWEE'
    response_time_seconds = models.FloatField(null=True, blank=True)
    words_per_minute = models.IntegerField(null=True, blank=True)
    filler_word_count = models.IntegerField(null=True, blank=True)
```

**Storage Pattern**:
- **AI Questions**: `role='AI'`, `question_level='MAIN'`, `question_text` = question, `transcribed_answer` = empty or backward compatibility
- **Candidate Answers**: `role='INTERVIEWEE'`, `question_level='INTERVIEWEE_RESPONSE'`, `question_text` = empty, `transcribed_answer` = answer
- **Candidate Questions**: `role='INTERVIEWEE'`, `question_level='CANDIDATE_QUESTION'`, `question_text` = empty, `transcribed_answer` = candidate's question
- **AI Responses to Candidate**: `role='AI'`, `question_level='AI_RESPONSE'`, `question_text` = AI's response, `transcribed_answer` = empty

---

## 🔄 Storage Flow

### Step 1: AI Question Generation

**Location**: `interview_app/complete_ai_bot.py` - `upload_answer()` function

**Process**:
1. AI generates question using Gemini API
2. Question is stored in memory session: `session.last_active_question_text = question`
3. Question is added to conversation history: `session.add_interviewer_message(question)`

**Example**:
```python
# In complete_ai_bot.py
next_question = generate_question(session, "regular", last_answer_text=transcript)
session.add_interviewer_message(next_question)
session.last_active_question_text = next_question
```

---

### Step 2: Saving AI Question to Database

**Location**: `interview_app/views.py` - `ai_upload_answer()` function

**Process**:
1. After `upload_answer()` returns, the result contains `next_question`
2. Question is saved to `InterviewQuestion` table with:
   - `role='AI'`
   - `question_level='MAIN'`
   - `question_text` = question text (cleaned, no "Q:" prefix)
   - `conversation_sequence` = odd number (1, 3, 5, 7...)
   - `order` = sequential order (0, 1, 2, 3...)

**Code Flow**:
```python
# In ai_upload_answer() after upload_answer() returns
if next_question_text and next_question_text.strip():
    # Check if question already exists (prevent duplicates)
    question_exists = InterviewQuestion.objects.filter(
        session=django_session,
        question_text__iexact=next_question_text.strip()
    ).exists()
    
    if not question_exists:
        # Calculate conversation_sequence (odd number for AI)
        max_seq = InterviewQuestion.objects.filter(
            session=django_session
        ).aggregate(max_seq=Max('conversation_sequence'))['max_seq'] or 0
        
        if max_seq % 2 == 0 and max_seq > 0:
            ai_sequence = max_seq + 1  # Last was Interviewee (even), next is AI (odd)
        else:
            ai_sequence = ((max_seq // 2) + 1) * 2 + 1  # Calculate next odd number
        
        # Create AI question record
        InterviewQuestion.objects.create(
            session=django_session,
            question_text=question_text_formatted,
            question_type='TECHNICAL',
            order=new_order,
            question_level='MAIN',
            role='AI',
            conversation_sequence=ai_sequence  # 1, 3, 5, 7...
        )
```

**Sequence Logic**:
- **First AI Question**: sequence = 1
- **Subsequent AI Questions**: If last sequence was even (Interviewee), next is odd (AI) = last + 1
- **If last was AI (odd)**: Calculate next odd = ((last // 2) + 1) * 2 + 1

---

### Step 3: Candidate Provides Answer

**Location**: Frontend sends transcript to `/interview_app/ai/upload_answer`

**Process**:
1. Frontend captures audio via microphone
2. Audio is transcribed using Deepgram API
3. Transcript is sent to backend: `POST /interview_app/ai/upload_answer`
4. Backend receives transcript in `ai_upload_answer()` function

---

### Step 4: Saving Candidate Answer to Database

**Location**: `interview_app/views.py` - `ai_upload_answer()` function

**Process**:
1. Find the question being answered (matches `last_active_question_text`)
2. Create separate `InterviewQuestion` record for answer with:
   - `role='INTERVIEWEE'`
   - `question_level='INTERVIEWEE_RESPONSE'`
   - `question_text` = empty
   - `transcribed_answer` = answer text (cleaned, no "A:" prefix)
   - `conversation_sequence` = even number (2, 4, 6, 8...)
   - `order` = same as the question it answers

**Code Flow**:
```python
# In ai_upload_answer() when saving answer
if question_obj:
    # Calculate conversation_sequence (even number for Interviewee)
    max_seq = InterviewQuestion.objects.filter(
        session=django_session
    ).aggregate(max_seq=Max('conversation_sequence'))['max_seq'] or 0
    
    if max_seq % 2 == 1:  # Last was AI (odd), next is Interviewee (even)
        interviewee_sequence = max_seq + 1
    else:  # Last was Interviewee or no sequence, find next even
        interviewee_sequence = ((max_seq // 2) + 1) * 2
    
    # Format answer text
    answer_text_formatted = answer_text.strip()
    if answer_text_formatted.startswith('A:'):
        answer_text_formatted = answer_text_formatted.replace('A:', '').strip()
    
    # Create separate record for Interviewee answer
    InterviewQuestion.objects.create(
        session=django_session,
        question_text='',  # Empty for Interviewee responses
        question_type=question_obj.question_type,
        order=question_obj.order,  # Same order as the question
        question_level='INTERVIEWEE_RESPONSE',
        transcribed_answer=answer_text_formatted,  # The actual answer
        response_time_seconds=response_time,
        role='INTERVIEWEE',
        conversation_sequence=interviewee_sequence  # 2, 4, 6, 8...
    )
    
    # Also update original question's transcribed_answer for backward compatibility
    question_obj.transcribed_answer = f'A: {answer_text_formatted}'
    question_obj.save(update_fields=['transcribed_answer', 'response_time_seconds'])
```

**Important Notes**:
- **ALWAYS saves answers**: Even if transcript is empty, saves "No answer provided"
- **Duplicate prevention**: Checks if answer already exists before creating
- **Backward compatibility**: Also updates original question's `transcribed_answer` field

---

## 📋 Sequence Example

### Complete Conversation Flow:

```
Sequence 1: AI Question 1 (order: 0, role: AI, question_level: MAIN)
  └─> question_text: "Can you tell me about yourself?"
  └─> transcribed_answer: empty (or backward compatibility)

Sequence 2: Candidate Answer 1 (order: 0, role: INTERVIEWEE, question_level: INTERVIEWEE_RESPONSE)
  └─> question_text: empty
  └─> transcribed_answer: "I am a software developer with 5 years of experience..."

Sequence 3: AI Question 2 (order: 1, role: AI, question_level: MAIN)
  └─> question_text: "What is your experience with Python?"
  └─> transcribed_answer: empty

Sequence 4: Candidate Answer 2 (order: 1, role: INTERVIEWEE, question_level: INTERVIEWEE_RESPONSE)
  └─> question_text: empty
  └─> transcribed_answer: "I have been using Python for 3 years..."

Sequence 5: AI Question 3 (order: 2, role: AI, question_level: MAIN)
  └─> question_text: "Do you have any questions for us?"
  └─> transcribed_answer: empty

Sequence 6: Candidate Answer 3 (order: 2, role: INTERVIEWEE, question_level: INTERVIEWEE_RESPONSE)
  └─> question_text: empty
  └─> transcribed_answer: "Yes, what is the team structure?"
```

---

## 🔍 Data Retrieval for UI

### Step 1: API Endpoint

**Endpoint**: `GET /api/interviews/`

**Location**: `interviews/views.py` - Uses `InterviewSerializer`

**Response Format**:
```json
{
  "id": "uuid",
  "candidate_name": "John Doe",
  "questions_and_answers": [
    {
      "question_number": 1,
      "question": "Can you tell me about yourself?",
      "answer": "I am a software developer...",
      "question_type": "TECHNICAL",
      "response_time": 15.5,
      "order": 0
    },
    ...
  ]
}
```

---

### Step 2: Serializer Logic

**Location**: `interviews/serializers.py` - `get_questions_and_answers()` method

**Process**:

#### 2.1 Find Interview Session
```python
# Find session by session_key
session = InterviewSession.objects.get(session_key=obj.session_key)

# Fallback: Find by candidate email and date proximity
if not session:
    sessions = InterviewSession.objects.filter(
        candidate_email=obj.candidate.email
    ).filter(
        created_at__gte=time_window_start,
        created_at__lte=time_window_end
    )
    session = sessions.first()
```

#### 2.2 Fetch All Questions and Answers
```python
# Get all conversation items ordered by conversation_sequence
questions = InterviewQuestion.objects.filter(
    session=session
).order_by(
    'conversation_sequence',  # Primary sort
    'order',  # Secondary sort
    'id'  # Tertiary sort
)
```

#### 2.3 Pair Questions with Answers
```python
# Group questions by order (composite key: order, conversation_sequence)
questions_by_order = {}

for q in questions:
    # Skip CODING questions (handled separately)
    if q.question_type == 'CODING':
        coding_questions_list.append(q)
        continue
    
    # Group by composite key (order, sequence)
    composite_key = (q.order, q.conversation_sequence or -1)
    
    if composite_key not in questions_by_order:
        questions_by_order[composite_key] = {
            'ai': None,
            'interviewee': None,
            'conversation_sequence': q.conversation_sequence,
            'order': q.order
        }
    
    # Assign to AI or Interviewee based on role
    if q.role == 'AI' and q.question_text:
        questions_by_order[composite_key]['ai'] = q
    elif q.role == 'INTERVIEWEE' and q.transcribed_answer:
        questions_by_order[composite_key]['interviewee'] = q
```

#### 2.4 Create Q&A Pairs
```python
# Sort by conversation_sequence, then order
sorted_order_keys = sorted(
    questions_by_order.keys(),
    key=lambda k: (
        questions_by_order[k].get('conversation_sequence') or 999999,
        questions_by_order[k].get('order', 0)
    )
)

# Create Q&A pairs
for composite_key in sorted_order_keys:
    q_pair = questions_by_order[composite_key]
    ai_q = q_pair['ai']
    interviewee_a = q_pair['interviewee']
    
    if ai_q:
        qa_item = {
            'question_number': ai_q.order + 1,
            'question': ai_q.question_text or '',
            'answer': interviewee_a.transcribed_answer if interviewee_a else 'No answer provided',
            'question_type': ai_q.question_type or 'TECHNICAL',
            'response_time': interviewee_a.response_time_seconds if interviewee_a else 0,
            'order': ai_q.order
        }
        qa_list.append(qa_item)
```

#### 2.5 Handle Coding Questions Separately
```python
# For CODING questions, get answer from CodeSubmission table
for coding_q in coding_questions_list:
    code_submission = CodeSubmission.objects.filter(
        session=session,
        question_id=str(coding_q.id)
    ).order_by('-created_at').first()
    
    qa_item = {
        'question_number': coding_q.order + 1,
        'question': coding_q.question_text or '',
        'answer': code_submission.submitted_code if code_submission else 'No code submitted',
        'question_type': 'CODING',
        'code_submission': {
            'submitted_code': code_submission.submitted_code,
            'language': code_submission.language,
            'passed_all_tests': code_submission.passed_all_tests,
            ...
        }
    }
    qa_list.append(qa_item)
```

#### 2.6 Sort and Return
```python
# Sort by order/question_number
qa_list.sort(key=lambda x: x.get('order', x.get('question_number', 0)))

return qa_list
```

---

## 🖥️ Frontend Display

### Step 1: Fetching Data

**Location**: `frontend/src/components/CandidateDetails.jsx`

**Process**:
```javascript
// Fetch interviews
const fetchInterviews = async () => {
  const interviewsResponse = await fetch(`${baseURL}/api/interviews/`, {
    method: "GET",
    headers: {
      Authorization: `Token ${authToken}`,
      "Content-Type": "application/json",
    },
  });
  
  const interviewsData = await interviewsResponse.json();
  // Process and filter by candidate
  const candidateInterviews = interviewsData.filter(
    (interview) => interview.candidate === candidate.id
  );
  
  setInterviews(candidateInterviews);
};
```

---

### Step 2: Processing Q&A Data

**Location**: `frontend/src/components/CandidateDetails.jsx`

**Process**:
```javascript
// Sort Q&A pairs by order/conversation_sequence
const sortQAPairs = (qaData) => {
  return qaData.sort((a, b) => {
    // Sort by conversation_sequence first (if available)
    const seqA = a.conversation_sequence ?? 999999;
    const seqB = b.conversation_sequence ?? 999999;
    if (seqA !== seqB) return seqA - seqB;
    
    // Fallback to order
    const orderA = a.order ?? 9999;
    const orderB = b.order ?? 9999;
    if (orderA !== orderB) return orderA - orderB;
    
    // Final fallback to id
    return (a.id || '').localeCompare(b.id || '');
  });
};

// Group by type
const qaData = sortQAPairs(interview.questions_and_answers || []);
const codingQuestions = qaData.filter(
  (qa) => (qa.question_type || '').toUpperCase() === 'CODING'
);
const technicalQuestions = qaData.filter(
  (qa) => (qa.question_type || '').toUpperCase() !== 'CODING'
);
```

---

### Step 3: Rendering in UI

**Location**: `frontend/src/components/CandidateDetails.jsx`

**Display Format**:

#### Technical Questions (Sequential Script Format):
```jsx
<div className="qa-section-below-interview">
  <h4>Questions & Answers - Round {interview.interview_round}</h4>
  
  {/* Technical Questions */}
  <div className="qa-section-divider">
    <h5>Technical Questions</h5>
  </div>
  
  <div style={{ backgroundColor: '#f9f9f9', padding: '20px' }}>
    {technicalQuestions.map((qa, index) => (
      <div key={qa.id || `tech-${index}`}>
        <div style={{ fontWeight: '600', color: '#2196F3' }}>
          Interviewer:
        </div>
        <div style={{ paddingLeft: '15px' }}>
          {qa.question || qa.question_text}
        </div>
        
        <div style={{ fontWeight: '600', color: '#4CAF50' }}>
          Candidate:
        </div>
        <div style={{ paddingLeft: '15px' }}>
          {qa.answer || 'No answer provided'}
        </div>
        
        {index < technicalQuestions.length - 1 && (
          <div style={{ borderTop: '1px solid #e0e0e0', margin: '15px 0' }}></div>
        )}
      </div>
    ))}
  </div>
  
  {/* Coding Questions */}
  {codingQuestions.length > 0 && (
    <div className="qa-section-divider">
      <h5>Coding Questions</h5>
    </div>
    
    <div style={{ backgroundColor: '#f9f9f9', padding: '20px' }}>
      {codingQuestions.map((qa, index) => (
        <div key={qa.id || `coding-${index}`}>
          <div style={{ fontWeight: '600', color: '#2196F3' }}>
            Interviewer:
          </div>
          <div style={{ paddingLeft: '15px' }}>
            {qa.question || qa.question_text}
          </div>
          
          <div style={{ fontWeight: '600', color: '#4CAF50' }}>
            Candidate:
          </div>
          <div style={{ paddingLeft: '15px' }}>
            {qa.answer && qa.answer !== 'No code submitted' ? (
              <pre style={{ backgroundColor: '#f5f5f5', padding: '12px' }}>
                {qa.answer}
              </pre>
            ) : (
              <span>No code submitted</span>
            )}
          </div>
        </div>
      ))}
    </div>
  )}
</div>
```

---

## 🔑 Key Features

### 1. **Complete Coverage**
- ✅ Every AI question is saved immediately when generated
- ✅ Every candidate answer is saved (including "No answer provided")
- ✅ No questions or answers are skipped

### 2. **Proper Sequence**
- ✅ Questions and answers saved with `conversation_sequence` (1, 2, 3, 4...)
- ✅ AI questions: odd numbers (1, 3, 5, 7...)
- ✅ Candidate answers: even numbers (2, 4, 6, 8...)
- ✅ Easy to fetch in sequence from UI

### 3. **Duplicate Prevention**
- ✅ Text-based similarity check prevents duplicate questions
- ✅ Checks for existing answers before creating new records
- ✅ Updates existing records if content changes

### 4. **Backward Compatibility**
- ✅ Original question's `transcribed_answer` is also updated
- ✅ Supports both new format (separate records) and old format (combined)

### 5. **Special Cases Handling**
- ✅ Candidate questions (when candidate asks AI)
- ✅ AI responses to candidate questions
- ✅ Pre-closing and closing questions
- ✅ Empty transcripts ("No answer provided")

---

## 📊 Database Query Examples

### Fetch All Q&A in Sequence:
```python
# Get all questions and answers ordered by conversation_sequence
questions = InterviewQuestion.objects.filter(
    session=session
).order_by('conversation_sequence', 'order', 'id')

# Separate AI questions and candidate answers
ai_questions = questions.filter(role='AI', question_level='MAIN')
candidate_answers = questions.filter(role='INTERVIEWEE', question_level='INTERVIEWEE_RESPONSE')
```

### Pair Questions with Answers:
```python
# Group by order and pair AI questions with Interviewee answers
qa_pairs = []
for ai_q in ai_questions:
    answer = candidate_answers.filter(order=ai_q.order).first()
    qa_pairs.append({
        'question': ai_q.question_text,
        'answer': answer.transcribed_answer if answer else 'No answer provided',
        'order': ai_q.order,
        'sequence': ai_q.conversation_sequence
    })
```

---

## 🎯 UI Display Features

### 1. **Sequential Display**
- Questions and answers displayed in the exact order they occurred
- Uses `conversation_sequence` for accurate ordering
- Falls back to `order` if sequence is not available

### 2. **Grouped by Type**
- Technical questions displayed separately
- Coding questions displayed separately
- Each group maintains proper sequence

### 3. **Visual Formatting**
- Interviewer questions in blue (#2196F3)
- Candidate answers in green (#4CAF50)
- Monospace font for code blocks
- Clear separation between Q&A pairs

### 4. **Empty Answer Handling**
- Shows "No answer provided" for empty transcripts
- Shows "No code submitted" for coding questions without submissions

---

## 🔄 Complete Flow Diagram

```
┌─────────────────────────────────────┐
│  1. Interview Starts                │
│     - AI generates introduction Q   │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  2. Save AI Question                │
│     - role='AI'                     │
│     - conversation_sequence=1        │
│     - order=0                       │
│     - question_text="..."           │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  3. Candidate Provides Answer       │
│     - Frontend captures audio       │
│     - Deepgram transcribes          │
│     - Sends to backend              │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  4. Save Candidate Answer           │
│     - role='INTERVIEWEE'             │
│     - conversation_sequence=2        │
│     - order=0 (same as question)    │
│     - transcribed_answer="..."       │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  5. Next Question Generated          │
│     - AI generates next question     │
│     - conversation_sequence=3        │
│     - order=1                       │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  6. Repeat Steps 3-5                │
│     - Until interview completes     │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  7. Fetch for UI                    │
│     - GET /api/interviews/           │
│     - Serializer pairs Q&A          │
│     - Returns sorted list           │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  8. Display in Candidate Details    │
│     - Frontend receives data         │
│     - Sorts by sequence/order       │
│     - Groups by type                 │
│     - Renders in UI                  │
└─────────────────────────────────────┘
```

---

## 📝 Summary

### Storage:
1. **AI Questions**: Saved immediately when generated with `role='AI'`, `conversation_sequence` = odd numbers
2. **Candidate Answers**: Saved immediately when received with `role='INTERVIEWEE'`, `conversation_sequence` = even numbers
3. **Sequence**: Maintained through `conversation_sequence` field (1, 2, 3, 4...)
4. **Order**: Maintained through `order` field (0, 1, 2, 3...)

### Retrieval:
1. **API Endpoint**: `/api/interviews/` returns interviews with `questions_and_answers` field
2. **Serializer**: `get_questions_and_answers()` pairs AI questions with Interviewee answers
3. **Sorting**: By `conversation_sequence` first, then `order`, then `id`

### Display:
1. **Frontend**: Fetches from `/api/interviews/` endpoint
2. **Processing**: Sorts Q&A pairs by sequence/order
3. **Grouping**: Separates technical and coding questions
4. **Rendering**: Displays in sequential script format with proper styling

---

## ✅ Benefits

1. **Complete Data**: Every question and answer is saved, nothing is skipped
2. **Proper Sequence**: Easy to fetch and display in correct order
3. **Flexible**: Supports various question types (Technical, Behavioral, Coding)
4. **Robust**: Handles edge cases (empty answers, candidate questions, etc.)
5. **User-Friendly**: Clean display in UI with proper formatting

---

## 🔍 Debugging

### Check Database:
```python
# Get all questions for a session
questions = InterviewQuestion.objects.filter(session=session).order_by('conversation_sequence')
for q in questions:
    print(f"Seq: {q.conversation_sequence}, Order: {q.order}, Role: {q.role}, "
          f"Level: {q.question_level}, Q: {q.question_text[:50]}, "
          f"A: {q.transcribed_answer[:50] if q.transcribed_answer else 'None'}")
```

### Check API Response:
```javascript
// In browser console
const response = await fetch(`${baseURL}/api/interviews/`, {
  headers: { Authorization: `Token ${authToken}` }
});
const data = await response.json();
console.log('Q&A Data:', data[0].questions_and_answers);
```

---

This system ensures that every question asked by AI and every answer given by candidates is properly stored and displayed in the correct sequence in the Candidate Details UI.

