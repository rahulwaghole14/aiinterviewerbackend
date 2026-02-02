import os
import io
import uuid
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

from django.conf import settings

try:
    import google.generativeai as genai
except Exception:  # pragma: no cover - optional at runtime
    genai = None

try:
    from google.cloud import texttospeech  # type: ignore
except Exception:  # pragma: no cover - optional at runtime
    texttospeech = None

# Optional dependencies for RAG
try:
    import faiss  # type: ignore
except Exception:  # pragma: no cover
    faiss = None

try:
    from sentence_transformers import SentenceTransformer  # type: ignore
except Exception:  # pragma: no cover
    SentenceTransformer = None

import numpy as np


# Configure Gemini - Get API key from Django settings
from django.conf import settings as django_settings
_GEMINI_KEY = getattr(django_settings, 'GEMINI_API_KEY', '')
if genai:
    try:
        genai.configure(api_key=_GEMINI_KEY)
        print(f"✅ Gemini API configured successfully")
    except Exception as e:
        print(f"❌ Gemini configuration failed: {e}")
        pass


# Upload directory for generated audio files
AI_UPLOADS_SUBDIR = "ai_uploads"
AI_UPLOADS_DIR = os.path.join(getattr(settings, "MEDIA_ROOT", "media"), AI_UPLOADS_SUBDIR)
os.makedirs(AI_UPLOADS_DIR, exist_ok=True)


def _sanitize_filename(name: str) -> str:
    base = "".join(c for c in name if c.isalnum() or c in ("-", "_", "."))
    return base or uuid.uuid4().hex


class RAGSystem:
    def __init__(self) -> None:
        self.model = None
        if SentenceTransformer is not None:
            try:
                self.model = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception:
                self.model = None
        self.dimension = 384
        self.index = None
        self.jd_chunks: List[str] = []
        self.is_initialized = False

    def process_jd(self, jd_text: str) -> None:
        sentences = [s.strip() for s in jd_text.split(". ") if s.strip()]
        self.jd_chunks = [f"{s}." if not s.endswith(".") else s for s in sentences]

        if self.model is not None and faiss is not None:
            try:
                embeddings = self.model.encode(self.jd_chunks).astype("float32")
                self.index = faiss.IndexFlatL2(embeddings.shape[1])
                self.index.add(embeddings)
            except Exception:
                self.index = None
        else:
            # Fallback: random vectors to keep flow working
            self.index = None
        self.is_initialized = True

    def retrieve_context(self, query: str, top_k: int = 3) -> List[str]:
        if not self.is_initialized:
            return []
        if self.model is not None and self.index is not None and faiss is not None:
            try:
                q = self.model.encode([query]).astype("float32")
                _, idx = self.index.search(q, top_k)
                return [self.jd_chunks[i] for i in idx[0] if 0 <= i < len(self.jd_chunks)]
            except Exception:
                pass
        # Fallback: return first K chunks
        return self.jd_chunks[:top_k]


def _gemini_generate(prompt: str) -> str:
    if not (genai and _GEMINI_KEY):
        return "Could not generate a response."
    try:
        # Use gemini-2.0-flash for interview questions
        model = genai.GenerativeModel("gemini-2.0-flash")
        resp = model.generate_content(prompt)
        return getattr(resp, "text", "") or "Could not generate a response."
    except Exception as e:
        print(f"❌ Gemini error: {e}")
        return f"[Gemini error: {str(e)}]"


def _text_to_speech(text: str, filename: str) -> str:
    safe_name = _sanitize_filename(filename)
    if not safe_name.lower().endswith(".mp3"):
        safe_name = f"{os.path.splitext(safe_name)[0]}.mp3"
    out_path = os.path.join(AI_UPLOADS_DIR, safe_name)

    # Prefer Google Cloud TTS if configured
    if texttospeech is not None:
        try:
            client = texttospeech.TextToSpeechClient()
            synthesis_input = texttospeech.SynthesisInput(text=text)
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-IN",
                ssml_gender=texttospeech.SsmlVoiceGender.MALE,
            )
            audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
            response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
            with open(out_path, "wb") as f:
                f.write(response.audio_content)
            return f"{getattr(settings, 'MEDIA_URL', '/media/').rstrip('/')}/{AI_UPLOADS_SUBDIR}/{safe_name}"
        except Exception:
            pass

    # Graceful fallback: create empty file to keep flow predictable
    try:
        with open(out_path, "wb") as f:
            f.write(b"")
    except Exception:
        pass
    return f"{getattr(settings, 'MEDIA_URL', '/media/').rstrip('/')}/{AI_UPLOADS_SUBDIR}/{safe_name}"


@dataclass
class ChatSession:
    session_id: str
    candidate_name: str
    jd_text: str
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    current_question_number: int = 0
    max_questions: int = 4
    is_completed: bool = False
    asked_for_questions: bool = False
    in_qa_phase: bool = False
    last_active_question_text: str = ""
    question_asked_at: float = 0.0

    def add_interviewer(self, text: str) -> None:
        self.conversation_history.append({"role": "interviewer", "text": text})

    def add_candidate(self, text: str) -> None:
        self.conversation_history.append({"role": "candidate", "text": text})

    def last_interviewer_question(self) -> str:
        for msg in reversed(self.conversation_history):
            if msg.get("role") == "interviewer":
                return msg.get("text", "")
        return ""

    def context_text(self) -> str:
        return "\n".join(f"{m['role']}: {m['text']}" for m in self.conversation_history)


class ChatBotManager:
    def __init__(self) -> None:
        self.sessions: Dict[str, ChatSession] = {}
        self.rag = RAGSystem()
        self._question_hints = (
            "can you", "could you", "would you", "what is", "what's",
            "why", "how", "where", "when", "help me", "explain", "clarify",
            "tell me", "show me", "walk me", "give me", "answer", "do you"
        )

    def _shape_question(self, text: str, ensure_intro: bool = False) -> str:
        """Ensure a concise 1-3 line question."""
        fallback_intro = "Could you briefly introduce yourself and mention one relevant experience?"
        fallback_regular = "Could you describe a recent technical project you worked on?"
        cleaned = (text or "").strip()
        cleaned = " ".join(cleaned.split())
        if not cleaned:
            cleaned = fallback_intro if ensure_intro else fallback_regular

        # Split into sentences and keep only first 1-2 sentences
        sentences = [s.strip() for s in cleaned.split('.') if s.strip()]
        if len(sentences) > 2:
            cleaned = '. '.join(sentences[:2]) + '.'
        
        # Ensure it ends with a question mark
        if not cleaned.endswith("?"):
            if cleaned.endswith("."):
                cleaned = cleaned[:-1] + "?"
            else:
                cleaned = cleaned + "?"

        # Limit to reasonable length (max 200 characters)
        if len(cleaned) > 200:
            cleaned = cleaned[:197] + "...?"

        if ensure_intro:
            intro_keywords = ("introduce yourself", "introduction", "background", "yourself", "tell me about")
            if not any(kw in cleaned.lower() for kw in intro_keywords):
                cleaned = fallback_intro

        return cleaned

    def _generate_candidate_response(self, session: ChatSession, candidate_question: str) -> str:
        """Provide clarifying response while refusing to reveal answers outright."""
        prompt = (
            f"Candidate asked: {candidate_question.strip()}\n\n"
            "Respond in 1-2 sentences. Clarify if needed, but don't give answers. "
            "Ask them to continue with their own approach."
        )
        response = _gemini_generate(prompt).strip()
        if not response:
            response = "I can clarify the requirements, but please walk me through your approach."
        return response

    def _generate_company_response(self, session: ChatSession, candidate_question: str) -> str:
        """Generate response to candidate's question about company or job role."""
        prompt = (
            f"You are an interviewer responding to a candidate's question about the company or job role.\n"
            f"Job Description Context: {session.jd_text[:500]}...\n\n"
            f"Candidate question: {candidate_question.strip()}\n\n"
            "Respond professionally in 1-3 sentences. Answer only if related to the job, company culture, "
            "benefits, or role responsibilities. If not related, politely decline and redirect to job-related topics."
        )
        response = _gemini_generate(prompt).strip()
        if not response:
            response = "I'd be happy to answer questions about the role or company. Could you ask something related to the position?"
        return response

    def _is_job_related_question(self, question: str, jd_text: str) -> bool:
        """Check if question is related to job, company, or role."""
        job_related_keywords = [
            'company', 'team', 'culture', 'benefits', 'salary', 'compensation', 
            'role', 'responsibilities', 'work', 'project', 'technology', 'stack',
            'opportunity', 'growth', 'career', 'position', 'job', 'interview',
            'next steps', 'timeline', 'decision', 'hiring', 'process'
        ]
        
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in job_related_keywords)

    def _generate_question(self, session: ChatSession, qtype: str = "regular", last_answer: Optional[str] = None) -> str:
        print(f"🔍 Generating {qtype} question for candidate: {session.candidate_name}")
        
        chunks = []
        if last_answer:
            chunks = self.rag.retrieve_context(last_answer, top_k=5)
        if not chunks:
            chunks = self.rag.retrieve_context("job requirements and responsibilities", top_k=5)
        jd_ctx = " ".join(chunks)
        conv = session.context_text()
        
        print(f"🔍 JD context length: {len(jd_ctx)}, conversation length: {len(conv)}")

        if qtype == "introduction":
            prompt = (
                f"Candidate: {session.candidate_name}\n"
                f"Job: {jd_ctx[:200]}...\n\n"
                "Ask a brief 1-2 line introduction question."
            )
        elif qtype == "follow_up":
            prompt = (
                f"Previous answer: {last_answer[:150]}...\n"
                f"Job context: {jd_ctx[:200]}...\n\n"
                "Ask a brief 1-2 line follow-up question."
            )
        else:
            prompt = (
                f"Conversation: {conv[-300:] if len(conv) > 300 else conv}\n"
                f"Job: {jd_ctx[:200]}...\n\n"
                "Ask a brief 1-2 line technical question."
            )

        print(f"🔍 Sending prompt to Gemini (length: {len(prompt)})")
        text = _gemini_generate(prompt).strip()
        ensure_intro = qtype == "introduction"
        text = self._shape_question(text, ensure_intro=ensure_intro)
        print(f"🔍 Gemini response: {text[:100]}...")
        return text or "Please describe a recent project you are proud of."

    def start(self, candidate_name: str, jd_text: str, max_questions: int = 4) -> Dict[str, object]:
        if not jd_text.strip():
            return {"error": "Job description is required"}
        self.rag.process_jd(jd_text)
        sid = uuid.uuid4().hex
        session = ChatSession(session_id=sid, candidate_name=candidate_name or "Candidate", jd_text=jd_text, max_questions=max_questions)
        self.sessions[sid] = session

        intro_fallback = (
            f"Hi {session.candidate_name or 'there'}, before we dive into the technical portion I'd love to hear "
            "a quick introduction from you. Could you tell me about yourself, your current role, and what excites "
            "you about this opportunity?"
        )

        q = self._generate_question(session, qtype="introduction")
        if not q or "introduc" not in q.lower():
            print(f"⚠️ Generated introduction question did not look like an intro. Using fallback prompt.")
            q = intro_fallback
        else:
            q = q.strip()
            if not q.lower().startswith("hi") and "introduc" not in q.lower():
                # Make sure it clearly asks for an introduction
                q = intro_fallback

        session.add_interviewer(q)
        session.current_question_number = 1
        session.last_active_question_text = q
        session.question_asked_at = time.time()
        audio_url = _text_to_speech(q, f"q{session.current_question_number}.mp3")

        return {
            "session_id": sid,
            "question": q,
            "audio_url": audio_url,
            "question_number": session.current_question_number,
            "max_questions": session.max_questions,
        }

    def upload_answer(self, session_id: str, transcript: str, silence: bool, had_voice: bool) -> Dict[str, object]:
        if not session_id or session_id not in self.sessions:
            return {"error": "Invalid session ID"}
        session = self.sessions[session_id]

        transcript = (transcript or "").strip()
        if not transcript:
            if silence and not had_voice:
                proceed = "I didn’t catch a response — shall we move to the next question?"
                session.add_interviewer(proceed)
                audio_url = _text_to_speech(proceed, f"proceed_{uuid.uuid4().hex}.mp3")
                session.last_active_question_text = proceed
                session.question_asked_at = time.time()
                return {
                    "transcript": "",
                    "completed": False,
                    "next_question": proceed,
                    "audio_url": audio_url,
                    "question_number": session.current_question_number,
                    "max_questions": session.max_questions,
                }
            return {
                "transcript": "",
                "completed": False,
                "acknowledge": True,
                "message": "I didn't catch that. Please try again.",
                "question_number": session.current_question_number,
                "max_questions": session.max_questions,
            }

        session.add_candidate(transcript)

        # Check if we've already asked the maximum number of questions
        if session.current_question_number >= session.max_questions and not session.in_qa_phase:
            # Transition to Q&A phase
            session.in_qa_phase = True
            qa_question = "Thank you for your answers! Do you have any questions for me about the company, the role, or anything else?"
            session.add_interviewer(qa_question)
            session.last_active_question_text = qa_question
            session.question_asked_at = time.time()
            audio_url = _text_to_speech(qa_question, f"qa_question.mp3")
            return {
                "transcript": transcript,
                "completed": False,
                "next_question": qa_question,
                "audio_url": audio_url,
                "question_number": session.current_question_number,
                "max_questions": session.max_questions,
                "qa_phase": True,
            }

        # Handle Q&A phase
        if session.in_qa_phase:
            if not transcript.strip():
                # No response to Q&A question, end interview
                session.is_completed = True
                closing = "Thank you for your time! We appreciate your interest in the position and will be in touch soon."
                audio_url = _text_to_speech(closing, f"final_closing.mp3")
                return {
                    "transcript": transcript,
                    "completed": True,
                    "message": closing,
                    "final_audio_url": audio_url,
                }
            
            session.add_candidate(transcript)
            
            # Check if candidate has a question
            if "?" in transcript and any(hint in transcript.lower() for hint in self._question_hints):
                # Candidate asked a question, check if it's job-related
                if self._is_job_related_question(transcript, session.jd_text):
                    response = self._generate_company_response(session, transcript)
                else:
                    response = "I can only answer questions related to the company, job role, or interview process. Do you have any questions about the position?"
                
                session.add_interviewer(response)
                session.last_active_question_text = response
                session.question_asked_at = time.time()
                audio_url = _text_to_speech(response, f"qa_answer.mp3")
                
                return {
                    "transcript": transcript,
                    "completed": False,
                    "next_question": response,
                    "audio_url": audio_url,
                    "question_number": session.current_question_number,
                    "max_questions": session.max_questions,
                    "qa_phase": True,
                }
            else:
                # Candidate doesn't have questions, end interview
                session.is_completed = True
                closing = "Great! Thank you for your time and interest. We'll be in touch with next steps soon."
                audio_url = _text_to_speech(closing, f"final_closing.mp3")
                return {
                    "transcript": transcript,
                    "completed": True,
                    "message": closing,
                    "final_audio_url": audio_url,
                }

        # Detect candidate clarification questions before moving on
        lower_transcript = transcript.lower()
        asked_question = "?" in transcript and any(hint in lower_transcript for hint in self._question_hints)
        if asked_question:
            clarification = self._generate_candidate_response(session, transcript)
            session.add_interviewer(clarification)
            audio_url = _text_to_speech(clarification, f"clarify_{uuid.uuid4().hex}.mp3")
            session.last_active_question_text = session.last_active_question_text or session.last_interviewer_question()
            session.question_asked_at = time.time()
            return {
                "transcript": transcript,
                "completed": False,
                "follow_up_answer": clarification,
                "follow_up_audio_url": audio_url,
                "repeat_question": session.last_active_question_text,
                "question_number": session.current_question_number,
                "max_questions": session.max_questions,
            }

        # Generate next question only if we haven't reached max_questions
        qtype = "follow_up" if session.current_question_number == 1 else "regular"
        print(f"🤖 Generating {qtype} question for session {session_id}, current question: {session.current_question_number}")
        next_q = self._generate_question(session, qtype=qtype, last_answer=transcript)
        print(f"🤖 Generated question: {next_q[:100]}...")
        
        if not next_q or next_q.startswith("[Gemini error"):
            print(f"❌ Question generation failed: {next_q}")
            return {
                "transcript": transcript,
                "completed": False,
                "error": f"Failed to generate next question: {next_q}",
                "question_number": session.current_question_number,
                "max_questions": session.max_questions,
            }
        
        # Increment question number AFTER generating the question
        session.add_interviewer(next_q)
        session.current_question_number += 1
        session.last_active_question_text = next_q
        session.question_asked_at = time.time()
        audio_url = _text_to_speech(next_q, f"q{session.current_question_number}.mp3")
        print(f"✅ Question {session.current_question_number} generated successfully")

        return {
            "transcript": transcript,
            "completed": False,
            "next_question": next_q,
            "audio_url": audio_url,
            "question_number": session.current_question_number,
            "max_questions": session.max_questions,
        }

    def repeat(self, session_id: str) -> Dict[str, object]:
        if not session_id or session_id not in self.sessions:
            return {"error": "Invalid session ID"}
        session = self.sessions[session_id]
        last_q = session.last_interviewer_question()
        if not last_q:
            return {"error": "No previous question found"}
        audio_url = _text_to_speech(last_q, f"repeat_{uuid.uuid4().hex}.mp3")
        session.last_active_question_text = last_q
        session.question_asked_at = time.time()
        return {
            "next_question": last_q,
            "audio_url": audio_url,
            "question_number": session.current_question_number,
            "max_questions": session.max_questions,
        }

    def transcript_pdf_bytes(self, session_id: str) -> bytes:
        try:
            from fpdf2 import FPDF  # type: ignore
        except ImportError as e:
            print(f"❌ fpdf2 import failed in transcript_pdf_bytes: {e}")
            try:
                from fpdf import FPDF  # type: ignore
                print("✅ Using fpdf (fallback) for transcript PDF generation")
            except ImportError as e2:
                print(f"❌ fpdf import also failed: {e2}")
                import traceback
                traceback.print_exc()
                return b""

        if not session_id or session_id not in self.sessions:
            return b""
        session = self.sessions[session_id]

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_left_margin(15)
        pdf.set_right_margin(15)
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Interview Transcript", ln=True)
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 8, f"Candidate: {session.candidate_name}", ln=True)
        pdf.cell(0, 8, f"Session ID: {session.session_id}", ln=True)
        pdf.ln(4)
        pdf.set_font("Arial", "B", 13)
        pdf.cell(0, 8, "Conversation:", ln=True)
        pdf.ln(2)
        pdf.set_font("Arial", size=12)
        for msg in session.conversation_history:
            role = "Interviewer" if msg.get("role") == "interviewer" else "Candidate"
            text = msg.get("text", "")
            pdf.set_font("Arial", "B", 12)
            pdf.multi_cell(0, 7, role + ":", align="L")
            pdf.set_font("Arial", size=12)
            pdf.multi_cell(0, 7, text, align="L")
            pdf.ln(2)
        data = pdf.output(dest='S')
        if isinstance(data, (bytes, bytearray)):
            return bytes(data)
        return str(data).encode('latin1', 'replace')


# Singleton manager used by Django views
chatbot_manager = ChatBotManager()


def ai_start_django(candidate_name: str, jd_text: str, session_key: str = None) -> Dict[str, object]:
    """Start AI interview, optionally getting data from database using session_key."""
    from .models import InterviewSession as DjangoInterviewSession
    
    # Get question count from InterviewSlot.ai_configuration or default to 4
    question_count = 4  # Default
    
    # If session_key is provided, get data from database
    if session_key:
        try:
            django_session = DjangoInterviewSession.objects.get(session_key=session_key)
            candidate_name = django_session.candidate_name
            jd_text = django_session.job_description or ""
            
            # Get question count from InterviewSlot.ai_configuration
            try:
                from interviews.models import Interview
                interview = Interview.objects.filter(session_key=session_key).first()
                
                # If not found via session_key, try via candidate email
                if not interview and django_session.candidate_email:
                    from candidates.models import Candidate
                    try:
                        candidate = Candidate.objects.get(email=django_session.candidate_email)
                        interview = Interview.objects.filter(candidate=candidate).order_by('-created_at').first()
                    except:
                        pass
                
                if interview and interview.slot:
                    slot = interview.slot
                    if slot.ai_configuration and isinstance(slot.ai_configuration, dict):
                        question_count = slot.ai_configuration.get('question_count', 4)
                        try:
                            question_count = int(question_count)
                        except (ValueError, TypeError):
                            question_count = 4
                    elif hasattr(slot, 'question_count') and slot.question_count:
                        question_count = int(slot.question_count)
            except Exception:
                # If there's any error getting question count, use default
                pass
        except DjangoInterviewSession.DoesNotExist:
            return {"error": "Invalid session key"}
    
    return chatbot_manager.start(candidate_name, jd_text, max_questions=question_count)


def ai_upload_answer_django(session_id: str, transcript: str, silence: bool, had_voice: bool) -> Dict[str, object]:
    return chatbot_manager.upload_answer(session_id, transcript, silence, had_voice)


def ai_repeat_django(session_id: str) -> Dict[str, object]:
    return chatbot_manager.repeat(session_id)


def ai_transcript_pdf_django(session_id: str) -> bytes:
    return chatbot_manager.transcript_pdf_bytes(session_id)


def get_audio_file_path(filename: str) -> str:
    return os.path.join(AI_UPLOADS_DIR, filename)


