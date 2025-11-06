// src/redux/slices/userSlice.js
import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  user: null, // Stores user data
};

const userSlice = createSlice({
  name: 'user',
  initialState,
  reducers: {
    // Action to set user data after login
    setUser: (state, action) => {
      state.user = action.payload;
    },
    // Action to clear user data on logout
    clearUser: (state) => {
      state.user = null;
    },
  },
});

export const { setUser, clearUser } = userSlice.actions;
export default userSlice.reducer;
