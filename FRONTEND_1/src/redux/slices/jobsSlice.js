// src/redux/slices/jobsSlice.js
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { baseURL } from '../../data';

// Async Thunk for fetching jobs with retry logic
export const fetchJobs = createAsyncThunk(
  'jobs/fetchJobs',
  async (_, { rejectWithValue, dispatch }) => {
    try {
      const authToken = localStorage.getItem('authToken');
      if (!authToken) {
        return rejectWithValue('Authentication token not found.');
      }

      const response = await fetch(`${baseURL}/api/jobs/`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${authToken}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const formattedJobs = data.map(job => ({
        id: job.id,
        job_title: job.job_title,
        company_name: job.company_name,
        domain: job.domain,
        domain_name: job.domain_name || '', // Add domain_name if available
        spoc_email: job.spoc_email,
        hiring_manager_email: job.hiring_manager_email,
        current_team_size_info: job.current_team_size_info,
        number_to_hire: job.number_to_hire,
        position_level: job.position_level,
        current_process: job.current_process,
        tech_stack_details: job.tech_stack_details,
        job_description: job.job_description || '', // Add job_description field
        jd_file: job.jd_file,
        jd_link: job.jd_link,
        created_at: job.created_at,
      }));
      
      return formattedJobs;
    } catch (error) {
      console.error("Error fetching jobs:", error);
      // You could add retry logic here if needed
      return rejectWithValue(error.message);
    }
  }
);

// Async Thunk for fetching domains
export const fetchDomains = createAsyncThunk(
  'jobs/fetchDomains',
  async (_, { rejectWithValue }) => {
    try {
      const authToken = localStorage.getItem('authToken');
      if (!authToken) {
        return rejectWithValue('Authentication token not found.');
      }

      const response = await fetch(`${baseURL}/api/jobs/domains/`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${authToken}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Error fetching domains:", error);
      return rejectWithValue(error.message);
    }
  }
);

const jobsSlice = createSlice({
  name: 'jobs',
  initialState: {
    allJobs: [],
    domains: [],
    jobsStatus: 'idle',
    domainsStatus: 'idle',
    jobsError: null,
    domainsError: null,
    lastFetchTime: null,
  },
  reducers: {
    setJobs: (state, action) => {
      state.allJobs = action.payload;
      state.lastFetchTime = new Date().toISOString();
    },
    addJob: (state, action) => {
      if (!Array.isArray(state.allJobs)) {
        state.allJobs = [];
      }
      state.allJobs.push(action.payload);
    },
    updateJob: (state, action) => {
      const { id, updatedData } = action.payload;
      const jobIndex = state.allJobs.findIndex(job => job.id === id);
      if (jobIndex !== -1) {
        state.allJobs[jobIndex] = { ...state.allJobs[jobIndex], ...updatedData };
      }
    },
    deleteJob: (state, action) => {
      const idToDelete = action.payload;
      state.allJobs = state.allJobs.filter(job => job.id !== idToDelete);
    },
    setDomains: (state, action) => {
      state.domains = action.payload;
    },
    addDomain: (state, action) => {
      state.domains.push(action.payload);
    },
    updateDomain: (state, action) => {
      const { id, updatedData } = action.payload;
      const domainIndex = state.domains.findIndex(domain => domain.id === id);
      if (domainIndex !== -1) {
        state.domains[domainIndex] = { ...state.domains[domainIndex], ...updatedData };
      }
    },
    deleteDomain: (state, action) => {
      const idToDelete = action.payload;
      state.domains = state.domains.filter(domain => domain.id !== idToDelete);
    },
    resetJobsStatus: (state) => {
      state.jobsStatus = 'idle';
      state.jobsError = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchJobs.pending, (state) => {
        state.jobsStatus = 'loading';
        state.jobsError = null;
      })
      .addCase(fetchJobs.fulfilled, (state, action) => {
        state.jobsStatus = 'succeeded';
        state.allJobs = action.payload;
        state.lastFetchTime = new Date().toISOString();
        state.jobsError = null;
      })
      .addCase(fetchJobs.rejected, (state, action) => {
        state.jobsStatus = 'failed';
        state.jobsError = action.payload;
      })
      .addCase(fetchDomains.pending, (state) => {
        state.domainsStatus = 'loading';
        state.domainsError = null;
      })
      .addCase(fetchDomains.fulfilled, (state, action) => {
        state.domainsStatus = 'succeeded';
        state.domains = action.payload;
        state.domainsError = null;
      })
      .addCase(fetchDomains.rejected, (state, action) => {
        state.domainsStatus = 'failed';
        state.domainsError = action.payload;
      });
  },
});

export const { 
  setJobs, 
  addJob, 
  updateJob, 
  deleteJob, 
  setDomains, 
  addDomain, 
  updateDomain, 
  deleteDomain,
  resetJobsStatus 
} = jobsSlice.actions;

export const selectAllJobs = (state) => state.jobs.allJobs;
export const selectJobsStatus = (state) => state.jobs.jobsStatus;
export const selectLastFetchTime = (state) => state.jobs.lastFetchTime;

export default jobsSlice.reducer;