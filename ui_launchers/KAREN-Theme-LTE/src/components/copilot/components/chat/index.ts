// Main Chat Interface component
import { ChatInterface as DefaultChatInterface } from './ChatInterface';
export { ChatInterface } from './ChatInterface';

// Sub-components
export { MessageBubbleComponent } from './MessageBubbleComponent';
export { MessageInputComponent } from './MessageInputComponent';
export { VoiceRecorderComponent } from './VoiceRecorderComponent';
export { ConversationHistoryComponent } from './ConversationHistoryComponent';
export { MessageSearchComponent } from './MessageSearchComponent';

// Theme provider and hook
export { ThemeProvider, useTheme, ThemeToggle } from './ThemeProvider';

// Type definitions
export type { Theme, ChatMessage, Conversation } from './types';

// Default exports
export default DefaultChatInterface;