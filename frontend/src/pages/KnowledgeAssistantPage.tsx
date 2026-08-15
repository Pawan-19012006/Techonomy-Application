import React, { useState, useRef, useEffect } from 'react';
import { Bot, Sparkles, Trash2 } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { ChatMessage } from '../components/chat/ChatMessage';
import { ChatInput } from '../components/chat/ChatInput';
import { ChatMessage as ChatMessageType, SourceItem } from '../types';
import { sendChatMessage, sendChatMessageStream } from '../services/api';
import { toast } from 'sonner';

const CHAT_HISTORY_KEY = 'techonomy_chat_history';

const DEFAULT_INITIAL_MESSAGES: ChatMessageType[] = [
  {
    id: '1',
    sender: 'assistant',
    text: "Hello Team! I'm your **AI Knowledge Assistant**. Ask me anything about your uploaded company documents, financial figures, or event metrics.",
    timestamp: '09:00 AM',
  },
];

export const KnowledgeAssistantPage: React.FC = () => {
  const { user } = useAuth();
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

  // Sync messages state to localStorage
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
    if (!text.trim() || isSubmitting) return;

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
        setStreamingMsgId(null);
        setIsSubmitting(false);
      },
      onError: async (streamErr: Error) => {
        console.warn('Streaming connection issue, attempting REST fallback:', streamErr);
        // Fallback to synchronous REST /api/chat if streaming had no tokens
        if (!accumulatedText.trim()) {
          try {
            const restResponse = await sendChatMessage(activeTeamName, text.trim());
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMsgId
                  ? { ...msg, text: restResponse.answer, sources: restResponse.sources }
                  : msg
              )
            );
          } catch (restErr: any) {
            console.error('REST Chat error:', restErr);
            const userFacingMsg =
              restErr?.userMessage ||
              restErr?.response?.data?.detail ||
              streamErr.message ||
              'Unable to connect to the Techonomy server. Please try again.';

            toast.error(userFacingMsg);
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMsgId
                  ? { ...msg, text: `⚠️ ${userFacingMsg}` }
                  : msg
              )
            );
          }
        }
        setStreamingMsgId(null);
        setIsSubmitting(false);
      },
    });
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
          <ChatMessage
            key={msg.id}
            message={msg}
            isStreaming={streamingMsgId === msg.id}
          />
        ))}

        {isSubmitting && !streamingMsgId && (
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
