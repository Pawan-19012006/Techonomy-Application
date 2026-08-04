import React from 'react';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtext?: string;
  icon: LucideIcon;
  iconBgColor?: string;
  iconColor?: string;
  className?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtext,
  icon: Icon,
  iconBgColor = 'bg-indigo-50 dark:bg-indigo-950/40',
  iconColor = 'text-indigo-600 dark:text-indigo-400',
  className = '',
}) => {
  return (
    <div className={`enterprise-card p-5 flex items-start justify-between ${className}`}>
      <div className="space-y-1">
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
          {title}
        </p>
        <h3 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-50">
          {value}
        </h3>
        {subtext && (
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            {subtext}
          </p>
        )}
      </div>
      <div className={`p-3 rounded-xl ${iconBgColor} ${iconColor} flex items-center justify-center shrink-0`}>
        <Icon className="w-5 h-5" />
      </div>
    </div>
  );
};
