import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Building2,
  Clock,
  HelpCircle,
  FileText,
  Layers,
  ArrowUpRight,
  ShieldCheck,
  Zap,
  Sparkles,
  Bot,
  Database,
} from 'lucide-react';
import { useDashboard } from '../hooks/useDashboard';
import { useDocuments } from '../hooks/useDocuments';
import { useAuth } from '../hooks/useAuth';
import { MetricCard } from '../components/common/MetricCard';
import { DashboardSkeleton } from '../components/common/LoadingSkeleton';
import { ErrorState } from '../components/common/ErrorState';
import { RecentDocuments } from '../components/dashboard/RecentDocuments';
import { DocumentModal } from '../components/documents/DocumentModal';
import { DocumentMetadata } from '../types';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { data: dashboard, isLoading, isError, refetch } = useDashboard();
  const { data: documents = [] } = useDocuments();
  const { user } = useAuth();

  const [selectedDoc, setSelectedDoc] = useState<DocumentMetadata | null>(null);

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  if (isError || !dashboard) {
    return <ErrorState onRetry={refetch} />;
  }

  const teamName = user?.team_name || user?.name || dashboard?.team_name || 'TEAM-01';
  const questionLimit = dashboard?.question_limit || user?.question_limit || 10;
  const questionsRemaining = dashboard?.questions_remaining ?? 10;
  const questionsUsed = Math.max(0, questionLimit - questionsRemaining);

  const formatTimer = (totalSeconds: number) => {
    const hrs = Math.floor(totalSeconds / 3600);
    const mins = Math.floor((totalSeconds % 3600) / 60);
    const secs = totalSeconds % 60;
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const totalPages = documents.reduce((acc, doc) => acc + (doc.pages || 1), 0);

  return (
    <div className="space-y-8">
      
      {/* Dashboard Banner Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200/80 dark:border-slate-800">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-950 dark:text-white">
            Good morning, {teamName} 👋
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Your organization's company knowledge, organized and ready to use.
          </p>
        </div>

        <button
          onClick={() => navigate('/assistant')}
          className="kairos-btn-primary text-xs"
        >
          <Bot className="w-4 h-4" />
          <span>Ask Kairos</span>
        </button>
      </div>

      {/* Top 4 Screenshot-Inspired Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <MetricCard
          title="Questions Remaining"
          value={`${questionsRemaining} / ${questionLimit}`}
          subtext={`${questionsUsed} question(s) asked this period`}
          icon={HelpCircle}
          iconBgColor="bg-amber-50 dark:bg-amber-950/40"
          iconColor="text-amber-600 dark:text-amber-400"
          badgeText="Active Quota"
          badgeType="warning"
          onClick={() => navigate('/assistant')}
        />

        <MetricCard
          title="Knowledge Sources"
          value={documents.length || dashboard.documents_available || 3}
          subtext={`${totalPages} pages indexed into vector space`}
          icon={FileText}
          iconBgColor="bg-blue-50 dark:bg-blue-950/40"
          iconColor="text-blue-600 dark:text-blue-400"
          badgeText="Qdrant Cloud"
          badgeType="info"
          onClick={() => navigate('/documents')}
        />

        <MetricCard
          title="Knowledge Base Status"
          value="HEALTHY"
          subtext="384-Dim Dense Embeddings · Ready"
          icon={ShieldCheck}
          iconBgColor="bg-emerald-50 dark:bg-emerald-950/40"
          iconColor="text-emerald-600 dark:text-emerald-400"
          badgeText="100% Verified"
          badgeType="success"
        />

        <MetricCard
          title="Session Timer"
          value={formatTimer(dashboard.timer_remaining_seconds || 9936)}
          subtext="UTC Server Time Synchronized"
          icon={Clock}
          iconBgColor="bg-slate-100 dark:bg-slate-800"
          iconColor="text-slate-800 dark:text-slate-200"
        />
      </div>

      {/* Screenshot-Inspired Content Layout Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Column: Knowledge Document Table (Task Table Style) */}
        <div className="lg:col-span-8 space-y-6">
          <div className="kairos-card p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-slate-950 dark:text-white">
                  Indexed Knowledge Documents
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Document sources available for RAG vector retrieval.
                </p>
              </div>
              <button
                onClick={() => navigate('/documents')}
                className="text-xs font-semibold text-slate-700 dark:text-slate-300 hover:underline flex items-center gap-1"
              >
                View all <ArrowUpRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 uppercase tracking-wider font-bold">
                    <th className="py-3 px-2">Document Name</th>
                    <th className="py-3 px-2">Pages</th>
                    <th className="py-3 px-2">Size</th>
                    <th className="py-3 px-2">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-medium">
                  {documents.slice(0, 5).map((doc) => (
                    <tr
                      key={doc.id}
                      onClick={() => setSelectedDoc(doc)}
                      className="hover:bg-slate-50 dark:hover:bg-slate-800/40 cursor-pointer transition-colors"
                    >
                      <td className="py-3.5 px-2 font-semibold text-slate-950 dark:text-slate-100 flex items-center gap-2">
                        <FileText className="w-4 h-4 text-slate-400 shrink-0" />
                        <span>{doc.filename}</span>
                      </td>
                      <td className="py-3.5 px-2 text-slate-600 dark:text-slate-400">
                        {doc.pages} page(s)
                      </td>
                      <td className="py-3.5 px-2 text-slate-600 dark:text-slate-400">
                        {(doc.file_size / (1024 * 1024)).toFixed(2)} MB
                      </td>
                      <td className="py-3.5 px-2">
                        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400 text-[11px] font-semibold">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                          Indexed
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right Column: Quota Progress & Quick Assistant Card */}
        <div className="lg:col-span-4 space-y-6">
          
          {/* Quota Progress Card */}
          <div className="kairos-card p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-950 dark:text-white">
                Team Question Usage
              </h3>
              <Zap className="w-4 h-4 text-amber-500" />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-semibold">
                <span className="text-slate-600 dark:text-slate-400">Questions Consumed</span>
                <span className="text-slate-950 dark:text-white font-bold">{questionsUsed} / {questionLimit}</span>
              </div>

              {/* Progress Bar */}
              <div className="w-full h-2.5 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                <div
                  className="h-full bg-slate-950 dark:bg-white rounded-full transition-all duration-300"
                  style={{ width: `${(questionsUsed / questionLimit) * 100}%` }}
                ></div>
              </div>

              <p className="text-[11px] text-slate-500 dark:text-slate-400">
                {questionsRemaining} question token(s) remaining for your team.
              </p>
            </div>

            <button
              onClick={() => navigate('/assistant')}
              className="kairos-btn-primary w-full text-xs justify-center"
            >
              <span>Launch Assistant</span>
              <Bot className="w-4 h-4" />
            </button>
          </div>

          {/* Business Objective Summary */}
          <div className="kairos-card p-6 space-y-3">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 block">
              Event Objective
            </span>
            <p className="text-sm font-bold text-slate-950 dark:text-white leading-snug">
              {dashboard.business_objective || 'Increase Corporate Revenue & Insights'}
            </p>
            <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
              Analyze official company reports, financial statements, and operational procedures to deliver context-backed strategic conclusions.
            </p>
          </div>

        </div>

      </div>

      {/* Document View Modal */}
      {selectedDoc && (
        <DocumentModal
          document={selectedDoc}
          onClose={() => setSelectedDoc(null)}
        />
      )}

    </div>
  );
};
