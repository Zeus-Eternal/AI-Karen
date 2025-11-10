"use client";

import { safeError } from '@/lib/safe-console';
import type {
  ChatMessage,
  HandleUserMessageResult,
  KarenSettings,
} from '@/lib/types';
import type {
  ChatRuntimeClient,
  ConversationSummaryRow,
  ProcessMessageOptions,
} from '@/types/chat-ui';

interface HttpError extends Error {
  status: number;
}

const JSON_HEADERS: HeadersInit = {
  'Content-Type': 'application/json',
};

function toIsoString(date: Date): string {
  return date instanceof Date ? date.toISOString() : new Date(date).toISOString();
}

function serializeMessage(message: ChatMessage) {
  return {
    ...message,
    timestamp: toIsoString(message.timestamp),
  };
}

async function parseResponse<T>(response: Response): Promise<T> {
  const text = await response.text();
  const data = text ? (JSON.parse(text) as T) : ({} as T);
  if (!response.ok) {
    const error = new Error(
      data && typeof data === 'object' && 'message' in (data as any)
        ? ((data as any).message as string)
        : response.statusText
    ) as HttpError;
    error.status = response.status;
    throw error;
  }
  return data;
}

class ChatUiService implements ChatRuntimeClient {
  async createConversationSession(userId: string): Promise<{ conversationId: string; sessionId: string }> {
    const payload = {
      session_id: crypto.randomUUID(),
      ui_source: 'web',
      title: 'New Conversation',
      user_settings: {},
      ui_context: {
        user_id: userId,
        created_from: 'web_ui',
        user_agent: typeof navigator !== 'undefined' ? navigator.userAgent : 'server',
      },
      tags: [] as string[],
      priority: 'normal',
    };

    const response = await fetch('/api/conversations/create', {
      method: 'POST',
      headers: JSON_HEADERS,
      credentials: 'include',
      body: JSON.stringify(payload),
    });

    const data = await parseResponse<{ conversation: { id: string; session_id?: string } }>(response);

    return {
      conversationId: data.conversation.id,
      sessionId: data.conversation.session_id ?? payload.session_id,
    };
  }

  async addMessageToConversation(conversationId: string, message: ChatMessage): Promise<void> {
    try {
      await fetch(`/api/conversations/${conversationId}/messages`, {
        method: 'POST',
        headers: JSON_HEADERS,
        credentials: 'include',
        body: JSON.stringify({
          role: message.role,
          content: message.content,
          ui_source: 'web',
          metadata: {
            ai_data: message.aiData,
            timestamp: toIsoString(message.timestamp),
          },
        }),
      });
    } catch (error) {
      safeError('Failed to add message to conversation', error);
    }
  }

  async processUserMessage(
    message: string,
    history: ChatMessage[],
    settings: Partial<KarenSettings>,
    options: ProcessMessageOptions = {}
  ): Promise<HandleUserMessageResult> {
    const response = await fetch('/api/chat/process', {
      method: 'POST',
      headers: JSON_HEADERS,
      credentials: 'include',
      body: JSON.stringify({
        message,
        conversation_history: history.map(serializeMessage),
        settings,
        user_id: options.userId,
        session_id: options.sessionId,
        preferences: {
          preferredLLMProvider: options.preferredLLMProvider,
          preferredModel: options.preferredModel,
        },
        tools: options.tools,
      }),
    });

    return parseResponse<HandleUserMessageResult>(response);
  }

  async getUserConversations(userId: string): Promise<ConversationSummaryRow[]> {
    const response = await fetch(`/api/conversations?user_id=${encodeURIComponent(userId)}`, {
      method: 'GET',
      headers: JSON_HEADERS,
      credentials: 'include',
    });

    const data = await parseResponse<{
      conversations: Array<{
        id: string;
        session_id: string;
        updated_at: string;
        messages: Array<{ id: string }>;
        metadata?: { title?: string; sentiment?: string; status?: string };
      }>;
    }>(response);

    return data.conversations.map((conversation) => ({
      id: conversation.id,
      sessionId: conversation.session_id,
      title:
        conversation.metadata?.title ?? `Conversation ${conversation.session_id.slice(0, 8)}`,
      lastActivity: new Date(conversation.updated_at),
      messageCount: conversation.messages.length,
      status: (conversation.metadata?.status as ConversationSummaryRow['status']) ?? 'active',
      sentiment: (conversation.metadata?.sentiment as ConversationSummaryRow['sentiment']) ?? 'neutral',
      lastMessage: conversation.messages.length ? 'View details in conversation' : undefined,
      participants: [],
      tags: [],
    }));
  }
}

const chatUiService = new ChatUiService();

export { chatUiService };
export type { ChatUiService };

