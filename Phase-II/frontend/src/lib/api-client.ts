/**
 * API Client module for communicating with the backend.
 * Handles token attachment, error handling, and standard HTTP operations.
 */

import axios, { AxiosInstance, AxiosError } from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ApiErrorResponse {
  error?: string;
  code?: string;
  message?: string;
  detail?: string;
  field?: string;
}

export class ApiError extends Error {
  constructor(
    public statusCode: number,
    public code: string,
    message: string,
    public details?: ApiErrorResponse
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Create axios instance with default configuration.
 */
const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: API_URL,
    timeout: 30000,
    withCredentials: true, // Include cookies in requests
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor: attach JWT token from cookie
  client.interceptors.request.use(
    (config) => {
      // Get token from cookie (will be set by Better Auth)
      const token = getTokenFromCookie();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );

  // Response interceptor: handle errors
  client.interceptors.response.use(
    (response) => response,
    (error: AxiosError<ApiErrorResponse>) => {
      const status = error.response?.status || 500;
      const data = error.response?.data || {};
      let message =
        data.message ||
        data.error ||
        error.message ||
        'An unexpected error occurred';
      const code = data.code || 'UNKNOWN_ERROR';

      // Handle 400 errors - provide user-friendly messages
      if (status === 400) {
        if (message.includes('already') || message.includes('exists') || message.includes('registered')) {
          message = 'The username has already taken, please choose another';
        }
      }

      // Handle 401 errors (token expired/invalid)
      if (status === 401) {
        // Clear auth state and redirect to login
        clearAuthCookie();
        window.location.href = '/login?redirect=' + encodeURIComponent(window.location.pathname);
      }

      throw new ApiError(status, code, message, data);
    }
  );

  return client;
};

/**
 * Singleton instance of the API client.
 */
let apiClient: AxiosInstance;

/**
 * Get or create the API client instance.
 */
export const getApiClient = (): AxiosInstance => {
  if (!apiClient) {
    apiClient = createApiClient();
  }
  return apiClient;
};

/**
 * Helper function to store JWT token in cookie.
 */
export const setTokenInCookie = (token: string): void => {
  // Store JWT token in cookie (expires in 24 hours)
  const expiresIn = new Date();
  expiresIn.setHours(expiresIn.getHours() + 24);
  document.cookie = `auth_token=${encodeURIComponent(token)}; path=/; expires=${expiresIn.toUTCString()}`;
};

/**
 * Helper function to get JWT token from cookie.
 */
export const getTokenFromCookie = (): string | null => {
  // Extract JWT from auth_token cookie
  console.log('[API] All cookies:', document.cookie);
  const cookies = document.cookie.split(';');
  for (const cookie of cookies) {
    const [name, value] = cookie.trim().split('=');
    if (name === 'auth_token' && value) {
      console.log('[API] Found auth_token in cookie');
      return decodeURIComponent(value);
    }
  }
  console.log('[API] auth_token not found in cookies');
  return null;
};

/**
 * Clear authentication cookie.
 */
export const clearAuthCookie = (): void => {
  // Clear auth token cookie
  document.cookie = 'auth_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
};

/**
 * API methods for authentication endpoints.
 */
export const authApi = {
  signup: async (email: string, password: string) => {
    const client = getApiClient();
    const response = await client.post('/api/v1/auth/signup', { email, password });
    // Store JWT token in cookie
    if (response.data.token) {
      setTokenInCookie(response.data.token);
    }
    return response.data;
  },

  login: async (email: string, password: string) => {
    const client = getApiClient();
    const response = await client.post('/api/v1/auth/login', { email, password });
    console.log('[API] Login response:', response.data);
    // Store JWT token in cookie
    if (response.data.token) {
      console.log('[API] Saving token to cookie');
      setTokenInCookie(response.data.token);
    } else {
      console.log('[API] No token in response.data.token. Checking other locations...');
      console.log('[API] response.data keys:', Object.keys(response.data));
    }
    return response.data;
  },

  logout: async () => {
    const client = getApiClient();
    const response = await client.post('/api/v1/auth/logout');
    return response.data;
  },

  getMe: async () => {
    const client = getApiClient();
    const response = await client.get('/api/v1/auth/me');
    return response.data;
  },
};

/**
 * API methods for task endpoints.
 */
export const tasksApi = {
  list: async () => {
    const client = getApiClient();
    const response = await client.get('/api/v1/tasks');
    return response.data;
  },

  create: async (title: string, description?: string) => {
    const client = getApiClient();
    const response = await client.post('/api/v1/tasks', { title, description });
    return response.data;
  },

  update: async (taskId: string, data: Record<string, unknown>) => {
    const client = getApiClient();
    const response = await client.put(`/api/v1/tasks/${taskId}`, data);
    return response.data;
  },

  delete: async (taskId: string) => {
    const client = getApiClient();
    const response = await client.delete(`/api/v1/tasks/${taskId}`);
    return response.data;
  },

  toggleComplete: async (taskId: string, completed: boolean) => {
    const client = getApiClient();
    const response = await client.put(`/api/v1/tasks/${taskId}`, { completed });
    return response.data;
  },
};

/**
 * Task API wrapper for consistent interface.
 */
export const taskApi = {
  listTasks: async () => {
    const response = await tasksApi.list();
    return response;
  },

  createTask: async (data: { title: string; description?: string }) => {
    const response = await tasksApi.create(data.title, data.description);
    return response;
  },

  updateTask: async (taskId: string, data: Record<string, unknown>) => {
    const response = await tasksApi.update(taskId, data);
    return response;
  },

  deleteTask: async (taskId: string) => {
    const response = await tasksApi.delete(taskId);
    return response;
  },
};

export default getApiClient;
