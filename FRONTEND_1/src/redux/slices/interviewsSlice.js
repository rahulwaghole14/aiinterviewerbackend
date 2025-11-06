// src/redux/slices/interviewsSlice.js
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { baseURL } from '../../data';

export const fetchInterviewsByCandidateId = createAsyncThunk(
  'interviews/fetchByCandidateId',
  async (candidateId, { rejectWithValue }) => {
    try {
      const authToken = localStorage.getItem('authToken');
      if (!authToken) {
        return rejectWithValue('Authentication token not found. Please log in.');
      }

      const response = await fetch(`${baseURL}/api/interviews/?candidate_id=${candidateId}`, {
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
      return { candidateId, data };
    } catch (error) {
      console.error("Error fetching interviews:", error);
      return rejectWithValue(error.message);
    }
  }
);

const interviewsSlice = createSlice({
  name: 'interviews',
  initialState: {
    interviewsByCandidate: {},
    status: 'idle',
    error: null,
  },
  reducers: {
    addInterview: (state, action) => {
      const { candidateId, interview } = action.payload;
      if (!state.interviewsByCandidate[candidateId]) {
        state.interviewsByCandidate[candidateId] = [];
      }
      state.interviewsByCandidate[candidateId].push(interview);
    },
    updateInterviewStatus: (state, action) => {
      const { candidateId, interviewId, newStatus } = action.payload;
      const interviews = state.interviewsByCandidate[candidateId];
      if (interviews) {
        const interview = interviews.find(i => i.id === interviewId);
        if (interview) {
          interview.status = newStatus;
        }
      }
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchInterviewsByCandidateId.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchInterviewsByCandidateId.fulfilled, (state, action) => {
        state.status = 'succeeded';
        const { candidateId, data } = action.payload;
        state.interviewsByCandidate[candidateId] = data;
      })
      .addCase(fetchInterviewsByCandidateId.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload;
      });
  },
});

export const { addInterview, updateInterviewStatus } = interviewsSlice.actions;

export const selectInterviewsByCandidateId = (state, candidateId) => 
  state.interviews.interviewsByCandidate[candidateId] || [];

export const selectInterviewsStatus = (state) => state.interviews.status;
export const selectInterviewsError = (state) => state.interviews.error;

export default interviewsSlice.reducer;