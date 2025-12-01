"""
COMPLETE AI Bot - Full port from app.py (1678 lines) for Django
This includes ALL prompts, RAG system, and advanced interview logic
"""
import os
import re
import uuid
import time
import threading
from typing import Dict, List
import google.generativeai as genai
from django.conf import settings
import numpy as np

# Configure Gemini - Using 2.5-flash as per your app.py
GEMINI_API_KEY = "AIzaSyA4DMuYRFP9-oxfQAJIMyZjabE5LA8YbyI"
genai.configure(api_key=GEMINI_API_KEY)

# Google Cloud TTS setup (exactly like app.py)
# Use absolute path from BASE_DIR
credentials_path = os.path.join(settings.BASE_DIR, "ringed-reach-471807-m3-cf0ec93e3257.json")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", credentials_path)
if os.path.exists(credentials_path):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
    print(f"✅ Google Cloud TTS credentials set to: {credentials_path}")
elif os.path.exists(GOOGLE_APPLICATION_CREDENTIALS):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_APPLICATION_CREDENTIALS
    print(f"✅ Google Cloud TTS credentials set to: {GOOGLE_APPLICATION_CREDENTIALS}")
else:
    print(f"⚠️ Google Cloud TTS credentials not found at: {credentials_path} or {GOOGLE_APPLICATION_CREDENTIALS}")

# Import Google Cloud TTS (exactly like app.py)
try:
    from google.cloud import texttospeech
    TTS_AVAILABLE = True
    print("✅ Google Cloud TTS imported successfully")
except ImportError as e:
    texttospeech = None
    TTS_AVAILABLE = False
    print(f"⚠️ Google Cloud TTS import failed: {e}")

# Upload directory for audio files
UPLOADS_DIR = os.path.join(settings.MEDIA_ROOT, 'ai_uploads')
os.makedirs(UPLOADS_DIR, exist_ok=True)


# ------------------ RAG System (from app.py lines 111-157) ------------------
try:
    import faiss
    from sentence_transformers import SentenceTransformer
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("⚠️ FAISS/SentenceTransformer not available - using fallback")


class RAGSystem:
    """Exact copy from app.py"""
    def __init__(self):
        if FAISS_AVAILABLE:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
        else:
            self.model = None
        self.dimension = 384
        if FAISS_AVAILABLE:
            import faiss
            self.index = faiss.IndexFlatL2(self.dimension)
        else:
            self.index = None
        self.jd_chunks = []
        self.is_initialized = False
    
    def process_jd(self, jd_text):
        """Process job description and create embeddings"""
        # Split JD into chunks
        sentences = jd_text.split('. ')
        self.jd_chunks = [s.strip() + '.' for s in sentences if s.strip()]
        
        if self.model and FAISS_AVAILABLE:
            # Create embeddings using SentenceTransformer
            embeddings = self.model.encode(self.jd_chunks)
            embeddings = embeddings.astype('float32')
            # Reset and rebuild index
            import faiss
            self.index = faiss.IndexFlatL2(self.dimension)
            self.index.add(embeddings)
        
        self.is_initialized = True
        print(f"✅ Processed JD into {len(self.jd_chunks)} chunks")
    
    def retrieve_context(self, query, top_k=3):
        """Retrieve relevant JD context"""
        if not self.is_initialized:
            return []
        
        if self.model and FAISS_AVAILABLE and self.index:
            query_embedding = self.model.encode([query])
            query_embedding = query_embedding.astype('float32')
            distances, indices = self.index.search(query_embedding, top_k)
            return [self.jd_chunks[i] for i in indices[0]]
        else:
            # Fallback: return first few chunks
            return self.jd_chunks[:top_k]


# Initialize RAG system
rag_system = RAGSystem()


# ------------------ Interview State Management (from app.py lines 521-558) ------------------
class InterviewSession:
    """Exact copy from app.py"""
    def __init__(self, session_id, candidate_name, jd_text, max_questions=4):
        self.session_id = session_id
        self.candidate_name = candidate_name
        self.conversation_history = []
        self.current_question_number = 0
        self.max_questions = max_questions
        self.is_completed = False
        self.jd_text = jd_text
        self.asked_for_questions = False
        self.completed_at = None
        self.awaiting_answer = False
        self.last_active_question_text = ""
        # Timing and activity tracking
        self.question_asked_at = 0.0
        self.first_voice_at = None
        self.last_transcript_update_at = None
        self.last_transcript_word_count = 0
        self.initial_silence_action_taken = False
        self.asked_pre_closing_question = False  # Track if we've asked the question before closing
        self.waiting_for_candidate_question = False  # Track if we're waiting for candidate's question after they said yes
        
        # Question type tracking for ratio management (30% follow-up, 70% regular)
        self.regular_questions_count = 0  # Count of regular questions asked
        self.follow_up_questions_count = 0  # Count of follow-up questions asked
        
        # Track all questions asked to prevent duplicates
        self.asked_questions = []  # List of all questions asked so far
        
        # Process JD for RAG
        rag_system.process_jd(jd_text)
    
    def add_interviewer_message(self, text):
        self.conversation_history.append({"role": "interviewer", "text": text})
        # Track questions (not responses/answers to candidate questions)
        # Only add if it's a question (contains question mark or is a question pattern)
        if "?" in text or any(word in text.lower() for word in ["what", "how", "why", "when", "where", "tell me", "describe", "explain", "can you"]):
            # Normalize question for comparison (remove extra spaces, lowercase)
            normalized_q = " ".join(text.lower().split())
            if normalized_q not in self.asked_questions:
                self.asked_questions.append(normalized_q)
    
    def add_candidate_message(self, text):
        self.conversation_history.append({"role": "candidate", "text": text})
    
    def get_last_interviewer_question(self):
        for message in reversed(self.conversation_history):
            if message["role"] == "interviewer":
                return message["text"]
        return None
    
    def get_conversation_context(self):
        return "\n".join([f"{msg['role']}: {msg['text']}" for msg in self.conversation_history])


# Global sessions storage
sessions = {}


# ------------------ Timing Helpers (from app.py lines 562-573) ------------------
def _reset_question_timers(session: InterviewSession):
    session.question_asked_at = time.time()
    session.first_voice_at = None
    session.last_transcript_update_at = None
    session.last_transcript_word_count = 0
    session.initial_silence_action_taken = False


def _count_words(text: str) -> int:
    if not text:
        return 0
    return len(re.findall(r"\b\w+\b", text))


# ------------------ Gemini helper (from app.py lines 394-401) ------------------
# Track last API call time to implement rate limiting
# Use a lock to ensure only one API call happens at a time globally
_gemini_api_lock = threading.Lock()
_last_gemini_call_time = 0
_min_delay_between_calls = 5.0  # Increased to 5 seconds between API calls to prevent rate limits

def gemini_generate(prompt, max_retries=5, initial_delay=5):
    """
    Use gemini-2.0-flash for interview questions with retry logic for rate limits.
    Uses a global lock to ensure only one API call happens at a time.
    
    Args:
        prompt: The prompt to send to Gemini
        max_retries: Maximum number of retry attempts (default: 5, increased from 3)
        initial_delay: Initial delay in seconds before retry (default: 5, increased from 2)
    
    Returns:
        Generated text or error message
    """
    global _last_gemini_call_time
    
    # Acquire lock to ensure only one API call at a time globally
    with _gemini_api_lock:
        # Rate limiting: Ensure minimum delay between API calls
        current_time = time.time()
        time_since_last_call = current_time - _last_gemini_call_time
        if time_since_last_call < _min_delay_between_calls:
            sleep_time = _min_delay_between_calls - time_since_last_call
            print(f"⏱️ Rate limiting: Waiting {sleep_time:.2f} seconds before next API call...")
            time.sleep(sleep_time)
        
        for attempt in range(max_retries):
            try:
                model = genai.GenerativeModel("gemini-2.0-flash")
                resp = model.generate_content(prompt)
                _last_gemini_call_time = time.time()  # Update last call time on success
                print(f"✅ Gemini API call successful (attempt {attempt + 1})")
                return resp.text if resp and resp.text else "Could not generate a response."
            except Exception as e:
                error_str = str(e).lower()
                is_rate_limit = '429' in error_str or 'resource exhausted' in error_str or 'quota' in error_str
                
                if is_rate_limit and attempt < max_retries - 1:
                    # Calculate exponential backoff delay: 5s, 10s, 20s, 40s, 80s
                    delay = initial_delay * (2 ** attempt)
                    print(f"⚠️ Gemini rate limit (429) detected. Retrying in {delay} seconds... (attempt {attempt + 1}/{max_retries})")
                    print(f"   Error details: {str(e)[:200]}")
                    print(f"   This is a rate limit error. Waiting longer to avoid hitting quota limits...")
                    time.sleep(delay)
                    continue
                else:
                    # For non-rate-limit errors or final attempt, return error
                    print(f"❌ Gemini error: {e}")
                    if is_rate_limit:
                        # If rate limit persists after all retries, suggest waiting longer
                        wait_time = initial_delay * (2 ** (max_retries - 1))
                        return f"[Gemini error: 429 Resource exhausted after {max_retries} attempts. The API quota may be temporarily exhausted. Please wait {wait_time} seconds and try again, or check your Gemini API quota limits.]"
                    return f"[Gemini error: {str(e)}]"
        
        # If all retries exhausted
        wait_time = initial_delay * (2 ** (max_retries - 1))
        return f"[Gemini error: Failed after {max_retries} attempts due to rate limiting. Please wait {wait_time} seconds before trying again or check your API quota.]"


# ------------------ Helper functions (from app.py lines 403-786) ------------------
def generate_final_closing(session):
    """Generate a brief, warm LLM-based closing for the interview."""
    conversation_context = session.get_conversation_context()
    prompt = (
        "You are a professional interviewer closing an interview.\n\n"
        f"Interview so far (short context):\n{conversation_context[-3000:]}\n\n"
        "Write a very brief, warm closing message. "
        "IMPORTANT: You MUST include 'Thank you for your time' or a similar thank you phrase. "
        "Keep it professional and friendly. "
        "Example: 'Thank you for your time today. We'll be in touch soon.' "
        "Keep it to one or two short sentences."
    )
    closing_text = gemini_generate(prompt)
    # Fallback if generation fails
    if not closing_text or "[Gemini error" in closing_text:
        return "Thank you for your time today. We'll be in touch soon."
    return closing_text


def generate_elaborated_question(session, candidate_request_text: str) -> str:
    """Generate a clearer, more detailed version of the last interviewer question with only 1-2 lines of extra context."""
    last_q = session.get_last_interviewer_question() or ""
    jd_context = " ".join(rag_system.retrieve_context(last_q or candidate_request_text, top_k=5))
    conversation_context = session.get_conversation_context()
    prompt = (
        "You are a professional technical interviewer conducting a TECHNICAL INTERVIEW. The candidate asked to elaborate/clarify the previous question.\n\n"
        f"Job Description Context: {jd_context}\n\n"
        "Interview so far:\n"
        f"{conversation_context}\n\n"
        f"Original question: {last_q}\n\n"
        "CRITICAL: This is a TECHNICAL INTERVIEW. You MUST provide elaboration/clarification ONLY for technical questions related to the job description.\n"
        "IMPORTANT: Rewrite the question with ONLY 1-2 lines of additional TECHNICAL context or clarification. "
        "Add minimal helpful TECHNICAL context or a brief TECHNICAL example, but DO NOT reveal the answer or provide too much detail. "
        "Keep it concise and TECHNICAL - the question should still require the candidate to think and provide their own TECHNICAL answer. "
        "Do not add multiple questions. Keep it professional and suitable for a TECHNICAL interview."
    )
    return gemini_generate(prompt)


def is_low_content_answer(text: str) -> bool:
    """Detect very short answers: 4 words or fewer."""
    if not text:
        return True
    try:
        return _count_words(text) <= 4
    except Exception:
        normalized = (text or "").strip()
        return len([w for w in normalized.split() if w]) <= 4


def is_dont_know_answer(text: str) -> bool:
    """Detect if candidate says they don't know or are unsure."""
    if not text:
        return False
    text_lower = text.strip().lower()
    dont_know_phrases = [
        "don't know", "dont know", "do not know", "don't know", "i don't know",
        "i dont know", "i do not know", "not sure", "unsure", "i'm not sure",
        "im not sure", "no idea", "have no idea", "not familiar", "unfamiliar",
        "don't remember", "dont remember", "can't recall", "cant recall",
        "not aware", "unaware", "haven't heard", "havent heard", "never heard",
        "don't understand", "dont understand", "not clear", "unclear",
        "i'm not familiar", "im not familiar", "not my area", "outside my expertise"
    ]
    return any(phrase in text_lower for phrase in dont_know_phrases)


def is_broad_or_vague_answer(answer: str) -> bool:
    """Check if answer is broad or vague (lacks specific details, examples, or depth)."""
    if not answer or not answer.strip():
        return True
    
    # Check for very short answers (4 words or fewer)
    if is_low_content_answer(answer):
        return True
    
    # Check for generic phrases that indicate vague answers
    vague_phrases = [
        "i think", "probably", "maybe", "kind of", "sort of", "basically",
        "generally", "usually", "typically", "in general", "more or less",
        "i guess", "i suppose", "not really", "not much", "nothing specific",
        "just", "only", "a bit", "a little", "somewhat"
    ]
    answer_lower = answer.lower()
    vague_count = sum(1 for phrase in vague_phrases if phrase in answer_lower)
    
    # If answer has multiple vague phrases, it's likely vague
    if vague_count >= 2:
        return True
    
    # Check word count - very short answers are likely vague
    word_count = _count_words(answer)
    if word_count <= 10:
        return True
    
    return False


def answer_matches_jd_context(answer: str, jd_text: str) -> bool:
    """Check if answer topic matches or relates to Job Description context."""
    if not answer or not jd_text:
        return False
    
    # Extract key terms from JD (simple keyword matching)
    jd_lower = jd_text.lower()
    answer_lower = answer.lower()
    
    # Common technical terms that might appear in both
    technical_terms = [
        "python", "java", "javascript", "react", "django", "flask", "node",
        "database", "sql", "api", "rest", "aws", "cloud", "docker", "kubernetes",
        "algorithm", "data structure", "frontend", "backend", "full stack",
        "machine learning", "ai", "testing", "agile", "scrum", "git", "ci/cd"
    ]
    
    # Check if answer contains any technical terms from JD
    matching_terms = [term for term in technical_terms if term in jd_lower and term in answer_lower]
    if len(matching_terms) >= 1:
        return True
    
    # Use RAG system to check relevance
    try:
        relevant_chunks = rag_system.retrieve_context(answer, top_k=3)
        if relevant_chunks:
            # If RAG finds relevant chunks, answer likely matches JD
            return True
    except Exception as e:
        print(f"⚠️ Error checking JD context match: {e}")
    
    return False


def should_ask_follow_up(session: InterviewSession, answer: str) -> bool:
    """
    Determine if a follow-up question should be asked based on:
    1. Answer quality (broad/vague)
    2. JD context match
    3. Ratio constraint (30% follow-up, 70% regular)
    
    IMPORTANT: Candidate questions are NOT counted in the overall question ratio.
    This function is only called for candidate ANSWERS, not candidate QUESTIONS.
    """
    # Don't ask follow-up for closing questions or when handling candidate questions
    if session.asked_for_questions or session.asked_pre_closing_question or session.waiting_for_candidate_question:
        return False
    
    # Don't ask follow-up if the transcript is actually a candidate question
    if is_candidate_question(answer):
        return False
    
    # Calculate current ratio
    total_questions = session.regular_questions_count + session.follow_up_questions_count
    if total_questions > 0:
        current_follow_up_ratio = session.follow_up_questions_count / total_questions
        # If we've already exceeded 30%, don't ask more follow-ups
        if current_follow_up_ratio >= 0.30:
            print(f"📊 Follow-up ratio already at {current_follow_up_ratio*100:.1f}% (target: 30%). Skipping follow-up.")
            return False
        
        # Check projected ratio if we add this follow-up
        projected_follow_ups = session.follow_up_questions_count + 1
        projected_total = total_questions + 1
        projected_ratio = projected_follow_ups / projected_total
        
        # If adding this follow-up would exceed 30%, don't generate it
        if projected_ratio > 0.30:
            print(f"📊 Projected follow-up ratio would be {projected_ratio*100:.1f}% (current: {current_follow_up_ratio*100:.1f}%, target: 30%). Skipping follow-up.")
            return False
    
    # Check if answer is broad/vague
    if not is_broad_or_vague_answer(answer):
        print(f"📊 Answer is detailed/specific. Skipping follow-up.")
        return False
    
    # Check if answer matches JD context
    if not answer_matches_jd_context(answer, session.jd_text):
        print(f"📊 Answer doesn't match JD context. Skipping follow-up.")
        return False
    
    # Both conditions met: answer is broad/vague AND matches JD context
    print(f"✅ Answer is broad/vague and matches JD context. Will ask follow-up.")
    return True


def assess_answer_relevance_with_llm(question: str, answer: str) -> bool:
    """Use LLM to conservatively judge if the answer is related to the question."""
    if not question or not answer:
        return False
    prompt = (
        "You are the interview taker evaluating a candidate's answer for relevance to your question.\n"
        f"Question: {question}\n"
        f"Answer: {answer}\n\n"
        "Guidelines: Respond 'unrelated' only if the answer is clearly off-topic or non-responsive."
        " If the answer is brief but plausibly responsive, or asks for clarification/repetition, respond 'related'.\n"
        "Answer with exactly one word: related OR unrelated."
    )
    verdict = (gemini_generate(prompt) or "").strip().lower()
    return "related" in verdict and "unrelated" not in verdict


def generate_clarification_prompt_with_question(session) -> str:
    """Generate a one-line polite clarification that includes the original question."""
    original_q = get_last_strict_question(session) or ""
    prompt = (
        "You are the interview taker conducting a live interview. The candidate's answer seems unrelated or unclear.\n"
        f"Original question: {original_q}\n\n"
        "Write exactly one single-line sentence that politely says you didn't understand the answer and asks them to repeat or clarify, "
        "and include the original question after this exact phrase: 'Here is the question again: '. "
        "Do not mention that you didn't understand the question; refer to their answer."
    )
    line = (gemini_generate(prompt) or "").strip().replace("\n", " ")
    return line


def is_elaboration_request(text: str) -> bool:
    """Detect if candidate is asking to elaborate/clarify the question."""
    if not text:
        return False
    t_lower = (text or "").strip().lower()
    cues = [
        "elaborate", "elaboration", "explain", "more detail", "clarify", "clarification",
        "what do you mean", "could you expand", "expand on", "help me understand",
        "can you elaborate", "please elaborate", "say it in detail"
    ]
    return any(cue in t_lower for cue in cues)


def is_repeat_request_via_llm(session, candidate_response: str, last_question: str) -> bool:
    """Use LLM to determine if the candidate is requesting to repeat the question"""
    if not candidate_response or not candidate_response.strip():
        return False
    
    if not last_question:
        return False
    
    try:
        prompt = (
            f"You are analyzing a candidate's response during a technical interview.\n\n"
            f"Last question asked: {last_question}\n\n"
            f"Candidate's response: {candidate_response}\n\n"
            f"Determine if the candidate is asking to repeat the previous question or asking to hear the question again.\n"
            f"Look for phrases like:\n"
            f"- 'repeat the question'\n"
            f"- 'repeat the previous question'\n"
            f"- 'ask again'\n"
            f"- 'ask previous question'\n"
            f"- 'can you repeat'\n"
            f"- 'say that again'\n"
            f"- 'what was the question'\n"
            f"- 'i didn't hear'\n"
            f"- 'pardon'\n"
            f"- 'sorry what'\n\n"
            f"IMPORTANT: \n"
            f"- If the candidate is explicitly asking to repeat or hear the question again, return the EXACT words/phrases from their response that indicate this (copy their words as-is).\n"
            f"- If the candidate is providing an answer (even if unclear), return 'NO'.\n"
            f"- If the candidate is asking a different question, return 'NO'.\n"
            f"- If the candidate is asking for clarification or elaboration, return 'NO'.\n\n"
            f"Examples:\n"
            f"- If candidate says 'Can you repeat the question?', return: 'Can you repeat the question?'\n"
            f"- If candidate says 'Sorry, what was the question?', return: 'Sorry, what was the question?'\n"
            f"- If candidate says 'I didn't hear that', return: 'I didn't hear that'\n"
            f"- If candidate says 'The answer is Python', return: 'NO'\n"
            f"- If candidate says 'What is the salary?', return: 'NO'\n\n"
            f"Return the candidate's exact words if it's a repeat request, or 'NO' if it's not."
        )
        
        response = gemini_generate(prompt, max_retries=3)
        if response:
            response_clean = response.strip()
            # Check if LLM returned 'NO' (not a repeat request)
            if response_clean.upper() == "NO":
                print(f"❌ LLM did not detect repeat request: '{candidate_response[:100]}...'")
                return False
            else:
                # LLM returned the candidate's words indicating a repeat request
                print(f"✅ LLM detected repeat request with words: '{response_clean}' from candidate response: '{candidate_response[:100]}...'")
                return True
        
        print(f"❌ LLM did not detect repeat request: '{candidate_response[:100]}...'")
        return False
    except Exception as e:
        print(f"⚠️ Error checking repeat request via LLM: {e}")
        return False


def generate_repeat_question_response(session, original_question: str) -> str:
    """Generate a response using LLM to repeat the question naturally"""
    try:
        conversation_context = session.get_conversation_context()
        
        prompt = (
            f"You are a professional technical interviewer. The candidate has asked you to repeat the question.\n\n"
            f"Original question that was asked: {original_question}\n\n"
            f"Interview context so far:\n{conversation_context}\n\n"
            f"Generate a natural, professional response that repeats the question. "
            f"Your response should:\n"
            f"1. Briefly acknowledge the request (e.g., 'Of course', 'Sure', 'No problem')\n"
            f"2. Repeat the exact same question clearly\n"
            f"3. Keep it concise and professional\n"
            f"4. Do NOT add any new information or change the question\n"
            f"5. Do NOT ask follow-up questions - just repeat the original question\n\n"
            f"Generate ONLY the response text, nothing else. Keep it to 1-2 sentences maximum."
        )
        
        response = gemini_generate(prompt, max_retries=3)
        if response and not response.startswith("[Gemini error"):
            return response.strip()
        else:
            # Fallback: Simple repeat with acknowledgment
            return f"Of course. {original_question}"
    except Exception as e:
        print(f"Error generating repeat question response: {e}")
        # Fallback: Simple repeat with acknowledgment
        return f"Of course. {original_question}"


def is_proceed_prompt_text(text: str) -> bool:
    if not text:
        return False
    t = (text or "").strip().lower()
    cues = [
        "i didn't catch a response", "i didn't catch a response",
        "shall we move to the next question"
    ]
    return any(c in t for c in cues)


def is_affirmative_response(text: str) -> bool:
    if not text:
        return False
    t = (text or "").strip().lower()
    affirmatives = [
        "yes", "yeah", "yep", "yup", "sure", "ok", "okay",
        "proceed", "move on", "next", "go ahead"
    ]
    return any(t == a or a in t for a in affirmatives)


def is_negative_response(text: str) -> bool:
    if not text:
        return False
    t = (text or "").strip().lower()
    negatives = ["no", "nope", "nah", "not now", "dont", "don't", "do not"]
    return any(t == n or n in t for n in negatives)


def is_candidate_question(text):
    """Heuristically detect if the candidate's transcript is a question for the interviewer."""
    if not text:
        return False
    t = text.strip().lower()
    if "?" in t:
        return True
    question_starters = [
        "what ", "how ", "why ", "when ", "where ", "who ", "which ",
        "can you", "could you", "would you", "should i", "do you", "are you",
        "is it", "may i", "might we", "could i", "please explain", "i have a question",
        "could you explain", "can i ask"
    ]
    return any(t.startswith(qs) or qs in t for qs in question_starters)


def generate_candidate_answer(session, candidate_question_text):
    """Answer the candidate's question about the interview, role, or company using JD context and interview history."""
    jd_context = " ".join(rag_system.retrieve_context(candidate_question_text, top_k=5))
    if not jd_context:
        jd_context = " ".join(rag_system.retrieve_context("job description", top_k=5))
    conversation_context = session.get_conversation_context()

    prompt = (
        "You are the interviewer. The candidate asked a question during the interview about the role, company, or interview process.\n\n"
        f"Job Description Context: {jd_context}\n\n"
        "Interview so far:\n"
        f"{conversation_context}\n\n"
        f"Candidate's question: {candidate_question_text}\n\n"
        "Answer the candidate's question briefly, accurately, and professionally based on the job description and interview context. "
        "If the question is about the role, team, or company, provide a helpful answer. "
        "If the question cannot be answered right now or is not related to the interview, "
        "say: 'Thanks for asking — we'll get back to you via email.' "
        "Keep your answer concise (2-3 sentences maximum). "
        "Do not ask a new interview question in this answer. "
        "IMPORTANT: Do NOT say 'go ahead with your answer' or 'please go ahead' - the candidate has already answered the previous question."
    )
    return gemini_generate(prompt)


def says_no_more_questions(text: str) -> bool:
    """Heuristically detect if candidate indicates they have no more questions."""
    if not text:
        return False
    t = (text or "").strip().lower()
    negatives = [
        "no", "nope", "nah", "that's all", "thats all", "that's it", "thats it",
        "all good", "im good", "i'm good", "i am good", "nothing else", "no further",
        "no more", "no more questions", "no questions", "no question", "none",
        "no thanks", "no thank you", "i'm fine", "im fine", "i am fine"
    ]
    if any(neg in t for neg in negatives):
        return True
    import re as _re
    if _re.search(r"(^|\b)no(\b|$)", t):
        return True
    return False


def looks_like_closing(text: str) -> bool:
    """Detect if text already reads like a final closing message."""
    if not text:
        return False
    tl = text.lower()
    cues = [
        "thank you for your time", "we will be in touch", "we'll be in touch",
        "have a good day", "thanks for your time", "next steps", "we appreciate your time"
    ]
    return any(c in tl for c in cues)


def generate_proceed_prompt(session):
    """Ask politely if the candidate wants to move to the next question."""
    jd_context = " ".join(rag_system.retrieve_context("proceed to next question", top_k=3))
    conversation_context = session.get_conversation_context()
    prompt = (
        "You are a polite interviewer. It seems there was no audible response.\n\n"
        f"Job Description Context: {jd_context}\n\n"
        "Interview so far:\n"
        f"{conversation_context}\n\n"
        "Ask in one concise line: 'I didn't catch a response — shall we move to the next question?'"
        " Avoid extra text."
    )
    return gemini_generate(prompt)


def get_last_strict_question(session: InterviewSession) -> str:
    """Return the most recent interviewer message that looks like a real question."""
    skip_phrases = [
        "thanks for asking", "please go ahead with your answer", "we'll follow up via email",
        "we'll follow up via email", "let's move on", "sure — please go ahead", "sure - please go ahead",
        "i didn't catch a response", "i didn't catch a response", "shall we move to the next question",
        "please try again", "we appreciate your question", "we appreciate your question",
        "before we wrap up"
    ]
    for msg in reversed(session.conversation_history):
        if msg.get("role") != "interviewer":
            continue
        text = (msg.get("text") or "").strip().lower()
        if any(p in text for p in skip_phrases):
            continue
        if msg.get("text", "").strip().endswith("?"):
            return msg["text"]
    return session.get_last_interviewer_question() or ""


# ------------------ TTS (from app.py lines 575-639) ------------------
def text_to_speech(text, filename):
    """Generate MP3 file for given text using Google Cloud Text-to-Speech (from app.py lines 575-639)"""
    try:
        # Ensure filename has .mp3 extension
        if not filename.lower().endswith('.mp3'):
            filename = f"{os.path.splitext(filename)[0]}.mp3"

        if not TTS_AVAILABLE or not texttospeech:
            print("⚠️ TTS library not available - skipping audio")
            return ""

        # Ensure Google Cloud credentials are set
        credentials_path = os.path.join(settings.BASE_DIR, "ringed-reach-471807-m3-cf0ec93e3257.json")
        if os.path.exists(credentials_path):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
            print(f"✅ Google Cloud credentials set: {credentials_path}")
        else:
            print(f"❌ Google Cloud credentials not found: {credentials_path}")
            # Still try to proceed in case credentials are set via environment variable

        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=text)
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,
            pitch=0.0
        )

        # Query available en-IN voices and select a male voice, preferring Neural2 then Wavenet
        try:
            available_voices = client.list_voices(language_code="en-IN").voices
        except Exception as list_err:
            print(f"⚠️ Could not list voices for en-IN: {list_err}")
            available_voices = []

        def score_voice(v):
            name = getattr(v, 'name', '') or ''
            quality = 2 if 'Neural2' in name else (1 if 'Wavenet' in name else 0)
            return (quality, name)

        male_voices = [v for v in available_voices if v.ssml_gender == texttospeech.SsmlVoiceGender.MALE]
        selected_voice_name = None
        if male_voices:
            male_voices.sort(key=score_voice, reverse=True)
            selected_voice_name = male_voices[0].name

        if selected_voice_name:
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-IN",
                name=selected_voice_name
            )
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
        else:
            # Fallback: request male gender without specifying a name
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-IN",
                ssml_gender=texttospeech.SsmlVoiceGender.MALE
            )
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )

        audio_path = os.path.join(UPLOADS_DIR, filename)
        with open(audio_path, "wb") as out:
            out.write(response.audio_content)
        
        # Verify file was created
        if not os.path.exists(audio_path):
            print(f"❌ TTS audio file not created at: {audio_path}")
            return ""
        
        file_size = os.path.getsize(audio_path)
        if file_size == 0:
            print(f"❌ TTS audio file is empty (0 bytes): {audio_path}")
            return ""
        
        # Return URL for Django media serving
        audio_url = f"{settings.MEDIA_URL}ai_uploads/{filename}"
        print(f"✅ TTS audio generated successfully: {audio_url} (size: {file_size} bytes)")
        return audio_url
    except Exception as e:
        print(f"❌ Google Cloud TTS error: {e}")
        import traceback
        traceback.print_exc()
        # Don't fail silently - return empty string so frontend can handle gracefully
        print(f"⚠️ Returning empty audio_url - frontend will handle text-only mode")
        return ""


# ------------------ Question Generation (from app.py lines 641-684) ------------------
def is_question_similar(new_question: str, existing_questions: list, threshold: float = 0.7) -> bool:
    """Check if a new question is similar to any previously asked questions."""
    if not existing_questions:
        return False
    
    new_q_normalized = " ".join(new_question.lower().split())
    
    # Simple word overlap check
    new_words = set(new_q_normalized.split())
    
    for existing_q in existing_questions:
        existing_words = set(existing_q.split())
        if len(existing_words) == 0:
            continue
        
        # Calculate word overlap ratio
        overlap = len(new_words.intersection(existing_words))
        total_unique = len(new_words.union(existing_words))
        similarity = overlap / total_unique if total_unique > 0 else 0
        
        # Also check if the normalized questions are very similar (exact match after normalization)
        if new_q_normalized == existing_q:
            return True
        
        # Check if key question words match (more than threshold similarity)
        if similarity >= threshold:
            return True
    
    return False


def _shape_question(text: str, ensure_intro: bool = False) -> str:
    """Ensure a single, concise question with a trailing question mark.
    CRITICAL: Extract only the FIRST question if multiple questions are present.
    """
    if not text:
        return "Could you describe a recent project where you solved a challenging technical problem?"
    
    cleaned = text.strip()
    # Normalize whitespace
    cleaned = " ".join(cleaned.split())
    
    # CRITICAL: If multiple questions are present (multiple "?"), keep ONLY the first one
    if cleaned.count("?") > 1:
        # Split by "?" and take only the first question
        first_question = cleaned.split("?")[0].strip() + "?"
        print(f"⚠️ Multiple questions detected! Extracting only first question:")
        print(f"   Original: {cleaned[:150]}...")
        print(f"   Extracted: {first_question}")
        cleaned = first_question
    elif "?" in cleaned:
        # Single question - ensure it ends with "?"
        cleaned = cleaned.split("?")[0].strip() + "?"
    else:
        # No question mark - convert statement to question
        cleaned = cleaned.rstrip(".")
        if not cleaned.lower().startswith(("what", "how", "why", "can", "could", "would", "tell", "describe", "share", "walk", "give", "do", "did", "have", "is", "are", "will")):
            cleaned = "Can you " + cleaned[0].lower() + cleaned[1:] if len(cleaned) > 1 else f"Can you {cleaned}"
        if not cleaned.endswith("?"):
            cleaned = cleaned + "?"
    
    if ensure_intro:
        intro_keywords = ("introduce yourself", "introduction", "background", "yourself", "tell me about yourself")
        if not any(kw in cleaned.lower() for kw in intro_keywords):
            cleaned = "To get started, could you briefly introduce yourself and highlight one experience you are proud of?"
    
    return cleaned


def generate_question(session, question_type="introduction", last_answer_text=None, allow_elaboration=False):
    """Generate the next interview question using JD + latest transcript context.
    
    Args:
        session: InterviewSession object
        question_type: Type of question ("introduction", "follow_up", "regular", "closing")
        last_answer_text: The candidate's last answer text
        allow_elaboration: If True, allows repeating/elaborating on the last question (only when candidate explicitly asks)
    """
    # Build JD context prioritized by the last answer if available
    jd_context_chunks = []
    if last_answer_text and last_answer_text.strip():
        jd_context_chunks = rag_system.retrieve_context(last_answer_text, top_k=5)
    if not jd_context_chunks:
        jd_context_chunks = rag_system.retrieve_context("job requirements and responsibilities", top_k=5)
    jd_context = " ".join(jd_context_chunks)

    conversation_context = session.get_conversation_context()
    
    # Build list of previously asked questions for the prompt
    previously_asked = ""
    if session.asked_questions and not allow_elaboration:
        # Show ALL asked questions, not just last 10, to ensure no repeats
        previously_asked = "\n\n" + "="*80 + "\n"
        previously_asked += "🚫 CRITICAL - DO NOT REPEAT ANY OF THESE QUESTIONS:\n"
        previously_asked += "="*80 + "\n"
        previously_asked += "The following questions have ALREADY been asked. You MUST ask a COMPLETELY DIFFERENT question.\n"
        previously_asked += "DO NOT ask the same question again.\n"
        previously_asked += "DO NOT ask a similar question with slightly different wording.\n"
        previously_asked += "DO NOT ask a question that covers the same topic.\n"
        previously_asked += "You MUST ask a NEW question on a DIFFERENT topic or aspect.\n\n"
        previously_asked += "Previously asked questions:\n"
        for i, q in enumerate(session.asked_questions, 1):  # Show ALL questions
            previously_asked += f"{i}. {q}\n"
        previously_asked += "\n" + "="*80 + "\n"
        previously_asked += "REMEMBER: The candidate has ALREADY answered these questions. Move to a NEW question.\n"
        previously_asked += "="*80 + "\n\n"
    
    if question_type == "introduction":
        prompt = (
            f"You are a professional technical interviewer conducting a TECHNICAL INTERVIEW. The candidate's name is {session.candidate_name}.\n\n"
            f"Job Description Context: {jd_context}\n\n"
            "CRITICAL: This is a TECHNICAL INTERVIEW. You MUST ask ONLY technical questions related to the job description.\n"
            "DO NOT ask:\n"
            "- Personal questions (hobbies, family, personal background)\n"
            "- Behavioral questions unrelated to technical skills\n"
            "- General conversation topics\n"
            "- Questions about salary, benefits, or company culture\n"
            "- Any non-technical questions\n\n"
            "CRITICAL - QUESTION UNIQUENESS:\n"
            "- Each question MUST be completely unique and different from all previous questions\n"
            "- DO NOT repeat any question that has been asked before\n"
            "- DO NOT ask the same question with slightly different wording\n"
            "- DO NOT ask about the same topic that was already covered\n"
            "- You MUST ask a NEW question on a DIFFERENT technical topic or aspect\n\n"
            "Ask a warm, professional TECHNICAL introduction question to start the interview. "
            "The question should be related to technical skills, experience, or knowledge mentioned in the job description. "
            "Keep it conversational and friendly, but TECHNICAL. Ask only one concise, single-line TECHNICAL question."
        )
    
    elif question_type == "follow_up":
        prompt = (
            "You are a professional technical interviewer conducting a TECHNICAL INTERVIEW. Ask only single-line, direct TECHNICAL questions.\n\n"
            f"Job Description Context: {jd_context}\n\n"
            "Interview so far:\n"
            f"{conversation_context}\n\n"
            f"{previously_asked}"
            "CRITICAL: This is a TECHNICAL INTERVIEW. You MUST ask ONLY technical questions related to the job description.\n"
            "DO NOT ask:\n"
            "- Personal questions (hobbies, family, personal background)\n"
            "- Behavioral questions unrelated to technical skills\n"
            "- General conversation topics\n"
            "- Questions about salary, benefits, or company culture\n"
            "- Any non-technical questions\n\n"
            "CRITICAL - QUESTION UNIQUENESS (READ CAREFULLY):\n"
            "- The candidate has ALREADY answered the previous question. Do NOT ask that question again.\n"
            "- You MUST ask a COMPLETELY NEW, DIFFERENT TECHNICAL question that has NEVER been asked before.\n"
            "- Check the list of previously asked questions above - DO NOT repeat ANY of them.\n"
            "- DO NOT ask the same question with different wording - it's still the SAME question.\n"
            "- DO NOT ask about the same topic that was already covered - move to a DIFFERENT topic.\n"
            "- Each question MUST be unique and cover a DIFFERENT technical aspect.\n\n"
            "Based on the candidate's last answer, ask a relevant TECHNICAL follow-up question grounded in the JD. "
            "CRITICAL RULES:\n"
            "1. NEVER repeat the previous question - the candidate has already answered it.\n"
            "2. NEVER say 'Thanks for asking' and then repeat the same question - this is wrong.\n"
            "3. NEVER use phrases like 'go ahead with your answer' or 'please go ahead' - they have already answered.\n"
            "4. You may use a brief introductory phrase like 'That's okay' or 'I understand' ONCE, but DO NOT repeat it.\n"
            "5. NEVER say phrases like 'That's okay, that's okay' or 'That's fine, that's fine' - this is repetitive and unprofessional.\n"
            "6. If their answer was solid, probe for technical details, impact, metrics, trade-offs, or examples on a COMPLETELY DIFFERENT TECHNICAL aspect.\n"
            "7. If it was brief, ask for clarification on a COMPLETELY DIFFERENT TECHNICAL point or a concrete technical example of something NEW.\n"
            "8. Keep it professional, TECHNICAL, JD-aligned, and ensure it's a COMPLETELY NEW TECHNICAL question.\n"
            "9. Before generating your question, verify it is NOT in the list of previously asked questions above and that it is TECHNICAL.\n"
            "10. REMEMBER: Each question must be UNIQUE and DIFFERENT from all previous questions.\n"
            "11. CRITICAL: Ask ONLY ONE single question. DO NOT ask two questions in a single response. If you generate multiple questions, only the first one will be used."
        )
    
    elif question_type == "closing":
        prompt = (
            "You are a professional interviewer wrapping up a technical interview. Ask only single-line questions.\n\n"
            f"Job Description Context: {jd_context}\n\n"
            "Interview so far:\n"
            f"{conversation_context}\n\n"
            "Generate a professional closing question to ask the candidate if they have any questions. "
            "This should be a natural transition to end the interview. "
            "Examples: 'Before we wrap up, do you have any questions for us?' or 'Is there anything you'd like to ask about the role or company?' "
            "Keep it warm, professional, and concise. Ask only one single-line question."
        )
    
    else:  # regular question
        prompt = (
            "You are a professional technical interviewer conducting a TECHNICAL INTERVIEW. Ask only single-line TECHNICAL questions.\n\n"
            f"Job Description Context: {jd_context}\n\n"
            "Interview so far:\n"
            f"{conversation_context}\n\n"
            f"{previously_asked}"
            "CRITICAL: This is a TECHNICAL INTERVIEW. You MUST ask ONLY technical questions related to the job description.\n"
            "DO NOT ask:\n"
            "- Personal questions (hobbies, family, personal background)\n"
            "- Behavioral questions unrelated to technical skills\n"
            "- General conversation topics\n"
            "- Questions about salary, benefits, or company culture\n"
            "- Any non-technical questions\n\n"
            "CRITICAL - QUESTION UNIQUENESS (READ CAREFULLY):\n"
            "- The candidate has ALREADY answered the previous question. Do NOT ask that question again.\n"
            "- You MUST ask a COMPLETELY NEW, DIFFERENT TECHNICAL question that has NEVER been asked before.\n"
            "- Check the list of previously asked questions above - DO NOT repeat ANY of them.\n"
            "- DO NOT ask the same question with different wording - it's still the SAME question.\n"
            "- DO NOT ask about the same topic that was already covered - move to a DIFFERENT topic.\n"
            "- Each question MUST be unique and cover a DIFFERENT technical aspect.\n\n"
            f"Ask the next TECHNICAL interview question (question {session.current_question_number + 1} of {session.max_questions}). "
            "CRITICAL RULES - READ CAREFULLY:\n"
            "1. NEVER repeat the previous question - the candidate has already answered it.\n"
            "2. NEVER say 'Thanks for asking' and then repeat the same question - this is wrong.\n"
            "3. NEVER use phrases like 'go ahead with your answer', 'please go ahead', or similar phrases - they have already answered.\n"
            "4. You MUST ask a COMPLETELY NEW, DIFFERENT TECHNICAL question that has NOT been asked before.\n"
            "5. Check the list of previously asked questions above - DO NOT repeat any of them.\n"
            "6. Base your question on the TECHNICAL aspects of the job description and the candidate's latest answer, but ensure it's a NEW TECHNICAL topic or aspect.\n"
            "7. NEVER repeat a question that has already been asked - even if you rephrase it slightly.\n"
            "8. NEVER ask a similar question on the same topic - move to a DIFFERENT TECHNICAL topic or aspect.\n"
            "9. Keep it precise, professional, TECHNICAL, and directly tied to the JD's technical requirements, but ensure it's COMPLETELY NEW.\n"
            "10. Before generating your question, verify it is NOT in the list of previously asked questions above and that it is TECHNICAL.\n"
            "11. If you're unsure, choose a DIFFERENT TECHNICAL topic from the job description that hasn't been covered yet.\n"
            "12. REMEMBER: Each question must be UNIQUE and DIFFERENT from all previous questions.\n"
            "13. CRITICAL: Ask ONLY ONE single question. DO NOT ask two questions in a single response. If you generate multiple questions, only the first one will be used."
        )
    
    # Generate question with retry logic to avoid duplicates
    max_retries = 5  # Increased retries for better duplicate prevention
    for attempt in range(max_retries):
        generated_question = gemini_generate(prompt).strip()
        
        # CRITICAL: Shape the question to ensure only ONE question is returned
        # This is especially important when candidate's answer is "No answer provided"
        ensure_intro = (question_type == "introduction")
        generated_question = _shape_question(generated_question, ensure_intro=ensure_intro)
        
        # Check if this question is similar to previously asked questions (only if not allowing elaboration)
        if not allow_elaboration and session.asked_questions:
            if is_question_similar(generated_question, session.asked_questions):
                print(f"⚠️ Generated question is similar to previous questions. Retrying... (attempt {attempt + 1}/{max_retries})")
                print(f"   Generated: '{generated_question[:100]}...'")
                print(f"   Similar to one of {len(session.asked_questions)} previously asked questions")
                if attempt < max_retries - 1:
                    # Add STRONG instruction to generate a different question
                    prompt += f"\n\n{'='*80}\n"
                    prompt += f"❌ ERROR: The question you just generated is TOO SIMILAR to questions already asked.\n"
                    prompt += f"Generated question: '{generated_question}'\n"
                    prompt += f"This question is similar to one of the {len(session.asked_questions)} previously asked questions.\n"
                    prompt += f"CRITICAL: You MUST generate a COMPLETELY DIFFERENT question.\n"
                    prompt += f"DO NOT:\n"
                    prompt += f"- Ask the same question with different wording (it's still the SAME question)\n"
                    prompt += f"- Ask about the same topic (even with different words)\n"
                    prompt += f"- Ask a similar question (it's still a REPEAT)\n"
                    prompt += f"- Say 'Thanks for asking' and repeat the question (this is WRONG)\n"
                    prompt += f"DO:\n"
                    prompt += f"- Choose a COMPLETELY DIFFERENT topic from the job description\n"
                    prompt += f"- Ask about a DIFFERENT technical aspect or skill that hasn't been covered\n"
                    prompt += f"- Ensure your question is UNIQUE and has NOT been asked before\n"
                    prompt += f"- Move to a NEW technical area from the job description\n"
                    prompt += f"Generate a NEW question NOW that is COMPLETELY DIFFERENT from all previously asked questions.\n"
                    prompt += f"REMEMBER: Each question must be UNIQUE. Do NOT repeat any question.\n"
                    prompt += f"{'='*80}\n"
                    continue
                else:
                    print(f"⚠️ Could not generate a unique question after {max_retries} attempts. Using generated question anyway.")
        
        # Additional check: ensure the question is not identical to the last active question
        if session.last_active_question_text:
            normalized_new = " ".join(generated_question.lower().split())
            normalized_last = " ".join(session.last_active_question_text.lower().split())
            if normalized_new == normalized_last:
                print(f"⚠️ Generated question is IDENTICAL to last question. Retrying... (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    prompt += f"\n\n❌ CRITICAL ERROR: You generated the EXACT same question as the last one: '{generated_question}'\n"
                    prompt += f"The candidate has ALREADY answered this question. You MUST NOT repeat it.\n"
                    prompt += f"NEVER say 'Thanks for asking' and then repeat the same question - this is WRONG.\n"
                    prompt += f"Generate a COMPLETELY DIFFERENT question on a DIFFERENT technical topic.\n"
                    prompt += f"Choose a NEW technical aspect from the job description that hasn't been covered yet.\n"
                    continue
        
        return generated_question
    
    return generated_question


# ------------------ Routes (from app.py lines 793-830) ------------------
def start_interview(candidate_name: str, jd_text: str, max_questions: int = 4) -> Dict:
    """Exact copy from app.py /start endpoint"""
    try:
        if not jd_text.strip():
            return {"error": "Job description is required"}
        
        # Create new session
        session_id = str(uuid.uuid4())
        session = InterviewSession(session_id, candidate_name, jd_text, max_questions=max_questions)
        sessions[session_id] = session
        
        # Generate introduction question
        question = generate_question(session, "introduction")
        session.add_interviewer_message(question)
        session.current_question_number = 1  # Start at 1 (introduction is question 1)
        session.awaiting_answer = True
        session.last_active_question_text = question
        # Introduction is counted as a regular question for ratio tracking
        session.regular_questions_count = 1
        _reset_question_timers(session)
        
        # Generate audio
        audio_url = text_to_speech(question, f"q{session.current_question_number}.mp3")
        
        print(f"🎯 Starting interview with max_questions={session.max_questions}, current_question_number={session.current_question_number}")

        return {
            "session_id": session_id,
            "question": question,
            "audio_url": audio_url,
            "question_number": session.current_question_number,
            "max_questions": session.max_questions
        }
    except Exception as e:
        print(f"❌ Error in /start: {e}")
        return {"error": str(e)}


# ------------------ Upload Answer (from app.py lines 832-1259) - COMPLETE VERSION ------------------
def upload_answer(session_id: str, transcript: str, silence_flag: bool = False, had_voice_flag: bool = False) -> Dict:
    """Complete version from app.py /upload_answer endpoint with ALL logic"""
    try:
        if not session_id or session_id not in sessions:
            return {"error": "Invalid session ID"}
        
        session = sessions[session_id]
        
        # If interview already completed, don't accept further answers
        if session.is_completed:
            return {
                "transcript": "[Session already completed]",
                "completed": True,
                "message": "Interview completed. Thank you for your time!"
            }
        
        # Prefer transcript sent from UI - keep as-is from Deepgram (empty if no speech)
        transcript = (transcript or "").strip()
        print(f"🗒️ /upload_answer: session={session_id}, transcript_len={len(transcript)}")
        
        # Keep empty transcript as empty string (don't convert to "[No speech detected]")
        # This will be sent to LLM to generate appropriate response
        session.add_candidate_message(transcript if transcript else "")
        print(f"💾 Saved candidate message: '{(transcript[:120] + ('...' if len(transcript) > 120 else ''))}'")
        
        # If we received content, we are no longer awaiting an answer
        if transcript.strip() and not transcript.startswith("["):
            session.awaiting_answer = False
        
        print(f"📶 Client flags: silence={silence_flag}, had_voice={had_voice_flag}")

        # ------------------ Activity tracking & timing-based flow ------------------
        now_ts = time.time()
        current_word_count = _count_words(transcript)
        if current_word_count > session.last_transcript_word_count:
            session.last_transcript_update_at = now_ts
            session.last_transcript_word_count = current_word_count
            if session.first_voice_at is None and current_word_count > 0:
                session.first_voice_at = now_ts

        # REMOVED: Auto-advance functionality - no longer automatically moves to next question
        # Users must explicitly submit their answer or click "Done" to proceed
        
        # If in closing Q&A phase
        if session.asked_for_questions and not session.is_completed:
            transcript_lower = transcript.lower()
            no_resp = (not transcript.strip()) or transcript.startswith("[No speech") or (silence_flag and not had_voice_flag)
            
            # Check if candidate says no or doesn't have questions
            if no_resp or says_no_more_questions(transcript):
                final_text = generate_final_closing(session)
                final_audio = text_to_speech(final_text, f"final_{uuid.uuid4().hex}.mp3")
                session.add_interviewer_message(final_text)
                session.completed_at = time.time()
                session.is_completed = True
                session.waiting_for_candidate_question = False
                return {
                    "transcript": transcript,
                    "completed": True,
                    "final_message": final_text,
                    "final_audio_url": final_audio
                }

            # If we're waiting for the candidate's question (after they said yes)
            if session.waiting_for_candidate_question:
                # Candidate provided their question - answer it
                # IMPORTANT: Candidate questions are NOT counted in the overall question count
                answer_text = generate_candidate_answer(session, transcript)
                session.add_interviewer_message(answer_text)
                session.waiting_for_candidate_question = False
                
                # After answering, ask if they have more questions
                # NOTE: We do NOT increment question_number or question counters for candidate Q&A
                prompt_again = "Do you have any other questions for us?"
                combined = f"{answer_text} {prompt_again}".strip()
                session.add_interviewer_message(combined)
                question_audio_url = text_to_speech(combined, f"closing_{uuid.uuid4().hex}.mp3")
                _reset_question_timers(session)
                return {
                    "transcript": transcript,
                    "completed": False,
                    "next_question": combined,
                    "audio_url": question_audio_url,
                    "question_number": session.current_question_number,  # Keep same question number - not a new interview question
                    "max_questions": session.max_questions,
                    "continuous": True
                }

            # Check if candidate explicitly says NO (only end interview if they say no)
            says_no = says_no_more_questions(transcript)
            
            if says_no:
                # Candidate explicitly said no - end the interview
                final_text = generate_final_closing(session)
                final_audio = text_to_speech(final_text, f"final_{uuid.uuid4().hex}.mp3")
                session.add_interviewer_message(final_text)
                session.completed_at = time.time()
                session.is_completed = True
                session.waiting_for_candidate_question = False
                return {
                    "transcript": transcript,
                    "completed": True,
                    "final_message": final_text,
                    "final_audio_url": final_audio
                }
            
            # Check if candidate says yes or asks a question directly
            says_yes = any(phrase in transcript_lower for phrase in [
                "yes", "yeah", "yep", "sure", "i do", "i have", "i'd like", "i would like"
            ])
            
            # Check if it looks like a direct question (contains question words or ends with ?)
            looks_like_question = any(word in transcript_lower for word in [
                "what", "when", "where", "who", "why", "how", "which", "can", "could", "would", "should"
            ]) or "?" in transcript
            
            if says_yes or looks_like_question:
                if says_yes and not looks_like_question:
                    # Candidate said yes but didn't ask a question yet - ask them what their question is
                    ask_question = "What is your question?"
                    session.add_interviewer_message(ask_question)
                    session.waiting_for_candidate_question = True
                    question_audio_url = text_to_speech(ask_question, f"ask_question_{uuid.uuid4().hex}.mp3")
                    _reset_question_timers(session)
                    return {
                        "transcript": transcript,
                        "completed": False,
                        "next_question": ask_question,
                        "audio_url": question_audio_url,
                        "question_number": session.current_question_number,
                        "max_questions": session.max_questions,
                        "continuous": True
                    }
                else:
                    # Candidate asked a question directly - answer it
                    # IMPORTANT: Candidate questions are NOT counted in the overall question count
                    answer_text = generate_candidate_answer(session, transcript)
                    session.add_interviewer_message(answer_text)
                    
                    # After answering, ask if they have more questions
                    # NOTE: We do NOT increment question_number or question counters for candidate Q&A
                    prompt_again = "Do you have any other questions for us?"
                    combined = f"{answer_text} {prompt_again}".strip()
                    session.add_interviewer_message(combined)
                    question_audio_url = text_to_speech(combined, f"closing_{uuid.uuid4().hex}.mp3")
                    _reset_question_timers(session)
                    return {
                        "transcript": transcript,
                        "completed": False,
                        "next_question": combined,
                        "audio_url": question_audio_url,
                        "question_number": session.current_question_number,  # Keep same question number - not a new interview question
                        "max_questions": session.max_questions,
                        "continuous": True
                    }
            else:
                # Candidate gave an answer that's not clearly "yes", "no", or a question
                # This might be a response like "thank you", "that's all", or other ambiguous responses
                # Ask them again if they have any questions to clarify
                prompt_again = "Do you have any other questions for us?"
                session.add_interviewer_message(prompt_again)
                question_audio_url = text_to_speech(prompt_again, f"closing_clarify_{uuid.uuid4().hex}.mp3")
                _reset_question_timers(session)
                return {
                    "transcript": transcript,
                    "completed": False,
                    "next_question": prompt_again,
                    "audio_url": question_audio_url,
                    "question_number": session.current_question_number,
                    "max_questions": session.max_questions,
                    "continuous": True
                }
        
        # Handle voice commands
        transcript_lower = transcript.lower()
        
        # Proceed-confirmation flow
        last_interviewer = session.get_last_interviewer_question() or ""
        if is_proceed_prompt_text(last_interviewer):
            if is_affirmative_response(transcript):
                # Use ratio logic to decide follow-up vs regular
                should_follow_up = should_ask_follow_up(session, transcript)
                if should_follow_up:
                    next_q_text = generate_question(session, "follow_up", last_answer_text=transcript)
                    session.follow_up_questions_count += 1
                else:
                    next_q_text = generate_question(session, "regular", last_answer_text=transcript)
                    session.regular_questions_count += 1
                session.add_interviewer_message(next_q_text)
                session.current_question_number += 1
                session.awaiting_answer = True
                session.last_active_question_text = next_q_text
                audio_url = text_to_speech(next_q_text, f"q{session.current_question_number}.mp3")
                _reset_question_timers(session)
                return {
                    "transcript": transcript,
                    "completed": False,
                    "next_question": next_q_text,
                    "audio_url": audio_url,
                    "question_number": session.current_question_number,
                    "max_questions": session.max_questions,
                    "continuous": True
                }
            elif is_negative_response(transcript):
                last_q = get_last_strict_question(session)
                if last_q:
                    session.add_interviewer_message(last_q)
                    session.awaiting_answer = True
                    session.last_active_question_text = last_q
                    question_audio_url = text_to_speech(last_q, f"q{session.current_question_number}_repeat.mp3")
                    _reset_question_timers(session)
                    return {
                        "transcript": transcript,
                        "completed": False,
                        "next_question": last_q,
                        "audio_url": question_audio_url,
                        "question_number": session.current_question_number,
                        "max_questions": session.max_questions,
                        "continuous": True
                    }

        # Check if candidate is requesting to repeat the question using LLM
        # Send candidate response to LLM to determine if it's a repeat request
        last_question = get_last_strict_question(session)
        if last_question:
            # Use LLM to analyze if candidate is asking to repeat the question
            is_repeat = is_repeat_request_via_llm(session, transcript, last_question)
            
            if is_repeat:
                # Candidate is asking to repeat - use LLM to generate a natural response that repeats the question
                repeat_response = generate_repeat_question_response(session, last_question)
                session.add_interviewer_message(repeat_response)
                session.awaiting_answer = True
                session.last_active_question_text = last_question  # Keep original question as active
                repeat_audio_url = text_to_speech(repeat_response, f"q{session.current_question_number}_repeat.mp3")
                _reset_question_timers(session)
                print(f"🔄 LLM detected repeat request. Generated repeat response: {repeat_response[:100]}...")
                return {
                    "transcript": transcript,
                    "completed": False,
                    "next_question": repeat_response,
                    "audio_url": repeat_audio_url,
                    "question_number": session.current_question_number,  # Don't increment - same question
                    "max_questions": session.max_questions,
                    "continuous": True
                }
        
        # Regular skip command handling (for skips like "skip", "next question", "move on")
        if any(phrase in transcript_lower for phrase in ["skip", "next question", "move on"]):
            # For skip commands, default to regular question (no meaningful answer to evaluate)
            next_q_text = generate_question(session, "regular", last_answer_text=transcript)
            session.regular_questions_count += 1
            # Use the question directly without any reassuring phrases - be professional like a real technical interviewer
            combined_text = next_q_text.strip()
            session.add_interviewer_message(combined_text)
            session.current_question_number += 1
            session.awaiting_answer = True
            session.last_active_question_text = next_q_text
            audio_url = text_to_speech(combined_text, f"q{session.current_question_number}.mp3")
            _reset_question_timers(session)
            return {
                "transcript": transcript,
                "completed": False,
                "next_question": combined_text,
                "audio_url": audio_url,
                "question_number": session.current_question_number,
                "max_questions": session.max_questions,
                "continuous": True
            }
        
        # Check if transcript is empty (as-is from Deepgram API) - send to LLM to generate next context
        is_empty_transcript = not transcript.strip() or transcript.startswith("[Speech detected") or transcript.startswith("[No speech detected")
        
        if is_empty_transcript:
            # Send empty transcript (as-is from Deepgram) to LLM to generate appropriate response
            # LLM will decide: ask again, move to next question, or provide encouragement
            llm_prompt = (
                f"You are a professional technical interviewer conducting a technical interview. "
                f"The candidate's response was empty or not detected (transcript from Deepgram API is empty: '{transcript}'). "
                f"\n\n"
                f"Current interview context:\n"
                f"- Question number: {session.current_question_number} of {session.max_questions}\n"
                f"- Last question asked: {session.last_active_question_text[:200] if session.last_active_question_text else 'N/A'}\n"
                f"- Interview progress: {session.current_question_number}/{session.max_questions} questions completed\n"
                f"\n"
                f"Generate a brief, professional response (1-2 sentences) that:\n"
                f"1. Acknowledges the situation naturally\n"
                f"2. Either asks them to try again OR moves to the next question (your judgment)\n"
                f"3. Keeps the conversation flowing smoothly\n"
                f"4. Is encouraging and professional\n"
                f"\n"
                f"IMPORTANT:\n"
                f"- If this is early in the interview (question 1-2), ask them to try again\n"
                f"- If this is later (question 3+), you may move to the next question\n"
                f"- Be natural and conversational, NOT robotic\n"
                f"- Do NOT use phrases like 'I didn't catch that' - be more professional\n"
                f"\n"
                f"Generate ONLY the response text (no explanations, no quotes):"
            )
            
            llm_response = gemini_generate(llm_prompt, max_retries=3)
            
            if not llm_response or llm_response.startswith("[Gemini error"):
                # Fallback response
                if session.current_question_number <= 2:
                    llm_response = "I didn't catch your response. Could you please try again?"
                else:
                    llm_response = "Let's move on to the next question."
            
            # Check if LLM response indicates moving to next question
            move_to_next = any(phrase in llm_response.lower() for phrase in [
                "next question", "move on", "let's continue", "proceed", "move forward"
            ])
            
            if move_to_next:
                # LLM decided to move to next question
                session.add_interviewer_message(llm_response)
                next_question = generate_question(session, "regular", last_answer_text="")
                session.regular_questions_count += 1
                session.add_interviewer_message(next_question)
                session.current_question_number += 1
                session.awaiting_answer = True
                session.last_active_question_text = next_question
                
                # Combine LLM response with next question
                combined_response = f"{llm_response} {next_question}".strip()
                audio_url = text_to_speech(combined_response, f"q{session.current_question_number}.mp3")
                _reset_question_timers(session)
                return {
                    "transcript": transcript if transcript else "",
                    "completed": False,
                    "next_question": combined_response,
                    "audio_url": audio_url,
                    "question_number": session.current_question_number,
                    "max_questions": session.max_questions,
                    "continuous": True
                }
            else:
                # LLM decided to ask again
                session.add_interviewer_message(llm_response)
                acknowledge_audio = text_to_speech(llm_response, f"acknowledge_{uuid.uuid4().hex}.mp3")
                _reset_question_timers(session)
                return {
                    "transcript": transcript if transcript else "",
                    "completed": False,
                    "acknowledge": True,
                    "message": llm_response,
                    "audio_url": acknowledge_audio,
                    "question_number": session.current_question_number,
                    "max_questions": session.max_questions,
                    "continuous": True
                }

        # Handle unrelated answers
        try:
            last_q_text = get_last_strict_question(session)
        except Exception:
            last_q_text = ""

        # DISABLED: Too aggressive rephrasing - only ask for repeat on explicit commands
        ask_for_repeat = False
        # if is_elaboration_request(transcript) or is_repeat_request(transcript):
        #     ask_for_repeat = False
        # elif last_q_text:
        #     try:
        #         is_related = assess_answer_relevance_with_llm(last_q_text, transcript)
        #         ask_for_repeat = not is_related
        #     except Exception:
        #         ask_for_repeat = False

        if ask_for_repeat:
            clarify_line = generate_clarification_prompt_with_question(session)
            session.add_interviewer_message(clarify_line)
            session.awaiting_answer = True
            session.last_active_question_text = clarify_line
            clarify_audio = text_to_speech(clarify_line, f"clarify_{uuid.uuid4().hex}.mp3")
            _reset_question_timers(session)
            return {
                "transcript": transcript,
                "completed": False,
                "next_question": clarify_line,
                "audio_url": clarify_audio,
                "question_number": session.current_question_number,
                "max_questions": session.max_questions,
                "continuous": True
            }
        
        # If the candidate asked a question
        if is_candidate_question(transcript):
            elaboration_cues = [
                "elaborate", "elaboration", "explain", "more detail", "clarify", "clarification",
                "what do you mean", "could you expand", "expand on", "help me understand"
            ]
            t_lower = transcript.lower()
            wants_elaboration = any(cue in t_lower for cue in elaboration_cues)

            if wants_elaboration:
                elaborated = generate_elaborated_question(session, transcript)
                session.add_interviewer_message(elaborated)
                session.awaiting_answer = True
                session.last_active_question_text = elaborated
                elaborated_audio_url = text_to_speech(elaborated, f"q{session.current_question_number}_elab.mp3")
                _reset_question_timers(session)
                return {
                    "transcript": transcript,
                    "completed": False,
                    "next_question": elaborated,
                    "audio_url": elaborated_audio_url,
                    "question_number": session.current_question_number,
                    "max_questions": session.max_questions,
                    "continuous": True
                }

            # Answer the candidate question - respond to their question about the interview/role
            # IMPORTANT: Candidate questions are NOT counted in the overall question count
            answer_text = generate_candidate_answer(session, transcript)
            session.add_interviewer_message(answer_text)

            # After answering candidate's question, move to the NEXT question (do NOT repeat previous question)
            # Use ratio logic to decide follow-up vs regular
            should_follow_up = should_ask_follow_up(session, transcript)
            if should_follow_up:
                next_question = generate_question(session, "follow_up", last_answer_text=transcript, allow_elaboration=False)
                session.follow_up_questions_count += 1
            else:
                next_question = generate_question(session, "regular", last_answer_text=transcript, allow_elaboration=False)
                session.regular_questions_count += 1
            
            # CRITICAL CHECK: Ensure the generated question is NOT the same as the last question
            if session.last_active_question_text:
                normalized_new = " ".join(next_question.lower().split())
                normalized_last = " ".join(session.last_active_question_text.lower().split())
                if normalized_new == normalized_last:
                    print(f"⚠️ Generated question is IDENTICAL to last question after candidate Q&A. Regenerating...")
                    # Force a different question type
                    should_follow_up = not should_follow_up
                    if should_follow_up:
                        next_question = generate_question(session, "follow_up", last_answer_text=transcript, allow_elaboration=False)
                    else:
                        next_question = generate_question(session, "regular", last_answer_text=transcript, allow_elaboration=False)
            
            # Increment question number and add to conversation
            session.current_question_number += 1
            session.add_interviewer_message(next_question)
            session.awaiting_answer = True
            session.last_active_question_text = next_question
            audio_url = text_to_speech(next_question, f"q{session.current_question_number}.mp3")
            _reset_question_timers(session)
            
            # Return both answer and next question
            return {
                "transcript": transcript,
                "completed": False,
                "interviewer_answer": answer_text,
                "answer_audio_url": text_to_speech(answer_text, f"ans_{uuid.uuid4().hex}.mp3"),
                "next_question": next_question,
                "audio_url": audio_url,
                "question_number": session.current_question_number,
                "max_questions": session.max_questions,
                "continuous": True
            }

        # Check if interview is completed (regular flow)
        # max_questions represents the TOTAL number of questions including pre-closing and closing
        # So if max_questions is 4, we ask: 2 main + 1 pre-closing + 1 closing = 4 total
        # The introduction question is question 1, so we need to account for that
        # Calculate how many main questions we should ask AFTER introduction (max_questions - 3: intro + pre-closing + closing)
        # Example: if max_questions=4, we want: intro(1) + 1 main(2) + pre-closing(3) + closing(4) = 4 total
        main_questions_after_intro = max(0, session.max_questions - 3)  # Questions after intro, before pre-closing
        
        # Check if we've asked enough main questions (intro is 1, so we check if current > 1 + main_questions_after_intro)
        main_questions_limit = 1 + main_questions_after_intro  # Total main questions including intro
        
        print(f"📊 Question count check: current={session.current_question_number}, max={session.max_questions}, main_limit={main_questions_limit}, main_after_intro={main_questions_after_intro}")
        
        if session.current_question_number >= main_questions_limit:
            # First, ask one more question before the closing question (pre-closing question)
            if not session.asked_pre_closing_question:
                # Generate one more regular question before closing (pre-closing question)
                next_q_text = generate_question(session, "regular", last_answer_text=transcript)
                session.add_interviewer_message(next_q_text)
                session.current_question_number += 1
                session.regular_questions_count += 1  # Pre-closing is a regular question
                session.awaiting_answer = True
                session.last_active_question_text = next_q_text
                session.asked_pre_closing_question = True
                _reset_question_timers(session)
                question_audio_url = text_to_speech(next_q_text, f"q{session.current_question_number}.mp3")
                return {
                    "transcript": transcript,
                    "completed": False,
                    "next_question": next_q_text,
                    "audio_url": question_audio_url,
                    "question_number": session.current_question_number,
                    "max_questions": session.max_questions,  # Total questions including pre-closing and closing
                    "continuous": True
                }
            # After pre-closing question is answered, ask the closing question (generated dynamically)
            elif not session.asked_for_questions:
                # Normal flow: ask the closing question
                closing = generate_question(session, "closing", last_answer_text=transcript)
                session.add_interviewer_message(closing)
                session.current_question_number += 1
                session.awaiting_answer = True
                session.last_active_question_text = closing
                session.asked_for_questions = True
                _reset_question_timers(session)
                closing_audio = text_to_speech(closing, f"closing_{uuid.uuid4().hex}.mp3")
                return {
                    "transcript": transcript,
                    "completed": False,
                    "next_question": closing,
                    "audio_url": closing_audio,
                    "question_number": session.current_question_number,
                    "max_questions": session.max_questions,  # Total questions including pre-closing and closing
                    "continuous": True
                }
            # Already in closing phase - generate final closing statement
            final_closing = generate_final_closing(session)
            session.add_interviewer_message(final_closing)
            print(f"🎬 Final closing statement: {final_closing}")
            
            # Generate audio for closing statement
            closing_audio = text_to_speech(final_closing, f"final_closing_{uuid.uuid4().hex}.mp3")
            
            session.completed_at = time.time()
            session.is_completed = True
            return {
                "transcript": transcript,
                "completed": True,
                "message": final_closing,  # Use the generated closing message
                "audio_url": closing_audio,  # Include audio for the closing statement
                "next_question": final_closing  # Also include as next_question for display
            }
        
        # Gate moving to next question until 5s of no new words after first voice
        if session.awaiting_answer and session.first_voice_at is not None:
            last_update = session.last_transcript_update_at or session.first_voice_at
            if (now_ts - last_update) < 5.0:
                return {
                    "transcript": transcript,
                    "completed": False,
                    "acknowledge": True,
                    "message": "Listening...",
                    "question_number": session.current_question_number,
                    "max_questions": session.max_questions,
                    "continuous": True
                }

        # Generate next question
        # Check if we've reached the limit for main questions (excluding pre-closing and closing)
        # The introduction question is question 1, so we need to account for that
        main_questions_after_intro = max(0, session.max_questions - 3)  # Questions after intro, before pre-closing
        main_questions_limit = 1 + main_questions_after_intro  # Total main questions including intro
        
        if session.current_question_number >= main_questions_limit:
            # We've reached the limit, should have been handled above
            # This shouldn't happen, but just in case, return error
            print(f"⚠️ WARNING: Reached main questions limit ({main_questions_limit}) but didn't trigger pre-closing")
            print(f"   Current: {session.current_question_number}, Max: {session.max_questions}")
            return {
                "transcript": transcript,
                "completed": False,
                "error": "Question limit reached"
            }
        
        # Decide whether to ask follow-up or regular question based on:
        # 1. Answer quality (broad/vague)
        # 2. JD context match
        # 3. Ratio constraint (30% follow-up, 70% regular)
        should_follow_up = should_ask_follow_up(session, transcript)
        
        # CRITICAL: Mark that the candidate has answered the previous question
        # The candidate has provided an answer, so we should move to the NEXT question
        session.awaiting_answer = False
        print(f"✅ Candidate provided answer. Moving to next question. Previous question was: '{session.last_active_question_text[:100] if session.last_active_question_text else 'None'}...'")
        print(f"📋 Previously asked questions count: {len(session.asked_questions)}")
        
        # IMPORTANT: When candidate is answering (not asking for elaboration), always generate a NEW question
        # Do NOT repeat the same question - move to the next question
        max_generation_attempts = 5
        next_question = None
        for gen_attempt in range(max_generation_attempts):
            if should_follow_up:
                next_question = generate_question(session, "follow_up", last_answer_text=transcript, allow_elaboration=False)
                if gen_attempt == 0:
                    session.follow_up_questions_count += 1
            else:
                next_question = generate_question(session, "regular", last_answer_text=transcript, allow_elaboration=False)
                if gen_attempt == 0:
                    session.regular_questions_count += 1
            
            # CRITICAL CHECK: Ensure the generated question is NOT the same as the last question
            if session.last_active_question_text:
                normalized_new = " ".join(next_question.lower().split())
                normalized_last = " ".join(session.last_active_question_text.lower().split())
                if normalized_new == normalized_last:
                    print(f"⚠️ ATTEMPT {gen_attempt + 1}/{max_generation_attempts}: Generated question is IDENTICAL to last question!")
                    print(f"   Last question: '{session.last_active_question_text[:100]}...'")
                    print(f"   Generated: '{next_question[:100]}...'")
                    if gen_attempt < max_generation_attempts - 1:
                        # Force a different question type to ensure uniqueness
                        should_follow_up = not should_follow_up
                        continue
                    else:
                        print(f"❌ ERROR: Could not generate a different question after {max_generation_attempts} attempts!")
                        # Still use it but log the error
                        break
                else:
                    # Question is different, proceed
                    break
            else:
                # No last question, proceed
                break
        
        # Additional check: Verify the question is not in asked_questions list
        normalized_next = " ".join(next_question.lower().split())
        if normalized_next in session.asked_questions:
            print(f"⚠️ WARNING: Generated question is already in asked_questions list! Regenerating...")
            # Force regeneration with different type
            should_follow_up = not should_follow_up
            if should_follow_up:
                next_question = generate_question(session, "follow_up", last_answer_text=transcript, allow_elaboration=False)
            else:
                next_question = generate_question(session, "regular", last_answer_text=transcript, allow_elaboration=False)
        
        # Final verification: Ensure this question is truly new
        normalized_final = " ".join(next_question.lower().split())
        if normalized_final in session.asked_questions:
            print(f"❌ CRITICAL ERROR: Question is already in asked_questions! This should not happen!")
            print(f"   Question: '{next_question[:100]}...'")
            print(f"   Asked questions: {session.asked_questions}")
            # Force a completely different question by using a different approach
            # Use a generic question that's definitely not in the list
            next_question = generate_question(session, "regular" if should_follow_up else "follow_up", last_answer_text="", allow_elaboration=False)
            normalized_final = " ".join(next_question.lower().split())
            if normalized_final in session.asked_questions:
                print(f"❌ ERROR: Even after regeneration, question is still duplicate!")
        
        # Increment question number FIRST (so it reflects the question we're about to ask)
        new_question_number = session.current_question_number + 1
        session.current_question_number = new_question_number
        print(f"🤖 Generated NEW question {new_question_number}/{session.max_questions}: '{next_question[:100]}...'")
        print(f"📋 Total asked questions before adding this: {len(session.asked_questions)}")
        print(f"📊 Question number set to: {new_question_number}")
        
        # Add the question to conversation and track it (this will add it to asked_questions)
        session.add_interviewer_message(next_question)
        print(f"📋 Total asked questions after adding: {len(session.asked_questions)}")
        
        # Update state
        session.awaiting_answer = True  # Now waiting for answer to this NEW question
        session.last_active_question_text = next_question  # Update last active question
        
        print(f"📊 Question progress: {session.current_question_number}/{session.max_questions} (main limit: {main_questions_limit})")
        
        audio_url = text_to_speech(next_question, f"q{session.current_question_number}.mp3")
        _reset_question_timers(session)

        return {
            "transcript": transcript,
            "completed": False,
            "next_question": next_question,
            "audio_url": audio_url,
            "question_number": session.current_question_number,
            "max_questions": session.max_questions,
            "continuous": True
        }
    except Exception as e:
        print(f"❌ Error in /upload_answer: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


def repeat_question(session_id: str) -> Dict:
    """Exact copy from app.py /repeat endpoint"""
    try:
        if not session_id or session_id not in sessions:
            return {"error": "Invalid session ID"}
        
        session = sessions[session_id]
        last_q = get_last_strict_question(session)
        
        if not last_q:
            return {"error": "No previous question found"}

        audio_url = text_to_speech(last_q, f"repeat_{uuid.uuid4().hex}.mp3")
        _reset_question_timers(session)
        return {
            "next_question": last_q,
            "audio_url": audio_url,
            "question_number": session.current_question_number,
            "max_questions": session.max_questions
        }
    except Exception as e:
        print(f"❌ Error in /repeat: {e}")
        return {"error": str(e)}

