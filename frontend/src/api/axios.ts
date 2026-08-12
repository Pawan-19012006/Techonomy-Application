import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  // Set timeout to 75s to ensure Frontend timeout (75s) > Backend max execution time (~61s)
  timeout: 75000,
});

// Request Interceptor
apiClient.interceptors.request.use(
  (config) => config,
  (error) => Promise.reject(error)
);

// Response Interceptor for user-friendly error formatting
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (!error.response) {
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        error.userMessage = 'The request timed out while waiting for the AI response. Please try asking your question again.';
      } else {
        error.userMessage = 'Unable to connect to the Techonomy server. Please check your backend network connection and try again.';
      }
    } else {
      const status = error.response.status;
      const detail = error.response.data?.detail;
      if (status === 404) {
        error.userMessage = detail || 'Requested resource or team not found.';
      } else if (status === 422) {
        error.userMessage = detail || 'Validation error. Please check your input fields.';
      } else if (status >= 500) {
        error.userMessage = detail || 'Techonomy server error occurred while processing your request. Please try again.';
      } else {
        error.userMessage = detail || 'An unexpected error occurred. Please try again.';
      }
    }
    return Promise.reject(error);
  }
);
