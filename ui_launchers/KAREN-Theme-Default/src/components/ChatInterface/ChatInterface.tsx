"use client";

import React, { useCallback } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card } from "@/components/ui/card";
import { ChatHeader } from "./components/ChatHeader";
import { ChatMainContent } from "./components/ChatMainContent";
import { ChatCodeTab } from "./components/ChatCodeTab";
import AnalyticsTab from "./components/AnalyticsTab";
import { useChatState } from "./hooks/useChatState";
import { useChatMessages } from "./hooks/useChatMessages";
import { useChatSettings } from "./hooks/useChatSettings";
import { useChatAnalytics } from "./hooks/useChatAnalytics";
import { useCopilotIntegration } from "./hooks/useCopilotIntegration";
import { useVoiceInput } from "./hooks/useVoiceInput";
import { useArtifactManagement } from "./hooks/useArtifactManagement";
import { ErrorBoundary } from "@/components/error-handling/ErrorBoundary";
import { useAuth } from "@/contexts/AuthContext";
import type { ChatInterfaceProps, CopilotAction } from "./types";
import { DEFAULT_CHAT_HEIGHT, DEFAULT_PLACEHOLDER } from "./constants";
import { safeDebug } from "@/lib/safe-console";

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  initialMessages = [],
  onMessageSent,
  onMessageReceived,
  useCopilotKit = false,
  enableCodeAssistance = false,
  enableContextualHelp = false,
  enableDocGeneration = false,
  className = "",
  height = DEFAULT_CHAT_HEIGHT,
  showHeader = true,
  showTabs = true,
  showSettings = true,
  enableVoiceInput = false,
  enableFileUpload = false,
  enableAnalytics = false,
  enableExport = false,
  enableSharing = false,
  enableCollaboration = false,
  maxMessages = 1000,
  placeholder = DEFAULT_PLACEHOLDER,
  welcomeMessage,
  theme = "auto",
  onSettingsChange,
  onExport,
  onShare,
  onAnalyticsUpdate,
}) => {
  const { user } = useAuth();

  // Core state management
  const {
    messages,
    setMessages,
    inputValue,
    setInputValue,
    codeValue,
    setCodeValue,
    isTyping,
    setIsTyping,
    isRecording,
    setIsRecording,
    isAnalyzing,
    activeTab,
    setActiveTab,
    isFullscreen,
    setIsFullscreen,
    showRoutingHistory,
    setShowRoutingHistory,
    showCodePreview,
    setShowCodePreview,
    sessionId,
    conversationId,
    messagesEndRef,
    selectedText,
    setSelectedText,
    sessionStartTime,
    copilotArtifacts,
    setCopilotArtifacts,
  } = useChatState(initialMessages, welcomeMessage);

  // Settings management
  const { settings, updateSettings, resetSettings } = useChatSettings(onSettingsChange);

  // Analytics management
  const { analytics, updateAnalytics, resetAnalytics } = useChatAnalytics(
    messages,
    sessionStartTime,
    onAnalyticsUpdate
  );

  // Message handling
  const {
    sendMessage,
    regenerateMessage,
    handleVoiceTranscript,
    handleCodeSubmit,
    handleMessageAction,
  } = useChatMessages(
    messages,
    setMessages,
    isTyping,
    setIsTyping,
    settings,
    sessionId,
    conversationId,
    user,
    useCopilotKit,
    enableCodeAssistance,
    enableContextualHelp,
    enableDocGeneration,
    maxMessages,
    onMessageSent,
    onMessageReceived
  );

  // CopilotKit integration
  const { copilotActions, handleCopilotAction } = useCopilotIntegration(
    useCopilotKit,
    enableCodeAssistance,
    enableContextualHelp,
    enableDocGeneration
  );

  // Voice input handling
  const { startRecording, stopRecording } = useVoiceInput(
    enableVoiceInput,
    setIsRecording,
    handleVoiceTranscript
  );

  // Artifact management
  const { handleArtifactApprove, handleArtifactReject, handleArtifactApply } =
    useArtifactManagement(copilotArtifacts, setCopilotArtifacts);

  // Chat context for CopilotActions
  const chatContext = {
    selectedText,
    currentFile: undefined,
    language: settings.language,
    recentMessages: messages.slice(-5).map((m) => ({
      role: m.role,
      content: m.content,
      timestamp: m.timestamp,
    })),
    codeContext: {
      hasCode: messages.some((m) => m.type === "code"),
      language: messages.find((m) => m.language)?.language,
      errorCount: messages.filter((m) => m.status === "error").length,
    },
    conversationContext: {
      topic: messages.length > 0 ? "ongoing" : undefined,
      intent: "chat",
      complexity: messages.length > 10 ? "complex" : messages.length > 3 ? "medium" : "simple",
    },
  };

  // Form submission handler
  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      if (inputValue.trim() && !isTyping) {
        sendMessage(inputValue.trim());
        setInputValue("");
      }
    },
    [inputValue, isTyping, sendMessage, setInputValue]
  );

  // Quick action handler
  const handleQuickAction = useCallback(
    (action: string, prompt: string, type?: string) => {
      safeDebug("Quick action triggered:", { action, prompt, type });
      setInputValue(prompt);
      sendMessage(prompt);
    },
    [sendMessage, setInputValue]
  );

  // Handle copilot action
  const onCopilotAction = useCallback(
    (action: CopilotAction) => {
      handleCopilotAction(action, chatContext);
    },
    [handleCopilotAction, chatContext]
  );

  // Export handler
  const handleExport = useCallback(() => {
    if (onExport) {
      onExport(messages);
    } else {
      const exportData = JSON.stringify(messages, null, 2);
      const blob = new Blob([exportData], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `chat-export-${Date.now()}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  }, [messages, onExport]);

  // Share handler
  const handleShare = useCallback(() => {
    if (onShare) {
      onShare(messages);
    } else {
      safeDebug("Share not implemented - onShare callback not provided");
    }
  }, [messages, onShare]);

  return (
    <ErrorBoundary
      fallback={
        <div className="p-4 text-center">
          <p className="text-destructive">An error occurred in the chat interface.</p>
          <p className="text-sm text-muted-foreground mt-2">Please refresh the page to try again.</p>
        </div>
      }
    >
      <Card
        className={`flex flex-col overflow-hidden ${className}`}
        style={{ height }}
        data-theme={theme}
      >
        {showHeader && (
          <ChatHeader
            activeTab={activeTab}
            isFullscreen={isFullscreen}
            showRoutingHistory={showRoutingHistory}
            showCodePreview={showCodePreview}
            showSettings={showSettings}
            enableExport={enableExport}
            enableSharing={enableSharing}
            settings={settings}
            analytics={analytics}
            onToggleFullscreen={() => setIsFullscreen(!isFullscreen)}
            onToggleRoutingHistory={() => setShowRoutingHistory(!showRoutingHistory)}
            onToggleCodePreview={() => setShowCodePreview(!showCodePreview)}
            onSettingsChange={updateSettings}
            onResetSettings={resetSettings}
            onExport={handleExport}
            onShare={handleShare}
          />
        )}

        {showTabs ? (
          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as any)} className="flex-1 flex flex-col">
            <TabsList className="w-full justify-start border-b rounded-none">
              <TabsTrigger value="chat">Chat</TabsTrigger>
              {enableCodeAssistance && <TabsTrigger value="code">Code</TabsTrigger>}
              {enableAnalytics && <TabsTrigger value="analytics">Analytics</TabsTrigger>}
            </TabsList>

            <TabsContent value="chat" className="flex-1 flex flex-col mt-0">
              <ChatMainContent
                messages={messages}
                inputValue={inputValue}
                placeholder={placeholder}
                isTyping={isTyping}
                isRecording={isRecording}
                useCopilotKit={useCopilotKit}
                enableCodeAssistance={enableCodeAssistance}
                enableVoiceInput={enableVoiceInput}
                enableFileUpload={enableFileUpload}
                settings={settings}
                chatContext={chatContext}
                artifacts={copilotArtifacts}
                copilotActions={copilotActions}
                onInputChange={setInputValue}
                onCopilotAction={onCopilotAction}
                onVoiceStart={startRecording}
                onVoiceStop={stopRecording}
                onSubmit={handleSubmit}
                onQuickAction={handleQuickAction}
                onMessageAction={handleMessageAction}
                onArtifactApprove={handleArtifactApprove}
                onArtifactReject={handleArtifactReject}
                onArtifactApply={handleArtifactApply}
              />
            </TabsContent>

            {enableCodeAssistance && (
              <TabsContent value="code" className="flex-1 flex flex-col mt-0">
                <ChatCodeTab
                  code={codeValue}
                  language={settings.language}
                  isAnalyzing={isAnalyzing}
                  onCodeChange={setCodeValue}
                  onSubmit={handleCodeSubmit}
                  messages={messages}
                />
              </TabsContent>
            )}

            {enableAnalytics && (
              <TabsContent value="analytics" className="flex-1 flex flex-col mt-0 overflow-auto">
                <AnalyticsTab analytics={analytics} messages={messages} />
              </TabsContent>
            )}
          </Tabs>
        ) : (
          <ChatMainContent
            messages={messages}
            inputValue={inputValue}
            placeholder={placeholder}
            isTyping={isTyping}
            isRecording={isRecording}
            useCopilotKit={useCopilotKit}
            enableCodeAssistance={enableCodeAssistance}
            enableVoiceInput={enableVoiceInput}
            enableFileUpload={enableFileUpload}
            settings={settings}
            chatContext={chatContext}
            artifacts={copilotArtifacts}
            copilotActions={copilotActions}
            onInputChange={setInputValue}
            onCopilotAction={onCopilotAction}
            onVoiceStart={startRecording}
            onVoiceStop={stopRecording}
            onSubmit={handleSubmit}
            onQuickAction={handleQuickAction}
            onMessageAction={handleMessageAction}
            onArtifactApprove={handleArtifactApprove}
            onArtifactReject={handleArtifactReject}
            onArtifactApply={handleArtifactApply}
          />
        )}
      </Card>
    </ErrorBoundary>
  );
};

// Export for backward compatibility
export default ChatInterface;

// Export commonly used exports to prevent import errors
export const DEFAULT_COPILOT_ACTIONS: CopilotAction[] = [];
