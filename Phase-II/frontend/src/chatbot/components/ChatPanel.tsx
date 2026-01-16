/**
 * Chat Panel Component
 * Displays message history with scroll and friendly formatting.
 */

'use client';

import React, { useEffect, useRef } from 'react';
import { useChat } from '../contexts/ChatContext';

export function ChatPanel() {
  const { messages, error } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  /**
   * Auto-scroll to bottom when new messages arrive.
   */
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto bg-slate-50 p-3 sm:p-4">
      {messages.length === 0 && !error && (
        <div className="flex h-full items-center justify-center">
          <p className="text-center text-sm text-slate-500">
            Say something like:<br />
            "Add a task to buy milk"<br />
            "Show my tasks"
          </p>
        </div>
      )}

      {error && (
        <div className="mb-3 rounded-lg border border-red-200 bg-red-50 p-3">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      <div className="space-y-3">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${
              msg.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`max-w-xs rounded-lg px-3 py-2 text-sm ${
                msg.role === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-white text-slate-800 border border-slate-200'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
      </div>

      <div ref={messagesEndRef} />
    </div>
  );
}
