"use client";

import React, { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Code, Eye, EyeOff, Send, Loader2 } from "lucide-react";
import dynamic from "next/dynamic";

// Lazy-load Copilot features
const CopilotTextarea = dynamic(() => 
  import("@/components/chat/copilot/CopilotTextarea").then(m => m.CopilotTextarea), 
  { ssr: false }
);

import type { ChatSettings } from "./types";

interface ChatCodeTabProps {
  useCopilotKit: boolean;
  settings: ChatSettings;
  codeValue: string;
  showCodePreview: boolean;
  isTyping: boolean;
  enableDocGeneration: boolean;
  onSettingsChange: (settings: Partial<ChatSettings>) => void;
  onCodeChange: (value: string) => void;
  onPreviewToggle: () => void;
  onCodeSubmit: () => void;
}

export const ChatCodeTab: React.FC<ChatCodeTabProps> = ({
  useCopilotKit,
  settings,
  codeValue,
  showCodePreview,
  isTyping,
  enableDocGeneration,
  onSettingsChange,
  onCodeChange,
  onPreviewToggle,
  onCodeSubmit,
}) => {
  const codeTextareaRef = useRef<HTMLTextAreaElement>(null);

  const languages = [
    { value: "javascript", label: "JavaScript" },
    { value: "typescript", label: "TypeScript" },
    { value: "python", label: "Python" },
    { value: "java", label: "Java" },
    { value: "cpp", label: "C++" },
    { value: "csharp", label: "C#" },
    { value: "go", label: "Go" },
    { value: "rust", label: "Rust" },
    { value: "php", label: "PHP" },
    { value: "ruby", label: "Ruby" },
  ];

  return (
    <div className="flex-1 flex flex-col">
      {/* Toolbar */}
      <div className="px-3 py-2 border-b flex items-center justify-between bg-background/50">
        <div className="flex items-center gap-2">
          <Code className="h-4 w-4" />
          <span className="font-medium">Code Assistant</span>
          {useCopilotKit && (
            <Badge variant="secondary" className="text-[10px]">
              AI
            </Badge>
          )}
          <Badge variant="outline" className="text-[10px]">
            {settings.model || 'model'}
          </Badge>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={settings.language}
            onChange={(e) => onSettingsChange({ language: e.target.value })}
            className="px-2 py-1 border rounded-md text-xs bg-background"
          >
            {languages.map((lang) => (
              <option key={lang.value} value={lang.value}>
                {lang.label}
              </option>
            ))}
          </select>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 px-2"
            onClick={onPreviewToggle}
            title={showCodePreview ? 'Hide Preview' : 'Show Preview'}
          >
            {showCodePreview ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </Button>
        </div>
      </div>

      {/* Editor + Preview */}
      <div className={`grid gap-3 p-3 ${showCodePreview ? 'grid-cols-1 md:grid-cols-2' : 'grid-cols-1'}`}>
        <div className="flex flex-col min-h-[300px]">
          {useCopilotKit ? (
            <CopilotTextarea
              value={codeValue}
              onChange={onCodeChange}
              placeholder="Write your code here... AI will provide suggestions as you type."
              language={settings.language}
              enableSuggestions={settings.enableSuggestions}
              enableCodeAnalysis={settings.enableCodeAnalysis}
              enableDocGeneration={enableDocGeneration}
              className="flex-1 font-mono text-sm"
              rows={18}
              disabled={isTyping}
            />
          ) : (
            <Textarea
              ref={codeTextareaRef}
              value={codeValue}
              onChange={(e) => onCodeChange(e.target.value)}
              placeholder="Write your code here..."
              className="flex-1 font-mono text-sm resize-none"
              rows={18}
              disabled={isTyping}
            />
          )}
          
          {/* Submit Button */}
          <div className="mt-2 flex justify-end">
            <Button
              onClick={onCodeSubmit}
              disabled={isTyping || !codeValue.trim()}
              size="sm"
              className="gap-2"
            >
              {isTyping ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
              {isTyping ? "Processing..." : "Analyze Code"}
            </Button>
          </div>
        </div>

        {/* Preview Panel */}
        {showCodePreview && (
          <div className="flex flex-col min-h-[300px] border rounded-lg bg-muted/20">
            <div className="px-3 py-2 border-b bg-muted/40 rounded-t-lg">
              <span className="text-sm font-medium">Preview</span>
            </div>
            <div className="flex-1 p-3">
              <pre className="text-sm font-mono whitespace-pre-wrap">
                {codeValue || "Code preview will appear here..."}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
