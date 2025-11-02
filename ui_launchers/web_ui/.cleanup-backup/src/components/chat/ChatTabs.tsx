"use client";

import React from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { MessageSquare, Code, BarChart3 } from "lucide-react";
import { ChatCodeTab } from "./ChatCodeTab";
import AnalyticsTab from "./AnalyticsTab";
import type { ChatMessage, ChatSettings, ChatAnalytics } from "./types";

interface ChatTabsProps {
  activeTab: string;
  showTabs: boolean;
  messages: ChatMessage[];
  settings: ChatSettings;
  analytics: ChatAnalytics;
  codeValue: string;
  showCodePreview: boolean;
  isTyping: boolean;
  useCopilotKit: boolean;
  enableDocGeneration: boolean;
  onTabChange: (tab: string) => void;
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

  return (
    <Tabs
      value={activeTab}
      onValueChange={onTabChange}
      className="flex-1 flex flex-col"
    >
      <TabsList className="grid w-full grid-cols-3 mx-4 mt-4">
        <TabsTrigger value="chat" className="flex items-center gap-2">
          <MessageSquare className="h-4 w-4" />
          Chat
        </TabsTrigger>
        <TabsTrigger value="code" className="flex items-center gap-2">
          <Code className="h-4 w-4" />
          Code
        </TabsTrigger>
        <TabsTrigger value="analytics" className="flex items-center gap-2">
          <BarChart3 className="h-4 w-4" />
          Analytics
        </TabsTrigger>
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
        />
      </TabsContent>

      <TabsContent value="analytics" className="flex-1 flex flex-col mt-0">
        <AnalyticsTab analytics={analytics} messages={messages} />
      </TabsContent>
    </Tabs>
  );
};
