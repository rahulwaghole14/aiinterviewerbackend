# Candidate Question Saving Fix Summary

## 🎯 **Problem Identified:**
When candidates asked questions during interviews, the system was incorrectly saving:
- Candidate's question in the `question_text` column
- AI's response in the `answer_text` column

This was backwards and inconsistent with the expected data structure.

## 🔍 **Expected Behavior:**
For candidate questions, the data should be saved as:
- `question_text`: AI's response to the candidate's question
- `answer_text`: The candidate's original question

This maintains consistency where `question_text` always contains the "question" part of the Q&A pair and `answer_text` contains the "answer" part.

## 🛠️ **Fix Applied:**

### **Before Fix:**
```python
if is_cand_q:
    # INCORRECT: Candidate question in question_text, AI response in answer_text
    qa_pair = save_qa_pair(
        session_key=django_session.session_key,
        question_text=transcript.strip(),  # ❌ Candidate's question
        answer_text=result.get('interviewer_answer') or result.get('next_question') or "I understand.",  # ❌ AI's response
        question_type='CANDIDATE_QUESTION'
    )
```

### **After Fix:**
```python
if is_cand_q:
    # CORRECT: AI response in question_text, candidate question in answer_text
    ai_response = result.get('interviewer_answer') or result.get('next_question') or "I understand."
    
    print(f"🗣️ Candidate asked question: {transcript.strip()[:100]}...")
    print(f"🤖 AI responded: {ai_response[:100]}...")
    
    qa_pair = save_qa_pair(
        session_key=django_session.session_key,
        question_text=ai_response,  # ✅ AI's response
        answer_text=transcript.strip(),  # ✅ Candidate's question
        question_type='CANDIDATE_QUESTION'
    )
```

## 📊 **Verification Results:**

### **Test Output After Fix:**
```
5. Question #5 (CANDIDATE_QUESTION):
   🤖 AI Response: can you explain the salary details...
   🗣️ Candidate Question: Thanks for asking — we'll get back to you via email. Do you have any other questions for us?...
```

This shows the correct structure:
- **AI Response** is in `question_text` (displayed as "🤖 AI Response")
- **Candidate Question** is in `answer_text` (displayed as "🗣️ Candidate Question")

## 🔧 **Enhanced Debugging:**

### **Added Logging:**
```python
print(f"🗣️ Candidate asked question: {transcript.strip()[:100]}...")
print(f"🤖 AI responded: {ai_response[:100]}...")
print(f"✅ Candidate Q&A pair saved with ID: {qa_pair.id if qa_pair else 'None'}")
```

### **Updated Test Script:**
The `test_qa_pairs.py` script now:
- Shows different formatting for candidate questions vs. regular questions
- Displays "🤖 AI Response" and "🗣️ Candidate Question" labels
- Includes specific analysis of candidate questions

## 🎉 **Data Structure Consistency:**

### **Regular AI Questions:**
- `question_text`: AI's question to candidate
- `answer_text`: Candidate's answer to AI

### **Candidate Questions:**
- `question_text`: AI's response to candidate
- `answer_text`: Candidate's question to AI

This maintains a consistent pattern where the "question" part is always what initiates the interaction, and the "answer" part is always the response.

## 📝 **Usage Instructions:**

### **During Interviews:**
Monitor console logs for these messages to verify candidate questions are being saved correctly:
- `🗣️ Candidate asked question:` - Shows what the candidate asked
- `🤖 AI responded:` - Shows how the AI responded
- `✅ Candidate Q&A pair saved with ID:` - Confirms successful saving

### **Data Analysis:**
Use the updated `test_qa_pairs.py` script to verify:
- Candidate questions are properly formatted
- No data inconsistencies
- Correct question-answer relationships

## 🚀 **Impact:**

### **Fixed Issues:**
- ✅ Correct data structure for candidate questions
- ✅ Consistent Q&A pair format across all question types
- ✅ Better debugging and monitoring capabilities
- ✅ Enhanced test verification

### **Data Integrity:**
- All Q&A pairs now follow consistent structure
- Easier to query and analyze candidate interactions
- Better data for reporting and analysis

The candidate question saving functionality now correctly maintains the expected data structure and provides clear debugging information! 🎯✨
