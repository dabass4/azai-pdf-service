import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [organization, setOrganization] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('auth_token'));

  // Setup axios interceptor to include token in all requests
  useEffect(() => {
    const interceptor = axios.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    return () => {
      axios.interceptors.request.eject(interceptor);
    };
  }, []);

  // Load user on mount
  useEffect(() => {
    if (token) {
      loadUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  const loadUser = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data.user);
      setOrganization(response.data.organization);
    } catch (error) {
      console.error('Failed to load user:', error);
      // Token might be expired, clear it
      logout();
    } finally {
      setLoading(false);
    }
  };

  const signup = async (email, password, firstName, lastName, organizationName, phone = null) => {
    try {
      const response = await axios.post(`${API}/auth/signup`, {
        email,
        password,
        first_name: firstName,
        last_name: lastName,
        organization_name: organizationName,
        phone
      });

      const { access_token, user: userData, organization: orgData } = response.data;
      
      localStorage.setItem('auth_token', access_token);
      setToken(access_token);
      setUser(userData);
      setOrganization(orgData);

      return { success: true };
    } catch (error) {
      console.error('Signup error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Signup failed'
      };
    }
  };

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, {
        email,
        password
      });

      const { access_token, user: userData, organization: orgData } = response.data;
      
      localStorage.setItem('auth_token', access_token);
      setToken(access_token);
      setUser(userData);
      setOrganization(orgData);

      return { success: true };
    } catch (error) {
      console.error('Login error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Login failed'
      };
    }
  };

  const logout = () => {
    localStorage.removeItem('auth_token');
    setToken(null);
    setUser(null);
    setOrganization(null);
  };

  const value = {
    user,
    organization,
    loading,
    isAuthenticated: !!user,
    signup,
    login,
    logout
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
