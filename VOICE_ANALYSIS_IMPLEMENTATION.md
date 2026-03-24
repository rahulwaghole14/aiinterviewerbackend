# Voice Analysis Implementation

## Overview
This implementation adds voice detection analysis and PDF report generation functionality to the AI Interview system.

## Features Implemented

### 1. Voice Analysis Models
- **VoiceActivityDetection**: Stores voice activity detection results (speech/silence percentages, response delays)
- **SpeakerDiarization**: Stores speaker diarization results (speaker changes, candidate vs interviewer speech ratios)
- **AnswerVoiceAnalysis**: Stores detailed analysis for individual answers (WPM, filler words, insights)

### 2. Voice Analysis Services
- **VoiceAnalysisService**: Full analysis using Hugging Face models (pyannote.audio)
- **FastVoiceAnalysisService**: Quick analysis without heavy model processing
- **Voice Analysis PDF Generator**: Creates comprehensive PDF reports

### 3. API Endpoints

#### Voice Analysis Endpoints
- `POST /api/voice/analyze/` - Analyze voice activity for interview session
- `GET /api/voice/pdf/<uuid:session_key>/` - Generate and download voice analysis PDF
- `GET /api/voice/data/<uuid:session_key>/` - Get voice analysis data for session
- `POST /api/voice/trigger/` - Automatically trigger analysis at interview end

### 4. Integration Points

#### InterviewSerializer Enhancement
- Added `voice_analysis_pdf` field to include PDF URL in candidate details
- Added `voice_analysis_pdf_url` method to generate proper media URLs

#### InterviewSession Model Enhancement
- Added `voice_analysis_pdf` FileField to store generated PDF reports

## Usage Instructions

### 1. Automatic Voice Analysis at Interview End
When an interview ends, trigger automatic analysis:

```javascript
fetch('/api/voice/trigger/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer YOUR_TOKEN'
    },
    body: JSON.stringify({
        session_key: 'SESSION_KEY',
        interview_video_path: 'PATH_TO_VIDEO_FILE'
    })
})
```

### 2. Manual Voice Analysis
Trigger manual analysis with fast or full processing:

```javascript
fetch('/api/voice/analyze/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer YOUR_TOKEN'
    },
    body: JSON.stringify({
        session_key: 'SESSION_KEY',
        audio_file_path: 'PATH_TO_AUDIO_FILE',
        use_fast_analysis: true  // Set to false for full analysis
    })
})
```

### 3. Generate PDF Report
Download voice analysis PDF:

```javascript
fetch(`/api/voice/pdf/${sessionKey}/`, {
    method: 'GET',
    headers: {
        'Authorization': 'Bearer YOUR_TOKEN'
    }
})
.then(response => response.blob())
.then(blob => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'voice_analysis_report.pdf';
    a.click();
})
```

### 4. Frontend Integration
Add voice analysis download button to candidate details page:

```javascript
// Check if voice analysis PDF is available
if (interview.voice_analysis_pdf_url) {
    const downloadBtn = document.createElement('button');
    downloadBtn.textContent = 'Download Voice Analysis Report';
    downloadBtn.onclick = () => {
        window.open(interview.voice_analysis_pdf_url, '_blank');
    };
    // Add to candidate details UI
}
```

## Configuration

### Environment Variables
- `HUGGINGFACE_TOKEN`: Required for full voice analysis with pyannote models
- No additional configuration needed for fast analysis

### Dependencies
- **Full Analysis**: pyannote.audio, torch, huggingface_hub
- **Fast Analysis**: No additional dependencies (uses basic metrics)
- **PDF Generation**: weasyprint, django-template-loader

## Database Schema

### VoiceActivityDetection
- session: ForeignKey to InterviewSession
- question: ForeignKey to InterviewQuestion (nullable for overall analysis)
- pause_duration: FloatField
- total_speech_time: FloatField
- speech_percentage: FloatField
- silence_percentage: FloatField
- response_delay_seconds: FloatField (nullable)
- vad_segments: JSONField
- analysis timestamps

### SpeakerDiarization
- session: ForeignKey to InterviewSession
- question: ForeignKey to InterviewQuestion (nullable)
- speaker_changes: IntegerField
- speaker_change_timestamps: JSONField
- num_speakers: IntegerField
- candidate_speech_percentage: FloatField
- interviewer_speech_percentage: FloatField
- diarization_segments: JSONField
- analysis timestamps

### AnswerVoiceAnalysis
- session: ForeignKey to InterviewSession
- question: ForeignKey to InterviewQuestion (nullable)
- answer_number: IntegerField
- segment timing fields
- speech quality metrics
- insights: JSONField
- audio quality scores

## PDF Report Features

### Report Sections
1. **Summary Cards**: Overall metrics (speech %, silence %, response time, speakers detected)
2. **Warnings**: Analysis warnings (high silence, multiple speakers, response delays)
3. **Overall Analysis**: Complete interview voice metrics
4. **Individual Answer Analysis**: Detailed breakdown of each answer
5. **Answer Metrics Summary**: Aggregated statistics across all answers

### Warning Types
- **High Silence**: >70% overall silence or >80% in individual questions
- **Response Delay**: >5 second average response delay
- **Multiple Speakers**: More than 2 speakers detected
- **Frequent Speaker Changes**: >20 speaker changes
- **Multiple Speakers in Answer**: Multiple speakers detected in individual answers
- **Very Short Answer**: Answers <10 seconds

## Performance Considerations

### Fast Analysis Mode
- Uses file size estimation for duration calculation
- Generates basic speech/silence split (60/40 default)
- Creates placeholder diarization data
- Suitable for quick processing or when HuggingFace token unavailable

### Full Analysis Mode
- Requires HuggingFace token and pyannote.audio
- Performs actual VAD and speaker diarization
- More accurate results but slower processing
- GPU acceleration available if supported

## File Structure

```
interview_app/
├── voice_models.py              # Voice analysis models
├── voice_analysis_service.py    # Full analysis service
├── voice_analysis_service_fast.py # Fast analysis service
├── voice_analysis_pdf.py        # PDF generation service
├── views.py                     # API endpoints (added voice analysis views)
├── models.py                    # Updated with voice_analysis_pdf field
└── migrations/
    └── 0020_add_voice_analysis_models.py

templates/
└── voice_analysis_report_simple.html  # PDF report template
```

## Testing

### Test Fast Analysis
```bash
curl -X POST http://localhost:8000/api/voice/analyze/ \
  -H "Content-Type: application/json" \
  -d '{
    "session_key": "test_session",
    "audio_file_path": "/path/to/audio.webm",
    "use_fast_analysis": true
  }'
```

### Test PDF Generation
```bash
curl -X GET http://localhost:8000/api/voice/pdf/SESSION_KEY_UUID/
```

## Frontend Integration Guide

### Candidate Details Page
1. Check for `voice_analysis_pdf_url` in interview data
2. Display download button if PDF available
3. Open PDF in new tab when clicked

### Interview Completion Flow
1. Call `/api/voice/trigger/` when interview ends
2. Show processing indicator during analysis
3. Enable PDF download once analysis complete

### Real-time Updates (Optional)
- Use WebSocket or polling to check analysis status
- Update UI when PDF becomes available
- Show progress indicators for long-running analyses

## Troubleshooting

### Common Issues
1. **Migration Errors**: Use `--fake` for problematic migrations
2. **Missing Dependencies**: Install pyannote.audio for full analysis
3. **HuggingFace Token**: Set environment variable for full analysis
4. **PDF Generation**: Install weasyprint for PDF reports
5. **File Paths**: Ensure audio/video files are accessible

### Error Handling
- Graceful fallback to fast analysis if full analysis fails
- Proper error messages for missing files or invalid sessions
- PDF generation handles missing data gracefully

## Security Considerations

- Authentication required for all voice analysis endpoints
- File access limited to media directory
- PDF files stored in media directory with proper permissions
- Session validation prevents unauthorized access to voice data
