import { getApiClient, hasTaskModifyingToolCalls, dispatchTasksRefreshEvent } from './api';

export interface ChatResponse {
  conversation_id: string;
  response: string;
  tool_calls: string[];
  status: string;
}

export class ChatService {
  static async sendMessage(
    userId: string, // kept for interface compatibility but not used in URL
    message: string,
    conversationId?: string
  ): Promise<ChatResponse> {
    const client = getApiClient();
    // Call /api/v1/chat - user_id is extracted from JWT on backend
    const response = await client.post('/api/v1/chat', {
      conversation_id: conversationId || undefined,
      message,
    });

    // Dispatch refresh event if task was modified
    if (hasTaskModifyingToolCalls(response.data)) {
      dispatchTasksRefreshEvent();
    }

    return response.data;
  }

  static formatResponse(response: ChatResponse): string {
    if (response.status === 'error') {
      return `Error: ${response.response}`;
    }
    return response.response;
  }
}
