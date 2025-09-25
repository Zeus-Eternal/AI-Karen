"use client";

import React, { useRef } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Mic, MicOff, Paperclip, Send, Loader2 } from "lucide-react";
import CopilotActions, { type CopilotAction, type ChatContext } from "@/components/chat/CopilotActions";

interface ChatInputProps {
  inputValue: string;
  placeholder: string;
  isTyping: boolean;
  isRecording: boolean;
  enableVoiceInput: boolean;
  enableFileUpload: boolean;
  chatContext: ChatContext;
  onInputChange: (value: string) => void;
  onCopilotAction: (action: CopilotAction) => void;
  onVoiceStart: () => void;
  onVoiceStop: () => void;
  onSubmit: (e: React.FormEvent) => void;
  onQuickAction: (action: string, prompt: string, type?: string) => void;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  inputValue,
  placeholder,
  isTyping,
  isRecording,
  enableVoiceInput,
  enableFileUpload,
  chatContext,
  onInputChange,
  onCopilotAction,
  onVoiceStart,
  onVoiceStop,
  onSubmit,
  onQuickAction,
}) => {
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div className="border-t p-4" id="chat-input">
      <form onSubmit={onSubmit} className="flex gap-2">
        <div className="flex-1 relative">
          <Input
            ref={inputRef}
            value={inputValue}
            onChange={(e) => onInputChange(e.target.value)}
            placeholder={placeholder}
            disabled={isTyping}
            className="pr-20"
            aria-label="Type your message"
            aria-describedby={isTyping ? "typing-indicator" : undefined}
          />

          {/* Voice Input Button */}
          {enableVoiceInput && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="absolute right-12 top-1/2 -translate-y-1/2 h-6 w-6 p-0"
              onClick={isRecording ? onVoiceStop : onVoiceStart}
              disabled={isTyping}
            >
              {isRecording ? (
                <MicOff className="h-4 w-4 text-red-500" />
              ) : (
                <Mic className="h-4 w-4" />
              )}
            </Button>
          )}

          {/* File Upload Button */}
          {enableFileUpload && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="absolute right-6 top-1/2 -translate-y-1/2 h-6 w-6 p-0"
              disabled={isTyping}
            >
              <Paperclip className="h-4 w-4" />
            </Button>
          )}
        </div>

        <Button
          type="submit"
          disabled={!inputValue.trim() || isTyping}
          size="sm"
        >
          {isTyping ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </Button>
      </form>

      {/* Quick Actions */}
      <div className="flex items-center justify-between mt-2">
        <CopilotActions
          onActionTriggered={onCopilotAction}
          context={chatContext}
          disabled={isTyping}
          showShortcuts={true}
        />

        <div className="flex items-center gap-2 flex-wrap">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onQuickAction("debug", "Help me debug this code", "code")}
            disabled={isTyping}
          >
            Debug Code
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onQuickAction("explain", "Explain this concept", "text")}
            disabled={isTyping}
          >
            Explain
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onQuickAction("docs", "Generate documentation", "documentation")}
            disabled={isTyping}
          >
            Document
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onQuickAction("optimize", "Optimize this code", "code")}
            disabled={isTyping}
          >
            Optimize
          </Button>
        </div>
      </div>
    </div>
  );
};
