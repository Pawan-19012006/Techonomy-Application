import React from 'react';
import { HelpCircle } from 'lucide-react';

interface QuestionCounterProps {
  used: number;
  limit: number;
}

export const QuestionCounterBadge: React.FC<QuestionCounterProps> = ({ used, limit }) => {
  const remaining = Math.max(0, limit - used);

  return (
    <div className="flex items-center gap-2 bg-slate-800/80 text-white px-3 py-1.5 rounded-lg border border-slate-700 text-xs font-mono font-medium">
      <HelpCircle className="w-3.5 h-3.5 text-amber-400" />
      <div className="flex flex-col">
        <span className="text-[10px] uppercase text-slate-400 leading-tight">Questions Left</span>
        <span className="text-xs font-bold text-white tracking-wide">
          {remaining} / {limit}
        </span>
      </div>
    </div>
  );
};

export const QuestionProgressBar: React.FC<QuestionCounterProps> = ({ used, limit }) => {
  const remaining = Math.max(0, limit - used);
  const percentage = limit > 0 ? Math.min(100, (used / limit) * 100) : 0;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-xs font-medium">
        <span className="text-slate-500 dark:text-slate-400">Question Quota Usage</span>
        <span className="font-semibold text-slate-900 dark:text-slate-100">
          {used} used ({remaining} remaining)
        </span>
      </div>
      <div className="w-full h-2.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden border border-slate-200 dark:border-slate-700">
        <div
          className={`h-full transition-all duration-300 ${
            percentage >= 100
              ? 'bg-red-500'
              : percentage >= 75
              ? 'bg-amber-500'
              : 'bg-indigo-600'
          }`}
          style={{ width: `${percentage}%` }}
        ></div>
      </div>
    </div>
  );
};
