// src/hooks/useNotification.js
import { useDispatch } from 'react-redux';
import { 
  showSuccess, 
  showError, 
  showWarning, 
  showInfo,
  clearAllNotifications 
} from '../redux/slices/notificationSlice';

/**
 * Custom hook for managing notifications
 * @returns {Object} Notification functions
 */
export const useNotification = () => {
  const dispatch = useDispatch();

  const notify = {
    /**
     * Show a success notification
     * @param {string} message - The message to display
     * @param {string} title - Optional title (defaults to "Success")
     * @param {number} duration - Auto-dismiss duration in ms (defaults to 3000)
     */
    success: (message, title = "Success", duration = 3000) => {
      dispatch(showSuccess(title, message, duration));
    },

    /**
     * Show an error notification
     * @param {string} message - The message to display
     * @param {string} title - Optional title (defaults to "Error")
     * @param {number} duration - Auto-dismiss duration in ms (defaults to 0 for manual dismiss)
     */
    error: (message, title = "Error", duration = 0) => {
      dispatch(showError(title, message, duration));
    },

    /**
     * Show a warning notification
     * @param {string} message - The message to display
     * @param {string} title - Optional title (defaults to "Warning")
     * @param {number} duration - Auto-dismiss duration in ms (defaults to 4000)
     */
    warning: (message, title = "Warning", duration = 4000) => {
      dispatch(showWarning(title, message, duration));
    },

    /**
     * Show an info notification
     * @param {string} message - The message to display
     * @param {string} title - Optional title (defaults to "Information")
     * @param {number} duration - Auto-dismiss duration in ms (defaults to 3000)
     */
    info: (message, title = "Information", duration = 3000) => {
      dispatch(showInfo(title, message, duration));
    },

    /**
     * Clear all notifications
     */
    clear: () => {
      dispatch(clearAllNotifications());
    },
  };

  return notify;
};
