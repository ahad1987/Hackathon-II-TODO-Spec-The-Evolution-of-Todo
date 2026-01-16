/**
 * Chat Input Component
 * Provides input field and send button for user messages.
 */

'use client';

import React, { useState, useRef } from 'react';
import { useChat } from '../contexts/ChatContext';

export function ChatInput() {
  const { sendMessage, isLoading } = useChat();
  const [input, setInput] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  /**
   * Handle form submission.
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!input.trim() || isLoading) return;

    const message = input.trim();
    setInput('');

    await sendMessage(message);

    // Refocus input after send
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };

  /**
   * Handle Enter key to submit.
   */
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey && !isLoading) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="border-t border-slate-200 bg-white p-3 sm:p-4"
    >
      <div className="flex gap-2">
        <input
          ref={inputRef}
          type="text"
          placeholder="Ask to add, list, or complete tasks..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          maxLength={200}
          className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none disabled:bg-slate-100"
          aria-label="Chat message input"
        />
        <button
          type="submit"
          disabled={!input.trim() || isLoading}
          className="rounded-lg bg-blue-500 px-4 py-2 text-sm font-medium text-white hover:bg-blue-600 disabled:bg-slate-300"
          aria-label="Send message"
        >
          {isLoading ? (
            <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-blue-500" />
          ) : (
            'Send'
          )}
        </button>
      </div>
    </form>
  );
}
