// API Configuration for different environments
import { baseURL } from './constants';

export const API_ENDPOINTS = {
  base: baseURL,
  
  // Authentication
  auth: {
    login: `${baseURL}/api/auth/login/`,
    register: `${baseURL}/api/auth/register/`,
    logout: `${baseURL}/api/auth/logout/`,
    refresh: `${baseURL}/api/auth/refresh/`,
    profile: `${baseURL}/api/auth/profile/`,
  },
  
  // Candidates
  candidates: {
    list: `${baseURL}/api/candidates/`,
    create: `${baseURL}/api/candidates/`,
    detail: (id) => `${baseURL}/api/candidates/${id}/`,
    update: (id) => `${baseURL}/api/candidates/${id}/`,
    delete: (id) => `${baseURL}/api/candidates/${id}/`,
  },
  
  // Jobs
  jobs: {
    list: `${baseURL}/api/jobs/`,
    create: `${baseURL}/api/jobs/`,
    detail: (id) => `${baseURL}/api/jobs/${id}/`,
    update: (id) => `${baseURL}/api/jobs/${id}/`,
    delete: (id) => `${baseURL}/api/jobs/${id}/`,
  },
  
  // Interviews
  interviews: {
    list: `${baseURL}/api/interviews/`,
    create: `${baseURL}/api/interviews/`,
    detail: (id) => `${baseURL}/api/interviews/${id}/`,
    update: (id) => `${baseURL}/api/interviews/${id}/`,
    delete: (id) => `${baseURL}/api/interviews/${id}/`,
    schedule: `${baseURL}/api/interviews/schedule/`,
    slots: `${baseURL}/api/interviews/slots/`,
  },
  
  // AI Interview
  aiInterview: {
    session: (sessionKey) => `${baseURL}/interview_app/?session_key=${sessionKey}`,
    questions: `${baseURL}/interview_app/get_questions/`,
    submitAnswer: `${baseURL}/interview_app/submit_answer/`,
    completeInterview: `${baseURL}/interview_app/complete_interview/`,
    results: (sessionId) => `${baseURL}/interview_app/results/${sessionId}/`,
  },
  
  // Dashboard
  dashboard: {
    stats: `${baseURL}/api/dashboard/stats/`,
    analytics: `${baseURL}/api/dashboard/analytics/`,
  },
  
  // Hiring Agencies
  hiringAgencies: {
    list: `${baseURL}/api/hiring_agency/`,
    create: `${baseURL}/api/hiring_agency/`,
    detail: (id) => `${baseURL}/api/hiring_agency/${id}/`,
    update: (id) => `${baseURL}/api/hiring_agency/${id}/`,
    delete: (id) => `${baseURL}/api/hiring_agency/${id}/`,
  },
  
  // Companies
  companies: {
    list: `${baseURL}/api/companies/`,
    create: `${baseURL}/api/companies/`,
    detail: (id) => `${baseURL}/api/companies/${id}/`,
    update: (id) => `${baseURL}/api/companies/${id}/`,
    delete: (id) => `${baseURL}/api/companies/${id}/`,
  },
  
  // Resumes
  resumes: {
    list: `${baseURL}/api/resumes/`,
    upload: `${baseURL}/api/resumes/upload/`,
    detail: (id) => `${baseURL}/api/resumes/${id}/`,
    delete: (id) => `${baseURL}/api/resumes/${id}/`,
  },
  
  // Notifications
  notifications: {
    list: `${baseURL}/api/notifications/`,
    markRead: (id) => `${baseURL}/api/notifications/${id}/mark_read/`,
    markAllRead: `${baseURL}/api/notifications/mark_all_read/`,
  },
};

// API request helper
export const apiRequest = async (url, options = {}) => {
  // Support both keys to avoid login/header mismatch
  const token = localStorage.getItem('authToken') || localStorage.getItem('token');
  
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Token ${token}` }),
      ...options.headers,
    },
  };
  
  const response = await fetch(url, { ...defaultOptions, ...options });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Network error' }));
    throw new Error(error.message || `HTTP error! status: ${response.status}`);
  }
  
  // Gracefully handle empty responses (e.g., 204 No Content)
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    return null;
  }
  return response.json();
};

// Environment detection
export const isProduction = import.meta.env.PROD;
export const isDevelopment = import.meta.env.DEV;

// Log API configuration in development
