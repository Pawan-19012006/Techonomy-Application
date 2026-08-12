import React, { createContext, useContext, useState, useEffect } from 'react';
import { TeamData } from '../types';
import { getTeam } from '../services/api';

interface AuthContextType {
  user: TeamData | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  loginTeam: (teamData: TeamData) => void;
  logoutTeam: () => void;
  refetchTeam: () => Promise<void>;
  // Aliases for backwards compatibility with existing UI components
  login?: (token: string, rememberMe?: boolean) => Promise<void>;
  logout?: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<TeamData | null>(() => {
    const saved = localStorage.getItem('techonomy_team');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        console.error('Failed to parse techonomy_team from localStorage:', e);
        localStorage.removeItem('techonomy_team');
      }
    }
    return null;
  });
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const restoreTeam = async () => {
      const saved = localStorage.getItem('techonomy_team');
      if (saved) {
        try {
          const parsed: TeamData = JSON.parse(saved);
          setUser(parsed);
          // Refresh team data from backend if server is reachable
          try {
            const fetched = await getTeam(parsed.team_name);
            if (fetched && fetched.team_name) {
              setUser(fetched);
              localStorage.setItem('techonomy_team', JSON.stringify(fetched));
            }
          } catch (err) {
            // If server unavailable, keep local restored team
            console.warn('Backend unavailable during team refresh, using cached team info');
          }
        } catch (e) {
          localStorage.removeItem('techonomy_team');
          setUser(null);
        }
      }
      setIsLoading(false);
    };

    restoreTeam();
  }, []);

  const loginTeam = (teamData: TeamData) => {
    localStorage.setItem('techonomy_team', JSON.stringify(teamData));
    setUser(teamData);
    setIsLoading(false);
  };

  const logoutTeam = () => {
    localStorage.removeItem('techonomy_team');
    setUser(null);
    setIsLoading(false);
  };

  const refetchTeam = async () => {
    if (user?.team_name) {
      try {
        const fetched = await getTeam(user.team_name);
        if (fetched) {
          loginTeam(fetched);
        }
      } catch (e) {
        console.error('Failed to refetch team data:', e);
      }
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        loginTeam,
        logoutTeam,
        refetchTeam,
        logout: logoutTeam,
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
