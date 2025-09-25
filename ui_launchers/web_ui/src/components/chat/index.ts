export { ChatInterface } from '@/components/ChatInterface';
export { CopilotChat } from './copilot';

// Export supporting components
export { MessageBubble } from './MessageBubble';
export { MetaBar } from './MetaBar';
export { ChatBubble } from './ChatBubble';
export { default as ModelSelector } from './ModelSelector';
export { default as EnhancedModelSelector } from './EnhancedModelSelector';

// Export copilot components
export { default as CopilotActions } from './CopilotActions';
export { default as CopilotArtifacts } from './CopilotArtifacts';
export { default as EnhancedMessageBubble } from './EnhancedMessageBubble';
export type { CopilotAction, ChatContext } from './CopilotActions';
export type { CopilotArtifact } from './CopilotArtifacts';

// Export AG-UI components
export { ConversationGrid } from './ConversationGrid';
export type { ConversationRow } from './ConversationGrid';

export { ChatAnalyticsChart } from './ChatAnalyticsChart';
export type { ChatAnalyticsData } from './ChatAnalyticsChart';

export { MemoryGrid } from './MemoryGrid';
export type { MemoryRow } from './MemoryGrid';
