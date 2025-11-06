// Authentication utility functions

export const isAuthenticated = () => {
  const authToken = localStorage.getItem('authToken');
  const userData = localStorage.getItem('userData');
  
  if (!authToken || !userData) {
    return false;
  }
  
  try {
    // Validate that userData is valid JSON
    JSON.parse(userData);
    return true;
  } catch (error) {
    console.error('Invalid user data in localStorage:', error);
    clearAuthData();
    return false;
  }
};

export const clearAuthData = () => {
  console.log('Clearing authentication data');
  localStorage.removeItem('authToken');
  localStorage.removeItem('userData');
};

export const getAuthToken = () => {
  if (!isAuthenticated()) {
    return null;
  }
  return localStorage.getItem('authToken');
};

export const getUserData = () => {
  if (!isAuthenticated()) {
    return null;
  }
  
  try {
    return JSON.parse(localStorage.getItem('userData'));
  } catch (error) {
    console.error('Error parsing user data:', error);
    clearAuthData();
    return null;
  }
};

export const handleAuthError = () => {
  console.log('Authentication error detected, clearing auth data');
  clearAuthData();
  
  // Dispatch a custom event to notify the app of auth failure
  const authErrorEvent = new CustomEvent('authError', {
    detail: { message: 'Authentication failed' }
  });
  window.dispatchEvent(authErrorEvent);
};
