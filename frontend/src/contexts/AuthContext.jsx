import React, { createContext, useState, useEffect, useCallback } from 'react';
import { STORAGE_KEYS, USER_ROLES } from '../utils/constants';
import authService from '../services/authService';

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => {
    try {
      return localStorage.getItem(STORAGE_KEYS.AUTH_TOKEN) || null;
    } catch {
      return null;
    }
  });

  const [user, setUser] = useState(() => {
    try {
      const savedUser = localStorage.getItem(STORAGE_KEYS.USER_DATA);
      return savedUser ? JSON.parse(savedUser) : null;
    } catch {
      return null;
    }
  });

  const [loading, setLoading] = useState(true);

  // Logout action to cleanly wipe storage and memory
  const logout = useCallback(() => {
    try {
      localStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN);
      localStorage.removeItem(STORAGE_KEYS.USER_DATA);
    } catch (err) {
      console.error('Error clearing local storage:', err);
    }
    setToken(null);
    setUser(null);
  }, []);

  // Synchronize authentication state on startup and token changes
  useEffect(() => {
    let isMounted = true;

    async function checkAuth() {
      const storedToken = localStorage.getItem(STORAGE_KEYS.AUTH_TOKEN);
      if (storedToken) {
        try {
          const userData = await authService.getMe();
          if (isMounted) {
            const normalizedUser = {
              id: userData.id,
              email: userData.email,
              full_name: userData.full_name,
              role: userData.role,
              phone_number: userData.phone_number || null,
              is_active: userData.is_active ?? true,
              is_verified: userData.is_verified ?? true,
            };
            setUser(normalizedUser);
            localStorage.setItem(STORAGE_KEYS.USER_DATA, JSON.stringify(normalizedUser));
          }
        } catch (err) {
          console.warn('Session verification failed, logging out:', err);
          if (isMounted) {
            logout();
          }
        }
      } else {
        if (isMounted) {
          localStorage.removeItem(STORAGE_KEYS.USER_DATA);
          setUser(null);
          setToken(null);
        }
      }

      if (isMounted) {
        setLoading(false);
      }
    }

    checkAuth();

    // Listen for unauthorized 401 events dispatched by ApiClient
    const handleUnauthorized = () => {
      if (isMounted) {
        logout();
      }
    };

    window.addEventListener('auth:unauthorized', handleUnauthorized);

    return () => {
      isMounted = false;
      window.removeEventListener('auth:unauthorized', handleUnauthorized);
    };
  }, [logout]);

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

  const hasRole = useCallback(
    (allowedRoles = []) => {
      if (!user?.role) return false;
      if (allowedRoles.length === 0) return true;
      return allowedRoles.includes(user.role);
    },
    [user]
  );

  const value = {
    user,
    token,
    loading,
    isAuthenticated: !!token && !!user,
    role: user?.role || null,
    isPatient: user?.role === USER_ROLES.PATIENT,
    isDoctor: user?.role === USER_ROLES.DOCTOR,
    isAdmin: user?.role === USER_ROLES.ADMIN,
    isLabTechnician: user?.role === USER_ROLES.LAB_TECHNICIAN,
    isPharmacyStaff: user?.role === USER_ROLES.PHARMACY_STAFF,
    hasRole,
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export default AuthContext;
