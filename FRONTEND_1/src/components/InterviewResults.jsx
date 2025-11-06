import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { BeatLoader } from 'react-spinners';
import { baseURL } from '../config/constants';
import './InterviewResults.css';

const InterviewResults = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  
  const [results, setResults] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchInterviewResults();
  }, [sessionId]);

  const fetchInterviewResults = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('authToken');
      
      if (!token) {
        setError('Authentication required');
        return;
      }

      // Fetch interview results
      const resultsResponse = await fetch(`${baseURL}/interview_app/api/results/${sessionId}/`, {
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!resultsResponse.ok) {
        throw new Error('Failed to fetch interview results');
      }

      const resultsData = await resultsResponse.json();
      setResults(resultsData);

      // Fetch detailed analytics
      const analyticsResponse = await fetch(`${baseURL}/interview_app/api/analytics/${sessionId}/`, {
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (analyticsResponse.ok) {
        const analyticsData = await analyticsResponse.json();
        setAnalytics(analyticsData);
      }

    } catch (err) {
      console.error('Error fetching interview results:', err);
      setError(err.message);
      toast.error('Failed to load interview results');
    } finally {
      setLoading(false);
    }
  };

  const formatScore = (score) => {
    if (score === null || score === undefined) return 'N/A';
    return `${score}/10`;
  };

  const getScoreColor = (score) => {
    if (score === null || score === undefined) return '#6c757d';
    if (score >= 8) return '#28a745';
    if (score >= 6) return '#ffc107';
    return '#dc3545';
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  const renderOverview = () => (
    <div className="results-overview">
      <div className="candidate-info">
        <h2>Candidate Information</h2>
        <div className="info-grid">
          <div className="info-item">
            <label>Name:</label>
            <span>{results.candidate_name}</span>
          </div>
          <div className="info-item">
            <label>Email:</label>
            <span>{results.candidate_email}</span>
          </div>
          <div className="info-item">
            <label>Scheduled:</label>
            <span>{formatDate(results.scheduled_at)}</span>
          </div>
          <div className="info-item">
            <label>Completed:</label>
            <span>{formatDate(results.completed_at)}</span>
          </div>
          <div className="info-item">
            <label>Status:</label>
            <span className={`status-badge ${results.status.toLowerCase()}`}>
              {results.status}
            </span>
          </div>
        </div>
      </div>

      <div className="evaluation-scores">
        <h2>Evaluation Scores</h2>
        <div className="scores-grid">
          <div className="score-card">
            <h3>Resume Score</h3>
            <div className="score-value" style={{ color: getScoreColor(results.resume_score) }}>
              {formatScore(results.resume_score)}
            </div>
          </div>
          <div className="score-card">
            <h3>Interview Answers</h3>
            <div className="score-value" style={{ color: getScoreColor(results.answers_score) }}>
              {formatScore(results.answers_score)}
            </div>
          </div>
          <div className="score-card">
            <h3>Overall Performance</h3>
            <div className="score-value" style={{ color: getScoreColor(results.overall_performance_score) }}>
              {formatScore(results.overall_performance_score)}
            </div>
          </div>
        </div>
      </div>

      <div className="session-metrics">
        <h2>Session Metrics</h2>
        <div className="metrics-grid">
          <div className="metric-item">
            <label>Total Questions:</label>
            <span>{results.analytics.communication_metrics.total_questions}</span>
          </div>
          <div className="metric-item">
            <label>Answered Questions:</label>
            <span>{results.analytics.communication_metrics.answered_questions}</span>
          </div>
          <div className="metric-item">
            <label>Code Submissions:</label>
            <span>{results.analytics.communication_metrics.code_submissions}</span>
          </div>
          <div className="metric-item">
            <label>Proctoring Warnings:</label>
            <span>{results.total_warnings}</span>
          </div>
        </div>
      </div>
    </div>
  );

  const renderQuestions = () => (
    <div className="questions-section">
      <h2>Questions & Answers</h2>
      <div className="questions-list">
        {results.questions.map((question, index) => (
          <div key={question.id} className="question-item">
            <div className="question-header">
              <span className="question-number">Q{index + 1}</span>
              <span className="question-type">{question.question_type}</span>
              <span className="question-level">{question.question_level}</span>
            </div>
            <div className="question-text">{question.question_text}</div>
            {question.transcribed_answer ? (
              <div className="answer-section">
                <h4>Answer:</h4>
                <p>{question.transcribed_answer}</p>
                <div className="answer-metrics">
                  <span>Response Time: {question.response_time_seconds}s</span>
                  <span>Words per minute: {question.words_per_minute}</span>
                  <span>Filler words: {question.filler_word_count}</span>
                </div>
              </div>
            ) : (
              <div className="no-answer">No answer provided</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );

  const renderCodeSubmissions = () => (
    <div className="code-submissions-section">
      <h2>Code Submissions</h2>
      {results.code_submissions.length > 0 ? (
        <div className="code-submissions-list">
          {results.code_submissions.map((submission, index) => (
            <div key={submission.id} className="code-submission-item">
              <div className="submission-header">
                <span className="submission-number">Submission {index + 1}</span>
                <span className="language-badge">{submission.language}</span>
                <span className="submission-time">
                  {formatDate(submission.submitted_at)}
                </span>
              </div>
              <div className="code-content">
                <h4>Submitted Code:</h4>
                <pre className="code-block">{submission.submitted_code}</pre>
              </div>
              {submission.output_log && (
                <div className="output-content">
                  <h4>Output:</h4>
                  <pre className="output-block">{submission.output_log}</pre>
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="no-submissions">No code submissions found</div>
      )}
    </div>
  );

  const renderAnalytics = () => (
    <div className="analytics-section">
      <h2>Detailed Analytics</h2>
      {analytics && (
        <div className="analytics-content">
          <div className="communication-metrics">
            <h3>Communication Metrics</h3>
            <div className="metrics-grid">
              <div className="metric-card">
                <label>Average Words per Minute</label>
                <span>{analytics.communication_metrics.avg_words_per_minute}</span>
              </div>
              <div className="metric-card">
                <label>Total Filler Words</label>
                <span>{analytics.communication_metrics.total_filler_words}</span>
              </div>
              <div className="metric-card">
                <label>Average Response Time</label>
                <span>{analytics.communication_metrics.avg_response_time}s</span>
              </div>
              <div className="metric-card">
                <label>Average Sentiment Score</label>
                <span>{analytics.communication_metrics.avg_sentiment_score}</span>
              </div>
            </div>
          </div>

          {analytics.proctoring_analytics.total_warnings > 0 && (
            <div className="proctoring-analytics">
              <h3>Proctoring Analytics</h3>
              <div className="warnings-list">
                {Object.entries(analytics.proctoring_analytics.warning_counts).map(([type, count]) => (
                  <div key={type} className="warning-item">
                    <span className="warning-type">{type}</span>
                    <span className="warning-count">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );

  const renderFeedback = () => (
    <div className="feedback-section">
      <h2>AI Evaluation Feedback</h2>
      <div className="feedback-content">
        {results.resume_feedback && (
          <div className="feedback-item">
            <h3>Resume Evaluation</h3>
            <div className="feedback-text">{results.resume_feedback}</div>
          </div>
        )}
        
        {results.answers_feedback && (
          <div className="feedback-item">
            <h3>Interview Answers Evaluation</h3>
            <div className="feedback-text">{results.answers_feedback}</div>
          </div>
        )}
        
        {results.overall_performance_feedback && (
          <div className="feedback-item">
            <h3>Overall Performance Assessment</h3>
            <div className="feedback-text">{results.overall_performance_feedback}</div>
          </div>
        )}
        
        {results.behavioral_analysis && (
          <div className="feedback-item">
            <h3>Behavioral Analysis</h3>
            <div className="feedback-text">{results.behavioral_analysis}</div>
          </div>
        )}
        
        {results.keyword_analysis && (
          <div className="feedback-item">
            <h3>Keyword Analysis</h3>
            <div className="feedback-text">{results.keyword_analysis}</div>
          </div>
        )}
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="interview-results">
        <div className="loading-container">
          <BeatLoader color="var(--color-primary)" size={15} />
          <h2>Loading Interview Results...</h2>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="interview-results">
        <div className="error-container">
          <div className="error-icon">⚠️</div>
          <h2>Error Loading Results</h2>
          <p>{error}</p>
          <button 
            className="retry-button"
            onClick={fetchInterviewResults}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!results) {
    return (
      <div className="interview-results">
        <div className="no-results">
          <h2>No Results Found</h2>
          <p>Interview results could not be found.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="interview-results">
      <div className="results-header">
        <h1>Interview Results</h1>
        <p>Session ID: {sessionId}</p>
      </div>

      <div className="results-tabs">
        <button 
          className={`tab-button ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button 
          className={`tab-button ${activeTab === 'questions' ? 'active' : ''}`}
          onClick={() => setActiveTab('questions')}
        >
          Questions & Answers
        </button>
        <button 
          className={`tab-button ${activeTab === 'code' ? 'active' : ''}`}
          onClick={() => setActiveTab('code')}
        >
          Code Submissions
        </button>
        <button 
          className={`tab-button ${activeTab === 'analytics' ? 'active' : ''}`}
          onClick={() => setActiveTab('analytics')}
        >
          Analytics
        </button>
        <button 
          className={`tab-button ${activeTab === 'feedback' ? 'active' : ''}`}
          onClick={() => setActiveTab('feedback')}
        >
          AI Feedback
        </button>
      </div>

      <div className="results-content">
        {activeTab === 'overview' && renderOverview()}
        {activeTab === 'questions' && renderQuestions()}
        {activeTab === 'code' && renderCodeSubmissions()}
        {activeTab === 'analytics' && renderAnalytics()}
        {activeTab === 'feedback' && renderFeedback()}
      </div>
    </div>
  );
};

export default InterviewResults;

