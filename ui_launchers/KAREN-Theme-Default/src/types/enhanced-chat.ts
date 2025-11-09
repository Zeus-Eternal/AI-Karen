/**
 * Enhanced Chat Interface Types
 * Supporting context awareness, multimodal interactions, and advanced features
 */

export interface EnhancedChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  type?: 'text' | 'code' | 'image' | 'file' | 'multimodal';
  status?: 'sending' | 'sent' | 'generating' | 'completed' | 'error';
  
  // Context and reasoning
  context?: MessageContext;
  reasoning?: ReasoningChain;
  confidence?: number;
  
  // Multimodal support
  attachments?: Attachment[];
  
  // Metadata
  metadata?: MessageMetadata;
}

export interface MessageContext {
  conversationId: string;
  threadId?: string;
  parentMessageId?: string;
  relatedMessages?: string[];
  topics?: string[];
  intent?: string;
  sentiment?: 'positive' | 'neutral' | 'negative';
  memoryReferences?: MemoryReference[];
}

export interface ReasoningChain {
  steps: ReasoningStep[];
  confidence: number;
  sources: SourceAttribution[];
  methodology: string;
}

export interface ReasoningStep {
  id: string;
  description: string;
  type: 'analysis' | 'inference' | 'retrieval' | 'synthesis';
  confidence: number;
  evidence?: string[];
  timestamp: Date;
}

export interface SourceAttribution {
  id: string;
  type: 'memory' | 'knowledge_base' | 'web' | 'document' | 'conversation';
  title: string;
  url?: string;
  reliability: number;
  relevance: number;
  snippet?: string;
}

export interface Attachment {
  id: string;
  name: string;
  type: 'image' | 'document' | 'code' | 'audio' | 'video';
  size: number;
  url: string;
  mimeType: string;
  metadata?: AttachmentMetadata;
  analysis?: AttachmentAnalysis;
}

export interface AttachmentMetadata {
  dimensions?: { width: number; height: number };
  duration?: number;
  language?: string;
  encoding?: string;
  [key: string]: any;
}

export interface AttachmentAnalysis {
  summary?: string;
  entities?: string[];
  topics?: string[];
  sentiment?: string;
  confidence?: number;
  extractedText?: string;
}

export interface MessageMetadata {
  model?: string;
  provider?: string;
  tokens?: number;
  cost?: number;
  latency?: number;
  temperature?: number;
  maxTokens?: number;
  suggestions?: ContextSuggestion[];
  rating?: 'up' | 'down';
  tags?: string[];
}

export interface ContextSuggestion {
  id: string;
  type: 'follow_up' | 'clarification' | 'related_topic' | 'action';
  text: string;
  confidence: number;
  reasoning?: string;
}

export interface MemoryReference {
  id: string;
  type: 'episodic' | 'semantic' | 'procedural';
  content: string;
  relevance: number;
  timestamp: Date;
  source?: string;
}

export interface ConversationThread {
  id: string;
  title: string;
  topic?: string;
  messages?: EnhancedChatMessage[];
  participants: Array<{ id: string; name?: string }>;
  createdAt: string | number | Date;
  updatedAt?: Date;
  status?: 'active' | 'archived' | 'deleted';
  metadata: {
    messageCount: number;
    complexity: string;
    averageResponseTime?: number;
    topicDrift?: number;
    sentiment?: 'positive' | 'neutral' | 'negative';
    tags?: string[];
    summary?: string;
  };
}

export interface ThreadMetadata {
  messageCount: number;
  averageResponseTime: number;
  topicDrift: number;
  sentiment: 'positive' | 'neutral' | 'negative';
  complexity: 'simple' | 'medium' | 'complex';
  tags: string[];
  summary?: string;
}

export interface ConversationContext {
  currentThread: ConversationThread;
  relatedThreads: ConversationThread[];
  userPatterns: UserPattern[];
  sessionContext: SessionContext;
  memoryContext: MemoryContext;
}

export interface UserPattern {
  type: 'preference' | 'behavior' | 'expertise' | 'interest';
  pattern: string;
  confidence: number;
  frequency: number;
  lastSeen: Date;
}

export interface SessionContext {
  sessionId: string;
  startTime: Date;
  duration: number;
  messageCount: number;
  topics: string[];
  mood: string;
  focus: string[];
}

export interface MemoryContext {
  recentMemories: MemoryReference[];
  relevantMemories: MemoryReference[];
  memoryStats: {
    totalMemories: number;
    relevantCount: number;
    averageRelevance: number;
  };
}

export interface ConversationExport {
  format: 'json' | 'markdown' | 'pdf' | 'html';
  includeMetadata: boolean;
  includeReasoning: boolean;
  includeAttachments: boolean;
  dateRange?: { start: Date; end: Date };
  threadIds?: string[];
}

export interface ConversationShare {
  shareId: string;
  type: 'public' | 'private' | 'team';
  permissions: SharePermission[];
  expiresAt?: Date;
  password?: string;
  allowComments: boolean;
  allowDownload: boolean;
}

export interface SharePermission {
  userId: string;
  role: 'viewer' | 'commenter' | 'editor';
  grantedAt: Date;
  grantedBy: string;
}

export interface ContextPanelProps {
  conversation: ConversationContext;
  onThreadSelect: (threadId: string) => void;
  onMemorySelect: (memoryId: string) => void;
  onSuggestionSelect: (suggestion: ContextSuggestion) => void;
  className?: string;
}

export interface EnhancedChatInterfaceProps {
  // Core functionality
  conversationId?: string;
  initialMessages?: EnhancedChatMessage[];
  
  // Context features
  enableContextPanel?: boolean;
  enableSuggestions?: boolean;
  enableThreading?: boolean;
  enableMemoryIntegration?: boolean;
  
  // Multimodal features
  enableFileUpload?: boolean;
  enableImageAnalysis?: boolean;
  enableVoiceInput?: boolean;
  
  // Advanced features
  enableReasoning?: boolean;
  enableExport?: boolean;
  enableSharing?: boolean;
  
  // Callbacks
  onMessageSent?: (message: EnhancedChatMessage) => void;
  onMessageReceived?: (message: EnhancedChatMessage) => void;
  onContextChange?: (context: ConversationContext) => void;
  onExport?: (exportConfig: ConversationExport) => void;
  onShare?: (shareConfig: ConversationShare) => void;
  
  // UI configuration
  className?: string;
  height?: string;
  theme?: 'light' | 'dark' | 'auto';
}