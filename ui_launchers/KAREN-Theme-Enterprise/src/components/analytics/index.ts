// Enhanced Analytics Components with AG-UI Integration
export { EnhancedAnalyticsChart } from './EnhancedAnalyticsChart';
export type { EnhancedAnalyticsData, AnalyticsStats } from './EnhancedAnalyticsChart';

export { MemoryNetworkVisualization } from './MemoryNetworkVisualization';
export type { MemoryNode, MemoryEdge, MemoryNetworkData } from './MemoryNetworkVisualization';

export { UserEngagementGrid } from './UserEngagementGrid';
export type { UserEngagementRow } from './UserEngagementGrid';

// Re-export existing chat analytics for backward compatibility
// Note: ChatAnalyticsChart doesn't exist yet - commented out to prevent compilation errors
// export { ChatAnalyticsChart } from '../chat/ChatAnalyticsChart';
// export type { ChatAnalyticsData } from '../chat/ChatAnalyticsChart';

// MemoryGrid is in the memory directory, not chat
export { MemoryGrid } from '../memory/MemoryGrid';
export type { MemoryGridRow as MemoryRow } from '../memory/MemoryGrid';
