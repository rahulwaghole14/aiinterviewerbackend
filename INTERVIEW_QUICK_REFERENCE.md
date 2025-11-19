# AI Interview Portal - Quick Interview Reference

## 🎯 Project in 30 Seconds
An AI-powered interview platform that conducts automated technical interviews with real-time proctoring, AI question generation, speech-to-text transcription, and comprehensive evaluation.

---

## 📚 Core Technology Stack

### **Backend Framework**
- **Django 5.1.6** - Main web framework
- **Django REST Framework 3.16.0** - API development
- **Django Channels 4.1.0** - WebSocket support
- **Daphne 4.1.2** - ASGI server for WebSockets

### **AI/ML Stack**
- **google-generativeai** - Google Gemini for question generation & evaluation
- **openai-whisper** - Speech-to-text transcription
- **google-cloud-texttospeech** - Text-to-speech for AI interviewer
- **ultralytics (YOLOv8)** - Face detection & proctoring
- **opencv-python** - Computer vision for camera processing

### **Frontend Stack**
- **React 19.1.0** - UI framework
- **Redux Toolkit** - State management
- **Axios** - API communication
- **React Router** - Client-side routing
- **Vite** - Build tool

### **Real-time Communication**
- **WebSockets** - Real-time audio streaming
- **Django Channels** - WebSocket handling

### **Document Processing**
- **PyPDF2** - PDF parsing (resumes)
- **python-docx** - Word document processing
- **WeasyPrint** - HTML to PDF (reports)

---

## 🔑 Key Libraries & Their Purpose

| Library | Purpose | Where Used |
|---------|---------|------------|
| **Django** | Web framework | Entire backend structure |
| **DRF** | REST APIs | All `/api/*` endpoints |
| **Channels** | WebSockets | Real-time audio transcription |
| **Gemini AI** | Question generation | Interview questions, evaluation |
| **Whisper** | Speech-to-text | Converting audio to text |
| **YOLO** | Face detection | Proctoring system |
| **OpenCV** | Camera processing | Video frame capture |
| **React** | Frontend UI | All user interfaces |
| **Axios** | HTTP client | API calls from frontend |

---

## 💬 Common Interview Questions & Answers

### **Q: Why did you choose Django over Flask/FastAPI?**
**A:** "Django provides a complete framework with built-in ORM, authentication, admin panel, and excellent documentation. For a complex application with multiple user roles (admin, company, hiring agency, candidate), Django's built-in features save significant development time. The admin panel is particularly useful for managing interviews, candidates, and jobs."

### **Q: How does the AI question generation work?**
**A:** "We use Google Gemini API (gemini-2.0-flash model) to generate contextual interview questions. The system takes the job description and candidate's resume, sends them to Gemini with a carefully crafted prompt, and receives structured questions. Gemini analyzes the job requirements and candidate experience to generate relevant technical and behavioral questions."

### **Q: Explain the real-time transcription system.**
**A:** "The browser captures audio from the candidate's microphone and streams it via WebSocket to Django. Django uses Channels to handle the WebSocket connection and proxies the audio to Deepgram API for real-time transcription. The transcription results are sent back to the browser, allowing live display of what the candidate is saying."

### **Q: How does the proctoring system work?**
**A:** "We use OpenCV to capture frames from the candidate's webcam. Each frame is processed by YOLOv8 (ultralytics) for face detection. The system checks for: (1) presence of a person, (2) multiple people detection, (3) phone detection, and (4) tab switching. Warnings are logged and can trigger interview termination."

### **Q: How do you evaluate candidate answers?**
**A:** "Candidate audio responses are transcribed using Whisper. The transcribed text, along with the original question, is sent to Gemini AI with an evaluation prompt. Gemini analyzes the answer for technical accuracy, completeness, and relevance, providing scores and detailed feedback. For coding questions, we execute test cases against the submitted code."

### **Q: Why use WebSockets instead of REST for audio?**
**A:** "REST APIs are request-response based, which isn't suitable for continuous audio streaming. WebSockets provide bidirectional, persistent connections perfect for real-time audio streaming. The browser can continuously send audio chunks while receiving transcription updates simultaneously."

### **Q: How do you handle file uploads (resumes)?**
**A:** "Resumes are uploaded via Django REST Framework API endpoints. We use PyPDF2 for PDF files and python-docx for Word documents to extract text. The extracted text is then analyzed by Gemini AI to understand candidate skills and experience, which helps in generating personalized interview questions."

### **Q: Explain the authentication system.**
**A:** "We use Django REST Framework's JWT authentication (djangorestframework-simplejwt). On login, the system generates access and refresh tokens. The frontend stores these tokens and includes them in API request headers. Django validates tokens on each request and provides role-based permissions for different user types (admin, company, candidate)."

### **Q: How is the interview report generated?**
**A:** "After the interview completes, we compile all data: questions asked, candidate answers (transcribed), coding submissions, proctoring warnings, and AI evaluations. This data is formatted into HTML using Django templates, then converted to PDF using WeasyPrint. The PDF includes scores, recommendations, and detailed feedback."

### **Q: What's the architecture for handling multiple interviews simultaneously?**
**A:** "Django's WSGI/ASGI architecture handles concurrent requests. Each interview session is stored in the database with a unique session ID. WebSocket connections are isolated per session. For production, we'd use Redis as the Channels backend to support horizontal scaling across multiple servers."

---

## 🏗️ System Architecture Flow

```
1. Candidate Access
   ↓
2. React Frontend (Interview UI)
   ↓
3. Django REST API (Session Management)
   ↓
4. Gemini AI (Question Generation)
   ↓
5. Google Cloud TTS (Question Audio)
   ↓
6. Browser Audio Capture
   ↓
7. WebSocket → Django Channels → Deepgram (Transcription)
   ↓
8. Whisper (Backup Transcription)
   ↓
9. Gemini AI (Answer Evaluation)
   ↓
10. OpenCV + YOLO (Proctoring)
    ↓
11. Database Storage (All Data)
    ↓
12. WeasyPrint (PDF Report Generation)
```

---

## 🎯 Technical Highlights to Mention

1. **Real-time Processing:** WebSockets for live audio transcription
2. **AI Integration:** Multiple AI services (Gemini, Whisper, YOLO) working together
3. **Proctoring:** Computer vision-based monitoring system
4. **Scalability:** Django Channels with Redis support for horizontal scaling
5. **Security:** JWT authentication, role-based permissions, CORS protection
6. **Document Processing:** Automated resume parsing and PDF generation
7. **Modern Frontend:** React with Redux for complex state management

---

## 📝 Code Examples to Reference

### **Question Generation (Gemini)**
```python
import google.generativeai as genai
model = genai.GenerativeModel("gemini-2.0-flash")
prompt = f"Generate interview questions for {job_title} based on {resume_text}"
response = model.generate_content(prompt)
```

### **WebSocket Consumer (Channels)**
```python
from channels.generic.websocket import AsyncWebsocketConsumer

class DeepgramProxyConsumer(AsyncWebsocketConsumer):
    async def receive(self, bytes_data=None):
        # Forward audio to Deepgram API
        await self.dg_ws.send(bytes_data)
```

### **Face Detection (YOLO)**
```python
from ultralytics import YOLO
model = YOLO('yolov8n.pt')
results = model(frame)
# Check for faces, phones, multiple people
```

### **API Endpoint (DRF)**
```python
from rest_framework.viewsets import ModelViewSet

class InterviewViewSet(ModelViewSet):
    queryset = Interview.objects.all()
    serializer_class = InterviewSerializer
    permission_classes = [IsAuthenticated]
```

---

## 🚀 Deployment Considerations

- **Gunicorn** - WSGI server for Django
- **Daphne** - ASGI server for WebSockets
- **PostgreSQL** - Production database (via psycopg2)
- **Redis** - Channels backend for multi-server support
- **Whitenoise** - Static file serving
- **Environment Variables** - Secure API key management

---

## 💡 Key Points to Emphasize

1. **Full-stack expertise:** Backend (Django) + Frontend (React) + AI/ML integration
2. **Real-time capabilities:** WebSockets for live transcription
3. **AI-powered:** Multiple AI services integrated seamlessly
4. **Security:** JWT auth, role-based access, proctoring
5. **Scalability:** Designed for production with proper architecture
6. **User experience:** Modern React UI with real-time updates

---

## 🎤 Elevator Pitch (1 minute)

*"I built an AI-powered interview platform using Django and React. The system uses Google Gemini to generate contextual interview questions based on job descriptions and resumes. During interviews, it uses WebSockets for real-time audio transcription via Deepgram, OpenAI Whisper for backup transcription, and YOLO for face detection and proctoring. Candidate answers are evaluated by Gemini AI, and comprehensive PDF reports are automatically generated. The platform supports multiple user roles with JWT authentication and handles everything from resume parsing to final evaluation."*

