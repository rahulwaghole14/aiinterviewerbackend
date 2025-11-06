// src/redux/slices/dashboardSlice.js
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { baseURL } from '../../data'; // Adjust path if necessary
import { handleAuthError } from '../../utils/authUtils';

// Async Thunk for fetching dashboard data
export const fetchDashboardData = createAsyncThunk(
  'dashboard/fetchDashboardData',
  async (_, { rejectWithValue }) => {
    try {
      const authToken = localStorage.getItem('authToken');
      if (!authToken) {
        return rejectWithValue('Authentication token not found. Please log in.');
      }

      const response = await fetch(`${baseURL}/api/dashboard/`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${authToken}`,
        },
      });

      if (!response.ok) {
        // Handle authentication errors specifically
        if (response.status === 401) {
          handleAuthError();
          throw new Error('Authentication failed. Please log in again.');
        }
        
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Error fetching dashboard data:", error);
      return rejectWithValue(error.message);
    }
  }
);

const dashboardSlice = createSlice({
  name: 'dashboard',
  initialState: {
    dashboardData: null,
    status: 'idle', // 'idle' | 'loading' | 'succeeded' | 'failed'
    error: null,
  },
  reducers: {
    // No specific reducers needed for direct state manipulation, as data is fetched via thunk
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchDashboardData.pending, (state) => {
        state.status = 'loading';
        state.error = null; // Clear previous errors on new fetch attempt
      })
      .addCase(fetchDashboardData.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.dashboardData = action.payload;
      })
      .addCase(fetchDashboardData.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload;
        state.dashboardData = null; // Clear data on failure
      });
  },
});

export default dashboardSlice.reducer;
