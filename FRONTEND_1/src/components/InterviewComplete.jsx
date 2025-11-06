import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import { BeatLoader } from 'react-spinners';
import { baseURL } from '../config/constants';
import './InterviewComplete.css';

const InterviewComplete = ({ sessionData, onClose }) => {
  const [loading, setLoading] = useState(false);
  const [completionData, setCompletionData] = useState(null);

  useEffect(() => {
    // Release camera and microphone resources
    const releaseMediaResources = () => {
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        // Stop all media tracks
        navigator.mediaDevices.getUserMedia({ video: true, audio: true })
          .then(stream => {
            stream.getTracks().forEach(track => track.stop());
          })
          .catch(() => {
            // Ignore errors if no media is active
          });
      }
    };

    releaseMediaResources();
    
    // Fetch completion data if needed
    fetchCompletionData();
  }, []);

  const fetchCompletionData = async () => {
    try {
      setLoading(true);
      
      // You can fetch interview summary or completion data here
      // For now, we'll just simulate a delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setCompletionData({
        totalQuestions: 5,
        completedQuestions: 5,
        duration: '15 minutes',
        status: 'completed'
      });
      
    } catch (err) {
      console.error('Error fetching completion data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCloseInterview = () => {
    try {
      // Attempt to close the tab/window
      if (window.opener) {
        // If opened in a popup, close it
        window.close();
      } else {
        // If opened in main window, redirect to a completion page
        window.location.href = '/interview-complete';
      }
    } catch (err) {
      console.error('Error closing interview:', err);
      // Fallback: show message to user
      toast.info('Interview completed! You can now close this tab.');
    }
  };

  const handleDownloadReport = async () => {
    try {
      setLoading(true);
      
      // Generate and download interview report
      const response = await fetch(`${baseURL}/interview_app/report/${sessionData.session_id}/`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `interview-report-${sessionData.session_id}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        toast.success('Interview report downloaded successfully!');
      } else {
        throw new Error('Failed to download report');
      }
      
    } catch (err) {
      console.error('Download error:', err);
      toast.error('Failed to download interview report. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !completionData) {
    return (
      <div className="interview-complete">
        <div className="completion-loading">
          <BeatLoader color="var(--color-primary)" size={15} />
          <h2>Completing Interview...</h2>
          <p>Please wait while we finalize your interview session.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="interview-complete">
      <div className="completion-container">
        <div className="completion-header">
          <div className="success-icon">🎉</div>
          <h1>Interview Completed!</h1>
          <p>Thank you for completing your Talaro interview session.</p>
        </div>
        
        <div className="completion-content">
          <div className="completion-summary">
            <h3>Interview Summary</h3>
            <div className="summary-grid">
              <div className="summary-item">
                <span className="summary-label">Total Questions:</span>
                <span className="summary-value">{completionData?.totalQuestions || 'N/A'}</span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Completed:</span>
                <span className="summary-value">{completionData?.completedQuestions || 'N/A'}</span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Duration:</span>
                <span className="summary-value">{completionData?.duration || 'N/A'}</span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Status:</span>
                <span className="summary-value status-completed">Completed</span>
              </div>
            </div>
          </div>
          
          <div className="completion-message">
            <h3>What happens next?</h3>
            <ul>
              <li>Your interview responses have been recorded and analyzed</li>
              <li>Our AI system will evaluate your performance</li>
              <li>You will receive feedback and results via email</li>
              <li>The hiring team will review your interview</li>
            </ul>
          </div>
          
          <div className="completion-actions">
            <button 
              className="download-report-button"
              onClick={handleDownloadReport}
              disabled={loading}
            >
              {loading ? (
                <>
                  <BeatLoader color="#ffffff" size={8} />
                  <span>Generating Report...</span>
                </>
              ) : (
                'Download Interview Report'
              )}
            </button>
            
            <button 
              className="close-interview-button"
              onClick={handleCloseInterview}
            >
              Close Interview
            </button>
          </div>
        </div>
        
        <div className="completion-footer">
          <p>
            <strong>Important:</strong> Your interview data has been securely saved. 
            You can close this window safely.
          </p>
          <p>
            If you have any questions, please contact your recruiter or the hiring team.
          </p>
        </div>
      </div>
    </div>
  );
};

export default InterviewComplete;

