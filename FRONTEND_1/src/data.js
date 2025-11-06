// src/data.js
import { baseURL } from './config/constants.js';

export { baseURL };

export const candidateDomains = [
];

export const candidateJobRoles = [
];

export const candidateStatusList = [
];

// These will now be populated dynamically from API
export const uniqueCandidateDomains = [];
export const uniqueCandidateJobRoles = [];
export const uniqueCandidatePocs = [];

// Dashboard Data - These will be fetched from the API
export const dashboardSummaryData = {}; // Will be fetched
export const dashboardCandidatesByStatus = []; // Will be fetched
export const dashboardInterviewsToday = []; // Will be fetched
export const dashboardRecentActivities = []; // Will be fetched
export const dashboardClientsData = []; // Will be fetched

export const initialJobs = []; // Will be fetched

export const jobStatusList = [
];

// searchableItems will now be dynamically generated in Header.jsx based on fetched data
export const searchableItems = [];

// Removed initialHiringAgencies as data will be fetched from API
