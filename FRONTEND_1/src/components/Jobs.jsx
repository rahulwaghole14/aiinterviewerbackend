// src/components/Jobs.jsx
import React, { useState, useRef, useEffect, useMemo } from "react";
import { useSelector, useDispatch } from "react-redux";
import "./Jobs.css"; // Import the new CSS file
import { baseURL } from "../data"; // Import baseURL
import {
  fetchJobs,
  fetchDomains,
  addJob,
  updateJob,
  deleteJob,
  addDomain,
  updateDomain,
  deleteDomain,
} from "../redux/slices/jobsSlice"; // Import actions and async thunks
import CustomDropdown from './common/CustomDropdown';
import { FaEdit, FaTrash, FaEllipsisV } from "react-icons/fa";
import DataTable from "./common/DataTable";
import LoadingSpinner from "./common/LoadingSpinner";
import Modal, { FormModal, ConfirmModal } from "./common/Modal";
import ContextMenu from "./common/ContextMenu";
import { useNotification } from "../hooks/useNotification";

const Jobs = () => {
  const dispatch = useDispatch();
  const notify = useNotification();
  const allJobs = useSelector((state) => state.jobs.allJobs);
  const domains = useSelector((state) => state.jobs.domains);
  const jobsStatus = useSelector((state) => state.jobs.jobsStatus);
  const domainsStatus = useSelector((state) => state.jobs.domainsStatus);
  const jobsError = useSelector((state) => state.jobs.jobsError);
  const domainsError = useSelector((state) => state.jobs.domainsError);
  const searchTerm = useSelector((state) => state.search.searchTerm);
  
  // Debug search term
  useEffect(() => {
  }, [searchTerm]);

  // Get user details from Redux store (userSlice)
  const user = useSelector((state) => state.user.user); // Assuming user object is available here
  const userRole = user?.role?.toUpperCase(); // Get the user's role and convert to uppercase for consistent comparison
  const userCompanyName = user?.company_name; // Get the logged-in user's company name

  // Helper function to get domain name by ID - moved to top to avoid hoisting issues
  const getDomainName = (domainId) => {
    const domain = domains.find((d) => d.id === domainId);
    return domain ? domain.name : `Domain ${domainId}`;
  };

  // Log user details for debugging
  useEffect(() => {
  }, [user, userRole, userCompanyName]);

  // Use useMemo to filter jobs based on user role and company name
  const jobsForUser = useMemo(() => {
    if (userRole === "ADMIN") {
      return allJobs; // Admin sees all jobs
    } else if (
      userRole === "COMPANY" ||
      userRole === "HIRING_AGENCY" ||
      userRole === "RECRUITER"
    ) {
      // Company, hiring agency, and recruiter users only see jobs from their company
      // Perform case-insensitive comparison for company name
      return allJobs.filter(
        (job) =>
          job.company_name &&
          userCompanyName &&
          job.company_name.toLowerCase() === userCompanyName.toLowerCase()
      );
    }
    return []; // Other user types see no jobs by default
  }, [allJobs, userRole, userCompanyName]);

  // Fetch jobs and domains on component mount, but only if not already loading or succeeded
  useEffect(() => {
    if (jobsStatus === "idle") {
      dispatch(fetchJobs());
    }
    if (domainsStatus === "idle") {
      dispatch(fetchDomains());
    }
  }, [jobsStatus, domainsStatus, dispatch]);



  const [formData, setFormData] = useState({
    job_title: "",
    company_name: "", // Initialize as empty, will be updated by useEffect if 'COMPANY' user
    domain: "", // This will hold the domain ID
    spoc_email: "",
    hiring_manager_email: "",
    current_team_size_info: "",
    number_to_hire: "",
    position_level: "",
    current_process: "",
    coding_language: "PYTHON", // Default to Python
    job_description: "", // Long text field for job description
  });

  // Effect to prefill company name for 'COMPANY' users when userCompanyName becomes available
  useEffect(() => {
    if (userRole === "COMPANY" && userCompanyName) {
      setFormData((prev) => ({
        ...prev,
        company_name: userCompanyName,
      }));
    }
  }, [userRole, userCompanyName]);


  // Loading states for various operations
  const [isCreatingJob, setIsCreatingJob] = useState(false);
  const [deletingJobId, setDeletingJobId] = useState(null);
  const [updatingJobId, setUpdatingJobId] = useState(null);

  const [isCreatingDomain, setIsCreatingDomain] = useState(false);
  const [updatingDomainId, setUpdatingDomainId] = useState(null);
  const [deletingDomainId, setDeletingDomainId] = useState(null);

  // Inline form feedback
  const [errorMessage, setErrorMessage] = useState("");
  const [showMessage, setShowMessage] = useState(false);

  // Row-wise editing
  const [editingJobId, setEditingJobId] = useState(null);
  const [editedJobData, setEditedJobData] = useState(null);

  // Popup state for deletion
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [jobIdToDelete, setJobIdToDelete] = useState(null);

  // State for sorting
  const [sortColumn, setSortColumn] = useState(null);
  const [sortDirection, setSortDirection] = "asc"; // 'asc' or 'desc'

  // Pagination states - removed manual pagination, let DataTable handle it

  // Domain management states
  const [showCreateDomainModal, setShowCreateDomainModal] = useState(false);
  const [showViewDomainsModal, setShowViewDomainsModal] = useState(false);
  const [domainFormData, setDomainFormData] = useState({
    name: "",
    description: "",
  });
  const [editingDomain, setEditingDomain] = useState(null);

  // Mobile form toggle state
  const [showMobileForm, setShowMobileForm] = useState(false);

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

  // Function to create a new domain
  const handleCreateDomain = async (e) => {
    e.preventDefault();
    setIsCreatingDomain(true);
    const authToken = localStorage.getItem("authToken");
    if (!authToken) {
      setIsCreatingDomain(false);
      notify.error("Authentication token not found. Please log in again.");
      return;
    }

    try {
      const response = await fetch(`${baseURL}/api/jobs/domains/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Token ${authToken}`,
        },
        body: JSON.stringify(domainFormData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`
        );
      }

      const newDomain = await response.json();
      dispatch(addDomain(newDomain)); // Dispatch to Redux store
      setDomainFormData({ name: "", description: "" });
      notify.success("Domain created successfully!");
    } catch (error) {
      notify.error(error.message || "Failed to create domain.");
    } finally {
      setIsCreatingDomain(false);
    }
  };

  // Function to update a domain
  const handleUpdateDomain = async (domainId, updatedData) => {
    setUpdatingDomainId(domainId);
    const authToken = localStorage.getItem("authToken");
    if (!authToken) {
      setUpdatingDomainId(null);
      notify.error("Authentication token not found. Please log in again.");
      return;
    }

    try {
      const response = await fetch(`${baseURL}/api/jobs/domains/${domainId}/`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Token ${authToken}`,
        },
        body: JSON.stringify(updatedData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`
        );
      }

      const updatedDomain = await response.json();
      dispatch(updateDomain({ id: domainId, updatedData: updatedDomain })); // Dispatch to Redux store
      setEditingDomain(null);
      notify.success("Domain updated successfully!");
    } catch (error) {
      notify.error(error.message || "Failed to update domain.");
    } finally {
      setUpdatingDomainId(null);
    }
  };

  // Function to delete a domain
  const handleDeleteDomain = async (domainId) => {
    setDeletingDomainId(domainId);
    const authToken = localStorage.getItem("authToken");
    if (!authToken) {
      setDeletingDomainId(null);
      notify.error("Authentication token not found. Please log in again.");
      return;
    }

    try {
      const response = await fetch(`${baseURL}/api/jobs/domains/${domainId}/`, {
        method: "DELETE",
        headers: {
          Authorization: `Token ${authToken}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`
        );
      }

      dispatch(deleteDomain(domainId)); // Dispatch to Redux store
      notify.success("Domain deleted successfully!");
    } catch (error) {
      notify.error(error.message || "Failed to delete domain.");
    } finally {
      setDeletingDomainId(null);
    }
  };

  // Handle domain form changes
  const handleDomainChange = (e) => {
    const { name, value } = e.target;
    setDomainFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  // Sort jobs based on search term relevance (don't filter out jobs)
  const sortedJobs = [...jobsForUser].sort((a, b) => {
    // First priority: search term relevance (if search term exists)
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      
      // Calculate relevance scores for both jobs - search ALL fields
      const getRelevanceScore = (job) => {
        let score = 0;
        
        // Search ALL fields in the job object dynamically
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
            } else {
              searchValue = String(value);
            }
            
            // Also include domain name lookup for domain field
            if (key === 'domain' && typeof value === 'number') {
              const domainName = getDomainName(value);
              if (domainName) {
                const domainStr = domainName.toLowerCase();
                if (domainStr.includes(searchLower)) {
                  if (domainStr.startsWith(searchLower)) score += 10;
                  else score += 5;
                }
              }
            }
            
            const fieldStr = searchValue.toLowerCase();
            if (fieldStr.includes(searchLower)) {
              if (fieldStr.startsWith(searchLower)) score += 10; // Starts with search term
              else score += 5; // Contains search term
            }
          });
        };
        
        searchAllFields(job);
        return score;
      };
      
      const aScore = getRelevanceScore(a);
      const bScore = getRelevanceScore(b);
      
      if (aScore !== bScore) {
        return bScore - aScore; // Higher relevance first
      }
    }
    
    // Second priority: column sorting (if specified)
      if (!sortColumn) return 0;

      const aValue =
        sortColumn === "domain" ? (a.domain_name || getDomainName(a[sortColumn])) : a[sortColumn];
      const bValue =
        sortColumn === "domain" ? (b.domain_name || getDomainName(b[sortColumn])) : b[sortColumn];

      if (aValue === null || aValue === undefined)
        return sortDirection === "asc" ? 1 : -1;
      if (bValue === null || bValue === undefined)
        return sortDirection === "asc" ? -1 : 1;

      if (typeof aValue === "string" && typeof bValue === "string") {
        return sortDirection === "asc"
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }
      if (typeof aValue === "number" && typeof bValue === "number") {
        return sortDirection === "asc" ? aValue - bValue : bValue - aValue;
      }
      return 0;
    });

  // Use sortedJobs directly - DataTable will handle pagination
  const currentRecords = sortedJobs;

  // DataTable will handle pagination automatically

  // Effect to add/remove 'show' class for modal animations
  // Delete confirmation modal is now handled by ConfirmModal component

  // Effect for Create Domain Modal animation
  useEffect(() => {
    const createDomainModalOverlay = document.getElementById(
      "create-domain-modal-overlay"
    );
    if (createDomainModalOverlay) {
      if (showCreateDomainModal) {
        createDomainModalOverlay.classList.remove("hidden");
      } else {
        createDomainModalOverlay.classList.add("hidden"); // Corrected from createDomainModal.classList.add('hidden');
      }
    }
  }, [showCreateDomainModal]);

  // Effect for View Domains Modal animation
  useEffect(() => {
    const viewDomainsModalOverlay = document.getElementById(
      "view-domains-modal-overlay"
    );
    if (viewDomainsModalOverlay) {
      if (showViewDomainsModal) {
        viewDomainsModalOverlay.classList.remove("hidden");
      } else {
        viewDomainsModalOverlay.classList.add("hidden");
      }
    }
  }, [showViewDomainsModal]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsCreatingJob(true); // Set loading state
    const {
      job_title,
      company_name,
      domain,
      spoc_email,
      hiring_manager_email,
      current_team_size_info,
      number_to_hire,
      position_level,
      current_process,
      coding_language,
      job_description,
    } = formData;

    // Validate required fields based on API
    if (
      !job_title ||
      !company_name ||
      !domain ||
      !spoc_email ||
      !hiring_manager_email ||
      !number_to_hire ||
      !position_level ||
      !coding_language
    ) {
      setErrorMessage(
        "Please fill all required fields: Job Title, Company Name, Domain, SPOC Email, Hiring Manager Email, Number to Hire, Position Level, and Coding Language."
      );
      setShowMessage(false);
      setIsCreatingJob(false); // Reset loading state on validation error
      return;
    }

    // Validate position level
    const validPositionLevels = ["IC", "Manager"];
    if (!validPositionLevels.includes(position_level)) {
      setErrorMessage(
        `Invalid position level: ${position_level}. Must be one of: ${validPositionLevels.join(", ")}`
      );
      setShowMessage(false);
      setIsCreatingJob(false);
      return;
    }
    setErrorMessage("");

    // Determine if we're creating or updating
    const isEditing = editingJobId !== null;
    
    try {
      const authToken = localStorage.getItem("authToken");
      
      const url = isEditing 
        ? `${baseURL}/api/jobs/${editingJobId}/`
        : `${baseURL}/api/jobs/`;
      const method = isEditing ? "PUT" : "POST";
      

      // Validate domain before sending (prevent NaN)
      const domainValue = domain && domain !== "" ? parseInt(domain, 10) : null;
      if (!domainValue || isNaN(domainValue)) {
        setErrorMessage("Please select a valid domain.");
        setShowMessage(false);
        setIsCreatingJob(false);
        return;
      }

      const response = await fetch(url, {
        method: method,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Token ${authToken}`,
        },
        body: JSON.stringify({
          job_title,
          company_name,
          domain: domainValue,
          spoc_email,
          hiring_manager_email,
          current_team_size_info: current_team_size_info || "",
          number_to_hire: parseInt(number_to_hire, 10),
          position_level,
          current_process: current_process || "",
          coding_language: coding_language ? coding_language.toUpperCase() : "PYTHON",
          job_description: job_description || "",
        }),
      });

      
      if (!response.ok) {
        const responseText = await response.text();
        
        try {
          const errorData = JSON.parse(responseText);
          // Handle DRF validation errors (field-specific errors)
          if (errorData.details && typeof errorData.details === 'object') {
            const errorMessages = Object.entries(errorData.details).map(([field, errors]) => {
              const fieldErrors = Array.isArray(errors) ? errors.join(', ') : errors;
              return `${field}: ${fieldErrors}`;
            }).join('\n');
            throw new Error(`Validation errors:\n${errorMessages}`);
          } else if (errorData.error) {
            throw new Error(errorData.error);
          } else if (errorData.detail) {
            throw new Error(errorData.detail);
          } else if (typeof errorData === 'object') {
            // Handle DRF serializer errors (flat structure)
            const errorMessages = Object.entries(errorData).map(([field, errors]) => {
              const fieldErrors = Array.isArray(errors) ? errors.join(', ') : errors;
              return `${field}: ${fieldErrors}`;
            }).join('\n');
            throw new Error(`Validation errors:\n${errorMessages}`);
          } else {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
        } catch (parseError) {
          throw new Error(`HTTP error! status: ${response.status}. Response: ${responseText.substring(0, 200)}`);
        }
      }

      const jobData = await response.json();
      
      if (isEditing) {
        dispatch(updateJob({ id: jobData.id, updatedData: jobData })); // Dispatch to Redux store
        setShowMessage(true);
        setEditingJobId(null); // Exit edit mode
      } else {
        dispatch(addJob(jobData)); // Dispatch to Redux store
        setShowMessage(true);
      }

      // Clear form after successful submission
      setFormData({
        job_title: "",
        company_name: userRole === "COMPANY" ? userCompanyName : "", // Reset to prefilled if company user
        domain: "",
        spoc_email: "",
        hiring_manager_email: "",
        current_team_size_info: "",
        number_to_hire: "",
        position_level: "",
        current_process: "",
        coding_language: "PYTHON",
        job_description: "",
      });
      
      setTimeout(() => {
        setShowMessage(false);
      }, 2000);
    } catch (error) {
      setErrorMessage(error.message || (isEditing ? "Failed to update job. Please try again." : "Failed to add job. Please try again."));
      setShowMessage(false); // Hide success message in case of error
    } finally {
      setIsCreatingJob(false); // Reset loading state
    }
  };

  const handleEditClick = (job) => {
    setEditingJobId(job.id);
    setEditedJobData({ ...job }); // Create a copy for editing
  };

  const handleEditCellChange = (e, field) => {
    const newValue = e.target.value;
    setEditedJobData((prev) => ({ ...prev, [field]: newValue }));
  };

  const handleSaveClick = async () => {
    if (editedJobData) {
      setUpdatingJobId(editedJobData.id); // Set loading state for job update with specific ID
      setErrorMessage("");
      const authToken = localStorage.getItem("authToken");
      if (!authToken) {
        setErrorMessage("Authentication token not found. Please log in again.");
        setUpdatingJobId(null);
        return;
      }
      // Validate required fields before saving
      const {
        job_title,
        company_name,
        domain,
        spoc_email,
        hiring_manager_email,
        number_to_hire,
        position_level,
        coding_language,
      } = editedJobData;
      if (
        !job_title ||
        !company_name ||
        !domain ||
        !spoc_email ||
        !hiring_manager_email ||
        !number_to_hire ||
        !position_level ||
        !coding_language
      ) {
        setErrorMessage("Please fill all required fields before saving.");
        setUpdatingJobId(null); // Reset loading state on validation error
        return;
      }

      // Validate position level
      const validPositionLevels = ["IC", "Manager"];
      if (!validPositionLevels.includes(position_level)) {
        setErrorMessage(
          `Invalid position level: ${position_level}. Must be one of: ${validPositionLevels.join(", ")}`
        );
        setUpdatingJobId(null);
        return;
      }

      try {
        const response = await fetch(
          `${baseURL}/api/jobs/${editedJobData.id}/`,
          {
            method: "PUT", // Use PUT for full update
            headers: {
              "Content-Type": "application/json",
              Authorization: `Token ${authToken}`,
            },
            body: JSON.stringify({
              job_title: editedJobData.job_title,
              company_name: editedJobData.company_name,
              domain: parseInt(editedJobData.domain, 10), // Ensure domain is an integer
              spoc_email: editedJobData.spoc_email,
              hiring_manager_email: editedJobData.hiring_manager_email,
              current_team_size_info: editedJobData.current_team_size_info,
              number_to_hire: parseInt(editedJobData.number_to_hire, 10), // Ensure number
              position_level: editedJobData.position_level,
              current_process: editedJobData.current_process,
              coding_language: editedJobData.coding_language ? editedJobData.coding_language.toUpperCase() : "PYTHON",
              job_description: editedJobData.job_description || "",
            }),
          }
        );

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(
            errorData.detail || `HTTP error! status: ${response.status}`
          );
        }

        const updatedJob = await response.json();

        dispatch(updateJob({ id: updatedJob.id, updatedData: updatedJob })); // Dispatch to Redux store

        setEditingJobId(null);
        setEditedJobData(null);
      } catch (error) {
        setErrorMessage(
          error.message || "Failed to update job. Please try again."
        );
      } finally {
        setUpdatingJobId(null); // Reset loading state
      }
    }
  };

  const handleCancelClick = () => {
    setEditingJobId(null);
    setEditedJobData(null);
  };

  const handleViewJob = (job) => {
    // For now, just log the job details
    // You can implement a modal or navigation to show job details
    alert(`Viewing job: ${job.job_title} at ${job.company_name}`);
  };

  const handleEditJob = (job) => {
    // Populate the form with job data for editing
    setFormData({
      job_title: job.job_title || "",
      company_name: job.company_name || "",
      domain: job.domain || "",
      spoc_email: job.spoc_email || "",
      hiring_manager_email: job.hiring_manager_email || "",
      current_team_size_info: job.current_team_size_info || "",
      number_to_hire: job.number_to_hire || "",
      position_level: job.position_level || "",
      current_process: job.current_process || "",
            coding_language: job.coding_language ? job.coding_language.toUpperCase() : "PYTHON",
      job_description: job.job_description || "",
    });
    // Set editing state to track which job is being edited
    setEditingJobId(job.id);
    // Clear any existing messages
    setShowMessage(false);
    setErrorMessage("");
  };

  const handleDeleteClick = (id) => {
    setJobIdToDelete(id); // Set the ID of the job to be deleted
    setShowDeleteConfirm(true);
  };

  const confirmDelete = async () => {
    if (jobIdToDelete !== null) {
      setDeletingJobId(jobIdToDelete); // Set loading state with specific job ID
      const authToken = localStorage.getItem("authToken");
      if (!authToken) {
        setErrorMessage("Authentication token not found. Please log in again.");
        setShowDeleteConfirm(false);
        setDeletingJobId(null); // Reset loading state
        setJobIdToDelete(null);
        return;
      }

      try {
        const response = await fetch(`${baseURL}/api/jobs/${jobIdToDelete}/`, {
          method: "DELETE",
          headers: {
            Authorization: `Token ${authToken}`,
          },
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(
            errorData.detail || `HTTP error! status: ${response.status}`
          );
        }

        dispatch(deleteJob(jobIdToDelete)); // Dispatch to Redux store

        setShowDeleteConfirm(false);
        setJobIdToDelete(null);
      } catch (error) {
        setErrorMessage(
          error.message || "Failed to delete job. Please try again."
        );
        setShowDeleteConfirm(false);
        setJobIdToDelete(null);
      } finally {
        setDeletingJobId(null); // Reset loading state
      }
    }
  };

  const cancelDelete = () => {
    setShowDeleteConfirm(false);
    setJobIdToDelete(null);
  };

  // New function for DataTable delete integration
  const handleDeleteJob = async (jobId) => {
    const authToken = localStorage.getItem("authToken");
    if (!authToken) {
      setErrorMessage("Authentication token not found. Please log in again.");
      return;
    }

    try {
      const response = await fetch(`${baseURL}/api/jobs/${jobId}/`, {
        method: "DELETE",
        headers: {
          Authorization: `Token ${authToken}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`
        );
      }

      dispatch(deleteJob(jobId)); // Dispatch to Redux store
    } catch (error) {
      setErrorMessage(
        error.message || "Failed to delete job. Please try again."
      );
      throw error; // Re-throw so DataTable can handle the error
    }
  };

  // New function for DataTable edit integration
  const handleUpdateJob = async (editedData) => {
    const authToken = localStorage.getItem("authToken");
    if (!authToken) {
      setErrorMessage("Authentication token not found. Please log in again.");
      throw new Error("Authentication token not found");
    }

    // Validate position level
    const validPositionLevels = ["IC", "Manager"];
    if (editedData.position_level && !validPositionLevels.includes(editedData.position_level)) {
      // Map common invalid values to valid ones
      if (editedData.position_level.toLowerCase().includes("mid") || editedData.position_level.toLowerCase().includes("senior")) {
        editedData.position_level = "IC";
      } else if (editedData.position_level.toLowerCase().includes("manager") || editedData.position_level.toLowerCase().includes("lead")) {
        editedData.position_level = "Manager";
      } else {
        throw new Error(`Invalid position level: ${editedData.position_level}. Must be one of: ${validPositionLevels.join(", ")}`);
      }
    }

    try {
      const response = await fetch(
        `${baseURL}/api/jobs/${editedData.id}/`,
        {
          method: "PUT", // Use PUT for full update
          headers: {
            "Content-Type": "application/json",
            Authorization: `Token ${authToken}`,
          },
          body: JSON.stringify({
            job_title: editedData.job_title,
            company_name: editedData.company_name,
            domain: editedData.domain && editedData.domain !== '' ? parseInt(editedData.domain, 10) : null, // Handle null/empty domain
            spoc_email: editedData.spoc_email,
            hiring_manager_email: editedData.hiring_manager_email,
            current_team_size_info: editedData.current_team_size_info,
            number_to_hire: Math.max(1, parseInt(editedData.number_to_hire, 10) || 1), // Ensure number is at least 1
            position_level: editedData.position_level,
            current_process: editedData.current_process,
            coding_language: editedData.coding_language ? editedData.coding_language.toUpperCase() : "PYTHON",
            job_description: editedData.job_description || "",
            // Remove is_active field as it doesn't exist in the Job model
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.detail || errorData.message || `HTTP error! status: ${response.status}`
        );
      }

      const updatedJob = await response.json();

      dispatch(updateJob({ id: updatedJob.id, updatedData: updatedJob })); // Dispatch to Redux store
    } catch (error) {
        setErrorMessage(
        error.message || "Failed to update job. Please try again."
      );
      throw error; // Re-throw so DataTable can handle the error
    }
  };

  // Handle sorting logic
  const handleSort = (column) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortColumn(column);
      setSortDirection("asc");
    }
  };

  const getSortIndicator = (column) => {
    if (sortColumn === column) {
      return sortDirection === "asc" ? " ▲" : " ▼";
    }
    return "";
  };

  // Utility function to trim text and show tooltip
  const trimWithTooltip = (text, maxLength = 20) => {
    if (text === null || text === undefined || text === "") return "-"; // Handle null, undefined, empty string
    const str = String(text);
    return str.length > maxLength ? (
      <span title={str}>{str.slice(0, maxLength) + "..."}</span>
    ) : (
      <span title={str}>{str}</span>
    );
  };

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
      // Trigger delete confirmation modal instead of direct delete
      setJobIdToDelete(rowData.id);
      setShowDeleteConfirm(true);
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


  // Determine if any job operation is in progress (for disabling other buttons)
  const isAnyJobOperationInProgress =
    isCreatingJob || updatingJobId !== null || deletingJobId !== null;
  // Determine if any domain operation is in progress (for disabling other buttons)
  const isAnyDomainOperationInProgress =
    isCreatingDomain || updatingDomainId !== null || deletingDomainId !== null;

  const [selectedRows, setSelectedRows] = useState([]);
  const [selectAll, setSelectAll] = useState(false);
  const [actionMenuId, setActionMenuId] = useState(null);

  const toggleRowSelection = (id) => {
    setSelectedRows((prev) =>
      prev.includes(id) ? prev.filter((rowId) => rowId !== id) : [...prev, id]
    );
  };

  const toggleSelectAll = () => {
    if (selectAll) {
      setSelectedRows([]);
    } else {
      setSelectedRows(jobsForUser.map((job) => job.id));
    }
    setSelectAll(!selectAll);
  };

  const toggleActionMenu = (id, e) => {
    e.stopPropagation();
    setActionMenuId((prev) => (prev === id ? null : id));
  };

  useEffect(() => {
    const handleClickOutside = () => setActionMenuId(null);
    document.addEventListener("click", handleClickOutside);
    return () => document.removeEventListener("click", handleClickOutside);
  }, []);

  // Check if any modal is open for blur effect
  const isAnyModalOpen = showCreateDomainModal || showViewDomainsModal || showDeleteConfirm;

  return (
    <>
      <div className={`jobs-container ${isAnyModalOpen ? 'blur-background' : ''}`}>
        {/* Management Buttons Row */}
        {/* Mobile Header - Domain Buttons */}
        {(userRole === "ADMIN" || userRole === "COMPANY") && (
          <div className="mobile-header-section">
            {/* Domain Management Container */}
            <div className="domain-management-section">
              <button
                type="button"
                className="domain-btn create-domain-btn"
                onClick={() => {
                  setDomainFormData({ name: "", description: "" });
                  setShowCreateDomainModal(true);
                }}
                disabled={isAnyDomainOperationInProgress}
              >
                {isCreatingDomain ? "Adding Domain..." : "+ Create New Domain"}
              </button>
              <button
                type="button"
                className="domain-btn view-domains-btn"
                onClick={() => setShowViewDomainsModal(true)}
                disabled={isAnyDomainOperationInProgress}
              >
                View All Domains
              </button>
            </div>

            {/* Jobs Header Container - Total Jobs + Create Button */}
            <div className="jobs-header-container">
              <div className="total-jobs-card">
                <div className="jobs-count-card">
                  <span className="jobs-count-text">Total Jobs: </span>
                  <span className="jobs-count-number">{jobsForUser.length}</span>
                </div>
              </div>

              <div className="mobile-form-toggle">
                <button
                  className={`mobile-create-job-btn ${showMobileForm ? 'form-open' : ''}`}
                  onClick={() => setShowMobileForm(!showMobileForm)}
                >
                  <span className="btn-icon">{showMobileForm ? '×' : '+'}</span>
                  <span className="btn-text">{showMobileForm ? 'Close' : 'Create New Job'}</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Desktop view - Domain buttons + Total Jobs */}
        {(userRole === "ADMIN" || userRole === "COMPANY") && (
          <div className="desktop-header-section desktop-only">
            {/* Domain Management Buttons - Left Side */}
            <div className="domain-management-section">
              <button
                type="button"
                className="domain-btn create-domain-btn"
                onClick={() => {
                  setDomainFormData({ name: "", description: "" });
                  setShowCreateDomainModal(true);
                }}
                disabled={isAnyDomainOperationInProgress}
              >
                {isCreatingDomain ? "Adding Domain..." : "+ Create New Domain"}
              </button>
              <button
                type="button"
                className="domain-btn view-domains-btn"
                onClick={() => setShowViewDomainsModal(true)}
                disabled={isAnyDomainOperationInProgress}
              >
                View All Domains
              </button>
            </div>

            {/* Total Jobs Card - Right Side */}
            <div className="total-jobs-card">
              <div className="jobs-count-card">
                <span className="jobs-count-text">Total Jobs: </span>
                <span className="jobs-count-number">{jobsForUser.length}</span>
              </div>
            </div>
          </div>
        )}



        {/* Main Content Area - Form and Table side-by-side */}
        <div
          className="jobs-main-content fixed-grid"
          style={
            userRole === "RECRUITER" || userRole === "HIRING_AGENCY"
              ? { gridTemplateColumns: "1fr" }
              : {}
          }
        >
          {/* Left Column: Create New Job Form */}
          {userRole === "ADMIN" || userRole === "COMPANY" ? (
            <div className={`jobs-form card slide-in-left ${showMobileForm ? 'mobile-form-visible' : 'mobile-form-hidden'}`}>
              <h2 className="form-title">
                {editingJobId ? "Edit Job" : "Create New Job"}
              </h2>
              <form id="jobForm" onSubmit={handleSubmit}>
                <div className="form-box">
                  <label htmlFor="job_title">Job Title</label>
                  <input
                    type="text"
                    id="job_title"
                    name="job_title"
                    placeholder="e.g., Data Analyst"
                    value={formData.job_title}
                    onChange={handleChange}
                    className="jobs-input"
                    required
                    disabled={isCreatingJob}
                  />

                  <label htmlFor="company_name">Company Name</label>
                  <input
                    type="text"
                    id="company_name"
                    name="company_name"
                    placeholder="e.g., Insight Analytics"
                    value={formData.company_name}
                    onChange={handleChange}
                    className="jobs-input"
                    required
                    readOnly={userRole === "COMPANY"}
                  />

                  <label htmlFor="domain">Domain</label>
                  <CustomDropdown
                    value={String(formData.domain)}
                    options={[
                      { value: '', label: 'Select a domain' },
                      ...domains.map(domain => ({ value: String(domain.id), label: domain.name }))
                    ]}
                    onChange={(value) => handleChange({ target: { name: 'domain', value } })}
                    placeholder="Select a domain"
                    disabled={isCreatingJob || domainsStatus === "loading"}
                  />

                  <label htmlFor="spoc_email">SPOC Email</label>
                  <input
                    type="email"
                    id="spoc_email"
                    name="spoc_email"
                    placeholder="e.g., hr@insight.com"
                    value={formData.spoc_email}
                    onChange={handleChange}
                    className="jobs-input"
                    required
                    disabled={isCreatingJob}
                  />

                  <label htmlFor="hiring_manager_email">
                    Hiring Manager Email
                  </label>
                  <input
                    type="email"
                    id="hiring_manager_email"
                    name="hiring_manager_email"
                    placeholder="e.g., lead@insight.com"
                    value={formData.hiring_manager_email}
                    onChange={handleChange}
                    className="jobs-input"
                    required
                    disabled={isCreatingJob}
                  />

                  <label htmlFor="current_team_size_info">
                    Current Team Size Info
                  </label>
                  <input
                    type="text"
                    id="current_team_size_info"
                    name="current_team_size_info"
                    placeholder="e.g., 5-10"
                    value={formData.current_team_size_info}
                    onChange={handleChange}
                    className="jobs-input"
                    disabled={isCreatingJob}
                  />

                  <label htmlFor="number_to_hire">Number to Hire</label>
                  <input
                    type="number"
                    id="number_to_hire"
                    name="number_to_hire"
                    placeholder="e.g., 2"
                    value={formData.number_to_hire}
                    onChange={handleChange}
                    className="jobs-input"
                    required
                    disabled={isCreatingJob}
                  />

                  <label htmlFor="position_level">Position Level</label>
                  <select
                    id="position_level"
                    name="position_level"
                    value={formData.position_level}
                    onChange={handleChange}
                    className="jobs-input"
                    required
                    disabled={isCreatingJob}
                  >
                    <option value="">Select Position Level</option>
                    <option value="IC">IC (Individual Contributor)</option>
                    <option value="Manager">Manager</option>
                  </select>

                  <label htmlFor="current_process">Current Process</label>
                  <input
                    type="text"
                    id="current_process"
                    name="current_process"
                    placeholder="e.g., Screening, Interview (optional)"
                    value={formData.current_process}
                    onChange={handleChange}
                    className="jobs-input"
                    disabled={isCreatingJob}
                  />

                  <label htmlFor="coding_language">Coding Language</label>
                  <CustomDropdown
                    value={formData.coding_language || "PYTHON"}
                    options={[
                      { value: 'PYTHON', label: 'Python' },
                      { value: 'JAVASCRIPT', label: 'JavaScript' },
                      { value: 'C', label: 'C' },
                      { value: 'CPP', label: 'C++' },
                      { value: 'JAVA', label: 'Java' },
                      { value: 'GO', label: 'Go' },
                      { value: 'HTML', label: 'HTML' },
                      { value: 'PHP', label: 'PHP' },
                    ]}
                    onChange={(value) => handleChange({ target: { name: 'coding_language', value } })}
                    placeholder="Select coding language"
                    disabled={isCreatingJob}
                  />

                  <label htmlFor="job_description">Job Description</label>
                  <textarea
                    id="job_description"
                    name="job_description"
                    placeholder="Enter detailed job description, responsibilities, requirements, etc."
                    value={formData.job_description}
                    onChange={handleChange}
                    className="jobs-input"
                    rows="6"
                    style={{ resize: "vertical", minHeight: "120px" }}
                    disabled={isCreatingJob}
                  />

                  <div className="form-actions">
                  <button
                    className="submit-btn"
                    type="submit"
                    disabled={isCreatingJob}
                  >
                    {isCreatingJob 
                      ? (editingJobId ? "Updating Job..." : "Creating Job...") 
                      : (editingJobId ? "Update Job" : "Create Job")
                    }
                  </button>
                  {editingJobId && (
                    <button
                      type="button"
                      className="cancel-btn"
                      onClick={() => {
                        setEditingJobId(null);
                        setFormData({
                          job_title: "",
                          company_name: userRole === "COMPANY" ? userCompanyName : "",
                          domain: "",
                          spoc_email: "",
                          hiring_manager_email: "",
                          current_team_size_info: "",
                          number_to_hire: "",
                          position_level: "",
                          current_process: "",
                          coding_language: "PYTHON",
                          job_description: "",
                        });
                        setShowMessage(false);
                        setErrorMessage("");
                      }}
                      disabled={isCreatingJob}
                    >
                      Cancel
                    </button>
                  )}
                  </div>
                </div>
              </form>
            </div>
          ) : null}

          {/* Job Listings Table */}
          <div className="job-listings-section card">
            <div className="data-table-wrapper">
              <DataTable
            title="Job Listings"
            columns={[
              {
                field: "job_title",
                header: "Job Title",
                width: "200px",
                editable: true,
                render: (value) => (
                  <div title={value} className="text-truncate">
                    {value}
                  </div>
                ),
              },
              {
                field: "company_name",
                header: "Company",
                width: "150px",
                editable: true,
                render: (value) => (
                  <div title={value} className="text-truncate">
                    {value}
                  </div>
                ),
              },
              {
                field: "domain",
                header: "Domain", 
                width: "120px",
                type: "select",
                editable: true,
                options: domains.map(domain => ({
                  value: domain.id,
                  label: domain.name
                })),
                placeholder: "Select Domain",
                render: (value, rowData) => (
                  <div title={rowData.domain_name || getDomainName(value) || "-"} className="text-truncate">
                    {rowData.domain_name || getDomainName(value) || "-"}
                  </div>
                ),
              },
              {
                field: "spoc_email",
                header: "SPOC Email",
                width: "180px",
                editable: true,
                render: (value) => (
                  <div title={value} className="text-truncate">
                    {value}
                  </div>
                ),
              },
              {
                field: "hiring_manager_email",
                header: "Hiring Manager Email",
                width: "180px",
                editable: true,
                render: (value) => (
                  <div title={value} className="text-truncate">
                    {value}
                  </div>
                ),
              },
              {
                field: "current_team_size_info",
                header: "Current Team Size Info",
                width: "160px",
                editable: true,
                render: (value) => (
                  <div title={value} className="text-truncate">
                    {value || 'N/A'}
                  </div>
                ),
              },
              {
                field: "number_to_hire",
                header: "Number to Hire",
                width: "120px",
                editable: true,
                type: "number",
              },
              {
                field: "position_level",
                header: "Position Level",
                width: "140px",
                type: "select",
                editable: true,
                options: [
                  { value: "IC", label: "IC" },
                  { value: "Manager", label: "Manager" },
                ],
              },
              {
                field: "current_process",
                header: "Current Process",
                width: "180px",
                editable: true,
                render: (value) => {
                  if (!value) return 'N/A';
                  const truncated = value.length > 50 ? value.substring(0, 50) + '...' : value;
                      return (
                    <div title={value} className="text-truncate">
                      {truncated}
                    </div>
                  );
                },
              },
              {
                field: "coding_language",
                header: "Coding Language",
                width: "150px",
                editable: true,
                render: (value) => {
                  if (!value) return 'N/A';
                  const languageLabels = {
                    'PYTHON': 'Python',
                    'JAVASCRIPT': 'JavaScript',
                    'C': 'C',
                    'CPP': 'C++',
                    'JAVA': 'Java',
                    'GO': 'Go',
                    'HTML': 'HTML',
                    'PHP': 'PHP',
                    'RUBY': 'Ruby',
                    'CSHARP': 'C#',
                    'SQL': 'SQL',
                  };
                  const displayValue = languageLabels[value] || value;
                  return (
                    <div title={displayValue} className="text-truncate">
                      {displayValue}
                    </div>
                  );
                },
              },
              {
                field: "job_description",
                header: "Job Description",
                width: "220px",
                editable: true,
                render: (value) => {
                  if (!value) return 'N/A';
                  const truncated = value.length > 60 ? value.substring(0, 60) + '...' : value;
                  return (
                    <div title={value} className="text-truncate">
                      {truncated}
                    </div>
                  );
                },
              },
              {
                field: "created_at",
                header: "Created",
                width: "120px",
                render: (value) => {
                  if (!value) return 'N/A';
                  return new Date(value).toLocaleDateString();
                },
              },
            ]}
            data={currentRecords || []}
            loading={jobsStatus === "loading"}
            actions={["edit", "delete"]}
            onAction={(action, rowData, rowIndex) => {
              if (action === "edit") {
                // For edit, we let DataTable handle inline editing
                // Just return to let DataTable handle it
                return;
              } else if (action === "delete") {
                // Handle delete directly with API call
                handleDeleteJob(rowData.id);
              }
            }}
            onContextMenuClick={handleContextMenuClick}
            onEdit={async (editedData) => {
              // Handle save from DataTable inline editing
              await handleUpdateJob(editedData);
            }}
            editingRow={editingRow}
            editingData={editingData}
            setEditingRow={setEditingRow}
            setEditingData={setEditingData}
            showRefresh={true}
            onRefresh={async () => {
              try {
                await dispatch(fetchJobs()).unwrap();
                notify.success("Jobs data refreshed successfully!");
              } catch (error) {
                notify.error("Failed to refresh jobs data. Please try again.");
              }
            }}
            showActions={true}
            defaultPageSize={10}
            pageSizeOptions={[10, 20, 50, 100, 200, 500]}
          />
            </div>
          </div>

        </div>
      </div>

      {/* Create Domain Modal - Moved outside main container */}
      <FormModal
        isOpen={showCreateDomainModal}
        onClose={() => setShowCreateDomainModal(false)}
        onSubmit={handleCreateDomain}
        title="Create New Domain"
        submitText="Create Domain"
        isSubmitting={isCreatingDomain}
        size="medium"
      >
                <div className="form-group">
                  <label htmlFor="domain-name">Domain Name</label>
                  <input
                    type="text"
                    id="domain-name"
                    name="name"
                    value={domainFormData.name}
                    onChange={handleDomainChange}
                    placeholder="e.g., Data Science"
                    required
                    disabled={isCreatingDomain}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="domain-description">Description</label>
                  <textarea
                    id="domain-description"
                    name="description"
                    value={domainFormData.description}
                    onChange={handleDomainChange}
                    placeholder="e.g., Data Science and Analytics domain"
                    rows="3"
                    required
                    disabled={isCreatingDomain}
                  />
                </div>
      </FormModal>

      {/* View Domains Modal - Moved outside main container */}
      <Modal
        isOpen={showViewDomainsModal}
        onClose={() => setShowViewDomainsModal(false)}
        title="All Domains"
        size="large"
        closeOnBackdrop={!isAnyDomainOperationInProgress}
        closeOnEscape={!isAnyDomainOperationInProgress}
        showFooter={true}
        footer={
          <div className="modal-confirm-actions">
              <button
              className="common-modal-btn btn-cancel" 
                onClick={() => setShowViewDomainsModal(false)}
                disabled={isAnyDomainOperationInProgress}
              >
              Close
              </button>
            </div>
        }
      >
              {domainsStatus === "loading" ? (
                <div className="loading-overlay">
                  <div className="loading-spinner"></div>
                  <p>Loading domains...</p>
                </div>
              ) : domains.length === 0 ? (
                <p>No domains found. Create your first domain!</p>
              ) : (
                <div className="domains-list">
                  {domains.map((domain) => (
                    <div key={domain.id} className="domain-item">
                      {editingDomain === domain.id ? (
                        <div className="domain-edit-form">
                          <label htmlFor={`edit-domain-name-${domain.id}`}>
                            Domain Name
                          </label>
                          <input
                            type="text"
                            id={`edit-domain-name-${domain.id}`}
                            value={domainFormData.name}
                            onChange={handleDomainChange}
                            name="name"
                            className="domain-edit-input"
                            disabled={updatingDomainId === domain.id}
                          />
                          <label
                            htmlFor={`edit-domain-description-${domain.id}`}
                          >
                            Description
                          </label>
                          <textarea
                            id={`edit-domain-description-${domain.id}`}
                            value={domainFormData.description}
                            onChange={handleDomainChange}
                            name="description"
                            className="domain-edit-input"
                            rows="2"
                            disabled={updatingDomainId === domain.id}
                          />
                          <div className="domain-edit-actions">
                            <button
                              className="save-btn"
                              onClick={() =>
                                handleUpdateDomain(domain.id, {
                                  name: domainFormData.name,
                                  description: domainFormData.description,
                                  is_active: domain.is_active,
                                })
                              }
                              disabled={updatingDomainId === domain.id}
                            >
                              {updatingDomainId === domain.id
                                ? "Saving..."
                                : "Save"}
                            </button>
                            <button
                              className="cancel-btn"
                              onClick={() => setEditingDomain(null)}
                              disabled={updatingDomainId === domain.id}
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="domain-info">
                          <div className="domain-details">
                            <h4>{domain.name}</h4>
                            <p>{trimWithTooltip(domain.description, 50)}</p>
                            <span
                              className={`domain-status ${
                                domain.is_active ? "active" : "inactive"
                              }`}
                            >
                              {domain.is_active ? "Active" : "Inactive"}
                            </span>
                          </div>
                          <div className="domain-actions">
                            <button
                              className="edit-btn"
                              onClick={() => {
                                setEditingDomain(domain.id);
                                setDomainFormData({
                                  name: domain.name,
                                  description: domain.description,
                                });
                              }}
                              disabled={isAnyDomainOperationInProgress}
                            >
                              Edit
                            </button>
                            <button
                              className="delete-btn"
                              onClick={() => handleDeleteDomain(domain.id)}
                              disabled={isAnyDomainOperationInProgress}
                            >
                              {deletingDomainId === domain.id
                                ? "Deleting..."
                                : "Delete"}
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
      </Modal>

      {/* Delete Confirmation Modal */}
      <ConfirmModal
        isOpen={showDeleteConfirm}
        onClose={cancelDelete}
        onConfirm={confirmDelete}
        title="Delete Job"
        message="Are you sure you want to delete this job? This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
        isLoading={deletingJobId !== null}
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
    </>
  );
};

export default Jobs;
