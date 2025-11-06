// CandidateDetails.jsx
import React, { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { FiChevronLeft } from "react-icons/fi";
import { useDispatch, useSelector } from "react-redux";
import { fetchCandidates } from "../redux/slices/candidatesSlice";
import {
  fetchJobs,
  selectAllJobs,
  selectJobsStatus,
} from "../redux/slices/jobsSlice";
import { baseURL } from "../data";
import "./CandidateDetails.css";
import "./common/DataTable.css";
import BeatLoader from "react-spinners/BeatLoader";
import StatusUpdateModal from "./StatusUpdateModal";
import { useNotification } from "../hooks/useNotification";
import { formatTimeTo12Hour } from "../utils/timeFormatting";
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

// Helper function to safely parse JSON fields
const parseJsonField = (field) => {
  if (!field) return [];
  if (typeof field === 'string') {
    try {
      return JSON.parse(field);
    } catch (e) {
      return [];
    }
  }
  return Array.isArray(field) ? field : [];
};

const CandidateDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const notify = useNotification();

  const allCandidates = useSelector((state) => state.candidates.allCandidates);
  const candidatesStatus = useSelector(
    (state) => state.candidates.candidatesStatus
  );
  const allJobs = useSelector(selectAllJobs);
  const jobsStatus = useSelector(selectJobsStatus);

  const [candidate, setCandidate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [interviews, setInterviews] = useState([]);
  const [interviewsLoading, setInterviewsLoading] = useState(false);
  const [authToken, setAuthToken] = useState("");

  // Get auth token from localStorage when component mounts
  useEffect(() => {
    const token = localStorage.getItem("authToken");
    if (token) {
      setAuthToken(token);
    } else {
      // Authentication token not found
      // navigate('/login');
    }
  }, []);

  // Modal states
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [selectedAction, setSelectedAction] = useState(null);
  const [showEditInterviewModal, setShowEditInterviewModal] = useState(false);
  const [editingInterview, setEditingInterview] = useState(null);
  const [showEditEvaluationModal, setShowEditEvaluationModal] = useState(false);
  const [editingEvaluation, setEditingEvaluation] = useState(null);
  
  // Delete confirmation modal states
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteType, setDeleteType] = useState(null); // 'interview' or 'evaluation'
  const [itemToDelete, setItemToDelete] = useState(null);

  // Helper function to get domain name by ID
  const getDomainName = (domainId) => {
    if (typeof domainId === "string" && !/^[0-9]+$/.test(domainId)) {
      return domainId;
    }
    return domainId || "N/A";
  };

  // Helper function to get job title by ID
  const getJobTitle = (jobId) => {
    if (typeof jobId === "string" && !/^[0-9]+$/.test(jobId)) {
      return jobId;
    }
    const job = allJobs.find((j) => String(j.id) === String(jobId));
    return job ? job.job_title : jobId || "N/A";
  };

  // Fetch interviews and evaluations
  const fetchInterviews = async () => {
    if (!candidate?.id || !authToken) return;

    setInterviewsLoading(true);
    try {
      // Fetch interviews
      const interviewsResponse = await fetch(`${baseURL}/api/interviews/`, {
        method: "GET",
        headers: {
          Authorization: `Token ${authToken}`,
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        credentials: "include",
      });

      if (!interviewsResponse.ok) {
        if (interviewsResponse.status === 401) {
          localStorage.removeItem("authToken");
          navigate("/login");
          return;
        }
        throw new Error(`HTTP error! status: ${interviewsResponse.status}`);
      }

      // Fetch evaluations
      const evaluationsResponse = await fetch(
        `${baseURL}/api/evaluation/crud/`,
        {
          method: "GET",
          headers: {
            Authorization: `Token ${authToken}`,
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          credentials: "include",
        }
      );

      if (!evaluationsResponse.ok) {
        // Don't throw error here as evaluations might be optional
      }

      const interviewsData = await interviewsResponse.json();
      const evaluationsData = evaluationsResponse.ok
        ? await evaluationsResponse.json()
        : [];

      // Process fetched data
      console.log('=== RAW API RESPONSE DEBUG ===');
      console.log('Interviews API response:', interviewsData);
      console.log('Evaluations API response:', evaluationsData);
      console.log('Candidate ID:', candidate.id, 'Type:', typeof candidate.id);
      
      // Process interviews and evaluations
      const allInterviews = Array.isArray(interviewsData)
        ? interviewsData
        : interviewsData.results || [];
      
      // Debug: Log first few interviews to see candidate field structure
      if (allInterviews.length > 0) {
        console.log('Sample interview structure:', {
          first_interview: allInterviews[0],
          candidate_field: allInterviews[0].candidate,
          candidate_type: typeof allInterviews[0].candidate,
          candidate_object: allInterviews[0].candidate_object
        });
      }
      
      // Filter interviews - handle different candidate field formats
      const candidateInterviews = allInterviews.filter((interview) => {
        // Convert both to strings for comparison to handle type mismatches
        const candidateIdStr = String(candidate.id);
        const interviewCandidateStr = interview.candidate 
          ? String(interview.candidate) 
          : null;
        const candidateObjectIdStr = interview.candidate_object?.id 
          ? String(interview.candidate_object.id) 
          : null;
        
        const matches = 
          interviewCandidateStr === candidateIdStr ||
          candidateObjectIdStr === candidateIdStr;
        
        if (!matches) {
          console.log(`Interview ${interview.id} doesn't match:`, {
            interview_candidate: interview.candidate,
            interview_candidate_type: typeof interview.candidate,
            candidate_object_id: interview.candidate_object?.id,
            candidate_id: candidate.id
          });
        }
        
        return matches;
      });
      
      console.log('Filtered candidate interviews:', candidateInterviews);
      candidateInterviews.forEach(interview => {
        console.log(`Interview ${interview.id} from API:`, {
          status: interview.status,
          ai_result: interview.ai_result,
          has_ai_result: !!interview.ai_result
        });
      });

      // Process candidate interviews

      // For each interview, fetch the associated slot details directly from slots API (same as AI Interview Scheduler)
      const interviewsWithSlots = await Promise.all(candidateInterviews.map(async (interview) => {
        // Process interview slot
        
        if (interview.slot) {
          try {
            // Fetch slot details
            const slotResponse = await fetch(`${baseURL}/api/interviews/slots/${interview.slot}/`, {
              method: "GET",
              headers: {
                Authorization: `Token ${authToken}`,
                "Content-Type": "application/json",
                Accept: "application/json",
              },
              credentials: "include",
            });

            if (slotResponse.ok) {
              const slotData = await slotResponse.json();
              // Process slot data
              
              // Create slot_details object with the same structure as AI Interview Scheduler
              const slotDetails = {
                id: slotData.id,
                start_time: slotData.start_time,
                end_time: slotData.end_time,
                duration_minutes: slotData.duration_minutes,
                ai_interview_type: slotData.ai_interview_type,
                status: slotData.status,
                current_bookings: slotData.current_bookings,
                max_candidates: slotData.max_candidates,
                interview_date: slotData.interview_date
              };
              
              console.log(`Created slot_details for interview ${interview.id}:`, slotDetails);
              console.log(`Slot details start_time: "${slotDetails.start_time}"`);
              console.log(`Slot details end_time: "${slotDetails.end_time}"`);
              
              return { 
                ...interview, 
                slot_details: slotDetails,
                slot: slotData // Keep original slot data too
              };
            } else {
              console.error(`Failed to fetch slot ${interview.slot}:`, slotResponse.status);
              return interview;
            }
          } catch (error) {
            console.error(`Error fetching slot ${interview.slot}:`, error);
            return interview;
          }
        }
        
        return interview;
      }));

      console.log("Interviews with slots:", interviewsWithSlots);

      // Add evaluations to interviews and extract ai_result if needed
      const processedInterviews = interviewsWithSlots.map((interview) => {
        // Find matching evaluation if exists
        const evaluation = Array.isArray(evaluationsData)
          ? evaluationsData.find(
              (evalItem) => String(evalItem.interview) === String(interview.id)
            )
          : null;

        // If interview doesn't have ai_result but evaluation has details.ai_analysis, extract it
        let aiResult = interview.ai_result;
        if (!aiResult && evaluation && evaluation.details && evaluation.details.ai_analysis) {
          const aiAnalysis = evaluation.details.ai_analysis;
          // Transform ai_analysis to ai_result format
          aiResult = {
            overall_score: (aiAnalysis.overall_score || 0) / 10.0,
            total_score: (aiAnalysis.overall_score || 0) / 10.0,
            technical_score: (aiAnalysis.technical_score || 0) / 10.0,
            behavioral_score: (aiAnalysis.behavioral_score || 0) / 10.0,
            coding_score: (aiAnalysis.coding_score || 0) / 10.0,
            communication_score: (aiAnalysis.communication_score || 0) / 10.0,
            strengths: aiAnalysis.strengths || '',
            weaknesses: aiAnalysis.weaknesses || '',
            technical_analysis: aiAnalysis.technical_analysis || '',
            behavioral_analysis: aiAnalysis.behavioral_analysis || '',
            coding_analysis: aiAnalysis.coding_analysis || '',
            detailed_feedback: aiAnalysis.detailed_feedback || '',
            hiring_recommendation: aiAnalysis.hiring_recommendation || '',
            recommendation: aiAnalysis.recommendation || 'MAYBE',
            hire_recommendation: ['STRONG_HIRE', 'HIRE'].includes(aiAnalysis.recommendation),
            confidence_level: (aiAnalysis.confidence_level || 0) / 10.0,
            proctoring_pdf_url: evaluation.details.proctoring_pdf_url || null,
            proctoring_warnings: evaluation.details.proctoring?.warnings || [],
          };
          console.log(`✅ Extracted ai_result from evaluation for interview ${interview.id}`);
        }

        return {
          ...interview,
          evaluation: evaluation || null,
          ai_result: aiResult || interview.ai_result || null,
        };
      });

      console.log("Processed interviews with evaluations and slots:", processedInterviews);
      
      // Debug: Log interview status and ai_result for debugging
      processedInterviews.forEach(interview => {
        console.log(`=== Interview ${interview.id} Debug ===`);
        console.log('Status:', interview.status);
        console.log('Has ai_result:', !!interview.ai_result);
        console.log('ai_result:', interview.ai_result);
        console.log('ai_result keys:', interview.ai_result ? Object.keys(interview.ai_result) : null);
        console.log('ai_result.total_score:', interview.ai_result?.total_score);
        console.log('Will show in UI?', interview.ai_result && (interview.status === 'completed' || interview.status === 'COMPLETED' || interview.status?.toLowerCase() === 'completed'));
        console.log('==========================');
      });
      
      setInterviews(processedInterviews);
    } catch (error) {
      console.error("Error fetching data:", error);
    } finally {
      setInterviewsLoading(false);
    }
  };

  // Function to update interview status
  const updateInterviewStatus = async (interviewId, status) => {
    if (!authToken) {
      console.error("Authentication token not found");
      return;
    }

    try {
      const response = await fetch(
        `${baseURL}/api/interviews/${interviewId}/`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Token ${authToken}`,
          },
          body: JSON.stringify({ status }),
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Refresh the interviews data
      fetchInterviews();
    } catch (error) {
      console.error("Error updating interview status:", error);
    }
  };

  // Determine current status based on interviews and candidate status
  const getCurrentStatus = () => {
    // First check if candidate has been hired or rejected
    if (candidate?.status === "HIRED") return "HIRED";
    if (candidate?.status === "REJECTED") return "REJECTED";
    
    if (!interviews.length) return "NEW";

    const latestInterview = interviews[interviews.length - 1];
    const status = latestInterview.status?.toLowerCase();

    // Check if there's any AI evaluation for any interview
    const hasAIEvaluation = interviews.some((i) => i.ai_result);
    
    // Also check for legacy evaluation system
    const hasLegacyEvaluation = interviews.some((i) => i.evaluation);

    // Handle new status structure
    if (hasLegacyEvaluation && hasAIEvaluation) return "AI_MANUAL_EVALUATED";
    if (hasLegacyEvaluation) return "MANUAL_EVALUATED";
    if (hasAIEvaluation) return "AI_EVALUATED";
    if (status === "completed") return "INTERVIEW_COMPLETED";
    if (status === "scheduled") return "INTERVIEW_SCHEDULED";

    return "NEW";
  };

  // Available actions based on current status
  const availableActions = [
    {
      id: "schedule_interview",
      label: "Schedule Interview",
      status: "INTERVIEW_SCHEDULED",
    },
    { id: "manual_evaluate", label: "Manual Evaluation", status: "MANUAL_EVALUATED" },
    { id: "hire_reject", label: "Make Decision", status: "HIRED" },
  ];

  // Get the next available action based on current status
  const getNextAction = (currentStatus) => {
    switch (currentStatus) {
      case "NEW":
        return { id: "schedule_interview", status: "INTERVIEW_SCHEDULED" };
      case "INTERVIEW_SCHEDULED":
        return { id: "complete_interview", status: "INTERVIEW_COMPLETED" };
      case "INTERVIEW_COMPLETED":
        // After interview completed, next step is manual evaluation (can be done even without AI evaluation)
        return { id: "manual_evaluate", status: "MANUAL_EVALUATED" };
      case "AI_EVALUATED":
        // After AI evaluation, next step is manual evaluation
        return { id: "manual_evaluate", status: "MANUAL_EVALUATED" };
      case "MANUAL_EVALUATED":
        return { id: "hire_reject", status: "HIRE" }; // Show hire option
      default:
        return null;
    }
  };

  // Handle status update
  const handleStatusUpdate = async (action) => {
    if (action === "schedule_interview") {
      setSelectedAction("schedule_interview");
      setShowStatusModal(true);
    } else if (action === "manual_evaluate") {
      setSelectedAction("manual_evaluate");
      setShowStatusModal(true);
    } else if (action === "hire_reject") {
      setSelectedAction("hire_reject");
      setShowStatusModal(true);
    } else if (action === "complete_interview") {
      // Find the latest scheduled interview
      const latestInterview = interviews.find(
        (interview) => interview.status?.toLowerCase() === "scheduled"
      );

      if (latestInterview) {
        try {
          await updateInterviewStatus(latestInterview.id, "completed");
          // Refresh interviews data
          await fetchInterviews();
        } catch (error) {
          console.error("Error completing interview:", error);
        }
      }
    }
  };

  const handleModalClose = () => {
    setShowStatusModal(false);
    setSelectedAction(null);
    // Refresh both interviews and candidate data after modal closes
    fetchInterviews();
    // Refresh candidate data from Redux
    dispatch(fetchCandidates());
  };

  // Interview management handlers
  const handleEditInterview = (interview) => {
    console.log("Edit interview:", interview);
    setEditingInterview(interview);
    setShowEditInterviewModal(true);
  };



  // Evaluation management handlers
  const handleEditEvaluation = (evaluation) => {
    console.log("Edit evaluation:", evaluation);
    console.log("Evaluation data structure:", {
      overall_score: evaluation.overall_score,
      traits: evaluation.traits,
      suggestions: evaluation.suggestions,
      created_at: evaluation.created_at
    });
    setEditingEvaluation(evaluation);
    setShowEditEvaluationModal(true);
  };

  const handleDeleteEvaluation = (evaluation) => {
    setDeleteType('evaluation');
    setItemToDelete(evaluation);
    setShowDeleteModal(true);
  };

  const confirmDeleteEvaluation = async () => {
    try {
      const authToken = localStorage.getItem("authToken");
      if (!authToken) {
        notify.error("Authentication token not found");
        return;
      }

      // Delete the evaluation
      const response = await fetch(`${baseURL}/api/evaluations/${itemToDelete.id}/`, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Token ${authToken}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to delete evaluation: ${response.status}`);
      }

      notify.success("Evaluation deleted successfully!");
      
      // Refresh data
      fetchInterviews();
      dispatch(fetchCandidates());
      
      // Close modal
      setShowDeleteModal(false);
      setDeleteType(null);
      setItemToDelete(null);
    } catch (error) {
      console.error("Error deleting evaluation:", error);
      notify.error(error.message || "Failed to delete evaluation");
    }
  };

  const handleDeleteInterview = (interview) => {
    setDeleteType('interview');
    setItemToDelete(interview);
    setShowDeleteModal(true);
  };

  const confirmDeleteInterview = async () => {
    try {
      const authToken = localStorage.getItem("authToken");
      if (!authToken) {
        notify.error("Authentication token not found");
        return;
      }

      // First, release the slot if it exists
      const slotId = itemToDelete.slot || itemToDelete.slot_details?.id;
      if (slotId) {
        try {
          const releaseResponse = await fetch(`${baseURL}/api/interviews/slots/${slotId}/release_slot/`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Token ${authToken}`,
            },
          });

          if (releaseResponse.ok) {
            console.log("Slot released successfully");
          } else {
            console.warn("Failed to release slot, but continuing with interview deletion");
          }
        } catch (slotError) {
          console.warn("Error releasing slot:", slotError);
          // Continue with interview deletion even if slot release fails
        }
      }

      // Delete the interview
      const response = await fetch(`${baseURL}/api/interviews/${itemToDelete.id}/`, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Token ${authToken}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to delete interview: ${response.status}`);
      }

      notify.success("Interview deleted and slot released successfully!");
      
      // Refresh data
      fetchInterviews();
      dispatch(fetchCandidates());
      
      // Close modal
      setShowDeleteModal(false);
      setDeleteType(null);
      setItemToDelete(null);
    } catch (error) {
      console.error("Error deleting interview:", error);
      notify.error(error.message || "Failed to delete interview");
    }
  };



  useEffect(() => {
    if (candidatesStatus === "idle") {
      dispatch(fetchCandidates());
    }
    if (jobsStatus === "idle") {
      dispatch(fetchJobs());
    }
  }, [candidatesStatus, jobsStatus, dispatch]);

  useEffect(() => {
    if (candidatesStatus === "succeeded" && allCandidates) {
      const foundCandidate = allCandidates.find((c) => String(c.id) === id);
      setCandidate(foundCandidate);
      setLoading(false);
    } else if (candidatesStatus === "failed") {
      setLoading(false);
    }
  }, [id, candidatesStatus, allCandidates]);

  // Additional effect to update candidate when allCandidates changes (for status updates)
  useEffect(() => {
    if (allCandidates && candidate?.id) {
      const updatedCandidate = allCandidates.find((c) => String(c.id) === candidate.id);
      if (updatedCandidate && (
        updatedCandidate.status !== candidate.status ||
        updatedCandidate.last_updated !== candidate.last_updated
      )) {
        console.log("Updating candidate from allCandidates:", {
          oldStatus: candidate.status,
          newStatus: updatedCandidate.status,
          oldLastUpdated: candidate.last_updated,
          newLastUpdated: updatedCandidate.last_updated
        });
        setCandidate(updatedCandidate);
      }
    }
  }, [allCandidates, candidate?.id]);

  useEffect(() => {
    if (candidate) {
      fetchInterviews();
    }
  }, [candidate]);

  // Handle evaluation submission
  const handleEvaluationSubmit = async (evaluationData) => {
    const token = localStorage.getItem("authToken");
    if (!token) {
      notify.error("Authentication token not found. Please log in again.");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${baseURL}/api/evaluations/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Token ${token}`,
        },
        body: JSON.stringify({
          ...evaluationData,
          candidate: candidate.id,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error("Error response:", errorData);
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Refresh the data with a slight delay to ensure backend processing is complete
      setTimeout(async () => {
        await fetchInterviews();
      }, 1000);
      setShowStatusModal(false);
      notify.success("Evaluation submitted successfully!");
    } catch (error) {
      console.error("Error submitting evaluation:", error);
      notify.error(
        error.message || "Failed to submit evaluation. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

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
        <button
          className="back-to-candidates-btn"
          onClick={() => navigate("/candidates")}
        >
          Go to Candidates List
        </button>
      </div>
    );
  }

  const currentStatus = getCurrentStatus();

  // Don't show actions if candidate is hired or rejected
  const shouldShowActions = currentStatus !== "HIRED" && currentStatus !== "REJECTED";

  return (
    <>
      <div className={`candidate-details-layout ${showStatusModal ? 'blur-background' : ''}`}>
      <div className="candidate-details-left-panel" style={{ paddingBottom: '50px' }}>
        <div className="candidate-details-content card">
          <div className="candidate-main-layout">
            <div className="candidate-info-section">
          <div className="back-button-container">
            <button className="back-button" onClick={() => navigate(-1)}>
              <FiChevronLeft size={24} /> Back
            </button>
          </div>
              
            <h1 className="candidate-name-display">
              {candidate.name || "N/A"}
            </h1>
              
          <div className="details-grid">
            <div className="detail-row">
              <span className="detail-label">Email:</span>
              <span className="detail-value">{candidate.email}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Phone:</span>
              <span className="detail-value">{candidate.phone}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Experience:</span>
              <span className="detail-value">
                {candidate.workExperience} years
              </span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Domain:</span>
              <span className="detail-value">
                {getDomainName(candidate.domain)}
              </span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Job Title:</span>
              <span className="detail-value">
                {getJobTitle(candidate.jobRole)}
              </span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Applied On:</span>
              <span className="detail-value">
                {candidate.applicationDate
                  ? (() => {
                      try {
                        const date = new Date(candidate.applicationDate);
                        return isNaN(date.getTime()) ? "N/A" : date.toLocaleDateString();
                      } catch (error) {
                        console.error("Error parsing application date:", error);
                        return "N/A";
                      }
                    })()
                  : "N/A"}
              </span>
            </div>
                <div className="detail-row">
                  <span className="detail-label">Status:</span>
                  <span className="detail-value">
                    <span className={`status-badge ${currentStatus.toLowerCase()}`}>
                      {currentStatus.replace(/_/g, " ")}
                    </span>
                  </span>
          </div>
                <div className="detail-row">
                  <span className="detail-label">Last Updated:</span>
                  <span className="detail-value">
                    {candidate.last_updated
                      ? (() => {
                          try {
                            const date = new Date(candidate.last_updated);
                            return isNaN(date.getTime()) ? "N/A" : date.toLocaleDateString() + ' ' + date.toLocaleTimeString('en-US', {
                              hour: 'numeric',
                              minute: '2-digit',
                              hour12: true
                            });
                          } catch (error) {
                            console.error("Error parsing last updated date:", error);
                            return "N/A";
                          }
                        })()
                      : "N/A"}
                  </span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Interview Count:</span>
                  <span className="detail-value">
                    {interviews.length} interview{interviews.length !== 1 ? 's' : ''}
                  </span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">AI Evaluated:</span>
                  <span className="detail-value">
                    {interviews.some((i) => i.ai_result) ? (
                      <span className="status-indicator evaluated">Yes</span>
                    ) : (
                      <span className="status-indicator pending">No</span>
                    )}
                  </span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Manual Evaluated:</span>
                  <span className="detail-value">
                    {interviews.some((i) => i.evaluation) ? (
                      <span className="status-indicator evaluated">Yes</span>
                    ) : (
                      <span className="status-indicator pending">No</span>
                    )}
                  </span>
                </div>
              </div>
            </div>
            
            {/* Hire Recommendation - Right side */}
            {interviews.some((i) => i.ai_result) && (
              <div className="hire-recommendation-section">
                <div className="hire-recommendation-card">
                  <div className="hire-status-row">
                    <span className="label">Hire Status:</span>
                    <span className={`value recommendation ${interviews.find(i => i.ai_result)?.ai_result.hire_recommendation ? "recommended" : "not-recommended"}`}>
                      {interviews.find(i => i.ai_result)?.ai_result.hire_recommendation ? "RECOMMENDED" : "NOT RECOMMENDED"}
                    </span>
                  </div>
                  {interviews.find(i => i.ai_result)?.ai_result.total_score !== undefined && (
                    <div className="score-row">
                      <span className="label">Score:</span>
                      <span className={`value score-value ${interviews.find(i => i.ai_result)?.ai_result.total_score >= 8 ? "high-score" : interviews.find(i => i.ai_result)?.ai_result.total_score >= 6 ? "medium-score" : "low-score"}`}>
                        {interviews.find(i => i.ai_result)?.ai_result.total_score?.toFixed(1) || "N/A"}/10
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          <hr className="details-divider" />
          <h3>POC Details</h3>
          <div className="poc-details-section">
            <p>
              <strong>POC Email:</strong> {candidate.poc || "N/A"}
            </p>
          </div>
        </div>

        {/* AI Evaluation Results Section - Matching Image Design */}
        <div className="evaluation-section card">
          {(() => {
            const interviewsWithAIResult = interviews.filter(i => i.ai_result);
            return interviewsWithAIResult.length > 0;
          })() && (
            <div className="ai-evaluation-results">
              <div className="evaluation-header-section">
                <h3 className="evaluation-title">AI Evaluation Results</h3>
                {interviews.find(i => i.ai_result)?.ai_result?.overall_rating && (
                  <span className={`overall-rating-badge ${interviews.find(i => i.ai_result)?.ai_result.overall_rating?.toLowerCase() || "fair"}`}>
                    {interviews.find(i => i.ai_result)?.ai_result.overall_rating?.toUpperCase() || "FAIR"}
                  </span>
                )}
              </div>
              
              {interviews
                .filter((i) => i.ai_result)
                .map((interview) => {
                  try {
                    const aiResult = interview.ai_result;
                    const qaData = interview.questions_and_answers || [];
                    
                    // Separate technical and coding questions
                    const technicalQuestions = qaData.filter(qa => 
                      qa.question_type === 'TECHNICAL' || qa.question_type === 'BEHAVIORAL' || !qa.question_type
                    );
                    const codingQuestions = qaData.filter(qa => qa.question_type === 'CODING');
                    
                    // Calculate TECHNICAL metrics only (for Interview Overview and Question Accuracy)
                    const technicalTotalQuestions = technicalQuestions.length || 0;
                    const technicalCorrectAnswers = technicalQuestions.filter(qa => {
                      // Estimate correctness from answer quality (simple heuristic)
                      const answer = (qa.answer || '').toLowerCase();
                      return answer && 
                             answer !== 'no answer provided' && 
                             answer !== "i don't know" && 
                             answer !== 'no thank you' &&
                             answer.length > 10;
                    }).length;
                    const technicalIncorrectAnswers = technicalTotalQuestions - technicalCorrectAnswers;
                    const technicalAccuracy = technicalTotalQuestions > 0 
                      ? (technicalCorrectAnswers / technicalTotalQuestions * 100) 
                      : 0;
                    
                    // Calculate CODING metrics
                    const codingTotalQuestions = codingQuestions.length || 0;
                    const codingCorrectAnswers = codingQuestions.filter(qa => {
                      const answer = (qa.answer || '').toLowerCase();
                      return answer && answer !== 'no answer provided' && answer.length > 10;
                    }).length;
                    const codingIncorrectAnswers = codingTotalQuestions - codingCorrectAnswers;
                    const codingAccuracy = codingTotalQuestions > 0 
                      ? (codingCorrectAnswers / codingTotalQuestions * 100) 
                      : 0;
                    
                    // Overall metrics (for display purposes, but we'll show separate sections)
                    const totalQuestions = technicalTotalQuestions + codingTotalQuestions;
                    const correctAnswers = technicalCorrectAnswers + codingCorrectAnswers;
                    const incorrectAnswers = totalQuestions - correctAnswers;
                    const accuracy = totalQuestions > 0 ? (correctAnswers / totalQuestions * 100) : 0;
                    const totalCompletionTime = aiResult.total_completion_time || 54.6;
                    
                    // Section scores (0-10 scale, convert to percentage)
                    const technicalScore = (aiResult.technical_score || 0) * 10;
                    const behavioralScore = (aiResult.behavioral_score || 0) * 10;
                    const codingScore = (aiResult.coding_score || 0) * 10;
                    const communicationScore = (aiResult.communication_score || 0) * 10;
                    const problemSolvingScore = (aiResult.problem_solving_score || 0) * 10;
                    
                    // Overall rating
                    const overallRating = aiResult.overall_rating || 'FAIR';
                    
                    // Strengths and weaknesses
                    const strengths = parseJsonField(aiResult.strengths);
                    const weaknesses = parseJsonField(aiResult.weaknesses);
                    
                    // Question accuracy chart data - TECHNICAL ONLY
                    const technicalAccuracyChartData = [
                      { name: 'Correct', value: technicalCorrectAnswers, color: '#4CAF50' },
                      { name: 'Incorrect', value: technicalIncorrectAnswers, color: '#F44336' }
                    ];
                    
                    // Coding accuracy chart data
                    const codingAccuracyChartData = [
                      { name: 'Correct', value: codingCorrectAnswers, color: '#4CAF50' },
                      { name: 'Incorrect', value: codingIncorrectAnswers, color: '#F44336' }
                    ];
                    
                    // Section scores data for bar chart
                    const sectionScoresData = [
                      { name: 'Technical', score: technicalScore, fullScore: 100 },
                      { name: 'Behavioral', score: behavioralScore, fullScore: 100 },
                      { name: 'Coding', score: codingScore, fullScore: 100 },
                      { name: 'Communication', score: communicationScore, fullScore: 100 },
                      { name: 'Problem Solving', score: problemSolvingScore, fullScore: 100 },
                    ];
                    
                    return (
                      <div key={interview.id} className="ai-evaluation-wrapper">
                        <div className="ai-evaluation-layout">
                          {/* Left Column - Metrics Grid */}
                          <div className="ai-evaluation-left">
                            {/* Row 1: Performance Metrics */}
                            <div className="metrics-row-1">
                              {/* Technical Performance Metrics Card */}
                              <div className="evaluation-card performance-metrics-card">
                                <h4 className="card-title">Technical Performance Metrics</h4>
                                <div className="metrics-grid">
                                  <div className="metric-circle">
                                    <div className="circle-chart" style={{ 
                                      background: `conic-gradient(#2196F3 0% ${technicalTotalQuestions > 0 ? (technicalTotalQuestions/12)*100 : 0}%, #e0e0e0 ${technicalTotalQuestions > 0 ? (technicalTotalQuestions/12)*100 : 0}% 100%)`
                                    }}>
                                      <span className="circle-value">{technicalTotalQuestions}</span>
                                    </div>
                                    <div className="circle-label">Questions Attempted</div>
                                  </div>
                                  <div className="metric-circle">
                                    <div className="circle-chart" style={{ 
                                      background: `conic-gradient(#4CAF50 0% ${technicalTotalQuestions > 0 ? (technicalCorrectAnswers/technicalTotalQuestions)*100 : 0}%, #e0e0e0 ${technicalTotalQuestions > 0 ? (technicalCorrectAnswers/technicalTotalQuestions)*100 : 0}% 100%)`
                                    }}>
                                      <span className="circle-value">{technicalCorrectAnswers}</span>
                                    </div>
                                    <div className="circle-label">Questions Correct</div>
                                  </div>
                                  <div className="metric-circle">
                                    <div className="circle-chart" style={{ 
                                      background: `conic-gradient(#7B2CBF 0% ${technicalAccuracy}%, #e0e0e0 ${technicalAccuracy}% 100%)`
                                    }}>
                                      <span className="circle-value">{technicalAccuracy.toFixed(0)}%</span>
                                    </div>
                                    <div className="circle-label">Accuracy (%)</div>
                                  </div>
                                </div>
                              </div>
                              
                              {/* Coding Performance Metrics Card */}
                              {codingTotalQuestions > 0 && (
                                <div className="evaluation-card performance-metrics-card">
                                  <h4 className="card-title">Coding Performance Metrics</h4>
                                  <div className="metrics-grid">
                                    <div className="metric-circle">
                                      <div className="circle-chart" style={{ 
                                        background: `conic-gradient(#2196F3 0% ${codingTotalQuestions > 0 ? (codingTotalQuestions/12)*100 : 0}%, #e0e0e0 ${codingTotalQuestions > 0 ? (codingTotalQuestions/12)*100 : 0}% 100%)`
                                      }}>
                                        <span className="circle-value">{codingTotalQuestions}</span>
                                      </div>
                                      <div className="circle-label">Questions Attempted</div>
                                    </div>
                                    <div className="metric-circle">
                                      <div className="circle-chart" style={{ 
                                        background: `conic-gradient(#4CAF50 0% ${codingTotalQuestions > 0 ? (codingCorrectAnswers/codingTotalQuestions)*100 : 0}%, #e0e0e0 ${codingTotalQuestions > 0 ? (codingCorrectAnswers/codingTotalQuestions)*100 : 0}% 100%)`
                                      }}>
                                        <span className="circle-value">{codingCorrectAnswers}</span>
                                      </div>
                                      <div className="circle-label">Questions Correct</div>
                                    </div>
                                    <div className="metric-circle">
                                      <div className="circle-chart" style={{ 
                                        background: `conic-gradient(#7B2CBF 0% ${codingAccuracy}%, #e0e0e0 ${codingAccuracy}% 100%)`
                                      }}>
                                        <span className="circle-value">{codingAccuracy.toFixed(0)}%</span>
                                      </div>
                                      <div className="circle-label">Accuracy (%)</div>
                                    </div>
                                  </div>
                                </div>
                              )}
                            </div>
                            
                            {/* Row 2: Time Metrics and Detailed Section Scores */}
                            <div className="metrics-row-2">
                              {/* Time Metrics Card */}
                              <div className="evaluation-card time-metrics-card">
                                <h4 className="card-title">Time Metrics</h4>
                                <div className="time-metrics-content">
                                  <div className="time-metric">
                                    <div className="time-value-box" style={{ backgroundColor: '#FFEBEE' }}>
                                      <div className="time-icon">⏱️</div>
                                      <div className="time-value">{totalCompletionTime.toFixed(1)}min</div>
                                    </div>
                                    <div className="time-label">Total Completion Time</div>
                                    <div className="time-total">Total: {totalCompletionTime.toFixed(1)} minutes</div>
                                  </div>
                                </div>
                              </div>
                              
                              {/* Detailed Section Scores Card */}
                              <div className="evaluation-card detailed-scores-card">
                                <h4 className="card-title">Detailed Section Scores</h4>
                                <div className="detailed-scores-list">
                                  {sectionScoresData.map((section, idx) => (
                                    <div key={idx} className="detailed-score-item">
                                      <div className="score-label">{section.name}</div>
                                      <div className="score-value">{((section.score/100) * 10).toFixed(1)}/10</div>
                                      <div className="progress-bar-horizontal">
                                        <div 
                                          className="progress-fill" 
                                          style={{ 
                                            width: `${section.score}%`, 
                                            backgroundColor: section.score >= 60 ? '#2196F3' : '#FF9800' 
                                          }}
                                        ></div>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            </div>
                            
                            {/* Other Cards Below (Strengths, Improvement, Summary, Proctoring) */}
                            <div className="other-cards-grid">
                              {/* Strengths Card */}
                              <div className="evaluation-card strengths-card">
                                <h4 className="card-title">
                                  <span className="card-icon">✅</span> Strengths
                                </h4>
                                <div className="strengths-list">
                                  {strengths.length > 0 ? (
                                    strengths.map((strength, idx) => (
                                      <div key={idx} className="strength-tag">{strength}</div>
                                    ))
                                  ) : (
                                    <div className="strength-tag">Strong analytical thinking</div>
                                  )}
                                </div>
                              </div>
                              
                              {/* Areas for Improvement Card */}
                              <div className="evaluation-card improvement-card">
                                <h4 className="card-title">
                                  <span className="card-icon">🔧</span> Areas for Improvement
                                </h4>
                                <div className="improvement-list">
                                  {weaknesses.length > 0 ? (
                                    weaknesses.map((weakness, idx) => (
                                      <div key={idx} className="improvement-tag">{weakness}</div>
                                    ))
                                  ) : (
                                    <div className="improvement-tag">Could improve on time management</div>
                                  )}
                                </div>
                              </div>
                              
                              {/* Summary Card */}
                              <div className="evaluation-card summary-card">
                                <h4 className="card-title">Summary</h4>
                                <p className="summary-text">
                                  {aiResult.detailed_feedback || aiResult.ai_summary || 'The candidate demonstrated solid technical knowledge and good problem-solving abilities.'}
                                </p>
                              </div>
                              
                              {/* Proctoring Warnings Report - Download Link */}
                              <div className="evaluation-card proctoring-report-card">
                                <h4 className="card-title">Proctoring Warnings Report</h4>
                                {aiResult.proctoring_pdf_url ? (
                                  <div className="proctoring-download-section">
                                    <a 
                                      href={`${baseURL}${aiResult.proctoring_pdf_url}`}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="proctoring-download-link"
                                    >
                                      <span className="download-icon">📄</span>
                                      <span>Download Proctoring Warnings Report</span>
                                    </a>
                                    {aiResult.proctoring_warnings && aiResult.proctoring_warnings.length > 0 && (
                                      <div className="proctoring-warning-info">
                                        <strong>Total Warnings: {aiResult.proctoring_warnings.length}</strong>
                                      </div>
                                    )}
                                  </div>
                                ) : (
                                  <div className="no-proctoring-report">
                                    <p>No proctoring warnings report available for this interview.</p>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  } catch (error) {
                    console.error('Error rendering evaluation for interview:', interview.id, error);
                    return (
                      <div key={interview.id} className="evaluation-error">
                        <p className="error-text">Error loading evaluation data. Please try refreshing.</p>
                      </div>
                    );
                  }
                })}
            </div>
          )}

          {/* No Evaluation Message with Debug Info */}
          {!interviews.some((i) => i.ai_result) && (
            <div className="no-evaluation-message">
              <p className="no-data">{`${
                currentStatus === "INTERVIEW_COMPLETED"
                  ? "Evaluation in progress..."
                  : "No evaluation available"
              }`}</p>
              <details style={{ marginTop: '10px', fontSize: '0.9em', color: '#666', cursor: 'pointer' }}>
                <summary style={{ cursor: 'pointer', padding: '5px' }}>🔍 Debug Info (Click to expand)</summary>
                <pre style={{ 
                  marginTop: '10px', 
                  padding: '10px', 
                  background: '#f5f5f5', 
                  borderRadius: '4px', 
                  overflow: 'auto',
                  fontSize: '0.85em',
                  maxHeight: '300px'
                }}>
                  {JSON.stringify(interviews.map(i => ({
                    id: i.id,
                    status: i.status,
                    has_ai_result: !!i.ai_result,
                    ai_result_type: typeof i.ai_result,
                    ai_result_is_null: i.ai_result === null,
                    ai_result_is_undefined: i.ai_result === undefined,
                    ai_result_keys: i.ai_result ? Object.keys(i.ai_result) : null,
                    ai_result_total_score: i.ai_result?.total_score,
                    ai_result_overall_score: i.ai_result?.overall_score,
                  })), null, 2)}
                </pre>
              </details>
            </div>
          )}
        </div>
      </div>

      <div className="candidate-details-right-panel">
        <div className="status-card">
          <div className="status-header">
            <h3>Status</h3>
            <span className={`status-badge ${currentStatus.toLowerCase()}`}>
              {currentStatus.replace(/_/g, " ")}
            </span>
          </div>

          <div className="status-progress-bar">
            {(() => {
              // Always show both evaluation steps in sequence
              const statusStages = [
                "NEW",
                "INTERVIEW_SCHEDULED",
                "INTERVIEW_COMPLETED",
                "AI_EVALUATED",
                "MANUAL_EVALUATED",
                "HIRE",
              ];

              const statusLabels = [
                "New",
                "Schedule Interview",
                "Interview Completed",
                "AI Evaluated",
                "Manual Evaluated",
                "Hire",
              ];

              const currentIndex = statusStages.indexOf(currentStatus);
              const nextAction = getNextAction(currentStatus);

              return statusLabels.map((label, index) => {
                const stage = statusStages[index];
                
                // Status step logic
                let isCompleted = false;
                let isCurrent = false;
                let isNextAction = false;
                let isClickable = false;
                let isRecommended = false;
                let displayLabel = label;
                
                if (stage === "HIRE") {
                  // Special handling for the hire step
                  if (currentStatus === "HIRED" || currentStatus === "REJECTED") {
                    // If candidate is hired or rejected, show the final status
                    displayLabel = currentStatus === "HIRED" ? "Hired" : "Rejected";
                    isCompleted = true;
                    isCurrent = true;
                    isClickable = false;
                  } else {
                    // Show "Hire" as the next action
                    isNextAction = nextAction && nextAction.status === "HIRE";
                    isClickable = isNextAction;
                    isRecommended = isNextAction;
                  }
                } else {
                  // Regular status steps
                  isCompleted = index < currentIndex;
                  isCurrent = index === currentIndex;
                  isNextAction = nextAction && statusStages[index] === nextAction.status;
                  
                  // Special handling for AI_EVALUATED - make it non-clickable when completed
                  if (stage === "AI_EVALUATED") {
                    const hasAIEvaluation = interviews.some((i) => i.ai_result);
                    if (hasAIEvaluation) {
                      isCompleted = true;
                      isClickable = false; // AI evaluation is not clickable
                      isCurrent = false; // Never current, always completed
                    } else {
                      isClickable = false; // AI evaluation is never clickable
                      isCompleted = false; // Show as incomplete if no AI results
                    }
                  } else if (stage === "MANUAL_EVALUATED") {
                    // Manual evaluation is always clickable as next action, even if AI evaluation is not complete
                  isClickable = isNextAction || isCompleted;
                  } else {
                    isClickable = isNextAction || isCompleted;
                  }
                  
                  isRecommended = isNextAction;
                }

                // Determine additional CSS classes based on status
                let additionalClasses = "";
                if (stage === "HIRE") {
                  if (currentStatus === "HIRED") {
                    additionalClasses = "hired";
                  } else if (currentStatus === "REJECTED") {
                    additionalClasses = "rejected";
                  }
                }

                return (
                  <div
                    key={stage}
                    className={`status-step ${isCompleted ? "completed" : ""} ${
                      isCurrent ? "current" : ""
                    } ${isClickable ? "clickable" : ""} ${isRecommended ? "recommended" : ""} ${additionalClasses}`}
                    onClick={() => {
                      if (!isClickable || !shouldShowActions) return;

                      if (stage === "INTERVIEW_SCHEDULED") {
                        handleStatusUpdate("schedule_interview");
                      } else if (stage === "INTERVIEW_COMPLETED") {
                        handleStatusUpdate("complete_interview");
                      } else if (stage === "AI_EVALUATED") {
                        // AI evaluation is not clickable - handled automatically
                        return;
                      } else if (stage === "MANUAL_EVALUATED") {
                        handleStatusUpdate("manual_evaluate");
                      } else if (stage === "HIRE") {
                        handleStatusUpdate("hire_reject");
                      } else if (isCompleted) {
                        const next = getNextAction(stage);
                        if (next) {
                          handleStatusUpdate(next.id);
                        }
                      }
                    }}
                  >
                    <div className="status-circle">{index + 1}</div>
                    <div className="status-label">{displayLabel}</div>
                    {index < statusStages.length - 1 && (
                      <div className="status-connector"></div>
                    )}
                  </div>
                );
              });
            })()}
          </div>
        </div>

        <div className="interview-section card">
          {interviewsLoading ? (
            <BeatLoader color="var(--color-primary-dark)" size={8} />
          ) : interviews.length > 0 ? (
            interviews.map((interview, index) => (
              <div key={interview.id}>
                <div className="interview-header">
                  <h4>Interview Details - Round {interview.interview_round}</h4>
                  <span className={`interview-status ${interview.status.toLowerCase()}`}>
                    {interview.status}
                  </span>
                </div>
                
                <div className="interview-basic-info">
                  <p>
                    <strong>Date:</strong>{" "}
                    {interview.started_at
                      ? new Date(interview.started_at).toLocaleDateString('en-US', {
                          timeZone: 'Asia/Kolkata'  // Force IST timezone for date display
                        })
                      : "TBD"}
                  </p>
                  <p>
                    <strong>Slot:</strong>{" "}
                    {(() => {
                      console.log("=== CANDIDATE DETAILS DEBUG ===");
                      console.log("Candidate ID:", candidate.id);
                      console.log("Candidate Name:", candidate.full_name);
                      console.log("Interview ID:", interview.id);
                      console.log("Full interview object:", interview);
                      console.log("Interview slot_details:", interview.slot_details);
                      console.log("Interview schedule:", interview.schedule);
                      console.log("Interview started_at:", interview.started_at);
                      console.log("Interview ended_at:", interview.ended_at);
                      
                      // Try different possible field names
                      const slotData = interview.slot_details || interview.schedule || interview.slot;
                      console.log("Slot data found:", slotData);
                      
                      // Also check if we can get slot data from the candidate's interviews
                      console.log("All candidate interviews:", candidate.interviews);
                      console.log("Current interview index:", interviews.findIndex(i => i.id === interview.id));
                      
                      // Check if there's a schedule relationship
                      if (interview.schedule) {
                        console.log("Interview schedule details:", interview.schedule);
                        if (interview.schedule.slot) {
                          console.log("Schedule slot details:", interview.schedule.slot);
                        }
                      }
                      
                      // CRITICAL: ALWAYS use interview.started_at/ended_at for time display
                      // These are proper DateTime objects set from slot times in IST, converted to UTC, then displayed in IST
                      // DO NOT use slot_details.start_time/end_time as they are raw TimeField values without timezone info
                      
                      // Check if started_at/ended_at exist - these are the ONLY source of truth
                      if (interview.started_at && interview.ended_at) {
                        try {
                          // Parse the datetime strings - they come as ISO 8601 strings from API
                          const startDate = new Date(interview.started_at);
                          const endDate = new Date(interview.ended_at);
                          
                          // Validate dates are valid
                          if (isNaN(startDate.getTime()) || isNaN(endDate.getTime())) {
                            console.error("Invalid date values:", interview.started_at, interview.ended_at);
                            throw new Error("Invalid date");
                          }
                          
                          // Force display in IST (Asia/Kolkata) timezone - this is the ONLY source of truth
                          const startTimeIST = startDate.toLocaleTimeString('en-US', {
                            hour: 'numeric',
                            minute: '2-digit',
                            hour12: true,
                            timeZone: 'Asia/Kolkata'  // Force IST timezone display
                          });
                          
                          const endTimeIST = endDate.toLocaleTimeString('en-US', {
                            hour: 'numeric',
                            minute: '2-digit',
                            hour12: true,
                            timeZone: 'Asia/Kolkata'  // Force IST timezone display
                          });
                          
                          console.log("Displaying time from started_at/ended_at:", startTimeIST, "-", endTimeIST);
                          return `${startTimeIST} - ${endTimeIST}`;
                        } catch (error) {
                          console.error("Error formatting interview time from started_at:", error, {
                            started_at: interview.started_at,
                            ended_at: interview.ended_at
                          });
                          // Continue to fallback but log the error
                        }
                      } else {
                        console.warn("interview.started_at or ended_at is missing!", {
                          started_at: interview.started_at,
                          ended_at: interview.ended_at
                        });
                      }
                      
                      // Fallback ONLY if started_at/ended_at are not available (shouldn't happen for scheduled interviews)
                      if (slotData && slotData.start_time && slotData.end_time) {
                        console.warn("Using slot_details as fallback - interview.started_at/ended_at should be set!");
                        try {
                          // If we must use slot_details, format the time string directly
                          if (typeof slotData.start_time === 'string' && slotData.start_time.includes(':')) {
                            const formatTime = (timeStr) => {
                              return formatTimeTo12Hour(timeStr);
                            };
                            
                            const startTimeFormatted = formatTime(slotData.start_time);
                            const endTimeFormatted = formatTime(slotData.end_time);
                            
                            return `${startTimeFormatted} - ${endTimeFormatted}`;
                          }
                        } catch (error) {
                          console.error("Error formatting slot time:", error);
                          return "Invalid time format";
                        }
                      }
                      
                      return "N/A";
                    })()}
                  </p>
                </div>
                
                {/* Interview Action Buttons - Only show for scheduled interviews */}
                {interview.status?.toLowerCase() === 'scheduled' && (
                  <div className="interview-actions-container">
                    <div className="interview-actions">
                      <button 
                        className="edit-interview-btn" 
                        onClick={() => handleEditInterview(interview)}
                        title="Edit Interview"
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                          <path d="m18.5 2.5 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                        </svg>
                        Edit
                      </button>
                      <button 
                        className="delete-interview-btn" 
                        onClick={() => handleDeleteInterview(interview)}
                        title="Delete Interview"
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <polyline points="3,6 5,6 21,6"></polyline>
                          <path d="m19,6v14a2,2 0 0,1 -2,2H7a2,2 0 0,1 -2,-2V6m3,0V4a2,2 0 0,1 2,-2h4a2,2 0 0,1 2,2v2"></path>
                          <line x1="10" y1="11" x2="10" y2="17"></line>
                          <line x1="14" y1="11" x2="14" y2="17"></line>
                        </svg>
                        Delete
                      </button>
                    </div>
                  </div>
                )}
                
                {/* Video Recording Section */}
                {interview.ai_result?.recording_video && (
                  <div className="recording-section">
                    <h4>Interview Recording</h4>
                    <div className="video-player-container">
                      <video
                        controls
                        className="video-player"
                        preload="metadata"
                      >
                        <source src={`${baseURL}${interview.ai_result.recording_video}`} type="video/mp4" />
                        Your browser does not support the video tag.
                      </video>
                    </div>
                    {interview.ai_result.recording_created_at && (
                      <p className="recording-metadata">
                        <strong>Recorded:</strong>{" "}
                        {new Date(interview.ai_result.recording_created_at).toLocaleDateString() + ' ' + new Date(interview.ai_result.recording_created_at).toLocaleTimeString('en-US', {
                          hour: 'numeric',
                          minute: '2-digit',
                          hour12: true
                        })}
                      </p>
                    )}
                  </div>
                )}
                
                {/* Questions & Answers Section - Below Interview Details */}
                {(() => {
                  const qaData = interview.questions_and_answers || [];
                  if (qaData.length === 0) return null;
                  
                  // Group questions by type
                  const technicalQuestions = qaData.filter(qa => 
                    qa.question_type === 'TECHNICAL' || qa.question_type === 'BEHAVIORAL' || !qa.question_type
                  );
                  const codingQuestions = qaData.filter(qa => qa.question_type === 'CODING');
                  
                  return (
                    <div className="qa-section-below-interview">
                      <h4 className="qa-section-title">Questions & Answers - Round {interview.interview_round || 'AI Interview'}</h4>
                      <div className="qa-list-container">
                        {/* Technical Questions Section */}
                        {technicalQuestions.length > 0 && (
                          <>
                            <div className="qa-section-divider">
                              <h5 className="qa-section-label">Technical Questions</h5>
                            </div>
                            {technicalQuestions.map((qa, index) => (
                              <div key={qa.id || `tech-${index}`} className="qa-card-item">
                                <div className="qa-header-info">
                                  <span className="qa-number-circle">{qa.order || index + 1}</span>
                                  <span className="qa-type-badge">{qa.question_type === 'BEHAVIORAL' ? 'Behavioral' : 'Technical'}</span>
                                </div>
                                <div className="qa-content">
                                  <div className="qa-question-section">
                                    <strong>Q:</strong> {qa.question_text}
                                  </div>
                                  <div className="qa-answer-section">
                                    <strong>A:</strong> {qa.answer || 'No answer provided'}
                                  </div>
                                  {qa.response_time > 0 && (
                                    <div className="qa-timestamp">
                                      Response Time: {qa.response_time.toFixed(1)}s
                                    </div>
                                  )}
                                  {qa.answered_at && (
                                    <div className="qa-timestamp">
                                      Answered: {new Date(qa.answered_at).toLocaleDateString('en-GB') + ', ' + new Date(qa.answered_at).toLocaleTimeString('en-US', {
                                        hour: '2-digit',
                                        minute: '2-digit',
                                        hour12: false
                                      })}
                                    </div>
                                  )}
                                </div>
                              </div>
                            ))}
                          </>
                        )}
                        
                        {/* Coding Questions Section */}
                        {codingQuestions.length > 0 && (
                          <>
                            <div className="qa-section-divider">
                              <h5 className="qa-section-label">Coding Questions</h5>
                            </div>
                            {codingQuestions.map((qa, index) => (
                              <div key={qa.id || `coding-${index}`} className="qa-card-item">
                                <div className="qa-header-info">
                                  <span className="qa-number-circle">{qa.order || technicalQuestions.length + index + 1}</span>
                                  <span className="qa-type-badge">Coding</span>
                                </div>
                                <div className="qa-content">
                                  <div className="qa-question-section">
                                    <strong>Q:</strong> {qa.question_text}
                                  </div>
                                  <div className="qa-answer-section">
                                    <strong>A:</strong> {qa.answer || 'No answer provided'}
                                  </div>
                                  {qa.response_time > 0 && (
                                    <div className="qa-timestamp">
                                      Response Time: {qa.response_time.toFixed(1)}s
                                    </div>
                                  )}
                                  {qa.answered_at && (
                                    <div className="qa-timestamp">
                                      Answered: {new Date(qa.answered_at).toLocaleDateString('en-GB') + ', ' + new Date(qa.answered_at).toLocaleTimeString('en-US', {
                                        hour: '2-digit',
                                        minute: '2-digit',
                                        hour12: false
                                      })}
                                    </div>
                                  )}
                                </div>
                              </div>
                            ))}
                          </>
                        )}
                      </div>
                    </div>
                  );
                })()}
                
              </div>
            ))
          ) : (
            <p className="no-data">No interviews scheduled</p>
          )}
        </div>
      </div>
      </div>

      {/* Status Update Modal */}
      {showStatusModal && (
        <StatusUpdateModal
          isOpen={showStatusModal}
          onClose={handleModalClose}
          onUpdateStatus={() => {
            // Refresh candidate data when status is updated
            dispatch(fetchCandidates());
          }}
          action={selectedAction}
          candidate={candidate}
          interviews={interviews}
          onSubmitEvaluation={handleEvaluationSubmit}
          onInterviewScheduled={() => {
            // Refresh both interview data and candidate data when interview is scheduled
            fetchInterviews();
            dispatch(fetchCandidates());
          }}
          onEvaluationSubmitted={() => {
            // Refresh both interview data and candidate data when evaluation is submitted
            fetchInterviews();
            dispatch(fetchCandidates());
          }}
        />
      )}

      {/* Edit Interview Modal */}
      {showEditInterviewModal && editingInterview && (
        <StatusUpdateModal
          isOpen={showEditInterviewModal}
          onClose={() => {
            setShowEditInterviewModal(false);
            setEditingInterview(null);
            fetchInterviews();
            dispatch(fetchCandidates());
          }}
          action="schedule_interview"
          candidate={candidate}
          interviews={interviews}
          isEditMode={true}
          editingInterview={editingInterview}
        />
      )}

      {/* Edit Evaluation Modal */}
      {showEditEvaluationModal && editingEvaluation && (
        <StatusUpdateModal
          isOpen={showEditEvaluationModal}
          onClose={() => {
            setShowEditEvaluationModal(false);
            setEditingEvaluation(null);
            fetchInterviews();
            dispatch(fetchCandidates());
          }}
          action="evaluate"
          candidate={candidate}
          interviews={interviews}
          isEditMode={true}
          editingEvaluation={editingEvaluation}
        />
      )}

      {/* Delete Confirmation Modal - Matching DataTable Style */}
      {showDeleteModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3>{deleteType === 'interview' ? "Delete Interview" : "Delete Evaluation"}</h3>
            <p>
              {deleteType === 'interview' 
                ? "Are you sure you want to delete this interview? This will also release the slot and cannot be undone."
                : "Are you sure you want to delete this evaluation? This action cannot be undone."
              }
            </p>
            <div className="modal-actions">
              <button
                onClick={() => {
                  setShowDeleteModal(false);
                  setDeleteType(null);
                  setItemToDelete(null);
                }}
                className="btn btn-secondary"
              >
                Cancel
              </button>
              <button 
                onClick={deleteType === 'interview' ? confirmDeleteInterview : confirmDeleteEvaluation} 
                className="btn btn-danger"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default CandidateDetails;
