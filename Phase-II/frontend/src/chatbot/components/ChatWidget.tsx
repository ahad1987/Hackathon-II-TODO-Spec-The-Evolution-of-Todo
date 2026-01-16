/**
 * Chat Widget Component
 * Pure inline-styled modal with guaranteed visibility.
 * No Tailwind CSS - uses only inline styles for consistency.
 */

'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '@/lib/auth-context';
import { useChat } from '../contexts/ChatContext';
import { ChatService } from '../services/chatService';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
}

export function ChatWidget() {
  const { isAuthenticated, user } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const { resetConversation } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest message (must be before early return to follow rules of hooks)
  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen]);

  if (!isAuthenticated || !user) {
    return null;
  }

  const handleClose = () => {
    setIsOpen(false);
  };

  const handleNewChat = () => {
    setMessages([]);
    setConversationId(undefined);
    resetConversation();
  };

  const handleButtonClick = () => {
    setIsOpen(true);
  };

  const handleSend = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessageText = inputValue.trim();
    const userMessage: Message = {
      id: Date.now().toString(),
      text: userMessageText,
      sender: 'user',
    };
    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    console.log('[ChatWidget] Sending message:', userMessageText);

    try {
      // Call backend chat endpoint
      const response = await ChatService.sendMessage(user.id, userMessageText, conversationId);

      // Update conversation ID on first message
      if (!conversationId && response.conversation_id) {
        setConversationId(response.conversation_id);
      }

      // Format and display bot response
      const formattedResponse = ChatService.formatResponse(response);
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: formattedResponse,
        sender: 'bot',
      };
      setMessages((prev) => [...prev, botMessage]);
      console.log('[ChatWidget] Bot response:', formattedResponse);
    } catch (error) {
      console.error('[ChatWidget] Error sending message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 2).toString(),
        text: `Error: ${error instanceof Error ? error.message : 'Failed to send message'}`,
        sender: 'bot',
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      {/* FAB Button - Pure inline styles */}
      <button
        onClick={handleButtonClick}
        style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          width: '60px',
          height: '60px',
          borderRadius: '50%',
          backgroundColor: '#3b82f6',
          border: '2px solid white',
          color: 'white',
          fontSize: '32px',
          cursor: 'pointer',
          zIndex: 9999,
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transition: 'background-color 0.2s ease',
        }}
        onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#2563eb')}
        onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = '#3b82f6')}
        title="Chat with TaskFlow AI"
        aria-label="Open chat widget"
      >
        💬
      </button>

      {/* Modal Overlay */}
      {isOpen && (
        <div
          onClick={handleClose}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            zIndex: 9998,
          }}
          aria-hidden="true"
        />
      )}

      {/* Modal Panel */}
      {isOpen && (
        <div
          style={{
            position: 'fixed',
            bottom: '100px',
            right: '24px',
            width: '400px',
            height: '600px',
            backgroundColor: 'white',
            borderRadius: '8px',
            boxShadow: '0 10px 40px rgba(0, 0, 0, 0.2)',
            zIndex: 9999,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            maxWidth: 'calc(100vw - 48px)',
            fontFamily: 'system-ui, -apple-system, sans-serif',
          }}
        >
          {/* Header */}
          <div
            style={{
              backgroundColor: '#3b82f6',
              color: 'white',
              padding: '16px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              borderBottom: '1px solid #e5e7eb',
              flexShrink: 0,
            }}
          >
            <h3 style={{ margin: 0, fontSize: '14px', fontWeight: '600' }}>TaskFlow AI Assistant</h3>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <button
                onClick={handleNewChat}
                style={{
                  backgroundColor: 'transparent',
                  border: 'none',
                  color: 'white',
                  cursor: 'pointer',
                  padding: '4px 8px',
                  fontSize: '12px',
                  fontWeight: '500',
                  borderRadius: '4px',
                  transition: 'background-color 0.2s ease',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.2)')}
                onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                title="Start new conversation"
              >
                New
              </button>
              <button
                onClick={handleClose}
                style={{
                  backgroundColor: 'transparent',
                  border: 'none',
                  color: 'white',
                  cursor: 'pointer',
                  padding: '4px 8px',
                  fontSize: '16px',
                  borderRadius: '4px',
                  transition: 'background-color 0.2s ease',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.2)')}
                onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                title="Close chat"
              >
                ✕
              </button>
            </div>
          </div>

          {/* Messages Area */}
          <div
            style={{
              flex: 1,
              overflowY: 'auto',
              backgroundColor: '#f8fafc',
              padding: '16px',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
            }}
          >
            {messages.length === 0 ? (
              <div style={{ textAlign: 'center', color: '#94a3b8', marginTop: '40px' }}>
                <p style={{ margin: '0 0 8px 0', fontSize: '14px' }}>Welcome to AI Task Assistant</p>
                <p style={{ margin: 0, fontSize: '12px' }}>Type a message to get started</p>
              </div>
            ) : (
              <>
                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    style={{
                      alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                      backgroundColor: msg.sender === 'user' ? '#3b82f6' : '#e2e8f0',
                      color: msg.sender === 'user' ? 'white' : '#1e293b',
                      padding: '8px 12px',
                      borderRadius: '8px',
                      maxWidth: '75%',
                      wordWrap: 'break-word',
                      fontSize: '13px',
                      lineHeight: '1.4',
                    }}
                  >
                    {msg.text}
                  </div>
                ))}
                {isLoading && (
                  <div
                    style={{
                      alignSelf: 'flex-start',
                      backgroundColor: '#e2e8f0',
                      color: '#1e293b',
                      padding: '8px 12px',
                      borderRadius: '8px',
                      fontSize: '13px',
                      fontStyle: 'italic',
                    }}
                  >
                    Loading...
                  </div>
                )}
                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          {/* Input Area */}
          <div
            style={{
              padding: '12px',
              borderTop: '1px solid #e5e7eb',
              backgroundColor: 'white',
              display: 'flex',
              gap: '8px',
              flexShrink: 0,
            }}
          >
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter' && !isLoading) {
                  handleSend();
                }
              }}
              disabled={isLoading}
              placeholder="Type your message..."
              style={{
                flex: 1,
                padding: '8px 12px',
                border: '1px solid #cbd5e1',
                borderRadius: '6px',
                fontSize: '13px',
                fontFamily: 'inherit',
                outline: 'none',
                transition: 'border-color 0.2s ease',
                opacity: isLoading ? 0.6 : 1,
                cursor: isLoading ? 'not-allowed' : 'text',
              }}
              onFocus={(e) => !isLoading && (e.currentTarget.style.borderColor = '#3b82f6')}
              onBlur={(e) => (e.currentTarget.style.borderColor = '#cbd5e1')}
            />
            <button
              onClick={handleSend}
              disabled={isLoading}
              style={{
                backgroundColor: isLoading ? '#9ca3af' : '#3b82f6',
                color: 'white',
                border: 'none',
                padding: '8px 16px',
                borderRadius: '6px',
                fontSize: '13px',
                fontWeight: '600',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                transition: 'background-color 0.2s ease',
                whiteSpace: 'nowrap',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                opacity: isLoading ? 0.7 : 1,
              }}
              onMouseEnter={(e) => !isLoading && (e.currentTarget.style.backgroundColor = '#2563eb')}
              onMouseLeave={(e) => !isLoading && (e.currentTarget.style.backgroundColor = '#3b82f6')}
              title="Send message"
            >
              {isLoading ? 'Sending...' : 'Send'}
            </button>
          </div>
        </div>
      )}
    </>
  );
}
