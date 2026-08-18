import React from 'react';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtext?: string;
  icon?: LucideIcon;
  iconBgColor?: string;
  iconColor?: string;
  badgeText?: string;
  badgeType?: 'success' | 'warning' | 'info';
  onClick?: () => void;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtext,
  icon: Icon,
  iconBgColor = 'bg-slate-100 dark:bg-slate-800',
  iconColor = 'text-slate-700 dark:text-slate-300',
  badgeText,
  badgeType = 'info',
  onClick,
}) => {
  return (
    <div
      onClick={onClick}
      className={`kairos-card p-5 space-y-3 transition-all ${
        onClick ? 'cursor-pointer kairos-card-hover' : ''
      }`}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
          {title}
        </span>
        {Icon && (
          <div className={`p-2 rounded-xl ${iconBgColor} ${iconColor} shrink-0`}>
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>

      <div className="space-y-1">
        <div className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-950 dark:text-white">
          {value}
        </div>
        {subtext && (
          <p className="text-xs text-slate-500 dark:text-slate-400 leading-snug">
            {subtext}
          </p>
        )}
      </div>

      {badgeText && (
        <div className="pt-2 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between">
          <span
            className={`text-[11px] font-semibold px-2 py-0.5 rounded-md ${
              badgeType === 'success'
                ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400'
                : badgeType === 'warning'
                ? 'bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400'
                : 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
            }`}
          >
            {badgeText}
          </span>
        </div>
      )}
    </div>
  );
};
