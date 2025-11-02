/**
 * Enhanced Chat Interface Components
 * 
 * This module provides context-aware chat components with advanced features:
 * - Context panel with conversation history and memory integration
 * - Smart suggestions based on conversation patterns
 * - Conversation threading and organization
 * - Export and sharing capabilities
 * - Reasoning visualization and confidence scoring
 * - Multimodal file upload and preview
 * - Conversation management and templates
 */

// Main chat interface
export { default as EnhancedChatInterface } from './EnhancedChatInterface';

// Context awareness components
export { default as ContextPanel } from './ContextPanel';
export { default as ContextSuggestions } from './ContextSuggestions';
export { default as ConversationThreading } from './ConversationThreading';

// Multimodal components
export { default as MultimodalFileUpload } from './MultimodalFileUpload';
export { default as FilePreview } from './FilePreview';
export { default as ImageAnalysis } from './ImageAnalysis';

// Reasoning and confidence components
export { default as ReasoningVisualization } from './ReasoningVisualization';
export { default as ConfidenceScoring } from './ConfidenceScoring';
export { default as SourceAttribution } from './SourceAttribution';

// Conversation management components
export { default as ConversationManager } from './ConversationManager';
export { default as ConversationTemplates } from './ConversationTemplates';
export { default as ConversationExportShare } from './ConversationExportShare';

// Re-export types for convenience
export type {
  EnhancedChatMessage,
  ConversationContext,
  ConversationThread,
  ContextSuggestion,
  MemoryReference,
  ReasoningChain,
  ReasoningStep,
  SourceAttribution as SourceAttributionType,
  Attachment,
  AttachmentMetadata,
  AttachmentAnalysis,
  ConversationExport,
  ConversationShare,
  EnhancedChatInterfaceProps,
  ContextPanelProps
} from '@/types/enhanced-chat';