"use client";

import React, { useCallback, useMemo } from "react";
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
import { useAuth } from "@/hooks/use-auth";
import type { ChatInterfaceProps, CopilotAction, CopilotArtifact, ChatContext } from "./types";
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
    sessionStartTime,
    copilotArtifacts,
    setCopilotArtifacts,
  } = useChatState(initialMessages, welcomeMessage);

  // Settings management
  const { settings, updateSettings } = useChatSettings(
    {},
    onSettingsChange
  );

  // Analytics management
  const { analytics } = useChatAnalytics(
    messages,
    sessionStartTime,
    onAnalyticsUpdate
  );

  // Message handling
  const {
    sendMessage,
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
  const { availableActions } = useCopilotIntegration({
    enabled: useCopilotKit,
    actions: [],
    messages,
    settings,
    context: {
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
    },
  });

  // Voice input handling
  const { handleVoiceStart, handleVoiceStop } = useVoiceInput({
    enabled: enableVoiceInput,
    isRecording,
    startRecording: async () => setIsRecording(true),
    stopRecording: () => setIsRecording(false),
  });

  // Artifact management
  const { artifacts, approveArtifact, rejectArtifact, applyArtifact } = useArtifactManagement({
    artifacts: copilotArtifacts,
    updateArtifact: (artifactId: string, updates: Partial<CopilotArtifact>) => {
      setCopilotArtifacts(prev => prev.map(artifact => 
        artifact.id === artifactId ? { ...artifact, ...updates } : artifact
      ));
    },
  });

  // Chat context for CopilotActions
  const chatContext: ChatContext = useMemo(() => ({
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
  }), [messages, selectedText, settings.language]);

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
      safeDebug("Copilot action triggered:", action);
      // Handle the copilot action by sending it as a message
      sendMessage(action.prompt, "text", { context: chatContext });
    },
    [sendMessage, chatContext]
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
      fallback={({ resetError }) => (
        <div className="p-4 text-center">
          <p className="text-destructive">An error occurred in the chat interface.</p>
          <p className="text-sm text-muted-foreground mt-2">Please refresh the page to try again.</p>
          <button 
            onClick={resetError}
            className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90"
          >
            Try Again
          </button>
        </div>
      )}
    >
      <Card
        className={`flex flex-col overflow-hidden ${className}`}
        style={{ height }}
        data-theme={theme}
      >
        {showHeader && (
          <ChatHeader
            showHeader={showHeader}
            useCopilotKit={useCopilotKit}
            selectedMessages={new Set<string>()}
            enableExport={enableExport}
            enableSharing={enableSharing}
            showSettings={showSettings}
            settings={settings}
            isFullscreen={isFullscreen}
            messages={messages}
            onSettingsChange={updateSettings}
            onExport={handleExport}
            onShare={handleShare}
            onToggleFullscreen={() => setIsFullscreen(!isFullscreen)}
            onShowRoutingHistory={() => setShowRoutingHistory(!showRoutingHistory)}
          />
        )}

        {showTabs ? (
          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as unknown)} className="flex-1 flex flex-col">
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
                artifacts={artifacts}
                copilotActions={availableActions}
                onInputChange={setInputValue}
                onCopilotAction={onCopilotAction}
                onVoiceStart={handleVoiceStart}
                onVoiceStop={handleVoiceStop}
                onSubmit={handleSubmit}
                onQuickAction={handleQuickAction}
                onMessageAction={handleMessageAction}
                onArtifactApprove={approveArtifact}
                onArtifactReject={rejectArtifact}
                onArtifactApply={applyArtifact}
                messagesEndRef={messagesEndRef}
              />
            </TabsContent>

            {enableCodeAssistance && (
              <TabsContent value="code" className="flex-1 flex flex-col mt-0">
                <ChatCodeTab
                  codeValue={codeValue}
                  onCodeChange={setCodeValue}
                  settings={settings}
                  onSettingsChange={updateSettings}
                  isTyping={isTyping}
                  showCodePreview={showCodePreview}
                  onPreviewToggle={() => setShowCodePreview(!showCodePreview)}
                  onCodeSubmit={(code: string) => sendMessage(code, "code")}
                  useCopilotKit={useCopilotKit}
                  enableDocGeneration={enableDocGeneration}
                  isAnalyzing={isAnalyzing}
                  onQuickAction={handleQuickAction}
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
            artifacts={artifacts}
            copilotActions={availableActions}
            onInputChange={setInputValue}
            onCopilotAction={onCopilotAction}
            onVoiceStart={handleVoiceStart}
            onVoiceStop={handleVoiceStop}
            onSubmit={handleSubmit}
            onQuickAction={handleQuickAction}
            onMessageAction={handleMessageAction}
            onArtifactApprove={approveArtifact}
            onArtifactReject={rejectArtifact}
            onArtifactApply={applyArtifact}
            messagesEndRef={messagesEndRef}
          />
        )}
      </Card>
    </ErrorBoundary>
  );
};

// Export for backward compatibility
export default ChatInterface;
