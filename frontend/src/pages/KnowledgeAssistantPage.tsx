import React, { useState, useRef, useEffect } from 'react';
import { Bot, Sparkles, Trash2, HelpCircle, MessageSquarePlus, RefreshCw, Zap } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useDashboard } from '../hooks/useDashboard';
import { ChatMessage } from '../components/chat/ChatMessage';
import { ChatInput } from '../components/chat/ChatInput';
import { ChatMessage as ChatMessageType, SourceItem } from '../types';
import { sendChatMessageStream } from '../services/api';
import { toast } from 'sonner';

const CHAT_HISTORY_KEY = 'kairos_chat_history';

const SUGGESTED_PROMPTS = [
  'What are the key technical specifications in the event documents?',
  'Summarize the primary guidelines and constraints for this challenge.',
  'Extract critical data points and figures from the knowledge base.',
];

const DEFAULT_INITIAL_MESSAGES: ChatMessageType[] = [
  {
    id: '1',
    sender: 'assistant',
    text: "Hello Team! I am **Kairos**, your AI Challenge Assistant. Ask me any question to analyze your event documents and extract grounded answers for your team.",
    timestamp: '09:00 AM',
  },
];

export const KnowledgeAssistantPage: React.FC = () => {
  const { user } = useAuth();
  const { data: dashboard } = useDashboard();
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
        console.error('Failed to load chat history from localStorage:', e);
      }
    }
    return DEFAULT_INITIAL_MESSAGES;
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const questionLimit = dashboard?.question_limit || user?.question_limit || 10;
  const questionsRemaining = dashboard?.questions_remaining ?? 10;
  const questionsExhausted = questionsRemaining <= 0;

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
      onComplete: (sources: SourceItem[]) => {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId ? { ...msg, sources } : msg
          )
        );
        setIsSubmitting(false);
        setStreamingMsgId(null);
      },
      onError: (err: Error) => {
        console.error('Streaming error:', err);
        const userMsg = err.message || 'Error generating AI response.';
        toast.error(userMsg);
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId
              ? {
                  ...msg,
                  text: `⚠️ **Error**: ${userMsg}`,
                  status: 'error',
                }
              : msg
          )
        );
        setIsSubmitting(false);
        setStreamingMsgId(null);
      },
    });
  };

  const handleClearHistory = () => {
    setMessages(DEFAULT_INITIAL_MESSAGES);
    localStorage.removeItem(CHAT_HISTORY_KEY);
    toast.success('Conversation history cleared.');
  };

  return (
    <div className="space-y-6">
      
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200/80 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-950 dark:text-white">
              Ask Kairos
            </h1>
            <span className="px-2.5 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 text-xs font-semibold">
              RAG v2.0
            </span>
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Investigate event documents and generate grounded answers for your team.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Quota Badge */}
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/60 text-amber-800 dark:text-amber-300 text-xs font-semibold">
            <Zap className="w-4 h-4 text-amber-500" />
            <span>{questionsRemaining} / {questionLimit} Quota</span>
          </div>

          {/* Clear History */}
          <button
            onClick={handleClearHistory}
            className="kairos-btn-secondary text-xs"
            title="Clear Chat History"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Clear Chat</span>
          </button>
        </div>
      </div>

      {/* Main Chat Layout Container */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Suggestions & History Column */}
        <div className="lg:col-span-4 space-y-4">
          
          <div className="kairos-card p-5 space-y-4">
            <div className="flex items-center gap-2 text-slate-950 dark:text-white font-bold text-sm">
              <Sparkles className="w-4 h-4 text-amber-500" />
              <span>Suggested Queries</span>
            </div>
            
            <div className="space-y-2">
              {SUGGESTED_PROMPTS.map((promptText, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSendMessage(promptText)}
                  disabled={isSubmitting || questionsExhausted}
                  className="w-full text-left p-3 rounded-xl bg-slate-50 dark:bg-slate-900/60 hover:bg-slate-100 dark:hover:bg-slate-800/80 border border-slate-200/80 dark:border-slate-800 text-xs text-slate-700 dark:text-slate-300 transition-colors flex items-start gap-2.5 group disabled:opacity-50"
                >
                  <MessageSquarePlus className="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-900 dark:group-hover:text-white shrink-0 mt-0.5" />
                  <span className="leading-snug">{promptText}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="kairos-card p-5 space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Vector Grounding
            </h4>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              Every query triggers cosine similarity matching against 384-dimensional dense vectors in Qdrant Cloud.
            </p>
          </div>

        </div>

        {/* Right Chat Messaging Column */}
        <div className="lg:col-span-8 space-y-4">
          <div className="kairos-card p-4 sm:p-6 flex flex-col min-h-[500px] max-h-[650px] justify-between">
            
            {/* Messages Scroll Area */}
            <div className="flex-1 overflow-y-auto pr-1 space-y-2">
              {messages.map((msg) => (
                <ChatMessage
                  key={msg.id}
                  message={msg}
                  isStreaming={msg.id === streamingMsgId}
                />
              ))}
              <div ref={messagesEndRef} />
            </div>

            {/* Bottom Composer */}
            <div className="pt-4 border-t border-slate-100 dark:border-slate-800/80">
              <ChatInput
                onSend={handleSendMessage}
                isLoading={isSubmitting}
                disabled={questionsExhausted}
              />
            </div>

          </div>
        </div>

      </div>

    </div>
  );
};
