// src/redux/slices/adminSlice.js
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { baseURL } from '../../data';
import { API_ENDPOINTS } from '../../config/api';

// Async thunk to fetch admin users from the database
export const fetchAdmins = createAsyncThunk(
  'admin/fetchAdmins',
  async (_, { rejectWithValue }) => {
    try {
      const token = localStorage.getItem('authToken');
      
      const response = await fetch(`${baseURL}/api/auth/admins/`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${token}`,
        },
      });


      if (!response.ok) {
        const errorData = await response.json();
        console.error('Admins API Error:', errorData);
        return rejectWithValue(errorData);
      }

      const data = await response.json();
      
      // Transform the data to match the expected format
      const transformedAdmins = (data.admins || []).map(admin => ({
        id: admin.id,
        name: admin.full_name,
        email: admin.email,
        role: admin.role,
        company_name: admin.company_name,
        username: admin.username,
        status: 'Active', // Assuming all admins are active
        userType: 'Admin',
        lastUpdated: new Date().toISOString().split('T')[0] // Current date as placeholder
      }));
      
      return transformedAdmins;
    } catch (error) {
      console.error('Exception in fetchAdmins:', error);
      return rejectWithValue(error.message);
    }
  }
);

const adminSlice = createSlice({
  name: 'admin',
  initialState: {
    admins: [],
    status: 'idle', // 'idle' | 'loading' | 'succeeded' | 'failed'
    error: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchAdmins.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchAdmins.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.admins = action.payload;
      })
      .addCase(fetchAdmins.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload;
      });
  },
});

export default adminSlice.reducer;
