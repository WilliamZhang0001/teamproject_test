import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authService, UserResponse } from '../services/authService';

export interface User {
  id: string;
  name: string;
  email: string;
  role: 'user' | 'admin';
}

interface AuthContextType {
  user: User | null;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
  updateUser: () => Promise<void>;
  mockLogin: () => void; // Mock login for development mode
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const updateUserFromAPI = async () => {
    try {
      const userData = await authService.getCurrentUser();
      const user: User = {
        id: userData.id.toString(),
        name: userData.username,
        email: userData.email,
        role: userData.role as 'user' | 'admin'
      };
      setUser(user);
      localStorage.setItem('user', JSON.stringify(user));
    } catch (error) {
      console.error('Failed to verify user token:', error);
      // Check if it's a mock token, if so don't log out
      const token = localStorage.getItem('token');
      if (token && token.startsWith('dev-mock-token-')) {
        console.log('Dev mode: Using mock token, skipping verification');
        return;
      }
      // Token is invalid, logout and redirect to login
      logout();
      // Redirect to login page if not already there
      if (window.location.pathname !== '/login' && window.location.pathname !== '/register' && window.location.pathname !== '/') {
        window.location.href = '/login';
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Check for stored user data and token on mount
    const token = localStorage.getItem('token');
    const storedUser = localStorage.getItem('user');
    
    if (token && storedUser) {
      try {
        const user = JSON.parse(storedUser);
        setUser(user);
        
        // Verify token validity in background (for real tokens, not mock tokens)
        if (!token.startsWith('dev-mock-token-')) {
          // Verify token by calling getCurrentUser in background
          // Don't wait for it to complete, let it happen async
          updateUserFromAPI().catch(() => {
            // If verification fails, token is invalid - logout will be called by updateUserFromAPI
            console.log('Token verification failed on app load');
          });
        } else {
          // For mock tokens, just set loading to false
          setLoading(false);
        }
      } catch (error) {
        console.error('Error parsing stored user data:', error);
        localStorage.removeItem('user');
        localStorage.removeItem('token');
        setLoading(false);
      }
    } else {
      setLoading(false);
    }
  }, []);

  // Listen for auth:logout event from API interceptor
  useEffect(() => {
    const handleAuthLogout = () => {
      setUser(null);
      localStorage.removeItem('user');
      localStorage.removeItem('token');
      // Redirect to login page if not already there
      // Note: ProtectedRoute will also handle redirect, but we do it here
      // to ensure immediate redirect even if user is on a non-protected page
      if (window.location.pathname !== '/login' && window.location.pathname !== '/register' && window.location.pathname !== '/') {
        window.location.href = '/login';
      }
    };
    
    window.addEventListener('auth:logout', handleAuthLogout);
    return () => {
      window.removeEventListener('auth:logout', handleAuthLogout);
    };
  }, []);

  const login = async (username: string, password: string) => {
    setLoading(true);
    try {
      const { token, user: userData } = await authService.login({ username, password });
      
      const user: User = {
        id: userData.id.toString(),
        name: userData.username,
        email: userData.email,
        role: userData.role as 'user' | 'admin'
      };
      
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify(user));
      setUser(user);
      setLoading(false);
    } catch (error) {
      console.error('Login error:', error);
      setLoading(false);
      throw error;
    }
  };

  const register = async (username: string, email: string, password: string) => {
    setLoading(true);
    try {
      const { token, user: userData } = await authService.register({ username, email, password });
      
      const user: User = {
        id: userData.id.toString(),
        name: userData.username,
        email: userData.email,
        role: userData.role as 'user' | 'admin'
      };
      
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify(user));
      setUser(user);
      setLoading(false);
    } catch (error) {
      console.error('Registration error:', error);
      setLoading(false);
      throw error;
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('user');
    localStorage.removeItem('token');
  };

  const updateUser = async () => {
    if (user) {
      await updateUserFromAPI();
    }
  };

  // Mock login for development mode - bypass backend
  const mockLogin = () => {
    const mockUser: User = {
      id: '1',
      name: 'DevUser',
      email: 'dev@example.com',
      role: 'user'
    };
    
    // Set mock token
    const mockToken = 'dev-mock-token-' + Date.now();
    
    localStorage.setItem('token', mockToken);
    localStorage.setItem('user', JSON.stringify(mockUser));
    setUser(mockUser);
    console.log('✅ Dev mode login successful! User:', mockUser);
  };

  const value: AuthContextType = {
    user,
    login,
    register,
    logout,
    loading,
    updateUser,
    mockLogin
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
