import React, { useState, useEffect, useRef } from 'react';
import { toast } from 'react-toastify';
import { BeatLoader } from 'react-spinners';
import { baseURL } from '../config/constants';
import './InterviewSession.css';

const InterviewSession = ({ sessionData, mediaStream, onComplete, onError }) => {
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [transcribedText, setTranscribedText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [interviewPhase, setInterviewPhase] = useState('loading'); // loading, question, answering, complete
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const audioContextRef = useRef(null);
  const audioElementRef = useRef(null);
  const questionStartTimeRef = useRef(null);

  // Initialize interview session
  useEffect(() => {
    initializeInterview();
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (mediaRecorderRef.current) {
        mediaRecorderRef.current.stop();
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  const initializeInterview = async () => {
    try {
      setLoading(true);
      
      // Fetch interview questions from backend
      const response = await fetch(`${baseURL}/interview_app/get_questions/?session_id=${sessionData.session_id}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to load interview questions');
      }

      const data = await response.json();
      setQuestions(data.questions || []);
      
      if (data.questions && data.questions.length > 0) {
        setCurrentQuestion(data.questions[0]);
        setInterviewPhase('question');
      } else {
        throw new Error('No questions available for this interview');
      }
      
    } catch (err) {
      console.error('Interview initialization error:', err);
      setError(err.message);
      onError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const playQuestionAudio = async (question) => {
    try {
      setIsPlaying(true);
      
      if (audioElementRef.current) {
        audioElementRef.current.src = question.audio_url;
        await audioElementRef.current.play();
        
        audioElementRef.current.onended = () => {
          setIsPlaying(false);
          startAnswering();
        };
      }
    } catch (err) {
      console.error('Error playing audio:', err);
      setIsPlaying(false);
      // Fallback to text display
      startAnswering();
    }
  };

  const startAnswering = () => {
    setInterviewPhase('answering');
    questionStartTimeRef.current = Date.now();
    startRecording();
  };

  const startRecording = () => {
    if (!mediaStream) {
      toast.error('No microphone access available');
      return;
    }

    try {
      audioChunksRef.current = [];
      
      const mediaRecorder = new MediaRecorder(mediaStream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      mediaRecorderRef.current = mediaRecorder;
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorder.onstop = async () => {
        await processRecording();
      };
      
      mediaRecorder.start();
      setIsRecording(true);
      
    } catch (err) {
      console.error('Recording error:', err);
      toast.error('Failed to start recording');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const processRecording = async () => {
    try {
      setLoading(true);
      
      const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
      const responseTime = (Date.now() - questionStartTimeRef.current) / 1000;
      
      // Send audio for transcription
      const formData = new FormData();
      formData.append('audio_data', audioBlob);
      formData.append('session_id', sessionData.session_id);
      formData.append('question_id', currentQuestion.id);
      formData.append('response_time', responseTime.toString());
      
      const response = await fetch(`${baseURL}/interview_app/transcribe_audio/`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to transcribe audio');
      }

      const data = await response.json();
      setTranscribedText(data.text || '');
      
      // Save the transcribed answer
      await saveAnswer(data.text, responseTime);
      
      // Move to next question or complete interview
      setTimeout(() => {
        moveToNextQuestion();
      }, 2000);
      
    } catch (err) {
      console.error('Processing error:', err);
      toast.error('Failed to process your answer. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const saveAnswer = async (text, responseTime) => {
    try {
      const response = await fetch(`${baseURL}/interview_app/save_answer/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionData.session_id,
          question_id: currentQuestion.id,
          transcribed_answer: text,
          response_time_seconds: responseTime,
        }),
      });

      if (!response.ok) {
        console.error('Failed to save answer');
      }
    } catch (err) {
      console.error('Save answer error:', err);
    }
  };

  const moveToNextQuestion = () => {
    const nextIndex = currentQuestionIndex + 1;
    
    if (nextIndex < questions.length) {
      setCurrentQuestionIndex(nextIndex);
      setCurrentQuestion(questions[nextIndex]);
      setTranscribedText('');
      setInterviewPhase('question');
    } else {
      // Interview complete
      completeInterview();
    }
  };

  const completeInterview = async () => {
    try {
      setLoading(true);
      
      // End the interview session
      const response = await fetch(`${baseURL}/interview_app/end_interview_session/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionData.session_id,
        }),
      });

      if (!response.ok) {
        console.error('Failed to end interview session');
      }
      
      setInterviewPhase('complete');
      onComplete();
      
    } catch (err) {
      console.error('Complete interview error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleQuestionStart = () => {
    if (currentQuestion.audio_url) {
      playQuestionAudio(currentQuestion);
    } else {
      startAnswering();
    }
  };

  // Render loading state
  if (loading && interviewPhase === 'loading') {
    return (
      <div className="interview-session">
        <div className="session-loading">
          <BeatLoader color="var(--color-primary)" size={15} />
          <h2>Preparing Your Interview...</h2>
          <p>Please wait while we load your interview questions.</p>
        </div>
      </div>
    );
  }

  // Render error state
  if (error) {
    return (
      <div className="interview-session">
        <div className="session-error">
          <div className="error-icon">⚠️</div>
          <h2>Interview Error</h2>
          <p>{error}</p>
          <button 
            className="retry-button"
            onClick={() => window.location.reload()}
          >
            Retry Interview
          </button>
        </div>
      </div>
    );
  }

  // Render question phase
  if (interviewPhase === 'question') {
    return (
      <div className="interview-session">
        <div className="session-container">
          <div className="session-header">
            <div className="progress-indicator">
              Question {currentQuestionIndex + 1} of {questions.length}
            </div>
            <div className="session-info">
              <h2>Talaro Interview</h2>
              <p>Listen to the question and prepare your answer</p>
            </div>
          </div>
          
          <div className="question-content">
            <div className="question-display">
              <h3>Question:</h3>
              <p>{currentQuestion.question}</p>
            </div>
            
            <div className="question-actions">
              <button 
                className="start-question-button"
                onClick={handleQuestionStart}
                disabled={isPlaying}
              >
                {isPlaying ? (
                  <>
                    <BeatLoader color="#ffffff" size={8} />
                    <span>Playing Question...</span>
                  </>
                ) : (
                  'Start Question'
                )}
              </button>
            </div>
          </div>
          
          {/* Hidden audio element */}
          <audio ref={audioElementRef} style={{ display: 'none' }} />
        </div>
      </div>
    );
  }

  // Render answering phase
  if (interviewPhase === 'answering') {
    return (
      <div className="interview-session">
        <div className="session-container">
          <div className="session-header">
            <div className="progress-indicator">
              Question {currentQuestionIndex + 1} of {questions.length}
            </div>
            <div className="session-info">
              <h2>Recording Your Answer</h2>
              <p>Speak clearly into your microphone</p>
            </div>
          </div>
          
          <div className="answering-content">
            <div className="recording-status">
              <div className={`recording-indicator ${isRecording ? 'active' : ''}`}>
                {isRecording ? '🔴 Recording...' : '⏹️ Stopped'}
              </div>
            </div>
            
            <div className="question-display">
              <h3>Question:</h3>
              <p>{currentQuestion.question}</p>
            </div>
            
            <div className="answer-controls">
              <button 
                className="stop-recording-button"
                onClick={stopRecording}
                disabled={!isRecording || loading}
              >
                {loading ? (
                  <>
                    <BeatLoader color="#ffffff" size={8} />
                    <span>Processing...</span>
                  </>
                ) : (
                  'Stop Recording'
                )}
              </button>
            </div>
            
            {transcribedText && (
              <div className="transcription-display">
                <h3>Your Answer:</h3>
                <p>{transcribedText}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return null;
};

export default InterviewSession;

