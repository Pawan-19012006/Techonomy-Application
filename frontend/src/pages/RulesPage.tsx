import React from 'react';
import {
  Calendar,
  MapPin,
  Clock,
  Laptop,
  Ban,
  FileCheck,
  AlertTriangle,
  Award,
  CheckCircle2,
  AlertCircle,
  Flame,
} from 'lucide-react';

export const RulesPage: React.FC = () => {
  return (
    <div className="space-y-8 max-w-5xl mx-auto select-none">
      
      {/* Header Title Section */}
      <div className="p-6 sm:p-8 rounded-3xl bg-gradient-to-r from-slate-950 via-[#0B0F19] to-slate-900 text-white border border-slate-800 shadow-xl space-y-3">
        <div className="flex items-center gap-2">
          <span className="px-3 py-1 rounded-full bg-indigo-500/20 text-indigo-400 font-mono text-xs font-bold border border-indigo-500/30 uppercase tracking-widest">
            KAIROS 2026
          </span>
          <span className="text-xs font-mono text-slate-400">OFFICIAL DIRECTIVE</span>
        </div>
        <h1 className="text-2xl sm:text-4xl font-black uppercase tracking-tight font-sans">
          PARTICIPANT GENERAL INSTRUCTIONS & GUIDELINES
        </h1>
        <p className="text-xs sm:text-sm text-slate-300 font-medium">
          Please review all competition rules, hardware requirements, prohibited items, and submission guidelines carefully.
        </p>
      </div>

      {/* QUICK EVENT DETAILS (4 Top Cards) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        <div className="p-5 rounded-2xl bg-white dark:bg-[#0F172A] border border-slate-200 dark:border-slate-800 space-y-2 shadow-sm">
          <div className="flex items-center justify-between text-xs font-mono font-bold uppercase text-slate-400">
            <span>Date</span>
            <Calendar className="w-4 h-4 text-indigo-500" />
          </div>
          <div className="text-lg font-black text-slate-900 dark:text-white font-sans">
            19 August 2026
          </div>
          <p className="text-[11px] font-mono text-slate-400">Official Event Date</p>
        </div>

        <div className="p-5 rounded-2xl bg-white dark:bg-[#0F172A] border border-slate-200 dark:border-slate-800 space-y-2 shadow-sm">
          <div className="flex items-center justify-between text-xs font-mono font-bold uppercase text-slate-400">
            <span>Venue</span>
            <MapPin className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="text-lg font-black text-slate-900 dark:text-white font-sans">
            403 Lab, CITAR
          </div>
          <p className="text-[11px] font-mono text-slate-400">Competition Venue</p>
        </div>

        <div className="p-5 rounded-2xl bg-white dark:bg-[#0F172A] border border-slate-200 dark:border-slate-800 space-y-2 shadow-sm">
          <div className="flex items-center justify-between text-xs font-mono font-bold uppercase text-slate-400">
            <span>Duration</span>
            <Clock className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-lg font-black text-slate-900 dark:text-white font-sans">
            2 Hours 30 Mins
          </div>
          <p className="text-[11px] font-mono text-slate-400">Per Allotted Batch</p>
        </div>

        <div className="p-5 rounded-2xl bg-white dark:bg-[#0F172A] border border-slate-200 dark:border-slate-800 space-y-2 shadow-sm">
          <div className="flex items-center justify-between text-xs font-mono font-bold uppercase text-slate-400">
            <span>Reporting Time</span>
            <AlertCircle className="w-4 h-4 text-blue-500" />
          </div>
          <div className="text-lg font-black text-slate-900 dark:text-white font-sans">
            5–10 Mins Before
          </div>
          <p className="text-[11px] font-mono text-slate-400">Report Before Batch</p>
        </div>

      </div>

      {/* BATCH TIMINGS BANNER */}
      <div className="p-6 rounded-2xl bg-indigo-950/40 border border-indigo-900/60 text-indigo-200 space-y-3 shadow-md">
        <div className="flex items-center gap-2 font-mono text-xs font-extrabold uppercase text-indigo-400 tracking-wider">
          <Clock className="w-4 h-4 text-indigo-400" />
          <span>BATCH TIMINGS</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
          <div className="p-4 rounded-xl bg-slate-900/90 border border-indigo-900/50 font-sans">
            <span className="text-xs font-mono font-bold text-slate-400 uppercase block">BATCH 1</span>
            <span className="text-xl font-black text-white">9:00 AM – 11:30 AM</span>
          </div>
          <div className="p-4 rounded-xl bg-slate-900/90 border border-indigo-900/50 font-sans">
            <span className="text-xs font-mono font-bold text-slate-400 uppercase block">BATCH 2</span>
            <span className="text-xl font-black text-white">12:00 PM – 2:30 PM</span>
          </div>
        </div>
        <p className="text-xs font-mono text-indigo-300 italic pt-1">
          * Participants must attend only their allotted batch.
        </p>
      </div>

      {/* TWO COLUMN CARDS: HARDWARE REQUIREMENTS & PROHIBITED ITEMS */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Laptop & SEB Requirements */}
        <div className="p-6 rounded-2xl bg-white dark:bg-[#0F172A] border border-slate-200 dark:border-slate-800 space-y-4 shadow-sm">
          <div className="flex items-center gap-2.5">
            <div className="p-2.5 rounded-xl bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-900">
              <Laptop className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-extrabold text-slate-900 dark:text-white uppercase font-sans">
                LAPTOP & SEB REQUIREMENTS
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">Hardware & Environment Setup</p>
            </div>
          </div>

          <ul className="space-y-3 text-xs sm:text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-sans">
            <li className="flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
              <span>Participants must bring their <strong>own laptop</strong>, as the computers in the lab will not be used for the competition.</span>
            </li>
            <li className="flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
              <span><strong>Safe Exam Browser (SEB)</strong> and the required configuration file must be installed and ready before arriving at the venue.</span>
            </li>
            <li className="flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
              <span>Internet connectivity will be provided at the venue.</span>
            </li>
            <li className="flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
              <span>Participants must carry their valid <strong>college ID card</strong>.</span>
            </li>
            <li className="flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
              <span>Ensure that the laptop is <strong>sufficiently charged</strong> and ready for the entire duration of the competition.</span>
            </li>
          </ul>
        </div>

        {/* Prohibited Items */}
        <div className="p-6 rounded-2xl bg-red-50/50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/40 space-y-4 shadow-sm">
          <div className="flex items-center gap-2.5">
            <div className="p-2.5 rounded-xl bg-red-100 dark:bg-red-900/50 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-800">
              <Ban className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-extrabold text-red-950 dark:text-red-200 uppercase font-sans">
                PROHIBITED ITEMS
              </h3>
              <p className="text-xs text-red-600 dark:text-red-400 font-mono">Strictly Forbidden at Venue</p>
            </div>
          </div>

          <p className="text-xs text-red-700 dark:text-red-300 font-medium">
            The following are strictly prohibited during the competition:
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 font-sans">
            {[
              'Mobile phones',
              'Smartwatches / Smart devices',
              'Headphones / Earphones',
              'Calculators',
              'Pens or writing materials',
              'Unauthorized external assistance',
            ].map((item, idx) => (
              <div
                key={idx}
                className="p-3 rounded-xl bg-white/80 dark:bg-slate-900/90 border border-red-200 dark:border-red-900/50 text-xs font-bold text-red-900 dark:text-red-300 flex items-center gap-2"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-red-500 shrink-0" />
                <span>{item}</span>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* COMPETITION & SUBMISSION RULES */}
      <div className="p-6 sm:p-8 rounded-2xl bg-white dark:bg-[#0F172A] border border-slate-200 dark:border-slate-800 space-y-5 shadow-sm">
        <div className="flex items-center gap-2.5">
          <div className="p-2.5 rounded-xl bg-amber-50 dark:bg-amber-950/50 text-amber-600 dark:text-amber-400 border border-amber-200 dark:border-amber-900">
            <FileCheck className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-extrabold text-slate-900 dark:text-white uppercase font-sans">
              COMPETITION & SUBMISSION RULES
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">Timelines & Submission Protocols</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs sm:text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-sans">
          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 space-y-2">
            <span className="font-bold text-slate-950 dark:text-white block uppercase text-xs font-mono">
              Allotted Round Duration
            </span>
            <p>Each batch will have <strong>2 hours and 30 minutes</strong> to complete the round. A <strong>5-minute warning</strong> will be given before the conclusion of the competition.</p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 space-y-2">
            <span className="font-bold text-slate-950 dark:text-white block uppercase text-xs font-mono">
              Google Drive Submission
            </span>
            <p>The required <strong>Google Document</strong> must be uploaded to the Google Drive provided by the organizing team within the allotted time.</p>
          </div>

          <div className="p-4 rounded-xl bg-red-50/50 dark:bg-red-950/30 border border-red-200 dark:border-red-900/50 text-red-900 dark:text-red-300 space-y-2 md:col-span-2">
            <span className="font-bold block uppercase text-xs font-mono text-red-600 dark:text-red-400">
              Late Submission Disqualification
            </span>
            <p>Late submissions will result in <strong>direct disqualification</strong> and will not be evaluated. No submissions or modifications will be accepted after the allotted time has ended.</p>
          </div>
        </div>
      </div>

      {/* TECHNICAL ISSUES & EVALUATION DECISION */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        <div className="p-6 rounded-2xl bg-amber-50/50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900/40 space-y-3 shadow-sm">
          <div className="flex items-center gap-2.5">
            <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400" />
            <h4 className="text-sm font-extrabold text-amber-950 dark:text-amber-200 uppercase font-sans">
              TECHNICAL ISSUES & DISRUPTIONS
            </h4>
          </div>
          <p className="text-xs sm:text-sm text-amber-900 dark:text-amber-300 leading-relaxed font-sans">
            In case of any technical issue, SEB error, internet disruption, system problem, or any other unforeseen difficulty, participants must <strong>immediately inform the event coordinators/authorities in charge</strong>.
          </p>
        </div>

        <div className="p-6 rounded-2xl bg-white dark:bg-[#0F172A] border border-slate-200 dark:border-slate-800 space-y-3 shadow-sm">
          <div className="flex items-center gap-2.5">
            <Award className="w-5 h-5 text-indigo-500" />
            <h4 className="text-sm font-extrabold text-slate-900 dark:text-white uppercase font-sans">
              EVALUATION & DECISION
            </h4>
          </div>
          <ul className="space-y-2 text-xs sm:text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-sans">
            <li>• The decision of the judges and evaluation panel will be <strong>final and binding</strong>.</li>
            <li>• No requests for reconsideration or disputes regarding the final results will be entertained.</li>
            <li>• Participants are expected to maintain <strong>discipline, fairness, and professional conduct</strong> throughout the competition.</li>
          </ul>
        </div>

      </div>

      {/* IMPORTANT WARNING & FOOTER BRANDING */}
      <div className="p-8 rounded-3xl bg-gradient-to-br from-indigo-950 via-slate-900 to-slate-950 text-white border border-indigo-900/80 shadow-xl space-y-6 text-center">
        <div className="max-w-2xl mx-auto space-y-3">
          <span className="px-3 py-1 rounded-full bg-amber-500/20 text-amber-400 font-mono text-xs font-bold border border-amber-500/30 uppercase">
            IMPORTANT NOTICE
          </span>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed font-sans">
            Participants are requested to arrive on time with their laptop, college ID card, and SEB already installed and configured. All participants must strictly follow the instructions provided by the organizing team. Failure to comply with the rules may result in disqualification.
          </p>
        </div>

        <div className="pt-4 border-t border-slate-800 flex flex-col items-center justify-center space-y-2">
          <div className="flex items-center gap-2 text-amber-400 font-black text-xl tracking-wider uppercase font-sans">
            <Flame className="w-6 h-6 fill-current" />
            <span>ALL THE BEST!</span>
          </div>
          <p className="text-xs font-mono font-bold text-indigo-300 uppercase tracking-widest">
            Techonomy Team
          </p>
        </div>
      </div>

    </div>
  );
};
