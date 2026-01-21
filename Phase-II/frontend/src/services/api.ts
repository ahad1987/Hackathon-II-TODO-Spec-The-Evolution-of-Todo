import axios, { AxiosInstance, AxiosError } from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://ahad-00-todo-backend-api.hf.space';

let apiClient: AxiosInstance | null = null;

// Custom error class
export class ApiError extends Error {
  statusCode: number;
  code: string;
  details?: unknown;

  constructor(statusCode: number, code: string, message: string, details?: unknown) {
    super(message);
    this.statusCode = statusCode;
    this.code = code;
    this.details = details;
    this.name = 'ApiError';
  }
}

// Cookie helpers
export const saveToken = (token: string): void => {
  const expires = new Date();
  expires.setHours(expires.getHours() + 24);
  document.cookie = `auth_token=${encodeURIComponent(token)}; path=/; expires=${expires.toUTCString()}`;
};

export const getToken = (): string | null => {
  for (const cookie of document.cookie.split(';')) {
    const [name, value] = cookie.trim().split('=');
    if (name === 'auth_token' && value) {
      return decodeURIComponent(value);
    }
  }
  return null;
};

export const clearToken = (): void => {
  document.cookie = 'auth_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
};

// Create API client with interceptors
const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: API_URL,
    timeout: 30000,
    withCredentials: true,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor - add auth token
  client.interceptors.request.use(
    (config) => {
      const token = getToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );

  // Response interceptor - handle errors
  client.interceptors.response.use(
    (response) => response,
    (error: AxiosError) => {
      const status = error.response?.status || 500;
      const data = (error.response?.data as Record<string, unknown>) || {};
      let message = (data.message as string) || (data.error as string) || error.message || 'An unexpected error occurred';
      const code = (data.code as string) || 'UNKNOWN_ERROR';

      if (status === 401) {
        clearToken();
        if (typeof window !== 'undefined') {
          window.location.href = '/login?redirect=' + encodeURIComponent(window.location.pathname);
        }
      }

      throw new ApiError(status, code, message, data);
    }
  );

  return client;
};

export function getApiClient(): AxiosInstance {
  if (!apiClient) {
    apiClient = createApiClient();
  }
  return apiClient;
}

// Alias for compatibility
export const sT = getApiClient;
export const GL = getToken;
export const I2 = clearToken;
export const MS = ApiError;

// Task Refresh Event System
export const TASK_MODIFYING_TOOLS = ['add_task', 'complete_task', 'delete_task', 'update_task'];
export const TASKS_REFRESH_EVENT = 'taskflow:tasks-refresh';

// Cooldown to prevent multiple rapid dispatches
let lastDispatchTime = 0;
const DISPATCH_COOLDOWN_MS = 2000; // 2 second cooldown

export function hasTaskModifyingToolCalls(response: ChatResponse): boolean {
  return response.tool_calls?.some(tool => TASK_MODIFYING_TOOLS.includes(tool)) ?? false;
}

export function dispatchTasksRefreshEvent(): void {
  if (typeof window === 'undefined') return;

  const now = Date.now();
  if (now - lastDispatchTime < DISPATCH_COOLDOWN_MS) {
    return;
  }

  lastDispatchTime = now;
  window.dispatchEvent(new CustomEvent(TASKS_REFRESH_EVENT));
}

// Auth API
export const iJ = {
  signup: async (email: string, password: string) => {
    const client = getApiClient();
    const response = await client.post('/api/v1/auth/signup', { email, password });
    if (response.data.token) saveToken(response.data.token);
    return response.data;
  },
  login: async (email: string, password: string) => {
    const client = getApiClient();
    const response = await client.post('/api/v1/auth/login', { email, password });
    if (response.data.token) {
      saveToken(response.data.token);
    }
    return response.data;
  },
  logout: async () => {
    const client = getApiClient();
    return (await client.post('/api/v1/auth/logout')).data;
  },
  getMe: async () => {
    const client = getApiClient();
    return (await client.get('/api/v1/auth/me')).data;
  },
};

// Tasks API
export const Qp = {
  listTasks: async () => {
    const client = getApiClient();
    return (await client.get('/api/v1/tasks')).data;
  },
  createTask: async (data: { title: string; description?: string }) => {
    const client = getApiClient();
    return (await client.post('/api/v1/tasks', data)).data;
  },
  updateTask: async (id: string, data: Record<string, unknown>) => {
    const client = getApiClient();
    return (await client.put(`/api/v1/tasks/${id}`, data)).data;
  },
  deleteTask: async (id: string) => {
    const client = getApiClient();
    return (await client.delete(`/api/v1/tasks/${id}`)).data;
  },
};

// Chat API - FIXED: Uses /api/v1/chat, NOT /api/{userId}/chat
export interface ChatResponse {
  conversation_id: string;
  response: string;
  tool_calls: string[];
  status: string;
}

export class ChatService {
  // CRITICAL FIX: Call /api/v1/chat - user_id is extracted from JWT on backend
  static async sendMessage(
    userId: string, // kept for interface compatibility but NOT used in URL
    message: string,
    conversationId?: string
  ): Promise<ChatResponse> {
    try {
      const client = getApiClient();
      // CORRECT URL: /api/v1/chat (user_id from JWT, not URL)
      const response = await client.post('/api/v1/chat', {
        conversation_id: conversationId || undefined,
        message,
      });

      // Dispatch refresh event if task was modified
      if (hasTaskModifyingToolCalls(response.data)) {
        dispatchTasksRefreshEvent();
      }

      return response.data;
    } catch (error) {
      if (error instanceof ApiError) {
        throw new Error(`Chat error (${error.statusCode}): ${error.message}`);
      }
      throw error;
    }
  }

  static formatResponse(response: ChatResponse): string {
    if (response.status === 'error') {
      return `Error: ${response.response}`;
    }
    return response.response;
  }

  static isTaskCreationSuccess(response: ChatResponse): boolean {
    return response.status === 'success' && response.tool_calls.includes('add_task');
  }
}

// Export ChatService as 'a' for compatibility with built code
export const a = ChatService;
