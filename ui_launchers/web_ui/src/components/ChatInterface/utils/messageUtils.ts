import { ChatMessage, ChatSettings, ChatContext } from "../types";

export const sanitizeMessageContent = (content: string) =>
  content.replace(/\s+/g, " ").trim();

export const isMessageLimitReached = (
  messages: ChatMessage[],
  maxMessages?: number
) => {
  if (!maxMessages) return false;
  return messages.length >= maxMessages;
};

export const canSendMessage = (
  content: string,
  isTyping: boolean,
  messages: ChatMessage[],
  maxMessages?: number
) => {
  if (!content || !sanitizeMessageContent(content)) {
    return false;
  }
  if (isTyping) {
    return false;
  }
  if (isMessageLimitReached(messages, maxMessages)) {
    return false;
  }
  return true;
};

export const buildChatContext = (
  messages: ChatMessage[],
  settings: ChatSettings,
  selectedText?: string
): ChatContext => {
  const recentMessages = messages.slice(-5);
  const hasCode = recentMessages.some((message) => message.type === "code");

  return {
    selectedText,
    currentFile: undefined,
    language: settings.language,
    recentMessages: recentMessages.map((message) => ({
      role: message.role,
      content: message.content.length > 200
        ? `${message.content.slice(0, 197)}...`
        : message.content,
      timestamp: message.timestamp,
    })),
    codeContext: {
      hasCode,
      language: settings.language,
      errorCount: 0,
    },
    conversationContext: {
      topic: undefined,
      intent: undefined,
      complexity: (hasCode ? "complex" : "medium") as const,
    },
  };
};

export const summarizeMessagesForExport = (messages: ChatMessage[]) =>
  messages.map((message) => ({
    id: message.id,
    role: message.role,
    type: message.type,
    timestamp: message.timestamp,
    preview:
      message.content.length > 120
        ? `${message.content.slice(0, 117)}...`
        : message.content,
  }));

export const getAssistantMessages = (messages: ChatMessage[]) =>
  messages.filter((message) => message.role === "assistant");
