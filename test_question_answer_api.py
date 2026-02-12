#!/usr/bin/env python
"""
Test the new question-answer API endpoints
"""
import requests
import json

# Base URL for API
BASE_URL = "http://localhost:8000/api/questions"

def test_save_question_answer_pair():
    """Test saving a single question-answer pair"""
    print("🧪 Testing Save Question-Answer Pair API")
    print("=" * 50)
    
    # Test data
    test_data = {
        "session_id": "test-session-id",
        "question_text": "What is your experience with Python?",
        "transcribed_answer": "I have 5 years of experience with Python development.",
        "question_type": "TECHNICAL",
        "question_level": "MAIN"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/save-pair/",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 201:
            print("✅ Question-answer pair saved successfully!")
        else:
            print("❌ Failed to save question-answer pair")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_get_interview_questions():
    """Test getting all questions for a session"""
    print("\n🧪 Testing Get Interview Questions API")
    print("=" * 50)
    
    session_id = "test-session-id"
    
    try:
        response = requests.get(f"{BASE_URL}/{session_id}/")
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Questions retrieved successfully!")
        else:
            print("❌ Failed to retrieve questions")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_save_interview_conversation():
    """Test saving multiple question-answer pairs"""
    print("\n🧪 Testing Save Interview Conversation API")
    print("=" * 50)
    
    test_data = {
        "session_id": "test-session-id",
        "conversation_pairs": [
            {
                "question_text": "Tell me about yourself.",
                "transcribed_answer": "I am a software developer with 5 years of experience.",
                "question_type": "INTRODUCTION",
                "question_level": "INTRO"
            },
            {
                "question_text": "What frameworks have you worked with?",
                "transcribed_answer": "I have worked with Django, Flask, and FastAPI.",
                "question_type": "TECHNICAL",
                "question_level": "MAIN"
            },
            {
                "question_text": "Do you have any questions for us?",
                "transcribed_answer": "No, I don't have any questions. Thank you!",
                "question_type": "CLOSING",
                "question_level": "CLOSE"
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/save-conversation/",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 201:
            print("✅ Conversation saved successfully!")
        else:
            print("❌ Failed to save conversation")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_get_interview_statistics():
    """Test getting interview statistics"""
    print("\n🧪 Testing Get Interview Statistics API")
    print("=" * 50)
    
    session_id = "test-session-id"
    
    try:
        response = requests.get(f"{BASE_URL}/{session_id}/statistics/")
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Statistics retrieved successfully!")
        else:
            print("❌ Failed to retrieve statistics")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Testing Question-Answer API Endpoints")
    print("Make sure Django server is running on http://localhost:8000")
    print()
    
    # Run all tests
    test_save_question_answer_pair()
    test_get_interview_questions()
    test_save_interview_conversation()
    test_get_interview_statistics()
    
    print("\n🎉 All API tests completed!")
