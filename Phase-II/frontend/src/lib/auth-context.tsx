/**
 * Auth Context for managing authentication state across the application.
 * Provides user state, login, logout, and auth status.
 */

'use client';

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { authApi, ApiError, clearAuthCookie, getTokenFromCookie } from './api-client';

export interface User {
  id: string;
  email: string;
  created_at?: string;
}

export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
}

/**
 * Create auth context with default undefined value.
 */
const AuthContext = createContext<AuthContextType | undefined>(undefined);

/**
 * Auth provider component.
 * Wraps the application and provides auth context to all children.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  /**
   * Check if user is authenticated on mount and after token changes.
   */
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const token = getTokenFromCookie();
        console.log('[Auth] Token from cookie:', token ? 'YES' : 'NO');

        if (!token) {
          // No token, user is not authenticated
          console.log('[Auth] No token found');
          setUser(null);
          setIsAuthenticated(false);
          setIsLoading(false);
          return;
        }

        // Token exists, try to fetch current user
        try {
          console.log('[Auth] Fetching user data...');
          const userData = await authApi.getMe();
          console.log('[Auth] User data received:', userData);
          setUser(userData);
          setIsAuthenticated(true);
        } catch (err: any) {
          // Token might be invalid or expired
          console.error('[Auth] Error fetching user:', err);
          if (err?.statusCode === 401 || err?.statusCode === 403) {
            // Token is invalid, clear it
            console.log('[Auth] Token invalid (401/403), clearing');
            clearAuthCookie();
            setUser(null);
            setIsAuthenticated(false);
          } else {
            // Some other error, but still mark as not loading
            console.error('[Auth] Check error:', err);
            setUser(null);
            setIsAuthenticated(false);
          }
        }
      } catch (err) {
        console.error('Unexpected auth check error:', err);
        setUser(null);
        setIsAuthenticated(false);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  /**
   * Handle login.
   */
  const login = async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await authApi.login(email, password);

      if (response.user) {
        setUser(response.user);
        setIsAuthenticated(true);

        // Redirect to tasks page
        router.push('/tasks');
      }
    } catch (err) {
      const error = err as ApiError;
      setError(error.message || 'Login failed');
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handle signup.
   */
  const signup = async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await authApi.signup(email, password);

      if (response.user) {
        setUser(response.user);
        setIsAuthenticated(true);

        // Redirect to tasks page
        router.push('/tasks');
      }
    } catch (err) {
      const error = err as ApiError;
      setError(error.message || 'Signup failed');
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handle logout.
   */
  const logout = async () => {
    setIsLoading(true);
    setError(null);

    try {
      await authApi.logout();

      // Clear auth state
      clearAuthCookie();
      setUser(null);
      setIsAuthenticated(false);

      // Redirect to login
      router.push('/login');
    } catch (err) {
      const error = err as ApiError;
      setError(error.message || 'Logout failed');
      // Still clear local state
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Clear error message.
   */
  const clearError = () => setError(null);

  const value: AuthContextType = {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    signup,
    logout,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Hook to use auth context.
 * Must be used within AuthProvider.
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);

  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }

  return context;
}
