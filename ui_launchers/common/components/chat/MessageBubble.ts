// Shared Message Bubble Component
// Framework-agnostic message display component

import { ChatMessage, Theme, AiData } from '../../abstractions/types';
import { formatRelativeTime, truncateText, parseMarkdown } from '../../abstractions/utils';

export interface MessageBubbleOptions {
  showTimestamp?: boolean;
  showAiData?: boolean;
  enableTts?: boolean;
  maxContentLength?: number;
  enableMarkdown?: boolean;
  showAvatar?: boolean;
  compactMode?: boolean;
}

export interface MessageBubbleData {
  message: ChatMessage;
  theme: Theme;
  options: MessageBubbleOptions;
  isPlaying?: boolean;
  onPlayAudio?: () => void;
  onStopAudio?: () => void;
}

export class SharedMessageBubble {
  private data: MessageBubbleData;

  constructor(data: MessageBubbleData) {
    this.data = {
      options: {
        showTimestamp: true,
        showAiData: true,
        enableTts: true,
        maxContentLength: 0, // 0 means no limit
        enableMarkdown: true,
        showAvatar: true,
        compactMode: false
      },
      ...data
    };
  }

  // Get the CSS classes for the message bubble
  getCssClasses(): string[] {
    const { message, options } = this.data;
    const classes = ['karen-message'];
    
    classes.push(`karen-message-${message.role}`);
    
    if (options.compactMode) {
      classes.push('karen-message-compact');
    }
    
    if (message.role === 'system') {
      classes.push('karen-message-system');
    }
    
    return classes;
  }

  // Get the formatted content
  getFormattedContent(): string {
    let content = this.data.message.content;
    
    // Truncate if needed
    if (this.data.options.maxContentLength && content.length > this.data.options.maxContentLength) {
      content = truncateText(content, this.data.options.maxContentLength);
    }
    
    // Parse markdown if enabled
    if (this.data.options.enableMarkdown) {
      content = parseMarkdown(content);
    }
    
    return content;
  }

  // Get the formatted timestamp
  getFormattedTimestamp(): string {
    if (!this.data.options.showTimestamp) return '';
    
    return formatRelativeTime(this.data.message.timestamp);
  }

  // Get AI data for display
  getAiDataDisplay(): AiDataDisplay | null {
    if (!this.data.options.showAiData || !this.data.message.aiData) {
      return null;
    }

    const aiData = this.data.message.aiData;
    return {
      hasKeywords: !!(aiData.keywords && aiData.keywords.length > 0),
      keywords: aiData.keywords || [],
      hasInsights: !!aiData.knowledgeGraphInsights,
      insights: aiData.knowledgeGraphInsights || '',
      confidence: aiData.confidence,
      reasoning: aiData.reasoning
    };
  }

  // Get avatar information
  getAvatarInfo(): AvatarInfo {
    const { message } = this.data;
    
    return {
      show: this.data.options.showAvatar,
      type: message.role === 'user' ? 'user' : 'assistant',
      icon: message.role === 'user' ? 'user' : 'bot',
      alt: message.role === 'user' ? 'User' : 'AI Karen'
    };
  }

  // Get TTS button information
  getTtsInfo(): TtsInfo | null {
    if (!this.data.options.enableTts || this.data.message.role === 'user') {
      return null;
    }

    return {
      enabled: true,
      isPlaying: this.data.isPlaying || false,
      canPlay: !!this.data.onPlayAudio,
      canStop: !!this.data.onStopAudio,
      label: this.data.isPlaying ? 'Stop audio' : 'Play audio'
    };
  }

  // Get message metadata
  getMetadata(): MessageMetadata {
    const { message } = this.data;
    
    return {
      id: message.id,
      role: message.role,
      timestamp: message.timestamp,
      hasAttachments: !!(message.attachments && message.attachments.length > 0),
      attachmentCount: message.attachments?.length || 0,
      shouldAutoPlay: message.shouldAutoPlay || false,
      contentLength: message.content.length
    };
  }

  // Generate inline styles based on theme
  getInlineStyles(): Record<string, string> {
    const { theme, message } = this.data;
    const isUser = message.role === 'user';
    
    return {
      backgroundColor: isUser ? theme.colors.primary : theme.colors.surface,
      color: isUser ? '#ffffff' : theme.colors.text,
      borderColor: theme.colors.border,
      borderRadius: theme.borderRadius,
      padding: theme.spacing.md,
      margin: `${theme.spacing.sm} 0`,
      fontFamily: theme.typography.fontFamily,
      fontSize: theme.typography.fontSize.base,
      boxShadow: theme.shadows.sm
    };
  }

  // Generate framework-specific render data
  getRenderData(): MessageRenderData {
    return {
      cssClasses: this.getCssClasses(),
      content: this.getFormattedContent(),
      timestamp: this.getFormattedTimestamp(),
      aiData: this.getAiDataDisplay(),
      avatar: this.getAvatarInfo(),
      tts: this.getTtsInfo(),
      metadata: this.getMetadata(),
      styles: this.getInlineStyles(),
      theme: this.data.theme
    };
  }

  // Update the message data
  updateData(newData: Partial<MessageBubbleData>): void {
    this.data = { ...this.data, ...newData };
  }

  // Handle TTS play action
  handlePlayAudio(): void {
    if (this.data.onPlayAudio) {
      this.data.onPlayAudio();
    }
  }

  // Handle TTS stop action
  handleStopAudio(): void {
    if (this.data.onStopAudio) {
      this.data.onStopAudio();
    }
  }
}

// Supporting interfaces
export interface AiDataDisplay {
  hasKeywords: boolean;
  keywords: string[];
  hasInsights: boolean;
  insights: string;
  confidence?: number;
  reasoning?: string;
}

export interface AvatarInfo {
  show: boolean;
  type: 'user' | 'assistant';
  icon: string;
  alt: string;
}

export interface TtsInfo {
  enabled: boolean;
  isPlaying: boolean;
  canPlay: boolean;
  canStop: boolean;
  label: string;
}

export interface MessageMetadata {
  id: string;
  role: string;
  timestamp: Date;
  hasAttachments: boolean;
  attachmentCount: number;
  shouldAutoPlay: boolean;
  contentLength: number;
}

export interface MessageRenderData {
  cssClasses: string[];
  content: string;
  timestamp: string;
  aiData: AiDataDisplay | null;
  avatar: AvatarInfo;
  tts: TtsInfo | null;
  metadata: MessageMetadata;
  styles: Record<string, string>;
  theme: Theme;
}

// Utility functions for message rendering
export function createMessageBubble(
  message: ChatMessage,
  theme: Theme,
  options: Partial<MessageBubbleOptions> = {}
): SharedMessageBubble {
  return new SharedMessageBubble({
    message,
    theme,
    options: { ...options }
  });
}

export function formatMessageForExport(message: ChatMessage, format: 'text' | 'html' | 'markdown'): string {
  const role = message.role === 'user' ? 'You' : 'AI Karen';
  const timestamp = message.timestamp.toLocaleString();
  const content = message.content;

  switch (format) {
    case 'html':
      return `
        <div class="message message-${message.role}">
          <div class="message-header">
            <strong>${role}</strong>
            <span class="timestamp">${timestamp}</span>
          </div>
          <div class="message-content">${parseMarkdown(content)}</div>
          ${message.aiData ? `<div class="ai-data">${JSON.stringify(message.aiData, null, 2)}</div>` : ''}
        </div>
      `;
    
    case 'markdown':
      return `
**${role}** _(${timestamp})_

${content}

${message.aiData ? `\`\`\`json\n${JSON.stringify(message.aiData, null, 2)}\n\`\`\`` : ''}

---
      `;
    
    case 'text':
    default:
      return `[${timestamp}] ${role}: ${content}\n`;
  }
}

export function getMessageSummary(message: ChatMessage): string {
  const preview = truncateText(message.content, 100);
  const role = message.role === 'user' ? 'You' : 'Karen';
  const time = formatRelativeTime(message.timestamp);
  
  return `${role} (${time}): ${preview}`;
}

export function groupMessagesByDate(messages: ChatMessage[]): Record<string, ChatMessage[]> {
  const groups: Record<string, ChatMessage[]> = {};
  
  messages.forEach(message => {
    const dateKey = message.timestamp.toDateString();
    if (!groups[dateKey]) {
      groups[dateKey] = [];
    }
    groups[dateKey].push(message);
  });
  
  return groups;
}

export function findMessageById(messages: ChatMessage[], id: string): ChatMessage | null {
  return messages.find(message => message.id === id) || null;
}

export function getMessageStats(messages: ChatMessage[]): {
  total: number;
  byRole: Record<string, number>;
  averageLength: number;
  totalLength: number;
} {
  const byRole: Record<string, number> = {};
  let totalLength = 0;
  
  messages.forEach(message => {
    byRole[message.role] = (byRole[message.role] || 0) + 1;
    totalLength += message.content.length;
  });
  
  return {
    total: messages.length,
    byRole,
    averageLength: messages.length > 0 ? Math.round(totalLength / messages.length) : 0,
    totalLength
  };
}