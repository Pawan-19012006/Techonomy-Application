import React from 'react';
import { Bot, User, Sparkles, FileText } from 'lucide-react';
import { ChatMessage as ChatMessageType } from '../../types';
import { MarkdownRenderer } from './MarkdownRenderer';

interface ChatMessageProps {
  message: ChatMessageType;
  isStreaming?: boolean;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message, isStreaming }) => {
  const isUser = message.sender === 'user';
  const hasSources = !isUser && message.sources && message.sources.length > 0;

  return (
    <div className={`flex gap-3.5 my-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-xl bg-indigo-600 text-white flex items-center justify-center shrink-0 shadow-sm mt-0.5">
          <Bot className="w-4 h-4" />
        </div>
      )}

      <div className={`max-w-3xl space-y-2 ${isUser ? 'items-end' : 'items-start'}`}>
        {/* Message Bubble Container */}
        <div
          className={`p-4 rounded-2xl shadow-sm text-sm leading-relaxed ${
            isUser
              ? 'bg-indigo-600 text-white rounded-br-none'
              : 'bg-white dark:bg-slate-800/90 border border-slate-200/80 dark:border-slate-700/80 text-slate-900 dark:text-slate-100 rounded-bl-none'
          }`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.text}</p>
          ) : (
            <MarkdownRenderer content={message.text} isStreaming={isStreaming} />
          )}

          {/* Sources Badge Section */}
          {hasSources && (
            <div className="mt-3.5 pt-2.5 border-t border-slate-100 dark:border-slate-700/60">
              <div className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 mb-1.5 flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-indigo-500" />
                Referenced Sources ({message.sources!.length})
              </div>
              <div className="flex flex-wrap items-center gap-1.5">
                {message.sources!.map((source, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-indigo-50/80 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 border border-indigo-200/60 dark:border-indigo-800/50 font-mono text-[11px]"
                  >
                    <FileText className="w-3 h-3 text-indigo-500" />
                    {source.document}{source.page != null ? ` (p. ${source.page})` : ''}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer / Attribution Info */}
        {!isUser && (
          <div className="flex flex-wrap items-center gap-2 text-[11px] text-slate-400 pl-1">
            <span className="flex items-center gap-1 font-mono text-slate-400">
              <Sparkles className="w-3 h-3 text-indigo-500" />
              Knowledge Assistant
            </span>
            <span>•</span>
            <span>{message.timestamp}</span>
          </div>
        )}

        {isUser && (
          <div className="text-[11px] text-slate-400 text-right pr-1">
            {message.timestamp}
          </div>
        )}
      </div>

      {isUser && (
        <div className="w-8 h-8 rounded-xl bg-slate-900 text-white flex items-center justify-center shrink-0 border border-slate-700 mt-0.5">
          <User className="w-4 h-4" />
        </div>
      )}
    </div>
  );
};
