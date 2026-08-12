import React from 'react';
import { Users, Calendar, History, UserCheck } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useTeamHistory } from '../hooks/useTeams';

export const TeamPage: React.FC = () => {
  const { user } = useAuth();
  const { data: history } = useTeamHistory(user?.team_name);

  const teamName = user?.team_name || 'TEAM-01';
  const memberNames = user?.member_names || ['Pawan', 'Rahul', 'Kabilan'];
  const startedDate = user?.started_at
    ? new Date(user.started_at).toLocaleString()
    : new Date().toLocaleString();

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Page Title */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-50">
          Team Profile
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Team identity, members, and execution query history logged on Techonomy server.
        </p>
      </div>

      {/* Team Profile Grid */}
      <div className="enterprise-card p-6 space-y-6">
        <div className="flex items-center gap-4 pb-6 border-b border-slate-100 dark:border-slate-800">
          <div className="w-14 h-14 rounded-2xl bg-indigo-600 text-white font-bold text-xl flex items-center justify-center border-2 border-indigo-400/30 shadow-md">
            {teamName.substring(0, 3).toUpperCase()}
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">
              {teamName}
            </h2>
            <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400 mt-1">
              <span className="flex items-center gap-1">
                <Users className="w-3.5 h-3.5 text-indigo-500" /> Members: {memberNames.join(', ')}
              </span>
            </div>
          </div>
        </div>

        {/* Info Grid Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/60 dark:border-slate-700/60">
            <span className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1">
              <Users className="w-3.5 h-3.5 text-indigo-500" /> Team Name
            </span>
            <p className="text-xl font-bold text-slate-900 dark:text-slate-100 mt-1">{teamName}</p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/60 dark:border-slate-700/60">
            <span className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1">
              <UserCheck className="w-3.5 h-3.5 text-indigo-500" /> Members Count
            </span>
            <p className="text-xl font-bold text-slate-900 dark:text-slate-100 mt-1">{memberNames.length}</p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/60 dark:border-slate-700/60">
            <span className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5 text-indigo-500" /> Started At
            </span>
            <p className="text-sm font-bold text-slate-900 dark:text-slate-100 mt-1">{startedDate}</p>
          </div>
        </div>
      </div>

      {/* Query Activity Log */}
      <div className="enterprise-card p-6 space-y-4">
        <div className="flex items-center gap-2">
          <History className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
          <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
            Prompt Query History Log
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
