"use client";

import React from "react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { MessageSquare, Code, BarChart3 } from "lucide-react";

// Hooks
import { useChatState } from "./hooks/useChatState";
import { useChatMessages } from "./hooks/useChatMessages";
import { useChatSettings } from "./hooks/useChatSettings";
import { useChatAnalytics } from "./hooks/useChatAnalytics";
import { useAuth } from "@/contexts/AuthContext";

// Components
import { ChatHeader } from "./components/ChatHeader";
import { ChatMessages } from "./components/ChatMessages";
import { ChatInput } from "./components/ChatInput";
import { ChatCodeTab } from "./components/ChatCodeTab";
import AnalyticsTab from "../chat/AnalyticsTab";

// Types
import { ChatInterfaceProps } from "./types";

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
  height = "600px",
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
  maxMessages = 1000,

  // Customization
  placeholder = "Ask me anything about code, get suggestions, or request help...",
  welcomeMessage,
  theme = "auto",

  // Callbacks
  onSettingsChange,
  onExport,
  onShare,
  onAnalyticsUpdate,
}) => {
  console.log('🔍 ChatInterface: Component mounting with props:', {
    initialMessagesCount: initialMessages.length,
    useCopilotKit,
    enableCodeAssistance,
    enableVoiceInput,
    className,
    height
  });

  // Initialize hooks
  const chatState = useChatState(initialMessages);
  const chatSettings = useChatSettings({}, onSettingsChange);
  const chatAnalytics = useChatAnalytics(
    chatState.messages,
    Date.now(),
    onAnalyticsUpdate
  );

  const { user } = useAuth(); // Assuming useAuth is available
  console.log('🔍 ChatInterface: Auth context user:', user);
  const chatMessages = useChatMessages(
    chatState.messages,
    chatState.setMessages,
    chatState.isTyping,
    chatState.setIsTyping,
    chatSettings.settings,
    chatState.sessionId,
    chatState.conversationId,
    user,
    useCopilotKit,
    enableCodeAssistance,
    enableContextualHelp,
    enableDocGeneration,
    maxMessages
  );

  // Chat context based on current state
  const chatContext = {
    selectedText: chatState.selectedText,
    currentFile: undefined, // TODO: Implement file context
    language: chatSettings.settings.language,
    recentMessages: chatState.messages.slice(-5).map(m => ({
      role: m.role,
      content: m.content.substring(0, 100) + (m.content.length > 100 ? "..." : ""),
      timestamp: m.timestamp
    })),
    codeContext: {
      hasCode: chatState.messages.some(m => m.type === "code"),
      language: chatSettings.settings.language,
      errorCount: 0 // TODO: Implement error counting
    },
    conversationContext: {
      topic: undefined, // TODO: Implement topic detection
      intent: undefined, // TODO: Implement intent detection
      complexity: "medium" as const
    }
  };

  // Voice input handlers
  const handleVoiceStart = () => {
    console.log('🔊 Voice recording started');
    chatState.setIsRecording(true);
  };

  const handleVoiceStop = () => {
    console.log('🔊 Voice recording stopped');
    chatState.setIsRecording(false);
  };

  // Copilot action handler
  const handleCopilotAction = (action: any) => {
    console.log('🤖 Copilot action triggered:', action);
    // TODO: Implement copilot action logic
  };

  // Quick action handler
  const handleQuickAction = (action: string, prompt: string, type?: string) => {
    console.log('⚡ Quick action:', { action, prompt, type });
    if (prompt.trim() && !chatState.isTyping) {
      chatMessages.sendMessage(prompt, type as any);
    }
  };

  // Render chat tab content
  const renderChatTab = () => (
    <div className="flex-1 flex flex-col">
      {/* Messages Area */}
      <ChatMessages
        messages={chatState.messages}
        isTyping={chatState.isTyping}
        useCopilotKit={useCopilotKit}
        enableCodeAssistance={enableCodeAssistance}
        settings={chatSettings.settings}
        onMessageAction={chatMessages.handleMessageAction}
        onArtifactApprove={(artifactId: string) => {
          console.log('Artifact approved:', artifactId);
          // TODO: Implement artifact approval logic
        }}
        onArtifactReject={(artifactId: string) => {
          console.log('Artifact rejected:', artifactId);
          // TODO: Implement artifact rejection logic
        }}
        onArtifactApply={(artifactId: string) => {
          console.log('Artifact applied:', artifactId);
          // TODO: Implement artifact application logic
        }}
      />

      {/* Input Area */}
      <div className="border-t p-4" id="chat-input">
        <ChatInput
          inputValue={chatState.inputValue}
          onInputChange={chatState.setInputValue}
          onSubmit={(e: React.FormEvent) => {
            e.preventDefault();
            if (chatState.inputValue.trim() && !chatState.isTyping) {
              chatMessages.sendMessage(chatState.inputValue, "text");
              chatState.clearInput();
            }
          }}
          placeholder={placeholder}
          isTyping={chatState.isTyping}
          isRecording={chatState.isRecording}
          enableVoiceInput={enableVoiceInput}
          enableFileUpload={enableFileUpload}
          chatContext={chatContext}
          onCopilotAction={handleCopilotAction}
          onVoiceStart={handleVoiceStart}
          onVoiceStop={handleVoiceStop}
          onQuickAction={handleQuickAction}
        />
      </div>
    </div>
  );

  // Render code tab content (simplified for now)
  const renderCodeTab = () => (
    <ChatCodeTab
      codeValue={chatState.codeValue}
      onCodeChange={chatState.setCodeValue}
      settings={chatSettings.settings}
      onSettingsChange={chatSettings.updateSettings}
      isTyping={chatState.isTyping}
      isAnalyzing={chatState.isAnalyzing}
      showCodePreview={chatState.showCodePreview}
      onPreviewToggle={() => chatState.setShowCodePreview(!chatState.showCodePreview)}
      onCodeSubmit={() => {
        if (chatState.codeValue.trim() && !chatState.isTyping) {
          chatMessages.sendMessage(chatState.codeValue, "code");
        }
      }}
      onQuickAction={(action, prompt, type) => {
        if (!chatState.isTyping) {
          return chatMessages.sendMessage(prompt, type as any);
        }
      }}
      useCopilotKit={useCopilotKit}
      enableDocGeneration={enableDocGeneration}
    />
  );

  return (
    <React.Fragment>
      {/* Skip to main content link for accessibility */}
      <a
        href="#chat-input"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-primary text-primary-foreground px-4 py-2 rounded-md z-50 transition-all duration-200"
        tabIndex={0}
      >
        Skip to message input
      </a>

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
              onSettingsChange={chatSettings.updateSettings}
              onExport={() => onExport?.(chatState.messages)}
              onShare={onShare}
              onToggleFullscreen={() => chatState.setIsFullscreen(!chatState.isFullscreen)}
              onShowRoutingHistory={() => chatState.setShowRoutingHistory(true)}
            />
          </CardHeader>
        )}

        <CardContent className="flex-1 flex flex-col p-0">
          {showTabs ? (
            <Tabs
              value={chatState.activeTab}
              onValueChange={(value: string) => chatState.setActiveTab(value as "chat" | "code" | "analytics")}
              className="flex-1 flex flex-col"
            >
              <TabsList className="grid w-full grid-cols-3 mx-3 mt-3">
                <TabsTrigger value="chat" className="flex items-center gap-2">
                  <MessageSquare className="h-4 w-4" />
                  Chat
                </TabsTrigger>
                <TabsTrigger value="code" className="flex items-center gap-2">
                  <Code className="h-4 w-4" />
                  Code
                </TabsTrigger>
                <TabsTrigger
                  value="analytics"
                  className="flex items-center gap-2"
                >
                  <BarChart3 className="h-4 w-4" />
                  Analytics
                </TabsTrigger>
              </TabsList>

              <TabsContent value="chat" className="flex-1 flex flex-col mt-0">
                {renderChatTab()}
              </TabsContent>

              <TabsContent value="code" className="flex-1 flex flex-col mt-0">
                {renderCodeTab()}
              </TabsContent>

              <TabsContent
                value="analytics"
                className="flex-1 flex flex-col mt-0"
              >
                <AnalyticsTab 
                  analytics={chatAnalytics.analytics} 
                  messages={chatState.messages} 
                />
              </TabsContent>
            </Tabs>
          ) : (
            renderChatTab()
          )}
        </CardContent>
      </Card>
    </React.Fragment>
  );
};
