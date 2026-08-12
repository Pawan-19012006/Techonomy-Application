import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 45000, // 45 seconds timeout for LLM/RAG responses
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
      error.userMessage = 'Unable to connect to the Techonomy server. Please check your backend network connection and try again.';
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
