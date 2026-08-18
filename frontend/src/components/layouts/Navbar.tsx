import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Bot,
  FileText,
  BookOpen,
  Users,
  Sun,
  Moon,
  LogOut,
  Sparkles,
  Menu,
  Clock,
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';

interface NavbarProps {
  onToggleMobileSidebar: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onToggleMobileSidebar }) => {
  const { user, logoutTeam, timerRemainingSeconds } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();

  const teamName = user?.team_name || 'TEAM-01';

  const handleLogout = () => {
    if (logoutTeam) logoutTeam();
    navigate('/login');
  };

  const formatTimer = (totalSeconds: number) => {
    const hrs = Math.floor(totalSeconds / 3600);
    const mins = Math.floor((totalSeconds % 3600) / 60);
    const secs = totalSeconds % 60;
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const navTabs = [
    { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { label: 'Ask Kairos', path: '/assistant', icon: Bot },
    { label: 'Documents', path: '/documents', icon: FileText },
    { label: 'Rules', path: '/rules', icon: BookOpen },
    { label: 'Team', path: '/team', icon: Users },
  ];

  const isLowTime = timerRemainingSeconds < 600; // <10 mins

  return (
    <header className="sticky top-0 z-30 bg-white/90 dark:bg-[#0F172A]/90 backdrop-blur-md border-b border-slate-200/80 dark:border-slate-800/80 px-4 sm:px-6 lg:px-8 transition-colors">
      <div className="max-w-[1500px] mx-auto h-16 flex items-center justify-between gap-4">
        
        {/* Left: Brand Logo & Mobile Trigger */}
        <div className="flex items-center gap-3">
          <button
            onClick={onToggleMobileSidebar}
            className="p-2 text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white rounded-lg lg:hidden"
            aria-label="Toggle Navigation"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div 
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2.5 cursor-pointer group"
          >
            <div className="w-9 h-9 rounded-xl bg-slate-950 dark:bg-white text-white dark:text-slate-950 flex items-center justify-center font-bold text-lg shadow-sm group-hover:scale-105 transition-transform">
              <Sparkles className="w-5 h-5 fill-current" />
            </div>
            <span className="font-black text-xl tracking-tighter text-slate-950 dark:text-white leading-none font-sans uppercase">
              KAIROS
            </span>
          </div>
        </div>

        {/* Center: Top Pill Tab Navigation */}
        <nav className="hidden lg:flex items-center gap-1.5 p-1 bg-slate-100 dark:bg-slate-900/90 rounded-xl border border-slate-200/60 dark:border-slate-800">
          {navTabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <NavLink
                key={tab.path}
                to={tab.path}
                className={({ isActive }) =>
                  `flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all duration-150 ${
                    isActive
                      ? 'bg-slate-950 text-white dark:bg-white dark:text-slate-950 shadow-sm'
                      : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-white/60 dark:hover:bg-slate-800/50'
                  }`
                }
              >
                <Icon className="w-3.5 h-3.5 shrink-0" />
                <span>{tab.label}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* Right: Team Info & Persistent Competition Timer */}
        <div className="flex items-center gap-2.5 sm:gap-3">
          
          {/* Team Identifier Pill */}
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 text-xs font-bold text-slate-900 dark:text-white">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>{teamName}</span>
          </div>

          {/* Persistent Competition Timer Pill */}
          <div
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-mono font-bold transition-all ${
              isLowTime
                ? 'bg-red-50 dark:bg-red-950/60 border-red-300 dark:border-red-800 text-red-600 dark:text-red-400 animate-pulse'
                : 'bg-slate-950 dark:bg-white text-white dark:text-slate-950 border-slate-900 dark:border-slate-200'
            }`}
            title="Competition Timer"
          >
            <Clock className="w-3.5 h-3.5 shrink-0" />
            <span>⏱ {formatTimer(timerRemainingSeconds)}</span>
          </div>

          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="p-2 text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white bg-slate-100 dark:bg-slate-800/80 hover:bg-slate-200/80 dark:hover:bg-slate-700/80 rounded-lg border border-slate-200/80 dark:border-slate-700 transition-colors"
            title="Toggle Theme"
          >
            {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-slate-600" />}
          </button>

          {/* Logout Button */}
          <button
            onClick={handleLogout}
            className="p-2 text-slate-500 hover:text-red-600 dark:text-slate-400 dark:hover:text-red-400 bg-slate-100 dark:bg-slate-800/80 hover:bg-red-50 dark:hover:bg-red-950/30 rounded-lg border border-slate-200/80 dark:border-slate-700 transition-colors flex items-center gap-1.5 text-xs font-semibold"
            title="Exit Arena"
          >
            <LogOut className="w-4 h-4" />
            <span className="hidden sm:inline">Exit</span>
          </button>

          {/* Team Initials Avatar */}
          <div className="w-8 h-8 rounded-full bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 font-bold text-xs flex items-center justify-center shadow-sm border border-slate-300 dark:border-slate-700">
            {teamName.substring(0, 2).toUpperCase()}
          </div>
        </div>

      </div>
    </header>
  );
};
