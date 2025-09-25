"use client";

import React from "react";
import { DegradedModeBanner } from "@/components/ui/degraded-mode-banner";
import ProfileSelector from "@/components/chat/ProfileSelector";
import { ChatMessages } from "@/components/chat/ChatMessages";
import { ChatInput } from "@/components/chat/ChatInput";
import type { ChatMessage, ChatSettings } from "./types";
import type { ChatContext, CopilotAction } from "./CopilotActions";

interface ChatMainContentProps {
  messages: ChatMessage[];
  inputValue: string;
  placeholder: string;
  isTyping: boolean;
  isRecording: boolean;
  useCopilotKit: boolean;
  enableCodeAssistance: boolean;
  enableVoiceInput: boolean;
  enableFileUpload: boolean;
  settings: ChatSettings;
  chatContext: ChatContext;
  onInputChange: (value: string) => void;
  onCopilotAction: (action: CopilotAction) => void;
  onVoiceStart: () => void;
  onVoiceStop: () => void;
  onSubmit: (e: React.FormEvent) => void;
  onQuickAction: (action: string, prompt: string, type?: string) => void;
  onMessageAction: (messageId: string, action: string) => void;
  onArtifactApprove: (artifactId: string) => void;
  onArtifactReject: (artifactId: string) => void;
  onArtifactApply: (artifactId: string) => void;
}

export const ChatMainContent: React.FC<ChatMainContentProps> = ({
  messages,
  inputValue,
  placeholder,
  isTyping,
  isRecording,
  useCopilotKit,
  enableCodeAssistance,
  enableVoiceInput,
  enableFileUpload,
  settings,
  chatContext,
  onInputChange,
  onCopilotAction,
  onVoiceStart,
  onVoiceStop,
  onSubmit,
  onQuickAction,
  onMessageAction,
  onArtifactApprove,
  onArtifactReject,
  onArtifactApply,
}) => {
  return (
    <div className="flex-1 flex flex-col">
      {/* Degraded Mode Banner */}
      <div className="px-4 pt-4">
        <DegradedModeBanner
          onRetry={() => {
            window.location.reload();
          }}
          onDismiss={() => {
            // Banner will handle its own dismissal
          }}
        />
      </div>

      {/* Profile Selector */}
      <div className="px-4 pt-2">
        <ProfileSelector />
      </div>

      {/* Messages Area - Using modular component */}
      <ChatMessages
        messages={messages}
        isTyping={isTyping}
        useCopilotKit={useCopilotKit}
        enableCodeAssistance={enableCodeAssistance}
        settings={settings}
        onMessageAction={onMessageAction}
        onArtifactApprove={onArtifactApprove}
        onArtifactReject={onArtifactReject}
        onArtifactApply={onArtifactApply}
      />

      {/* Input Area - Using modular component */}
      <ChatInput
        inputValue={inputValue}
        placeholder={placeholder}
        isTyping={isTyping}
        isRecording={isRecording}
        enableVoiceInput={enableVoiceInput}
        enableFileUpload={enableFileUpload}
        chatContext={chatContext}
        onInputChange={onInputChange}
        onCopilotAction={onCopilotAction}
        onVoiceStart={onVoiceStart}
        onVoiceStop={onVoiceStop}
        onSubmit={onSubmit}
        onQuickAction={onQuickAction}
      />
    </div>
  );
};
