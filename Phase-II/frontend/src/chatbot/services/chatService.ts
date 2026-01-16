/**
 * Chat Service for communicating with the backend chat endpoint.
 * Handles message sending and conversation management.
 */

import { getApiClient, ApiError } from '@/lib/api-client';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  id?: string;
  timestamp?: string;
}

export interface ChatResponse {
  conversation_id: string;
  response: string;
  tool_calls: string[];
  status: 'success' | 'error';
}

export class ChatService {
  /**
   * Send a message to the chat endpoint.
   * Creates a new conversation if conversation_id is not provided.
   */
  static async sendMessage(
    userId: string,
    message: string,
    conversationId?: string
  ): Promise<ChatResponse> {
    try {
      const client = getApiClient();
      const response = await client.post(`/api/${userId}/chat`, {
        conversation_id: conversationId || undefined,
        message,
      });
      return response.data;
    } catch (error) {
      if (error instanceof ApiError) {
        throw new Error(
          `Chat error (${error.statusCode}): ${error.message}`
        );
      }
      throw error;
    }
  }

  /**
   * Format a chat response for display.
   * Extracts friendly message from agent response.
   */
  static formatResponse(response: ChatResponse): string {
    if (response.status === 'error') {
      return `Error: ${response.response}`;
    }

    // Agent responds with natural language confirmation
    // e.g., "✓ Added task: 'buy milk'"
    return response.response;
  }

  /**
   * Check if a response indicates a successful task creation.
   */
  static isTaskCreationSuccess(response: ChatResponse): boolean {
    return (
      response.status === 'success' &&
      response.tool_calls.includes('add_task')
    );
  }
}
