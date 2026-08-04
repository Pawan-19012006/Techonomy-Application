import React from 'react';
import { FileUp, UserCheck, CheckCircle2 } from 'lucide-react';
import { PromptLog } from '../../types';

interface ActivityFeedProps {
  logs?: PromptLog[];
}

export const ActivityFeed: React.FC<ActivityFeedProps> = ({ logs = [] }) => {
  const defaultActivities = [
    {
      id: '1',
      title: "Document 'Annual_Report_2024.pdf' uploaded",
      time: '09:15 AM',
      icon: FileUp,
      iconColor: 'text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40',
    },
    {
      id: '2',
      title: 'Team logged in',
      time: '09:00 AM',
      icon: UserCheck,
      iconColor: 'text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/40',
    },
    {
      id: '3',
      title: 'Welcome to Techonomy',
      time: '08:59 AM',
      icon: CheckCircle2,
      iconColor: 'text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/40',
    },
  ];

  return (
    <div className="enterprise-card p-5 space-y-4">
      <h3 className="text-base font-bold tracking-tight text-slate-900 dark:text-slate-100">
        Activity Feed
      </h3>
      <div className="space-y-3">
        {logs.length > 0
          ? logs.slice(0, 5).map((log) => (
              <div key={log.id} className="flex items-center justify-between p-2.5 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400">
                    <FileUp className="w-4 h-4" />
                  </div>
                  <span className="text-xs font-medium text-slate-800 dark:text-slate-200 line-clamp-1">
                    Query: "{log.prompt}"
                  </span>
                </div>
                <span className="text-[11px] text-slate-400 shrink-0 ml-2">
                  {new Date(log.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
            ))
          : defaultActivities.map((act) => {
              const Icon = act.icon;
              return (
                <div key={act.id} className="flex items-center justify-between p-2.5 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${act.iconColor}`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <span className="text-xs font-medium text-slate-800 dark:text-slate-200">
                      {act.title}
                    </span>
                  </div>
                  <span className="text-[11px] text-slate-400 shrink-0">
                    {act.time}
                  </span>
                </div>
              );
            })}
      </div>
    </div>
  );
};
