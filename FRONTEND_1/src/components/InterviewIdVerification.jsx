import React, { useState, useEffect, useRef } from 'react';
import { toast } from 'react-toastify';
import { BeatLoader } from 'react-spinners';
import './InterviewIdVerification.css';

const InterviewIdVerification = ({ sessionData, onComplete, onError }) => {
  const [step, setStep] = useState('camera-setup'); // camera-setup, id-verification, ready
  const [mediaStream, setMediaStream] = useState(null);
  const [cameraReady, setCameraReady] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  // Setup camera on component mount
  useEffect(() => {
    setupCamera();
    
    // Cleanup on unmount
    return () => {
      if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  const setupCamera = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { 
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'user'
        },
        audio: false // No audio needed for ID verification
      });

      setMediaStream(stream);
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => {
          setCameraReady(true);
          setStep('id-verification');
        };
      }
    } catch (err) {
      console.error('Camera setup error:', err);
      if (err.name === 'NotAllowedError') {
        setError('Camera access is required for ID verification. Please allow camera access and refresh the page.');
      } else if (err.name === 'NotFoundError') {
        setError('No camera found. Please connect a camera and refresh the page.');
      } else {
        setError('Failed to access camera. Please check your device and refresh the page.');
      }
    } finally {
      setLoading(false);
    }
  };

  const capturePhoto = () => {
    if (!videoRef.current || !canvasRef.current) return null;
    
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');
    
    // Set canvas size to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Draw video frame to canvas
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Convert to blob
    return new Promise((resolve) => {
      canvas.toBlob(resolve, 'image/jpeg', 0.8);
    });
  };

  const handleIdVerification = async () => {
    try {
      setLoading(true);
      
      // Capture photo for verification
      const photoBlob = await capturePhoto();
      
      // For now, we'll simulate ID verification
      // In a real implementation, you would send the photo to your backend
      await new Promise(resolve => setTimeout(resolve, 2000)); // Simulate API call
      
      setStep('ready');
      toast.success('ID verification completed successfully!');
      
      // Auto-proceed to interview after a short delay
      setTimeout(() => {
        onComplete();
      }, 2000);
      
    } catch (err) {
      console.error('ID verification error:', err);
      setError('Failed to verify ID. Please try again.');
      toast.error('ID verification failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const retryCameraSetup = () => {
    setError(null);
    setStep('camera-setup');
    setupCamera();
  };

  // Render camera setup step
  if (step === 'camera-setup') {
    return (
      <div className="interview-id-verification">
        <div className="verification-container">
          <div className="verification-header">
            <h2>Camera Setup</h2>
            <p>Please allow camera access to continue with ID verification</p>
          </div>
          
          {loading ? (
            <div className="camera-loading">
              <BeatLoader color="var(--color-primary)" size={15} />
              <p>Setting up camera...</p>
            </div>
          ) : error ? (
            <div className="camera-error">
              <div className="error-icon">📷</div>
              <p>{error}</p>
              <button className="retry-button" onClick={retryCameraSetup}>
                Retry Camera Setup
              </button>
            </div>
          ) : (
            <div className="camera-preview">
              <video
                ref={videoRef}
                autoPlay
                muted
                playsInline
                className="camera-video"
              />
              <p>Camera is ready!</p>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Render ID verification step
  if (step === 'id-verification') {
    return (
      <div className="interview-id-verification">
        <div className="verification-container">
          <div className="verification-header">
            <h2>ID Verification</h2>
            <p>Please position your face in the camera and click "Verify ID"</p>
          </div>
          
          <div className="verification-content">
            <div className="camera-preview">
              <video
                ref={videoRef}
                autoPlay
                muted
                playsInline
                className="camera-video"
              />
              <div className="face-overlay">
                <div className="face-frame"></div>
              </div>
            </div>
            
            <div className="verification-instructions">
              <h3>Instructions:</h3>
              <ul>
                <li>Ensure your face is clearly visible</li>
                <li>Remove any hats or sunglasses</li>
                <li>Look directly at the camera</li>
                <li>Ensure good lighting</li>
              </ul>
            </div>
            
            <div className="verification-actions">
              <button 
                className="verify-button"
                onClick={handleIdVerification}
                disabled={loading}
              >
                {loading ? (
                  <>
                    <BeatLoader color="#ffffff" size={8} />
                    <span>Verifying...</span>
                  </>
                ) : (
                  'Verify ID'
                )}
              </button>
            </div>
          </div>
          
          {/* Hidden canvas for photo capture */}
          <canvas ref={canvasRef} style={{ display: 'none' }} />
        </div>
      </div>
    );
  }

  // Render ready step
  if (step === 'ready') {
    return (
      <div className="interview-id-verification">
        <div className="verification-container">
          <div className="verification-header">
            <h2>Ready to Start!</h2>
            <p>ID verification completed successfully</p>
          </div>
          
          <div className="ready-content">
            <div className="success-icon">✅</div>
            <h3>You're all set!</h3>
            <p>Your interview will begin in a moment...</p>
            <div className="loading-indicator">
              <BeatLoader color="var(--color-primary)" size={10} />
            </div>
          </div>
        </div>
      </div>
    );
  }

  return null;
};

export default InterviewIdVerification;







