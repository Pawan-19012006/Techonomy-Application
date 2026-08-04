import React from 'react';
import { BookOpen, ShieldCheck, HelpCircle, Clock, CheckCircle2, FileText } from 'lucide-react';
import { useEventDetails } from '../hooks/useEvent';

export const RulesPage: React.FC = () => {
  const { data: eventDetails } = useEventDetails();

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header Banner */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-50">
          Rules & Guidelines
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Official challenge guidelines, allowed system usage, question limits, and competition rules.
        </p>
      </div>

      {/* Primary Rules Container */}
      <div className="space-y-5">
        {/* Card 1: Objective & Event Overview */}
        <div className="enterprise-card p-6 space-y-3">
          <div className="flex items-center gap-3 text-indigo-600 dark:text-indigo-400">
            <BookOpen className="w-5 h-5" />
            <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
              {eventDetails?.name || 'Techonomy Enterprise Challenge'}
            </h3>
          </div>
          <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
            {eventDetails?.description ||
              'Analyze company documents, financial statements, and market research reports to deliver actionable business intelligence and revenue growth strategies.'}
          </p>
          {eventDetails?.business_objective && (
            <div className="p-3.5 rounded-lg bg-indigo-50/50 dark:bg-indigo-950/30 border border-indigo-100 dark:border-indigo-900/50 text-xs text-indigo-900 dark:text-indigo-200">
              <span className="font-bold uppercase tracking-wider block mb-0.5">Business Objective:</span>
              {eventDetails.business_objective}
            </div>
          )}
        </div>

        {/* Card 2: Rules & Quotas */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div className="enterprise-card p-6 space-y-3">
            <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400">
              <HelpCircle className="w-5 h-5" />
              <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                Question Limit Quota
              </h4>
            </div>
            <ul className="space-y-2 text-xs text-slate-600 dark:text-slate-300">
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                <span>Each team is allocated a strict quota of 10 AI questions for the challenge.</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                <span>Every submission to the Knowledge Assistant consumes 1 question token.</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                <span>Requests submitted after reaching 0 remaining will be rejected (HTTP 429).</span>
              </li>
            </ul>
          </div>

          <div className="enterprise-card p-6 space-y-3">
            <div className="flex items-center gap-2 text-amber-600 dark:text-amber-400">
              <Clock className="w-5 h-5" />
              <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                Timer & Execution Rules
              </h4>
            </div>
            <ul className="space-y-2 text-xs text-slate-600 dark:text-slate-300">
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
                <span>Timer duration is computed dynamically by the FastAPI backend server.</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
                <span>Client-side timer tampering is prevented through UTC synchronization.</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
                <span>When the timer reaches 00:00:00, all submission routes are paused.</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Card 3: Allowed Usage & Security Policy */}
        <div className="enterprise-card p-6 space-y-3">
          <div className="flex items-center gap-2 text-slate-900 dark:text-slate-100">
            <ShieldCheck className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
            <h4 className="text-sm font-bold">Allowed Usage & Security Policy</h4>
          </div>
          <div className="space-y-2 text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
            <p>
              1. All document uploads and metadata must comply with corporate data governance standards.
            </p>
            <p>
              2. Do not attempt to bypass API authentication headers or share JWT authorization credentials outside your registered team members.
            </p>
            <p>
              3. System events and prompt query interactions are logged for audit compliance.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
