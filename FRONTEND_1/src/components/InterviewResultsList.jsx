import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { BeatLoader } from 'react-spinners';
import { baseURL } from '../config/constants';
import CustomDropdown from './common/CustomDropdown';
import './InterviewResultsList.css';

const InterviewResultsList = () => {
  const navigate = useNavigate();
  
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    fetchInterviewSessions();
  }, []);

  const fetchInterviewSessions = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('authToken');
      
      if (!token) {
        setError('Authentication required');
        return;
      }

      const response = await fetch(`${baseURL}/interview_app/api/results/`, {
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch interview sessions');
      }

      const data = await response.json();
      setSessions(data.sessions);

    } catch (err) {
      console.error('Error fetching interview sessions:', err);
      setError(err.message);
      toast.error('Failed to load interview sessions');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString() + ' ' + new Date(dateString).toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };

  const getScoreColor = (score) => {
    if (score === null || score === undefined) return '#6c757d';
    if (score >= 8) return '#28a745';
    if (score >= 6) return '#ffc107';
    return '#dc3545';
  };

  const formatScore = (score) => {
    if (score === null || score === undefined) return 'N/A';
    return `${score}/10`;
  };

  const getStatusColor = (status) => {
    switch (status.toLowerCase()) {
      case 'scheduled':
        return '#ffc107';
      case 'completed':
        return '#28a745';
      case 'expired':
        return '#dc3545';
      default:
        return '#6c757d';
    }
  };

  const filteredSessions = sessions.filter(session => {
    const matchesSearch = session.candidate_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         session.candidate_email.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || session.status.toLowerCase() === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const handleViewResults = (sessionId) => {
    navigate(`/interview-results/${sessionId}`);
  };

  if (loading) {
    return (
      <div className="interview-results-list">
        <div className="loading-container">
          <BeatLoader color="var(--color-primary)" size={15} />
          <h2>Loading Interview Sessions...</h2>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="interview-results-list">
        <div className="error-container">
          <div className="error-icon">⚠️</div>
          <h2>Error Loading Sessions</h2>
          <p>{error}</p>
          <button 
            className="retry-button"
            onClick={fetchInterviewSessions}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="interview-results-list">
      <div className="list-header">
        <h1>Interview Results</h1>
        <p>View and analyze interview session results</p>
      </div>

      <div className="filters-section">
        <div className="search-filter">
          <input
            type="text"
            placeholder="Search by candidate name or email..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
        </div>
        
        <div className="status-filter">
          <CustomDropdown
            value={statusFilter}
            options={[
              { value: 'all', label: 'All Status' },
              { value: 'scheduled', label: 'Scheduled' },
              { value: 'completed', label: 'Completed' },
              { value: 'expired', label: 'Expired' }
            ]}
            onChange={(value) => setStatusFilter(value)}
            placeholder="All Status"
          />
        </div>
      </div>

      <div className="sessions-stats">
        <div className="stat-card">
          <span className="stat-number">{sessions.length}</span>
          <span className="stat-label">Total Sessions</span>
        </div>
        <div className="stat-card">
          <span className="stat-number">
            {sessions.filter(s => s.status === 'COMPLETED').length}
          </span>
          <span className="stat-label">Completed</span>
        </div>
        <div className="stat-card">
          <span className="stat-number">
            {sessions.filter(s => s.is_evaluated).length}
          </span>
          <span className="stat-label">Evaluated</span>
        </div>
        <div className="stat-card">
          <span className="stat-number">
            {sessions.filter(s => s.status === 'SCHEDULED').length}
          </span>
          <span className="stat-label">Scheduled</span>
        </div>
      </div>

      {filteredSessions.length === 0 ? (
        <div className="no-sessions">
          <div className="no-sessions-icon">📋</div>
          <h2>No Interview Sessions Found</h2>
          <p>
            {searchTerm || statusFilter !== 'all' 
              ? 'No sessions match your current filters. Try adjusting your search criteria.'
              : 'No interview sessions have been created yet.'
            }
          </p>
        </div>
      ) : (
        <div className="sessions-grid">
          {filteredSessions.map((session) => (
            <div key={session.session_id} className="session-card">
              <div className="session-header">
                <div className="candidate-info">
                  <h3>{session.candidate_name}</h3>
                  <p>{session.candidate_email}</p>
                </div>
                <div 
                  className="status-badge"
                  style={{ backgroundColor: getStatusColor(session.status) }}
                >
                  {session.status}
                </div>
              </div>

              <div className="session-details">
                <div className="detail-item">
                  <label>Scheduled:</label>
                  <span>{formatDate(session.scheduled_at)}</span>
                </div>
                <div className="detail-item">
                  <label>Completed:</label>
                  <span>{formatDate(session.completed_at)}</span>
                </div>
                <div className="detail-item">
                  <label>Questions:</label>
                  <span>{session.answered_questions}/{session.total_questions}</span>
                </div>
                <div className="detail-item">
                  <label>Code Submissions:</label>
                  <span>{session.code_submissions}</span>
                </div>
                <div className="detail-item">
                  <label>Warnings:</label>
                  <span>{session.warning_count}</span>
                </div>
              </div>

              {session.is_evaluated && (
                <div className="evaluation-scores">
                  <h4>Evaluation Scores</h4>
                  <div className="scores-row">
                    <div className="score-item">
                      <label>Resume:</label>
                      <span 
                        className="score-value"
                        style={{ color: getScoreColor(session.resume_score) }}
                      >
                        {formatScore(session.resume_score)}
                      </span>
                    </div>
                    <div className="score-item">
                      <label>Answers:</label>
                      <span 
                        className="score-value"
                        style={{ color: getScoreColor(session.answers_score) }}
                      >
                        {formatScore(session.answers_score)}
                      </span>
                    </div>
                    <div className="score-item">
                      <label>Overall:</label>
                      <span 
                        className="score-value"
                        style={{ color: getScoreColor(session.overall_performance_score) }}
                      >
                        {formatScore(session.overall_performance_score)}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              <div className="session-actions">
                <button
                  className="view-results-btn"
                  onClick={() => handleViewResults(session.session_id)}
                >
                  View Detailed Results
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default InterviewResultsList;

