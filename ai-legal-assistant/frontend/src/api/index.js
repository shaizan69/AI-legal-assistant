import axios from 'axios';

// Build a robust base URL for Supabase Edge Functions
const DEFAULT_SUPABASE_URL = 'https://iuxqomqbxfoetnieaorw.supabase.co';
const rawSupabaseUrl = process.env.REACT_APP_SUPABASE_URL || DEFAULT_SUPABASE_URL;
// Strip any trailing slashes to avoid double slashes
const normalizedSupabaseUrl = rawSupabaseUrl.replace(/\/+$/, '');
// Final base URL for our Edge Function (no trailing slash)
export const API_BASE_URL = `${normalizedSupabaseUrl}/functions/v1/api`;

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'apikey': process.env.REACT_APP_SUPABASE_ANON_KEY,
    'Content-Type': 'application/json',
  }
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Only redirect to login if we're not already on the login page
      if (window.location.pathname !== '/login') {
        localStorage.removeItem('token');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
