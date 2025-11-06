import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { baseURL } from '../../data';

export const fetchInterviewSlots = createAsyncThunk(
  'interviewSlots/fetchAll',
  async (_, { getState, rejectWithValue }) => {
    try {
      const token = localStorage.getItem('authToken');
      if (!token) {
        console.error('No auth token found');
        return rejectWithValue('Authentication required');
      }

      const state = getState();
      
      // Try both possible paths to user data
      const user = state?.auth?.user || state?.user?.currentUser;
      
      const companyId = user?.company_id || user?.id;
      let url = `${baseURL}/api/interviews/slots/`;
      
      if (companyId) {
        url += `${url.includes('?') ? '&' : '?'}company_id=${companyId}`;
      }

      const response = await fetch(url, {
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json().catch(e => ({}));
      
      if (!response.ok) {
        console.error('API Error:', { status: response.status, data });
        return rejectWithValue(data.detail || 'Failed to fetch interview slots');
      }

      return data.results || data || [];
    } catch (error) {
      console.error('Error in fetchInterviewSlots:', error);
      return rejectWithValue(error.message);
    }
  }
);

const initialState = {
  slots: [],
  loading: false,
  error: null,
  lastFetched: null,
};

const interviewSlotsSlice = createSlice({
  name: 'interviewSlots',
  initialState,
  reducers: {
    clearSlotsError: (state) => {
      state.error = null;
    },
    setSlots: (state, action) => {
      state.slots = action.payload;
      state.loading = false;
      state.error = null;
      state.lastFetched = new Date().toISOString();
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchInterviewSlots.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchInterviewSlots.fulfilled, (state, action) => {
        state.loading = false;
        state.slots = action.payload;
        state.lastFetched = new Date().toISOString();
      })
      .addCase(fetchInterviewSlots.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch interview slots';
      });
  },
});

export const { clearSlotsError, setSlots } = interviewSlotsSlice.actions;
export default interviewSlotsSlice.reducer;
