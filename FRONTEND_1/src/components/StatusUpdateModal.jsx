// StatusUpdateModal.jsx
import React, { useState, useEffect } from "react";
import { baseURL } from "../data";
import HorizontalDatePicker from "./HorizontalDatePicker";
import TimeSlotPicker from "./TimeSlotPicker";
import Modal from "./common/Modal";
import { useNotification } from "../hooks/useNotification";
import { useDispatch } from "react-redux";
import { updateCandidateStatus } from "../redux/slices/candidatesSlice";
import "./StatusUpdateModal.css";

const StatusUpdateModal = ({
  isOpen,
  onClose,
  action,
  candidate,
  interviews,
  onInterviewScheduled,
  onEvaluationSubmitted,
  onUpdateStatus,
  isEditMode = false,
  editingInterview = null,
  editingEvaluation = null,
}) => {
  const notify = useNotification();
  const dispatch = useDispatch();
  const [loading, setLoading] = useState(false);
  const [authToken, setAuthToken] = useState("");

  // Get auth token from localStorage when component mounts
  useEffect(() => {
    const token = localStorage.getItem("authToken");
    if (token) {
      setAuthToken(token);
    } else {
      notify.error("Authentication token not found. Please log in again.");
    }
  }, []);

  // Common headers for API calls
  const getAuthHeaders = () => ({
    "Content-Type": "application/json",
    Authorization: `Token ${authToken}`,
  });

  // Schedule Interview Form State
  const [scheduleForm, setScheduleForm] = useState({
    selectedDate: new Date(),
    selectedTimes: [],
    feedback: "",
  });

  // Initialize form for edit mode
  useEffect(() => {
    // Form initialization effect
    
    if (isEditMode && editingInterview) {
      const interviewDate = new Date(editingInterview.started_at);
      const startTime = editingInterview.started_at.split('T')[1].substring(0, 5);
      const endTime = editingInterview.ended_at.split('T')[1].substring(0, 5);
      
      setScheduleForm({
        selectedDate: interviewDate,
        selectedTimes: [`${startTime}-${endTime}`],
        feedback: editingInterview.feedback || "",
      });
    } else if (isEditMode && editingEvaluation && action === "evaluate") {
      // Edit evaluation mode
      
      const formData = {
        overall_score: editingEvaluation.overall_score?.toString() || "",
        traits: editingEvaluation.traits || "",
        suggestions: editingEvaluation.suggestions || "",
      };
      
      setEvaluationForm(formData);
    } else {
      setScheduleForm({
        selectedDate: new Date(),
        selectedTimes: [],
        feedback: "",
      });
      setEvaluationForm({
        overall_score: "",
        traits: "",
        suggestions: "",
      });
    }
  }, [isEditMode, editingInterview, editingEvaluation, action]);

  // Additional effect to ensure form is updated when editingEvaluation changes
  useEffect(() => {
    if (isEditMode && editingEvaluation && action === "evaluate") {
      setEvaluationForm({
        overall_score: editingEvaluation.overall_score?.toString() || "",
        traits: editingEvaluation.traits || "",
        suggestions: editingEvaluation.suggestions || "",
      });
    }
  }, [editingEvaluation?.id, isEditMode, action]); // Only run when evaluation ID changes

  // Force form update when modal opens in edit mode
  useEffect(() => {
    if (isOpen && isEditMode && editingEvaluation && action === "evaluate") {
      const formData = {
        overall_score: editingEvaluation.overall_score?.toString() || "",
        traits: editingEvaluation.traits || "",
        suggestions: editingEvaluation.suggestions || "",
      };
      
      setEvaluationForm(formData);
    }
  }, [isOpen, isEditMode, editingEvaluation, action]);

  // Additional effect to reset form when editingEvaluation changes (only once)
  useEffect(() => {
    if (editingEvaluation && isEditMode && action === "evaluate") {
      // Initialize form with new evaluation data
      
      setEvaluationForm({
        overall_score: editingEvaluation.overall_score?.toString() || "",
        traits: editingEvaluation.traits || "",
        suggestions: editingEvaluation.suggestions || "",
      });
    }
  }, [editingEvaluation?.id]); // Only run when evaluation ID changes

  // Evaluation Form State
  const [evaluationForm, setEvaluationForm] = useState({
    overall_score: "",
    traits: "",
    suggestions: "",
  });

  // Hire/Reject Form State
  const [hireRejectForm, setHireRejectForm] = useState({
    decision: "", // 'hired' or 'rejected'
    feedback: "",
  });

  const resetForms = () => {
    setScheduleForm({
      selectedDate: new Date(),
      selectedTimes: [],
      feedback: "",
    });
    setEvaluationForm({
      overall_score: "",
      traits: "",
      suggestions: "",
    });
    setHireRejectForm({
      decision: "",
      feedback: "",
    });
  };

  useEffect(() => {
    if (isOpen) {
      resetForms();
    }
  }, [isOpen, action]);

  const handleScheduleInterview = async () => {
    // Handle schedule interview
    
    if (!authToken) {
      notify.error("Authentication token not found. Please log in again.");
      return;
    }

    if (scheduleForm.selectedTimes.length === 0) {
      notify.error("Please select a time slot");
      return;
    }

    // Convert selected times to proper datetime format
    const selectedDate = scheduleForm.selectedDate.toISOString().split("T")[0];
    let startedAt = null;
    let endedAt = null;
    
    if (scheduleForm.selectedTimes.length > 0) {
      // Get the first selected time slot
      const firstTime = scheduleForm.selectedTimes[0];
      const lastTime = scheduleForm.selectedTimes[scheduleForm.selectedTimes.length - 1];
      
      // Parse time ranges (e.g., "10:00-11:00" or "10:00")
      let startTime, endTime;
      
      if (firstTime.includes("-")) {
        startTime = firstTime.split("-")[0];
      } else {
        startTime = firstTime;
      }
      
      if (lastTime.includes("-")) {
        endTime = lastTime.split("-")[1];
      } else {
        // If no end time specified, assume 1 hour duration
        const [hours, minutes] = startTime.split(":");
        const endHours = (parseInt(hours) + 1).toString().padStart(2, "0");
        endTime = `${endHours}:${minutes}`;
      }
      
      // Create timezone-aware datetime strings using the same approach as AI Interview Scheduler
      // Use the selected date and time directly without timezone conversion
      startedAt = `${selectedDate}T${startTime}:00`;
      endedAt = `${selectedDate}T${endTime}:00`;
      
      // Calculate interview times
    }

    // Validate that we have valid start and end times
    if (!startedAt || !endedAt) {
      notify.error("Please select valid time slots for the interview");
      return;
    }

    setLoading(true);

    try {
      // First, find the matching slot to get the slot ID
      const formattedDate = scheduleForm.selectedDate.toISOString().split("T")[0];
      // Fetch available slots
      
      const slotsResponse = await fetch(
        `${baseURL}/api/interviews/slots/?date=${formattedDate}&status=available`,
        {
          headers: getAuthHeaders(),
        }
      );

      if (!slotsResponse.ok) {
        throw new Error("Failed to fetch available slots");
      }

      const slotsData = await slotsResponse.json();
      const availableSlots = slotsData.results || slotsData || [];

      // Process available slots

      // Find the matching slot
      
      const matchingSlot = availableSlots.find(slot => {
        let slotStartTime, slotEndTime;
        
        if (typeof slot.start_time === 'string') {
          if (slot.start_time.includes("T")) {
            // Handle datetime format: "2025-09-23T10:30:00Z" -> "10:30"
            slotStartTime = slot.start_time.split("T")[1]?.substring(0, 5);
            slotEndTime = slot.end_time.split("T")[1]?.substring(0, 5);
          } else {
            // Handle time format: "10:30:00" -> "10:30"
            slotStartTime = slot.start_time.substring(0, 5);
            slotEndTime = slot.end_time.substring(0, 5);
          }
        } else {
          // Handle other formats (shouldn't happen with current API)
          return false;
        }
        
        const slotTimeRange = `${slotStartTime}-${slotEndTime}`;
        const isMatch = scheduleForm.selectedTimes.includes(slotTimeRange);
        return isMatch;
      });

      if (matchingSlot) {
        // Found matching slot
        
        // Handle slot changes for edit mode
        if (isEditMode && editingInterview) {
          const oldSlotId = editingInterview.slot || editingInterview.slot_details?.id;
          const newSlotId = matchingSlot.id;
          
          // If slot has changed, release the old slot
          if (oldSlotId && oldSlotId !== newSlotId) {
            try {
              const releaseResponse = await fetch(`${baseURL}/api/interviews/slots/${oldSlotId}/release_slot/`, {
                method: "POST",
                headers: getAuthHeaders(),
              });
              
              if (releaseResponse.ok) {
                // Old slot released successfully
              } else {
                // Failed to release old slot, but continuing with new slot booking
              }
            } catch (error) {
              // Error releasing old slot, but continuing with new slot booking
            }
          } else if (oldSlotId === newSlotId) {
            // Same slot selected, no slot change needed
          }
        }
        
        // Check if candidate already has an interview for this slot (excluding current interview in edit mode)
        
        // Check if this candidate already has an interview for this specific slot
        const existingInterviewForSlot = interviews.find(interview => {
          // In edit mode, exclude the current interview being edited
          if (isEditMode && editingInterview && interview.id === editingInterview.id) {
            return false;
          }
          return interview.slot === matchingSlot.id || 
                 (interview.slot_details && interview.slot_details.id === matchingSlot.id);
        });
        
        if (existingInterviewForSlot) {
          notify.error("This candidate already has an interview scheduled for this time slot. Please select a different time slot.");
          return;
        }
        
        // Use the ACTUAL slot times instead of parsed selected times
        const slotStartTime = matchingSlot.start_time.substring(0, 5); // "09:00:00" -> "09:00"
        const slotEndTime = matchingSlot.end_time.substring(0, 5); // "09:30:00" -> "09:30"
        
        // Update the interview times to use the actual slot times
        startedAt = `${selectedDate}T${slotStartTime}:00`;
        endedAt = `${selectedDate}T${slotEndTime}:00`;
        
        // Use actual slot times for consistency
      } else {
        // No matching slot found, using parsed selected times
      }

      const interviewData = {
        candidate: candidate.id,
        job: candidate.job?.id || candidate.job || null,
        ...(matchingSlot && { slot: matchingSlot.id }), // Only add slot if found
        started_at: startedAt,
        ended_at: endedAt,
        feedback: scheduleForm.feedback || "",
      };

      // Send interview data

      // Step 1: Create or update the interview
      const url = isEditMode ? `${baseURL}/api/interviews/${editingInterview.id}/` : `${baseURL}/api/interviews/`;
      const method = isEditMode ? "PATCH" : "POST";
      
      const response = await fetch(url, {
        method: method,
        headers: getAuthHeaders(),
        body: JSON.stringify(interviewData),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        
        // Handle error data
        
        throw new Error(errorData.detail || errorData.message || JSON.stringify(errorData) || "Failed to create interview");
      }

      const responseData = await response.json();
      const interviewId = responseData.id;

      // Step 2: Update the slot booking (only if we found a matching slot)
      if (matchingSlot) {
        // Slot booking process
        
        // Update slot booking based on current bookings
        const currentBookings = matchingSlot.current_bookings || 0;
        const maxCandidates = matchingSlot.max_candidates || 1;
        
        let updateData;
        if (currentBookings >= maxCandidates - 1) {
          // If this is the last available slot, mark as booked
          updateData = {
            current_bookings: maxCandidates,
            status: "booked"
          };
        } else {
          // Otherwise, just increment current_bookings
          updateData = {
            current_bookings: currentBookings + 1
          };
        }

        console.log("=== SLOT UPDATE PROCESS ===");
        console.log(`Updating slot ${matchingSlot.id}:`, updateData);
        console.log(`Before update - current_bookings: ${currentBookings}, max_candidates: ${maxCandidates}`);

        // Get the complete slot data first
        console.log("Fetching complete slot data...");
        const slotGetResponse = await fetch(
          `${baseURL}/api/interviews/slots/${matchingSlot.id}/`,
          {
            method: "GET",
            headers: getAuthHeaders(),
          }
        );

        if (!slotGetResponse.ok) {
          console.error("Failed to fetch slot data for update");
        } else {
          const completeSlotData = await slotGetResponse.json();
          console.log("Complete slot data fetched:", completeSlotData);
          
          // Merge the update data with complete slot data
          const fullUpdateData = {
            ...completeSlotData,
            ...updateData
          };

          console.log("Full update data (merged):", fullUpdateData);
          console.log("Update data being sent:", updateData);

          console.log("Sending PUT request to update slot...");
          const slotUpdateResponse = await fetch(
            `${baseURL}/api/interviews/slots/${matchingSlot.id}/`,
            {
              method: "PUT",
              headers: getAuthHeaders(),
              body: JSON.stringify(fullUpdateData),
            }
          );

          console.log("Slot update response status:", slotUpdateResponse.status);
          console.log("Slot update response headers:", Object.fromEntries(slotUpdateResponse.headers.entries()));

          if (!slotUpdateResponse.ok) {
            const errorData = await slotUpdateResponse.json().catch(() => ({}));
            console.error("=== SLOT UPDATE FAILED ===");
            console.error("Failed to update slot:", errorData);
            console.error("Response status:", slotUpdateResponse.status);
            console.warn("Failed to update slot, but interview was created");
          } else {
            const updatedSlotData = await slotUpdateResponse.json();
            console.log("=== SLOT UPDATE SUCCESS ===");
            console.log("Slot updated successfully:", updatedSlotData);
            console.log(`After update - current_bookings: ${updatedSlotData.current_bookings}, status: ${updatedSlotData.status}`);
            console.log("Updated slot times:", {
              start_time: updatedSlotData.start_time,
              end_time: updatedSlotData.end_time
            });
          }
        }

        // Also create the schedule relationship
        const bookingData = {
          interview_id: interviewId,
          booking_notes: scheduleForm.feedback || ""
        };

        console.log("=== CREATING SCHEDULE RELATIONSHIP ===");
        console.log("Sending booking data:", bookingData);
        console.log("Matching slot details:", {
          id: matchingSlot.id,
          status: matchingSlot.status,
          current_bookings: matchingSlot.current_bookings,
          max_candidates: matchingSlot.max_candidates
        });
        
        const bookingResponse = await fetch(
          `${baseURL}/api/interviews/slots/${matchingSlot.id}/book_slot/`,
          {
            method: "POST",
            headers: getAuthHeaders(),
            body: JSON.stringify(bookingData),
          }
        );

        console.log("Schedule creation response status:", bookingResponse.status);
        console.log("Schedule creation response headers:", Object.fromEntries(bookingResponse.headers.entries()));

        if (!bookingResponse.ok) {
          const errorData = await bookingResponse.json().catch(() => ({}));
          console.error("=== SCHEDULE CREATION FAILED ===");
          console.error("Failed to create schedule relationship:", errorData);
          console.error("Response status:", bookingResponse.status);
          console.error("Response headers:", Object.fromEntries(bookingResponse.headers.entries()));
          console.error("Full error response:", errorData);
          console.warn("Failed to create schedule relationship, but interview was created");
        } else {
          const scheduleResult = await bookingResponse.json();
          console.log("=== SCHEDULE CREATION SUCCESS ===");
          console.log("Schedule relationship created:", scheduleResult);
        }
      }

      notify.success(isEditMode ? "Interview updated successfully!" : "Interview scheduled successfully!");
      onClose();
      // Call callback to refresh interview data
      if (onInterviewScheduled) {
        onInterviewScheduled();
      }
    } catch (err) {
      console.error("Error scheduling interview:", err);
      notify.error(err.message || "Error scheduling interview");
    } finally {
      setLoading(false);
    }
  };

  const handleEvaluate = async () => {
    const token = localStorage.getItem("authToken");
    if (!token) {
      notify.error("Authentication token not found. Please log in again.");
      return;
    }

    if (!evaluationForm.overall_score || !evaluationForm.traits) {
      notify.error("Please fill in all required fields");
      return;
    }

    const latestInterview = interviews[interviews.length - 1];
    if (!latestInterview) {
      notify.error("No interview found to evaluate");
      return;
    }

    setLoading(true);
    try {
      const evaluationData = {
        interview: latestInterview.id,
        overall_score: parseFloat(evaluationForm.overall_score),
        traits: evaluationForm.traits,
        suggestions: evaluationForm.suggestions,
      };

      // Use PATCH for edit mode, POST for create mode
      const url = isEditMode && editingEvaluation 
        ? `${baseURL}/api/evaluation/crud/${editingEvaluation.id}/`
        : `${baseURL}/api/evaluation/crud/`;
      const method = isEditMode && editingEvaluation ? "PATCH" : "POST";

      const response = await fetch(url, {
        method: method,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Token ${token}`,
        },
        body: JSON.stringify(evaluationData),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to create evaluation");
      }

      notify.success(isEditMode ? "Evaluation updated successfully!" : "Evaluation submitted successfully!");
      
      // Call the callback to refresh evaluation data in parent component
      if (onEvaluationSubmitted) {
        onEvaluationSubmitted();
      }
      
      setTimeout(() => {
        onClose();
      }, 1500);
    } catch (error) {
      console.error("Error creating evaluation:", error);
      notify.error(
        error.message || "Failed to submit evaluation. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleHireReject = async () => {
    if (!authToken) {
      notify.error("Authentication token not found. Please log in again.");
      return;
    }

    if (!hireRejectForm.decision) {
      notify.error("Please select hire or reject");
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem("authToken");

      // Update candidate status
      const statusData = {
        status: hireRejectForm.decision === "hired" ? "HIRED" : "REJECTED",
        feedback: hireRejectForm.feedback,
      };

      const response = await fetch(
        `${baseURL}/api/candidates/${candidate.id}/`,
        {
          method: "PATCH",
          headers: getAuthHeaders(),
          body: JSON.stringify(statusData),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to update candidate status");
      }

      // Get the updated candidate data from API response
      const updatedCandidateData = await response.json();
      console.log("=== API RESPONSE DEBUG ===");
      console.log("API Response:", updatedCandidateData);
      console.log("Updated candidate status from API:", updatedCandidateData.status);

      // Update Redux state with the actual API response data
      dispatch(updateCandidateStatus({
        id: candidate.id,
        newStatus: updatedCandidateData.status,
        updatedData: updatedCandidateData
      }));

      notify.success(`Candidate ${hireRejectForm.decision} successfully!`);
      // Call the onUpdateStatus callback if provided
      if (onUpdateStatus) {
        onUpdateStatus();
      }
      onClose();
    } catch (error) {
      console.error("Error updating candidate status:", error);
      notify.error("Failed to update candidate status. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const fetchAvailableSlots = async (date) => {
    if (!authToken) return [];

    try {
      const formattedDate = date.toISOString().split("T")[0];
      const response = await fetch(
        `${baseURL}/api/interviews/slots/?date=${formattedDate}&is_available=true`,
        {
          headers: getAuthHeaders(),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to fetch available slots");
      }

      const data = await response.json();
      return data;
    } catch (err) {
      console.error("Error fetching available slots:", err);
      notify.error("Failed to load available time slots");
      return [];
    }
  };

  const renderScheduleInterviewForm = () => (
    <div className="modal-form">
      <h3>{isEditMode ? "Edit Interview" : "Schedule Interview"}</h3>

      <div className="form-group">
        <label>Select Date *</label>
        <HorizontalDatePicker
          selectedDate={scheduleForm.selectedDate}
          onSelectDate={(date) =>
            setScheduleForm({ ...scheduleForm, selectedDate: date })
          }
        />
      </div>

      <div className="form-group">
        <label>Select Time Slot *</label>
        <TimeSlotPicker
          selectedTimes={scheduleForm.selectedTimes}
          onSelectTimes={(times) =>
            setScheduleForm({ ...scheduleForm, selectedTimes: times })
          }
          selectedDate={scheduleForm.selectedDate}
          baseURL={baseURL}
          isModal={true}
        />
      </div>

      <div className="form-group">
        <label>Additional Notes</label>
        <textarea
          value={scheduleForm.feedback}
          onChange={(e) =>
            setScheduleForm({ ...scheduleForm, feedback: e.target.value })
          }
          placeholder="Any additional notes for the interview"
          rows="3"
        />
      </div>

    </div>
  );

  const renderAIEvaluationForm = () => {
    return (
      <div className="ai-evaluation-info">
        <div className="info-card">
          <h3>🤖 AI Evaluation</h3>
          <p>AI evaluation is automatically generated based on the candidate's interview performance.</p>
          <p>This evaluation includes:</p>
          <ul>
            <li>Technical skills assessment</li>
            <li>Problem-solving abilities</li>
            <li>Communication skills</li>
            <li>Overall performance rating</li>
            <li>Strengths and areas for improvement</li>
            <li>Hire recommendation</li>
          </ul>
          <p><strong>Note:</strong> AI evaluation is generated automatically after the interview is completed. No manual input is required.</p>
        </div>
      </div>
    );
  };

  const renderEvaluationForm = () => {
    console.log("=== RENDERING EVALUATION FORM ===");
    console.log("isEditMode:", isEditMode);
    console.log("editingEvaluation:", editingEvaluation);
    console.log("evaluationForm state:", evaluationForm);
    
    // Ensure form is populated if we're in edit mode
    if (isEditMode && editingEvaluation && action === "evaluate") {
      const expectedData = {
        overall_score: editingEvaluation.overall_score?.toString() || "",
        traits: editingEvaluation.traits || "",
        suggestions: editingEvaluation.suggestions || "",
      };
      
      console.log("Expected data for form:", expectedData);
      console.log("Current form data:", evaluationForm);
      
      // If form is empty but we have evaluation data, populate it
      if (!evaluationForm.overall_score && !evaluationForm.traits && !evaluationForm.suggestions) {
        console.log("Form is empty, populating with evaluation data");
        setEvaluationForm(expectedData);
      }
    }
    
    return (
      <div className="modal-form" key={editingEvaluation?.id || 'new'}>
        <h3>{isEditMode ? "Edit Evaluation" : "Evaluate Candidate"}</h3>

      <div className="form-group">
        <label>Overall Score (0-10) *</label>
        <input
          type="number"
          step="0.1"
          min="0"
          max="10"
          value={evaluationForm.overall_score}
          onChange={(e) =>
            setEvaluationForm({
              ...evaluationForm,
              overall_score: e.target.value,
            })
          }
          placeholder="8.5"
          required
        />
      </div>

      <div className="form-group">
        <label>Traits & Strengths *</label>
        <textarea
          value={evaluationForm.traits}
          onChange={(e) =>
            setEvaluationForm({ ...evaluationForm, traits: e.target.value })
          }
          placeholder="Strong technical skills, excellent problem-solving ability, good communication..."
          rows="4"
          required
        />
      </div>

      <div className="form-group">
        <label>Suggestions & Feedback</label>
        <textarea
          value={evaluationForm.suggestions}
          onChange={(e) =>
            setEvaluationForm({
              ...evaluationForm,
              suggestions: e.target.value,
            })
          }
          placeholder="Consider for next round, focus on system design in future interviews..."
          rows="4"
        />
      </div>

    </div>
    );
  };

  const renderHireRejectForm = () => (
    <div className="modal-form">
      <h3>Final Decision</h3>

      <div className="form-group">
        <label>Decision *</label>
        <div className="decision-buttons">
          <button
            type="button"
            className={`decision-btn hire ${
              hireRejectForm.decision === "hired" ? "selected" : ""
            }`}
            onClick={() =>
              setHireRejectForm({ ...hireRejectForm, decision: "hired" })
            }
          >
            ✓ Hire
          </button>
          <button
            type="button"
            className={`decision-btn reject ${
              hireRejectForm.decision === "rejected" ? "selected" : ""
            }`}
            onClick={() =>
              setHireRejectForm({ ...hireRejectForm, decision: "rejected" })
            }
          >
            ✗ Reject
          </button>
        </div>
      </div>

      <div className="form-group">
        <label>Feedback & Reasoning</label>
        <textarea
          value={hireRejectForm.feedback}
          onChange={(e) =>
            setHireRejectForm({ ...hireRejectForm, feedback: e.target.value })
          }
          placeholder="Provide reasoning for your decision..."
          rows="4"
        />
      </div>

    </div>
  );

  const renderForm = () => {
    switch (action) {
      case "schedule_interview":
        return renderScheduleInterviewForm();
      case "ai_evaluate":
        return renderAIEvaluationForm();
      case "manual_evaluate":
        return renderEvaluationForm();
      case "hire_reject":
        return renderHireRejectForm();
      default:
        return <div>Unknown action</div>;
    }
  };

  const getModalTitle = () => {
    switch (action) {
      case "schedule_interview":
        return isEditMode ? "Edit Interview" : "Schedule Interview";
      case "ai_evaluate":
        return "AI Evaluation";
      case "manual_evaluate":
        return isEditMode ? "Edit Manual Evaluation" : "Manual Evaluation";
      case "hire_reject":
        return "Hire/Reject Decision";
      default:
        return "Update Status";
    }
  };

  if (!isOpen) return null;

  const getModalFooter = () => {
    switch (action) {
      case "schedule_interview":
        return (
          <div className="modal-form-actions">
            <button type="button" onClick={onClose} className="common-modal-btn btn-cancel">
              Cancel
            </button>
            <button
              type="button"
              onClick={handleScheduleInterview}
              className="common-modal-btn btn-primary"
              disabled={loading}
            >
              {loading ? (isEditMode ? "Updating..." : "Scheduling...") : (isEditMode ? "Update Interview" : "Schedule Interview")}
            </button>
          </div>
        );
      case "ai_evaluate":
        return (
          <div className="modal-form-actions">
            <button type="button" onClick={onClose} className="common-modal-btn btn-cancel">
              Close
            </button>
          </div>
        );
      case "manual_evaluate":
        return (
          <div className="modal-form-actions">
            <button type="button" onClick={onClose} className="common-modal-btn btn-cancel">
              Cancel
            </button>
            <button
              type="button"
              onClick={handleEvaluate}
              className="common-modal-btn btn-primary"
              disabled={loading}
            >
              {loading ? (isEditMode ? "Updating..." : "Submitting...") : (isEditMode ? "Update Evaluation" : "Submit Evaluation")}
            </button>
          </div>
        );
      case "hire_reject":
        return (
          <div className="modal-form-actions">
            <button type="button" onClick={onClose} className="common-modal-btn btn-cancel">
              Cancel
            </button>
            <button
              type="button"
              onClick={handleHireReject}
              className="common-modal-btn btn-primary"
              disabled={loading || !hireRejectForm.decision}
            >
              {loading ? "Processing..." : "Submit Decision"}
            </button>
          </div>
        );
      default:
        return (
          <div className="modal-confirm-actions">
            <button className="common-modal-btn btn-cancel" onClick={onClose}>
              Close
            </button>
          </div>
        );
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={getModalTitle()}
      size="large"
      showCloseButton={true}
      closeOnBackdrop={!loading}
      closeOnEscape={!loading}
      showFooter={true}
      footer={getModalFooter()}
    >
      {renderForm()}
    </Modal>
  );
};

export default StatusUpdateModal;
