import React from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { ShieldCheck, LayoutDashboard, FileText, LogOut, Sun, Moon, Sparkles } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { useTheme } from '../../contexts/ThemeContext';

export const AdminLayout: React.FC = () => {
  const navigate = useNavigate();
  const { logoutAdmin } = useAuth();
  const { theme, toggleTheme } = useTheme();

  const handleAdminLogout = () => {
    logoutAdmin();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans select-none">
      
      {/* ADMIN TOP CONTROL BAR */}
      <header className="sticky top-0 z-50 bg-[#0B0F19]/90 backdrop-blur-md border-b border-slate-800 px-4 sm:px-8 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
          
          {/* Brand & Admin Badge */}
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-indigo-600 text-white flex items-center justify-center font-bold shadow-md">
              <Sparkles className="w-4 h-4 fill-current" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-black text-lg tracking-tight text-white uppercase font-sans leading-none">
                  KAIROS
                </span>
                <span className="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-400 font-mono text-[10px] font-bold border border-indigo-500/30 flex items-center gap-1">
                  <ShieldCheck className="w-3 h-3 text-indigo-400" />
                  ADMIN CONTROL PANEL
                </span>
              </div>
              <p className="text-[10px] font-mono text-slate-400">
                Authorized Event Evaluator Dashboard
              </p>
            </div>
          </div>

          {/* Center Nav Links */}
          <nav className="hidden md:flex items-center gap-2 p-1 rounded-xl bg-slate-900 border border-slate-800 text-xs font-semibold">
            <NavLink
              to="/admin"
              end
              className={({ isActive }) =>
                `px-3.5 py-1.5 rounded-lg flex items-center gap-2 transition-all ${
                  isActive
                    ? 'bg-indigo-600 text-white font-bold shadow-sm'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                }`
              }
            >
              <LayoutDashboard className="w-3.5 h-3.5" />
              <span>Team Overview</span>
            </NavLink>

            <NavLink
              to="/admin/documents"
              className={({ isActive }) =>
                `px-3.5 py-1.5 rounded-lg flex items-center gap-2 transition-all ${
                  isActive
                    ? 'bg-indigo-600 text-white font-bold shadow-sm'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                }`
              }
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Event Documents</span>
            </NavLink>
          </nav>

          {/* Right Action Controls */}
          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-lg bg-slate-900 border border-slate-800 text-xs font-mono text-slate-300">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>kairos@csbs</span>
            </div>

            <button
              onClick={toggleTheme}
              className="p-2 rounded-xl text-slate-400 hover:text-white bg-slate-900 border border-slate-800 transition-colors"
              title="Toggle Theme"
            >
              {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>

            <button
              onClick={handleAdminLogout}
              className="px-3 py-1.5 rounded-xl bg-red-950/40 text-red-400 hover:bg-red-900/60 border border-red-900/60 text-xs font-bold flex items-center gap-2 transition-colors"
              title="Admin Logout"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Logout</span>
            </button>
          </div>

        </div>
      </header>

      {/* ADMIN WORKSPACE CONTAINER */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
        <Outlet />
      </main>

    </div>
  );
};
