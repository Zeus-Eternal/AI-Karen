import React from 'react';

// This file contains documentation for the Chat Interface components
// It's structured as a React component to allow for easy integration with the project

export const ChatInterfaceDocumentation: React.FC = () => {
  return (
    <div className="karen-documentation">
      <h1>Chat Interface Components Documentation</h1>
      
      <section>
        <h2>Overview</h2>
        <p>
          This directory contains React components for implementing a comprehensive chat interface as part of CoPilot Architecture. 
          The components are designed to be accessible, responsive, and themeable.
        </p>
      </section>
      
      <section>
        <h2>Components</h2>
        
        <h3>1. ChatInterfaceComponent</h3>
        <p>
          The main component that integrates all chat interface functionality.
        </p>
        
        <h4>Props</h4>
        <table>
          <thead>
            <tr>
              <th>Prop</th>
              <th>Type</th>
              <th>Default</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>theme</td>
              <td>Theme</td>
              <td>defaultTheme</td>
              <td>Theme configuration for styling</td>
            </tr>
            <tr>
              <td>messages</td>
              <td>ChatMessage[]</td>
              <td>sampleMessages</td>
              <td>Array of chat messages to display</td>
            </tr>
            <tr>
              <td>conversations</td>
              <td>ConversationSession[]</td>
              <td>[]</td>
              <td>Array of conversation sessions</td>
            </tr>
            <tr>
              <td>currentConversationId</td>
              <td>string | null</td>
              <td>null</td>
              <td>ID of the currently active conversation</td>
            </tr>
            <tr>
              <td>onSendMessage</td>
              <td>(message: string, attachments?: any[]) => void</td>
              <td>-</td>
              <td>Callback when a message is sent</td>
            </tr>
            <tr>
              <td>onRetryMessage</td>
              <td>(messageId: string) => void</td>
              <td>-</td>
              <td>Callback when a message is retried</td>
            </tr>
            <tr>
              <td>onDeleteMessage</td>
              <td>(messageId: string) => void</td>
              <td>-</td>
              <td>Callback when a message is deleted</td>
            </tr>
            <tr>
              <td>onCopyMessage</td>
              <td>(messageId: string) => void</td>
              <td>-</td>
              <td>Callback when a message is copied</td>
            </tr>
            <tr>
              <td>onSelectConversation</td>
              <td>(conversation: ConversationSession) => void</td>
              <td>-</td>
              <td>Callback when a conversation is selected</td>
            </tr>
            <tr>
              <td>onDeleteConversation</td>
              <td>(conversationId: string) => void</td>
              <td>-</td>
              <td>Callback when a conversation is deleted</td>
            </tr>
            <tr>
              <td>onExportConversations</td>
              <td>(format: 'json' | 'text' | 'csv', conversationIds?: string[]) => string</td>
              <td>-</td>
              <td>Callback when conversations are exported</td>
            </tr>
            <tr>
              <td>onClearHistory</td>
              <td>() => void</td>
              <td>-</td>
              <td>Callback when conversation history is cleared</td>
            </tr>
            <tr>
              <td>onVoiceMessage</td>
              <td>(message: string) => void</td>
              <td>-</td>
              <td>Callback when a voice message is recorded</td>
            </tr>
            <tr>
              <td>onTyping</td>
              <td>(isTyping: boolean) => void</td>
              <td>-</td>
              <td>Callback when user is typing</td>
            </tr>
            <tr>
              <td>placeholder</td>
              <td>string</td>
              <td>'Type a message...'</td>
              <td>Placeholder text for the message input</td>
            </tr>
            <tr>
              <td>disabled</td>
              <td>boolean</td>
              <td>false</td>
              <td>Whether the chat interface is disabled</td>
            </tr>
            <tr>
              <td>maxLength</td>
              <td>number</td>
              <td>4000</td>
              <td>Maximum length of a message</td>
            </tr>
            <tr>
              <td>showHistory</td>
              <td>boolean</td>
              <td>true</td>
              <td>Whether to show the conversation history</td>
            </tr>
            <tr>
              <td>showVoiceInput</td>
              <td>boolean</td>
              <td>true</td>
              <td>Whether to show the voice input option</td>
            </tr>
            <tr>
              <td>showAiData</td>
              <td>boolean</td>
              <td>false</td>
              <td>Whether to show AI data in messages</td>
            </tr>
            <tr>
              <td>showConfidence</td>
              <td>boolean</td>
              <td>false</td>
              <td>Whether to show AI confidence in messages</td>
            </tr>
            <tr>
              <td>showKeywords</td>
              <td>boolean</td>
              <td>false</td>
              <td>Whether to show AI keywords in messages</td>
            </tr>
            <tr>
              <td>showReasoning</td>
              <td>boolean</td>
              <td>false</td>
              <td>Whether to show AI reasoning in messages</td>
            </tr>
            <tr>
              <td>showTimestamps</td>
              <td>boolean</td>
              <td>true</td>
              <td>Whether to show message timestamps</td>
            </tr>
            <tr>
              <td>showActions</td>
              <td>boolean</td>
              <td>true</td>
              <td>Whether to show message actions</td>
            </tr>
            <tr>
              <td>showCharacterCount</td>
              <td>boolean</td>
              <td>true</td>
              <td>Whether to show character count in input</td>
            </tr>
            <tr>
              <td>showSendButton</td>
              <td>boolean</td>
              <td>true</td>
              <td>Whether to show the send button</td>
            </tr>
            <tr>
              <td>showVoiceButton</td>
              <td>boolean</td>
              <td>true</td>
              <td>Whether to show the voice button</td>
            </tr>
            <tr>
              <td>showAttachButton</td>
              <td>boolean</td>
              <td>true</td>
              <td>Whether to show the attach button</td>
            </tr>
            <tr>
              <td>allowAttachments</td>
              <td>boolean</td>
              <td>true</td>
              <td>Whether to allow file attachments</td>
            </tr>
            <tr>
              <td>allowVoiceInput</td>
              <td>boolean</td>
              <td>true</td>
              <td>Whether to allow voice input</td>
            </tr>
            <tr>
              <td>autoFocus</td>
              <td>boolean</td>
              <td>true</td>
              <td>Whether to auto-focus the input field</td>
            </tr>
            <tr>
              <td>className</td>
              <td>string</td>
              <td>''</td>
              <td>Additional CSS classes</td>
            </tr>
          </tbody>
        </table>
        
        <h4>Usage Example</h4>
        <pre>
          {`import { ChatInterface } from './ChatInterfaceComponent';

const MyChatApp = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  
  const handleSendMessage = (message: string, attachments?: any[]) => {
    // Handle sending message
  };
  
  return (
    <ChatInterface
      messages={messages}
      onSendMessage={handleSendMessage}
      showHistory={true}
      showVoiceInput={true}
    />
  );
};`}
        </pre>
        
        <h3>2. MessageBubbleComponent</h3>
        <p>
          Component for displaying individual chat messages with various features.
        </p>
        
        <h4>Props</h4>
        <table>
          <thead>
            <tr>
              <th>Prop</th>
              <th>Type</th>
              <th>Default</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>message</td>
              <td>ChatMessage</td>
              <td>-</td>
              <td>The message to display</td>
            </tr>
            <tr>
              <td>theme</td>
              <td>Theme</td>
              <td>defaultTheme</td>
              <td>Theme configuration for styling</td>
            </tr>
            <tr>
              <td>isLast</td>
              <td>boolean</td>
              <td>false</td>
              <td>Whether this is the last message in the list</td>
            </tr>
            <tr>
              <td>onMessageAction</td>
              <td>(action: string, messageId: string) => void</td>
              <td>-</td>
              <td>Callback when a message action is triggered</td>
            </tr>
            <tr>
              <td>onCopyMessage</td>
              <td>(messageId: string) => void</td>
              <td>-</td>
              <td>Callback when a message is copied</td>
            </tr>
            <tr>
              <td>onRetryMessage</td>
              <td>(messageId: string) => void</td>
              <td>-</td>
              <td>Callback when a message is retried</td>
            </tr>
            <tr>
              <td>onDeleteMessage</td>
              <td>(messageId: string) => void</td>
              <td>-</td>
              <td>Callback when a message is deleted</td>
            </tr>
            <tr>
              <td>showTimestamp</td>
              <td>boolean</td>
              <td>true</td>
              <td>Whether to show the timestamp</td>
            </tr>
            <tr>
              <td>showActions</td>
              <td>boolean</td>
              <td>true</td>
              <td>Whether to show message actions</td>
            </tr>
            <tr>
              <td>showAiData</td>
              <td>boolean</td>
              <td>false</td>
              <td>Whether to show AI data</td>
            </tr>
            <tr>
              <td>showConfidence</td>
              <td>boolean</td>
              <td>false</td>
              <td>Whether to show AI confidence</td>
            </tr>
            <tr>
              <td>showKeywords</td>
              <td>boolean</td>
              <td>false</td>
              <td>Whether to show AI keywords</td>
            </tr>
            <tr>
              <td>showReasoning</td>
              <td>boolean</td>
              <td>false</td>
              <td>Whether to show AI reasoning</td>
            </tr>
            <tr>
              <td>className</td>
              <td>string</td>
              <td>''</td>
              <td>Additional CSS classes</td>
            </tr>
          </tbody>
        </table>
        
        <h3>3. MessageInputComponent</h3>
        <p>
          Component for handling user message input with various features.
        </p>
        
        <h4>Props</h4>
        <table>
          <thead>
            <tr>
              <th>Prop</th>
              <th>Type</th>
              <th>Default</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>theme</td>
              <td>Theme</td>
              <td>defaultTheme</td>
              <td>Theme configuration for styling</td>
            </tr>
            <tr>
              <td>onSendMessage</td>
              <td>(message: string, attachments?: any[]) => void</td>
              <td>-</td>
              <td>Callback when a message is sent</td>
            </tr>
            <tr>
              <td>onVoiceInput</td>
              <td>() => void</td>
              <td>-</td>
              <td>Callback when voice input is triggered</td>
            </tr>
            <tr>
              <td>onAttachFile</td>
              <td>(files: File[]) => void</td>
              <td>-</td>
              <td>Callback when files are attached</td>
            </tr>
            <tr>
              <td>onTyping</td>
              <td>(isTyping: boolean) => void</td>
              <td>-</td>
              <td>Callback when user is typing</td>
            </tr>
            <tr>
              <td>placeholder</td>
              <td>string</td>
              <td>'Type a message...'</td>
              <td>Placeholder text for the input</td>
            </tr>
            <tr>
              <td>disabled</td>
              <td>boolean</td>
              <td>false</td>
              <td>Whether the input is disabled</td>
            </tr>
            <tr>
              <td>maxLength</td>
              <td>number</td>
              <td>4000</td>
              <td>Maximum length of a message</td>
            </tr>
            <tr>
              <td>showCharacterCount</td>
              <td>boolean</td>
              <td>true</td>
              <td>Whether to show character count</td>
            </tr>
            <tr>
              <td>showSendButton</td>
              <td>boolean</td>
              <td>true</td>
              <td>Whether to show the send button</td>
            </tr>
            <tr>
              <td>showVoiceButton</td>
              <td>boolean</td>
              <td>true</td>
              <td>Whether to show the voice button</td>
            </tr>
            <tr>
              <td>showAttachButton</td>
              <td>boolean</td>
              <td>true</td>
              <td>Whether to show the attach button</td>
            </tr>
            <tr>
              <td>allowAttachments</td>
              <td>boolean</td>
              <td>true</td>
              <td>Whether to allow file attachments</td>
            </tr>
            <tr>
              <td>allowVoiceInput</td>
              <td>boolean</td>
              <td>true</td>
              <td>Whether to allow voice input</td>
            </tr>
            <tr>
              <td>autoFocus</td>
              <td>boolean</td>
              <td>true</td>
              <td>Whether to auto-focus the input</td>
            </tr>
            <tr>
              <td>initialValue</td>
              <td>string</td>
              <td>''</td>
              <td>Initial value for the input</td>
            </tr>
            <tr>
              <td>className</td>
              <td>string</td>
              <td>''</td>
              <td>Additional CSS classes</td>
            </tr>
          </tbody>
        </table>
        
        <h3>4. ConversationHistoryComponent</h3>
        <p>
          Component for displaying and managing conversation history.
        </p>
        
        <h4>Props</h4>
        <table>
          <thead>
            <tr>
              <th>Prop</th>
              <th>Type</th>
              <th>Default</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>theme</td>
              <td>Theme</td>
              <td>defaultTheme</td>
              <td>Theme configuration for styling</td>
            </tr>
            <tr>
              <td>conversations</td>
              <td>ConversationSession[]</td>
              <td>[]</td>
              <td>Array of conversation sessions</td>
            </tr>
            <tr>
              <td>currentConversationId</td>
              <td>string | null</td>
              <td>null</td>
              <td>ID of the currently active conversation</td>
            </tr>
            <tr>
              <td>onSelectConversation</td>
              <td>(conversation: ConversationSession) => void</td>
              <td>-</td>
              <td>Callback when a conversation is selected</td>
            </tr>
            <tr>
              <td>onDeleteConversation</td>
              <td>(conversationId: string) => void</td>
              <td>-</td>
              <td>Callback when a conversation is deleted</td>
            </tr>
            <tr>
              <td>onExportConversations</td>
              <td>(format: 'json' | 'text' | 'csv', conversationIds?: string[]) => string</td>
              <td>-</td>
              <td>Callback when conversations are exported</td>
            </tr>
            <tr>
              <td>onClearHistory</td>
              <td>() => void</td>
              <td>-</td>
              <td>Callback when conversation history is cleared</td>
            </tr>
            <tr>
              <td>className</td>
              <td>string</td>
              <td>''</td>
              <td>Additional CSS classes</td>
            </tr>
          </tbody>
        </table>
        
        <h3>5. VoiceRecorderComponent</h3>
        <p>
          Component for recording voice input using the Web Speech API.
        </p>
        
        <h4>Props</h4>
        <table>
          <thead>
            <tr>
              <th>Prop</th>
              <th>Type</th>
              <th>Default</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>theme</td>
              <td>Theme</td>
              <td>defaultTheme</td>
              <td>Theme configuration for styling</td>
            </tr>
            <tr>
              <td>onRecordingComplete</td>
              <td>(message: string) => void</td>
              <td>-</td>
              <td>Callback when recording is complete</td>
            </tr>
            <tr>
              <td>isRecording</td>
              <td>boolean</td>
              <td>false</td>
              <td>Whether recording is in progress</td>
            </tr>
            <tr>
              <td>onRecordingStart</td>
              <td>() => void</td>
              <td>-</td>
              <td>Callback when recording starts</td>
            </tr>
            <tr>
              <td>onRecordingEnd</td>
              <td>() => void</td>
              <td>-</td>
              <td>Callback when recording ends</td>
            </tr>
            <tr>
              <td>className</td>
              <td>string</td>
              <td>''</td>
              <td>Additional CSS classes</td>
            </tr>
          </tbody>
        </table>
        
        <h3>6. AccessibilityEnhancements</h3>
        <p>
          Component for adding accessibility features to the chat interface.
        </p>
        
        <h4>Props</h4>
        <table>
          <thead>
            <tr>
              <th>Prop</th>
              <th>Type</th>
              <th>Default</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>theme</td>
              <td>Theme</td>
              <td>defaultTheme</td>
              <td>Theme configuration for styling</td>
            </tr>
            <tr>
              <td>announcements</td>
              <td>AccessibilityAnnouncement[]</td>
              <td>[]</td>
              <td>Array of announcements for screen readers</td>
            </tr>
            <tr>
              <td>onAnnouncementComplete</td>
              <td>(announcement: AccessibilityAnnouncement) => void</td>
              <td>-</td>
              <td>Callback when an announcement is complete</td>
            </tr>
            <tr>
              <td>onKeyboardShortcut</td>
              <td>(shortcut: string) => void</td>
              <td>-</td>
              <td>Callback when a keyboard shortcut is triggered</td>
            </tr>
            <tr>
              <td>children</td>
              <td>ReactNode</td>
              <td>-</td>
              <td>Child components</td>
            </tr>
            <tr>
              <td>className</td>
              <td>string</td>
              <td>''</td>
              <td>Additional CSS classes</td>
            </tr>
          </tbody>
        </table>
        
        <h3>7. ResponsiveDesign</h3>
        <p>
          Component for making the chat interface responsive across different screen sizes.
        </p>
        
        <h4>Props</h4>
        <table>
          <thead>
            <tr>
              <th>Prop</th>
              <th>Type</th>
              <th>Default</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>theme</td>
              <td>Theme</td>
              <td>defaultTheme</td>
              <td>Theme configuration for styling</td>
            </tr>
            <tr>
              <td>breakpoints</td>
              <td>Breakpoints</td>
              <td>defaultBreakpoints</td>
              <td>Breakpoints for responsive design</td>
            </tr>
            <tr>
              <td>children</td>
              <td>ReactNode</td>
              <td>-</td>
              <td>Child components</td>
            </tr>
            <tr>
              <td>className</td>
              <td>string</td>
              <td>''</td>
              <td>Additional CSS classes</td>
            </tr>
          </tbody>
        </table>
        
        <h3>8. ThemeManagement</h3>
        <p>
          Component for managing themes in the chat interface.
        </p>
        
        <h4>Props</h4>
        <table>
          <thead>
            <tr>
              <th>Prop</th>
              <th>Type</th>
              <th>Default</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>children</td>
              <td>ReactNode</td>
              <td>-</td>
              <td>Child components</td>
            </tr>
            <tr>
              <td>defaultThemeId</td>
              <td>string</td>
              <td>'light'</td>
              <td>ID of the default theme</td>
            </tr>
            <tr>
              <td>customThemes</td>
              <td>Theme[]</td>
              <td>[]</td>
              <td>Array of custom themes</td>
            </tr>
          </tbody>
        </table>
        
        <h3>9. ChatInterfaceDemo</h3>
        <p>
          Demo component that showcases all the chat interface components.
        </p>
        
        <h4>Usage</h4>
        <pre>
          {`import { ChatInterfaceDemoApp } from './ChatInterfaceDemo';

const App = () => {
  return <ChatInterfaceDemoApp />;
};`}
        </pre>
      </section>
      
      <section>
        <h2>Type Definitions</h2>
        
        <h3>Theme</h3>
        <pre>
          {`interface Theme {
  id: string;
  name: string;
  colors: {
    primary: string;
    secondary: string;
    background: string;
    surface: string;
    text: string;
    textSecondary: string;
    border: string;
    error: string;
    warning: string;
    success: string;
    info: string;
  };
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
    xxl: string;
  };
  typography: {
    fontFamily: string;
    fontSize: {
      xs: string;
      sm: string;
      base: string;
      lg: string;
      xl: string;
      xxl: string;
    };
    fontWeight: {
      light: number;
      normal: number;
      medium: number;
      semibold: number;
      bold: number;
    };
  };
  borderRadius: string;
  shadows: {
    sm: string;
    md: string;
    lg: string;
  };
  isDark?: boolean;
}`}
        </pre>
        
        <h3>ChatMessage</h3>
        <pre>
          {`interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  aiData?: {
    keywords?: string[];
    knowledgeGraphInsights?: string;
    confidence?: number;
    reasoning?: string;
  };
  shouldAutoPlay?: boolean;
  attachments?: Array<{
    id: string;
    name: string;
    size: string;
    type: string;
    url?: string;
  }>;
}`}
        </pre>
        
        <h3>ConversationSession</h3>
        <pre>
          {`interface ConversationSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: Date;
  updatedAt: Date;
  messageCount: number;
  summary?: string;
  tags?: string[];
}`}
        </pre>
      </section>
      
      <section>
        <h2>Accessibility Features</h2>
        <p>
          The chat interface components include several accessibility features:
        </p>
        <ul>
          <li>ARIA labels and roles for screen readers</li>
          <li>Keyboard navigation support</li>
          <li>Screen reader announcements</li>
          <li>Focus management</li>
          <li>Keyboard shortcuts</li>
          <li>Skip to content links</li>
        </ul>
        
        <h3>Keyboard Shortcuts</h3>
        <table>
          <thead>
            <tr>
              <th>Shortcut</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>/</td>
              <td>Focus on message input</td>
            </tr>
            <tr>
              <td>Ctrl + H</td>
              <td>Toggle conversation history</td>
            </tr>
            <tr>
              <td>Ctrl + V</td>
              <td>Toggle voice input</td>
            </tr>
            <tr>
              <td>Escape</td>
              <td>Close modals or cancel actions</td>
            </tr>
            <tr>
              <td>Arrow Up</td>
              <td>Navigate to previous message</td>
            </tr>
            <tr>
              <td>Arrow Down</td>
              <td>Navigate to next message</td>
            </tr>
            <tr>
              <td>Enter</td>
              <td>Send message</td>
            </tr>
            <tr>
              <td>Shift + Enter</td>
              <td>Add new line to message</td>
            </tr>
          </tbody>
        </table>
      </section>
      
      <section>
        <h2>Responsive Design</h2>
        <p>
          The chat interface components are designed to be responsive across different screen sizes:
        </p>
        <ul>
          <li>Mobile: Less than 600px</li>
          <li>Tablet: 600px to 960px</li>
          <li>Desktop: 960px and above</li>
        </ul>
        
        <p>
          The responsive design includes:
        </p>
        <ul>
          <li>Responsive layouts</li>
          <li>Responsive sidebars</li>
          <li>Responsive grids</li>
          <li>Responsive text</li>
          <li>Responsive containers</li>
          <li>Responsive flex</li>
        </ul>
      </section>
      
      <section>
        <h2>Theme Support</h2>
        <p>
          The chat interface components support multiple themes:
        </p>
        <ul>
          <li>Light theme (default)</li>
          <li>Dark theme</li>
          <li>High contrast theme</li>
          <li>Blue theme</li>
          <li>Custom themes</li>
        </ul>
        
        <p>
          Theme features include:
        </p>
        <ul>
          <li>Theme switching</li>
          <li>Theme customization</li>
          <li>Dark mode support</li>
          <li>Theme persistence</li>
        </ul>
      </section>
      
      <section>
        <h2>Browser Support</h2>
        <p>
          The chat interface components support the following browsers:
        </p>
        <ul>
          <li>Chrome (latest)</li>
          <li>Firefox (latest)</li>
          <li>Safari (latest)</li>
          <li>Edge (latest)</li>
        </ul>
        
        <p>
          Note: Voice input requires a browser that supports the Web Speech API.
        </p>
      </section>
      
      <section>
        <h2>Contributing</h2>
        <p>
          When contributing to the chat interface components, please follow these guidelines:
        </p>
        <ul>
          <li>Follow the existing code style</li>
          <li>Add TypeScript types for all props</li>
          <li>Ensure accessibility compliance</li>
          <li>Test on different screen sizes</li>
          <li>Test with different themes</li>
          <li>Add documentation for new features</li>
        </ul>
      </section>
    </div>
  );
};

export default ChatInterfaceDocumentation;