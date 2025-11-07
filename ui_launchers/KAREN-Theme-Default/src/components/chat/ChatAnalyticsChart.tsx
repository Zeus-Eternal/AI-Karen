"use client";

import React from 'react';

// Temporary stub for build - original backed up as ChatAnalyticsChart.tsx.build-backup
function ChatAnalyticsChartComponent() {
  return (
    <div>
      <h2>ChatAnalyticsChart</h2>
      <p>This component is temporarily disabled for production build.</p>
    </div>
  );
}

// Type stub for ChatAnalyticsData
export interface ChatAnalyticsData {
  [key: string]: any;
}

// Export any commonly used exports to prevent import errors
export const DEFAULT_COPILOT_ACTIONS = [];
export const ChatInterface = ChatAnalyticsChartComponent;
export const AdaptiveChatInterface = ChatAnalyticsChartComponent;
export { ChatAnalyticsChartComponent as ChatAnalyticsChart };
export default ChatAnalyticsChartComponent;
