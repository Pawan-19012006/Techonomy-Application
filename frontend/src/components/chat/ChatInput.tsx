import React, { useState } from 'react';
import { Send, Loader2, Sparkles, CornerDownLeft } from 'lucide-react';

interface ChatInputProps {
  onSend: (text: string) => void;
  isLoading: boolean;
  disabled?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSend, isLoading, disabled = false }) => {
  const [input, setInput] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading || disabled) return;
    onSend(input.trim());
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative space-y-2">
      <div className="relative flex items-center shadow-sm">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            disabled
              ? 'Question limit reached. Please contact event operator.'
              : 'Ask Kairos about company documents, financials, operational strategy...'
          }
          disabled={disabled || isLoading}
          className="kairos-input w-full pr-24 py-3.5 text-sm font-normal"
        />

        <div className="absolute right-2 flex items-center gap-2">
          <button
            type="submit"
            disabled={!input.trim() || isLoading || disabled}
            className="kairos-btn-primary py-2 px-3 text-xs disabled:opacity-30 transition-all"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <>
                <span>Send</span>
                <CornerDownLeft className="w-3.5 h-3.5" />
              </>
            )}
          </button>
        </div>
      </div>

      <div className="flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400 px-1">
        <span className="flex items-center gap-1">
          <Sparkles className="w-3 h-3 text-slate-700 dark:text-slate-300" />
          Grounded in official indexed documents
        </span>
        <span className="hidden sm:inline">Press <kbd className="px-1.5 py-0.5 rounded bg-slate-200 dark:bg-slate-800 text-[10px] font-mono text-slate-700 dark:text-slate-300">Enter</kbd> to submit</span>
      </div>
    </form>
  );
};
