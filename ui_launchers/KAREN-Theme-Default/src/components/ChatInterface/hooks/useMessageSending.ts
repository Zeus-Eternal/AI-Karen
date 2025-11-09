"use client";

import React, { useMemo } from "react";
import { useChatMessages } from "./useChatMessages";
import type { ChatMessage, ChatSettings } from "../types";
import { canSendMessage } from "../utils/messageUtils";

interface UseMessageSendingOptions {
  messages: ChatMessage[];
  setMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>;
  isTyping: boolean;
  setIsTyping: React.Dispatch<React.SetStateAction<boolean>>;
  settings: ChatSettings;
  sessionId: string | null;
  conversationId: string | null;
  user: any;
  useCopilotKit: boolean;
  enableCodeAssistance: boolean;
  enableContextualHelp: boolean;
  enableDocGeneration: boolean;
  maxMessages?: number;
  onMessageSent?: (message: ChatMessage) => void;
  onMessageReceived?: (message: ChatMessage) => void;
}

export const useMessageSending = (options: UseMessageSendingOptions) => {
  const chatMessages = useChatMessages(
    options.messages,
    options.setMessages,
    options.isTyping,
    options.setIsTyping,
    options.settings,
    options.sessionId,
    options.conversationId,
    options.user,
    options.useCopilotKit,
    options.enableCodeAssistance,
    options.enableContextualHelp,
    options.enableDocGeneration,
    options.maxMessages,
    options.onMessageSent,
    options.onMessageReceived
  );

  const canSend = useMemo(
    () =>
      (content: string) =>
        canSendMessage(
          content,
          options.isTyping,
          chatMessages.messages,
          options.maxMessages
        ),
    [chatMessages.messages, options.isTyping, options.maxMessages]
  );

  return {
    ...chatMessages,
    canSendMessage: canSend,
  };
};
