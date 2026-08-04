import React, { useState } from 'react';
import { Target, Building2, Clock, HelpCircle, FileText, Layers, UploadCloud, Users } from 'lucide-react';
import { useDashboard } from '../hooks/useDashboard';
import { useDocuments } from '../hooks/useDocuments';
import { useAuth } from '../hooks/useAuth';
import { MetricCard } from '../components/common/MetricCard';
import { DashboardSkeleton } from '../components/common/LoadingSkeleton';
import { ErrorState } from '../components/common/ErrorState';
import { QuestionProgressBar } from '../components/common/QuestionCounter';
import { ActivityFeed } from '../components/dashboard/ActivityFeed';
import { RecentDocuments } from '../components/dashboard/RecentDocuments';
import { DocumentModal } from '../components/documents/DocumentModal';
import { DocumentMetadata } from '../types';

export const DashboardPage: React.FC = () => {
  const { data: dashboard, isLoading, isError, refetch } = useDashboard();
  const { data: documents } = useDocuments();
  const { user } = useAuth();

  const [selectedDoc, setSelectedDoc] = useState<DocumentMetadata | null>(null);

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  if (isError || !dashboard) {
    return <ErrorState onRetry={refetch} />;
  }

  const teamName = user?.name || dashboard.team_name || 'Team 14';
  const teamId = user ? `T${user.id}` : 'T14';
  const questionLimit = dashboard.question_limit || user?.question_limit || 10;
  const questionsRemaining = dashboard.questions_remaining;
  const questionsUsed = Math.max(0, questionLimit - questionsRemaining);

  const formatTimer = (totalSeconds: number) => {
    const hrs = Math.floor(totalSeconds / 3600);
    const mins = Math.floor((totalSeconds % 3600) / 60);
    const secs = totalSeconds % 60;
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const totalPages = documents?.reduce((acc, doc) => acc + (doc.pages || 1), 0) || 1248;

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-50">
          Dashboard
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Welcome back, <span className="font-semibold text-slate-700 dark:text-slate-300">{teamName}</span>! Here's your challenge overview.
        </p>
      </div>

      {/* Top 4 Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <MetricCard
          title="Objective"
          value={dashboard.business_objective || 'Increase Revenue by 20%'}
          subtext="Analyze the provided company documents and provide insights."
          icon={Target}
          iconBgColor="bg-purple-50 dark:bg-purple-950/40"
          iconColor="text-purple-600 dark:text-purple-400"
        />

        <MetricCard
          title="Company"
          value={dashboard.current_event || 'ABC Retail Pvt Ltd.'}
          subtext="Consumer Goods & Retail"
          icon={Building2}
          iconBgColor="bg-blue-50 dark:bg-blue-950/40"
          iconColor="text-blue-600 dark:text-blue-400"
        />

        <MetricCard
          title="Time Remaining"
          value={formatTimer(dashboard.timer_remaining_seconds || 9936)}
          subtext="Stay focused and make it count!"
          icon={Clock}
          iconBgColor="bg-emerald-50 dark:bg-emerald-950/40"
          iconColor="text-emerald-600 dark:text-emerald-400"
        />

        <MetricCard
          title="Questions Left"
          value={`${questionsRemaining} / ${questionLimit}`}
          subtext="AI questions remaining"
          icon={HelpCircle}
          iconBgColor="bg-amber-50 dark:bg-amber-950/40"
          iconColor="text-amber-600 dark:text-amber-400"
        />
      </div>

      {/* Overview Stats Row */}
      <div className="enterprise-card p-6 space-y-4">
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
          Overview
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/60 dark:border-slate-700/60">
            <span className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-indigo-500" /> Documents
            </span>
            <p className="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-1">
              {dashboard.documents_available || documents?.length || 8}
            </p>
            <span className="text-[11px] text-slate-400">Total Documents</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/60 dark:border-slate-700/60">
            <span className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-indigo-500" /> Pages
            </span>
            <p className="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-1">
              {totalPages.toLocaleString()}
            </p>
            <span className="text-[11px] text-slate-400">Total Pages</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/60 dark:border-slate-700/60">
            <span className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
              <UploadCloud className="w-3.5 h-3.5 text-indigo-500" /> Uploaded
            </span>
            <p className="text-sm font-bold text-slate-900 dark:text-slate-100 mt-2">
              Today, 09:15 AM
            </p>
            <span className="text-[11px] text-slate-400">Latest Upload</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/60 dark:border-slate-700/60">
            <span className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
              <Users className="w-3.5 h-3.5 text-indigo-500" /> Team ID
            </span>
            <p className="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-1">
              {teamId}
            </p>
            <span className="text-[11px] text-slate-400">Your Team ID</span>
          </div>
        </div>
      </div>

      {/* Main Grid: Left (Question Usage & Activity Feed), Right (Recent Documents) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="enterprise-card p-6">
            <QuestionProgressBar used={questionsUsed} limit={questionLimit} />
          </div>
          <ActivityFeed />
        </div>

        <div>
          <RecentDocuments documents={documents} onViewDoc={(doc) => setSelectedDoc(doc)} />
        </div>
      </div>

      {/* Document Inspection Modal */}
      <DocumentModal
        document={selectedDoc}
        isOpen={!!selectedDoc}
        onClose={() => setSelectedDoc(null)}
      />
    </div>
  );
};
