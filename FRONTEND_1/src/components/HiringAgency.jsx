// src/components/HiringAgencies.jsx
import React, { useState, useEffect, useRef } from "react";
import { useSelector, useDispatch } from "react-redux";
import { useSearchParams } from "react-router-dom";
import "./HiringAgency.css";
import { baseURL } from "../data";
import { API_ENDPOINTS } from "../config/api";
import { fetchCompanies } from "../redux/slices/companiesSlice";
import { fetchHiringAgencies } from "../redux/slices/hiringAgenciesSlice";
import { fetchRecruiters } from "../redux/slices/recruitersSlice";
import { fetchAdmins } from "../redux/slices/adminSlice"; // Import the dummy fetch for admins
import DataTable from "./common/DataTable";
import LoadingSpinner from "./common/LoadingSpinner";
import ContextMenu from "./common/ContextMenu";
import { FaSave, FaTimes, FaEdit, FaTrash } from "react-icons/fa";
import { FormModal, ConfirmModal } from "./common/Modal";
import { FiChevronDown } from 'react-icons/fi';
import { useNotification } from "../hooks/useNotification";
import CustomDropdown from './common/CustomDropdown';

const formInputStyle = {
  width: "100%",
  padding: "0.5rem 0.75rem",
  border: "1px solid var(--color-border)",
  borderRadius: "var(--radius-small)",
  fontSize: "0.9rem",
  backgroundColor: "var(--color-card)",
  color: "var(--color-text)",
  transition: "border-color 0.2s, box-shadow 0.2s",
};

const formInputFocusStyle = {
  outline: "none",
  borderColor: "var(--color-primary)",
  boxShadow: "0 0 0 2px rgba(127, 202, 146, 0.25)",
};

const actionButtonStyle = {
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  width: "32px",
  height: "32px",
  borderRadius: "var(--radius-small)",
  border: "1px solid var(--color-border)",
  cursor: "pointer",
  transition: "var(--transition)",
  fontSize: "14px",
  color: "var(--color-text)",
  backgroundColor: "var(--color-card)",
  "&:hover": {
    backgroundColor: "var(--color-hover)",
    boxShadow: "var(--shadow-button-hover)",
  },
  "&:focus": {
    outline: "none",
    boxShadow: "0 0 0 2px var(--color-primary)",
  },
};

const saveButtonStyle = {
  ...actionButtonStyle,
  backgroundColor: "var(--color-success)",
  color: "white",
  borderColor: "var(--color-success-dark)",
  "&:hover": {
    backgroundColor: "var(--color-success-dark)",
    borderColor: "var(--color-success-dark)",
    boxShadow: "var(--shadow-button-hover)",
  },
  "&:active": {
    transform: "translateY(1px)",
  },
};

const cancelButtonStyle = {
  ...actionButtonStyle,
  backgroundColor: "var(--color-card)",
  borderColor: "var(--color-border)",
  color: "var(--color-text-secondary)",
  "&:hover": {
    backgroundColor: "var(--color-hover)",
    borderColor: "var(--color-gray)",
    color: "var(--color-text)",
    boxShadow: "var(--shadow-button-hover)",
  },
  "&:active": {
    transform: "translateY(1px)",
  },
};

const buttonContainerStyle = {
  display: "flex",
  gap: "0.5rem",
  justifyContent: "center",
  alignItems: "center",
};

const HiringAgencies = () => {
  const dispatch = useDispatch();
  const notify = useNotification();
  const searchTerm = useSelector((state) => state.search?.searchTerm || '');
  
  const user = useSelector((state) => state.user?.user || null); // Get the full user object
  const userRole = user?.role; // Access the user's role from the Redux store
  const userCompany = user?.company_name; // Get the logged-in user's company name

  // Data from Redux slices with fallbacks to prevent selector warnings
  const companies = useSelector((state) => state.companies?.companies || []);
  const hiringAgencies = useSelector(
    (state) => state.hiringAgencies?.hiringAgencies || []
  );
  const recruiters = useSelector((state) => state.recruiters?.recruiters || []);
  const admins = useSelector((state) => state.admin?.admins || []); // Get admin dummy data

  // Debug data to see what fields are available

  // Loading and error states (can be combined for a single loading indicator if preferred)
  const companiesStatus = useSelector((state) => state.companies?.status || 'idle');
  const hiringAgenciesStatus = useSelector(
    (state) => state.hiringAgencies?.status || 'idle'
  );
  const recruitersStatus = useSelector((state) => state.recruiters?.status || 'idle');
  const adminStatus = useSelector((state) => state.admin?.status || 'idle');

  const [searchParams, setSearchParams] = useSearchParams();
  const [activeTab, setActiveTab] = useState(() => {
    // Try to get tab from URL parameters first
    const urlTab = searchParams.get('tab');
    if (urlTab) {
      return urlTab;
    }
    // Fall back to localStorage
    const savedTab = localStorage.getItem('hiringAgencyActiveTab');
    if (savedTab) {
      return savedTab;
    }
    // Default to 'Recruiter' tab
    return "Recruiter";
  });
  const [showMobileDropdown, setShowMobileDropdown] = useState(false);
  const mobileDropdownRef = useRef(null);

  // Context menu state
  const [contextMenu, setContextMenu] = useState({
    visible: false,
    x: 0,
    y: 0,
    rowData: null,
    rowIndex: null,
  });

  // DataTable edit state (Hiring Agency already has editingUserId and editedUserData)
  // We'll use the existing state for consistency
  
  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (mobileDropdownRef.current && !mobileDropdownRef.current.contains(event.target)) {
        setShowMobileDropdown(false);
      }
    };
    
    if (showMobileDropdown) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showMobileDropdown]);
  
  const [formData, setFormData] = useState({
    // Common fields
    username: "",
    full_name: "",
    email: "",
    password: "",
    role: "",
    
    // Company specific
    name: "",
    description: "",
    is_active: true,
    
    // Hiring Agency specific
    first_name: "",
    last_name: "",
    phone_number: "",
    linkedin_url: "",
    company_name: userRole === "COMPANY" ? userCompany : "",
    
    // Recruiter specific
    company_id: userRole === "COMPANY" ? (user?.company_id || user?.id || "") : "",
  });
  const [showAddModal, setShowAddModal] = useState(false);
  
  // Track modal state changes
  useEffect(() => {
    // Modal state changed
  }, [showAddModal]);
  
  // Track form data changes
  useEffect(() => {
    // Form data changed
  }, [formData]);
  const [editingUserId, setEditingUserId] = useState(null);
  const [editedUserData, setEditedUserData] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteUserId, setDeleteUserId] = useState(null);
  const [sortColumn, setSortColumn] = useState(null);
  const [sortDirection, setSortDirection] = useState("asc");
  // Pagination is now handled by DataTable component
  const [permissionError, setPermissionError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isDeleting, setIsDeleting] = useState(false);

  // Define tabs based on user role
  const getAvailableTabs = (role) => {
    const normalizedRole = String(role || "")
      .toLowerCase()
      .trim();
    if (normalizedRole === "admin") {
      return ["Recruiter", "Hiring Agency", "Company", "Admin"];
    } else if (normalizedRole === "company") {
      return ["Recruiter", "Hiring Agency"];
    } else if (normalizedRole === "hiring_agency") {
      return ["Recruiter"];
    }
    return [];
  };

  const availableTabs = getAvailableTabs(userRole);

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
      // Trigger DataTable's edit mode using existing state
      setEditingUserId(rowData.id);
      setEditedUserData({ ...rowData });
    } else if (action === "delete") {
      // Trigger delete confirmation modal instead of direct delete
      setDeleteUserId(rowData.id);
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

  // NEW: Define role options for the Add New User form based on user role
  const getRoleOptions = (role) => {
    const normalizedRole = role?.toUpperCase();
    if (normalizedRole === "ADMIN") {
      return [
        { value: "ADMIN", label: "Admin" },
        { value: "COMPANY", label: "Company" },
        { value: "Hiring Agency", label: "Hiring Agency" },
        { value: "RECRUITER", label: "Recruiter" },
      ];
    } else if (normalizedRole === "COMPANY") {
      return [
        { value: "Hiring Agency", label: "Hiring Agency" },
        { value: "RECRUITER", label: "Recruiter" },
      ];
    } else if (normalizedRole === "HIRING_AGENCY") {
      return [{ value: "RECRUITER", label: "Recruiter" }];
    }
    return [];
  };

  const roleOptions = getRoleOptions(userRole);

  // Function to handle tab changes with URL and localStorage persistence
  const handleTabChange = (newTab) => {
    setActiveTab(newTab);
    // Update URL parameters
    setSearchParams({ tab: newTab });
    // Update localStorage
    localStorage.setItem('hiringAgencyActiveTab', newTab);
  };

  // Set default tab based on available tabs
  useEffect(() => {
    if (availableTabs.length > 0 && !availableTabs.includes(activeTab)) {
      const defaultTab = availableTabs[0];
      handleTabChange(defaultTab);
    }
  }, [userRole, availableTabs, activeTab]);

  // Reset form data when tab changes (only when activeTab actually changes)
  useEffect(() => {
    setFormData({
      username: "",
      full_name: "",
      email: "",
      password: "",
      role: "",
      name: "",
      description: "",
      is_active: true,
      first_name: "",
      last_name: "",
      phone_number: "",
      linkedin_url: "",
      company_name: userRole === "COMPANY" ? userCompany : "",
      company_id: userRole === "COMPANY" ? (user?.company_id || user?.id || "") : "",
    });
  }, [activeTab, userRole, userCompany, user]); // Include user dependencies to update company_id


  // Handle search navigation to specific tab
  useEffect(() => {
    const highlightData = localStorage.getItem('searchHighlight');
    if (highlightData) {
      try {
        const parsed = JSON.parse(highlightData);
        if (parsed.type === 'Hiring Agencies' || parsed.type === 'Companies') {
        if (parsed.tab && availableTabs.includes(parsed.tab)) {
          handleTabChange(parsed.tab);
        }
          // Clear the highlight data after using it
          localStorage.removeItem('searchHighlight');
        }
      } catch (e) {
        // Error parsing search highlight
      }
    }
  }, [availableTabs]);

  // Function to get dynamic button text based on active tab
  const getAddButtonText = () => {
    switch (activeTab) {
      case "Recruiter":
        return "Add New Recruiter";
      case "Hiring Agency":
        return "Add New Agency";
      case "Company":
        return "Add New Company";
      case "Admin":
        return "Add New Admin";
      default:
        return "Add New User";
    }
  };

  // Function to get table columns based on active tab
  const getTableColumns = () => {
    switch (activeTab) {
      case "Company":
        return [
          {
            field: "name",
            header: "Name",
            width: "20%",
            editable: true,
          },
          {
            field: "email",
            header: "Email",
            width: "20%",
            editable: true,
          },
          {
            field: "description",
            header: "Description",
            width: "30%",
            editable: true,
          },
          {
            field: "is_active",
            header: "Status",
            width: "15%",
            type: "select",
            options: [
              { value: "true", label: "Active" },
              { value: "false", label: "Inactive" },
            ],
            parseFromEdit: (value) => value === "true",
            formatForEdit: (value) => value ? "true" : "false",
            render: (value) => (
              <span className="status-cell" data-status={value ? "active" : "inactive"}>
                {value ? "Active" : "Inactive"}
              </span>
            ),
            editable: true,
          },
        ];
      case "Hiring Agency":
        return [
          {
            field: "first_name",
            header: "First Name",
            width: "12%",
            editable: true,
          },
          {
            field: "last_name",
            header: "Last Name",
            width: "12%",
            editable: true,
          },
          {
            field: "email",
            header: "Email",
            width: "18%",
            editable: true,
          },
          {
            field: "phone_number",
            header: "Phone",
            width: "12%",
            editable: true,
          },
          {
            field: "company_name",
            header: "Company",
            width: "15%",
            editable: true,
          },
          {
            field: "role",
            header: "Role",
            width: "12%",
            editable: false,
            render: (value) => value || '-',
          },
          {
            field: "linkedin_url",
            header: "LinkedIn",
            width: "15%",
            editable: true,
          },
          {
            field: "status",
            header: "Status",
            width: "10%",
            type: "select",
            editable: true,
            options: [
              { value: "Active", label: "Active" },
              { value: "Inactive", label: "Inactive" },
            ],
            parseFromEdit: (value) => value,
            formatForEdit: (value) => value,
            render: (value) => (
              <span className="status-cell" data-status={value?.toLowerCase()}>
                {value || 'N/A'}
              </span>
            ),
          },
        ];
      case "Recruiter":
      case "Admin":
      default:
        return [
          {
            field: "full_name",
            header: "Full Name",
            width: "25%",
            editable: true,
            render: (value, rowData) => {
              // Handle different name field formats
              return value || `${rowData.first_name || ''} ${rowData.last_name || ''}`.trim() || rowData.name || rowData.username || '-';
            }
          },
          {
            field: "email",
            header: "Email",
            width: "25%",
            editable: true,
          },
          {
            field: "company_name",
            header: "Company",
            width: "20%",
            editable: false, // Make non-editable
          },
          {
            field: "role",
            header: "Role",
            width: "15%",
            editable: false, // Make non-editable
            render: (value) => value || '-',
          },
          {
            field: "is_active",
            header: "Active",
            width: "10%",
            type: "select",
            editable: true,
            options: [
              { value: "true", label: "Active" },
              { value: "false", label: "Inactive" },
            ],
            parseFromEdit: (value) => value === "true",
            formatForEdit: (value) => value ? "true" : "false",
            render: (value) => (
              <span className="status-cell" data-status={value ? "active" : "inactive"}>
                {value ? "Active" : "Inactive"}
              </span>
            ),
          },
        ];
    }
  };

  // Fetch data on component mount and when activeTab changes (if data isn't already loaded)
  useEffect(() => {
    // Only proceed if we have user data
    if (!user) {
      setIsLoading(false);
      return;
    }

    // Reset permission error first
    setPermissionError("");
    setIsLoading(true);

    // Normalize role for comparison (handle both 'hiring_agency' and 'hiring agency' formats)
    const normalizedRole = String(userRole || "")
      .toLowerCase()
      .trim()
      .replace(/ /g, "_");
    const allowedRoles = ["admin", "company", "hiring_agency"];

    if (!allowedRoles.includes(normalizedRole)) {
      setPermissionError("You do not have permission to access this page.");
      setIsLoading(false);
      return;
    }

    // Fetch data based on user role
    const fetchData = async () => {
      try {
        if (["admin", "company"].includes(normalizedRole)) {
          if (hiringAgenciesStatus === "idle") {
            await dispatch(fetchHiringAgencies()).unwrap();
          }
        }

        if (["admin", "company", "hiring_agency"].includes(normalizedRole)) {
          if (recruitersStatus === "idle") {
            await dispatch(fetchRecruiters());
          }
        }

        if (normalizedRole === "admin") {
          if (companiesStatus === "idle") {
            await dispatch(fetchCompanies());
          }
          if (adminStatus === "idle") {
            await dispatch(fetchAdmins());
          }
        } else if (normalizedRole === "company") {
          // Company users also need companies data to resolve company names for recruiters
          if (companiesStatus === "idle") {
            await dispatch(fetchCompanies());
          }
        }
      } catch (error) {
        setPermissionError("An error occurred while loading data.");
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [
    user,
    userRole,
    dispatch,
    hiringAgenciesStatus,
    recruitersStatus,
    companiesStatus,
    adminStatus,
  ]);

  // Determine the data to display based on the active tab
  const getCurrentTableData = () => {
    
    switch (activeTab) {
      case "Recruiter":
        // Map recruiter data to fit the table structure and resolve company names
        const recruiterData = (recruiters || []).map((recruiter) => {
          // Find company name by ID - ensure proper type comparison
          const company = companies.find(comp => String(comp.id) === String(recruiter.company));
          const companyName = company ? company.name : `Company ID: ${recruiter.company}`;
          
          
          return {
            id: recruiter.id,
            full_name: recruiter.full_name,
            email: recruiter.email,
            company_name: companyName,
            role: recruiter.role || recruiter.userType,
            is_active: recruiter.is_active,
          };
        });
        
        return recruiterData;
      case "Hiring Agency":
        // Map hiring agency data to include status field
        const hiringAgencyData = (hiringAgencies || []).map((agency) => ({
          ...agency,
          status: agency.is_active ? "Active" : "Inactive", // Convert boolean to string status
        }));
        return hiringAgencyData;
      case "Company":
        // Map company data to fit the table structure
        const companyData = (companies || []).map((company) => ({
          id: company.id,
          name: company.name,
          email: company.email, // Add email field
          description: company.description, // Use description for a relevant column
          is_active: company.is_active, // Use is_active for status
          status: company.is_active ? "Active" : "Inactive", // Convert boolean to string status
        }));
        return companyData;
      case "Admin":
        // Ensure admins is an array before returning
        return admins || [];
      default:
        return [];
    }
  };

  const currentTableData = getCurrentTableData();

  // Apply only company filter, not search term filter (search should sort, not filter)
  
  const filteredByCompany = currentTableData.filter((item) => {
    // Apply company name filter if logged-in user is a COMPANY
    const matchesCompany =
      userRole === "COMPANY"
        ? item.company_name?.toLowerCase() === userCompany?.toLowerCase()
        : true; // No company filter for ADMIN or other roles

    if (!matchesCompany) {
    }
    return matchesCompany;
  });
  

  const sortedUsers = [...filteredByCompany].sort((a, b) => {
    // First priority: search term relevance (if search term exists)
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      
      // Calculate relevance scores for both items - search ALL fields
      const getRelevanceScore = (item) => {
        let score = 0;
        
        // Search ALL fields in the item object dynamically
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
              searchValue = value.toLocaleDateString();
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
        
        searchAllFields(item);
        
        
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

    const aValue = a[sortColumn];
    const bValue = b[sortColumn];

    // Handle boolean for is_active in Company tab
    if (sortColumn === "is_active" && activeTab === "Company") {
      if (aValue === bValue) return 0;
      if (sortDirection === "asc") {
        return aValue ? -1 : 1; // true comes before false for asc
      } else {
        return aValue ? 1 : -1; // false comes before true for desc
      }
    }

    if (aValue < bValue) {
      return sortDirection === "asc" ? -1 : 1;
    }
    if (aValue > bValue) {
      return sortDirection === "asc" ? 1 : -1;
    }
    return 0;
  });


  // Effect to add/remove 'show' class for modal animations
  useEffect(() => {
    const addModalOverlay = document.querySelector(".add-agency-modal-overlay");

    if (addModalOverlay) {
      if (showAddModal) {
        addModalOverlay.classList.add("show");
      } else {
        addModalOverlay.classList.remove("show");
      }
    }

    // Delete confirmation modal is now handled by ConfirmModal component
  }, [showAddModal]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    
    // Prevent event bubbling to avoid any potential modal closing
    e.stopPropagation();
    
    setFormData((prevData) => {
      // Only update if the value actually changed
      if (prevData[name] === value) {
        return prevData;
      }
      
      const newData = {
        ...prevData,
        [name]: value,
      };
      return newData;
    });
  };

  // Helper function to add event protection to form elements
  const addEventProtection = (e) => {
    e.stopPropagation();
  };

  const handleAddUser = async (e) => {
    
    // Prevent default form submission if event exists
    if (e && e.preventDefault) {
      e.preventDefault();
    }
    
    
    let endpoint = "";
    let payload = {};
    let requiredFields = [];

    // Determine endpoint, payload, and validation based on active tab
    switch (activeTab) {
      case "Company":
        endpoint = `${baseURL}/api/companies/`;
        payload = {
          name: formData.name,
          email: formData.email,
          description: formData.description,
          is_active: formData.is_active,
          password: formData.password,
        };
        requiredFields = ["name", "email"];
        break;
        
      case "Hiring Agency":
        endpoint = `${baseURL}/api/hiring_agency/`;
        payload = {
          first_name: formData.first_name,
          last_name: formData.last_name,
          email: formData.email,
          phone_number: formData.phone_number,
          linkedin_url: formData.linkedin_url,
          role: "Hiring Agency",
        };
        
        // Handle company name based on user role
        if (userRole === "COMPANY") {
          // For company users, don't send company_name - it will be set automatically
        } else {
          // For admin users, send company_name as input_company_name
          payload.input_company_name = formData.company_name;
        }
        
        requiredFields = ["first_name", "last_name", "email", "phone_number"];
        break;
        
      case "Recruiter":
        endpoint = `${baseURL}/api/companies/recruiters/create/`;
        // For company users, we need to get the company_id from the user object
        // For other users, use the selected company_id from the form
        const recruiterCompanyId = userRole === "COMPANY" 
          ? (user?.company_id || user?.id || "") 
          : formData.company_id;
        
        
        payload = {
          username: formData.username || formData.email,
          full_name: formData.full_name,
          email: formData.email,
          password: formData.password,
          company_id: recruiterCompanyId,
        };
        requiredFields = ["full_name", "email", "password"];
        // Only require company_id for non-company users
        if (userRole !== "COMPANY") {
          requiredFields.push("company_id");
        }
        break;
        
      case "Admin":
        endpoint = API_ENDPOINTS.auth.register;
        payload = {
          username: formData.username || formData.email,
          email: formData.email,
          full_name: formData.full_name,
          role: "ADMIN",
          password: formData.password,
        };
        requiredFields = ["full_name", "email", "password"];
        break;
        
      default:
        notify.error("Invalid tab selected.");
        return;
    }


    
    // Validate required fields
    const missingFields = requiredFields.filter(field => !formData[field]);
    
    if (missingFields.length > 0) {
      notify.error(`Missing required fields: ${missingFields.join(", ")}`);
      return;
    }


    try {
      const token = localStorage.getItem("authToken");
      
      
      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Token ${token}`,
        },
        body: JSON.stringify(payload),
      });


      if (!response.ok) {
        const responseText = await response.text();
        
        let errorData;
        try {
          errorData = JSON.parse(responseText);
          
          // Handle validation errors with detailed messages
          const errorMessages = [];
          
          // Handle field-specific errors (both direct fields and nested errors)
          Object.entries(errorData).forEach(([field, messages]) => {
            // Skip non-error fields
            if (field === 'message' || field === 'detail') {
              return;
            }
            
            if (Array.isArray(messages)) {
              messages.forEach(msg => errorMessages.push(`${field}: ${msg}`));
            } else {
              errorMessages.push(`${field}: ${messages}`);
            }
          });
          
          // Handle non-field errors
          if (errorData.non_field_errors) {
            if (Array.isArray(errorData.non_field_errors)) {
              errorMessages.push(...errorData.non_field_errors);
            } else {
              errorMessages.push(errorData.non_field_errors);
            }
          }
          
          if (errorMessages.length > 0) {
            throw new Error(errorMessages.join('; '));
          }
          
          throw new Error(errorData.message || errorData.detail || "Failed to add user.");
        } catch (parseError) {
          // If it's HTML (like Django error page), try to extract useful info
          if (responseText.includes('IntegrityError')) {
            throw new Error("A user with this username or email already exists. Please use different credentials.");
          }
          throw new Error(`Server error (status ${response.status}). Please try again.`);
        }
      }

      const result = await response.json();
      
      const successMessage = activeTab === "Company" 
        ? `Company ${result.name} added successfully!`
        : `User ${result.full_name || result.name || `${result.first_name || ''} ${result.last_name || ''}`.trim() || 'Unknown'} added successfully!`;
      
      notify.success(successMessage);
      
      setShowAddModal(false);
      
      // Reset form data
      const resetFormData = {
        username: "",
        full_name: "",
        email: "",
        password: "",
        role: "",
        name: "",
        description: "",
        is_active: true,
        first_name: "",
        last_name: "",
        phone_number: "",
        linkedin_url: "",
        company_name: userRole === "COMPANY" ? userCompany : "",
        company_id: userRole === "COMPANY" ? (user?.company_id || user?.id || "") : "",
      };
      setFormData(resetFormData);
      
      // Re-fetch data for the active tab to update the table
      if (activeTab === "Recruiter") {
        dispatch(fetchRecruiters());
      } else if (activeTab === "Hiring Agency") {
        dispatch(fetchHiringAgencies());
      } else if (activeTab === "Company") {
        dispatch(fetchCompanies());
      } else if (activeTab === "Admin") {
        dispatch(fetchAdmins());
      }
      
    } catch (error) {
      // Handle error silently
      notify.error(error.message || "Failed to add user");
    }
  };

  const handleEditClick = (user) => {
    setEditingUserId(user.id);
    setEditedUserData({ ...user });
  };

  const handleEditedInputChange = (e) => {
    const { name, value } = e.target;
    setEditedUserData((prevData) => ({ ...prevData, [name]: value }));
  };

  const handleSaveEdit = async () => {
    if (!editedUserData || !editingUserId) {
      return;
    }

    // Find the original user data
    const originalUser = sortedUsers.find(
      (user) => user.id === editingUserId
    );

    // Check if there are any changes
    const hasChanges = Object.keys(editedUserData).some((key) => {
      // Special handling for status vs is_active
      if (key === "status") {
        const newStatus = editedUserData[key]?.toLowerCase() === "active";
        return originalUser.is_active !== newStatus;
      }
      // Special handling for full_name vs name
      if (key === "full_name") {
        return originalUser.full_name !== editedUserData[key];
      }
      return originalUser[key] !== editedUserData[key];
    });

    if (!hasChanges) {
      notify.info("No changes detected.");
      setEditingUserId(null);
      setEditedUserData(null);
      return;
    }

    try {
      let endpoint = "";
      let payload = {};
      const token = localStorage.getItem("authToken");

      // Determine endpoint and payload based on active tab
      switch (activeTab) {
        case "Recruiter":
          endpoint = `${baseURL}/api/companies/recruiters/${editedUserData.id}/`;
          payload = {
            new_full_name: editedUserData.full_name || editedUserData.name,
            new_email: editedUserData.email,
            is_active: editedUserData.is_active !== undefined ? editedUserData.is_active : (editedUserData.status?.toLowerCase() === "active"),
          };
          break;
        case "Hiring Agency":
          endpoint = `${baseURL}/api/hiring_agency/${editedUserData.id}/`;
          payload = {
            name: editedUserData.name,
            email: editedUserData.email,
            is_active: editedUserData.status?.toLowerCase() === "active",
          };
          break;
        case "Company":
          endpoint = `${baseURL}/api/companies/${editedUserData.id}/`;
          payload = {
            name: editedUserData.name,
            description: editedUserData.description,
            is_active: editedUserData.status?.toLowerCase() === "active",
          };
          break;
        case "Admin":
          endpoint = `${baseURL}/api/admins/${editedUserData.id}/`;
          payload = {
            name: editedUserData.name,
            email: editedUserData.email,
            is_active: editedUserData.status?.toLowerCase() === "active",
          };
          break;
        default:
          throw new Error("Invalid user type");
      }


      const response = await fetch(endpoint, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Token ${token}`,
        },
        body: JSON.stringify(payload),
      });

      const responseData = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(responseData.detail || "Failed to update user");
      }
      
      // Refresh the data after successful update
      if (activeTab === "Recruiter") {
        dispatch(fetchRecruiters());
      } else if (activeTab === "Hiring Agency") {
        dispatch(fetchHiringAgencies());
      } else if (activeTab === "Company") {
        dispatch(fetchCompanies());
      } else if (activeTab === "Admin") {
        dispatch(fetchAdmins());
      }

      setEditingUserId(null);
      setEditedUserData(null);
      notify.success("User updated successfully!");
    } catch (error) {
      notify.error(error.message || "Failed to update user");
    }
  };

  const handleCancelEdit = () => {
    setEditingUserId(null);
    setEditedUserData(null);
  };

  const handleViewClick = (user) => {
    notify.info(`Viewing user: ${user.name} (${user.email})`, "User Details");
  };

  const handleDeleteClick = (userId) => {
    // If userId is an event object (from context menu), get the user ID from data attribute
    if (userId && typeof userId === "object" && userId.preventDefault) {
      userId.preventDefault();
      const userIdFromMenu = userId.currentTarget?.getAttribute("data-userid");
      if (userIdFromMenu) {
        setDeleteUserId(userIdFromMenu);
        setShowDeleteConfirm(true);
      }
    } else {
      // Handle regular button click
      setDeleteUserId(userId);
      setShowDeleteConfirm(true);
    }
  };

  const confirmDelete = async () => {

    if (!deleteUserId) {
      return;
    }
    setIsDeleting(true);

    try {
      let endpoint = "";
      const token = localStorage.getItem("authToken");

      // Determine endpoint based on active tab
      switch (activeTab) {
        case "Recruiter":
          endpoint = `${baseURL}/api/companies/recruiters/${deleteUserId}/`;
          break;
        case "Hiring Agency":
          endpoint = `${baseURL}/api/hiring_agency/${deleteUserId}/`;
          break;
        case "Company":
          endpoint = `${baseURL}/api/companies/${deleteUserId}/`;
          break;
        default:
          throw new Error("Invalid tab for delete operation.");
      }
      const response = await fetch(endpoint, {
        method: "DELETE",
        headers: {
          Authorization: `Token ${token}`,
          "Content-Type": "application/json",
        },
      });


      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
          `Failed to delete user: ${response.status} - ${errorText}`
        );
      }

      // Refresh the data after successful deletion
      const fetchPromises = [];

      if (activeTab === "Recruiter") {
        fetchPromises.push(dispatch(fetchRecruiters()));
      } else if (activeTab === "Hiring Agency") {
        fetchPromises.push(dispatch(fetchHiringAgencies()));
      } else if (activeTab === "Company") {
        fetchPromises.push(dispatch(fetchCompanies()));
      }

      // Wait for all fetches to complete
      await Promise.all(fetchPromises);

      notify.success("User deleted successfully!");
    } catch (error) {
      notify.error(error.message || "Failed to delete user");
    } finally {
      setIsDeleting(false);
      setShowDeleteConfirm(false);
      setDeleteUserId(null);
    }
  };

  const cancelDelete = () => {
    setShowDeleteConfirm(false);
    setDeleteUserId(null);
    setIsDeleting(false);
  };

  // New function for DataTable edit integration
  const handleUpdateUser = async (editedData) => {
    if (!editedData || !editedData.id) {
      throw new Error("Invalid data provided for update");
    }

    // Find the original user data
    const originalUser = sortedUsers.find(
      (user) => user.id === editedData.id
    );

    // Check if there are any changes
    const hasChanges = Object.keys(editedData).some((key) => {
      // Special handling for status vs is_active
      if (key === "status") {
        const newStatus = editedData[key]?.toLowerCase() === "active";
        return originalUser.is_active !== newStatus;
      }
      // Special handling for full_name vs name
      if (key === "full_name") {
        return originalUser.full_name !== editedData[key];
      }
      // Special handling for hiring agency fields
      if (activeTab === "Hiring Agency") {
        if (key === "first_name" || key === "last_name" || key === "phone_number" || key === "linkedin_url") {
          return originalUser[key] !== editedData[key];
        }
      }
      // Special handling for company fields
      if (activeTab === "Company") {
        if (key === "email" || key === "description") {
          return originalUser[key] !== editedData[key];
        }
      }
      return originalUser[key] !== editedData[key];
    });

    if (!hasChanges) {
      notify.info("No changes detected.");
      return;
    }

    try {
      let endpoint = "";
      let payload = {};
      const token = localStorage.getItem("authToken");

      // Determine endpoint and payload based on active tab
      switch (activeTab) {
        case "Recruiter":
          endpoint = `${baseURL}/api/companies/recruiters/${editedData.id}/`;
          payload = {
            new_full_name: editedData.full_name || editedData.name,
            new_email: editedData.email,
            is_active: editedData.is_active !== undefined ? editedData.is_active : (editedData.status?.toLowerCase() === "active"),
          };
          break;
        case "Hiring Agency":
          endpoint = `${baseURL}/api/hiring_agency/${editedData.id}/`;
          payload = {
            first_name: editedData.first_name,
            last_name: editedData.last_name,
            email: editedData.email,
            phone_number: editedData.phone_number,
            linkedin_url: editedData.linkedin_url,
            is_active: editedData.status?.toLowerCase() === "active",
          };
          break;
        case "Company":
          endpoint = `${baseURL}/api/companies/${editedData.id}/`;
          payload = {
            name: editedData.name,
            email: editedData.email,
            description: editedData.description,
            is_active: editedData.is_active !== undefined ? editedData.is_active : (editedData.status?.toLowerCase() === "active"),
          };
          break;
        case "Admin":
          endpoint = `${baseURL}/api/admins/${editedData.id}/`;
          payload = {
            name: editedData.name,
            email: editedData.email,
            is_active: editedData.status?.toLowerCase() === "active",
          };
          break;
        default:
          throw new Error("Invalid user type");
      }

      const response = await fetch(endpoint, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Token ${token}`,
        },
        body: JSON.stringify(payload),
      });

      const responseData = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(responseData.detail || "Failed to update user");
      }

      // Refresh the data after successful update
      if (activeTab === "Recruiter") dispatch(fetchRecruiters());
      else if (activeTab === "Hiring Agency") dispatch(fetchHiringAgencies());
      else if (activeTab === "Company") dispatch(fetchCompanies());
      else if (activeTab === "Admin") dispatch(fetchAdmins());

      notify.success("User updated successfully!");
    } catch (error) {
      notify.error(error.message || "Failed to update user");
      throw error; // Re-throw so DataTable can handle the error
    }
  };

  // New function for DataTable delete integration
  const handleDeleteUser = async (userId) => {

    if (!userId) {
      throw new Error("No user ID provided");
    }

    try {
      let endpoint = "";
      const token = localStorage.getItem("authToken");

      // Determine endpoint based on active tab
      switch (activeTab) {
        case "Recruiter":
          endpoint = `${baseURL}/api/companies/recruiters/${userId}/`;
          break;
        case "Hiring Agency":
          endpoint = `${baseURL}/api/hiring_agency/${userId}/`;
          break;
        case "Company":
          endpoint = `${baseURL}/api/companies/${userId}/`;
          break;
        default:
          throw new Error("Invalid tab for delete operation.");
      }

      const response = await fetch(endpoint, {
        method: "DELETE",
        headers: {
          Authorization: `Token ${token}`,
          "Content-Type": "application/json",
        },
      });


      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
          `Failed to delete user: ${response.status} - ${errorText}`
        );
      }

      // Refresh the data after successful deletion
      const fetchPromises = [];

      if (activeTab === "Recruiter") {
        fetchPromises.push(dispatch(fetchRecruiters()));
      } else if (activeTab === "Hiring Agency") {
        fetchPromises.push(dispatch(fetchHiringAgencies()));
      } else if (activeTab === "Company") {
        fetchPromises.push(dispatch(fetchCompanies()));
      }

      // Wait for all fetches to complete
      await Promise.all(fetchPromises);

      notify.success("User deleted successfully!");
    } catch (error) {
      notify.error(error.message || "Failed to delete user");
      throw error; // Re-throw so DataTable can handle the error
    }
  };

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

  const getStatusBadgeClass = (status) => {
    switch (status?.toLowerCase()) {
      case "active":
        return "status-badge active";
      case "inactive":
        return "status-badge inactive";
      case "on hold":
        return "status-badge on-hold";
      default:
        return "status-badge";
    }
  };

  // Function to render form fields based on active tab
  const renderFormFields = () => {
    switch (activeTab) {
      case "Company":
        return (
          <>
            <div className="form-group">
              <label htmlFor="name">Company Name *</label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                onClick={addEventProtection}
                onFocus={addEventProtection}
                onMouseDown={addEventProtection}
                required
                placeholder="Enter company name"
              />
            </div>

            <div className="form-group">
              <label htmlFor="email">Email *</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                onClick={addEventProtection}
                onFocus={addEventProtection}
                onMouseDown={addEventProtection}
                required
                placeholder="Enter company email"
              />
            </div>

            <div className="form-group">
              <label htmlFor="description">Description</label>
              <textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                onClick={addEventProtection}
                onFocus={addEventProtection}
                onMouseDown={addEventProtection}
                placeholder="Enter company description"
                rows="3"
              />
            </div>

            <div className="form-group">
              <label htmlFor="is_active">Status</label>
              <CustomDropdown
                value={formData.is_active ? "true" : "false"}
                options={[
                  { value: 'true', label: 'Active' },
                  { value: 'false', label: 'Inactive' }
                ]}
                onChange={(value) => setFormData(prev => ({ ...prev, is_active: value === "true" }))}
                placeholder="Select Status"
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                placeholder="Enter password (optional)"
              />
            </div>
          </>
        );

      case "Hiring Agency":
        return (
          <>
            <div className="form-group">
              <label htmlFor="first_name">First Name *</label>
              <input
                type="text"
                id="first_name"
                name="first_name"
                value={formData.first_name}
                onChange={handleInputChange}
                required
                placeholder="Enter first name"
              />
            </div>

            <div className="form-group">
              <label htmlFor="last_name">Last Name *</label>
              <input
                type="text"
                id="last_name"
                name="last_name"
                value={formData.last_name}
                onChange={handleInputChange}
                required
                placeholder="Enter last name"
              />
            </div>

            <div className="form-group">
              <label htmlFor="email">Email *</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                required
                placeholder="Enter email address"
              />
            </div>

            <div className="form-group">
              <label htmlFor="phone_number">Phone Number *</label>
              <input
                type="tel"
                id="phone_number"
                name="phone_number"
                value={formData.phone_number}
                onChange={handleInputChange}
                required
                placeholder="Enter phone number"
              />
            </div>

            <div className="form-group">
              <label htmlFor="linkedin_url">LinkedIn URL</label>
              <input
                type="url"
                id="linkedin_url"
                name="linkedin_url"
                value={formData.linkedin_url}
                onChange={handleInputChange}
                placeholder="Enter LinkedIn profile URL"
              />
            </div>

            {/* Company Name field - only show for non-company users */}
            {userRole !== "COMPANY" && (
              <div className="form-group">
                <label htmlFor="company_name">Company Name</label>
                <input
                  type="text"
                  id="company_name"
                  name="company_name"
                  value={formData.company_name}
                  onChange={handleInputChange}
                  placeholder="Enter company name"
                />
              </div>
            )}
          </>
        );

      case "Recruiter":
        return (
          <>
            <div className="form-group">
              <label htmlFor="full_name">Full Name *</label>
              <input
                type="text"
                id="full_name"
                name="full_name"
                value={formData.full_name}
                onChange={handleInputChange}
                onClick={addEventProtection}
                onFocus={addEventProtection}
                onMouseDown={addEventProtection}
                required
                placeholder="Enter full name"
              />
            </div>

            <div className="form-group">
              <label htmlFor="email">Email *</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                onClick={addEventProtection}
                onFocus={addEventProtection}
                onMouseDown={addEventProtection}
                required
                placeholder="Enter email address"
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Password *</label>
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                onClick={addEventProtection}
                onFocus={addEventProtection}
                onMouseDown={addEventProtection}
                required
                placeholder="Enter password"
              />
            </div>

            <div className="form-group">
              <label htmlFor="username">Username</label>
              <input
                type="text"
                id="username"
                name="username"
                value={formData.username}
                onChange={handleInputChange}
                onClick={addEventProtection}
                onFocus={addEventProtection}
                onMouseDown={addEventProtection}
                placeholder="Enter username (optional, defaults to email)"
              />
            </div>

            {/* Company field - only show for non-company users */}
            {userRole !== "COMPANY" && (
              <div className="form-group">
                <label htmlFor="company_id">Company</label>
                <CustomDropdown
                  value={formData.company_id}
                  options={[
                    { value: '', label: 'Select a company' },
                    ...companies.map(company => ({ value: company.id, label: company.name }))
                  ]}
                  onChange={(value) => handleInputChange({ target: { name: 'company_id', value } })}
                  placeholder="Select a company"
                />
              </div>
            )}
          </>
        );

      case "Admin":
        return (
          <>
            <div className="form-group">
              <label htmlFor="full_name">Full Name *</label>
              <input
                type="text"
                id="full_name"
                name="full_name"
                value={formData.full_name}
                onChange={handleInputChange}
                required
                placeholder="Enter full name"
              />
            </div>

            <div className="form-group">
              <label htmlFor="email">Email *</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                required
                placeholder="Enter email address"
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Password *</label>
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                required
                placeholder="Enter password"
              />
            </div>

            <div className="form-group">
              <label htmlFor="username">Username</label>
              <input
                type="text"
                id="username"
                name="username"
                value={formData.username}
                onChange={handleInputChange}
                placeholder="Enter username (optional, defaults to email)"
              />
            </div>
          </>
        );

      default:
        return null;
    }
  };

  // If user doesn't have permission, show access denied
  const normalizedUserRole = String(userRole || "")
    .toLowerCase()
    .trim()
    .replace(/ /g, "_");
  const allowedRoles = ["admin", "company", "hiring_agency"];

  if (!allowedRoles.includes(normalizedUserRole)) {
    return (
      <div className="hiring-agencies-container">
        <div className="permission-denied">
          <h2>Access Denied</h2>
          <p>You do not have permission to access this page.</p>
          <p>
            Please contact your administrator if you believe this is an error.
          </p>
        </div>
      </div>
    );
  }

  // Define table headers based on the active tab
  const getTableHeaders = () => {
    if (activeTab === "Company") {
      return (
        <tr>
          <th>Name</th><th>Description</th><th>Status</th><th className="text-center">Actions</th>
        </tr>
      );
    } else if (activeTab === "Hiring Agency") {
      return (
        <tr>
          <th>Name</th><th>Email</th><th>Phone</th><th>Company Name</th><th>Role</th><th>Status</th><th>Permission Granted</th><th className="text-center">Actions</th>
        </tr>
      );
    } else {
      // Default for Recruiter and Admin
      return (
        <tr>
          <th>Name</th><th>Email</th><th>Status</th><th>Role</th><th className="text-center">Actions</th>
        </tr>
      );
    }
  };

  // Define table rows based on the active tab
  const renderTableRows = () => {
    if (isLoading) {
      return (
        <tr>
          <td colSpan="100%" className="text-center py-8">
            <div className="flex justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
            </div>
          </td>
        </tr>
      );
    }

    if (sortedUsers.length === 0) {
      return (
        <tr>
          <td colSpan="100%" className="text-center py-8 text-gray-500">
            No {activeTab.toLowerCase()} found
          </td>
        </tr>
      );
    }

    return sortedUsers.map((item) => (
      <tr key={item.id}>
        {editingUserId === item.id ? (
          // Edit Mode
          <>
            {activeTab === "Company" ? (
              <>
                <td>
                  <input
                    type="text"
                    name="name"
                    value={editedUserData?.name || ""}
                    onChange={handleEditedInputChange}
                    style={formInputStyle}
                    className="form-input"
                  />
                </td>
                <td>
                  <input
                    type="text"
                    name="description"
                    value={editedUserData?.description || ""}
                    onChange={handleEditedInputChange}
                    style={formInputStyle}
                    className="form-input"
                  />
                </td>
                <td>
                  <select
                    name="is_active"
                    value={editedUserData?.is_active || false}
                    onChange={(e) =>
                      setEditedUserData((prev) => ({
                        ...prev,
                        is_active: e.target.value === "true",
                      }))
                    }
                    style={formInputStyle}
                    className="form-input"
                  >
                    <option value={true}>Active</option>
                    <option value={false}>Inactive</option>
                  </select>
                </td>
              </>
            ) : activeTab === "Hiring Agency" ? (
              <>
                <td>
                  <input
                    type="text"
                    name="name"
                    value={editedUserData?.name || ""}
                    onChange={handleEditedInputChange}
                    style={formInputStyle}
                    className="form-input"
                  />
                </td>
                <td>
                  <input
                    type="email"
                    name="email"
                    value={editedUserData?.email || ""}
                    onChange={handleEditedInputChange}
                    style={formInputStyle}
                    className="form-input"
                  />
                </td>
                <td>
                  <input
                    type="tel"
                    name="phone"
                    value={editedUserData?.phone || ""}
                    onChange={handleEditedInputChange}
                    style={formInputStyle}
                    className="form-input"
                  />
                </td>
                <td>
                  <input
                    type="text"
                    name="company_name"
                    value={editedUserData?.company_name || ""}
                    onChange={handleEditedInputChange}
                    style={formInputStyle}
                    className="form-input"
                  />
                </td>
                <td>{item.role}</td>
                <td>
                  <select
                    name="status"
                    value={editedUserData?.status || "Active"}
                    onChange={handleEditedInputChange}
                    style={formInputStyle}
                    className="form-input"
                  >
                    <option value="Active">Active</option>
                    <option value="Inactive">Inactive</option>
                  </select>
                </td>
                <td>{item.lastUpdated || "-"}</td>
              </>
            ) : (
              // Default for Recruiter and Admin
              <>
                <td>
                  <input
                    type="text"
                    name="full_name"
                    value={editedUserData?.full_name || editedUserData?.name || ""}
                    onChange={handleEditedInputChange}
                    style={formInputStyle}
                    className="form-input"
                  />
                </td>
                <td>
                  <input
                    type="email"
                    name="email"
                    value={editedUserData?.email || ""}
                    onChange={handleEditedInputChange}
                    style={formInputStyle}
                    className="form-input"
                  />
                </td>
                <td>
                  <select
                    name="is_active"
                    value={editedUserData?.is_active !== undefined ? editedUserData.is_active : (editedUserData?.status?.toLowerCase() === "active")}
                    onChange={(e) =>
                      setEditedUserData((prev) => ({
                        ...prev,
                        is_active: e.target.value === "true",
                      }))
                    }
                    style={formInputStyle}
                    className="form-input"
                  >
                    <option value={true}>Active</option>
                    <option value={false}>Inactive</option>
                  </select>
                </td>
                <td>{item.role}</td>
              </>
            )}
            <td className="action-menu">
              <div className="action-buttons">
                <button
                  onClick={handleSaveEdit}
                  className="action-button save"
                  title="Save changes"
                >
                  <FaSave />
                </button>
                <button
                  onClick={handleCancelEdit}
                  className="action-button cancel"
                  title="Cancel"
                >
                  <FaTimes />
                </button>
              </div>
            </td>
          </>
        ) : (
          // View Mode
          <>
            {activeTab === "Company" ? (
              <>
                <td>{item.name}</td>
                <td>{item.description || "-"}</td>
                <td>
                  <span className={getStatusBadgeClass(item.status)}>
                    {item.status}
                  </span>
                </td>
              </>
            ) : activeTab === "Hiring Agency" ? (
              <>
                <td>{item.name}</td>
                <td>{item.email}</td>
                <td>{item.phone || "-"}</td>
                <td>{item.company_name || "-"}</td>
                <td>{item.role}</td>
                <td>
                  <span
                    className={`status-badge ${
                      item.status === "Active"
                        ? "status-active"
                        : "status-inactive"
                    }`}
                  >
                    {item.status}
                  </span>
                </td>
                <td>{item.lastUpdated || "-"}</td>
              </>
            ) : (
              // Default for Recruiter and Admin
              <>
                <td>{item.full_name || item.name}</td>
                <td>{item.email}</td>
                <td>
                  <span
                    className={`status-badge ${
                      item.is_active ? "status-active" : "status-inactive"
                    }`}
                  >
                    {item.is_active ? "Active" : "Inactive"}
                  </span>
                </td>
                <td>{item.role}</td>
              </>
            )}
            <td>
              <div className="action-buttons">
                <button
                  onClick={() => handleViewClick(item)}
                  className="action-button"
                  title="View"
                  style={{
                    width: "32px",
                    height: "32px",
                    padding: "0.5rem",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    margin: "0 2px"
                  }}
                >
                  <FaEye />
                </button>
                <button
                  onClick={() => handleEditClick(item)}
                  className="action-button"
                  title="Edit"
                  style={{
                    width: "32px",
                    height: "32px",
                    padding: "0.5rem",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    margin: "0 2px"
                  }}
                >
                  <FaEdit />
                </button>
                <button
                  onClick={() => handleDeleteClick(item.id)}
                  className="action-button"
                  title="Delete"
                  style={{
                    width: "32px",
                    height: "32px",
                    padding: "0.5rem",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    margin: "0 2px"
                  }}
                >
                  <FaTrash />
                </button>
              </div>
            </td>
          </>
        )}
      </tr>
    ));
  };

  // Check if any modal is open for blur effect
  const isAnyModalOpen = showAddModal || showDeleteConfirm;

  return (
    <>
      <div className={`hiring-agencies-container ${isAnyModalOpen ? 'blur-background' : ''}`}>
      <div className="hiring-agencies-card">
        {/* Tabs */}
        <div className="hiring-agencies-tabs-container">
          {/* Desktop Tabs */}
          <div className="hiring-agency-tabs desktop-tabs">
            {availableTabs.map((tab) => (
              <button
                key={tab}
                className={`hiring-agency-tab ${
                  activeTab === tab ? "active" : ""
                }`}
                onClick={() => handleTabChange(tab)}
                disabled={isLoading}
              >
                {tab}
              </button>
            ))}
          </div>
          
          {/* Mobile Custom Dropdown Selector */}
          <div className="mobile-tab-selector" ref={mobileDropdownRef}>
            <button
              className={`tab-dropdown-button ${showMobileDropdown ? 'open' : ''}`}
              onClick={() => !isLoading && setShowMobileDropdown(!showMobileDropdown)}
              disabled={isLoading}
            >
              <span className="dropdown-selected-text">{activeTab}</span>
              <FiChevronDown className={`dropdown-icon ${showMobileDropdown ? 'open' : ''}`} />
            </button>
            
            {showMobileDropdown && !isLoading && (
              <div className="tab-dropdown-menu">
                {availableTabs.map((tab) => (
                  <button
                    key={tab}
                    type="button"
                    className={`tab-dropdown-item ${activeTab === tab ? 'active' : ''}`}
                    onClick={() => {
                      handleTabChange(tab);
                      setShowMobileDropdown(false);
                    }}
                  >
                    {tab}
                  </button>
                ))}
              </div>
            )}
          </div>
          
          {/* Dynamic "Add New" button visible only for ADMIN or COMPANY */}
          {["ADMIN", "COMPANY"].includes(userRole) && (
            <button
              className="add-agency-btn"
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                setShowAddModal(true);
              }}
              disabled={isLoading}
            >
              {getAddButtonText()}
            </button>
          )}
        </div>

      {/* DataTable */}
      <DataTable
        title={
          activeTab === "Recruiter"
                ? "Recruiters"
                : activeTab === "Hiring Agency"
                ? "Hiring Agencies"
                : activeTab === "Company"
                ? "Companies"
            : "Admins"
        }
        columns={getTableColumns()}
        data={sortedUsers || []}
        loading={isLoading}
        actions={["edit", "delete"]}
        onEdit={handleUpdateUser}
        onAction={(action, rowData, rowIndex) => {
          if (action === "edit") {
            setEditingUserId(rowData.id);
            setEditedUserData({ ...rowData });
          } else if (action === "delete") {
            // Handle delete directly with API call
            handleDeleteUser(rowData.id);
          }
        }}
        onContextMenuClick={handleContextMenuClick}
        editingRow={editingUserId !== null ? sortedUsers.findIndex(item => item.id === editingUserId) : null}
        editingData={editedUserData}
        setEditingRow={(rowIndex) => {
          if (rowIndex === null) {
            setEditingUserId(null);
            setEditedUserData(null);
          } else {
            const user = sortedUsers[rowIndex];
            setEditingUserId(user.id);
            setEditedUserData({ ...user });
          }
        }}
        setEditingData={setEditedUserData}
        showRefresh={true}
        onRefresh={async () => {
          // Set loading state during refresh
          setIsLoading(true);
          
          try {
            // Refresh data based on active tab
            if (activeTab === "Recruiter") {
              await dispatch(fetchRecruiters()).unwrap();
            } else if (activeTab === "Hiring Agency") {
              await dispatch(fetchHiringAgencies()).unwrap();
            } else if (activeTab === "Company") {
              await dispatch(fetchCompanies()).unwrap();
            } else if (activeTab === "Admin") {
              await dispatch(fetchAdmins()).unwrap();
            }
            
            // Also refresh companies data for company users to ensure company names are resolved
            if (userRole === "COMPANY" && companiesStatus !== "loading") {
              await dispatch(fetchCompanies()).unwrap();
            }
            
            notify.success("Data refreshed successfully!");
          } catch (error) {
            notify.error("Failed to refresh data. Please try again.");
          } finally {
            setIsLoading(false);
          }
        }}
        showActions={true}
        defaultPageSize={10}
        pageSizeOptions={[10, 25, 50, 100]}
        editingRow={editingUserId !== null ? sortedUsers.findIndex(item => item.id === editingUserId) : null}
        editingData={editedUserData}
        setEditingRow={(rowIndex) => {
          if (rowIndex === null) {
            setEditingUserId(null);
            setEditedUserData(null);
          } else {
            const item = sortedUsers[rowIndex];
            setEditingUserId(item?.id || null);
            setEditedUserData(item ? { ...item } : null);
          }
        }}
        setEditingData={setEditedUserData}
      />

              </div>


              </div>

      {/* Modals outside the main container to avoid blur effect */}
      <FormModal
        isOpen={showAddModal}
        onClose={() => {
          setShowAddModal(false);
        }}
        onSubmit={(e) => {
          handleAddUser(e);
        }}
        title={getAddButtonText()}
        submitText={activeTab === "Company" ? "Add Company" : "Add User"}
        size="medium"
      >
        {renderFormFields()}
      </FormModal>

      {/* Delete Confirmation Modal */}
      <ConfirmModal
        isOpen={showDeleteConfirm}
        onClose={cancelDelete}
        onConfirm={confirmDelete}
        title="Delete User"
        message="Are you sure you want to delete this user? This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
        isLoading={isDeleting}
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

export default HiringAgencies;
