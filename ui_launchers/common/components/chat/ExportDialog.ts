// Shared Export Dialog Component
// Framework-agnostic conversation export functionality

import { ChatMessage, Theme } from '../../abstractions/types';
import { formatTimestamp } from '../../abstractions/utils';

export interface ExportOptions {
  format: 'text' | 'json' | 'html' | 'csv' | 'markdown';
  includeTimestamps: boolean;
  includeAiData: boolean;
  includeSystemMessages: boolean;
  dateRange?: {
    start: Date;
    end: Date;
  };
  messageRoles?: ('user' | 'assistant' | 'system')[];
}

export interface ExportDialogState {
  isOpen: boolean;
  isExporting: boolean;
  options: ExportOptions;
  previewContent: string;
  exportedContent: string;
  fileName: string;
  fileSize: number;
  messageCount: number;
}

export interface ExportDialogCallbacks {
  onExport?: (content: string, options: ExportOptions) => void;
  onDownload?: (content: string, fileName: string, mimeType: string) => void;
  onClose?: () => void;
}

export class SharedExportDialog {
  private state: ExportDialogState;
  private callbacks: ExportDialogCallbacks;
  private theme: Theme;
  private messages: ChatMessage[];

  constructor(
    messages: ChatMessage[],
    theme: Theme,
    callbacks: ExportDialogCallbacks = {}
  ) {
    this.messages = messages;
    this.theme = theme;
    this.callbacks = callbacks;

    this.state = {
      isOpen: false,
      isExporting: false,
      options: {
        format: 'text',
        includeTimestamps: true,
        includeAiData: false,
        includeSystemMessages: false,
        messageRoles: ['user', 'assistant']
      },
      previewContent: '',
      exportedContent: '',
      fileName: this.generateFileName('text'),
      fileSize: 0,
      messageCount: 0
    };
  }

  // Get current state
  getState(): ExportDialogState {
    return { ...this.state };
  }

  // Update state
  updateState(newState: Partial<ExportDialogState>): void {
    this.state = { ...this.state, ...newState };
  }

  // Open the export dialog
  open(): void {
    this.updateState({ isOpen: true });
    this.updatePreview();
  }

  // Close the export dialog
  close(): void {
    this.updateState({ 
      isOpen: false,
      exportedContent: '',
      previewContent: ''
    });

    if (this.callbacks.onClose) {
      this.callbacks.onClose();
    }
  }

  // Update export options
  updateOptions(newOptions: Partial<ExportOptions>): void {
    const options = { ...this.state.options, ...newOptions };
    const fileName = this.generateFileName(options.format);
    
    this.updateState({ 
      options,
      fileName
    });
    
    this.updatePreview();
  }

  // Update preview content
  private updatePreview(): void {
    const filteredMessages = this.filterMessages();
    const previewMessages = filteredMessages.slice(0, 5); // Show first 5 messages in preview
    const previewContent = this.generateContent(previewMessages, true);
    
    this.updateState({
      previewContent,
      messageCount: filteredMessages.length
    });
  }

  // Filter messages based on options
  private filterMessages(): ChatMessage[] {
    let filtered = [...this.messages];

    // Filter by roles
    if (this.state.options.messageRoles && this.state.options.messageRoles.length > 0) {
      filtered = filtered.filter(msg => this.state.options.messageRoles!.includes(msg.role));
    }

    // Filter system messages
    if (!this.state.options.includeSystemMessages) {
      filtered = filtered.filter(msg => msg.role !== 'system');
    }

    // Filter by date range
    if (this.state.options.dateRange) {
      const { start, end } = this.state.options.dateRange;
      filtered = filtered.filter(msg => 
        msg.timestamp >= start && msg.timestamp <= end
      );
    }

    return filtered;
  }

  // Generate export content
  private generateContent(messages: ChatMessage[], isPreview: boolean = false): string {
    const { format } = this.state.options;

    switch (format) {
      case 'json':
        return this.generateJsonContent(messages, isPreview);
      case 'html':
        return this.generateHtmlContent(messages, isPreview);
      case 'csv':
        return this.generateCsvContent(messages, isPreview);
      case 'markdown':
        return this.generateMarkdownContent(messages, isPreview);
      case 'text':
      default:
        return this.generateTextContent(messages, isPreview);
    }
  }

  // Generate text format
  private generateTextContent(messages: ChatMessage[], isPreview: boolean): string {
    let content = 'AI Karen Conversation Export\n';
    content += '='.repeat(50) + '\n';
    content += `Export Date: ${new Date().toLocaleString()}\n`;
    content += `Total Messages: ${this.state.messageCount}\n`;
    content += `Format: Plain Text\n\n`;

    if (isPreview && messages.length < this.state.messageCount) {
      content += `Showing first ${messages.length} of ${this.state.messageCount} messages\n\n`;
    }

    messages.forEach(msg => {
      const role = this.getRoleDisplayName(msg.role);
      let line = '';

      if (this.state.options.includeTimestamps) {
        line += `[${formatTimestamp(msg.timestamp)}] `;
      }

      line += `${role}: ${msg.content}`;

      if (this.state.options.includeAiData && msg.aiData) {
        if (msg.aiData.keywords && msg.aiData.keywords.length > 0) {
          line += `\n  Keywords: ${msg.aiData.keywords.join(', ')}`;
        }
        if (msg.aiData.knowledgeGraphInsights) {
          line += `\n  Insights: ${msg.aiData.knowledgeGraphInsights}`;
        }
        if (msg.aiData.confidence) {
          line += `\n  Confidence: ${(msg.aiData.confidence * 100).toFixed(1)}%`;
        }
      }

      content += line + '\n\n';
    });

    return content;
  }

  // Generate JSON format
  private generateJsonContent(messages: ChatMessage[], isPreview: boolean): string {
    const exportData = {
      exportInfo: {
        exportDate: new Date().toISOString(),
        totalMessages: this.state.messageCount,
        format: 'JSON',
        options: this.state.options,
        isPreview
      },
      messages: messages.map(msg => ({
        id: msg.id,
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp.toISOString(),
        ...(this.state.options.includeAiData && msg.aiData ? { aiData: msg.aiData } : {}),
        ...(msg.attachments ? { attachments: msg.attachments } : {})
      }))
    };

    return JSON.stringify(exportData, null, 2);
  }

  // Generate HTML format
  private generateHtmlContent(messages: ChatMessage[], isPreview: boolean): string {
    let html = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Karen Conversation Export</title>
    <style>
        body { 
            font-family: ${this.theme.typography.fontFamily}; 
            background-color: ${this.theme.colors.background};
            color: ${this.theme.colors.text};
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .header { 
            border-bottom: 2px solid ${this.theme.colors.border}; 
            padding-bottom: 20px; 
            margin-bottom: 30px; 
        }
        .message { 
            margin: 20px 0; 
            padding: 15px; 
            border-radius: ${this.theme.borderRadius}; 
            border-left: 4px solid ${this.theme.colors.primary};
        }
        .message.user { 
            background-color: ${this.theme.colors.primary}; 
            color: white; 
            border-left-color: ${this.theme.colors.secondary};
        }
        .message.assistant { 
            background-color: ${this.theme.colors.surface}; 
            border-left-color: ${this.theme.colors.primary};
        }
        .message.system { 
            background-color: ${this.theme.colors.surface}; 
            border-left-color: ${this.theme.colors.warning};
            font-style: italic;
        }
        .message-header { 
            font-weight: bold; 
            margin-bottom: 10px; 
            display: flex; 
            justify-content: space-between; 
        }
        .timestamp { 
            font-size: 0.9em; 
            opacity: 0.8; 
        }
        .ai-data { 
            margin-top: 15px; 
            padding: 10px; 
            background-color: rgba(0,0,0,0.1); 
            border-radius: 4px; 
            font-size: 0.9em; 
        }
        .keywords { 
            margin: 5px 0; 
        }
        .keyword { 
            display: inline-block; 
            background-color: ${this.theme.colors.secondary}; 
            color: white; 
            padding: 2px 6px; 
            border-radius: 3px; 
            margin: 2px; 
            font-size: 0.8em; 
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>AI Karen Conversation Export</h1>
        <p><strong>Export Date:</strong> ${new Date().toLocaleString()}</p>
        <p><strong>Total Messages:</strong> ${this.state.messageCount}</p>
        <p><strong>Format:</strong> HTML</p>
        ${isPreview ? `<p><em>Preview showing first ${messages.length} messages</em></p>` : ''}
    </div>
    <div class="messages">
`;

    messages.forEach(msg => {
      const role = this.getRoleDisplayName(msg.role);
      html += `
        <div class="message ${msg.role}">
            <div class="message-header">
                <span class="role">${role}</span>
                ${this.state.options.includeTimestamps ? `<span class="timestamp">${formatTimestamp(msg.timestamp)}</span>` : ''}
            </div>
            <div class="content">${this.escapeHtml(msg.content)}</div>
`;

      if (this.state.options.includeAiData && msg.aiData) {
        html += `<div class="ai-data">`;
        
        if (msg.aiData.keywords && msg.aiData.keywords.length > 0) {
          html += `<div class="keywords"><strong>Keywords:</strong> `;
          msg.aiData.keywords.forEach(keyword => {
            html += `<span class="keyword">${this.escapeHtml(keyword)}</span>`;
          });
          html += `</div>`;
        }
        
        if (msg.aiData.knowledgeGraphInsights) {
          html += `<div><strong>Insights:</strong> ${this.escapeHtml(msg.aiData.knowledgeGraphInsights)}</div>`;
        }
        
        if (msg.aiData.confidence) {
          html += `<div><strong>Confidence:</strong> ${(msg.aiData.confidence * 100).toFixed(1)}%</div>`;
        }
        
        html += `</div>`;
      }

      html += `</div>`;
    });

    html += `
    </div>
</body>
</html>`;

    return html;
  }

  // Generate CSV format
  private generateCsvContent(messages: ChatMessage[], isPreview: boolean): string {
    const headers = ['Role', 'Content', 'Timestamp'];
    
    if (this.state.options.includeAiData) {
      headers.push('Keywords', 'Insights', 'Confidence');
    }

    let csv = headers.join(',') + '\n';

    messages.forEach(msg => {
      const row = [
        msg.role,
        `"${msg.content.replace(/"/g, '""')}"`,
        this.state.options.includeTimestamps ? msg.timestamp.toISOString() : ''
      ];

      if (this.state.options.includeAiData) {
        row.push(
          msg.aiData?.keywords ? `"${msg.aiData.keywords.join(', ')}"` : '',
          msg.aiData?.knowledgeGraphInsights ? `"${msg.aiData.knowledgeGraphInsights.replace(/"/g, '""')}"` : '',
          msg.aiData?.confidence ? msg.aiData.confidence.toString() : ''
        );
      }

      csv += row.join(',') + '\n';
    });

    return csv;
  }

  // Generate Markdown format
  private generateMarkdownContent(messages: ChatMessage[], isPreview: boolean): string {
    let content = '# AI Karen Conversation Export\n\n';
    content += `**Export Date:** ${new Date().toLocaleString()}\n`;
    content += `**Total Messages:** ${this.state.messageCount}\n`;
    content += `**Format:** Markdown\n\n`;

    if (isPreview && messages.length < this.state.messageCount) {
      content += `*Showing first ${messages.length} of ${this.state.messageCount} messages*\n\n`;
    }

    content += '---\n\n';

    messages.forEach(msg => {
      const role = this.getRoleDisplayName(msg.role);
      
      content += `## ${role}`;
      
      if (this.state.options.includeTimestamps) {
        content += ` _(${formatTimestamp(msg.timestamp)})_`;
      }
      
      content += '\n\n';
      content += `${msg.content}\n\n`;

      if (this.state.options.includeAiData && msg.aiData) {
        if (msg.aiData.keywords && msg.aiData.keywords.length > 0) {
          content += `**Keywords:** ${msg.aiData.keywords.map(k => `\`${k}\``).join(', ')}\n\n`;
        }
        
        if (msg.aiData.knowledgeGraphInsights) {
          content += `**Insights:** ${msg.aiData.knowledgeGraphInsights}\n\n`;
        }
        
        if (msg.aiData.confidence) {
          content += `**Confidence:** ${(msg.aiData.confidence * 100).toFixed(1)}%\n\n`;
        }
      }

      content += '---\n\n';
    });

    return content;
  }

  // Perform the export
  async performExport(): Promise<void> {
    this.updateState({ isExporting: true });

    try {
      const filteredMessages = this.filterMessages();
      const content = this.generateContent(filteredMessages);
      const fileSize = new Blob([content]).size;

      this.updateState({
        exportedContent: content,
        fileSize,
        isExporting: false
      });

      if (this.callbacks.onExport) {
        this.callbacks.onExport(content, this.state.options);
      }

    } catch (error) {
      console.error('Export failed:', error);
      this.updateState({ isExporting: false });
      throw error;
    }
  }

  // Download the exported content
  downloadExport(): void {
    if (!this.state.exportedContent) return;

    const mimeType = this.getMimeType(this.state.options.format);
    
    if (this.callbacks.onDownload) {
      this.callbacks.onDownload(
        this.state.exportedContent,
        this.state.fileName,
        mimeType
      );
    }
  }

  // Get MIME type for format
  private getMimeType(format: string): string {
    const mimeTypes: Record<string, string> = {
      'text': 'text/plain',
      'json': 'application/json',
      'html': 'text/html',
      'csv': 'text/csv',
      'markdown': 'text/markdown'
    };

    return mimeTypes[format] || 'text/plain';
  }

  // Generate file name
  private generateFileName(format: string): string {
    const date = new Date().toISOString().split('T')[0];
    const extensions: Record<string, string> = {
      'text': 'txt',
      'json': 'json',
      'html': 'html',
      'csv': 'csv',
      'markdown': 'md'
    };

    const extension = extensions[format] || 'txt';
    return `karen-conversation-${date}.${extension}`;
  }

  // Get role display name
  private getRoleDisplayName(role: string): string {
    const roleNames: Record<string, string> = {
      'user': 'You',
      'assistant': 'AI Karen',
      'system': 'System'
    };

    return roleNames[role] || role;
  }

  // Escape HTML characters
  private escapeHtml(text: string): string {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // Get render data
  getRenderData(): ExportDialogRenderData {
    return {
      state: this.getState(),
      theme: this.theme,
      formatOptions: [
        { value: 'text', label: 'Plain Text (.txt)' },
        { value: 'json', label: 'JSON (.json)' },
        { value: 'html', label: 'HTML (.html)' },
        { value: 'csv', label: 'CSV (.csv)' },
        { value: 'markdown', label: 'Markdown (.md)' }
      ],
      handlers: {
        onOpen: () => this.open(),
        onClose: () => this.close(),
        onOptionsChange: (options: Partial<ExportOptions>) => this.updateOptions(options),
        onExport: () => this.performExport(),
        onDownload: () => this.downloadExport()
      }
    };
  }

  // Update theme
  updateTheme(theme: Theme): void {
    this.theme = theme;
  }

  // Update messages
  updateMessages(messages: ChatMessage[]): void {
    this.messages = messages;
    if (this.state.isOpen) {
      this.updatePreview();
    }
  }
}

// Supporting interfaces
export interface ExportDialogRenderData {
  state: ExportDialogState;
  theme: Theme;
  formatOptions: Array<{ value: string; label: string }>;
  handlers: {
    onOpen: () => void;
    onClose: () => void;
    onOptionsChange: (options: Partial<ExportOptions>) => void;
    onExport: () => Promise<void>;
    onDownload: () => void;
  };
}

// Utility functions
export function createExportDialog(
  messages: ChatMessage[],
  theme: Theme,
  callbacks: ExportDialogCallbacks = {}
): SharedExportDialog {
  return new SharedExportDialog(messages, theme, callbacks);
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

export function getExportPreview(content: string, maxLength: number = 500): string {
  if (content.length <= maxLength) return content;
  return content.substring(0, maxLength) + '...';
}