export { ChatInterface } from "@/components/ChatInterface";
export { CopilotChat } from "./copilot";

// Export supporting components
export { MessageBubble } from "./MessageBubble";
export { MetaBar } from "./MetaBar";
export { ChatBubble } from "./ChatBubble";
export { default as ModelSelector } from "./ModelSelector";
export { default as EnhancedModelSelector } from "./EnhancedModelSelector";

// Export adaptive chat components
// NOTE: AdaptiveChatInterface is currently disabled (.broken file)
// export { default as AdaptiveChatInterface } from "./AdaptiveChatInterface";
export { default as ImageGenerationControls } from "./ImageGenerationControls";
export { default as ChatModeSelector } from "./ChatModeSelector";

// Export copilot components
export { default as CopilotActions } from "./CopilotActions";
export { default as CopilotArtifacts } from "./CopilotArtifacts";
export { default as EnhancedMessageBubble } from "./EnhancedMessageBubble";

// Export types from ChatInterface
export type { CopilotAction, ChatContext, CopilotArtifact } from "@/components/ChatInterface/types";

// Export AG-UI components
export { ConversationGrid } from "./ConversationGrid";
export type { ConversationSummaryRow } from "@/types/chat-ui";

export { ChatAnalyticsChart } from "./ChatAnalyticsChart";
export type { ChatAnalyticsData } from "./ChatAnalyticsChart";

export { MemoryGrid } from "./MemoryGrid";
export type { MemoryRow } from "./MemoryGrid";
