import React, { useState, useRef, useEffect } from 'react';
import { Bot, Sparkles, AlertCircle } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useTeamQuestions } from '../hooks/useTeams';
import { useChatMutation } from '../hooks/useChat';
import { ChatMessage } from '../components/chat/ChatMessage';
import { ChatInput } from '../components/chat/ChatInput';
import { QuestionCounterBadge } from '../components/common/QuestionCounter';
import { ChatMessage as ChatMessageType } from '../types';

export const KnowledgeAssistantPage: React.FC = () => {
  const { user } = useAuth();
  const { data: questions } = useTeamQuestions();
  const chatMutation = useChatMutation();

  const questionsUsed = questions?.questions_used ?? user?.questions_used ?? 0;
  const questionLimit = questions?.question_limit ?? user?.question_limit ?? 10;
  const remaining = Math.max(0, questionLimit - questionsUsed);

  const [messages, setMessages] = useState<ChatMessageType[]>([
    {
      id: '1',
      sender: 'assistant',
      text: "Hello Team! I'm your AI Knowledge Assistant. Ask me anything about the company documents.",
      timestamp: '09:16 AM',
    },
    {
      id: '2',
      sender: 'user',
      text: 'Which region has the highest revenue?',
      timestamp: '09:16 AM',
    },
    {
      id: '3',
      sender: 'assistant',
      text: 'According to the Annual Report 2024 (Page 117), South India generated the highest revenue contributing 32% of the total revenue.',
      timestamp: '09:16 AM',
    },
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, chatMutation.isPending]);

  const handleSendMessage = async (text: string) => {
    const userMsg: ChatMessageType = {
      id: Date.now().toString(),
      sender: 'user',
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);

    try {
      const response = await chatMutation.mutateAsync(text);

      const assistantMsg: ChatMessageType = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text: response.response,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessageType = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text: err?.response?.data?.detail || 'Error: Question quota limit reached or server unavailable.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    }
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

        <QuestionCounterBadge used={questionsUsed} limit={questionLimit} />
      </div>

      {/* Quota Exhaustion Warning Banner if limit reached */}
      {remaining <= 0 && (
        <div className="p-3 rounded-xl bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 text-red-700 dark:text-red-300 text-xs flex items-center gap-2 shrink-0">
          <AlertCircle className="w-4 h-4 shrink-0 text-red-500" />
          <span>You have exhausted your team question limit. Contact your administrator to increase your quota.</span>
        </div>
      )}

      {/* Chat Messages Log Area */}
      <div className="flex-1 overflow-y-auto pr-2 space-y-2 rounded-xl">
        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}

        {chatMutation.isPending && (
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
          isLoading={chatMutation.isPending}
          disabled={remaining <= 0}
        />
      </div>
    </div>
  );
};
