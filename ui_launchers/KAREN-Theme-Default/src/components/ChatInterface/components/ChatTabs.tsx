"use client";

import React from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { MessageSquare, Code, BarChart3 } from "lucide-react";
import { ChatCodeTab } from "./ChatCodeTab";
import AnalyticsTab from "./AnalyticsTab";
import type { ChatMessage, ChatSettings, ChatAnalytics } from "../types";

interface ChatTabsProps {
  activeTab: "chat" | "code" | "analytics";
  showTabs: boolean;
  messages: ChatMessage[];
  settings: ChatSettings;
  analytics: ChatAnalytics;
  codeValue: string;
  showCodePreview: boolean;
  isTyping: boolean;
  useCopilotKit: boolean;
  enableDocGeneration: boolean;
  enableAnalytics?: boolean;
  onTabChange: (tab: "chat" | "code" | "analytics") => void;
  onSettingsChange: (settings: Partial<ChatSettings>) => void;
  onCodeChange: (value: string) => void;
  onPreviewToggle: () => void;
  onCodeSubmit: () => void;
  renderChatTab: () => React.ReactNode;
}

export const ChatTabs: React.FC<ChatTabsProps> = ({
  activeTab,
  showTabs,
  messages,
  settings,
  analytics,
  codeValue,
  showCodePreview,
  isTyping,
  useCopilotKit,
  enableDocGeneration,
  enableAnalytics = true,
  onTabChange,
  onSettingsChange,
  onCodeChange,
  onPreviewToggle,
  onCodeSubmit,
  renderChatTab,
}) => {
  if (!showTabs) {
    return <>{renderChatTab()}</>;
  }

  const tabColumns = enableAnalytics ? "grid-cols-3" : "grid-cols-2";

  return (
    <Tabs value={activeTab} onValueChange={(value) => onTabChange(value as ChatTabsProps["activeTab"])} className="flex-1 flex flex-col">
      <TabsList className={`grid w-full ${tabColumns} mx-4 mt-4`}>
        <TabsTrigger value="chat" className="flex items-center gap-2">
          <MessageSquare className="h-4 w-4 " />
        </TabsTrigger>
        <TabsTrigger value="code" className="flex items-center gap-2">
          <Code className="h-4 w-4 " />
        </TabsTrigger>
        {enableAnalytics && (
          <TabsTrigger value="analytics" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4 " />
          </TabsTrigger>
        )}
      </TabsList>

      <TabsContent value="chat" className="flex-1 flex flex-col mt-0">
        {renderChatTab()}
      </TabsContent>

      <TabsContent value="code" className="flex-1 flex flex-col mt-0">
        <ChatCodeTab
          useCopilotKit={useCopilotKit}
          settings={settings}
          codeValue={codeValue}
          showCodePreview={showCodePreview}
          isTyping={isTyping}
          enableDocGeneration={enableDocGeneration}
          onSettingsChange={onSettingsChange}
          onCodeChange={onCodeChange}
          onPreviewToggle={onPreviewToggle}
          onCodeSubmit={onCodeSubmit}
          onQuickAction={() => undefined}
        />
      </TabsContent>

      {enableAnalytics && (
        <TabsContent value="analytics" className="flex-1 flex flex-col mt-0">
          <AnalyticsTab analytics={analytics} messages={messages} />
        </TabsContent>
      )}
    </Tabs>
  );
};
