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

// Helper function to safely parse JSON fields or bullet-pointed text
const parseJsonField = (field) => {
  if (!field) return [];
  if (typeof field === 'string') {
    try {
      // First try to parse as JSON
      const parsed = JSON.parse(field);
      return Array.isArray(parsed) ? parsed : [];
    } catch (e) {
      // If not JSON, try to parse as bullet-pointed text
      const lines = field.split('\n').map(line => line.trim()).filter(line => line);
      if (lines.length > 0) {
        // Check if it's bullet-pointed (starts with -, •, *, etc.)
        const items = lines.map(line => {
          // Remove bullet markers
          return line.replace(/^[-•*]\s*/, '').trim();
        }).filter(item => item);
        return items.length > 0 ? items : [];
      }
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
          const resolveScore = (score10, score100) =>
            typeof score10 === "number"
              ? score10
              : (score100 || 0) / 10.0;
          // Transform ai_analysis to ai_result format
          aiResult = {
            overall_score: resolveScore(aiAnalysis.overall_score_10, aiAnalysis.overall_score),
            total_score: resolveScore(aiAnalysis.overall_score_10, aiAnalysis.overall_score),
            technical_score: resolveScore(aiAnalysis.technical_score_10, aiAnalysis.technical_score),
            behavioral_score: resolveScore(aiAnalysis.behavioral_score_10, aiAnalysis.behavioral_score),
            coding_score: resolveScore(aiAnalysis.coding_score_10, aiAnalysis.coding_score),
            communication_score: resolveScore(aiAnalysis.communication_score_10, aiAnalysis.communication_score),
            strengths: aiAnalysis.strengths || '',
            weaknesses: aiAnalysis.weaknesses || '',
            technical_analysis: aiAnalysis.technical_analysis || '',
            behavioral_analysis: aiAnalysis.behavioral_analysis || '',
            coding_analysis: aiAnalysis.coding_analysis || '',
            detailed_feedback: aiAnalysis.detailed_feedback || '',
            hiring_recommendation: aiAnalysis.hiring_recommendation || '',
            recommendation: aiAnalysis.recommendation || 'MAYBE',
            hire_recommendation: ['STRONG_HIRE', 'HIRE'].includes(aiAnalysis.recommendation),
            confidence_level: resolveScore(aiAnalysis.confidence_level_10, aiAnalysis.confidence_level),
            problem_solving_score: resolveScore(aiAnalysis.problem_solving_score_10, aiAnalysis.problem_solving_score),
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
            {interviews.some((i) => i.ai_result) && (() => {
              const aiResult = interviews.find(i => i.ai_result)?.ai_result;
              // Get recommendation from LLM evaluation (STRONG_HIRE, HIRE, MAYBE, NO_HIRE)
              const llmRecommendation = aiResult?.recommendation || aiResult?.hiring_recommendation || 'MAYBE';
              
              // Determine status class based on LLM recommendation
              const getStatusClass = (rec) => {
                const recUpper = (rec || '').toUpperCase();
                if (recUpper === 'STRONG_HIRE') return 'strong-recommended';
                if (recUpper === 'HIRE') return 'recommended';
                if (recUpper === 'MAYBE') return 'maybe';
                if (recUpper === 'NO_HIRE' || recUpper === 'REJECT') return 'not-recommended';
                return 'maybe';
              };
              
              // Format recommendation for display
              const formatRecommendation = (rec) => {
                const recUpper = (rec || '').toUpperCase();
                if (recUpper === 'STRONG_HIRE') return 'STRONG HIRE';
                if (recUpper === 'HIRE') return 'HIRE';
                if (recUpper === 'MAYBE') return 'MAYBE';
                if (recUpper === 'NO_HIRE') return 'NO HIRE';
                if (recUpper === 'REJECT') return 'REJECT';
                return recUpper || 'MAYBE';
              };
              
              return (
              <div className="hire-recommendation-section">
                <div className="hire-recommendation-card">
                  <div className="hire-status-row">
                    <span className="label">Hire Status:</span>
                      <span className={`value recommendation ${getStatusClass(llmRecommendation)}`}>
                        {formatRecommendation(llmRecommendation)}
                    </span>
                  </div>
                    {aiResult?.total_score !== undefined && (
                    <div className="score-row">
                      <span className="label">Score:</span>
                        <span className={`value score-value ${aiResult.total_score >= 8 ? "high-score" : aiResult.total_score >= 6 ? "medium-score" : "low-score"}`}>
                          {aiResult.total_score?.toFixed(1) || "N/A"}/10
                      </span>
                    </div>
                  )}
                </div>
              </div>
              );
            })()}
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
                    // IMPORTANT: Sort by order field to maintain correct sequence
                    // Use case-insensitive matching for question types
                    const technicalQuestions = qaData
                      .filter(qa => {
                        const qType = (qa.question_type || '').toUpperCase();
                        return qType === 'TECHNICAL' || 
                               qType === 'BEHAVIORAL' || 
                        qa.question_level === 'CANDIDATE_QUESTION' ||
                               !qa.question_type ||
                               (qType !== 'CODING' && qType !== 'CODING CHALLENGE');
                      })
                      .sort((a, b) => {
                        // Sort by order field (if available), then by index
                        const orderA = a.order !== undefined && a.order !== null ? a.order : 9999;
                        const orderB = b.order !== undefined && b.order !== null ? b.order : 9999;
                        return orderA - orderB;
                      });
                    const codingQuestions = qaData
                      .filter(qa => {
                        const qType = (qa.question_type || '').toUpperCase();
                        const isCoding = qType === 'CODING' || qType === 'CODING CHALLENGE';
                        return isCoding;
                      })
                      .sort((a, b) => {
                        // Sort by order field (if available), then by index
                        const orderA = a.order !== undefined && a.order !== null ? a.order : 9999;
                        const orderB = b.order !== undefined && b.order !== null ? b.order : 9999;
                        return orderA - orderB;
                      });
                    
                    // Debug: Log coding questions found with full details
                    console.log(`🔍 Coding Questions Debug (AI Evaluation Section):`);
                    console.log(`   Total qaData items: ${qaData.length}`);
                    console.log(`   Found ${codingQuestions.length} coding questions`);
                    console.log(`   Found ${technicalQuestions.length} technical/behavioral questions`);
                    if (qaData.length > 0) {
                      console.log(`   All question types in qaData:`, qaData.map(q => ({
                        id: q.id,
                        order: q.order,
                        question_type: q.question_type,
                        question_type_upper: (q.question_type || '').toUpperCase(),
                        has_question: !!q.question_text,
                        has_answer: !!q.answer
                      })));
                    }
                    if (codingQuestions.length > 0) {
                      console.log('   Coding questions details:', codingQuestions.map(q => ({
                        id: q.id,
                        order: q.order,
                        question_type: q.question_type,
                        question_type_upper: (q.question_type || '').toUpperCase(),
                        has_answer: !!q.answer,
                        answer_preview: q.answer ? q.answer.substring(0, 50) : 'No answer',
                        code_submission: q.code_submission ? 'exists' : 'none'
                      })));
                    } else {
                      console.log('   ⚠️ No coding questions found in qaData!');
                      // Check if there are any questions with CODING in the type
                      const potentialCoding = qaData.filter(q => {
                        const qType = (q.question_type || '').toUpperCase();
                        return qType.includes('CODING');
                      });
                      if (potentialCoding.length > 0) {
                        console.log(`   Found ${potentialCoding.length} questions with 'CODING' in type:`, potentialCoding.map(q => ({
                          id: q.id,
                          question_type: q.question_type,
                          question_type_upper: (q.question_type || '').toUpperCase()
                        })));
                      }
                    }
                    
                    // Calculate TECHNICAL metrics - use AI evaluation data (based on actual answer correctness analysis)
                    const technicalTotalQuestions = technicalQuestions.length || 0;
                    
                    // Use AI-provided correct/incorrect counts from AI analysis (not just answer presence)
                    let technicalCorrectAnswers = 0;
                    let technicalIncorrectAnswers = 0;
                    let technicalAccuracy = 0;
                    
                    if (aiResult.questions_correct !== undefined && aiResult.questions_attempted !== undefined) {
                      // Use AI evaluation data - these are based on actual answer correctness analysis
                      // AI analyzes each answer and determines if it's correct or incorrect
                      technicalCorrectAnswers = Math.round(aiResult.questions_correct || 0);
                      const technicalAttempted = Math.round(aiResult.questions_attempted || technicalTotalQuestions);
                      technicalIncorrectAnswers = Math.max(0, technicalAttempted - technicalCorrectAnswers);
                      technicalAccuracy = technicalAttempted > 0 
                        ? (technicalCorrectAnswers / technicalAttempted * 100) 
                        : 0;
                    } else if (aiResult.accuracy_percentage !== undefined && aiResult.questions_attempted !== undefined) {
                      // Calculate from accuracy percentage if available
                      const technicalAttempted = Math.round(aiResult.questions_attempted || technicalTotalQuestions);
                      technicalAccuracy = aiResult.accuracy_percentage || 0;
                      technicalCorrectAnswers = Math.round((technicalAccuracy / 100) * technicalAttempted);
                      technicalIncorrectAnswers = Math.max(0, technicalAttempted - technicalCorrectAnswers);
                    } else {
                      // Fallback: count from technical_questions if they have is_correct flag from AI analysis
                      const technicalWithCorrectness = technicalQuestions.filter(qa => qa.is_correct === true);
                      technicalCorrectAnswers = technicalWithCorrectness.length;
                      technicalIncorrectAnswers = technicalTotalQuestions - technicalCorrectAnswers;
                      technicalAccuracy = technicalTotalQuestions > 0 
                        ? (technicalCorrectAnswers / technicalTotalQuestions * 100) 
                        : 0;
                    }
                    
                    // Calculate CODING metrics - use test results if available
                    let codingTotalQuestions = codingQuestions.length || 0;
                    let codingCorrectAnswers = 0;
                    let codingIncorrectAnswers = 0;
                    let codingAccuracy = 0;
                    
                    // Calculate test cases passed/failed from coding questions
                    let totalTestCases = 0;
                    let testCasesPassed = 0;
                    let testCasesFailed = 0;
                    
                    // For coding questions, check if they passed tests (from is_correct flag or test results)
                    codingQuestions.forEach(qa => {
                      // Check if there's a code submission that passed tests
                      // Priority: 1) is_correct flag, 2) code_submission.passed_all_tests, 3) answer presence
                      let isCorrect = false;
                      if (qa.is_correct === true) {
                        isCorrect = true;
                      } else if (qa.code_submission && qa.code_submission.passed_all_tests === true) {
                        isCorrect = true;
                      } else if (qa.answer && qa.answer !== 'No code submitted' && qa.answer !== 'no answer provided' && qa.answer !== 'None') {
                        // If answer exists and is not empty, consider it attempted (but not necessarily correct)
                        isCorrect = false; // Default to false unless explicitly marked as correct
                      }
                      
                      if (isCorrect) {
                        codingCorrectAnswers++;
                      } else if (qa.answer && qa.answer !== 'No code submitted' && qa.answer !== 'no answer provided' && qa.answer !== 'None') {
                        // If there's an answer but it's not marked as correct, count as incorrect
                        codingIncorrectAnswers++;
                      }
                      
                      // Extract test case information from code_submission output_log or answer
                      if (qa.code_submission && qa.code_submission.output_log) {
                        // Parse test case results from output_log
                        const outputLog = qa.code_submission.output_log;
                        const testCaseMatches = outputLog.match(/(\d+)\/(\d+)\s+test.*passed|passed.*(\d+).*(\d+)|test.*case.*(\d+).*(\d+)/i);
                        if (testCaseMatches) {
                          const passed = parseInt(testCaseMatches[1] || testCaseMatches[3] || testCaseMatches[5] || 0);
                          const total = parseInt(testCaseMatches[2] || testCaseMatches[4] || testCaseMatches[6] || 0);
                          if (total > 0) {
                            testCasesPassed += passed;
                            testCasesFailed += (total - passed);
                            totalTestCases += total;
                          }
                        }
                      } else if (qa.answer && typeof qa.answer === 'string') {
                        // Try to parse test case results from answer text
                        const testCaseMatches = qa.answer.match(/(\d+)\/(\d+)\s+test.*passed|passed.*(\d+).*(\d+)|test.*case.*(\d+).*(\d+)/i);
                        if (testCaseMatches) {
                          const passed = parseInt(testCaseMatches[1] || testCaseMatches[3] || testCaseMatches[5] || 0);
                          const total = parseInt(testCaseMatches[2] || testCaseMatches[4] || testCaseMatches[6] || 0);
                          if (total > 0) {
                            testCasesPassed += passed;
                            testCasesFailed += (total - passed);
                            totalTestCases += total;
                          }
                        }
                      }
                    });
                    
                    // Fallback: If no test case data found, estimate from coding questions
                    if (totalTestCases === 0 && codingTotalQuestions > 0) {
                      // Assume 3 test cases per question on average
                      totalTestCases = codingTotalQuestions * 3;
                      testCasesPassed = codingCorrectAnswers * 3;
                      testCasesFailed = totalTestCases - testCasesPassed;
                    }
                    
                    codingAccuracy = codingTotalQuestions > 0 
                      ? (codingCorrectAnswers / codingTotalQuestions * 100) 
                      : 0;
                    
                    // Overall metrics (for display purposes, but we'll show separate sections)
                    const totalQuestions = technicalTotalQuestions + codingTotalQuestions;
                    const correctAnswers = technicalCorrectAnswers + codingCorrectAnswers;
                    const incorrectAnswers = totalQuestions - correctAnswers;
                    const accuracy = totalQuestions > 0 ? (correctAnswers / totalQuestions * 100) : 0;
                    const totalCompletionTime = aiResult.total_completion_time || 54.6;
                    
                    // Section scores (AI returns 0-100 scale, use directly as percentage)
                    // Note: AI scores are already in 0-100 scale, so use them directly
                    const technicalScore = aiResult.technical_score || 0;
                    const behavioralScore = aiResult.behavioral_score || 0;
                    const codingScore = aiResult.coding_score || 0;
                    const communicationScore = aiResult.communication_score || 0;
                    const problemSolvingScore = aiResult.problem_solving_score || 0;
                    
                    // IMPORTANT: If we have a coding score but no questions in Q&A data, use the score to estimate metrics
                    // This ensures the Coding Performance Metrics card shows even if questions aren't in Q&A data
                    if (codingTotalQuestions === 0 && codingScore > 0) {
                      // Estimate questions attempted based on coding score (assume at least 1 question)
                      const estimatedQuestions = Math.max(1, Math.round(codingScore / 20)); // Rough estimate
                      codingTotalQuestions = estimatedQuestions; // Update total questions
                      codingCorrectAnswers = Math.round((codingScore / 100) * estimatedQuestions);
                      codingIncorrectAnswers = estimatedQuestions - codingCorrectAnswers;
                      codingAccuracy = codingScore; // Use coding score as accuracy
                      console.log(`⚠️ No coding questions in Q&A data, but coding score exists (${codingScore}). Using estimated metrics.`);
                    }
                    
                    // Debug: Log final coding metrics
                    console.log(`📊 Coding Metrics: Total=${codingTotalQuestions}, Correct=${codingCorrectAnswers}, Accuracy=${codingAccuracy.toFixed(0)}%, Score=${codingScore}`);
                    console.log(`   Coding Questions Array Length: ${codingQuestions.length}`);
                    console.log(`   Will show Coding Performance Metrics: ${(codingTotalQuestions > 0 || codingScore > 0 || codingQuestions.length > 0)}`);
                    
                    // Overall rating
                    const overallRating = aiResult.overall_rating || 'FAIR';
                    
                    // Strengths and weaknesses - try array fields first, then parse from string
                    const strengths = aiResult.strengths_array || parseJsonField(aiResult.strengths || '');
                    const weaknesses = aiResult.weaknesses_array || parseJsonField(aiResult.weaknesses || '');
                    
                    // Question accuracy chart data - TECHNICAL ONLY
                    const technicalAccuracyChartData = [
                      { name: 'Correct', value: technicalCorrectAnswers, color: '#4CAF50' },
                      { name: 'Incorrect', value: technicalIncorrectAnswers, color: '#F44336' }
                    ];
                    
                    // Coding accuracy chart data - Questions Correct/Incorrect
                    // Ensure we have at least some data for the chart (even if all zeros)
                    const codingQuestionsChartData = [
                      { name: 'Correct', value: Math.max(0, codingCorrectAnswers), color: '#4CAF50' },
                      { name: 'Incorrect', value: Math.max(0, codingIncorrectAnswers), color: '#F44336' }
                    ];
                    
                    // Test cases passed/failed chart data
                    const testCasesChartData = [
                      { name: 'Passed', value: testCasesPassed, color: '#4CAF50' },
                      { name: 'Failed', value: testCasesFailed, color: '#F44336' }
                    ];
                    
                    // Extract AI evaluation summary points
                    const technicalAnalysis = aiResult.technical_analysis || '';
                    const codingAnalysis = aiResult.coding_analysis || '';
                    const behavioralAnalysis = aiResult.behavioral_analysis || '';
                    const detailedFeedback = aiResult.detailed_feedback || aiResult.ai_summary || '';
                    
                    // Parse summary points from detailed feedback
                    const parseSummaryPoints = (text) => {
                      if (!text) return [];
                      const lines = text.split('\n').map(line => line.trim()).filter(line => line);
                      const points = [];
                      lines.forEach(line => {
                        // Check for bullet points or numbered lists
                        const cleaned = line.replace(/^[-•*]\s*/, '').replace(/^\d+[.)]\s*/, '').trim();
                        if (cleaned.length > 10) { // Only include substantial points
                          points.push(cleaned);
                        }
                      });
                      return points.length > 0 ? points : [text]; // Fallback to full text if no points found
                    };
                    
                    // Get JD keywords/skills from interview job
                    const jobDescription = interview.job?.job_description || interview.job?.job_title || '';
                    const extractJDKeywords = (jd) => {
                      if (!jd) return [];
                      const commonSkills = ['python', 'javascript', 'java', 'react', 'node', 'sql', 'database', 'api', 'rest', 'aws', 'docker', 'kubernetes', 'machine learning', 'ai', 'data science', 'algorithm', 'data structure', 'frontend', 'backend', 'full stack'];
                      const jdLower = jd.toLowerCase();
                      return commonSkills.filter(skill => jdLower.includes(skill));
                    };
                    
                    const jdKeywords = extractJDKeywords(jobDescription);
                    
                    // Build AI evaluation summary points organized by category
                    const technicalPoints = [];
                    const codingPoints = [];
                    const grammarPoints = [];
                    
                    // TECHNICAL ASPECTS
                    // Add technical skills assessment based on JD keywords
                    if (jdKeywords.length > 0 && technicalAnalysis) {
                      const matchedSkills = jdKeywords.filter(keyword => 
                        technicalAnalysis.toLowerCase().includes(keyword.toLowerCase())
                      );
                      if (matchedSkills.length > 0) {
                        technicalPoints.push(`Strong technical skills demonstrated in: ${matchedSkills.join(', ').toUpperCase()}`);
                      }
                    }
                    
                    // Add points from technical analysis
                    if (technicalAnalysis) {
                      const techPointsParsed = parseSummaryPoints(technicalAnalysis);
                      techPointsParsed.forEach(point => {
                        if (point.length > 20 && !technicalPoints.includes(point)) {
                          technicalPoints.push(point);
                        }
                      });
                    }
                    
                    // Add technical score summary
                    if (technicalScore > 0) {
                      const techRating = technicalScore >= 80 ? 'Excellent' : technicalScore >= 60 ? 'Good' : technicalScore >= 40 ? 'Fair' : 'Needs Improvement';
                      technicalPoints.push(`Technical Score: ${techRating} (${technicalScore.toFixed(0)}/100)`);
                    }
                    
                    // Fallback for technical if empty
                    if (technicalPoints.length === 0) {
                      technicalPoints.push('Technical knowledge demonstrated through interview responses.');
                    }
                    
                    // CODING ASPECTS
                    // Add points from coding analysis
                    if (codingAnalysis) {
                      const codingPointsParsed = parseSummaryPoints(codingAnalysis);
                      codingPointsParsed.forEach(point => {
                        if (point.length > 20 && !codingPoints.includes(point)) {
                          codingPoints.push(point);
                        }
                      });
                    }
                    
                    // Add coding score and test case summary
                    if (codingScore > 0) {
                      const codingRating = codingScore >= 80 ? 'Excellent' : codingScore >= 60 ? 'Good' : codingScore >= 40 ? 'Fair' : 'Needs Improvement';
                      codingPoints.push(`Coding Score: ${codingRating} (${codingScore.toFixed(0)}/100)`);
                    }
                    
                    if (totalTestCases > 0) {
                      const testCaseAccuracy = (testCasesPassed / totalTestCases) * 100;
                      codingPoints.push(`Test Cases: ${testCasesPassed}/${totalTestCases} passed (${testCaseAccuracy.toFixed(0)}% accuracy)`);
                    }
                    
                    if (codingTotalQuestions > 0) {
                      codingPoints.push(`Coding Questions: ${codingCorrectAnswers}/${codingTotalQuestions} correct (${codingAccuracy.toFixed(0)}% accuracy)`);
                    }
                    
                    // Fallback for coding if empty
                    if (codingPoints.length === 0 && codingTotalQuestions > 0) {
                      codingPoints.push('Coding ability assessed through programming challenges.');
                    } else if (codingPoints.length === 0) {
                      codingPoints.push('No coding questions were part of this interview.');
                    }
                    
                    // GRAMMAR AND COMMUNICATION
                    // Add grammar assessment (extract from communication score or analysis)
                    const grammarRating = communicationScore >= 80 ? 'Excellent' : communicationScore >= 60 ? 'Good' : communicationScore >= 40 ? 'Fair' : 'Needs Improvement';
                    if (communicationScore > 0) {
                      grammarPoints.push(`Grammar and Communication: ${grammarRating} (${communicationScore.toFixed(0)}/100)`);
                    }
                    
                    // Add points from behavioral/communication analysis
                    if (behavioralAnalysis) {
                      const behavioralPointsParsed = parseSummaryPoints(behavioralAnalysis);
                      behavioralPointsParsed.forEach(point => {
                        const pointLower = point.toLowerCase();
                        if (point.length > 20 && (pointLower.includes('grammar') || pointLower.includes('communication') || pointLower.includes('language') || pointLower.includes('speaking'))) {
                          grammarPoints.push(point);
                        }
                      });
                    }
                    
                    // Fallback for grammar if empty
                    if (grammarPoints.length === 0) {
                      grammarPoints.push(`Communication skills: ${grammarRating} based on interview responses.`);
                    }
                    
                    // Combine all points for backward compatibility
                    const aiEvaluationSummary = [
                      ...technicalPoints,
                      ...codingPoints,
                      ...grammarPoints
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
                                      <span className="circle-value">{aiResult.questions_attempted !== undefined ? Math.round(aiResult.questions_attempted) : technicalTotalQuestions}</span>
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
                              
                              {/* Coding Performance Metrics Card - Always show if any coding data exists */}
                              {(() => {
                                // Check multiple conditions to ensure we show the card when coding data exists
                                const hasCodingQuestions = codingQuestions.length > 0;
                                const hasCodingTotal = codingTotalQuestions > 0;
                                const hasCodingScore = codingScore > 0;
                                const shouldShow = hasCodingQuestions || hasCodingTotal || hasCodingScore;
                                
                                console.log(`🎯 Coding Performance Metrics Display Check:`, {
                                  hasCodingQuestions,
                                  hasCodingTotal,
                                  hasCodingScore,
                                  codingQuestionsLength: codingQuestions.length,
                                  codingTotalQuestions,
                                  codingScore,
                                  shouldShow
                                });
                                
                                if (!shouldShow) return null;
                                
                                return (
                                <div className="evaluation-card performance-metrics-card">
                                  <h4 className="card-title">Coding Performance Metrics</h4>
                                  <div className="metrics-grid">
                                    <div className="metric-circle">
                                      <div className="circle-chart" style={{ 
                                          background: `conic-gradient(#2196F3 0% ${codingTotalQuestions > 0 ? Math.min((codingTotalQuestions/12)*100, 100) : 0}%, #e0e0e0 ${codingTotalQuestions > 0 ? Math.min((codingTotalQuestions/12)*100, 100) : 0}% 100%)`
                                      }}>
                                          <span className="circle-value">{codingTotalQuestions || codingQuestions.length || 0}</span>
                                      </div>
                                      <div className="circle-label">Questions Attempted</div>
                                    </div>
                                    <div className="metric-circle">
                                      <div className="circle-chart" style={{ 
                                          background: `conic-gradient(#4CAF50 0% ${codingTotalQuestions > 0 ? Math.min((codingCorrectAnswers/codingTotalQuestions)*100, 100) : 0}%, #e0e0e0 ${codingTotalQuestions > 0 ? Math.min((codingCorrectAnswers/codingTotalQuestions)*100, 100) : 0}% 100%)`
                                      }}>
                                        <span className="circle-value">{codingCorrectAnswers}</span>
                                      </div>
                                      <div className="circle-label">Questions Correct</div>
                                    </div>
                                    <div className="metric-circle">
                                      <div className="circle-chart" style={{ 
                                          background: `conic-gradient(#7B2CBF 0% ${Math.min(codingAccuracy, 100)}%, #e0e0e0 ${Math.min(codingAccuracy, 100)}% 100%)`
                                      }}>
                                        <span className="circle-value">{codingAccuracy.toFixed(0)}%</span>
                                      </div>
                                      <div className="circle-label">Accuracy (%)</div>
                                    </div>
                                      {totalTestCases > 0 && (
                                        <div className="metric-circle">
                                          <div className="circle-chart" style={{ 
                                            background: `conic-gradient(#FF9800 0% ${Math.min((testCasesPassed/totalTestCases)*100, 100)}%, #e0e0e0 ${Math.min((testCasesPassed/totalTestCases)*100, 100)}% 100%)`
                                          }}>
                                            <span className="circle-value">{testCasesPassed}/{totalTestCases}</span>
                                  </div>
                                          <div className="circle-label">Test Cases Passed</div>
                                </div>
                              )}
                                    </div>
                                  </div>
                                );
                              })()}
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
                                <h4 className="card-title">AI Evaluation Summary</h4>
                                <div className="summary-content">
                                  {/* Technical Aspects */}
                                  {technicalPoints.length > 0 && (
                                    <div className="summary-section">
                                      <h5 className="summary-section-title">📊 Technical Aspects</h5>
                                      <ul className="summary-points-list">
                                        {technicalPoints.map((point, idx) => (
                                          <li key={`tech-${idx}`} className="summary-point">{point}</li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}
                                  
                                  {/* Coding Aspects */}
                                  {codingPoints.length > 0 && (
                                    <div className="summary-section">
                                      <h5 className="summary-section-title">💻 Coding Aspects</h5>
                                      <ul className="summary-points-list">
                                        {codingPoints.map((point, idx) => (
                                          <li key={`coding-${idx}`} className="summary-point">{point}</li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}
                                  
                                  {/* Grammar and Communication */}
                                  {grammarPoints.length > 0 && (
                                    <div className="summary-section">
                                      <h5 className="summary-section-title">📝 Grammar and Communication</h5>
                                      <ul className="summary-points-list">
                                        {grammarPoints.map((point, idx) => (
                                          <li key={`grammar-${idx}`} className="summary-point">{point}</li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}
                                  
                                  {/* Fallback if no points available */}
                                  {technicalPoints.length === 0 && codingPoints.length === 0 && grammarPoints.length === 0 && (
                                <p className="summary-text">
                                  {aiResult.detailed_feedback || aiResult.ai_summary || 'The candidate demonstrated solid technical knowledge and good problem-solving abilities.'}
                                </p>
                                  )}
                                </div>
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
                  
                  // Always use old Q&A format (question_text and answer together)
                  // Group questions by type (case-insensitive)
                  const codingQuestions = qaData
                    .filter(qa => {
                      const qType = (qa.question_type || '').toUpperCase();
                      return qType === 'CODING' || qType === 'CODING CHALLENGE';
                    })
                    .sort((a, b) => {
                      // Sort by conversation_sequence first (if available), then by order, then by id
                      const seqA = a.conversation_sequence !== undefined && a.conversation_sequence !== null ? a.conversation_sequence : 999999;
                      const seqB = b.conversation_sequence !== undefined && b.conversation_sequence !== null ? b.conversation_sequence : 999999;
                      if (seqA !== seqB) {
                        return seqA - seqB;
                      }
                      // Fallback to order
                      const orderA = a.order !== undefined && a.order !== null ? a.order : 9999;
                      const orderB = b.order !== undefined && b.order !== null ? b.order : 9999;
                      if (orderA !== orderB) {
                        return orderA - orderB;
                      }
                      // Final fallback to id
                      return (a.id || '').localeCompare(b.id || '');
                    });
                  const technicalQuestions = qaData
                    .filter(qa => {
                      const qType = (qa.question_type || '').toUpperCase();
                      return qType !== 'CODING' && qType !== 'CODING CHALLENGE';
                    })
                    .sort((a, b) => {
                      // Sort by conversation_sequence first (if available), then by order, then by id
                      const seqA = a.conversation_sequence !== undefined && a.conversation_sequence !== null ? a.conversation_sequence : 999999;
                      const seqB = b.conversation_sequence !== undefined && b.conversation_sequence !== null ? b.conversation_sequence : 999999;
                      if (seqA !== seqB) {
                        return seqA - seqB;
                      }
                      // Fallback to order
                      const orderA = a.order !== undefined && a.order !== null ? a.order : 9999;
                      const orderB = b.order !== undefined && b.order !== null ? b.order : 9999;
                      if (orderA !== orderB) {
                        return orderA - orderB;
                      }
                      // Final fallback to id
                      return (a.id || '').localeCompare(b.id || '');
                    });
                  
                  // Debug: Log Q&A section coding questions
                  console.log(`🔍 Q&A Section Debug: Found ${codingQuestions.length} coding questions, ${technicalQuestions.length} technical questions`);
                  if (codingQuestions.length > 0) {
                    console.log('   Q&A Coding questions:', codingQuestions.map(q => ({
                      id: q.id,
                      order: q.order,
                      question_type: q.question_type,
                      has_question_text: !!q.question_text,
                      has_answer: !!q.answer,
                      question_preview: q.question_text ? q.question_text.substring(0, 50) : 'No question',
                      answer_preview: q.answer ? q.answer.substring(0, 50) : 'No answer'
                    })));
                  }
                  
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
                            {technicalQuestions.map((qa, index) => {
                              // Convert 0-indexed order to 1-indexed display number
                              const displayNumber = (qa.order !== undefined && qa.order !== null) ? qa.order + 1 : index + 1;
                              return (
                              <div key={qa.id || `tech-${index}`} className="qa-card-item">
                                <div className="qa-header-info">
                                  <span className="qa-number-circle">{displayNumber}</span>
                                  <span className="qa-type-badge">{qa.question_type === 'BEHAVIORAL' ? 'Behavioral' : 'Technical'}</span>
                                </div>
                                <div className="qa-content">
                                  <div className="qa-question-section">
                                    {qa.question_text && qa.question_text.trim().startsWith('Q:') ? (
                                      qa.question_text
                                    ) : (
                                      <><strong>Q:</strong> {qa.question_text}</>
                                    )}
                                  </div>
                                  <div className="qa-answer-section">
                                    {qa.answer && qa.answer.trim().startsWith('A:') ? (
                                      <div className="qa-answer-text">{qa.answer}</div>
                                    ) : (
                                      <>
                                        <strong>A:</strong>
                                        <div className="qa-answer-text">
                                          {qa.answer || 'No answer provided'}
                                        </div>
                                      </>
                                    )}
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
                            );
                          })}
                        </>
                      )}
                      
                      {/* Coding Questions Section */}
                      {(() => {
                        console.log(`📝 Q&A Section - Coding Questions Check:`, {
                          codingQuestionsLength: codingQuestions.length,
                          codingQuestions: codingQuestions.map(q => ({
                            id: q.id,
                            order: q.order,
                            question_type: q.question_type,
                            has_question: !!q.question_text,
                            has_answer: !!q.answer,
                            answer_length: q.answer ? q.answer.length : 0,
                            answer_preview: q.answer ? q.answer.substring(0, 100) : 'No answer'
                          }))
                        });
                        
                        if (codingQuestions.length > 0) {
                          return (
                            <>
                              <div className="qa-section-divider">
                                <h5 className="qa-section-label">Coding Questions</h5>
                              </div>
                              {codingQuestions.map((qa, index) => {
                                // Convert 0-indexed order to 1-indexed display number
                                // For coding questions, continue numbering after technical questions
                                const displayNumber = (qa.order !== undefined && qa.order !== null) ? qa.order + 1 : technicalQuestions.length + index + 1;
                                
                                // Extract actual code from answer if it contains "Submitted Code:"
                                let codeToDisplay = qa.answer || 'No code submitted';
                                if (codeToDisplay.includes('Submitted Code:')) {
                                  const codeStart = codeToDisplay.indexOf('Submitted Code:') + 'Submitted Code:'.length;
                                  codeToDisplay = codeToDisplay.substring(codeStart).trim();
                                }
                                
                                console.log(`   Rendering coding question ${index + 1}: ID=${qa.id}, has_answer=${!!qa.answer}, code_length=${codeToDisplay.length}`);
                                
                                return (
                                  <div key={qa.id || `coding-${index}`} className="qa-card-item">
                                    <div className="qa-header-info">
                                      <span className="qa-number-circle">{displayNumber}</span>
                                      <span className="qa-type-badge">Coding</span>
                                    </div>
                                    <div className="qa-content">
                                      <div className="qa-question-section">
                                        {qa.question_text && qa.question_text.trim().startsWith('Q:') ? (
                                          qa.question_text
                                        ) : (
                                          <><strong>Q:</strong> {qa.question_text || 'No question text'}</>
                                        )}
                                      </div>
                                      <div className="qa-answer-section">
                                        {codeToDisplay && codeToDisplay !== 'No code submitted' && codeToDisplay !== 'A: No code submitted' ? (
                                          <pre className="qa-code-block">
                                            {codeToDisplay}
                                          </pre>
                                        ) : (
                                          <span>{codeToDisplay || 'No code submitted'}</span>
                                        )}
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
                                );
                              })}
                            </>
                          );
                        } else {
                          console.log('   ⚠️ No coding questions to display in Q&A section');
                          return null;
                        }
                      })()}
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
    </div>
  );
};

export default CandidateDetails;
                        const seqA = a.sequence !== undefined ? a.sequence : (a.order || 0) * 100;
                        const seqB = b.sequence !== undefined ? b.sequence : (b.order || 0) * 100;
                        return seqA - seqB;
                      });
                    
                    const codingConversation = qaData
                      .filter(item => {
                        const qType = (item.question_type || '').toUpperCase();
                        return qType === 'CODING' || qType === 'CODING CHALLENGE';
                      })
                      .sort((a, b) => {
                        const seqA = a.sequence !== undefined ? a.sequence : (a.order || 0) * 100;
                        const seqB = b.sequence !== undefined ? b.sequence : (b.order || 0) * 100;
                        return seqA - seqB;
                      });
                    
                    return (
                      <div className="qa-section-below-interview">
                        <h4 className="qa-section-title">Questions & Answers - Round {interview.interview_round || 'AI Interview'}</h4>
                        <div className="qa-list-container">
                          {/* Technical Questions Section - Conversation Format */}
                          {technicalConversation.length > 0 && (
                            <>
                              <div className="qa-section-divider">
                                <h5 className="qa-section-label">Technical Questions</h5>
                              </div>
                              {technicalConversation.map((item, index) => {
                                const isAI = item.role === 'AI';
                                const isInterviewee = item.role === 'Interviewee';
                                return (
                                  <div key={item.id || `conv-${index}`} className={`qa-card-item conversation-item ${isAI ? 'ai-message' : 'interviewee-message'}`}>
                                    <div className="qa-header-info">
                                      <span className={`qa-role-badge ${isAI ? 'ai-badge' : 'interviewee-badge'}`}>
                                        {isAI ? '🤖 AI' : '👤 Interviewee'}
                                      </span>
                                      {item.question_type && (
                                        <span className="qa-type-badge">
                                          {item.question_type === 'BEHAVIORAL' ? 'Behavioral' : 'Technical'}
                                        </span>
                                      )}
                                    </div>
                                    <div className="qa-content">
                                      <div className={`qa-message-section ${isAI ? 'ai-message-content' : 'interviewee-message-content'}`}>
                                        {item.text || 'No content'}
                                      </div>
                                      {isInterviewee && item.response_time > 0 && (
                                        <div className="qa-timestamp">
                                          Response Time: {item.response_time.toFixed(1)}s
                                        </div>
                                      )}
                                      {isInterviewee && item.answered_at && (
                                        <div className="qa-timestamp">
                                          Answered: {new Date(item.answered_at).toLocaleDateString('en-GB') + ', ' + new Date(item.answered_at).toLocaleTimeString('en-US', {
                                            hour: '2-digit',
                                            minute: '2-digit',
                                            hour12: false
                                          })}
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                );
                              })}
                            </>
                          )}
                          
                          {/* Coding Questions Section - Conversation Format */}
                          {codingConversation.length > 0 && (
                            <>
                              <div className="qa-section-divider">
                                <h5 className="qa-section-label">Coding Questions</h5>
                              </div>
                              {codingConversation.map((item, index) => {
                                const isAI = item.role === 'AI';
                                const isInterviewee = item.role === 'Interviewee';
                                return (
                                  <div key={item.id || `coding-conv-${index}`} className={`qa-card-item conversation-item ${isAI ? 'ai-message' : 'interviewee-message'}`}>
                                    <div className="qa-header-info">
                                      <span className={`qa-role-badge ${isAI ? 'ai-badge' : 'interviewee-badge'}`}>
                                        {isAI ? '🤖 AI' : '👤 Interviewee'}
                                      </span>
                                      <span className="qa-type-badge">Coding</span>
                                    </div>
                                    <div className="qa-content">
                                      <div className={`qa-message-section ${isAI ? 'ai-message-content' : 'interviewee-message-content'}`}>
                                        {isInterviewee && item.text && item.text !== 'No code submitted' ? (
                                          <pre className="qa-code-block">{item.text}</pre>
                                        ) : (
                                          <div>{item.text || 'No content'}</div>
                                        )}
                                      </div>
                                      {isInterviewee && item.response_time > 0 && (
                                        <div className="qa-timestamp">
                                          Response Time: {item.response_time.toFixed(1)}s
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                );
                              })}
                            </>
                          )}
                        </div>
                      </div>
                    );
                  } else {
                    // Old format: Q&A pairs (backward compatibility)
                  const codingQuestions = qaData
                    .filter(qa => (qa.question_type || '').toUpperCase() === 'CODING')
                    .sort((a, b) => {
                      const orderA = a.order !== undefined && a.order !== null ? a.order : 9999;
                      const orderB = b.order !== undefined && b.order !== null ? b.order : 9999;
                      return orderA - orderB;
                    });
                  const technicalQuestions = qaData
                    .filter(qa => !codingQuestions.includes(qa))
                    .sort((a, b) => {
                      const orderA = a.order !== undefined && a.order !== null ? a.order : 9999;
                      const orderB = b.order !== undefined && b.order !== null ? b.order : 9999;
                      return orderA - orderB;
                    });
                  
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
                              {technicalQuestions.map((qa, index) => {
                                // Convert 0-indexed order to 1-indexed display number
                                const displayNumber = (qa.order !== undefined && qa.order !== null) ? qa.order + 1 : index + 1;
                                return (
                              <div key={qa.id || `tech-${index}`} className="qa-card-item">
                                <div className="qa-header-info">
                                    <span className="qa-number-circle">{displayNumber}</span>
                                  <span className="qa-type-badge">{qa.question_type === 'BEHAVIORAL' ? 'Behavioral' : 'Technical'}</span>
                                </div>
                                <div className="qa-content">
                                  <div className="qa-question-section">
                                      {qa.question_text && qa.question_text.trim().startsWith('Q:') ? (
                                        qa.question_text
                                      ) : (
                                        <><strong>Q:</strong> {qa.question_text}</>
                                      )}
                                  </div>
                                  <div className="qa-answer-section">
                                      {qa.answer && qa.answer.trim().startsWith('A:') ? (
                                        <div className="qa-answer-text">{qa.answer}</div>
                                      ) : (
                                        <>
                                    <strong>A:</strong>
                                    <div className="qa-answer-text">
                                      {qa.answer || 'No answer provided'}
                                    </div>
                                        </>
                                      )}
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
                            {codingQuestions.map((qa, index) => {
                              // Convert 0-indexed order to 1-indexed display number
                              // For coding questions, continue numbering after technical questions
                              const displayNumber = (qa.order !== undefined && qa.order !== null) ? qa.order + 1 : technicalQuestions.length + index + 1;
                              return (
                              <div key={qa.id || `coding-${index}`} className="qa-card-item">
                                <div className="qa-header-info">
                                  <span className="qa-number-circle">{displayNumber}</span>
                                  <span className="qa-type-badge">Coding</span>
                                </div>
                                <div className="qa-content">
                                  <div className="qa-question-section">
                                    {qa.question_text && qa.question_text.trim().startsWith('Q:') ? (
                                      qa.question_text
                                    ) : (
                                      <><strong>Q:</strong> {qa.question_text}</>
                                    )}
                                  </div>
                                  <div className="qa-answer-section">
                                    {qa.answer && qa.answer.trim().startsWith('A:') ? (
                                      qa.answer && qa.answer !== 'No code submitted' && qa.answer !== 'A: No code submitted' ? (
                                        <pre className="qa-code-block">
                                          {qa.answer.replace(/^A:\s*/, '')}
                                        </pre>
                                      ) : (
                                        <span>{qa.answer || 'No code submitted'}</span>
                                      )
                                    ) : (
                                      <>
                                    <strong>A:</strong>
                                    {qa.answer && qa.answer !== 'No code submitted' ? (
                                      <pre className="qa-code-block">
                                        {qa.answer}
                                      </pre>
                                    ) : (
                                      <span>{qa.answer || 'No code submitted'}</span>
                                        )}
                                      </>
                                    )}
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
