'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { iJ as AuthAPI, GL as getToken, I2 as clearToken } from '@/services/api';

interface User {
  id: string;
  email: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const token = getToken();
        console.log('[Auth] Token from cookie:', token ? 'YES' : 'NO');

        if (!token) {
          console.log('[Auth] No token found');
          setUser(null);
          setIsAuthenticated(false);
          setIsLoading(false);
          return;
        }

        try {
          console.log('[Auth] Fetching user data...');
          const userData = await AuthAPI.getMe();
          console.log('[Auth] User data received:', userData);
          setUser(userData);
          setIsAuthenticated(true);
        } catch (err: any) {
          console.error('[Auth] Error fetching user:', err);
          if (err?.statusCode === 401 || err?.statusCode === 403) {
            console.log('[Auth] Token invalid (401/403), clearing');
            clearToken();
          } else {
            console.error('[Auth] Check error:', err);
          }
          setUser(null);
          setIsAuthenticated(false);
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

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await AuthAPI.login(email, password);
      if (response.user) {
        setUser(response.user);
        setIsAuthenticated(true);
        router.push('/tasks');
      }
    } catch (err: any) {
      setError(err.message || 'Login failed');
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  };

  const signup = async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await AuthAPI.signup(email, password);
      if (response.user) {
        setUser(response.user);
        setIsAuthenticated(true);
        router.push('/tasks');
      }
    } catch (err: any) {
      setError(err.message || 'Signup failed');
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    setError(null);
    try {
      await AuthAPI.logout();
      clearToken();
      setUser(null);
      setIsAuthenticated(false);
      router.push('/login');
    } catch (err: any) {
      setError(err.message || 'Logout failed');
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        isLoading,
        error,
        login,
        signup,
        logout,
        clearError: () => setError(null),
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
