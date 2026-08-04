import React from 'react';
import { Users, Mail, Calendar, HelpCircle, History, ShieldCheck } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useTeamQuestions, useTeamHistory } from '../hooks/useTeams';
import { QuestionProgressBar } from '../components/common/QuestionCounter';
import { CardSkeleton } from '../components/common/LoadingSkeleton';

export const TeamPage: React.FC = () => {
  const { user } = useAuth();
  const { data: questions } = useTeamQuestions();
  const { data: history } = useTeamHistory();

  const teamName = user?.name || 'Team 14';
  const teamEmail = user?.email || 'devs@acme.com';
  const teamId = user ? `T${user.id}` : 'T14';
  const joinedDate = user?.created_at
    ? new Date(user.created_at).toLocaleDateString(undefined, { month: 'short', day: '2-digit', year: 'numeric' })
    : 'Aug 03, 2026';

  const questionsUsed = questions?.questions_used ?? user?.questions_used ?? 0;
  const questionLimit = questions?.question_limit ?? user?.question_limit ?? 10;

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Page Title */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-50">
          Team Profile
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Team identity, quota limits, and execution query history.
        </p>
      </div>

      {/* Team Profile Grid */}
      <div className="enterprise-card p-6 space-y-6">
        <div className="flex items-center gap-4 pb-6 border-b border-slate-100 dark:border-slate-800">
          <div className="w-14 h-14 rounded-2xl bg-indigo-600 text-white font-bold text-xl flex items-center justify-center border-2 border-indigo-400/30 shadow-md">
            {teamId}
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">
              {teamName}
            </h2>
            <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400 mt-1">
              <span className="flex items-center gap-1">
                <Mail className="w-3.5 h-3.5 text-indigo-500" /> {teamEmail}
              </span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" /> {user?.is_admin ? 'Admin' : 'Standard Team'}
              </span>
            </div>
          </div>
        </div>

        {/* Info Grid Cards matching mockup */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/60 dark:border-slate-700/60">
            <span className="text-xs text-slate-500 dark:text-slate-400">Team ID</span>
            <p className="text-xl font-bold text-slate-900 dark:text-slate-100 mt-1">{teamId}</p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/60 dark:border-slate-700/60">
            <span className="text-xs text-slate-500 dark:text-slate-400">Team Name</span>
            <p className="text-xl font-bold text-slate-900 dark:text-slate-100 mt-1">{teamName}</p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/60 dark:border-slate-700/60">
            <span className="text-xs text-slate-500 dark:text-slate-400">Joined On</span>
            <p className="text-xl font-bold text-slate-900 dark:text-slate-100 mt-1">{joinedDate}</p>
          </div>
        </div>
      </div>

      {/* Question Usage Bar */}
      <div className="enterprise-card p-6">
        <QuestionProgressBar used={questionsUsed} limit={questionLimit} />
      </div>

      {/* Recent Query Activity Log */}
      <div className="enterprise-card p-6 space-y-4">
        <div className="flex items-center gap-2">
          <History className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
          <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
            Prompt Query History
          </h3>
        </div>

        {history && history.logs.length > 0 ? (
          <div className="space-y-3 divide-y divide-slate-100 dark:divide-slate-800">
            {history.logs.map((log) => (
              <div key={log.id} className="pt-3 first:pt-0 space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-indigo-600 dark:text-indigo-400">
                    Query #{log.id}
                  </span>
                  <span className="text-slate-400">
                    {new Date(log.created_at).toLocaleString()}
                  </span>
                </div>
                <p className="text-sm font-medium text-slate-800 dark:text-slate-200">
                  "{log.prompt}"
                </p>
                {log.response && (
                  <p className="text-xs text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-800/50 p-2.5 rounded-lg border border-slate-100 dark:border-slate-800">
                    {log.response}
                  </p>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center p-6 text-xs text-slate-500">
            No prompt query history recorded yet. Questions asked in Knowledge Assistant will appear here.
          </div>
        )}
      </div>
    </div>
  );
};
