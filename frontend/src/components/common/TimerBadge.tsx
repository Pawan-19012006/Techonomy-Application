import React, { useState, useEffect } from 'react';
import { Clock } from 'lucide-react';

interface TimerBadgeProps {
  initialSeconds: number;
}

export const TimerBadge: React.FC<TimerBadgeProps> = ({ initialSeconds }) => {
  const [seconds, setSeconds] = useState<number>(initialSeconds);

  useEffect(() => {
    setSeconds(initialSeconds);
  }, [initialSeconds]);

  useEffect(() => {
    if (seconds <= 0) return;
    const timer = setInterval(() => {
      setSeconds((prev) => Math.max(0, prev - 1));
    }, 1000);
    return () => clearInterval(timer);
  }, [seconds]);

  const formatTime = (totalSeconds: number) => {
    const hrs = Math.floor(totalSeconds / 3600);
    const mins = Math.floor((totalSeconds % 3600) / 60);
    const secs = totalSeconds % 60;
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="flex items-center gap-2 bg-slate-800/80 text-white px-3 py-1.5 rounded-lg border border-slate-700 text-xs font-mono font-medium">
      <Clock className="w-3.5 h-3.5 text-indigo-400 animate-pulse" />
      <div className="flex flex-col">
        <span className="text-[10px] uppercase text-slate-400 leading-tight">Time Left</span>
        <span className="text-xs font-bold text-white tracking-wide">{formatTime(seconds)}</span>
      </div>
    </div>
  );
};
