import React, { useState, useRef, useEffect } from 'react';
import { Sparkles, Trash2, Zap, AlertCircle } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { ChatMessage } from '../components/chat/ChatMessage';
import { ChatInput } from '../components/chat/ChatInput';
import { ChatMessage as ChatMessageType, SourceItem } from '../types';
import { sendChatMessageStream } from '../services/api';
import { toast } from 'sonner';

const CHAT_HISTORY_KEY = 'kairos_chat_history';

const DEFAULT_INITIAL_MESSAGES: ChatMessageType[] = [
  {
    id: '1',
    sender: 'assistant',
    text: "Hello Team! I am **Kairos**, your AI assistant for the event knowledge base. Ask me any question about the competition documents.",
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  },
];

export const KnowledgeAssistantPage: React.FC = () => {
  const { user, refetchTeam } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [streamingMsgId, setStreamingMsgId] = useState<string | null>(null);

  const [messages, setMessages] = useState<ChatMessageType[]>(() => {
    const saved = localStorage.getItem(CHAT_HISTORY_KEY);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          return parsed;
        }
      } catch (e) {
        console.error('Failed to load chat history:', e);
      }
    }
    return DEFAULT_INITIAL_MESSAGES;
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Authoritative Team Quota calculation from PostgreSQL backend
  const questionLimit = user?.question_limit ?? 10;
  const questionsUsed = user?.questions_used ?? 0;
  const questionsRemaining = user?.questions_remaining ?? Math.max(0, questionLimit - questionsUsed);
  const questionsExhausted = questionsRemaining <= 0;

  // Sync team quota on mount
  useEffect(() => {
    if (refetchTeam) {
      refetchTeam();
    }
  }, []);

  useEffect(() => {
    localStorage.setItem(CHAT_HISTORY_KEY, JSON.stringify(messages));
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isSubmitting, streamingMsgId]);

  const handleSendMessage = async (text: string) => {
    if (!text.trim() || isSubmitting || questionsExhausted) return;

    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const userMsg: ChatMessageType = {
      id: Date.now().toString(),
      sender: 'user',
      text: text.trim(),
      timestamp,
    };

    const assistantMsgId = (Date.now() + 1).toString();
    const assistantPlaceholder: ChatMessageType = {
      id: assistantMsgId,
      sender: 'assistant',
      text: '',
      timestamp,
    };

    setMessages((prev) => [...prev, userMsg, assistantPlaceholder]);
    setIsSubmitting(true);
    setStreamingMsgId(assistantMsgId);

    const activeTeamName = user?.team_name || (() => {
      const stored = localStorage.getItem('techonomy_team');
      return stored ? JSON.parse(stored).team_name : 'TEAM-01';
    })();

    let accumulatedText = '';

    await sendChatMessageStream(activeTeamName, text.trim(), {
      onChunk: (token: string) => {
        accumulatedText += token;
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId ? { ...msg, text: accumulatedText } : msg
          )
        );
      },
      onComplete: async (sources: SourceItem[]) => {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId ? { ...msg, sources } : msg
          )
        );
        setIsSubmitting(false);
        setStreamingMsgId(null);
        // Refresh authoritative team quota after successful question submission
        if (refetchTeam) {
          await refetchTeam();
        }
      },
      onError: async (err: Error) => {
        console.error('Streaming error:', err);
        const userMsg = err.message || 'Error generating AI response.';
        toast.error(userMsg);
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId
              ? {
                  ...msg,
                  text: `⚠️ **Request Error**: ${userMsg}`,
                  status: 'error',
                }
              : msg
          )
        );
        setIsSubmitting(false);
        setStreamingMsgId(null);
        // Refresh authoritative team quota state
        if (refetchTeam) {
          await refetchTeam();
        }
      },
    });
  };

  const handleClearHistory = () => {
    setMessages(DEFAULT_INITIAL_MESSAGES);
    localStorage.removeItem(CHAT_HISTORY_KEY);
    toast.success('Conversation history cleared.');
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6 select-none">
      
      {/* PAGE HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200/80 dark:border-slate-800">
        <div>
          <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-slate-950 dark:text-white uppercase font-sans">
            ASK KAIROS
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            Your AI assistant for the event knowledge base.
          </p>
        </div>

        <div className="flex items-center gap-3">
          
          {/* Authoritative Persistent Team Quota Badge */}
          <div
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-mono font-bold transition-all ${
              questionsExhausted
                ? 'bg-red-50 dark:bg-red-950/40 border-red-300 dark:border-red-800 text-red-600 dark:text-red-400'
                : 'bg-amber-50 dark:bg-amber-950/40 border-amber-200 dark:border-amber-900/60 text-amber-800 dark:text-amber-300'
            }`}
          >
            <Zap className="w-4 h-4 text-amber-500 shrink-0" />
            <span>⚡ {questionsRemaining} / {questionLimit} remaining</span>
          </div>

          {/* Clear History */}
          <button
            onClick={handleClearHistory}
            className="kairos-btn-secondary py-1.5 px-3 text-xs"
            title="Clear Conversation"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Clear</span>
          </button>

        </div>
      </div>

      {/* PRIMARY CHATBOT WORKSPACE (Occupies 80%+ of content area) */}
      <div className="kairos-card p-4 sm:p-6 flex flex-col min-h-[600px] max-h-[750px] justify-between shadow-xl relative overflow-hidden">
        
        {/* Messages Scroll Container */}
        <div className="flex-1 overflow-y-auto pr-2 space-y-2">
          {messages.map((msg) => (
            <ChatMessage
              key={msg.id}
              message={msg}
              isStreaming={msg.id === streamingMsgId}
            />
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Quota Exhaustion Warning Banner */}
        {questionsExhausted && (
          <div className="my-3 p-3.5 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/60 text-amber-800 dark:text-amber-300 text-xs flex items-center justify-between">
            <div className="flex items-center gap-2 font-bold">
              <AlertCircle className="w-4 h-4 text-amber-500 shrink-0" />
              <span>Team question quota exhausted ({questionsUsed}/{questionLimit} questions used).</span>
            </div>
            <span className="text-[11px] font-mono text-amber-600 dark:text-amber-400">LOCKED</span>
          </div>
        )}

        {/* Bottom Composer Bar */}
        <div className="pt-4 border-t border-slate-100 dark:border-slate-800">
          <ChatInput
            onSend={handleSendMessage}
            isLoading={isSubmitting}
            disabled={questionsExhausted}
          />
        </div>

      </div>

    </div>
  );
};
