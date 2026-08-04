import React from 'react';
import { Bot, User, Sparkles, FileText } from 'lucide-react';
import { ChatMessage as ChatMessageType } from '../../types';

interface ChatMessageProps {
  message: ChatMessageType;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.sender === 'user';

  return (
    <div className={`flex gap-3.5 my-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-xl bg-indigo-600 text-white flex items-center justify-center shrink-0 shadow-sm">
          <Bot className="w-4 h-4" />
        </div>
      )}

      <div className={`max-w-2xl space-y-2 ${isUser ? 'items-end' : 'items-start'}`}>
        {/* Bubble */}
        <div
          className={`p-4 rounded-2xl text-sm leading-relaxed ${
            isUser
              ? 'bg-indigo-600 text-white rounded-br-none shadow-sm'
              : 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 rounded-bl-none shadow-sm'
          }`}
        >
          <p className="whitespace-pre-wrap">{message.text}</p>
        </div>

        {/* Assistant Attribution Badge if applicable */}
        {!isUser && (
          <div className="flex items-center gap-2 text-[11px] text-slate-400 pl-1">
            <span className="flex items-center gap-1 font-mono">
              <Sparkles className="w-3 h-3 text-indigo-500" />
              Source: Annual_Report_2024.pdf (Page 117)
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
        <div className="w-8 h-8 rounded-xl bg-slate-900 text-white flex items-center justify-center shrink-0 border border-slate-700">
          <User className="w-4 h-4" />
        </div>
      )}
    </div>
  );
};
