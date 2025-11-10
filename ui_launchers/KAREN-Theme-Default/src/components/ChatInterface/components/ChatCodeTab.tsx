"use client";

import React, { useRef } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Code, Eye, EyeOff, AlertCircle, Zap, FileText, Send, Loader2 } from "lucide-react";
import dynamic from "next/dynamic";
import { ChatSettings } from "../types";

// Lazy-load Copilot features only when enabled
const CopilotTextarea = dynamic(() => import("@/components/chat/copilot/CopilotTextarea").then(m => m.CopilotTextarea), { ssr: false });

interface ChatCodeTabProps {
  codeValue: string;
  onCodeChange: (value: string) => void;
  settings: ChatSettings;
  onSettingsChange: (settings: Partial<ChatSettings>) => void;
  isTyping: boolean;
  showCodePreview: boolean;
  onPreviewToggle: () => void;
  onCodeSubmit: (code: string) => void | Promise<void>;
  useCopilotKit: boolean;
  enableDocGeneration: boolean;
  isAnalyzing?: boolean;
  onQuickAction?: (action: string, prompt: string, type: string) => void | Promise<void>;
}

export const ChatCodeTab: React.FC<ChatCodeTabProps> = ({
  codeValue,
  onCodeChange,
  settings,
  onSettingsChange,
  isTyping,
  isAnalyzing,
  showCodePreview,
  onPreviewToggle,
  onCodeSubmit,
  onQuickAction,
  useCopilotKit,
  enableDocGeneration,
}) => {
  const codeTextareaRef = useRef<HTMLTextAreaElement>(null);

  const handleCodeAnalysis = async () => {
    if (!codeValue.trim() || isAnalyzing) return;
    
    const analysisPrompt = `Analyze this ${settings?.language || 'code'} code for issues, performance, and best practices:\n\n\`\`\`${settings?.language || 'code'}\n${codeValue}\n\`\`\``;
    // Since onQuickAction is optional, we need to handle it safely
    if (onQuickAction) {
      await onQuickAction("analyze", analysisPrompt, "analysis");
    }
  };

  return (
    <div className="flex-1 flex flex-col">
      {/* Toolbar */}
      <div className="px-3 py-2 border-b flex items-center justify-between bg-background/50">
        <div className="flex items-center gap-2">
          <Code className="h-4 w-4 " />
          <span className="font-medium">Code Assistant</span>
          {useCopilotKit && <span className="inline-flex items-center rounded-full border border-transparent bg-secondary text-secondary-foreground px-2 py-0.5 text-[10px] font-semibold">AI</span>}
          <span className="inline-flex items-center rounded-full border border-transparent bg-secondary text-secondary-foreground px-2 py-0.5 text-[10px] font-semibold">{settings?.model || 'model'}</span>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={settings?.language || 'javascript'}
            onChange={(e: React.ChangeEvent<HTMLSelectElement>) => onSettingsChange({ language: e.target.value })}
            className="px-2 py-1 border rounded-md text-xs sm:text-sm md:text-base"
            aria-label="Select programming language"
          >
            <option value="javascript">JavaScript</option>
            <option value="typescript">TypeScript</option>
            <option value="python">Python</option>
            <option value="java">Java</option>
            <option value="cpp">C++</option>
            <option value="csharp">C#</option>
            <option value="go">Go</option>
            <option value="rust">Rust</option>
            <option value="php">PHP</option>
            <option value="ruby">Ruby</option>
          </select>
          <Button variant="ghost" size="sm" className="h-8 px-2" onClick={onPreviewToggle} title={showCodePreview ? 'Hide Preview' : 'Show Preview'}>
            {showCodePreview ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </Button>
        </div>
      </div>

      {/* Editor + Preview */}
      <div className={`grid gap-3 p-3 ${showCodePreview ? 'grid-cols-1 md:grid-cols-2' : 'grid-cols-1'}`}>
        <div className="flex flex-col min-h-[300px]">
          {useCopilotKit ? (
            <div className="flex-1">
              {/* CopilotTextarea placeholder - will be implemented when available */}
              <textarea
                ref={codeTextareaRef}
                value={codeValue}
                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => onCodeChange(e.target.value)}
                placeholder="Write your code here... AI will provide suggestions as you type."
                className="flex-1 font-mono text-sm resize-none md:text-base lg:text-lg"
                rows={18}
                disabled={isTyping}
                aria-label="Code editor textarea"
              />
            </div>
          ) : (
            <textarea
              ref={codeTextareaRef}
              value={codeValue}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => onCodeChange(e.target.value)}
              placeholder="Write your code here..."
              className="flex-1 font-mono text-sm resize-none md:text-base lg:text-lg"
              rows={18}
              disabled={isTyping}
              aria-label="Code editor textarea"
            />
          )}
          {/* Actions */}
          <div className="flex flex-wrap gap-2 mt-3">
            <Button
              onClick={() => onCodeSubmit(codeValue)}
              disabled={!codeValue.trim() || isTyping}
            >
              {isTyping ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Send className="h-4 w-4 mr-2" />}
            </Button>
            <Button variant="outline" onClick={handleCodeAnalysis} disabled={!codeValue.trim() || isTyping || isAnalyzing}>
              {isAnalyzing ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <AlertCircle className="h-4 w-4 mr-2" />}
            </Button>
            <Button variant="outline" onClick={() => onQuickAction?.("optimize", `Optimize this ${settings?.language || 'code'} code:\n\n\`\`\`${settings?.language || 'code'}\n${codeValue}\n\`\`\``, "code")} disabled={!codeValue.trim() || isTyping || !onQuickAction}>
              <Zap className="h-4 w-4 mr-2" />
            </Button>
            <Button variant="outline" onClick={() => onQuickAction?.("docs", `Generate documentation for this ${settings?.language || 'code'} code:\n\n\`\`\`${settings?.language || 'code'}\n${codeValue}\n\`\`\``, "documentation")} disabled={!codeValue.trim() || isTyping || !onQuickAction}>
              <FileText className="h-4 w-4 mr-2" />
            </Button>
          </div>
        </div>

        {showCodePreview && (
          <div className="min-h-[300px] border rounded-md p-3 bg-muted/30 sm:p-4 md:p-6">
            <div className="text-xs text-muted-foreground mb-2 sm:text-sm md:text-base">Preview</div>
            <pre className="text-xs md:text-sm whitespace-pre-wrap font-mono overflow-auto max-h-[60vh]">{codeValue || '// Start typing code to preview here'}</pre>
          </div>
        )}
      </div>

      {/* Status bar */}
      <div className="px-3 py-2 text-[11px] md:text-xs text-muted-foreground border-t flex items-center gap-3">
        <span>Language: {settings?.language || 'javascript'}</span>
        <span>Model: {settings?.model || 'model'}</span>
        {isTyping && (
          <span className="inline-flex items-center gap-1">
            <Loader2 className="h-3 w-3 animate-spin" /> generating…
          </span>
        )}
      </div>
    </div>
  );
};