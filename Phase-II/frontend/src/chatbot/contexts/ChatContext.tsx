/**
 * Chat Context for managing conversation state.
 * Provides message history, conversation ID, and send message functionality.
 */

'use client';

import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  ReactNode,
} from 'react';
import { ChatService, ChatMessage, ChatResponse } from '../services/chatService';
import { useAuth } from '@/lib/auth-context';

export interface ChatContextType {
  conversationId: string | null;
  messages: ChatMessage[];
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
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Send a message to the chat endpoint.
   */
  const sendMessage = useCallback(
    async (content: string) => {
      // Validate prerequisites
      if (!user?.id) {
        setError('Not authenticated');
        return;
      }

      if (!content.trim()) {
        setError('Message cannot be empty');
        return;
      }

      setError(null);
      setIsLoading(true);

      try {
        // Add user message to history
        const userMessage: ChatMessage = {
          role: 'user',
          content: content.trim(),
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, userMessage]);

        // Send to backend
        const response: ChatResponse = await ChatService.sendMessage(
          user.id,
          content,
          conversationId || undefined
        );

        // Update conversation ID if new
        if (!conversationId) {
          setConversationId(response.conversation_id);
        }

        // Add assistant message to history
        const assistantMessage: ChatMessage = {
          role: 'assistant',
          content: ChatService.formatResponse(response),
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error';
        setError(errorMessage);
        // Remove the user message on error
        setMessages((prev) => prev.slice(0, -1));
      } finally {
        setIsLoading(false);
      }
    },
    [user?.id, conversationId]
  );

  /**
   * Clear error message.
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  /**
   * Reset conversation (start new chat).
   */
  const resetConversation = useCallback(() => {
    setConversationId(null);
    setMessages([]);
    setError(null);
  }, []);

  const value: ChatContextType = {
    conversationId,
    messages,
    isLoading,
    error,
    sendMessage,
    clearError,
    resetConversation,
  };

  return (
    <ChatContext.Provider value={value}>{children}</ChatContext.Provider>
  );
}

/**
 * Hook to use chat context.
 * Must be used within ChatProvider.
 */
export function useChat(): ChatContextType {
  const context = useContext(ChatContext);

  if (context === undefined) {
    throw new Error('useChat must be used within a ChatProvider');
  }

  return context;
}
