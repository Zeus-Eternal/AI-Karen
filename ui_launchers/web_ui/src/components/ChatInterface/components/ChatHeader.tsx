"use client";

import React from "react";
import { CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Activity, Maximize2, Minimize2, Settings, Sparkles } from "lucide-react";
import ModelSelector from "@/components/chat/ModelSelector";
import ExportShareHandler from "./ExportShareHandler";
import type { ChatSettings, ChatMessage } from "../types";

interface ChatHeaderProps {
  showHeader: boolean;
  useCopilotKit: boolean;
  selectedMessages: Set<string>;
  enableExport: boolean;
  enableSharing: boolean;
  showSettings: boolean;
  settings: ChatSettings;
  isFullscreen: boolean;
  messages: ChatMessage[];
  onSettingsChange: (settings: Partial<ChatSettings>) => void;
  onExport?: (messages: ChatMessage[]) => void;
  onShare?: (messages: ChatMessage[]) => void;
  onToggleFullscreen: () => void;
  onShowRoutingHistory: () => void;
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({
  showHeader,
  useCopilotKit,
  selectedMessages,
  enableExport,
  enableSharing,
  showSettings,
  settings,
  isFullscreen,
  messages,
  onSettingsChange,
  onExport,
  onShare,
  onToggleFullscreen,
  onShowRoutingHistory,
}: ChatHeaderProps) => {
  if (!showHeader) return null;

  return (
    <CardHeader className="pb-3">
      <div className="flex items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 sm:w-auto md:w-full" />
          AI Assistant
          {useCopilotKit && (
            <Badge variant="secondary" className="text-xs sm:text-sm md:text-base">
              CopilotKit Enhanced
            </Badge>
          )}
          <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
            Production Ready
          </Badge>
        </CardTitle>

        <div className="flex items-center gap-2">
          {selectedMessages.size > 0 && (
            <Badge variant="secondary" className="text-xs sm:text-sm md:text-base">
              {selectedMessages.size} selected
            </Badge>
          )}

          <ExportShareHandler
            messages={messages}
            enableExport={enableExport}
            enableSharing={enableSharing}
            onExport={onExport}
            onShare={onShare}
          />

          {/* Model selector */}
          <ModelSelector
            value={settings.model}
            onValueChange={(value: string) => onSettingsChange({ model: value })}
            className="w-48 sm:w-auto md:w-full"
            placeholder="Select model..."
            showDetails={true}
            task="chat"
          />

          {/* Routing History */}
          <Button
            variant="ghost"
            size="sm"
            onClick={onShowRoutingHistory}
            className="h-8 w-8 p-0 sm:w-auto md:w-full"
            title="Routing History"
          >
            <Activity className="h-4 w-4 sm:w-auto md:w-full" />
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={onToggleFullscreen}
            className="h-8 w-8 p-0 sm:w-auto md:w-full"
            title={isFullscreen ? "Exit Fullscreen" : "Enter Fullscreen"}
          >
            {isFullscreen ? (
              <Minimize2 className="h-4 w-4 sm:w-auto md:w-full" />
            ) : (
              <Maximize2 className="h-4 w-4 sm:w-auto md:w-full" />
            )}
          </Button>

          {showSettings && (
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0 sm:w-auto md:w-full"
              title="Settings"
            >
              <Settings className="h-4 w-4 sm:w-auto md:w-full" />
            </Button>
          )}
        </div>
      </div>
    </CardHeader>
  );
};
