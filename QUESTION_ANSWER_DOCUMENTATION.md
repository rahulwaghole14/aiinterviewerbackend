# Question-Answer Pair Database Functionality

## 🎯 **Overview**

This document describes the comprehensive database functionality for saving every question-answer pair during AI interviews. The system ensures that all questions displayed on screen as interviewer are saved in the `question_text` column, and every transcribed answer from the interviewee is saved in the `transcribed_answer` column. Each question-answer pair is stored in the same row for proper data integrity.

## 📊 **Database Schema**

### **InterviewQuestion Model**

The enhanced `InterviewQuestion` model includes all necessary fields to capture complete interview data:

```python
class InterviewQuestion(models.Model):
    # Core fields
    session = models.ForeignKey(InterviewSession, related_name='questions', on_delete=models.CASCADE)
    question_text = models.TextField()  # Question displayed by AI interviewer
    transcribed_answer = models.TextField(null=True, blank=True)  # Interviewee's answer
    
    # Question categorization
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES)
    question_level = models.CharField(max_length=10, choices=QUESTION_LEVEL_CHOICES)
    
    # Metadata and performance
    order = models.PositiveIntegerField(help_text="Question order in interview")
    conversation_sequence = models.PositiveIntegerField(help_text="Sequential conversation flow")
    asked_at = models.DateTimeField(null=True, blank=True)
    answered_at = models.DateTimeField(null=True, blank=True)
    
    # Performance metrics
    words_per_minute = models.IntegerField(null=True, blank=True)
    filler_word_count = models.IntegerField(null=True, blank=True)
    response_time_seconds = models.FloatField(null=True, blank=True)
    
    # Additional fields
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='AI')
    coding_language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES, null=True, blank=True)
    is_follow_up = models.BooleanField(default=False)
    question_category = models.CharField(max_length=50, null=True, blank=True)
```

### **Question Types Supported**

All interview phases are properly categorized:

- **`INTRODUCTION`** - Initial greeting and introduction questions
- **`TECHNICAL`** - Technical skill and experience questions
- **`BEHAVIORAL`** - Behavioral and situational questions
- **`CODING`** - Programming challenge questions
- **`PRECLOSING`** - Pre-closing wrap-up questions
- **`CLOSING`** - Final closing questions

### **Question Levels**

- **`INTRO`** - Introduction phase
- **`MAIN`** - Main interview questions
- **`FOLLOWUP`** - Follow-up questions
- **`PRECLOSE`** - Pre-closing phase
- **`CLOSE`** - Closing phase

## 🔧 **API Endpoints**

### **1. Save Question-Answer Pair**
```
POST /api/questions/save-pair/
```

**Request Body:**
```json
{
    "session_id": "uuid-string",
    "question_text": "What is your experience with Python?",
    "transcribed_answer": "I have 5 years of experience with Python development.",
    "question_type": "TECHNICAL",
    "question_level": "MAIN"
}
```

**Response:**
```json
{
    "success": true,
    "question_id": "uuid-string",
    "order": 0,
    "question_type": "TECHNICAL",
    "message": "Question-answer pair saved successfully for John Doe"
}
```

### **2. Update Answer for Question**
```
PUT /api/questions/<question_id>/update-answer/
```

**Request Body:**
```json
{
    "transcribed_answer": "Updated answer text",
    "response_time_seconds": 45.5,
    "words_per_minute": 120,
    "filler_word_count": 3
}
```

### **3. Get Interview Questions**
```
GET /api/questions/<session_id>/
```

**Response:**
```json
{
    "success": true,
    "session_id": "uuid-string",
    "candidate_name": "John Doe",
    "total_questions": 5,
    "questions": [
        {
            "id": "uuid-string",
            "question_text": "What is your experience with Python?",
            "transcribed_answer": "I have 5 years of experience...",
            "question_type": "TECHNICAL",
            "question_level": "MAIN",
            "order": 0,
            "asked_at": "2024-01-15T10:30:00Z",
            "answered_at": "2024-01-15T10:31:30Z",
            "response_time_seconds": 90.5,
            "words_per_minute": 120,
            "filler_word_count": 2
        }
    ]
}
```

### **4. Save Interview Conversation**
```
POST /api/questions/save-conversation/
```

**Request Body:**
```json
{
    "session_id": "uuid-string",
    "conversation_pairs": [
        {
            "question_text": "Tell me about yourself.",
            "transcribed_answer": "I am a software developer...",
            "question_type": "INTRODUCTION",
            "question_level": "INTRO"
        },
        {
            "question_text": "What frameworks have you used?",
            "transcribed_answer": "I have worked with Django...",
            "question_type": "TECHNICAL",
            "question_level": "MAIN"
        }
    ]
}
```

### **5. Get Interview Statistics**
```
GET /api/questions/<session_id>/statistics/
```

**Response:**
```json
{
    "success": true,
    "session_id": "uuid-string",
    "candidate_name": "John Doe",
    "total_questions": 10,
    "answered_questions": 8,
    "answer_rate": 80.0,
    "questions_by_type": {
        "INTRODUCTION": 1,
        "TECHNICAL": 5,
        "BEHAVIORAL": 2,
        "CODING": 1,
        "CLOSING": 1
    },
    "questions_by_level": {
        "INTRO": 1,
        "MAIN": 7,
        "CLOSE": 2
    },
    "average_response_time_seconds": 65.5,
    "average_words_per_minute": 115.0
}
```

## 🔄 **Integration with Existing System**

### **Automatic Question Saving**

The system automatically saves questions when they are generated by the AI:

```python
# In interview_app/views.py
InterviewQuestion.objects.create(
    session=session,
    question_text=question_text,
    question_type=question_type,
    question_level=question_level,
    order=next_order,
    asked_at=timezone.now(),
    role='AI'
)
```

### **Automatic Answer Saving**

When interviewee answers are transcribed, they are automatically linked to the question:

```python
# Update existing question with transcribed answer
question.transcribed_answer = transcribed_answer
question.answered_at = timezone.now()
question.response_time_seconds = response_time
question.words_per_minute = wpm
question.filler_word_count = filler_count
question.save()
```

## 📋 **Data Integrity Features**

### **1. Sequential Ordering**
- Questions are automatically ordered using `order` field
- `conversation_sequence` provides conversation flow tracking
- Prevents duplicate questions and maintains interview structure

### **2. Type Validation**
- All question types are validated against predefined choices
- Ensures data consistency across interviews
- Enables proper filtering and analysis

### **3. Timestamp Tracking**
- `asked_at` records when question was displayed
- `answered_at` records when answer was received
- Enables response time analysis

### **4. Performance Metrics**
- `response_time_seconds` tracks answer speed
- `words_per_minute` measures speaking rate
- `filler_word_count` tracks speech quality

## 🎯 **Use Cases**

### **1. Complete Interview Recording**
Every question asked by AI and every answer given by candidate is preserved:

```python
# Get complete interview transcript
questions = InterviewQuestion.objects.filter(session=session).order_by('order')
for question in questions:
    print(f"Q{question.order + 1}: {question.question_text}")
    print(f"A{question.order + 1}: {question.transcribed_answer}")
```

### **2. Interview Analysis**
Analyze interview patterns and performance:

```python
# Get questions by type
technical_questions = InterviewQuestion.objects.filter(
    session=session, 
    question_type='TECHNICAL'
).count()

# Calculate average response time
avg_response_time = InterviewQuestion.objects.filter(
    session=session,
    response_time_seconds__isnull=False
).aggregate(avg=models.Avg('response_time_seconds'))
```

### **3. Export and Reporting**
Generate complete interview reports:

```python
# Export to JSON
interview_data = {
    'candidate': session.candidate_name,
    'questions': [
        {
            'question': q.question_text,
            'answer': q.transcribed_answer,
            'type': q.question_type,
            'timestamp': q.asked_at.isoformat()
        }
        for q in questions
    ]
}
```

## 🔒 **Security and Permissions**

- All endpoints require authentication (`@permission_classes([IsAuthenticated])`)
- Session validation ensures data integrity
- Input validation prevents malformed data
- Database constraints maintain referential integrity

## 📈 **Performance Considerations**

### **Database Indexes**
```python
class Meta:
    indexes = [
        models.Index(fields=['session', 'order']),
        models.Index(fields=['session', 'question_type']),
        models.Index(fields=['conversation_sequence']),
    ]
```

### **Efficient Queries**
- Optimized for session-based queries
- Bulk operations for conversation saving
- Selective field loading for performance

## ✅ **Testing**

### **Unit Tests**
```python
# Test question creation
question = InterviewQuestion.objects.create(
    session=session,
    question_text="Test question",
    transcribed_answer="Test answer",
    question_type="TECHNICAL"
)
assert question.question_text == "Test question"
assert question.transcribed_answer == "Test answer"
```

### **API Tests**
```python
# Test endpoint responses
response = client.post('/api/questions/save-pair/', data)
assert response.status_code == 201
assert response.json()['success'] == True
```

## 🎉 **Summary**

This comprehensive question-answer pair functionality ensures:

✅ **Complete Data Capture** - Every question and answer is saved
✅ **Proper Categorization** - All interview phases are tracked
✅ **Performance Metrics** - Response time and speech quality analysis
✅ **Data Integrity** - Sequential ordering and validation
✅ **API Integration** - RESTful endpoints for frontend integration
✅ **Scalability** - Optimized for high-volume interview data

The system provides a robust foundation for interview data management and analysis!
