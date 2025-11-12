"use client";

import React from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Bot, Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import EnhancedMessageBubble from "@/components/chat/EnhancedMessageBubble";
import MessageActions from "./MessageActions";
import type { ChatMessage, ChatSettings } from "../types";

interface ChatMessagesProps {
  messages: ChatMessage[];
  isTyping: boolean;
  useCopilotKit: boolean;
  enableCodeAssistance: boolean;
  settings: ChatSettings;
  onMessageAction: (messageId: string, action: string) => void;
  messagesEndRef?: React.RefObject<HTMLDivElement>;
}

export const ChatMessages: React.FC<ChatMessagesProps> = ({
  messages,
  isTyping,
  useCopilotKit,
  enableCodeAssistance,
  settings,
  onMessageAction,
  messagesEndRef,
}: ChatMessagesProps) => {
  return (
    <ScrollArea className="flex-1 px-4">
      <div
        className="space-y-4 pb-4"
        role="log"
        aria-live="polite"
        aria-relevant="additions text"
        aria-label="Chat messages"
      >
        {messages.length === 0 ? (
          <div
            className="text-center py-8 text-muted-foreground"
            role="status"
            aria-label="Welcome message"
          >
            <Bot
              className="h-12 w-12 mx-auto mb-4 opacity-50 "
              aria-hidden="true"
            />
            <div className="text-lg font-medium mb-2">
              {useCopilotKit && (
                <Badge
                  variant="secondary"
                  className="ml-2 text-xs sm:text-sm md:text-base"
                >
                  CopilotKit
                </Badge>
              )}
            </div>
            <div className="text-sm md:text-base lg:text-lg">
              suggestions.
              {enableCodeAssistance &&
                " Try asking me about code or programming concepts!"}
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className="group relative"
              role="article"
              aria-label={`Message from ${message.role}`}
            >
              <MessageActions
                messageId={message.id}
                onAction={onMessageAction}
                className="absolute top-2 right-2"
              />
              <EnhancedMessageBubble
                message={{
                  ...message,
                  type:
                    message.type === "analysis" ||
                    message.type === "documentation" ||
                    message.type === "suggestion"
                      ? "text"
                      : message.type,
                  status:
                    message.status === "generating" || message.status === "completed"
                      ? "sent"
                      : message.status,
                  metadata: message.metadata
                    ? {
                        confidence: message.metadata.confidence,
                        model: message.metadata.model,
                        latency: message.metadata.latencyMs,
                        tokens:
                          typeof message.metadata.tokens === "number"
                            ? { total: message.metadata.tokens }
                            : undefined,
                      }
                    : undefined,
                }}
                onCopy={() => {
                  onMessageAction(message.id, "copy");
                }}
                onRegenerate={() => {
                  onMessageAction(message.id, "regenerate");
                }}
                showMetadata={true}
                isDarkMode={settings.theme === "dark"}
              />
            </div>
          ))
        )}

        {isTyping && (
          <div
            className="flex gap-3 mb-4"
            role="status"
            aria-live="polite"
            id="typing-indicator"
          >
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-muted flex items-center justify-center ">
              <Bot className="h-4 w-4 " aria-hidden="true" />
            </div>
            <div className="flex-1">
              <div className="inline-block p-3 rounded-lg bg-muted border sm:p-4 md:p-6">
                <div className="flex items-center gap-2">
                  <Loader2
                    className="h-4 w-4 animate-spin "
                    aria-hidden="true"
                  />
                  <span className="text-sm text-muted-foreground md:text-base lg:text-lg">
                    AI is thinking...
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} aria-hidden="true" />
      </div>
    </ScrollArea>
  );
};
