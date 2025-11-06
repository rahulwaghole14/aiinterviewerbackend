// CandidateDetails.jsx
import React, { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { FiChevronLeft } from 'react-icons/fi';
import { useDispatch, useSelector } from 'react-redux';
import { fetchCandidates } from '../redux/slices/candidatesSlice';
import { fetchJobs, selectAllJobs, selectJobsStatus } from '../redux/slices/jobsSlice';
import { baseURL } from '../data';
import "./CandidateDetails.css";
import BeatLoader from "react-spinners/BeatLoader";

const CandidateDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const allCandidates = useSelector((state) => state.candidates.allCandidates);
  const candidatesStatus = useSelector((state) => state.candidates.candidatesStatus);
  const allJobs = useSelector(selectAllJobs);
  const jobsStatus = useSelector(selectJobsStatus);
  
  const [candidate, setCandidate] = useState(null);
  const [loading, setLoading] = useState(true);

  // Helper function to get domain name by ID
  const getDomainName = (domainId) => {
    if (typeof domainId === 'string' && !/^[0-9]+$/.test(domainId)) {
      return domainId;
    }
    return domainId || 'N/A';
  };

  // Helper function to get job title by ID
  const getJobTitle = (jobId) => {
    if (typeof jobId === 'string' && !/^[0-9]+$/.test(jobId)) {
      return jobId;
    }
    const job = allJobs.find(j => String(j.id) === String(jobId));
    return job ? job.job_title : (jobId || 'N/A');
  };

  useEffect(() => {
    if (candidatesStatus === 'idle') {
      dispatch(fetchCandidates());
    }
    if (jobsStatus === 'idle') {
      dispatch(fetchJobs());
    }
  }, [candidatesStatus, jobsStatus, dispatch]);

  useEffect(() => {
    if (candidatesStatus === 'succeeded' && allCandidates) {
      const foundCandidate = allCandidates.find(c => String(c.id) === id);
      setCandidate(foundCandidate);
      setLoading(false);
    } else if (candidatesStatus === 'failed') {
      setLoading(false);
    }
  }, [id, candidatesStatus, allCandidates]);

  if (loading) {
    return (
      <div className="candidate-details-layout loading-container">
        <BeatLoader color="var(--color-primary-dark)" />
        <p>Loading candidate details...</p>
      </div>
    );
  }

  if (!candidate) {
    return (
      <div className="candidate-not-found-container">
        <p>Candidate not found.</p>
        <button className="back-to-candidates-btn" onClick={() => navigate('/candidates')}>Go to Candidates List</button>
      </div>
    );
  }

  return (
    <div className="candidate-details-layout">
      <div className="candidate-details-left-panel">
        <div className="candidate-details-content card">
          <div className="back-button-container">
            <button className="back-button" onClick={() => navigate(-1)}>
              <FiChevronLeft size={24} /> Back
            </button>
          </div>
          <div className="candidate-header-container">
            <h1 className="candidate-name-display">{candidate.full_name}</h1>
            <span className={`candidate-status-badge ${candidate.status?.toLowerCase().replace(' ', '-') || 'pending'}`}>
              {candidate.status || 'Pending'}
            </span>
          </div>
          <div className="details-grid">
            <p><strong>Email:</strong> {candidate.email}</p>
            <p><strong>Phone:</strong> {candidate.phone}</p>
            <p><strong>Experience:</strong> {candidate.workExperience} years</p>
            <p><strong>Domain:</strong> {getDomainName(candidate.domain)}</p>
            <p><strong>Job Title:</strong> {getJobTitle(candidate.jobRole)}</p>
            <p><strong>Applied On:</strong> {candidate.applicationDate ? new Date(candidate.applicationDate).toLocaleDateString() : 'N/A'}</p>
          </div>
          <hr className="details-divider" />
          <h3>POC Details</h3>
          <p><strong>POC Name:</strong> {candidate.poc_name || 'N/A'}</p>
          <p><strong>POC Email:</strong> {candidate.poc_email || 'N/A'}</p>
        </div>
      </div>

      <div className="candidate-details-right-panel">
        <div className="update-status-section card">
          <h3>Candidate Status</h3>
          <p>Current Status: <strong>{candidate.status || 'Pending'}</strong></p>
          <div className="basic-info-section">
            <h4>Basic Information</h4>
            <p><strong>Full Name:</strong> {candidate.full_name}</p>
            <p><strong>Email:</strong> {candidate.email}</p>
            <p><strong>Phone:</strong> {candidate.phone}</p>
            <p><strong>Work Experience:</strong> {candidate.workExperience} years</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CandidateDetails;

  const handleChange = (e) => {
    const { name, value } = e.target;
    setEditedInterview(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSlotDetails = (slot) => {
    setCurrentSlot(slot);
    setShowSlotDetails(true);
  };

  const handleCloseSlotDetails = () => {
    setShowSlotDetails(false);
  };

  const handleSlotUpdate = async (updatedSlot) => {
    try {
      const authToken = localStorage.getItem('authToken');
      if (!authToken) {
        console.error('Authentication token not found.');
        return;
      }

      const response = await fetch(`${baseURL}/api/interviews/slots/${updatedSlot.id}/`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${authToken}`,
        },
        body: JSON.stringify(updatedSlot),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const updatedData = await response.json();
      setCurrentSlot(updatedData);
      
      // Update the interview details with the new slot data
      setInterviewDetails(prev => prev.map(i => 
        i.slot?.id === updatedData.id ? { ...i, slot: updatedData } : i
      ));
      
      return true;
    } catch (error) {
      console.error("Failed to update slot:", error);
      throw error;
    }
  };

  const handleSlotDelete = async (slotId) => {
    try {
      const authToken = localStorage.getItem('authToken');
      if (!authToken) {
        console.error('Authentication token not found.');
        return;
      }

      const response = await fetch(`${baseURL}/api/interviews/slots/${slotId}/`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${authToken}`,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Remove the slot from the interview details
      setInterviewDetails(prev => prev.map(i => 
        i.slot?.id === slotId ? { ...i, slot: null } : i
      ));
      
      setShowSlotDetails(false);
      return true;
    } catch (error) {
      console.error("Failed to delete slot:", error);
      throw error;
    }
  };

  return (
    <div className={`modal-overlay ${showModal ? 'show' : ''}`}>
      <div className={`modal-content interview-modal-large ${showModal ? 'show' : ''}`}>
        <button className="modal-close-button" onClick={handleClose}>
          <FiX size={24} />
        </button>
        <h3>Interview Details</h3>
        
        {isEditing ? (
          <div className="edit-interview-form">
            <div className="form-group">
              <label>Interview Round</label>
              <input
                type="text"
                name="interview_round"
                value={editedInterview.interview_round || ''}
                onChange={handleChange}
                placeholder="e.g., Technical Round 1"
              />
            </div>
            <div className="form-group">
              <label>Status</label>
              <select
                name="status"
                value={editedInterview.status || ''}
                onChange={handleChange}
              >
                <option value="scheduled">Scheduled</option>
                <option value="completed">Completed</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>
            <div className="form-group">
              <label>Start Date & Time</label>
              <input
                type="datetime-local"
                name="started_at"
                value={editedInterview.started_at ? new Date(editedInterview.started_at).toISOString().slice(0, 16) : ''}
                onChange={handleChange}
              />
            </div>
            <div className="form-group">
              <label>End Date & Time</label>
              <input
                type="datetime-local"
                name="ended_at"
                value={editedInterview.ended_at ? new Date(editedInterview.ended_at).toISOString().slice(0, 16) : ''}
                onChange={handleChange}
              />
            </div>
            <div className="form-group">
              <label>Video URL</label>
              <input
                type="url"
                name="video_url"
                value={editedInterview.video_url || ''}
                onChange={handleChange}
                placeholder="https://meet.google.com/abc-defg-hij"
              />
            </div>
            <div className="form-group">
              <label>Feedback</label>
              <textarea
                name="feedback"
                value={editedInterview.feedback || ''}
                onChange={handleChange}
                rows="4"
              />
            </div>
            <div className="modal-actions">
              <button className="cancel-btn" onClick={handleCancelEdit}>
                Cancel
              </button>
              <button className="save-btn" onClick={handleSave} disabled={loading}>
                {loading ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        ) : (
          <>
            {interviewDetails && interviewDetails.length > 0 ? (
              interviewDetails.map((interview, index) => (
                <div key={index} className="interview-card">
                  <div className="interview-header">
                    <h4>Interview {index + 1}</h4>
                    <div className="interview-actions">
                      <button className="edit-btn" onClick={handleEdit}>
                        <FiEdit /> Edit
                      </button>
                      <button className="delete-btn" onClick={() => onDelete(interview.id)}>
                        <FiTrash2 /> Delete
                      </button>
                    </div>
                  </div>
                  
                  <div className="detail-row">
                    <FiInfo className="detail-icon" />
                    <span><strong>Round:</strong> {interview.interview_round || '-'}</span>
                  </div>
                  <div className="detail-row">
                    <FiCalendar className="detail-icon" />
                    <span><strong>Date:</strong> {interview.started_at ? new Date(interview.started_at).toLocaleDateString() : '-'}</span>
                  </div>
                  <div className="detail-row">
                    <FiClock className="detail-icon" />
                    <span><strong>Time:</strong> {interview.started_at ? new Date(interview.started_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', hour12: true}) : '-'}</span>
                  </div>
                  <div className="detail-row">
                    <span><strong>Status:</strong> <span className={`status-badge ${interview.status || ''}`}>{interview.status || '-'}</span></span>
                  </div>
                  {interview.video_url && (
                    <div className="detail-row">
                      <FiVideo className="detail-icon" />
                      <span><strong>Meeting Link:</strong> {interview.video_url !== '-' ? <a href={interview.video_url} target="_blank" rel="noopener noreferrer">{interview.video_url}</a> : '-'}</span>
                    </div>
                  )}
                  {interview.feedback && (
                    <div className="feedback-section">
                      <h5>Feedback:</h5>
                      <p>{interview.feedback || '-'}</p>
                    </div>
                  )}
                  
                  {interview.slot && (
                    <div className="slot-section">
                      <h5>Slot Details:</h5>
                      <div className="slot-info">
                        <p><strong>Type:</strong> {interview.slot.ai_interview_type}</p>
                        <p><strong>Configuration:</strong> {JSON.stringify(interview.slot.ai_configuration)}</p>
                        <button 
                          className="view-slot-btn"
                          onClick={() => handleSlotDetails(interview.slot)}
                        >
                          View Slot Details
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))
            ) : (
              <p>No interview details available. Please update the candidate status to schedule an interview.</p>
            )}
          </>
        )}
      </div>
      
      {showSlotDetails && currentSlot && (
        <SlotDetailsModal 
          slot={currentSlot}
          onClose={handleCloseSlotDetails}
          onUpdate={handleSlotUpdate}
          onDelete={handleSlotDelete}
        />
      )}
    </div>
  );
};

// Evaluation Modal Component
const EvaluationDetailModal = ({ evaluation, onClose }) => {
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    setShowModal(true);
  }, []);

  const handleClose = () => {
    setShowModal(false);
    setTimeout(onClose, 300);
  };

  return (
    <div className={`modal-overlay ${showModal ? 'show' : ''}`}>
      <div className={`modal-content evaluation-modal-large ${showModal ? 'show' : ''}`}>
        <button className="modal-close-button" onClick={handleClose}>
          <FiX size={24} />
        </button>
        <h3>Evaluation Details</h3>
        {evaluation ? (
          <>
            <div className="detail-row">
              <span><strong>Score:</strong> {evaluation.score || '-'}/10</span>
            </div>
            <div className="detail-row">
              <span><strong>Result:</strong> <span className={`eval-result ${evaluation.result?.toLowerCase() || ''}`}>{evaluation.result || '-'}</span></span>
            </div>
            {evaluation.interviewDuration && (
              <div className="detail-row">
                <span><strong>Interview Duration:</strong> {evaluation.interviewDuration || '-'}</span>
              </div>
            )}
            <div className="feedback-section">
              <h5>Feedback:</h5>
              <p>{evaluation.feedback || '-'}</p>
            </div>
            {evaluation.strengths && (
              <div className="strengths-section">
                <h5>Strengths:</h5>
                <p>{evaluation.strengths || '-'}</p>
              </div>
            )}
            {evaluation.areasForImprovement && (
              <div className="improvement-section">
                <h5>Areas for Improvement:</h5>
                <p>{evaluation.areasForImprovement || '-'}</p>
              </div>
            )}
            {evaluation.recommendation && (
              <div className="recommendation-section">
                <h5>Recommendation:</h5>
                <p>{evaluation.recommendation || '-'}</p>
              </div>
            )}
          </>
        ) : (
          <p>No evaluation details available. Please update the candidate status to complete evaluation.</p>
        )}
      </div>
    </div>
  );
};

// Create Slot Modal Component
const CreateSlotModal = ({ onClose, onCreate }) => {
  const [showModal, setShowModal] = useState(true);
  const [loading, setLoading] = useState(false);
  const [slotData, setSlotData] = useState({
    date: '',
    start_time: '09:00',
    end_time: '09:30',
    ai_interview_type: 'technical',
    max_candidates: 1,
    is_available: true,
    ai_configuration: {
      difficulty_level: 'intermediate',
      question_count: 10,
      time_limit: 60,
      topics: ['algorithms', 'data_structures']
    }
  });

  const handleClose = () => {
    setShowModal(false);
    setTimeout(onClose, 300);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setSlotData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleAiConfigChange = (e) => {
    const { name, value } = e.target;
    setSlotData(prev => ({
      ...prev,
      ai_configuration: {
        ...prev.ai_configuration,
        [name]: value
      }
    }));
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      await onCreate(slotData);
      handleClose();
    } catch (error) {
      console.error("Failed to create slot:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`modal-overlay ${showModal ? 'show' : ''}`}>
      <div className={`modal-content create-slot-modal ${showModal ? 'show' : ''}`}>
        <button className="modal-close-button" onClick={handleClose}>
          <FiX size={24} />
        </button>
        <h3>Create New Interview Slot</h3>
        
        <div className="form-group">
          <label>Date</label>
          <input 
            type="date" 
            name="date" 
            value={slotData.date} 
            onChange={handleChange} 
          />
        </div>
        <div className="form-group">
          <label>Start Time</label>
          <input 
            type="time" 
            name="start_time" 
            value={slotData.start_time} 
            onChange={handleChange} 
          />
        </div>
        <div className="form-group">
          <label>End Time</label>
          <input 
            type="time" 
            name="end_time" 
            value={slotData.end_time} 
            onChange={handleChange} 
          />
        </div>
        <div className="form-group">
                                  <label>Talaro Interview Type</label>
          <select 
            name="ai_interview_type" 
            value={slotData.ai_interview_type} 
            onChange={handleChange}
          >
            <option value="technical">Technical</option>
            <option value="behavioral">Behavioral</option>
            <option value="coding">Coding</option>
            <option value="system_design">System Design</option>
            <option value="case_study">Case Study</option>
          </select>
        </div>
        <div className="form-group">
          <label>Max Candidates</label>
          <input 
            type="number" 
            name="max_candidates" 
            value={slotData.max_candidates} 
            onChange={handleChange} 
            min="1"
          />
        </div>
        
        <div className="ai-config-section">
          <h4>AI Configuration</h4>
          <div className="form-group">
            <label>Difficulty Level</label>
            <select
              name="difficulty_level"
              value={slotData.ai_configuration.difficulty_level}
              onChange={handleAiConfigChange}
            >
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
              <option value="expert">Expert</option>
            </select>
          </div>
          <div className="form-group">
            <label>Question Count</label>
            <input
              type="number"
              name="question_count"
              value={slotData.ai_configuration.question_count}
              onChange={handleAiConfigChange}
              min="1"
              max="20"
            />
          </div>
          <div className="form-group">
            <label>Time Limit (minutes)</label>
            <input
              type="number"
              name="time_limit"
              value={slotData.ai_configuration.time_limit}
              onChange={handleAiConfigChange}
              min="15"
              max="120"
            />
          </div>
          <div className="form-group">
            <label>Topics (comma separated)</label>
            <input
              type="text"
              name="topics"
              value={slotData.ai_configuration.topics.join(', ')}
              onChange={(e) => handleAiConfigChange({
                target: {
                  name: 'topics',
                  value: e.target.value.split(',').map(t => t.trim())
                }
              })}
            />
          </div>
        </div>
        
        <div className="modal-actions">
          <button className="cancel-btn" onClick={handleClose}>
            Cancel
          </button>
          <button className="save-btn" onClick={handleSubmit} disabled={loading}>
            {loading ? 'Creating...' : 'Create Slot'}
          </button>
        </div>
      </div>
    </div>
  );
};

// Update Status Modal Component
const UpdateStatusModal = ({ candidate, interviewDetails, onClose, onSave }) => {
  const [showModal, setShowModal] = useState(true);
  const allJobs = useSelector(selectAllJobs);
  const jobsStatus = useSelector(selectJobsStatus);
  const dispatch = useDispatch();

  const processSteps = [
    "Requires Action",
    "Interview Pending",
    "Interview Scheduled",
    "Interview Completed",
    "Evaluated"
  ];

  const [selectedStatus, setSelectedStatus] = useState(candidate.status);
  const [interviewRound, setInterviewRound] = useState('');
  const [interviewDate, setInterviewDate] = useState(new Date());
  const [interviewTime, setInterviewTime] = useState([]);
  const [interviewDuration, setInterviewDuration] = useState('');
  const [evaluationRemark, setEvaluationRemark] = useState('');
  const [evaluationScore, setEvaluationScore] = useState('');
  const [evaluationResult, setEvaluationResult] = useState('');
  const [isBooking, setIsBooking] = useState(false);
  const [availableSlots, setAvailableSlots] = useState([]);
  const [allSlots, setAllSlots] = useState([]);
  const [showCreateSlotModal, setShowCreateSlotModal] = useState(false);

  // Error state variables
  const [dateError, setDateError] = useState('');
  const [timeError, setTimeError] = useState('');
  const [durationError, setDurationError] = useState('');
  const [scoreError, setScoreError] = useState('');
  const [resultError, setResultError] = useState('');
  const [feedbackError, setFeedbackError] = useState('');
  const [interviewRoundError, setInterviewRoundError] = useState('');
  const [jobMatchError, setJobMatchError] = useState('');

  const resetErrors = () => {
    setDateError('');
    setTimeError('');
    setDurationError('');
    setScoreError('');
    setResultError('');
    setFeedbackError('');
    setInterviewRoundError('');
    setJobMatchError('');
  };

  // Prefill interview details when interview is already scheduled
  useEffect(() => {
    if (candidate.status === "Interview Scheduled" && interviewDetails && interviewDetails.length > 0) {
      const interview = interviewDetails[0];
      
      if (interview.interview_round) {
        setInterviewRound(interview.interview_round);
      }
      
      if (interview.started_at) {
        const date = new Date(interview.started_at);
        setInterviewDate(date);
        
        const timeString = `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
        setInterviewTime([timeString]);
      }
    }
  }, [candidate.status, interviewDetails]);

  const handleScheduleInterview = async () => {
    if (!interviewRound.trim()) {
      setInterviewRoundError("Interview round is required.");
      return;
    }
    if (!interviewDate) {
      setDateError("Interview Date is required.");
      return;
    }
    if (interviewTime.length === 0) {
      setTimeError("Please select at least one time slot.");
      return;
    }

    try {
      setIsBooking(true);
      
      const authToken = localStorage.getItem('authToken');
      if (!authToken) {
        console.error('Authentication token not found.');
        setIsBooking(false);
        return;
      }

      const job = allJobs.find(j => String(j.id) === String(candidate.jobRole) || j.job_title === candidate.jobRole);
      if (!job) {
        setJobMatchError(`No matching job found for title: ${candidate.jobRole}`);
        console.error("Available jobs:", allJobs);
        setIsBooking(false);
        return;
      }

      // Create interview first
      const [timeHours, timeMinutes] = interviewTime[0].split(':');
      
      const interviewStart = new Date(interviewDate);
      interviewStart.setHours(timeHours, timeMinutes, 0, 0);

      const interviewEnd = new Date(interviewStart);
      interviewEnd.setHours(interviewEnd.getHours() + 1);

      const interviewPayload = {
        candidate: candidate.id,
        job: job.id,
        status: "scheduled",
        interview_round: interviewRound,
        feedback: "",
        started_at: interviewStart.toISOString(),
        ended_at: interviewEnd.toISOString(),
        video_url: "https://meet.google.com/test-interview"
      };

      const interviewResponse = await fetch(`${baseURL}/api/interviews/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${authToken}`,
        },
        body: JSON.stringify(interviewPayload),
      });

      if (!interviewResponse.ok) {
        const errorData = await interviewResponse.json();
        throw new Error(errorData.detail || `HTTP error! status: ${interviewResponse.status}`);
      }

      // Book the selected slots
      const interviewData = await interviewResponse.json();
      
      // Find the slot that matches our selected time
      const slot = allSlots.find(s => s.start_time === interviewTime[0]);
      if (slot) {
        const bookingData = {
          candidate_id: candidate.id,
          interview_id: interviewData.id
        };
        
        const bookingResponse = await fetch(`${baseURL}/api/interviews/slots/${slot.id}/book_slot/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Token ${authToken}`,
          },
          body: JSON.stringify(bookingData),
        });

        if (!bookingResponse.ok) {
          throw new Error(`Failed to book slot: ${bookingResponse.status}`);
        }
      }
      
      // Update candidate status
      const updatedCandidate = {
        ...candidate,
        status: "Interview Scheduled"
      };
      
      dispatch(updateCandidate({ id: candidate.id, updatedData: updatedCandidate }));
      
      // Close modal and refresh interview details
      handleClose();
      
    } catch (error) {
      console.error("Failed to schedule interview:", error);
    } finally {
      setIsBooking(false);
    }
  };

  const handleCreateSlot = async (slotData) => {
    try {
      setIsBooking(true);
      
      const authToken = localStorage.getItem('authToken');
      if (!authToken) {
        console.error('Authentication token not found.');
        setIsBooking(false);
        return;
      }

      const response = await fetch(`${baseURL}/api/interviews/slots/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${authToken}`,
        },
        body: JSON.stringify(slotData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      // Refresh available slots
      const data = await fetch(`${baseURL}/api/interviews/slots/?date=${interviewDate.toISOString().split('T')[0]}`, {
        method: 'GET',
        headers: {
          'Authorization': `Token ${authToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (!data.ok) {
        throw new Error(`Failed to fetch slots: ${data.status}`);
      }

      const slotsData = await data.json();
      
      // Update available and unavailable slots
      const available = [];
      const booked = [];
      
      if (slotsData.slots) {
        setAllSlots(slotsData.slots);
        
        slotsData.slots.forEach(slot => {
          if (slot.is_available) {
            available.push(slot.start_time);
          } else {
            booked.push(slot.start_time);
          }
        });
      } else {
        setAvailableSlots(slotsData.available_slots || []);
        setUnavailableSlots(slotsData.booked_slots || []);
        return;
      }
      
      setAvailableSlots(available);
      setUnavailableSlots(booked);
      
    } catch (error) {
      console.error("Failed to create slot:", error);
    } finally {
      setIsBooking(false);
    }
  };

  const isFormValid = () => {
    resetErrors();
    let isValid = true;

    if (selectedStatus === "Interview Scheduled") {
      if (!interviewRound.trim()) {
        setInterviewRoundError("Interview round is required.");
        isValid = false;
      }
      if (!interviewDate) {
        setDateError("Interview Date is required.");
        isValid = false;
      }
      if (interviewTime.length === 0) {
        setTimeError("Please select at least one time slot.");
        isValid = false;
      }
    }

    if (selectedStatus === "Interview Completed" || selectedStatus === "Evaluated") {
      if (!interviewDuration.trim()) {
        setDurationError("Interview Duration is required.");
        isValid = false;
      }
      if (!evaluationScore) {
        setScoreError("Evaluation Score is required.");
        isValid = false;
      } else if (isNaN(parseFloat(evaluationScore))) {
        setScoreError("Score must be a number.");
        isValid = false;
      } else if (parseFloat(evaluationScore) < 0 || parseFloat(evaluationScore) > 10) {
        setScoreError("Score must be between 0 and 10.");
        isValid = false;
      }
      if (!evaluationResult.trim()) {
        setResultError("Evaluation Result is required.");
        isValid = false;
      }
      if (!evaluationRemark.trim()) {
        setFeedbackError("Feedback is required.");
        isValid = false;
      }
    }

    return isValid;
  };

  const formatTimeForDisplay = (time24hr) => {
    if (!time24hr) return '';
    const [hourStr, minuteStr] = time24hr.split(':');
    let hour = parseInt(hourStr, 10);
    const minutes = minuteStr;
    const ampm = hour >= 12 ? 'PM' : 'AM';
    hour = hour % 12;
    hour = hour === 0 ? 12 : hour;
    return `${hour}:${minutes} ${ampm}`;
  };

  const getDisplayRange = (times) => {
    if (times.length === 0) {
      return (
        <div className="empty-time-slot-boxes">
          <div className="empty-time-slot-box">No time selected</div>
        </div>
      );
    }

    const sortedTimes = [...times].sort();
    const formattedSegments = [];
    let currentSegment = [];

    const addSegment = (segment) => {
      if (segment.length === 0) return;
      const first = segment[0];
      const last = segment[segment.length - 1];

      const [lastHourStr, lastMinuteStr] = last.split(':');
      let lastHour = parseInt(lastHourStr, 10);
      let lastMinute = parseInt(lastMinuteStr, 10);

      lastMinute += 30;
      if (lastMinute >= 60) {
        lastMinute -= 60;
        lastHour += 1;
      }
      const endOfLastSlot24hr = `${String(lastHour).padStart(2, '0')}:${String(lastMinute).padStart(2, '0')}`;

      formattedSegments.push(
        `${formatTimeForDisplay(first)} - ${formatTimeForDisplay(endOfLastSlot24hr)}`
      );
    };

    for (let i = 0; i < sortedTimes.length; i++) {
      const currentTime = sortedTimes[i];
      if (currentSegment.length === 0) {
        currentSegment.push(currentTime);
      } else {
        const prevTime = currentSegment[currentSegment.length - 1];
        const [prevHour, prevMinute] = prevTime.split(':').map(Number);
        let expectedCurrentHour = prevHour;
        let expectedCurrentMinute = prevMinute + 30;

        if (expectedCurrentMinute >= 60) {
          expectedCurrentMinute -= 60;
          expectedCurrentHour += 1;
        }
        const expectedCurrentTime = `${String(expectedCurrentHour).padStart(2, '0')}:${String(expectedCurrentMinute).padStart(2, '0')}`;

        if (expectedCurrentTime === currentTime) {
          currentSegment.push(currentTime);
        } else {
          addSegment(currentSegment);
          currentSegment = [currentTime];
        }
      }
    }
    addSegment(currentSegment);

    const formattedDate = interviewDate.toLocaleString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
    return (
      <div className="selected-time-slot-boxes">
        {formattedSegments.slice(0, 1).map((segment, index) => (
          <div key={index} className="selected-time-slot-box">
            {`${formattedDate}, ${segment}`}
          </div>
        ))}
      </div>
    );
  };

  const isDateFullyBooked = (_date) => {
    return false;
  };

  const handleSaveCurrentStepData = async () => {
    if (!isFormValid()) {
      return;
    }

    try {
      const authToken = localStorage.getItem('authToken');
      if (!authToken) {
        console.error('Authentication token not found.');
        return;
      }

      const job = allJobs.find(j => String(j.id) === String(candidate.jobRole) || j.job_title === candidate.jobRole);
      if (!job && selectedStatus === "Interview Scheduled") {
        setJobMatchError(`No matching job found for title: ${candidate.jobRole}`);
        console.error("Available jobs:", allJobs);
        return;
      }

      const formattedTimeSlots = interviewTime.map(time => {
        const [hours, minutes] = time.split(':');
        return `${hours}:${minutes}`;
      });

      const updatedFormData = {
        interviewDetails: {
          ...candidate.interviewDetails,
          date: interviewDate ? interviewDate.toISOString().slice(0, 10) : candidate?.interviewDetails?.date,
          timeSlots: formattedTimeSlots,
        },
        evaluation: {
          ...candidate.evaluation,
          interviewDuration: interviewDuration || candidate?.evaluation?.interviewDuration,
          score: evaluationScore || candidate?.evaluation?.score,
          result: evaluationResult || candidate?.evaluation?.result,
          feedback: evaluationRemark || candidate?.evaluation?.feedback,
        }
      };

      const candidateUpdatePayload = {
        ...candidate,
        status: selectedStatus,
        lastUpdated: new Date().toISOString().slice(0, 10),
        ...updatedFormData
      };

      const updateResponse = await fetch(`${baseURL}/api/candidates/${candidate.id}/`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${authToken}`,
        },
        body: JSON.stringify(candidateUpdatePayload),
      });

      if (!updateResponse.ok) {
        const errorData = await updateResponse.json();
        throw new Error(errorData.detail || `HTTP error! status: ${updateResponse.status}`);
      }

      const updatedCandidateData = await updateResponse.json();
      dispatch(updateCandidate({ id: candidate.id, updatedData: updatedCandidateData }));

      if (selectedStatus === 'Interview Scheduled' && interviewDate && interviewTime.length > 0) {
        await handleScheduleInterview();
      }

      onSave(selectedStatus, updatedFormData);

    } catch (error) {
      console.error("Failed to update candidate or schedule interview:", error);
    } finally {
      setIsBooking(false);
    }
  };

  const handleClose = () => {
    setShowModal(false);
    setTimeout(onClose, 300);
  };

  const getFormForStatus = (status) => {
    switch (status) {
      case "Interview Scheduled":
        return (
          <div className="status-update-form">
            <h4 className="form-title">Schedule Interview</h4>
            {jobMatchError && <p className="error-message">{jobMatchError}</p>}
            <div className="form-group">
              <label>Interview Round</label>
              <input
                type="text"
                value={interviewRound}
                onChange={(e) => setInterviewRound(e.target.value)}
                placeholder="e.g., Technical Round 1"
              />
              {interviewRoundError && <p className="error-message">{interviewRoundError}</p>}
            </div>
            <div className="form-group">
              <label>Date</label>
              <HorizontalDatePicker
                selectedDate={interviewDate}
                onSelectDate={setInterviewDate}
                isDateFullyBooked={isDateFullyBooked}
              />
              {dateError && <p className="error-message">{dateError}</p>}
            </div>
            <div className="form-group">
              <label>Select Time Slot</label>
              <div className="time-slot-picker-container">
                <TimeSlotPicker
                  selectedTimes={interviewTime}
                  onSelectTimes={setInterviewTime}
                  selectedDate={interviewDate}
                  baseURL={baseURL}
                  setAvailableSlots={setAvailableSlots}
                  setAllSlots={setAllSlots}
                  isBooking={isBooking}
                  setIsBooking={setIsBooking}
                />
                <button 
                  className="create-slot-btn"
                  onClick={() => setShowCreateSlotModal(true)}
                >
                  <FiPlus /> Create New Slot
                </button>
              </div>
              {timeError && <p className="error-message">{timeError}</p>}
              <p className="instruction-text">To select multiple slots, hold <b>Ctrl</b> and click the boxes</p>
            </div>
            <div className="selected-slots-display-section">
              <h4>Selected Time Slot:</h4>
              {getDisplayRange(interviewTime)}
            </div>
          </div>
        );
      case "Interview Completed":
      case "Evaluated":
        return (
          <div className="status-update-form">
            <h4 className="form-title">Complete Evaluation</h4>
            <div className="form-group">
              <label>Interview Duration (e.g., 60 mins)</label>
              <input
                type="text"
                value={interviewDuration}
                onChange={(e) => setInterviewDuration(e.target.value)}
              />
              {durationError && <p className="error-message">{durationError}</p>}
            </div>
            <div className="form-group">
              <label>Evaluation Score (0-10)</label>
              <input
                type="number"
                value={evaluationScore}
                onChange={(e) => setEvaluationScore(e.target.value)}
                min="0"
                max="10"
              />
              {scoreError && <p className="error-message">{scoreError}</p>}
            </div>
            <div className="form-group">
              <label>Evaluation Result</label>
              <select
                value={evaluationResult}
                onChange={(e) => setEvaluationResult(e.target.value)}
              >
                <option value="">Select Result</option>
                <option value="Hired">Hired</option>
                <option value="Rejected">Rejected</option>
                <option value="On Hold">On Hold</option>
              </select>
              {resultError && <p className="error-message">{resultError}</p>}
            </div>
            <div className="form-group">
              <label>Feedback</label>
              <textarea
                value={evaluationRemark}
                onChange={(e) => setEvaluationRemark(e.target.value)}
              />
              {feedbackError && <p className="error-message">{feedbackError}</p>}
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className={`modal-overlay ${showModal ? 'show' : ''}`}>
      <div className={`modal-content ${showModal ? 'show' : ''}`}>
        <button className="modal-close-button" onClick={handleClose}>
          <FiX size={24} />
        </button>
        <h3>Update Status</h3>
        {jobsStatus === 'loading' && (
          <div className="loading-container">
            <BeatLoader color="var(--color-primary-dark)" size={10} />
            <p>Loading jobs data...</p>
          </div>
        )}
        {jobsStatus === 'failed' && (
          <div className="error-container">
            <p>Error loading jobs data. Please try again.</p>
            <button onClick={() => dispatch(fetchJobs())}>Retry</button>
          </div>
        )}
        {jobsStatus === 'succeeded' && (
          <>
            <div className="process-status-container">
              {processSteps.map((step, index) => (
                <div 
                  key={index} 
                  className={`process-step ${step === selectedStatus ? 'active' : ''} ${index < processSteps.indexOf(selectedStatus) ? 'completed' : ''}`}
                  onClick={() => setSelectedStatus(step)}
                  style={{ cursor: 'pointer' }}
                >
                  <div className="step-number">{index + 1}</div>
                  <p>{step}</p>
                </div>
              ))}
            </div>

            {getFormForStatus(selectedStatus)}

            <div className="modal-actions">
              <button className="status-nav-btn close-btn" onClick={handleClose}>
                Close
              </button>
              <button 
                className="status-nav-btn save-btn" 
                onClick={handleSaveCurrentStepData}
                disabled={jobsStatus !== 'succeeded'}
              >
                {selectedStatus === 'Interview Scheduled' && isBooking ? 'Scheduling...' : selectedStatus === 'Interview Scheduled' ? 'Schedule Interview' : 'Save Changes'}
              </button>
            </div>
          </>
        )}
      </div>
      
      {showCreateSlotModal && (
        <CreateSlotModal 
          onClose={() => setShowCreateSlotModal(false)}
          onCreate={handleCreateSlot}
        />
      )}
    </div>
  );
};


// Candidate Details Page
const CandidateDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const allCandidates = useSelector((state) => state.candidates.allCandidates);
  const candidatesStatus = useSelector((state) => state.candidates.candidatesStatus);
  const allJobs = useSelector(selectAllJobs);
  const jobsStatus = useSelector(selectJobsStatus);
  const [showAiScheduler, setShowAiScheduler] = useState(false);
  const [candidate, setCandidate] = useState(null);
  const [interviewDetails, setInterviewDetails] = useState([]);
  const [interviewDetailsLoading, setInterviewDetailsLoading] = useState(false);
  const [interviewDetailsLoaded, setInterviewDetailsLoaded] = useState(false);
  const [loading, setLoading] = useState(true);

  const [showInterviewModal, setShowInterviewModal] = useState(false);
  const [showEvaluationModal, setShowEvaluationModal] = useState(false);
  const [showUpdateStatusModal, setShowUpdateStatusModal] = useState(false);

  // Helper function to get domain name by ID
  const getDomainName = (domainId) => {
    if (typeof domainId === 'string' && !/^[0-9]+$/.test(domainId)) {
      return domainId;
    }
    return domainId || 'N/A';
  };

  // Helper function to get job title by ID
  const getJobTitle = (jobId) => {
    if (typeof jobId === 'string' && !/^[0-9]+$/.test(jobId)) {
      return jobId;
    }
    const job = allJobs.find(j => String(j.id) === String(jobId));
    return job ? job.job_title : (jobId || 'N/A');
  };

  // Determine candidate status based on interview details
  const getCandidateStatus = () => {
    if (!interviewDetails || interviewDetails.length === 0) {
      return "Requires Action";
    }
    
    const latestInterview = interviewDetails[0];
    
    if (latestInterview.status === "scheduled") {
      return "Interview Scheduled";
    } else if (latestInterview.status === "completed") {
      if (candidate.evaluation && candidate.evaluation.score) {
        return "Evaluated";
      }
      return "Interview Completed";
    } else if (latestInterview.status === "cancelled") {
      return "Requires Action";
    }
    
    return "Requires Action";
  };

  useEffect(() => {
    if (candidatesStatus === 'idle') {
      dispatch(fetchCandidates());
    }
    if (jobsStatus === 'idle') {
      dispatch(fetchJobs());
    }
  }, [candidatesStatus, jobsStatus, dispatch]);

  useEffect(() => {
    if (candidatesStatus === 'succeeded' && allCandidates) {
      const foundCandidate = allCandidates.find(c => String(c.id) === id);
      setCandidate(foundCandidate);
      if (foundCandidate) {
        fetchInterviewDetails(foundCandidate.id);
      } else {
        setLoading(false);
      }
    } else if (candidatesStatus === 'failed') {
      setLoading(false);
    }
  }, [id, candidatesStatus, allCandidates]);

  const fetchInterviewDetails = async (candidateId) => {
    try {
      setInterviewDetailsLoading(true);
      const authToken = localStorage.getItem('authToken');
      if (!authToken) {
        console.error('Authentication token not found.');
        setInterviewDetailsLoading(false);
        setInterviewDetailsLoaded(true);
        return;
      }

      // Fetch interviews for the candidate
      const response = await fetch(`${baseURL}/api/interviews/?candidate=${candidateId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${authToken}`,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const candidateInterviews = await response.json();
      
      // For each interview, fetch the associated slot details
      const interviewsWithSlots = await Promise.all(candidateInterviews.map(async (interview) => {
        if (interview.slot) {
          const slotResponse = await fetch(`${baseURL}/api/interviews/slots/${interview.slot}/`, {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Token ${authToken}`,
            },
          });
          
          if (slotResponse.ok) {
            const slotData = await slotResponse.json();
            return { ...interview, slot: slotData };
          }
        }
        return interview;
      }));

      setInterviewDetails(interviewsWithSlots);

    } catch (error) {
      console.error("Failed to fetch interview details:", error);
    } finally {
      setInterviewDetailsLoading(false);
      setInterviewDetailsLoaded(true);
      setLoading(false);
    }
  };

  const handleUpdateInterview = async (updatedInterview) => {
    try {
      const authToken = localStorage.getItem('authToken');
      if (!authToken) {
        console.error('Authentication token not found.');
        return;
      }

      const response = await fetch(`${baseURL}/api/interviews/${updatedInterview.id}/`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${authToken}`,
        },
        body: JSON.stringify(updatedInterview),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const updatedData = await response.json();
      setInterviewDetails(prev => prev.map(i => i.id === updatedData.id ? updatedData : i));
      
      // If the interview has a slot, refetch the slot details
      if (updatedData.slot) {
        const slotResponse = await fetch(`${baseURL}/api/interviews/slots/${updatedData.slot}/`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Token ${authToken}`,
          },
        });
        
        if (slotResponse.ok) {
          const slotData = await slotResponse.json();
          setInterviewDetails(prev => prev.map(i => 
            i.id === updatedData.id ? { ...updatedData, slot: slotData } : i
          ));
        }
      }

      return true;
    } catch (error) {
      console.error("Failed to update interview:", error);
      throw error;
    }
  };

  const handleDeleteInterview = async (interviewId) => {
    try {
      const authToken = localStorage.getItem('authToken');
      if (!authToken) {
        console.error('Authentication token not found.');
        return;
      }

      const response = await fetch(`${baseURL}/api/interviews/${interviewId}/`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${authToken}`,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      setInterviewDetails(prev => prev.filter(i => i.id !== interviewId));
      return true;
    } catch (error) {
      console.error("Failed to delete interview:", error);
      throw error;
    }
  };

  const handleSaveStatus = (newStatus, updatedData) => {
    if (candidate) {
      const updatedCandidate = {
        ...candidate,
        status: newStatus,
        ...updatedData,
      };
      setCandidate(updatedCandidate);
      dispatch(updateCandidate({ id: candidate.id, updatedData: updatedCandidate }));
    }
  };

  if (loading || (candidate && !interviewDetailsLoaded)) {
    return (
      <div className="candidate-details-layout loading-container">
        <BeatLoader color="var(--color-primary-dark)" />
        <p>Loading candidate details...</p>
      </div>
    );
  }

  if (!candidate) {
    return (
      <div className="candidate-not-found-container">
        <p>Candidate not found.</p>
        <button className="back-to-candidates-btn" onClick={() => navigate('/candidates')}>Go to Candidates List</button>
      </div>
    );
  }

  const candidateStatus = getCandidateStatus();

  if (showAiScheduler) {
    return (
      <AiInterviewScheduler
        candidate={candidate}
        onClose={() => setShowAiScheduler(false)}
        onSchedule={(slot) => {
          // Update candidate status to "Interview Scheduled"
          const updatedCandidate = {
            ...candidate,
            status: "Interview Scheduled"
          };
          dispatch(updateCandidate({ id: candidate.id, updatedData: updatedCandidate }));
          setShowAiScheduler(false);
        }}
        baseURL={baseURL}
      />
    );
  }

  return (
    <div className="candidate-details-layout">
      <div className="candidate-details-left-panel">
        <div className="candidate-details-content card">
          <div className="back-button-container">
            <button className="back-button" onClick={() => navigate(-1)}>
              <FiChevronLeft size={24} /> Back
            </button>
          </div>
          <div className="candidate-header-container">
            <h1 className="candidate-name-display">{candidate.full_name}</h1>
            <span className={`candidate-status-badge ${candidateStatus.toLowerCase().replace(' ', '-')}`}>
              {candidateStatus}
            </span>
          </div>
          <div className="details-grid">
            <p><strong>Email:</strong> {candidate.email}</p>
            <p><strong>Phone:</strong> {candidate.phone}</p>
            <p><strong>Experience:</strong> {candidate.workExperience} years</p>
            <p><strong>Domain:</strong> {getDomainName(candidate.domain)}</p>
            <p><strong>Job Title:</strong> {getJobTitle(candidate.jobRole)}</p>
            <p><strong>Applied On:</strong> {candidate.applicationDate ? new Date(candidate.applicationDate).toLocaleDateString() : 'N/A'}</p>
          </div>
          <hr className="details-divider" />
          <h3>POC Details</h3>
          <p><strong>POC Name:</strong> {candidate.poc_name || 'N/A'}</p>
          <p><strong>POC Email:</strong> {candidate.poc_email || 'N/A'}</p>
        </div>
      </div>

      <div className="candidate-details-right-panel">
        <div className="update-status-section card">
          <h3>Candidate Status</h3>
          <p>Current Status: <strong>{candidateStatus}</strong></p>
          <div className="process-status-container mt-2">
            <div className={`process-step ${candidateStatus === 'Requires Action' ? 'active' : ''} ${candidateStatus !== 'Requires Action' ? 'completed' : ''}`}>
              <div className="step-number">1</div>
              <p>Requires Action</p>
            </div>
            <div className={`process-step ${candidateStatus === 'Interview Pending' ? 'active' : ''} ${['Interview Scheduled', 'Interview Completed', 'Evaluated'].includes(candidateStatus) ? 'completed' : ''}`}>
              <div className="step-number">2</div>
              <p>Interview Pending</p>
            </div>
            <div className={`process-step ${candidateStatus === 'Interview Scheduled' ? 'active' : ''} ${['Interview Completed', 'Evaluated'].includes(candidateStatus) ? 'completed' : ''}`}>
              <div className="step-number">3</div>
              <p>Interview Scheduled</p>
            </div>
            <div className={`process-step ${candidateStatus === 'Interview Completed' ? 'active' : ''} ${candidateStatus === 'Evaluated' ? 'completed' : ''}`}>
              <div className="step-number">4</div>
              <p>Interview Completed</p>
            </div>
            <div className={`process-step ${candidateStatus === 'Evaluated' ? 'active' : ''}`}>
              <div className="step-number">5</div>
              <p>Evaluated</p>
            </div>
          </div>
         <button
  className="save-status-btn mt-4"
  onClick={() => setShowAiScheduler(true)}
>
                  Schedule Talaro Interview
</button>
        </div>

        <div className="interview-summary-card card" onClick={() => setShowInterviewModal(true)}>
          <h3>Interview Details</h3>
          {interviewDetailsLoading ? (
            <p>Loading interview details...</p>
          ) : interviewDetails && interviewDetails.length > 0 ? (
            <>
              <p>Round: {interviewDetails[0].interview_round}</p>
              <p>Status: {interviewDetails[0].status}</p>
              <p>Scheduled On: {new Date(interviewDetails[0].started_at).toLocaleDateString()}</p>
              <p>Time: {new Date(interviewDetails[0].started_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', hour12: true})}</p>
              <span className="view-details-link">View More</span>
            </>
          ) : (
            <p>Interview needs to be scheduled.</p>
          )}
        </div>

        <div className="evaluation-summary-card card" onClick={() => setShowEvaluationModal(true)}>
          <h3>Evaluation Details</h3>
          {candidate.evaluation ? (
            <>
              <p>Score: {candidate.evaluation.score || '-'}/10</p>
              <p>Result: {candidate.evaluation.result || '-'}</p>
              {candidate.evaluation.interviewDuration && <p>Interview Duration: {candidate.evaluation.interviewDuration || '-'}</p>}
              <p>Feedback: {candidate.evaluation.feedback || '-'}</p>
              <span className="view-details-link">View More</span>
            </>
          ) : (
            <p>Evaluation needs to be completed.</p>
          )}
        </div>
      </div>

      {showInterviewModal && (
        <InterviewDetailModal
          interviewDetails={interviewDetails}
          onClose={() => setShowInterviewModal(false)}
          onUpdate={handleUpdateInterview}
          onDelete={handleDeleteInterview}
        />
      )}
      {showEvaluationModal && (
        <EvaluationDetailModal
          evaluation={candidate.evaluation}
          onClose={() => setShowEvaluationModal(false)}
        />
      )}
      
    </div>
  );
};

export default CandidateDetails;