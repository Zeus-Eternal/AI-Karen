// Export modern AG-UI + CopilotKit interface as default
export { default as ChatInterface } from './ModernChatInterface';
export { default as ModernChatInterface } from './ModernChatInterface';

// Export legacy interface for backward compatibility (deprecated)
export { default as LegacyChatInterface } from './ChatInterface';

// Export supporting components
export { MessageBubble } from './MessageBubble';

// Export AG-UI components
export { ConversationGrid } from './ConversationGrid';
export type { ConversationRow } from './ConversationGrid';

export { ChatAnalyticsChart } from './ChatAnalyticsChart';
export type { ChatAnalyticsData } from './ChatAnalyticsChart';

export { MemoryGrid } from './MemoryGrid';
export type { MemoryRow } from './MemoryGrid';

export { EnhancedChatInterface } from './EnhancedChatInterface';