import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { BeatLoader } from 'react-spinners';
import InterviewIdVerification from './InterviewIdVerification';
import InterviewSession from './InterviewSession';
import InterviewComplete from './InterviewComplete';
import { baseURL } from '../config/constants';
import './InterviewPortal.css';

const InterviewPortal = () => {
  const { sessionKey } = useParams();
  const navigate = useNavigate();
  
  const [interviewState, setInterviewState] = useState('loading'); // loading, id-verification, interview, complete, error
  const [sessionData, setSessionData] = useState(null);
  const [mediaStream, setMediaStream] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  
  const videoRef = useRef(null);
  const audioRef = useRef(null);

  // Check interview session validity
  useEffect(() => {
    const checkInterviewSession = async () => {
      try {
        setLoading(true);
        const response = await fetch(`${baseURL}/interview_app/?session_key=${sessionKey}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        const data = await response.json();
        
        if (response.ok) {
          setSessionData(data);
          setInterviewState('id-verification');
        } else {
          if (data.status === 'not_started') {
            setInterviewState('not_started');
            setError('Interview has not started yet. Please wait for your scheduled time.');
          } else if (data.status === 'expired') {
            setInterviewState('expired');
            setError('This interview link has expired.');
          } else {
            setInterviewState('error');
            setError(data.error || 'Invalid interview link.');
          }
        }
      } catch (err) {
        console.error('Error checking interview session:', err);
        setInterviewState('error');
        setError('Failed to load interview session. Please check your internet connection.');
      } finally {
        setLoading(false);
      }
    };

    if (sessionKey) {
      checkInterviewSession();
    }
  }, [sessionKey]);

  // Setup camera and microphone
  const setupMedia = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { 
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'user'
        },
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });

      setMediaStream(stream);
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      
      return stream;
    } catch (err) {
      console.error('Error accessing media devices:', err);
      if (err.name === 'NotAllowedError') {
        toast.error('Camera and microphone access is required for this interview.');
      } else if (err.name === 'NotFoundError') {
        toast.error('No camera or microphone found. Please connect your devices.');
      } else {
        toast.error('Failed to access camera and microphone. Please check your device permissions.');
      }
      throw err;
    }
  };

  // Handle ID verification completion
  const handleIdVerificationComplete = async () => {
    try {
      setInterviewState('interview');
      await setupMedia();
    } catch (err) {
      setInterviewState('error');
      setError('Failed to start interview. Please refresh the page and try again.');
    }
  };

  // Handle interview completion
  const handleInterviewComplete = () => {
    setInterviewState('complete');
    // Release media resources
    if (mediaStream) {
      mediaStream.getTracks().forEach(track => track.stop());
      setMediaStream(null);
    }
  };

  // Handle interview errors
  const handleInterviewError = (errorMessage) => {
    setInterviewState('error');
    setError(errorMessage);
  };

  // Render loading state
  if (loading) {
    return (
      <div className="interview-portal">
        <div className="interview-loading">
          <div className="loading-content">
            <BeatLoader color="var(--color-primary)" size={15} />
            <h2>Loading Interview...</h2>
            <p>Please wait while we prepare your interview session.</p>
          </div>
        </div>
      </div>
    );
  }

  // Render error state
  if (interviewState === 'error') {
    return (
      <div className="interview-portal">
        <div className="interview-error">
          <div className="error-content">
            <div className="error-icon">⚠️</div>
            <h2>Interview Error</h2>
            <p>{error}</p>
            <button 
              className="retry-button"
              onClick={() => window.location.reload()}
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Render not started state
  if (interviewState === 'not_started') {
    return (
      <div className="interview-portal">
        <div className="interview-not-started">
          <div className="not-started-content">
            <div className="clock-icon">⏰</div>
            <h2>Interview Not Started</h2>
            <p>{error}</p>
            <div className="countdown-info">
              <p>Your interview will begin at the scheduled time.</p>
              <p>Please keep this page open and wait for the countdown to complete.</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Render expired state
  if (interviewState === 'expired') {
    return (
      <div className="interview-portal">
        <div className="interview-expired">
          <div className="expired-content">
            <div className="expired-icon">⏰</div>
            <h2>Interview Expired</h2>
            <p>{error}</p>
            <p>Please contact your recruiter for a new interview link.</p>
          </div>
        </div>
      </div>
    );
  }

  // Render main interview interface
  return (
    <div className="interview-portal">
      {/* Hidden video element for camera feed */}
      <video
        ref={videoRef}
        autoPlay
        muted
        playsInline
        style={{ display: 'none' }}
      />
      
      {/* Hidden audio element for microphone */}
      <audio
        ref={audioRef}
        autoPlay
        muted
        playsInline
        style={{ display: 'none' }}
      />

      {/* Interview phases */}
      {interviewState === 'id-verification' && (
        <InterviewIdVerification
          sessionData={sessionData}
          onComplete={handleIdVerificationComplete}
          onError={handleInterviewError}
        />
      )}

      {interviewState === 'interview' && (
        <InterviewSession
          sessionData={sessionData}
          mediaStream={mediaStream}
          onComplete={handleInterviewComplete}
          onError={handleInterviewError}
        />
      )}

      {interviewState === 'complete' && (
        <InterviewComplete
          sessionData={sessionData}
          onClose={() => window.close()}
        />
      )}
    </div>
  );
};

export default InterviewPortal;





