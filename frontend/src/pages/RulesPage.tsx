import React from 'react';
import { BookOpen, ShieldCheck, HelpCircle, Clock, CheckCircle2, FileText, Zap } from 'lucide-react';
import { useEventDetails } from '../hooks/useEvent';

export const RulesPage: React.FC = () => {
  const { data: eventDetails } = useEventDetails();

  return (
    <div className="space-y-6 max-w-4xl">
      
      {/* Header Banner */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-950 dark:text-white">
          Rules & Guidelines
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Official challenge governance, system usage policies, question quotas, and execution rules.
        </p>
      </div>

      {/* Rules Grid */}
      <div className="space-y-6">
        
        {/* Objective & Overview Card */}
        <div className="kairos-card p-6 space-y-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white">
              <BookOpen className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-950 dark:text-white">
                {eventDetails?.name || 'Kairos Enterprise Challenge'}
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Official Event Specification
              </p>
            </div>
          </div>

          <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
            {eventDetails?.description ||
              'Analyze company documents, financial statements, and market research reports to deliver actionable business intelligence and strategic growth recommendations.'}
          </p>

          {eventDetails?.business_objective && (
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200/80 dark:border-slate-800 text-xs space-y-1">
              <span className="font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 block">
                Primary Business Objective:
              </span>
              <p className="font-bold text-slate-950 dark:text-white text-sm">
                {eventDetails.business_objective}
              </p>
            </div>
          )}
        </div>

        {/* Quota & Execution Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          
          <div className="kairos-card p-6 space-y-4">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-xl bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400">
                <Zap className="w-5 h-5" />
              </div>
              <h4 className="text-sm font-bold text-slate-950 dark:text-white">
                Question Quota Governance
              </h4>
            </div>

            <ul className="space-y-3 text-xs text-slate-600 dark:text-slate-300">
              <li className="flex items-start gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                <span>Each team receives an absolute allocation of 10 AI questions for the event session.</span>
              </li>
              <li className="flex items-start gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                <span>Submissions to Ask Kairos consume 1 question token atomically via PostgreSQL locks.</span>
              </li>
              <li className="flex items-start gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                <span>Submissions attempted after exhausting 10 tokens will be rejected (HTTP 429).</span>
              </li>
            </ul>
          </div>

          <div className="kairos-card p-6 space-y-4">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-xl bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400">
                <Clock className="w-5 h-5" />
              </div>
              <h4 className="text-sm font-bold text-slate-950 dark:text-white">
                Timer & UTC Synchronization
              </h4>
            </div>

            <ul className="space-y-3 text-xs text-slate-600 dark:text-slate-300">
              <li className="flex items-start gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-blue-500 shrink-0 mt-0.5" />
                <span>Timer duration is computed dynamically by the FastAPI backend server.</span>
              </li>
              <li className="flex items-start gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-blue-500 shrink-0 mt-0.5" />
                <span>Client-side timer manipulation is prevented via UTC timestamp validation.</span>
              </li>
              <li className="flex items-start gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-blue-500 shrink-0 mt-0.5" />
                <span>When the timer reaches 00:00:00, submission routes are automatically paused.</span>
              </li>
            </ul>
          </div>

        </div>

        {/* Security & Data Governance */}
        <div className="kairos-card p-6 space-y-3">
          <div className="flex items-center gap-2.5">
            <ShieldCheck className="w-5 h-5 text-slate-950 dark:text-white" />
            <h4 className="text-sm font-bold text-slate-950 dark:text-white">
              Data Security & Privacy Audit Policy
            </h4>
          </div>
          <div className="space-y-2 text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
            <p>1. All document vectors are indexed exclusively into your team's designated Qdrant collection space.</p>
            <p>2. Backend LLM routing strips unnecessary user metadata and enforces key privacy audit standards.</p>
            <p>3. Answers must strictly reference grounded chunks retrieved from official uploaded documents.</p>
          </div>
        </div>

      </div>

    </div>
  );
};
