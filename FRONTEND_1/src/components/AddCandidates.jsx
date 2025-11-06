import React, { useState, useRef, useEffect, useMemo, useCallback } from "react";
import axios from "axios";
import { useSelector, useDispatch } from "react-redux";
import "./AddCandidates.css";
import { baseURL } from "../data";
import { FiTrash2, FiEdit2 } from "react-icons/fi";
import { useNavigate } from "react-router-dom";
import { fetchJobs, fetchDomains } from '../redux/slices/jobsSlice';
import Modal, { ConfirmModal } from './common/Modal';
import { useNotification } from '../hooks/useNotification';
import CustomDropdown from './common/CustomDropdown';

const AddCandidates = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const notify = useNotification();
  const loggedInUser = useSelector((state) => state.user.user);
  const userRole = loggedInUser?.role;
  const userEmail = loggedInUser?.email;

  // Get jobs and domains from Redux store
  const allJobs = useSelector((state) => state.jobs.allJobs || []);
  const domains = useSelector((state) => state.jobs.domains || []);
  const jobsStatus = useSelector((state) => state.jobs.jobsStatus);
  const domainsStatus = useSelector((state) => state.jobs.domainsStatus);

  // Fetch jobs and domains on component mount if not already loaded
  useEffect(() => {
    if (jobsStatus === 'idle') {
      dispatch(fetchJobs());
    }
    if (domainsStatus === 'idle') {
      dispatch(fetchDomains());
    }
  }, [jobsStatus, domainsStatus, dispatch]);


  const [formData, setFormData] = useState({
    domain: "", // This will be the domain ID from the dropdown
    job_title: "", // This will be the job ID from the dropdown
    poc_email: userRole === 'RECRUITER' || userRole === 'HIRING_AGENCY' ? userEmail : "",
    resumes: [],
  });


  const fileInputRef = useRef(null);

  // State for parsed resume data from the 'extract' step
  const [parsedResumeData, setParsedResumeData] = useState([]);
  const [isUploading, setIsUploading] = useState(false); // For the 'extract' step
  const [isSubmittingCandidates, setIsSubmittingCandidates] = useState(false); // For the 'submit' step

  // Use a temporary ID for client-side editing of parsed data
  const [editingCandidateTempId, setEditingCandidateTempId] = useState(null);
  const [editedCandidateData, setEditedCandidateData] = useState(null);

  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteTempId, setDeleteTempId] = useState(null); // Use temp ID for delete
  const [showDeleteModalOverlay, setShowDeleteModalOverlay] = useState(false);

  // Memoized extraction summary calculation
  const extractionSummary = useMemo(() => {
    const total = parsedResumeData.length;
    const successful = parsedResumeData.filter(candidate => 
      candidate.extracted_data && 
      candidate.extracted_data.name && 
      candidate.extracted_data.email
    ).length;
    const failed = total - successful;
    
    return {
      total_files: total,
      successful_extractions: successful,
      failed_extractions: failed,
    };
  }, [parsedResumeData]);

  // NEW: State for success modal
  const [showSuccessModal, setShowSuccessModal] = useState(false);

  // State for mobile view and expand functionality
  const [isMobileView, setIsMobileView] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [selectedCard, setSelectedCard] = useState(null); // null, 'files', 'successful', 'failed', 'add'

  // Effect to detect mobile screen size
  useEffect(() => {
    const checkMobileView = () => {
      setIsMobileView(window.innerWidth <= 768);
    };
    
    checkMobileView();
    window.addEventListener('resize', checkMobileView);
    
    return () => window.removeEventListener('resize', checkMobileView);
  }, []);

  // Memoized filtered jobs based on selected domain
  const filteredJobsByDomain = useMemo(() => {
    if (formData.domain && allJobs.length > 0) {
      const selectedDomainId = parseInt(formData.domain, 10);
      return allJobs.filter(job => job.domain === selectedDomainId);
    }
    return [];
  }, [formData.domain, allJobs]);

  // Effect to reset job title when domain changes
  useEffect(() => {
    setFormData(prev => ({ ...prev, job_title: "" }));
  }, [formData.domain]);


  const handleChange = useCallback((e) => {
    const { name, value } = e.target;
    console.log('handleChange called with:', { name, value, type: typeof value });
    setFormData((prev) => ({ ...prev, [name]: value }));
  }, []);

  // Specific handlers for dropdowns
  const handleDomainChange = useCallback((value) => {
    setFormData((prev) => ({ ...prev, domain: value }));
  }, []);

  const handleJobTitleChange = useCallback((value) => {
    setFormData((prev) => ({ ...prev, job_title: value }));
  }, []);

  const handleResumeChange = useCallback((e) => {
    const files = Array.from(e.target.files).slice(0, 10); // Changed to 10 files max
    setFormData((prev) => ({ ...prev, resumes: files }));
  }, []);

  const validateForm = () => {
    if (!formData.domain) {
      notify.error("Domain is required");
      return false;
    }
    // New validation: Check if selected domain ID exists in the domains list
    const selectedDomainExists = domains.some(d => d.id === parseInt(formData.domain, 10));
    if (!selectedDomainExists) {
      notify.error("Selected domain is invalid or no longer exists.");
      return false;
    }

    if (!formData.job_title) {
      notify.error("Job title is required");
      return false;
    }
    // New validation: Check if selected job title ID exists in the filteredJobsByDomain list
    const selectedJobExists = filteredJobsByDomain.some(job => job.id === parseInt(formData.job_title, 10));
    if (!selectedJobExists) {
      notify.error("Selected job title is invalid or no longer exists for the chosen domain.");
      return false;
    }

    if (!formData.poc_email) {
      notify.error("POC email is required");
      return false;
    }
    if (!/^\S+@\S+\.\S+$/.test(formData.poc_email)) {
      notify.error("Please enter a valid POC email");
      return false;
    }
    if (formData.resumes.length === 0) {
      notify.error("At least one resume is required");
      return false;
    }
    return true;
  };

  // Function to handle bulk resume upload and extraction
  const handleBulkResumeUpload = async (e) => {
    e.preventDefault();
    setShowSuccessModal(false); // Clear any previous success modal

    if (!validateForm()) return;

    const authToken = localStorage.getItem('authToken');
    if (!authToken) {
      notify.error("Please log in to upload resumes.");
      navigate('/login');
      return;
    }

    setIsUploading(true);

    const uploadPayload = new FormData();
    // Get domain name from ID
    const selectedDomainName = domains.find(d => d.id === parseInt(formData.domain, 10))?.name;
    // Get job title from ID
    const selectedJobTitle = allJobs.find(job => job.id === parseInt(formData.job_title, 10))?.job_title;

    uploadPayload.append("domain", selectedDomainName); // Send domain name
    uploadPayload.append("role", selectedJobTitle); // Send job title (role)

    formData.resumes.forEach((file) => {
      uploadPayload.append("resume_files", file);
    });

    try {
      const response = await axios.post(
        `${baseURL}/api/candidates/bulk-create/?step=extract`, // New API endpoint
        uploadPayload,
        {
          headers: {
            Authorization: `Token ${authToken}`,
            "Content-Type": "multipart/form-data",
          },
        }
      );

      // Set parsed resume data and extraction summary
      // Add a temporary unique ID to each parsed candidate for client-side operations
      const parsedDataWithTempId = (response.data.extracted_candidates || []).map(candidate => ({
        ...candidate,
        tempId: crypto.randomUUID() // Generate a unique ID for client-side use
      }));
      setParsedResumeData(parsedDataWithTempId);

      notify.success("Resumes uploaded and parsed successfully! Review the extracted data below.");
    } catch (error) {
      notify.error(error.response?.data?.message || "Failed to upload and parse resumes. Please try again.");
      if (error.response?.status === 401) {
        navigate('/login');
      }
    } finally {
      setIsUploading(false);
    }
  };

  // Function to handle submitting candidates from parsed data
  const handleSubmitCandidates = async () => {
    if (parsedResumeData.length === 0) {
      notify.error("No candidate data to submit");
      return;
    }

    const authToken = localStorage.getItem('authToken');
    if (!authToken) {
      notify.error("Please log in to submit candidates.");
      navigate('/login');
      return;
    }

    setIsSubmittingCandidates(true);
    setShowSuccessModal(false); // Clear any previous success modal

    // Get domain name from ID
    const selectedDomainName = domains.find(d => d.id === parseInt(formData.domain, 10))?.name;
    // Get job title from ID
    const selectedJobTitle = allJobs.find(job => job.id === parseInt(formData.job_title, 10))?.job_title;


    // No threshold filtering: include all parsed candidates
    const eligibleCandidates = parsedResumeData;

    const candidatesToSubmit = eligibleCandidates.map(candidate => ({
      filename: candidate.filename,
      edited_data: {
        // Use the keys expected by the API as per your example payload
        name: candidate.extracted_data.name || "",
        email: candidate.extracted_data.email || "",
        phone: candidate.extracted_data.phone || "",
        work_experience: candidate.extracted_data.work_experience || 0,
        // Include other fields if they are part of the API's expected edited_data structure
        current_company: candidate.extracted_data.current_company || "",
        current_role: candidate.extracted_data.current_role || "",
        expected_salary: candidate.extracted_data.expected_salary || 0,
        notice_period: candidate.extracted_data.notice_period || 0,
      }
    }));

    const submissionPayload = {
      domain: selectedDomainName, // Send domain name
      role: selectedJobTitle, // Send job title (role)
      poc_email: formData.poc_email,
      candidates: candidatesToSubmit,
    };

    try {
      const response = await axios.post(
        `${baseURL}/api/candidates/bulk-create/?step=submit`, // New API endpoint
        submissionPayload,
        {
          headers: {
            Authorization: `Token ${authToken}`,
            "Content-Type": "application/json",
          },
        }
      );

      // Candidates submitted successfully

      // Display success message if any candidates were successfully created
      if (response.data.summary.successful_creations > 0) {
        notify.success("Candidates added successfully!");
        setShowSuccessModal(true); // Show the new success modal
        // Clear parsed data after successful submission
        setParsedResumeData([]);
        // Reset form fields
        setFormData({
          domain: "",
          job_title: "",
          poc_email: userRole === 'RECRUITER' || userRole === 'HIRING_AGENCY' ? userEmail : "",
          resumes: [],
        });
        if (fileInputRef.current) fileInputRef.current.value = "";
      } else {
        notify.error(response.data.message || "No candidates were successfully added.");
      }

      // No need for setTimeout here, modal will be closed by user
    } catch (error) {
      notify.error(error.response?.data?.message || "Failed to submit candidates. Please try again.");
      if (error.response?.status === 401) {
        navigate('/login');
      }
    } finally {
      setIsSubmittingCandidates(false);
    }
  };

  // NEW: Function to close the success modal
  const closeSuccessModal = () => {
    setShowSuccessModal(false);
  };

  // Modified handleDeleteClick to work with parsedResumeData (client-side)
  const handleDeleteClick = async (tempId) => {
    setDeleteTempId(tempId);
    setShowDeleteModalOverlay(true);
    setShowDeleteConfirm(true);
  };

  // Modified confirmDelete to work with parsedResumeData (client-side)
  const confirmDelete = () => {
    if (!deleteTempId) return;

    setParsedResumeData(prev => prev.filter(c => c.tempId !== deleteTempId));
    setShowDeleteModalOverlay(false);
    setShowDeleteConfirm(false);
    setDeleteTempId(null);
  };

  const cancelDelete = () => {
    setShowDeleteModalOverlay(false);
    setShowDeleteConfirm(false);
    setDeleteTempId(null);
  };

  // Modified handleEditClick to work with parsedResumeData (client-side)
  const handleEditClick = useCallback((candidate) => {
    setEditingCandidateTempId(candidate.tempId);
    // Ensure all fields are present in editedCandidateData, even if empty
    setEditedCandidateData({
      ...candidate.extracted_data, // Edit the extracted_data part
      filename: candidate.filename, // Keep filename for reference
      tempId: candidate.tempId // Keep tempId for identification
    });
  }, []);

  // Modified handleEditCellChange to update editedCandidateData
  const handleEditCellChange = useCallback((e, field) => {
    const newValue = e.target.value;
    setEditedCandidateData(prev => ({
      ...prev,
      [field]: newValue
    }));
  }, []);

  // Modified handleSaveClick to update parsedResumeData (client-side)
  const handleSaveClick = useCallback(() => {
    if (!editedCandidateData || !editingCandidateTempId) return;

    setParsedResumeData(prev =>
      prev.map(c =>
        c.tempId === editingCandidateTempId
          ? {
              ...c,
              extracted_data: {
                name: editedCandidateData.name,
                email: editedCandidateData.email,
                phone: editedCandidateData.phone,
                work_experience: editedCandidateData.work_experience,
                current_company: editedCandidateData.current_company,
                current_role: editedCandidateData.current_role,
                expected_salary: editedCandidateData.expected_salary,
                notice_period: editedCandidateData.notice_period,
              }
            }
          : c
      )
    );
    setEditingCandidateTempId(null);
    setEditedCandidateData(null);
  }, [editedCandidateData, editingCandidateTempId]);

  const handleCancelEdit = useCallback(() => {
    setEditingCandidateTempId(null);
    setEditedCandidateData(null);
  }, []);

  // Memoized helper functions
  const getDomainName = useCallback((domainId) => {
    const domain = domains.find(d => d.id === domainId);
    return domain ? domain.name : `Domain ${domainId}`;
  }, [domains]);

  const getJobTitle = useCallback((jobId) => {
    const job = allJobs.find(j => j.id === jobId);
    return job ? job.job_title : `Job ${jobId}`;
  }, [allJobs]);


  // Function to handle card/button clicks on mobile
  const handleCardClick = (cardType) => {
    if (selectedCard === cardType) {
      // If same card clicked, collapse
      setSelectedCard(null);
      setIsExpanded(false);
    } else {
      // If different card clicked, select it
      setSelectedCard(cardType);
      // Only set expanded to true for Add Candidate button
      setIsExpanded(cardType === 'add');
    }
  };

  // Check if any modal is open for blur effect
  const isAnyModalOpen = showSuccessModal || showDeleteModalOverlay || showDeleteConfirm;

  return (
    <>
      <div className={`add-candidates-container ${isAnyModalOpen ? 'blur-background' : ''}`}>
      <div className="add-candidates-top-section">
        {isMobileView ? (
          <>
            <div className="mobile-cards-container">
              <div className="mobile-cards-row">
                <div className="mobile-cards-icons">
                  {selectedCard === 'files' ? (
                    <div className="mobile-selected-icon">
                      <div className="icon-wrapper">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M14 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V8L14 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          <path d="M14 2V8H20" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      </div>
                      <div className="selected-content">
                        <span className="selected-title">Total Files</span>
                        <span className="selected-number">{extractionSummary.total_files}</span>
                      </div>
                      <button className="mobile-close-btn" onClick={() => handleCardClick('files')}>
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M18 6L6 18M6 6L18 18" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      </button>
                    </div>
                  ) : selectedCard === 'successful' ? (
                    <div className="mobile-selected-icon">
                      <div className="icon-wrapper">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M9 12L11 14L15 10M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      </div>
                      <div className="selected-content">
                        <span className="selected-title">Successful Extractions</span>
                        <span className="selected-number">{extractionSummary.successful_extractions}</span>
                      </div>
                      <button className="mobile-close-btn" onClick={() => handleCardClick('successful')}>
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M18 6L6 18M6 6L18 18" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      </button>
                    </div>
                  ) : selectedCard === 'failed' ? (
                    <div className="mobile-selected-icon">
                      <div className="icon-wrapper">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M12 9V13M12 17H12.01M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      </div>
                      <div className="selected-content">
                        <span className="selected-title">Failed Extractions</span>
                        <span className="selected-number">{extractionSummary.failed_extractions}</span>
                      </div>
                      <button className="mobile-close-btn" onClick={() => handleCardClick('failed')}>
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M18 6L6 18M6 6L18 18" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      </button>
                    </div>
                  ) : (
                    <>
                      <div className={`mobile-card-icon ${selectedCard === 'files' ? 'selected' : ''}`} onClick={() => handleCardClick('files')}>
                        <div className="icon-wrapper">
                          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M14 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V8L14 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                            <path d="M14 2V8H20" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          </svg>
                        </div>
                        <span className="icon-number">{extractionSummary.total_files}</span>
                      </div>
                      <div className={`mobile-card-icon ${selectedCard === 'successful' ? 'selected' : ''}`} onClick={() => handleCardClick('successful')}>
                        <div className="icon-wrapper">
                          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M9 12L11 14L15 10M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          </svg>
                        </div>
                        <span className="icon-number">{extractionSummary.successful_extractions}</span>
                      </div>
                      <div className={`mobile-card-icon ${selectedCard === 'failed' ? 'selected' : ''}`} onClick={() => handleCardClick('failed')}>
                        <div className="icon-wrapper">
                          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M12 9V13M12 17H12.01M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          </svg>
                        </div>
                        <span className="icon-number">{extractionSummary.failed_extractions}</span>
                      </div>
                    </>
                  )}
                </div>
              </div>
              <button className={`mobile-add-candidate-btn ${selectedCard === 'add' ? 'selected' : ''}`} onClick={() => handleCardClick('add')}>
                <span className="btn-icon">{selectedCard === 'add' ? '×' : '+'}</span>
                <span className="btn-text">{selectedCard === 'add' ? 'Close' : 'Add Candidate'}</span>
              </button>
            </div>
            
            {/* Show Add Candidate form below when Add Candidate button is selected */}
            {selectedCard === 'add' && (
              <div className="mobile-selected-card">
                <div className="add-candidates-form card">
                  <h2 className="form-title">Add New Candidate</h2>
                  <form id="candidateForm" onSubmit={handleBulkResumeUpload}>
                    <div className="form-box">
                      <div className="form-group">
                        <label htmlFor="domainSelect">Domain <span className="required-field">*</span></label>
                        <CustomDropdown
                          value={formData.domain || ''}
                          options={[
                            { value: '', label: 'Select Domain' },
                            ...domains.map(domain => ({ value: String(domain.id), label: domain.name }))
                          ]}
                          onChange={handleDomainChange}
                          placeholder="Select Domain"
                          disabled={domainsStatus === 'loading'}
                        />
                      </div>

                      <div className="form-group">
                        <label htmlFor="jobTitleSelect">Job Title <span className="required-field">*</span></label>
                        <CustomDropdown
                          value={formData.job_title || ''}
                          options={[
                            { value: '', label: 'Select Job Title' },
                            ...filteredJobsByDomain.map(job => ({ value: String(job.id), label: `${job.job_title} (${job.company_name})` }))
                          ]}
                          onChange={handleJobTitleChange}
                          placeholder="Select Job Title"
                          disabled={!formData.domain || jobsStatus === 'loading'}
                        />
                        {/* Debug info */}
                        <div style={{fontSize: '12px', color: '#666', marginTop: '4px'}}>
                          DEBUG: formData.job_title = "{formData.job_title}" (type: {typeof formData.job_title})
                        </div>
                      </div>

                      <div className="form-group">
                        <label htmlFor="pocEmail">POC Email <span className="required-field">*</span></label>
                        <input
                          type="email"
                          id="pocEmail"
                          name="poc_email"
                          placeholder="Point of contact email"
                          value={formData.poc_email}
                          onChange={handleChange}
                          className="add-candidates-input"
                          required
                          readOnly={userRole === 'RECRUITER' || userRole === 'HIRING_AGENCY'}
                        />
                      </div>

                      <div className="form-group resume-upload">
                        <label htmlFor="resumeUploadInput" className="resume-upload-label">
                          <p className="resume-upload-text">Upload Resumes (Max 10) <span className="required-field">*</span></p>
                          <div className="upload-icon-container">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                              <path d="M14 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V8L14 2Z"
                                stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                              <path d="M14 2V8H20" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                              <path d="M12 13V17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                              <path d="M10 15H14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                            </svg>
                          </div>
                          {formData.resumes.length > 0 ? (
                            <p className="selected-files-text resume-upload-text">
                              Selected: {formData.resumes.map((file) => file.name).join(", ")}
                            </p>
                          ) : (
                            <p className="selected-files-text resume-upload-text">No files selected</p>
                          )}
                        </label>
                        <input
                          type="file"
                          id="resumeUploadInput"
                          accept=".pdf,.doc,.docx"
                          multiple
                          ref={fileInputRef}
                          onChange={handleResumeChange}
                          style={{ display: "none" }}
                          required
                        />
                      </div>
                    </div>
                    <div className="form-actions">
                      <button
                        className="submit-btn"
                        type="submit"
                        disabled={isUploading}
                      >
                        {isUploading ? 'Uploading & Parsing...' : 'Upload & Parse Resumes'}
                      </button>
                    </div>
                  </form>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="add-candidates-header-cards">
            <div className="add-candidates-card">
              <h3>Total Files</h3>
              <p>{extractionSummary.total_files}</p>
            </div>
            <div className="add-candidates-card">
              <h3>Successful Extractions</h3>
              <p>{extractionSummary.successful_extractions}</p>
            </div>
            <div className="add-candidates-card">
              <h3>Failed Extractions</h3>
              <p>{extractionSummary.failed_extractions}</p>
            </div>
          </div>
        )}
      </div>

      <div className={`add-candidates-main-content fixed-grid ${isMobileView && !isExpanded ? 'mobile-collapsed' : ''}`}>
        <div className="add-candidates-form card slide-in-left">
          <h2 className="form-title">Add New Candidate</h2>
          <form 
            id="candidateForm" 
            onSubmit={handleBulkResumeUpload}
            role="form"
            aria-label="Add new candidate form"
          >
            <div className="form-box">
              <div className="form-group">
                <label htmlFor="domainSelect">
                  Domain <span className="required-field" aria-label="required">*</span>
                </label>
                <CustomDropdown
                  value={formData.domain || ''}
                  options={[
                    { value: '', label: 'Select Domain' },
                    ...domains.map(domain => ({ value: String(domain.id), label: domain.name }))
                  ]}
                  onChange={handleDomainChange}
                  placeholder="Select Domain"
                  disabled={domainsStatus === 'loading'}
                />
              </div>

              <div className="form-group">
                <label htmlFor="jobTitleSelect">
                  Job Title <span className="required-field" aria-label="required">*</span>
                </label>
                        <CustomDropdown
                          value={formData.job_title || ''}
                          options={[
                            { value: '', label: 'Select Job Title' },
                            ...filteredJobsByDomain.map(job => ({ value: String(job.id), label: `${job.job_title} (${job.company_name})` }))
                          ]}
                          onChange={handleJobTitleChange}
                          placeholder="Select Job Title"
                          disabled={!formData.domain || jobsStatus === 'loading'}
                        />
              </div>

              <div className="form-group">
                <label htmlFor="pocEmail">
                  POC Email <span className="required-field" aria-label="required">*</span>
                </label>
                <input
                  type="email"
                  id="pocEmail"
                  name="poc_email"
                  placeholder="Point of contact email"
                  value={formData.poc_email}
                  onChange={handleChange}
                  className="add-candidates-input"
                  required
                  readOnly={userRole === 'RECRUITER' || userRole === 'HIRING_AGENCY'}
                  aria-label="Point of contact email address"
                />
              </div>

              <div className="form-group resume-upload">
                <label htmlFor="resumeUploadInput" className="resume-upload-label">
                  <p className="resume-upload-text">
                    Upload Resumes (Max 10) <span className="required-field" aria-label="required">*</span>
                  </p>
                  <div className="upload-icon-container" aria-hidden="true">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M14 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V8L14 2Z"
                        stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M14 2V8H20" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M12 13V17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M10 15H14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </div>
                  {formData.resumes.length > 0 ? (
                    <p className="selected-files-text resume-upload-text" aria-live="polite">
                      Selected: {formData.resumes.map((file) => file.name).join(", ")}
                    </p>
                  ) : (
                    <p className="selected-files-text resume-upload-text">No files selected</p>
                  )}
                </label>
                <input
                  type="file"
                  id="resumeUploadInput"
                  accept=".pdf,.doc,.docx"
                  multiple
                  ref={fileInputRef}
                  onChange={handleResumeChange}
                  style={{ display: "none" }}
                  required
                  aria-label="Upload resume files (PDF, DOC, DOCX format, maximum 10 files)"
                />
              </div>

            </div>
            <div className="form-actions">
              <button
                className="submit-btn"
                type="submit"
                disabled={isUploading}
                aria-label={isUploading ? 'Uploading and parsing resumes, please wait' : 'Upload and parse resume files'}
              >
                {isUploading ? 'Uploading & Parsing...' : 'Upload & Parse Resumes'}
              </button>
            </div>
          </form>
        </div>

        {/* Parsed Resume Data Table - Always visible */}
        <div className="preview-section card slide-in-right">
          <div className="table-header-with-button">
            <h2 className="table-title">Parsed Resume Data</h2>
          </div>
          <div className="table-box">
            {/* Removed the inline success message div here */}
            <table className="candidate-table" role="table" aria-label="Parsed resume data table">
              <thead>
                <tr>
                  <th scope="col">Filename</th>
                  <th scope="col">Name</th>
                  <th scope="col">Email</th>
                  <th scope="col">Phone</th>
                  <th scope="col">Experience (Years)</th>
                  <th scope="col">Domain</th>
                  <th scope="col">Job Role</th>
                  <th scope="col">Match %</th>
                  <th scope="col">Actions</th>
                </tr>
              </thead>
              <tbody>
                {parsedResumeData.length > 0 ? (
                  parsedResumeData.map((candidate) => (
                    <tr 
                      key={candidate.tempId}
                      className={"candidate-row"}
                    >
                      <td>{candidate.filename || '-'}</td>
                      <td>
                        {editingCandidateTempId === candidate.tempId ? (
                          <input
                            type="text"
                            value={editedCandidateData?.name || ''}
                            onChange={(e) => handleEditCellChange(e, 'name')}
                            className="add-candidates-input-inline"
                          />
                        ) : (
                          candidate.extracted_data.name || '-'
                        )}
                      </td>
                      <td>
                        {editingCandidateTempId === candidate.tempId ? (
                          <input
                            type="email"
                            value={editedCandidateData?.email || ''}
                            onChange={(e) => handleEditCellChange(e, 'email')}
                            className="add-candidates-input-inline"
                          />
                        ) : (
                          candidate.extracted_data.email || '-'
                        )}
                      </td>
                      <td>
                        {editingCandidateTempId === candidate.tempId ? (
                          <input
                            type="tel"
                            value={editedCandidateData?.phone || ''}
                            onChange={(e) => handleEditCellChange(e, 'phone')}
                            className="add-candidates-input-inline"
                          />
                        ) : (
                          candidate.extracted_data.phone || '-'
                        )}
                      </td>
                      <td>
                        {editingCandidateTempId === candidate.tempId ? (
                          <input
                            type="number"
                            value={editedCandidateData?.work_experience || ''}
                            onChange={(e) => handleEditCellChange(e, 'work_experience')}
                            className="add-candidates-input-inline"
                          />
                        ) : (
                          candidate.extracted_data.work_experience || '-'
                        )}
                      </td>
                      {/* Display Domain from formData, not editable */}
                      <td>{getDomainName(parseInt(formData.domain, 10)) || '-'}</td>
                      {/* Display Job Role from formData, not editable */}
                      <td>{getJobTitle(parseInt(formData.job_title, 10)) || '-'}</td>
                      {/* Display Matching Percentage */}
                      <td>
                        {candidate.extracted_data.job_matching ? (
                          <div className="match-percentage">
                            <span 
                              className={"match-score"}
                              title={`Overall: ${candidate.extracted_data.job_matching.overall_match}%
Skills: ${candidate.extracted_data.job_matching.skill_match}%
Text Similarity: ${candidate.extracted_data.job_matching.text_similarity}%
Experience: ${candidate.extracted_data.job_matching.experience_match}%`}
                            >
                              {candidate.extracted_data.job_matching.overall_match}%
                            </span>
                            {candidate.extracted_data.job_matching.error && (
                              <div className="match-error" title={candidate.extracted_data.job_matching.error}>
                                ⚠️
                              </div>
                            )}
                          </div>
                        ) : (
                          '-'
                        )}
                      </td>
                      <td className="actions-cell">
                        {editingCandidateTempId === candidate.tempId ? (
                          <div className="action-buttons-group">
                            <button 
                              onClick={handleSaveClick} 
                              className="save-btn" 
                              title="Save changes"
                              aria-label="Save changes to candidate data"
                            >
                              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                                  <path d="M19 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H12L21 12V19C21 19.5304 20.7893 20.0391 20.4142 20.4142C20.0391 20.7893 19.5304 21 19 21Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                  <path d="M17 21V13H7V21" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                  <path d="M7 3V8H15" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                              </svg>
                            </button>
                            <button 
                              onClick={handleCancelEdit} 
                              className="cancel-btn" 
                              title="Cancel editing"
                              aria-label="Cancel editing and discard changes"
                            >
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                                    <path d="M18 6L6 18M6 6L18 18" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                </svg>
                            </button>
                          </div>
                        ) : (
                          <div className="action-buttons-group">
                            <button
                              onClick={() => handleEditClick(candidate)}
                              className="edit-btn"
                              title="Edit candidate data"
                              aria-label={`Edit data for ${candidate.extracted_data.name || 'candidate'}`}
                            >
                              <FiEdit2 aria-hidden="true" />
                            </button>
                            <button
                              onClick={() => handleDeleteClick(candidate.tempId)}
                              className="delete-btn"
                              title="Delete candidate"
                              aria-label={`Delete ${candidate.extracted_data.name || 'candidate'} from list`}
                            >
                              <FiTrash2 aria-hidden="true" />
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="9" className="empty-table-message">
                      <div className="empty-state">
                        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M14 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V8L14 2Z"
                            stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          <path d="M14 2V8H20" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          <path d="M12 13V17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          <path d="M10 15H14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                        <p>No parsed candidates found. Upload resumes to see details.</p>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          {parsedResumeData.length > 0 && (
            <div className="table-actions">
              <button
                className="submit-candidates-btn"
                onClick={handleSubmitCandidates}
                disabled={isSubmittingCandidates}
                aria-label={isSubmittingCandidates ? 'Submitting candidates, please wait' : 'Submit all candidates to the system'}
              >
                {isSubmittingCandidates ? 'Submitting Candidates...' : 'Submit All Candidates'}
              </button>
            </div>
          )}
        </div>
      </div>
      </div>

      {/* Modals outside the main container to avoid blur effect */}
      <ConfirmModal
        isOpen={showDeleteModalOverlay}
        onClose={cancelDelete}
        onConfirm={confirmDelete}
        title="Confirm Deletion"
        message="Are you sure you want to delete this candidate? This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
        confirmButtonClass="btn-danger"
        aria-label="Confirm candidate deletion"
      />

      <Modal
        isOpen={showSuccessModal}
        onClose={closeSuccessModal}
        title="Success!"
        size="small"
        showFooter={true}
        className="success-modal"
        footer={
          <div className="modal-confirm-actions">
            <button className="common-modal-btn btn-primary" onClick={closeSuccessModal}>
              Close
            </button>
          </div>
        }
      >
        <div style={{ textAlign: 'center', padding: '1rem 0' }}>
          <svg width="60" height="60" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ marginBottom: '1rem' }}>
            <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM10 17L5 12L6.41 10.59L10 14.17L17.59 6.58L19 8L10 17Z" fill="currentColor"/>
          </svg>
          <p>Candidates processed successfully!</p>
        </div>
      </Modal>
    </>
  );
};

export default React.memo(AddCandidates);
