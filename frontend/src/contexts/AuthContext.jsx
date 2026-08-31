import React, { createContext, useState, useEffect, useCallback } from 'react';
import { STORAGE_KEYS, USER_ROLES } from '../utils/constants';
import authService from '../services/authService';

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const savedUser = localStorage.getItem(STORAGE_KEYS.USER_DATA);
      return savedUser ? JSON.parse(savedUser) : null;
    } catch {
      return null;
    }
  });
  const [token, setToken] = useState(() => localStorage.getItem(STORAGE_KEYS.AUTH_TOKEN));
  const [loading, setLoading] = useState(true);

  // Synchronize authentication state
  useEffect(() => {
    async function checkAuth() {
      const storedToken = localStorage.getItem(STORAGE_KEYS.AUTH_TOKEN);
      if (storedToken) {
        try {
          const userData = await authService.getMe();
          setUser(userData);
          localStorage.setItem(STORAGE_KEYS.USER_DATA, JSON.stringify(userData));
        } catch (err) {
          console.error('Session validation failed:', err);
          logout();
        }
      }
      setLoading(false);
    }
    checkAuth();
  }, []);

  const login = useCallback(async (credentials) => {
    const authData = await authService.login(credentials);
    const userPayload = {
      id: authData.user_id,
      email: authData.email,
      full_name: authData.full_name,
      role: authData.role,
    };
    localStorage.setItem(STORAGE_KEYS.AUTH_TOKEN, authData.access_token);
    localStorage.setItem(STORAGE_KEYS.USER_DATA, JSON.stringify(userPayload));
    setToken(authData.access_token);
    setUser(userPayload);
    return userPayload;
  }, []);

  const register = useCallback(async (userData) => {
    const authData = await authService.register(userData);
    const userPayload = {
      id: authData.user_id,
      email: authData.email,
      full_name: authData.full_name,
      role: authData.role,
    };
    localStorage.setItem(STORAGE_KEYS.AUTH_TOKEN, authData.access_token);
    localStorage.setItem(STORAGE_KEYS.USER_DATA, JSON.stringify(userPayload));
    setToken(authData.access_token);
    setUser(userPayload);
    return userPayload;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.USER_DATA);
    setToken(null);
    setUser(null);
  }, []);

  const value = {
    user,
    token,
    loading,
    isAuthenticated: !!token && !!user,
    role: user?.role || null,
    isPatient: user?.role === USER_ROLES.PATIENT,
    isDoctor: user?.role === USER_ROLES.DOCTOR,
    isAdmin: user?.role === USER_ROLES.ADMIN,
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
