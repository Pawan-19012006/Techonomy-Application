import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, ArrowUp, CornerDownLeft } from 'lucide-react';

interface ChatInputProps {
  onSend: (text: string) => void;
  isLoading: boolean;
  disabled?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSend, isLoading, disabled = false }) => {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  // Auto-focus input when loading finishes
  useEffect(() => {
    if (!isLoading && !disabled && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [isLoading, disabled]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || isLoading || disabled) return;
    onSend(input.trim());
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative space-y-2">
      <div className="relative flex items-end bg-white dark:bg-[#141C2E] border border-slate-200 dark:border-slate-800 rounded-2xl shadow-md p-2 transition-colors focus-within:border-slate-900 dark:focus-within:border-slate-100">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          placeholder={
            disabled
              ? 'Team question quota exhausted.'
              : 'Ask Kairos about the event documents...'
          }
          disabled={disabled || isLoading}
          className="w-full bg-transparent border-0 resize-none py-2 px-3 text-sm text-slate-950 dark:text-slate-100 focus:outline-none placeholder:text-slate-400 font-normal leading-relaxed max-h-32 min-h-[42px]"
        />

        <div className="p-1 shrink-0">
          <button
            type="submit"
            disabled={!input.trim() || isLoading || disabled}
            className="w-9 h-9 rounded-xl bg-slate-950 dark:bg-white text-white dark:text-slate-950 flex items-center justify-center disabled:opacity-30 hover:opacity-90 transition-all shadow-sm active:scale-95"
            title="Send Question"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <ArrowUp className="w-4 h-4 stroke-[2.5]" />
            )}
          </button>
        </div>
      </div>

      <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 px-2">
        <span>
          {disabled ? 'QUOTA EXHAUSTED' : 'EVENT KNOWLEDGE BASE'}
        </span>
        <span className="hidden sm:inline">
          <kbd className="px-1.5 py-0.5 rounded bg-slate-200 dark:bg-slate-800 text-[10px] text-slate-700 dark:text-slate-300">Enter</kbd> to submit · <kbd className="px-1.5 py-0.5 rounded bg-slate-200 dark:bg-slate-800 text-[10px] text-slate-700 dark:text-slate-300">Shift + Enter</kbd> for new line
        </span>
      </div>
    </form>
  );
};
