import React, { createContext, useContext, useState, useEffect } from 'react';
import { TeamData } from '../types';
import { getTeam } from '../services/api';

export const EVENT_DURATION_SECONDS = 9000; // 2 Hours 30 Minutes

export const getRemainingSeconds = (startedAtStr?: string): number => {
  if (!startedAtStr) return EVENT_DURATION_SECONDS;
  const startedAtMs = new Date(startedAtStr).getTime();
  if (isNaN(startedAtMs)) return EVENT_DURATION_SECONDS;
  const endMs = startedAtMs + EVENT_DURATION_SECONDS * 1000;
  const remainingMs = endMs - Date.now();
  return Math.max(0, Math.floor(remainingMs / 1000));
};

interface AuthContextType {
  user: TeamData | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  loginTeam: (teamData: TeamData) => void;
  logoutTeam: () => void;
  refetchTeam: () => Promise<void>;
  timerRemainingSeconds: number;
  isSessionExpired: boolean;
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
  const [timerRemainingSeconds, setTimerRemainingSeconds] = useState<number>(() =>
    getRemainingSeconds(user?.started_at)
  );
  const [isSessionExpired, setIsSessionExpired] = useState<boolean>(false);

  // Sync team data from backend on mount
  useEffect(() => {
    const restoreTeam = async () => {
      const saved = localStorage.getItem('techonomy_team');
      if (saved) {
        try {
          const parsed: TeamData = JSON.parse(saved);
          setUser(parsed);
          try {
            const fetched = await getTeam(parsed.team_name);
            if (fetched && fetched.team_name) {
              setUser(fetched);
              localStorage.setItem('techonomy_team', JSON.stringify(fetched));
            }
          } catch (err) {
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

  // Synchronized Event Session Countdown Timer
  useEffect(() => {
    if (!user?.started_at) {
      setTimerRemainingSeconds(EVENT_DURATION_SECONDS);
      setIsSessionExpired(false);
      return;
    }

    const updateTimer = () => {
      const remaining = getRemainingSeconds(user.started_at);
      setTimerRemainingSeconds(remaining);
      if (remaining <= 0) {
        setIsSessionExpired(true);
      }
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);
    return () => clearInterval(interval);
  }, [user?.started_at]);

  const loginTeam = (teamData: TeamData) => {
    localStorage.setItem('techonomy_team', JSON.stringify(teamData));
    setUser(teamData);
    setTimerRemainingSeconds(getRemainingSeconds(teamData.started_at));
    setIsSessionExpired(getRemainingSeconds(teamData.started_at) <= 0);
    setIsLoading(false);
  };

  const logoutTeam = () => {
    localStorage.removeItem('techonomy_team');
    setUser(null);
    setTimerRemainingSeconds(EVENT_DURATION_SECONDS);
    setIsSessionExpired(false);
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
        timerRemainingSeconds,
        isSessionExpired,
        logout: logoutTeam,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const useAuthContext = useAuth;
