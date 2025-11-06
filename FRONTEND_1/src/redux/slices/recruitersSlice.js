// src/redux/slices/recruitersSlice.js
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { baseURL } from '../../data';

// Async thunk to fetch recruiters
export const fetchRecruiters = createAsyncThunk(
  'recruiters/fetchRecruiters',
  async (_, { rejectWithValue }) => {
    try {
      const token = localStorage.getItem('authToken');
      
      // Try to fetch all records by setting a large page size or using a different endpoint
      const response = await fetch(`${baseURL}/api/companies/recruiters/?page_size=1000`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${token}`, // Use auth token
        },
      });


      if (!response.ok) {
        const errorData = await response.json();
        console.error('API Error:', errorData);
        return rejectWithValue(errorData);
      }

      const data = await response.json();
      
      // Handle both paginated and non-paginated responses
      let recruiters = data;
      if (data.results) {
        // Paginated response
        recruiters = data.results;
      } else if (Array.isArray(data)) {
        // Non-paginated response
        recruiters = data;
      }
      
      // Add a userType field for consistent filtering in HiringAgency.jsx
      const mappedData = recruiters.map(recruiter => ({ ...recruiter, userType: 'Recruiter' }));
      return mappedData;
    } catch (error) {
      console.error('Exception in fetchRecruiters:', error);
      return rejectWithValue(error.message);
    }
  }
);

const recruitersSlice = createSlice({
  name: 'recruiters',
  initialState: {
    recruiters: [],
    status: 'idle', // 'idle' | 'loading' | 'succeeded' | 'failed'
    error: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchRecruiters.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchRecruiters.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.recruiters = action.payload;
      })
      .addCase(fetchRecruiters.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload;
      });
  },
});

export default recruitersSlice.reducer;
