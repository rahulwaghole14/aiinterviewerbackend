// API Configuration Constants
export const API_BASE_URL = 'http://127.0.0.1:8000';

// Legacy support - keep baseURL for existing components
export const baseURL = API_BASE_URL;

// Environment detection
export const isProduction = import.meta.env.PROD;
export const isDevelopment = import.meta.env.DEV;

// Log configuration in development
