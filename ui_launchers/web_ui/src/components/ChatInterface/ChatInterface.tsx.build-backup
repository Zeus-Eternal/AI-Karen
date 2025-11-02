"use client";

import React, { useCallback, useEffect, useMemo } from "react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { useAuth } from "@/contexts/AuthContext";

// Hooks
import { useChatState } from "./hooks/useChatState";
import { useChatSettings } from "./hooks/useChatSettings";
import { useChatAnalytics } from "./hooks/useChatAnalytics";
import { useMessageSending } from "./hooks/useMessageSending";
import { useCopilotIntegration } from "./hooks/useCopilotIntegration";
import { useVoiceInput } from "./hooks/useVoiceInput";
import { useArtifactManagement } from "./hooks/useArtifactManagement";

// Components
import { ChatHeader } from "./components/ChatHeader";
import { ChatMainContent } from "./components/ChatMainContent";
import { ChatTabs } from "./components/ChatTabs";
import { DEFAULT_COPILOT_ACTIONS } from "./components/CopilotActions";

// Utils & constants
import {
  DEFAULT_CHAT_HEIGHT,
  DEFAULT_PLACEHOLDER,
  MAX_DEFAULT_MESSAGES,
} from "./constants";
import { buildChatContext } from "./utils/messageUtils";

// Types
import { ChatInterfaceProps, CopilotAction } from "./types";

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  // Core Props
  initialMessages = [],
  onMessageSent,
  onMessageReceived,

  // CopilotKit Integration
  useCopilotKit = true,
  enableCodeAssistance = true,
  enableContextualHelp = true,
  enableDocGeneration = true,

  // UI Configuration
  className = "",
  height = DEFAULT_CHAT_HEIGHT,
  showHeader = true,
  showTabs = true,
  showSettings = true,
  enableVoiceInput = false,
  enableFileUpload = true,

  // Advanced Features
  enableAnalytics = true,
  enableExport = true,
  enableSharing = true,
  enableCollaboration = false,
  maxMessages = MAX_DEFAULT_MESSAGES,

  // Customization
  placeholder = DEFAULT_PLACEHOLDER,
  welcomeMessage,
  theme = "auto",

  // Callbacks
  onSettingsChange,
  onExport,
  onShare,
  onAnalyticsUpdate,
}) => {
  const { user } = useAuth();

  const chatState = useChatState(initialMessages, welcomeMessage);
  const chatSettings = useChatSettings({ theme }, onSettingsChange);
  const chatAnalytics = useChatAnalytics(
    chatState.messages,
    chatState.sessionStartTime,
    onAnalyticsUpdate
  );

  const messageSending = useMessageSending({
    messages: chatState.messages,
    setMessages: chatState.setMessages,
    isTyping: chatState.isTyping,
    setIsTyping: chatState.setIsTyping,
    settings: chatSettings.settings,
    sessionId: chatState.sessionId,
    conversationId: chatState.conversationId,
    user,
    useCopilotKit,
    enableCodeAssistance,
    enableContextualHelp,
    enableDocGeneration,
    maxMessages: maxMessages,
    onMessageSent,
    onMessageReceived,
  });

  const artifactManagement = useArtifactManagement({
    artifacts: chatState.copilotArtifacts,
    updateArtifact: chatState.updateCopilotArtifact,
    removeArtifact: chatState.removeCopilotArtifact,
  });

  const chatContext = useMemo(
    () => buildChatContext(chatState.messages, chatSettings.settings, chatState.selectedText),
    [chatState.messages, chatSettings.settings, chatState.selectedText]
  );

  const copilotIntegration = useCopilotIntegration({
    enabled: useCopilotKit,
    actions: DEFAULT_COPILOT_ACTIONS,
    messages: chatState.messages,
    settings: chatSettings.settings,
    context: chatContext,
  });

  const voiceInput = useVoiceInput({
    enabled: enableVoiceInput,
    isRecording: chatState.isRecording,
    startRecording: chatState.startRecording,
    stopRecording: chatState.stopRecording,
  });

  useEffect(() => {
    if (!enableAnalytics && chatState.activeTab === "analytics") {
      chatState.setActiveTab("chat");
    }
  }, [enableAnalytics, chatState.activeTab, chatState.setActiveTab]);

  const handleMessageSubmit = useCallback(
    (event: React.FormEvent) => {
      event.preventDefault();
      if (!messageSending.canSendMessage(chatState.inputValue)) {
        return;
      }
      messageSending.sendMessage(chatState.inputValue, "text");
      chatState.clearInput();
    },
    [chatState, messageSending]
  );

  const handleCopilotAction = useCallback(
    (action: CopilotAction) => {
      const prompt = action.prompt;
      messageSending.sendMessage(prompt, "text", { context: chatContext });
    },
    [chatContext, messageSending]
  );

  const handleQuickAction = useCallback(
    (action: string, prompt: string, type?: string) => {
      if (!prompt || !messageSending.canSendMessage(prompt)) {
        return;
      }
      messageSending.sendMessage(prompt, type as any, { context: chatContext });
    },
    [chatContext, messageSending]
  );

  const renderChatTab = useCallback(
    () => (
      <ChatMainContent
        messages={chatState.messages}
        inputValue={chatState.inputValue}
        placeholder={placeholder}
        isTyping={chatState.isTyping}
        isRecording={chatState.isRecording}
        useCopilotKit={useCopilotKit}
        enableCodeAssistance={enableCodeAssistance}
        enableVoiceInput={enableVoiceInput}
        enableFileUpload={enableFileUpload}
        settings={chatSettings.settings}
        chatContext={chatContext}
        artifacts={artifactManagement.artifacts}
        copilotActions={copilotIntegration.availableActions}
        onInputChange={chatState.setInputValue}
        onCopilotAction={handleCopilotAction}
        onVoiceStart={voiceInput.handleVoiceStart}
        onVoiceStop={voiceInput.handleVoiceStop}
        onSubmit={handleMessageSubmit}
        onQuickAction={handleQuickAction}
        onMessageAction={messageSending.handleMessageAction}
        onArtifactApprove={artifactManagement.approveArtifact}
        onArtifactReject={artifactManagement.rejectArtifact}
        onArtifactApply={artifactManagement.applyArtifact}
      />
    ),
    [
      artifactManagement.artifacts,
      artifactManagement.approveArtifact,
      artifactManagement.rejectArtifact,
      artifactManagement.applyArtifact,
      chatContext,
      chatSettings.settings,
      chatState.inputValue,
      chatState.isRecording,
      chatState.isTyping,
      chatState.messages,
      enableCodeAssistance,
      enableFileUpload,
      enableVoiceInput,
      copilotIntegration.availableActions,
      handleCopilotAction,
      handleMessageSubmit,
      handleQuickAction,
      messageSending.handleMessageAction,
      placeholder,
      useCopilotKit,
      voiceInput.handleVoiceStart,
      voiceInput.handleVoiceStop,
    ]
  );

  return (
    <React.Fragment>
      <Card
        className={`flex flex-col ${className} ${
          chatState.isFullscreen ? "fixed inset-0 z-50" : ""
        }`}
        style={chatState.isFullscreen ? { height: "100vh" } : { height }}
        role="main"
        aria-label="Chat conversation interface"
        variant="glass"
      >
        {/* Header */}
        {showHeader && (
          <CardHeader className="pb-2">
            <ChatHeader
              showHeader={showHeader}
              useCopilotKit={useCopilotKit}
              selectedMessages={chatState.selectedMessages}
              enableExport={enableExport}
              enableSharing={enableSharing}
              showSettings={showSettings}
              settings={chatSettings.settings}
              isFullscreen={chatState.isFullscreen}
              messages={chatState.messages}
              onSettingsChange={chatSettings.updateSettings}
              onExport={() => onExport?.(chatState.messages)}
              onShare={onShare}
              onToggleFullscreen={() => chatState.setIsFullscreen(!chatState.isFullscreen)}
              onShowRoutingHistory={() => chatState.setShowRoutingHistory(true)}
            />
          </CardHeader>
        )}

        <CardContent className="flex-1 flex flex-col p-0 sm:p-4 md:p-6">
          {showTabs ? (
            <ChatTabs
              activeTab={chatState.activeTab}
              showTabs={showTabs}
              messages={chatState.messages}
              settings={chatSettings.settings}
              analytics={chatAnalytics.analytics}
              codeValue={chatState.codeValue}
              showCodePreview={chatState.showCodePreview}
              isTyping={chatState.isTyping}
              useCopilotKit={useCopilotKit}
              enableDocGeneration={enableDocGeneration}
              enableAnalytics={enableAnalytics}
              onTabChange={(tab) => chatState.setActiveTab(tab)}
              onSettingsChange={chatSettings.updateSettings}
              onCodeChange={chatState.setCodeValue}
              onPreviewToggle={() => chatState.setShowCodePreview(!chatState.showCodePreview)}
              onCodeSubmit={() => {
                if (!chatState.codeValue.trim()) return;
                messageSending.sendMessage(chatState.codeValue, "code");
              }}
              renderChatTab={renderChatTab}
            />
          ) : (
            renderChatTab()
          )}
        </CardContent>
      </Card>
    </React.Fragment>
  );
};
