import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Bot, User, Sparkles, FileText, Copy, Check, ExternalLink } from 'lucide-react';
import { ChatMessage as ChatMessageType } from '../../types';
import { MarkdownRenderer } from './MarkdownRenderer';
import { toast } from 'sonner';

interface ChatMessageProps {
  message: ChatMessageType;
  isStreaming?: boolean;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message, isStreaming }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const isUser = message.sender === 'user';
  const hasSources = !isUser && message.sources && message.sources.length > 0;
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (!message.text) return;
    navigator.clipboard.writeText(message.text);
    setCopied(true);
    toast.success('Response copied to clipboard');
    setTimeout(() => setCopied(false), 2000);
  };

  const handleCitationClick = (docName: string, pageNum?: number | null) => {
    const cleanDoc = docName.trim();
    const pageParam = pageNum && pageNum > 0 ? `?page=${pageNum}` : '';
    const prefix = location.pathname.startsWith('/admin') ? '/admin/documents' : '/documents';
    navigate(`${prefix}/${encodeURIComponent(cleanDoc)}${pageParam}`);
  };

  return (
    <div className={`flex gap-3.5 my-5 ${isUser ? 'justify-end' : 'justify-start'}`}>
      
      {/* Kairos Avatar */}
      {!isUser && (
        <div className="w-8 h-8 rounded-xl bg-slate-950 dark:bg-white text-white dark:text-slate-950 flex items-center justify-center shrink-0 shadow-sm mt-1">
          <Sparkles className="w-4 h-4 fill-current" />
        </div>
      )}

      <div className={`max-w-3xl space-y-2 ${isUser ? 'items-end' : 'items-start'}`}>
        
        {/* Message Card */}
        <div
          className={`p-4 sm:p-5 rounded-2xl shadow-sm text-sm leading-relaxed transition-colors ${
            isUser
              ? 'bg-slate-900 dark:bg-white text-white dark:text-slate-950 rounded-br-xs font-medium'
              : 'bg-white dark:bg-[#141C2E] border border-slate-200/90 dark:border-slate-800 text-slate-950 dark:text-slate-100 rounded-bl-xs'
          }`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.text}</p>
          ) : (
            <MarkdownRenderer content={message.text} isStreaming={isStreaming} />
          )}

          {/* Sources Section (Refinement from Section 10 of prompt) */}
          {hasSources && (
            <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800/80 space-y-2">
              <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-slate-700 dark:text-slate-300" />
                <span>Citations & Referenced Sources ({message.sources!.length})</span>
              </div>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {message.sources!.map((source, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleCitationClick(source.document, source.page)}
                    className="flex items-center justify-between gap-2 p-2.5 rounded-xl bg-slate-50 dark:bg-slate-900/60 hover:bg-slate-100 dark:hover:bg-slate-800/90 border border-slate-200/80 dark:border-slate-800 text-xs text-left transition-all group cursor-pointer"
                    title={`Open ${source.document} at Page ${source.page || 1}`}
                  >
                    <div className="flex items-center gap-2.5 truncate flex-1">
                      <div className="p-1.5 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-indigo-600 dark:text-indigo-400 group-hover:scale-105 transition-transform">
                        <FileText className="w-3.5 h-3.5" />
                      </div>
                      <div className="truncate flex-1">
                        <p className="font-bold text-slate-950 dark:text-white truncate group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                          {source.document}
                        </p>
                        <p className="text-[10px] font-mono text-slate-500 dark:text-slate-400">
                          {source.page != null ? `Page ${source.page}` : 'Verified Source'}
                        </p>
                      </div>
                    </div>
                    <ExternalLink className="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-900 dark:group-hover:text-white shrink-0 group-hover:translate-x-0.5 transition-all" />
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Action Controls & Footer Metadata */}
        {!isUser && message.text && (
          <div className="flex items-center justify-between gap-4 text-[11px] text-slate-400 px-1 pt-0.5">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-slate-700 dark:text-slate-300">Kairos Response</span>
              <span>•</span>
              <span>{message.timestamp}</span>
            </div>
            
            <button
              onClick={handleCopy}
              className="flex items-center gap-1 hover:text-slate-700 dark:hover:text-slate-200 transition-colors p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800"
              title="Copy Answer"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>
          </div>
        )}

        {isUser && (
          <div className="text-[11px] text-slate-400 text-right pr-1">
            {message.timestamp}
          </div>
        )}

      </div>

      {/* User Avatar */}
      {isUser && (
        <div className="w-8 h-8 rounded-xl bg-slate-200 dark:bg-slate-800 text-slate-900 dark:text-white flex items-center justify-center shrink-0 border border-slate-300 dark:border-slate-700 font-bold text-xs mt-1">
          <User className="w-4 h-4" />
        </div>
      )}

    </div>
  );
};
