import React, { useState, useRef, useEffect } from 'react';
import { Bot, Sparkles, Trash2 } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { ChatMessage } from '../components/chat/ChatMessage';
import { ChatInput } from '../components/chat/ChatInput';
import { ChatMessage as ChatMessageType } from '../types';
import { sendChatMessage } from '../services/api';
import { toast } from 'sonner';

const CHAT_HISTORY_KEY = 'techonomy_chat_history';

const DEFAULT_INITIAL_MESSAGES: ChatMessageType[] = [
  {
    id: '1',
    sender: 'assistant',
    text: "Hello Team! I'm your AI Knowledge Assistant. Ask me anything about the company documents.",
    timestamp: '09:00 AM',
  },
];

export const KnowledgeAssistantPage: React.FC = () => {
  const { user } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

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

  // Sync messages state to localStorage
  useEffect(() => {
    localStorage.setItem(CHAT_HISTORY_KEY, JSON.stringify(messages));
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isSubmitting]);

  const handleSendMessage = async (text: string) => {
    if (!text.trim() || isSubmitting) return;

    const userMsg: ChatMessageType = {
      id: Date.now().toString(),
      sender: 'user',
      text: text.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsSubmitting(true);

    const activeTeamName = user?.team_name || (() => {
      const stored = localStorage.getItem('techonomy_team');
      return stored ? JSON.parse(stored).team_name : 'TEAM-01';
    })();

    try {
      const response = await sendChatMessage(activeTeamName, text.trim());

      const assistantMsg: ChatMessageType = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text: response.answer,
        sources: response.sources,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      console.error('Chat error:', err);
      const userFacingMsg =
        err?.userMessage ||
        err?.response?.data?.detail ||
        'Unable to connect to the Techonomy server. Please try again.';

      toast.error(userFacingMsg);

      const errorMsg: ChatMessageType = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text: `⚠️ ${userFacingMsg}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClearHistory = () => {
    setMessages(DEFAULT_INITIAL_MESSAGES);
    localStorage.setItem(CHAT_HISTORY_KEY, JSON.stringify(DEFAULT_INITIAL_MESSAGES));
    toast.info('Chat view reset.');
  };

  return (
    <div className="h-[calc(100vh-6.5rem)] flex flex-col justify-between space-y-4">
      {/* Header Banner */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800 shrink-0">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-indigo-600 text-white shadow-md shadow-indigo-600/30">
            <Bot className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900 dark:text-slate-50 leading-tight">
              Knowledge Assistant
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Interactive document query engine connected to Techonomy backend
            </p>
          </div>
        </div>

        <button
          onClick={handleClearHistory}
          className="p-2 text-slate-400 hover:text-red-500 dark:hover:text-red-400 rounded-lg transition-colors flex items-center gap-1.5 text-xs border border-slate-200 dark:border-slate-800"
          title="Clear visible chat history"
        >
          <Trash2 className="w-4 h-4" />
          <span className="hidden sm:inline">Clear Chat</span>
        </button>
      </div>

      {/* Chat Messages Log Area */}
      <div className="flex-1 overflow-y-auto pr-2 space-y-2 rounded-xl">
        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}

        {isSubmitting && (
          <div className="flex items-center gap-3 my-4 text-slate-400 text-xs pl-2">
            <div className="w-8 h-8 rounded-xl bg-indigo-600 text-white flex items-center justify-center animate-pulse">
              <Sparkles className="w-4 h-4" />
            </div>
            <span className="font-mono animate-pulse">Knowledge Assistant is analyzing document context...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Box Footer */}
      <div className="pt-2 border-t border-slate-200 dark:border-slate-800 shrink-0">
        <ChatInput
          onSend={handleSendMessage}
          isLoading={isSubmitting}
          disabled={isSubmitting}
        />
      </div>
    </div>
  );
};
