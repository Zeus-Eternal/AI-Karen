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
import { export { default as EnhancedChatInterface } from './EnhancedChatInterface';

// Context awareness components
import { export { default as ContextPanel } from './ContextPanel';
import { export { default as ContextSuggestions } from './ContextSuggestions';
import { export { default as ConversationThreading } from './ConversationThreading';

// Multimodal components
import { export { default as MultimodalFileUpload } from './MultimodalFileUpload';
import { export { default as FilePreview } from './FilePreview';
import { export { default as ImageAnalysis } from './ImageAnalysis';

// Reasoning and confidence components
import { export { default as ReasoningVisualization } from './ReasoningVisualization';
import { export { default as ConfidenceScoring } from './ConfidenceScoring';
import { export { default as SourceAttribution } from './SourceAttribution';

// Conversation management components
import { export { default as ConversationManager } from './ConversationManager';
import { export { default as ConversationTemplates } from './ConversationTemplates';
import { export { default as ConversationExportShare } from './ConversationExportShare';

// Re-export types for convenience
export type {
import { } from '@/types/enhanced-chat';