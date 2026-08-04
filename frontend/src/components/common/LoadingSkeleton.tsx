import React from 'react';

export const CardSkeleton: React.FC = () => {
  return (
    <div className="enterprise-card p-5 animate-pulse space-y-3">
      <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-1/3"></div>
      <div className="h-7 bg-slate-200 dark:bg-slate-700 rounded w-1/2"></div>
      <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-2/3"></div>
    </div>
  );
};

export const TableRowSkeleton: React.FC = () => {
  return (
    <div className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-800 animate-pulse">
      <div className="flex items-center space-x-3 w-1/2">
        <div className="w-8 h-8 bg-slate-200 dark:bg-slate-700 rounded-lg"></div>
        <div className="space-y-1 w-full">
          <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-3/4"></div>
          <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-1/2"></div>
        </div>
      </div>
      <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-1/6"></div>
    </div>
  );
};

export const DashboardSkeleton: React.FC = () => {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
        <CardSkeleton />
        <CardSkeleton />
        <CardSkeleton />
        <CardSkeleton />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="md:col-span-2 h-64 bg-slate-200 dark:bg-slate-800 rounded-xl"></div>
        <div className="h-64 bg-slate-200 dark:bg-slate-800 rounded-xl"></div>
      </div>
    </div>
  );
};
