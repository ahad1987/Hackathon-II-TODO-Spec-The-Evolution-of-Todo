'use client';

import { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { ChatService as ChatServiceClass } from '@/services/api';
import { useAuth } from '@/lib/auth-context';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

interface ChatContextType {
  conversationId: string | null;
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  sendMessage: (message: string) => Promise<void>;
  clearError: () => void;
  resetConversation: () => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(
    async (message: string) => {
      if (!user?.id) {
        setError('Not authenticated');
        return;
      }

      if (!message.trim()) {
        setError('Message cannot be empty');
        return;
      }

      setError(null);
      setIsLoading(true);

      try {
        const userMessage: Message = {
          role: 'user',
          content: message.trim(),
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, userMessage]);

        const response = await ChatServiceClass.sendMessage(user.id, message, conversationId || undefined);

        if (!conversationId) {
          setConversationId(response.conversation_id);
        }

        const assistantMessage: Message = {
          role: 'assistant',
          content: ChatServiceClass.formatResponse(response),
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
        setMessages((prev) => prev.slice(0, -1));
      } finally {
        setIsLoading(false);
      }
    },
    [user?.id, conversationId]
  );

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const resetConversation = useCallback(() => {
    setConversationId(null);
    setMessages([]);
    setError(null);
  }, []);

  return (
    <ChatContext.Provider
      value={{
        conversationId,
        messages,
        isLoading,
        error,
        sendMessage,
        clearError,
        resetConversation,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
}
