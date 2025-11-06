// src/redux/slices/notificationSlice.js
import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  notifications: [], // Array of notifications (newest first for stacking)
};

const notificationSlice = createSlice({
  name: 'notification',
  initialState,
  reducers: {
    showNotification: (state, action) => {
      const { type, title, message, duration = 3000, id = Date.now() } = action.payload;
      
      const notification = {
        id,
        type, // 'success', 'error', 'warning', 'info'
        title,
        message,
        duration,
        timestamp: new Date().toISOString(),
      };

      // Add to beginning of notifications array (newest first for stacking)
      state.notifications.unshift(notification);
      
      // Keep only the last 5 notifications to prevent memory issues
      if (state.notifications.length > 5) {
        state.notifications = state.notifications.slice(0, 5);
      }
    },

    hideNotification: (state, action) => {
      const notificationId = action.payload;
      
      // Remove from notifications array
      state.notifications = state.notifications.filter(
        notification => notification.id !== notificationId
      );
    },

    clearAllNotifications: (state) => {
      state.notifications = [];
    },
  },
});

export const {
  showNotification,
  hideNotification,
  clearAllNotifications,
} = notificationSlice.actions;

// Helper action creators for common notification types
export const showSuccess = (title, message, duration) => 
  showNotification({ type: 'success', title, message, duration });

export const showError = (title, message, duration) => 
  showNotification({ type: 'error', title, message, duration });

export const showWarning = (title, message, duration) => 
  showNotification({ type: 'warning', title, message, duration });

export const showInfo = (title, message, duration) => 
  showNotification({ type: 'info', title, message, duration });

export default notificationSlice.reducer;
