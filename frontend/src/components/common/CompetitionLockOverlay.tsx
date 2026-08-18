import React from 'react';
import { Lock, Sparkles, ShieldAlert } from 'lucide-react';

export const CompetitionLockOverlay: React.FC = () => {
  return (
    <div className="fixed inset-0 z-[9999] bg-[#090D16] text-white flex flex-col items-center justify-center p-6 text-center select-none animate-in fade-in duration-300">
      <div className="max-w-xl space-y-6 border border-slate-800 p-8 sm:p-12 rounded-3xl bg-[#0B0F19]/90 shadow-2xl backdrop-blur-md">
        
        {/* Lock Icon */}
        <div className="w-16 h-16 rounded-2xl bg-red-950/60 text-red-400 border border-red-800/80 flex items-center justify-center mx-auto shadow-lg">
          <Lock className="w-8 h-8" />
        </div>

        {/* Header */}
        <div className="space-y-2">
          <div className="flex items-center justify-center gap-2 text-xs font-mono font-bold uppercase tracking-[0.3em] text-red-400">
            <ShieldAlert className="w-4 h-4" />
            <span>COMPETITION COMPLETE</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white uppercase">
            KAIROS ARENA CLOSED
          </h1>
        </div>

        {/* Description */}
        <p className="text-sm text-slate-300 leading-relaxed max-w-md mx-auto">
          Your 2 hour 30 minute competition session has ended. Thank you for participating in KAIROS. Your team's submission window is now closed.
        </p>

        {/* Footer */}
        <div className="pt-4 border-t border-slate-800/80 text-xs font-mono text-slate-500 flex items-center justify-center gap-2">
          <Sparkles className="w-3.5 h-3.5 text-slate-600" />
          <span>SESSION_ID // EXPIRED_00:00:00</span>
        </div>

      </div>
    </div>
  );
};
