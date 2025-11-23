// AiInterviewScheduler.jsx - Company Slot Management System
import React, { useState, useEffect, useCallback, useMemo } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  fetchInterviewSlots,
  setSlots,
} from "../redux/slices/interviewSlotsSlice";
import CustomDropdown from './common/CustomDropdown';
import {
  FiPlus,
  FiEdit,
  FiTrash2,
  FiCalendar,
  FiClock,
  FiUsers,
  FiSettings,
  FiBarChart,
} from "react-icons/fi";
import { BeatLoader } from "react-spinners";
import HorizontalDatePicker from "./HorizontalDatePicker";
import TimeSlotPicker from "./TimeSlotPicker";
import DataTable from "./common/DataTable";
import LoadingSpinner from "./common/LoadingSpinner";
import ContextMenu from "./common/ContextMenu";
import { baseURL } from "../config/constants";
import { useNotification } from "../hooks/useNotification";
import { formatTimeTo24Hour } from "../utils/timeFormatting";
import "./AiInterviewScheduler.css";

const AiInterviewScheduler = ({
  onTitleChange,
}) => {
  const dispatch = useDispatch();
  const notify = useNotification();
  const searchTerm = useSelector((state) => state.search?.searchTerm || '');
  
  // Search term handling
  useEffect(() => {
    // Handle search term changes
  }, [searchTerm]);
  const {
    slots,
    loading: slotsLoading,
    error: slotsError,
  } = useSelector(
    (state) =>
      state.interviewSlots ?? { slots: [], loading: false, error: null }
  );

  // Get user data from Redux store
  const user = useSelector(
    (state) => state?.user?.user || state?.user?.currentUser || {}
  );

  const [initialLoading, setInitialLoading] = useState(true);
  const [retryCount] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [editingSlot, setEditingSlot] = useState(null);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [selectedTimes, setSelectedTimes] = useState([]);
  const [refreshKey, setRefreshKey] = useState(0);
  const [showMobileForm, setShowMobileForm] = useState(false);
  const [hasShownError, setHasShownError] = useState(false);
  const [companies, setCompanies] = useState([]);
  const [selectedCompanyId, setSelectedCompanyId] = useState(null);
  const [companiesLoading, setCompaniesLoading] = useState(false);
  const [jobs, setJobs] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState(null);
  const [jobsLoading, setJobsLoading] = useState(false);

  // Context menu state
  const [contextMenu, setContextMenu] = useState({
    visible: false,
    x: 0,
    y: 0,
    rowData: null,
    rowIndex: null,
  });

  // DataTable edit state
  const [editingRow, setEditingRow] = useState(null);
  const [editingData, setEditingData] = useState(null);

  // Sort slots based on search term for better user experience
  const sortedSlots = useMemo(() => {
    if (!slots || slots.length === 0) return [];
    
    // If no search term, return all slots sorted by date (most recent first)
    if (!searchTerm) {
      return [...slots].sort((a, b) => {
        if (a.interview_date && b.interview_date) {
          return new Date(b.interview_date) - new Date(a.interview_date);
        }
        return 0;
      });
    }
    
    const searchLower = searchTerm.toLowerCase();
    
    return [...slots].sort((a, b) => {
      // Calculate relevance scores for both slots - search ALL fields
      const getRelevanceScore = (slot) => {
        let score = 0;
        
        // Search ALL fields in the slot object dynamically
        const searchAllFields = (obj, prefix = '') => {
          Object.entries(obj || {}).forEach(([key, value]) => {
            if (value === null || value === undefined) return;
            
            let searchValue;
            if (typeof value === 'object' && value !== null) {
              // Handle nested objects recursively
              searchAllFields(value, `${prefix}${key}.`);
              return;
            } else if (typeof value === 'boolean') {
              searchValue = value ? 'true' : 'false';
            } else if (typeof value === 'number') {
              searchValue = String(value);
            } else if (value instanceof Date) {
              searchValue = value.toLocaleDateString() + ' ' + value.toLocaleTimeString('en-US', {
                hour: 'numeric',
                minute: '2-digit',
                hour12: true
              });
            } else {
              searchValue = String(value);
            }
            
            const fieldStr = searchValue.toLowerCase();
            if (fieldStr.includes(searchLower)) {
              if (fieldStr.startsWith(searchLower)) score += 10; // Starts with search term
              else score += 5; // Contains search term
            }
          });
        };
        
        searchAllFields(slot);
        
        // Calculate relevance score for search
        
        return score;
      };
      
      const aScore = getRelevanceScore(a);
      const bScore = getRelevanceScore(b);
      
      // Sort by relevance score (higher scores first)
      if (bScore !== aScore) return bScore - aScore;
      
      // If same relevance, sort by date (most recent first)
      if (a.interview_date && b.interview_date) {
        return new Date(b.interview_date) - new Date(a.interview_date);
      }
      
      return 0;
    });
  }, [slots, searchTerm]);

  // Initialize form with default values (updated for 10-minute slots)
  const [slotForm, setSlotForm] = useState(() => ({
    ai_interview_type: "technical",
    difficulty_level: "intermediate",
    question_count: 10, // Use number instead of string
    time_limit: "10", // Default to 10 minutes for 10-minute slots
    topics: "",
    max_candidates: "1",
    job: "",
    company: "",
  }));

  // Reset form function - defined before any handlers that use it
  const resetSlotForm = useCallback(() => {
    setSelectedDate(new Date());
    setSelectedTimes([]);
    setSlotForm({
      ai_interview_type: "technical",
      difficulty_level: "intermediate",
      question_count: 10, // Use number instead of string
      time_limit: "10", // Default to 10 minutes for 10-minute slots
      topics: "",
      max_candidates: "1",
      job: "",
      company: "",
    });
  }, []);

  // Initialize data with better error handling
  const initializeData = useCallback(async () => {
    setInitialLoading(true);
    try {
      const token = localStorage.getItem("authToken");
      if (!token) {
        throw new Error("No authentication token found");
      }

      const resultAction = await dispatch(fetchInterviewSlots());

      if (fetchInterviewSlots.fulfilled.match(resultAction)) {
        // Slots loaded successfully
      } else {
        notify.error(
          resultAction.error.message || "Failed to load interview slots"
        );
      }
    } catch (error) {
      notify.error(error.message || "An error occurred while loading slots");
    } finally {
      setInitialLoading(false);
    }
  }, [dispatch, notify]);

  // Fetch jobs for a specific company
  const fetchJobsForCompany = useCallback(async (companyId) => {
    if (!companyId) {
      setJobs([]);
      return;
    }
    
    setJobsLoading(true);
    try {
      const authToken = localStorage.getItem("authToken");
      if (!authToken) throw new Error("Authentication token not found");

      const response = await fetch(`${baseURL}/api/jobs/?company_id=${companyId}`, {
        headers: {
          "Content-Type": "application/json",
          Authorization: `Token ${authToken}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch jobs: ${response.status}`);
      }

      const data = await response.json();
      const jobsData = data.results || data;
      
      if (Array.isArray(jobsData) && jobsData.length === 0) {
        notify.info('No jobs found for this company');
      }
      
      setJobs(Array.isArray(jobsData) ? jobsData : []);
    } catch {
      console.error('Error fetching jobs');
      notify.error('Failed to fetch jobs');
      setJobs([]);
    } finally {
      setJobsLoading(false);
    }
  }, [notify]);

  // Fetch companies for admin users
  const fetchCompanies = useCallback(async () => {
    if (user?.role?.toLowerCase() !== 'admin') return;
    
    setCompaniesLoading(true);
    try {
      const authToken = localStorage.getItem("authToken");
      if (!authToken) throw new Error("Authentication token not found");

      const response = await fetch(`${baseURL}/api/companies/`, {
        headers: {
          "Content-Type": "application/json",
          Authorization: `Token ${authToken}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch companies: ${response.status}`);
      }

      const data = await response.json();
      const companiesData = data.results || data;
      setCompanies(Array.isArray(companiesData) ? companiesData : []);
    } catch {
      console.error('Error fetching companies');
      notify.error('Failed to fetch companies');
    } finally {
      setCompaniesLoading(false);
    }
  }, [user?.role, notify]);

  useEffect(() => {
    if (user && Object.keys(user).length > 0) {
      initializeData();
      fetchCompanies();
      
      // Set default company based on user role
      if (user.role?.toLowerCase() === 'company') {
        const companyId = user.id || user.company_id;
        setSelectedCompanyId(companyId);
        // Fetch jobs for company users immediately
        fetchJobsForCompany(companyId);
      }
    } else {
      notify.error("Please log in to access interview scheduling.");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  // Handle company changes for admin users
  useEffect(() => {
    if (user?.role?.toLowerCase() === 'admin' && selectedCompanyId) {
      fetchJobsForCompany(selectedCompanyId);
      setSelectedJobId(null); // Reset job selection when company changes
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedCompanyId, user?.role]);

  // Context menu handlers
  const handleContextMenuClick = (event, rowData, rowIndex) => {
    event.preventDefault();
    event.stopPropagation();
    
    setContextMenu({
      visible: true,
      x: event.clientX,
      y: event.clientY,
      rowData,
      rowIndex,
    });
  };

  const handleContextMenuAction = (action, rowData, rowIndex) => {
    if (action === "edit") {
      // Trigger DataTable's edit mode by setting editing state
      setEditingRow(rowIndex);
      setEditingData({ ...rowData });
    } else if (action === "delete") {
      // Use the same delete function that shows confirmation
      handleDeleteSlot(rowData.id);
    }
  };

  const handleContextMenuClose = () => {
    setContextMenu({
      visible: false,
      x: 0,
      y: 0,
      rowData: null,
      rowIndex: null,
    });
  };


  // Enhanced fetchSlots with better error handling
  const fetchSlots = useCallback(
    async (force = false) => {
      if ((slotsLoading || isSubmitting) && !force) {
        return;
      }

      try {
        const authToken = localStorage.getItem("authToken");
        if (!authToken) {
          throw new Error("Authentication token not found");
        }

        const userData = JSON.parse(localStorage.getItem("user") || "{}");
        const companyId = userData?.company_id || userData?.id;

        let url = `${baseURL}/api/interviews/slots/`;
        if (companyId) {
          url += `${url.includes("?") ? "&" : "?"}company_id=${companyId}`;
        }

        const response = await fetch(url, {
          headers: {
            "Content-Type": "application/json",
            Authorization: `Token ${authToken}`,
          },
        });

        if (!response.ok) {
          throw new Error(
            `Failed to fetch slots: ${response.status} ${response.statusText}`
          );
        }

        const data = await response.json();
        // Handle both array and object with results property
        const slotsData = data.results || data;

        // Update Redux state with the fetched slots
        const validSlots = Array.isArray(slotsData) ? slotsData : [];
        dispatch(setSlots(validSlots));
        
        // Show success notification only if this is a manual refresh
        if (force) {
          notify.success("Interview slots refreshed successfully!");
        }
        
        // Reset error flag on successful load
        setHasShownError(false);
        
        return validSlots;
      } catch (error) {
        notify.error(error.message || "Failed to fetch slots");
        throw error;
      }
    },
    [slotsLoading, isSubmitting, dispatch, notify]
  );

  const handleDateSelect = useCallback((date) => {
    setSelectedDate(date);
    setSelectedTimes([]);
  }, []);

  const handleTimeSelect = useCallback((times, duration) => {
    setSelectedTimes(times);
    if (duration) {
      setSlotForm((prev) => ({
        ...prev,
        time_limit: duration,
      }));
    }
  }, []);

  const addMinutesToTime = useCallback((time, minutes, baseDate) => {
    if (!time) return "";
    const [hours, mins] = time.split(":").map(Number);
    const date = new Date(baseDate);
    date.setHours(hours, mins + minutes, 0, 0);

    const newHours = String(date.getHours()).padStart(2, "0");
    const newMins = String(date.getMinutes()).padStart(2, "0");

    return `${newHours}:${newMins}`;
  }, []);

  const handleSlotSubmit = useCallback(
    async (e) => {
      if (e) e.preventDefault();

      if (selectedTimes.length === 0) {
        notify.error("Please select at least one time slot");
        return;
      }

      // Validate required fields
      if (!slotForm.ai_interview_type) {
        notify.error("Please select an interview type");
        return;
      }

      if (!slotForm.difficulty_level) {
        notify.error("Please select a difficulty level");
        return;
      }

      // Validate company selection for admin users
      if (user?.role?.toLowerCase() === 'admin' && !selectedCompanyId) {
        notify.error("Please select a company");
        return;
      }

      // Validate job selection
      if (!selectedJobId) {
        notify.error("Please select a job");
        return;
      }

      try {
        setIsSubmitting(true);
        const authToken = localStorage.getItem("authToken");
        if (!authToken) throw new Error("Authentication token not found");

        console.log('👤 User data:', user);
        console.log('🏢 User company_id:', user?.company_id);
        console.log('🆔 User id:', user?.id);
        console.log('🎯 Selected company ID:', selectedCompanyId);
        console.log('📋 Available companies:', companies);
        console.log('💼 Selected job ID:', selectedJobId);
        console.log('📋 Available jobs:', jobs);

        const formattedDate = selectedDate.toISOString().split("T")[0];

        if (selectedTimes.length > 0) {
          const sortedTimes = [...selectedTimes].sort();

          let overallStartTime, overallEndTime;

          const firstTime = sortedTimes[0];
          const lastTime = sortedTimes[sortedTimes.length - 1];

          if (firstTime.includes("-")) {
            overallStartTime = firstTime.split("-")[0];
          } else {
            overallStartTime = firstTime;
          }

          if (lastTime.includes("-")) {
            overallEndTime = lastTime.split("-")[1];
          } else {
            overallEndTime = addMinutesToTime(lastTime, 10, selectedDate); // Changed from 30 to 10 minutes
          }

          // Create single slot with calculated times

          // Ensure time format includes seconds (HH:MM:SS)
          const formatTimeWithSeconds = (time) => {
            if (!time) return time;
            if (time.includes(':')) {
              const parts = time.split(':');
              if (parts.length === 2) {
                return `${time}:00`; // Add seconds if missing
              }
            }
            return time;
          };

          // Ensure question_count is a valid number
          const questionCount = slotForm.question_count 
            ? (typeof slotForm.question_count === 'number' 
                ? slotForm.question_count 
                : parseInt(slotForm.question_count, 10))
            : 10;
          
          // Validate question_count is between 1 and 20
          const validQuestionCount = (questionCount >= 1 && questionCount <= 20) 
            ? questionCount 
            : 10;

          const slotData = {
            interview_date: formattedDate,
            start_time: formatTimeWithSeconds(overallStartTime),
            end_time: formatTimeWithSeconds(overallEndTime),
            ai_interview_type: slotForm.ai_interview_type || "technical",
            ai_configuration: {
              difficulty_level: slotForm.difficulty_level || "intermediate",
              question_count: validQuestionCount,
              time_limit: parseInt(slotForm.time_limit) || 10, // Default to 10 minutes for 10-minute slots
              topics: slotForm.topics ? slotForm.topics.split(",").map((t) => t.trim()) : ["algorithms", "data_structures"],
            },
            max_candidates: parseInt(slotForm.max_candidates) || 1,
            status: slotForm.status || "available",
            job: selectedJobId || null,
            company: selectedCompanyId || null,
          };

          console.log('📊 Question Count being sent:', validQuestionCount);
          console.log('📊 Full ai_configuration:', slotData.ai_configuration);
          console.log('🚀 Sending slot data:', slotData);

          const response = await fetch(`${baseURL}/api/interviews/slots/`, {
            method: "POST",
            headers: {
              Authorization: `Token ${authToken}`,
              "Content-Type": "application/json",
            },
            body: JSON.stringify(slotData),
          });

          if (!response.ok) {
            const errorData = await response.json();
            console.error('❌ API Error Response:', errorData);
            console.error('❌ Response Status:', response.status);
            throw new Error(
              `Failed to create slot: ${JSON.stringify(errorData)}`
            );
          }

          await fetchSlots();
          // Force TimeSlotPicker to refresh by changing the key
          setRefreshKey(prev => prev + 1);
          // Also clear and reset selected times to trigger refresh
          setSelectedTimes([]);
          resetSlotForm();
          notify.success("Interview slot created successfully!");
        }
      } catch {
        notify.error("Failed to create slot");
      } finally {
        setIsSubmitting(false);
      }
    },
    [
      selectedTimes,
      selectedDate,
      slotForm,
      user,
      fetchSlots,
      resetSlotForm,
      addMinutesToTime,
      notify,
      companies,
      selectedCompanyId,
      selectedJobId,
      jobs,
    ]
  );


  const handleDeleteSlot = useCallback(
    async (slotId) => {
      if (!window.confirm("Are you sure you want to delete this slot?")) return;

      try {
        setIsSubmitting(true);
        const authToken = localStorage.getItem("authToken");
        if (!authToken) throw new Error("Authentication token not found");

        const response = await fetch(
          `${baseURL}/api/interviews/slots/${slotId}/`,
          {
            method: "DELETE",
            headers: { Authorization: `Token ${authToken}` },
          }
        );

        if (!response.ok) throw new Error("Failed to delete slot");

        await fetchSlots();
        notify.success("Interview slot deleted successfully!");
      } catch {
        notify.error("Failed to delete slot");
      } finally {
        setIsSubmitting(false);
      }
    },
    [fetchSlots, notify]
  );


  // New function for DataTable edit integration
  const handleUpdateSlotAPI = useCallback(
    async (editedData) => {
      try {
        const authToken = localStorage.getItem("authToken");
        if (!authToken) throw new Error("Authentication token not found");

        // Process the simplified data structure
        let processedData = { ...editedData };
        
        // Process edited data
        
        // Helper function to convert 12-hour to 24-hour format
        function convertTo24Hour(time12) {
          try {
            const timeParts = time12.match(/(\d{1,2}):(\d{2})\s*(AM|PM)/i);
            if (!timeParts) {
              return time12; // Return as-is if not 12-hour format
            }
            
            let hours = parseInt(timeParts[1]);
            const minutes = parseInt(timeParts[2]);
            const ampm = timeParts[3].toUpperCase();
            
            // Convert to 24-hour format
            if (ampm === 'AM' && hours === 12) {
              hours = 0;
            } else if (ampm === 'PM' && hours !== 12) {
              hours += 12;
            }
            
            // Format as HH:MM:SS for backend
            const hours24 = hours.toString().padStart(2, '0');
            const minutes24 = minutes.toString().padStart(2, '0');
            return `${hours24}:${minutes24}:00`;
          } catch {
            return time12; // Return original if conversion fails
          }
        }
        
        // Convert 12-hour format times to 24-hour format if needed
        if (processedData.start_time && processedData.start_time.includes('M')) {
          // This is 12-hour format, convert it
          processedData.start_time = convertTo24Hour(processedData.start_time);
        }
        
        if (processedData.end_time && processedData.end_time.includes('M')) {
          // This is 12-hour format, convert it
          processedData.end_time = convertTo24Hour(processedData.end_time);
        }
        
        // Validate times (now with 24-hour format)
        if (processedData.start_time && processedData.end_time) {
          try {
            // Parse time strings (format: "HH:MM:SS" or "HH:MM")
            const startParts = processedData.start_time.split(':');
            const endParts = processedData.end_time.split(':');
            
            const startHours = parseInt(startParts[0]);
            const startMinutes = parseInt(startParts[1]);
            const endHours = parseInt(endParts[0]);
            const endMinutes = parseInt(endParts[1]);
            
            // Create time objects for comparison
            const startTimeMinutes = startHours * 60 + startMinutes;
            const endTimeMinutes = endHours * 60 + endMinutes;
            
            if (startTimeMinutes >= endTimeMinutes) {
              throw new Error("End time must be after start time");
            }

            // Check business hours (8:00 AM - 10:00 PM)
            const businessStart = 8 * 60; // 8:00 AM in minutes
            const businessEnd = 22 * 60;  // 10:00 PM in minutes
            
            if (startTimeMinutes < businessStart || endTimeMinutes > businessEnd) {
              const startTime12 = new Date(2000, 0, 1, startHours, startMinutes).toLocaleTimeString([], {
                hour: 'numeric',
                minute: '2-digit',
                hour12: true
              });
              const endTime12 = new Date(2000, 0, 1, endHours, endMinutes).toLocaleTimeString([], {
                hour: 'numeric',
                minute: '2-digit',
                hour12: true
              });
              
              throw new Error(
                `Interview time (${startTime12} - ${endTime12}) must be between 8:00 AM and 10:00 PM.`
              );
            }
                 } catch {
            throw new Error('Invalid time format. Please use format like "9:30 AM" or "2:15 PM"');
          }
        }

        const slotData = {
          interview_date: processedData.interview_date,
          start_time: processedData.start_time,
          end_time: processedData.end_time,
          ai_interview_type: processedData.ai_interview_type,
          status: processedData.status,
          max_candidates: processedData.max_candidates,
          // Keep other fields from original data
          ai_configuration: processedData.ai_configuration,
          job: processedData.job,
          company: processedData.company,
          slot_type: processedData.slot_type,
          notes: processedData.notes,
          is_recurring: processedData.is_recurring,
          recurring_pattern: processedData.recurring_pattern,
        };
        
        // Send slot data to API

        const response = await fetch(
          `${baseURL}/api/interviews/slots/${editedData.id}/`,
          {
            method: "PATCH",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Token ${authToken}`,
            },
            body: JSON.stringify(slotData),
          }
        );

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          
          throw new Error(
            errorData.detail || errorData.message || JSON.stringify(errorData) || `HTTP error! status: ${response.status}`
          );
        }

        // Force refresh the data and UI
        await fetchSlots();
        setRefreshKey(prev => prev + 1); // Refresh TimeSlotPicker and DataTable
        
        // Add a small delay to ensure state updates are processed
        setTimeout(() => {
          // Data refresh completed
        }, 100);
      } catch {
        throw new Error('Failed to update slot'); // Re-throw so DataTable can handle the error
      }
    },
    [fetchSlots]
  );




  const formatTimeTo12Hour = useCallback((time24) => {
    if (!time24) return "";
    const [hours, minutes] = time24.split(":");
    const hour = parseInt(hours, 10);
    const ampm = hour >= 12 ? "PM" : "AM";
    const hour12 = hour % 12 || 12;
    return `${hour12}:${minutes} ${ampm}`;
  }, []);







  useEffect(() => {
    if (onTitleChange) {
              onTitleChange("Talaro Interview Manager");
    }
  }, [onTitleChange]);

  if (initialLoading) {
    return (
      <div className="ai-int-interview-scheduler-loading">
        <BeatLoader color="#4f46e5" />
        <p>Loading Management System...</p>
      </div>
    );
  }

  // Show error notification and continue with normal render
  if (slotsError && retryCount === 0 && !hasShownError) {
    notify.error(slotsError, "Failed to Load Slots");
    setHasShownError(true);
  }

  return (
    <div className="ai-interview-scheduler">
            {/* Mobile Toggle Button */}
            <div className="mobile-form-toggle">
              <button
                className={`mobile-create-slot-btn ${showMobileForm ? 'form-open' : ''}`}
                onClick={() => setShowMobileForm(!showMobileForm)}
              >
                <span className="btn-icon">{showMobileForm ? '×' : '+'}</span>
                <span className="btn-text">{showMobileForm ? 'Close' : 'Create New Slot'}</span>
              </button>
            </div>

      {/* Left Side - Form */}
      <div className={`ai-int-form-container slide-in-left ${showMobileForm ? 'mobile-form-visible' : 'mobile-form-hidden'}`}>
          <form className="ai-int-form" onSubmit={handleSlotSubmit}>
          <h3 className="ai-int-form-title">Interview Scheduler</h3>
            <div className="ai-int-form-group">
              <label>Date</label>
              <HorizontalDatePicker
                selectedDate={selectedDate}
                onSelectDate={handleDateSelect}
                isDateFullyBooked={() => false}
              />
            </div>

            <div className="ai-int-form-group">
              <label>Time Slots</label>
              {selectedDate && (
                <TimeSlotPicker
                  selectedTimes={selectedTimes}
                  onSelectTimes={handleTimeSelect}
                  selectedDate={selectedDate}
                  baseURL={baseURL}
                  isBooking={isSubmitting}
                  setIsBooking={setIsSubmitting}
                  aiInterviewType={slotForm.ai_interview_type}
                />
              )}
            </div>

            <div className="ai-int-form-group">
              <label>Interview Type</label>
              <CustomDropdown
                value={slotForm.ai_interview_type}
                options={[
                  { value: '', label: 'Select interview type' },
                  { value: 'technical', label: 'Technical' },
                  { value: 'behavioral', label: 'Behavioral' },
                  { value: 'system-design', label: 'System Design' }
                ]}
                onChange={(value) =>
                  setSlotForm((prev) => ({
                    ...prev,
                    ai_interview_type: value,
                  }))
                }
                placeholder="Select interview type"
              />
            </div>

            <div className="ai-int-form-group">
              <label>Difficulty Level</label>
              <CustomDropdown
                value={slotForm.difficulty_level}
                options={[
                  { value: '', label: 'Select difficulty level' },
                  { value: 'easy', label: 'Easy' },
                  { value: 'intermediate', label: 'Intermediate' },
                  { value: 'hard', label: 'Hard' }
                ]}
                onChange={(value) =>
                  setSlotForm((prev) => ({
                    ...prev,
                    difficulty_level: value,
                  }))
                }
                placeholder="Select difficulty level"
              />
            </div>

            <div className="ai-int-form-group">
              <label>Question Count</label>
              <input
                type="number"
                min="1"
                max="20"
                value={slotForm.question_count}
                placeholder="Enter number of questions (1-20)"
                onChange={(e) => {
                  const value = e.target.value;
                  // Allow empty string while typing, but convert to number when valid
                  if (value === '') {
                    setSlotForm((prev) => ({
                      ...prev,
                      question_count: '',
                    }));
                  } else {
                    const numValue = parseInt(value, 10);
                    if (!isNaN(numValue) && numValue >= 1 && numValue <= 20) {
                      setSlotForm((prev) => ({
                        ...prev,
                        question_count: numValue,
                      }));
                    }
                  }
                }}
                onBlur={(e) => {
                  // Ensure we have a valid value when field loses focus
                  const value = e.target.value;
                  if (value === '' || isNaN(parseInt(value, 10)) || parseInt(value, 10) < 1) {
                    setSlotForm((prev) => ({
                      ...prev,
                      question_count: 10, // Default to 10 if invalid
                    }));
                  }
                }}
              />
            </div>

            <div className="ai-int-form-group">
              <label>Topics (comma separated)</label>
              <input
                type="text"
                value={slotForm.topics}
                onChange={(e) =>
                  setSlotForm((prev) => ({ ...prev, topics: e.target.value }))
                }
                placeholder="e.g., algorithms, data structures, system design"
              />
            </div>

            <div className="ai-int-form-group">
              <label>Max Candidates</label>
              <input
                type="number"
                min="1"
                value={slotForm.max_candidates}
                placeholder="Enter maximum number of candidates"
                onChange={(e) =>
                  setSlotForm((prev) => ({
                    ...prev,
                    max_candidates: parseInt(e.target.value) || 0,
                  }))
                }
              />
            </div>

            {/* Company Selection - Only show for admin users */}
            {user?.role?.toLowerCase() === 'admin' && (
              <div className="ai-int-form-group">
                <label>Company</label>
                <CustomDropdown
                  value={selectedCompanyId ? String(selectedCompanyId) : ''}
                  options={[
                    { value: '', label: 'Select a company' },
                    ...companies.map(company => ({
                      value: String(company.id),
                      label: company.name || company.company_name || `Company ${company.id}`
                    }))
                  ]}
                  onChange={(value) => setSelectedCompanyId(value ? parseInt(value) : null)}
                  placeholder="Select a company"
                  disabled={companiesLoading}
                  searchable={true}
                  openAbove={true}
                />
                {companiesLoading && <small>Loading companies...</small>}
              </div>
            )}

            {/* Job Selection - Show for all users */}
            <div className="ai-int-form-group">
              <label>Job</label>
              <CustomDropdown
                value={selectedJobId ? String(selectedJobId) : ''}
                options={[
                  { value: '', label: 'Select a job' },
                  ...jobs.map(job => ({
                    value: String(job.id),
                    label: job.title || job.job_title || `Job ${job.id}`
                  }))
                ]}
                onChange={(value) => setSelectedJobId(value ? parseInt(value) : null)}
                placeholder="Select a job"
                disabled={jobsLoading || (user?.role?.toLowerCase() === 'admin' && !selectedCompanyId)}
                searchable={true}
                openAbove={true}
              />
              {jobsLoading && <small>Loading jobs...</small>}
              {user?.role?.toLowerCase() === 'admin' && !selectedCompanyId && (
                <small style={{color: 'var(--color-muted)'}}>Please select a company first</small>
              )}
            </div>

            <div className="ai-int-form-actions">
              <button
                type="submit"
                className="ai-int-btn ai-int-btn-primary"
                disabled={isSubmitting || slotsLoading}
              >
                {isSubmitting ? (
                  <BeatLoader size={8} color="#fff" />
                ) : editingSlot ? (
                  "Update Slot"
                ) : (
                  "Create Slot"
                )}
              </button>
              {editingSlot && (
                <button
                  type="button"
                  className="ai-int-btn ai-int-btn-secondary"
                  onClick={() => {
                    setEditingSlot(null);
                    resetSlotForm();
                  }}
                >
                  Cancel
                </button>
              )}
            </div>
          </form>
      </div>

      {/* Interview Slots Table */}
      <div className="ai-int-table-container slide-in-right">
        <DataTable
          key={`slots-table-${refreshKey}`}
          title="Interview Slots"
          columns={[
            {
              field: "interview_date",
              header: "Date",
              width: "8%",
              type: "date",
              editable: true,
              render: (value) => {
                if (!value) return 'N/A';
                return new Date(value).toLocaleDateString();
              },
            },
            {
              field: "start_time",
              header: "Start Time",
              width: "9%",
              type: "time12",
              editable: true,
              render: (value) => {
                if (!value || typeof value !== 'string') {
                  return 'N/A';
                }
                return formatTimeTo12Hour(value);
              },
              formatForEdit: (value) => {
                if (!value || typeof value !== 'string') {
                  return '';
                }
                return formatTimeTo12Hour(value);
              },
                       parseFromEdit: (editValue) => {
                if (!editValue) return '';
                const time24 = formatTimeTo24Hour(editValue);
                return time24;
              }
            },
            {
              field: "end_time", 
              header: "End Time",
              width: "9%",
              type: "time12",
              editable: true,
              render: (value) => {
                if (!value || typeof value !== 'string') {
                  return 'N/A';
                }
                return formatTimeTo12Hour(value);
              },
              formatForEdit: (value) => {
                if (!value || typeof value !== 'string') {
                  return '';
                }
                return formatTimeTo12Hour(value);
              },
                       parseFromEdit: (editValue) => {
                if (!editValue) return '';
                const time24 = formatTimeTo24Hour(editValue);
                return time24;
              }
            },
            {
              field: "ai_interview_type",
              header: "Type",
              width: "18%",
              type: "select",
              editable: true,
              options: [
                { value: "technical", label: "Technical Interview" },
                { value: "behavioral", label: "Behavioral Interview" },
                { value: "coding", label: "Coding Interview" },
                { value: "system_design", label: "System Design Interview" },
                { value: "general", label: "General Interview" },
              ],
            },
            {
              field: "status",
              header: "Status",
              width: "15%",
              type: "select",
              editable: true,
              options: [
                { value: "available", label: "Available" },
                { value: "booked", label: "Booked" },
                { value: "cancelled", label: "Cancelled" },
                { value: "completed", label: "Completed" },
              ],
              render: (value) => (
                <span className="status-cell" data-status={value?.toLowerCase()}>
                  {value}
                </span>
              ),
            },
            {
              field: "max_candidates",
              header: "Max",
              width: "8%",
              type: "number",
              editable: true,
              render: (value) => value || 1,
            },
            {
              field: "job_title",
              header: "Job",
              width: "8%",
              editable: false,
            },
            {
              field: "created_at",
              header: "Created",
              width: "8%",
              editable: false,
              render: (value) => {
                if (!value) return 'N/A';
                return new Date(value).toLocaleDateString();
              },
            },
            {
              field: "updated_at",
              header: "Updated",
              width: "8%",
              editable: false,
              render: (value) => {
                if (!value) return 'N/A';
                return new Date(value).toLocaleDateString();
              },
            },
          ]}
          data={sortedSlots}
          loading={slotsLoading}
          actions={["edit", "delete"]}
                 onAction={(action, rowData) => {
            if (action === "edit") {
              return;
            } else if (action === "delete") {
              handleDeleteSlot(rowData.id);
            }
          }}
          onContextMenuClick={handleContextMenuClick}
          onEdit={async (editedData) => {
            await handleUpdateSlotAPI(editedData);
          }}
          editingRow={editingRow}
          editingData={editingData}
          setEditingRow={setEditingRow}
          setEditingData={setEditingData}
          showRefresh={true}
          onRefresh={async () => {
            try {
              await fetchSlots(true);
              setRefreshKey(prev => prev + 1);
                   } catch {
              notify.error("Failed to refresh interview slots. Please try again.");
            }
          }}
          showActions={true}
          defaultPageSize={10}
          pageSizeOptions={[10, 20, 50, 100]}
        />

        {/* Context Menu */}
        <ContextMenu
          visible={contextMenu.visible}
          x={contextMenu.x}
          y={contextMenu.y}
          actions={["edit", "delete"]}
          onAction={handleContextMenuAction}
          onClose={handleContextMenuClose}
          rowData={contextMenu.rowData}
          rowIndex={contextMenu.rowIndex}
        />
      </div>

    </div>
  );
};

export default AiInterviewScheduler;
