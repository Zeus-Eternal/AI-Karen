"use client";

import React from "react";
import { DegradedModeBanner } from "@/components/ui/degraded-mode-banner";
import ProfileSelector from "@/components/chat/ProfileSelector";
import { ChatMessages } from "./ChatMessages";
import { ChatInput } from "./ChatInput";
import CopilotArtifacts from "./CopilotArtifacts";
import type { ChatMessage, ChatSettings, ChatContext, CopilotArtifact, CopilotAction } from "../types";

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
  artifacts: CopilotArtifact[];
  copilotActions?: CopilotAction[];
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
  artifacts,
  copilotActions,
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
      <div className="px-4 pt-4">
        <DegradedModeBanner onRetry={() => window.location.reload()} />
      </div>

      <div className="px-4 pt-2">
        <ProfileSelector />
      </div>

      {artifacts.length > 0 && (
        <div className="px-4 pt-2">
          <CopilotArtifacts
            artifacts={artifacts}
            onApprove={onArtifactApprove}
            onReject={onArtifactReject}
            onApply={onArtifactApply}
          />
        </div>
      )}

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
        artifacts={artifacts}
      />

      <ChatInput
        inputValue={inputValue}
        placeholder={placeholder}
        isTyping={isTyping}
        isRecording={isRecording}
        enableVoiceInput={enableVoiceInput}
        enableFileUpload={enableFileUpload}
        chatContext={chatContext}
        copilotActions={copilotActions}
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
