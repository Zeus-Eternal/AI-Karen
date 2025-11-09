/**
 * Copilot and AI Assistant Types
 * 
 * Type definitions for copilot actions, chat context, and AI assistance features.
 */

export interface ChatContext {
  selectedText?: string;
  currentFile?: string;
  language?: string;
  recentMessages: Array<{
    role: string;
    content: string;
    timestamp: Date;
  }>;
  codeContext: {
    hasCode: boolean;
    language?: string;
    errorCount: number;
  };
  conversationContext: {
    topic?: string;
    intent?: string;
    complexity: "simple" | "medium" | "complex";
  };
}

export interface CopilotAction {
  id: string;
  title: string;
  description: string;
  prompt: string;
  category: string;
  icon?: React.ComponentType<{ className?: string }> | string;
  shortcut?: string;
  requiresSelection?: boolean;
  contextTypes?: string[];
}

export interface Artifact {
  id: string;
  type: 'code' | 'document' | 'image' | 'data';
  title: string;
  content: string;
  language?: string;
  metadata?: Record<string, unknown>;
  createdAt: Date;
  updatedAt: Date;
}

export interface ChatModeOption {
  id: string;
  name: string;
  description: string;
  icon?: React.ComponentType<{ className?: string }> | string;
  enabled: boolean;
  settings?: Record<string, unknown>;
}