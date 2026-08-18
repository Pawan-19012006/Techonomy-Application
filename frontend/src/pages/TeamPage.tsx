import React from 'react';
import { Users, Calendar, History, UserCheck, Zap, ShieldCheck } from 'lucide-react';
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
      
      {/* Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-950 dark:text-white">
          Team Identity & Quotas
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Registered team details, member list, and execution prompt history logged on Kairos.
        </p>
      </div>

      {/* Team Profile Card */}
      <div className="kairos-card p-6 space-y-6">
        
        <div className="flex items-center gap-4 pb-6 border-b border-slate-200/80 dark:border-slate-800">
          <div className="w-14 h-14 rounded-2xl bg-slate-950 dark:bg-white text-white dark:text-slate-950 font-bold text-xl flex items-center justify-center shadow-md">
            {teamName.substring(0, 3).toUpperCase()}
          </div>
          <div>
            <h2 className="text-xl font-extrabold text-slate-950 dark:text-white">
              {teamName}
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Registered Event Team • Kairos Platform User
            </p>
          </div>
        </div>

        {/* Info Grid Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
          
          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200/80 dark:border-slate-800 space-y-1">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
              <Users className="w-4 h-4 text-slate-700 dark:text-slate-300" /> Team Identifier
            </span>
            <p className="text-xl font-extrabold text-slate-950 dark:text-white">{teamName}</p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200/80 dark:border-slate-800 space-y-1">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
              <UserCheck className="w-4 h-4 text-slate-700 dark:text-slate-300" /> Active Members
            </span>
            <p className="text-xl font-extrabold text-slate-950 dark:text-white">{memberNames.length}</p>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 truncate">{memberNames.join(', ')}</p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200/80 dark:border-slate-800 space-y-1">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
              <Calendar className="w-4 h-4 text-slate-700 dark:text-slate-300" /> Session Started
            </span>
            <p className="text-xs font-bold text-slate-950 dark:text-white mt-1 leading-tight">{startedDate}</p>
          </div>

        </div>

      </div>

      {/* Query History Log */}
      <div className="kairos-card p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <History className="w-5 h-5 text-slate-950 dark:text-white" />
            <h3 className="text-base font-bold text-slate-950 dark:text-white">
              Prompt Execution History
            </h3>
          </div>
          <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
            {history?.logs.length || 0} query log(s)
          </span>
        </div>

        {history && history.logs.length > 0 ? (
          <div className="space-y-3 divide-y divide-slate-100 dark:divide-slate-800/80">
            {history.logs.map((log) => (
              <div key={log.id} className="pt-3 first:pt-0 space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-slate-900 dark:text-slate-200">
                    Query #{log.id}
                  </span>
                  <span className="text-slate-400">
                    {new Date(log.created_at).toLocaleString()}
                  </span>
                </div>
                <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                  "{log.prompt}"
                </p>
                {log.response && (
                  <p className="text-xs text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-900/60 p-3 rounded-xl border border-slate-200/80 dark:border-slate-800 leading-relaxed">
                    {log.response}
                  </p>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="p-8 text-center text-slate-500 dark:text-slate-400 text-xs">
            No queries have been submitted by this team yet.
          </div>
        )}
      </div>

    </div>
  );
};
