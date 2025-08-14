// Export CopilotChat interface as default
export { CopilotChat as ChatInterface } from './copilot';
export { CopilotChat } from './copilot';

// Export enhanced chat interfaces
export { ChatInterface as EnhancedChatInterface, LegacyChatInterface } from './ChatInterface';

// Export supporting components
export { MessageBubble } from './MessageBubble';
export { MetaBar } from './MetaBar';
export { ChatBubble } from './ChatBubble';

// Export AG-UI components
export { ConversationGrid } from './ConversationGrid';
export type { ConversationRow } from './ConversationGrid';

export { ChatAnalyticsChart } from './ChatAnalyticsChart';
export type { ChatAnalyticsData } from './ChatAnalyticsChart';

export { MemoryGrid } from './MemoryGrid';
export type { MemoryRow } from './MemoryGrid';
