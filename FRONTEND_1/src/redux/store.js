// src/redux/store.js
import { configureStore } from '@reduxjs/toolkit';
import searchReducer from './slices/searchSlice';
import candidatesReducer from './slices/candidatesSlice';
import jobsReducer from './slices/jobsSlice';
import userReducer from './slices/userSlice';
import companiesReducer from './slices/companiesSlice';
import hiringAgenciesReducer from './slices/hiringAgenciesSlice';
import recruitersReducer from './slices/recruitersSlice';
import adminReducer from './slices/adminSlice';
import dashboardReducer from './slices/dashboardSlice'; // Import the new dashboard slice
import interviewsReducer from './slices/interviewsSlice';
import interviewSlotsReducer from './slices/interviewSlotsSlice';
import notificationReducer from './slices/notificationSlice';

const store = configureStore({
  reducer: {
    search: searchReducer,
    candidates: candidatesReducer,
    jobs: jobsReducer,
    interviews: interviewsReducer,
    user: userReducer,
    dashboard: dashboardReducer, // Add the dashboard reducer
    companies: companiesReducer,
    hiringAgencies: hiringAgenciesReducer,
    recruiters: recruitersReducer,
    admin: adminReducer,
    interviewSlots: interviewSlotsReducer,
    notification: notificationReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false,
    }),
});

export default store;
