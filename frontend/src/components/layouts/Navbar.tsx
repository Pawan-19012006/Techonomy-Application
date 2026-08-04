import React from 'react';
import { Menu, Sun, Moon, Users } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { useTheme } from '../../contexts/ThemeContext';
import { useEventStatus } from '../../hooks/useEvent';
import { TimerBadge } from '../common/TimerBadge';
import { QuestionCounterBadge } from '../common/QuestionCounter';

interface NavbarProps {
  onToggleMobileSidebar: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onToggleMobileSidebar }) => {
  const { user } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { data: eventStatus } = useEventStatus();

  const teamName = user?.name || 'Team 14';
  const teamId = user ? `T${user.id}` : 'T14';
  const questionsUsed = user?.questions_used || 0;
  const questionLimit = user?.question_limit || 10;

  return (
    <header className="sticky top-0 z-30 h-16 bg-[#111827] text-white border-b border-slate-800 px-4 sm:px-6 flex items-center justify-between">
      {/* Left Menu Toggle & Team Label */}
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleMobileSidebar}
          className="p-2 text-slate-400 hover:text-white rounded-lg lg:hidden"
          aria-label="Toggle Navigation"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="hidden sm:flex items-center gap-2 bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700">
          <Users className="w-4 h-4 text-indigo-400" />
          <span className="text-xs font-semibold text-slate-200">{teamName}</span>
          <span className="text-[10px] bg-indigo-500/20 text-indigo-300 px-1.5 py-0.5 rounded font-mono">
            {teamId}
          </span>
        </div>
      </div>

      {/* Right Action Widgets (Timer, Questions, Theme Toggle, Profile Avatar) */}
      <div className="flex items-center gap-3 sm:gap-4">
        {/* Live Timer */}
        <TimerBadge initialSeconds={eventStatus?.timer_remaining_seconds || 9936} />

        {/* Questions Remaining Counter */}
        <QuestionCounterBadge used={questionsUsed} limit={questionLimit} />

        {/* Dark Mode Toggle */}
        <button
          onClick={toggleTheme}
          className="p-2 text-slate-400 hover:text-white bg-slate-800/80 hover:bg-slate-700/80 rounded-lg border border-slate-700 transition-colors"
          title="Toggle Theme"
        >
          {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-slate-300" />}
        </button>

        {/* Team Profile Avatar */}
        <div className="w-8 h-8 rounded-full bg-indigo-600 text-white font-bold text-xs flex items-center justify-center border-2 border-indigo-400/30">
          {teamId}
        </div>
      </div>
    </header>
  );
};
