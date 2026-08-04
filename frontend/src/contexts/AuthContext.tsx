import React, { createContext, useContext, useState, useEffect } from 'react';
import { Team } from '../types';
import { getMeApi } from '../api/auth';

interface AuthContextType {
  user: Team | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (token: string, rememberMe?: boolean) => Promise<void>;
  logout: () => void;
  refetchUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('techonomy_jwt'));
  const [user, setUser] = useState<Team | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchUserProfile = async (authToken: string) => {
    try {
      setIsLoading(true);
      const userProfile = await getMeApi();
      setUser(userProfile);
    } catch (error) {
      console.error('Failed to fetch user profile:', error);
      logout();
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchUserProfile(token);
    } else {
      setIsLoading(false);
    }
  }, [token]);

  const login = async (newToken: string, _rememberMe: boolean = true) => {
    localStorage.setItem('techonomy_jwt', newToken);
    setToken(newToken);
    await fetchUserProfile(newToken);
  };

  const logout = () => {
    localStorage.removeItem('techonomy_jwt');
    setToken(null);
    setUser(null);
    setIsLoading(false);
  };

  const refetchUser = async () => {
    if (token) {
      await fetchUserProfile(token);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token && !!user,
        isLoading,
        login,
        logout,
        refetchUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuthContext = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuthContext must be used within an AuthProvider');
  }
  return context;
};
