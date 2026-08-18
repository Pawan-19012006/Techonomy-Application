import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Clock,
  HelpCircle,
  FileText,
  Users,
  ArrowRight,
  Zap,
  Sparkles,
  Bot,
  BookOpen,
  CheckCircle2,
  ChevronRight,
} from 'lucide-react';
import { useDashboard } from '../hooks/useDashboard';
import { useDocuments } from '../hooks/useDocuments';
import { useAuth } from '../contexts/AuthContext';
import { MetricCard } from '../components/common/MetricCard';
import { DashboardSkeleton } from '../components/common/LoadingSkeleton';
import { ErrorState } from '../components/common/ErrorState';
import { DocumentModal } from '../components/documents/DocumentModal';
import { DocumentMetadata } from '../types';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { data: dashboard, isLoading, isError, refetch } = useDashboard();
  const { data: documents = [] } = useDocuments();
  const { user, timerRemainingSeconds } = useAuth();

  const [selectedDoc, setSelectedDoc] = useState<DocumentMetadata | null>(null);

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  if (isError || !dashboard) {
    return <ErrorState onRetry={refetch} />;
  }

  const teamName = user?.team_name || user?.name || dashboard?.team_name || 'TEAM-01';
  const memberNames = user?.member_names || dashboard?.member_names || ['Student Member'];
  const questionLimit = dashboard?.question_limit || user?.question_limit || 10;
  const questionsRemaining = dashboard?.questions_remaining ?? 10;
  const questionsUsed = Math.max(0, questionLimit - questionsRemaining);

  const formatTimer = (totalSeconds: number) => {
    const hrs = Math.floor(totalSeconds / 3600);
    const mins = Math.floor((totalSeconds % 3600) / 60);
    const secs = totalSeconds % 60;
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const isLowTime = timerRemainingSeconds < 600;

  return (
    <div className="space-y-8 select-none">
      
      {/* HERO SECTION — Competition Arena Header */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-slate-950 via-[#0B0F19] to-slate-900 text-white p-6 sm:p-8 lg:p-10 border border-slate-800 shadow-xl">
        
        {/* Subtle Ambient Grid & Orbs */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] opacity-20 pointer-events-none" />
        <div className="absolute -top-24 -right-24 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-8">
          
          {/* Left Hero Content */}
          <div className="space-y-3 max-w-2xl">
            <div className="flex items-center gap-2.5">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-950/80 border border-emerald-800/80 text-emerald-400 text-xs font-mono font-bold">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <span>KAIROS AI CHALLENGE</span>
              </span>
              <span className="text-xs font-mono text-slate-400 uppercase tracking-widest hidden sm:inline">
                LIVE ARENA
              </span>
            </div>

            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black tracking-tight uppercase leading-tight font-sans">
              Welcome back, <span className="text-slate-100">{teamName}</span> 👋
            </h1>

            <p className="text-sm sm:text-base text-slate-300 font-medium leading-relaxed">
              Your team is in the KAIROS arena. Solve smart. Move fast.
            </p>
          </div>

          {/* Right Hero Timer Card (Prominent & Central) */}
          <div className="shrink-0 w-full lg:w-80">
            <div
              className={`p-6 rounded-2xl border transition-all shadow-2xl ${
                isLowTime
                  ? 'bg-red-950/80 border-red-800/80 text-red-100 animate-pulse'
                  : 'bg-white/10 dark:bg-slate-900/90 border-white/15 text-white backdrop-blur-md'
              }`}
            >
              <div className="flex items-center justify-between text-xs font-mono font-bold uppercase tracking-wider text-slate-400 mb-2">
                <span className="flex items-center gap-1.5">
                  <Clock className="w-4 h-4 text-amber-400" />
                  <span>COMPETITION TIME</span>
                </span>
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
              </div>

              <div className="text-4xl sm:text-5xl font-black font-mono tracking-tight my-1 text-white">
                {formatTimer(timerRemainingSeconds)}
              </div>

              <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 pt-2 border-t border-white/10">
                <span>150 MIN TOTAL SESSION</span>
                <span className="text-emerald-400 font-bold">ACTIVE</span>
              </div>
            </div>
          </div>

        </div>
      </div>

      {/* QUICK COMPETITION STATS (4 Cards) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        
        <MetricCard
          title="Questions Remaining"
          value={`${questionsRemaining} / ${questionLimit}`}
          subtext={`${questionsUsed} question token(s) used`}
          icon={HelpCircle}
          iconBgColor="bg-amber-50 dark:bg-amber-950/40"
          iconColor="text-amber-600 dark:text-amber-400"
          badgeText="Active Quota"
          badgeType="warning"
          onClick={() => navigate('/assistant')}
        />

        <MetricCard
          title="Team Members"
          value={`${memberNames.length} / 4`}
          subtext={memberNames.join(', ')}
          icon={Users}
          iconBgColor="bg-indigo-50 dark:bg-indigo-950/40"
          iconColor="text-indigo-600 dark:text-indigo-400"
          badgeText="Registered"
          badgeType="info"
          onClick={() => navigate('/team')}
        />

        <MetricCard
          title="Event Documents"
          value={documents.length || dashboard.documents_available || 3}
          subtext="Indexed Knowledge Sources"
          icon={FileText}
          iconBgColor="bg-blue-50 dark:bg-blue-950/40"
          iconColor="text-blue-600 dark:text-blue-400"
          badgeText="Qdrant Vectors"
          badgeType="info"
          onClick={() => navigate('/documents')}
        />

        <MetricCard
          title="Competition Status"
          value="ACTIVE"
          subtext="Arena Connected · Ready"
          icon={CheckCircle2}
          iconBgColor="bg-emerald-50 dark:bg-emerald-950/40"
          iconColor="text-emerald-600 dark:text-emerald-400"
          badgeText="Live Session"
          badgeType="success"
        />

      </div>

      {/* MAIN WORKSPACE SECTION */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* LEFT / LARGE: Ask Kairos Assistant Launchpad */}
        <div className="lg:col-span-8 space-y-6">
          <div className="kairos-card p-6 sm:p-8 space-y-6 flex flex-col justify-between min-h-[320px]">
            
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="p-3 rounded-2xl bg-slate-950 dark:bg-white text-white dark:text-slate-950 shadow-md">
                  <Bot className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-2xl font-extrabold text-slate-950 dark:text-white uppercase tracking-tight">
                    Ask Kairos
                  </h3>
                  <p className="text-xs font-mono font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mt-0.5">
                    Grounded AI Reasoning Engine
                  </p>
                </div>
              </div>

              <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed font-normal">
                Use the event knowledge base to investigate, reason, and find grounded answers for your team's challenge queries.
              </p>
            </div>

            <div className="pt-4 border-t border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 dark:text-slate-400">
                <Zap className="w-4 h-4 text-amber-500" />
                <span>{questionsRemaining} token(s) available for your team</span>
              </div>

              <button
                onClick={() => navigate('/assistant')}
                className="kairos-btn-primary py-3 px-6 text-sm font-extrabold tracking-wider uppercase justify-center group"
              >
                <span>Launch Ask Kairos</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </button>
            </div>

          </div>
        </div>

        {/* RIGHT: Event Resources & Quick Access */}
        <div className="lg:col-span-4 space-y-6">
          <div className="kairos-card p-6 space-y-4">
            
            <h3 className="text-base font-extrabold text-slate-950 dark:text-white uppercase tracking-tight flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-slate-700 dark:text-slate-300" />
              <span>Event Resources</span>
            </h3>

            <div className="space-y-2.5">
              
              {/* Documents Quick Link */}
              <div
                onClick={() => navigate('/documents')}
                className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-900/60 hover:bg-slate-100 dark:hover:bg-slate-800/80 border border-slate-200/80 dark:border-slate-800 cursor-pointer transition-colors flex items-center justify-between group"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                    <FileText className="w-4 h-4 text-slate-700 dark:text-slate-300" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-slate-950 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                      Event Documents
                    </h4>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400">
                      {documents.length || 3} indexed sources
                    </p>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-400 group-hover:translate-x-0.5 transition-transform" />
              </div>

              {/* Competition Rules Quick Link */}
              <div
                onClick={() => navigate('/rules')}
                className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-900/60 hover:bg-slate-100 dark:hover:bg-slate-800/80 border border-slate-200/80 dark:border-slate-800 cursor-pointer transition-colors flex items-center justify-between group"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                    <BookOpen className="w-4 h-4 text-slate-700 dark:text-slate-300" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-slate-950 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                      Competition Rules
                    </h4>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400">
                      Session & quota guidelines
                    </p>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-400 group-hover:translate-x-0.5 transition-transform" />
              </div>

              {/* Team Profile Quick Link */}
              <div
                onClick={() => navigate('/team')}
                className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-900/60 hover:bg-slate-100 dark:hover:bg-slate-800/80 border border-slate-200/80 dark:border-slate-800 cursor-pointer transition-colors flex items-center justify-between group"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                    <Users className="w-4 h-4 text-slate-700 dark:text-slate-300" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-slate-950 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                      Team Details
                    </h4>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400">
                      {memberNames.length} student member(s)
                    </p>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-400 group-hover:translate-x-0.5 transition-transform" />
              </div>

            </div>

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
