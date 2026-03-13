/**
 * Message Export Component - Export message data in various formats
 */

import React, { useState, useEffect } from 'react';
import { Message, Conversation } from '../../types/conversation';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Checkbox } from '../ui/checkbox';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { RadioGroup, RadioGroupItem } from '../ui/radio-group';
import { Separator } from '../ui/separator';
import { 
  Download,
  FileText,
  FileSpreadsheet,
  FileImage,
  Settings,
  Calendar,
  Filter,
  CheckCircle,
  AlertCircle,
  Loader2
} from 'lucide-react';
import { cn } from '../../lib/utils';

interface MessageExportProps {
  conversationId?: string;
  userId: string;
  className?: string;
}

interface ExportOptions {
  format: 'json' | 'csv' | 'pdf' | 'txt';
  includeAttachments: boolean;
  includeMetadata: boolean;
  dateRange: {
    start: string;
    end: string;
  };
  messageIds: string[];
  conversationIds: string[];
}

interface ExportProgress {
  status: 'idle' | 'preparing' | 'processing' | 'completed' | 'error';
  progress: number;
  message: string;
  downloadUrl?: string;
}

export const MessageExport: React.FC<MessageExportProps> = ({
  conversationId,
  userId,
  className = ''
}) => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [exportOptions, setExportOptions] = useState<ExportOptions>({
    format: 'json',
    includeAttachments: true,
    includeMetadata: true,
    dateRange: {
      start: '',
      end: ''
    },
    messageIds: [],
    conversationIds: conversationId ? [conversationId] : []
  });
  const [exportProgress, setExportProgress] = useState<ExportProgress>({
    status: 'idle',
    progress: 0,
    message: ''
  });
  const [loading, setLoading] = useState(false);

  // Mock data - in real implementation, this would fetch from API
  const mockConversations: Conversation[] = [
    {
      id: 'conv_1',
      title: 'Project Planning Discussion',
      userId: userId,
      createdAt: new Date(Date.now() - 86400000 * 5).toISOString(),
      updatedAt: new Date(Date.now() - 86400000 * 2).toISOString(),
      metadata: {
        provider: 'OpenAI',
        model: 'gpt-4',
        messageCount: 25,
        tags: ['work', 'planning']
      }
    },
    {
      id: 'conv_2',
      title: 'React Development Help',
      userId: userId,
      createdAt: new Date(Date.now() - 86400000 * 3).toISOString(),
      updatedAt: new Date(Date.now() - 86400000).toISOString(),
      metadata: {
        provider: 'Anthropic',
        model: 'claude-3',
        messageCount: 18,
        tags: ['development', 'react']
      }
    }
  ];

  useEffect(() => {
    if (!conversationId) {
      setConversations(mockConversations);
    }
  }, [conversationId, userId]);

  const handleExport = async () => {
    setExportProgress({
      status: 'preparing',
      progress: 0,
      message: 'Preparing export...'
    });

    // Simulate export process
    setTimeout(() => {
      setExportProgress({
        status: 'processing',
        progress: 25,
        message: 'Gathering messages...'
      });
    }, 500);

    setTimeout(() => {
      setExportProgress({
        status: 'processing',
        progress: 50,
        message: 'Processing content...'
      });
    }, 1500);

    setTimeout(() => {
      setExportProgress({
        status: 'processing',
        progress: 75,
        message: 'Generating file...'
      });
    }, 2500);

    setTimeout(() => {
      // Generate mock export data
      const exportData = generateExportData();
      const blob = createExportBlob(exportData, exportOptions.format);
      const url = URL.createObjectURL(blob);
      
      setExportProgress({
        status: 'completed',
        progress: 100,
        message: 'Export completed successfully!',
        downloadUrl: url
      });
    }, 3500);
  };

  const generateExportData = () => {
    // Mock export data - in real implementation, this would fetch from API
    return {
      conversations: conversationId ? [mockConversations[0]] : mockConversations,
      messages: [
        {
          id: 'msg_1',
          conversationId: conversationId || 'conv_1',
          content: 'Hello! How can I help you today?',
          role: 'assistant',
          timestamp: new Date(Date.now() - 86400000 * 2).toISOString(),
          metadata: {
            provider: 'OpenAI',
            model: 'gpt-4',
            tokens: 25,
            processingTime: 1.2
          }
        },
        {
          id: 'msg_2',
          conversationId: conversationId || 'conv_1',
          content: 'I need help with my project.',
          role: 'user',
          timestamp: new Date(Date.now() - 86400000 * 2 + 60000).toISOString(),
          metadata: {
            tokens: 8
          }
        }
      ],
      exportOptions,
      exportedAt: new Date().toISOString(),
      exportedBy: userId
    };
  };

  const createExportBlob = (data: any, format: string): Blob => {
    switch (format) {
      case 'json':
        return new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      
      case 'csv':
        const csvContent = convertToCSV(data);
        return new Blob([csvContent], { type: 'text/csv' });
      
      case 'txt':
        const txtContent = convertToTXT(data);
        return new Blob([txtContent], { type: 'text/plain' });
      
      case 'pdf':
        // In a real implementation, this would use a PDF library
        const pdfContent = `PDF Export (mock)\n\n${JSON.stringify(data, null, 2)}`;
        return new Blob([pdfContent], { type: 'application/pdf' });
      
      default:
        return new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    }
  };

  const convertToCSV = (data: any): string => {
    const headers = ['ID', 'Conversation', 'Role', 'Content', 'Timestamp', 'Provider', 'Model'];
    const rows = data.messages.map((msg: Message) => [
      msg.id,
      msg.conversationId,
      msg.role,
      `"${msg.content.replace(/"/g, '""')}"`, // Escape quotes in CSV
      msg.timestamp,
      msg.metadata?.provider || '',
      msg.metadata?.model || ''
    ]);
    
    return [headers, ...rows].map(row => row.join(',')).join('\n');
  };

  const convertToTXT = (data: any): string => {
    let txtContent = `Conversation Export\n`;
    txtContent += `Exported: ${new Date().toLocaleString()}\n`;
    txtContent += `Format: ${exportOptions.format}\n`;
    txtContent += `Include Attachments: ${exportOptions.includeAttachments}\n`;
    txtContent += `Include Metadata: ${exportOptions.includeMetadata}\n\n`;
    
    data.conversations.forEach((conv: Conversation) => {
      txtContent += `Conversation: ${conv.title}\n`;
      txtContent += `Created: ${new Date(conv.createdAt).toLocaleString()}\n`;
      txtContent += `Messages: ${conv.metadata?.messageCount || 0}\n\n`;
      
      const convMessages = data.messages.filter((msg: Message) => msg.conversationId === conv.id);
      convMessages.forEach((msg: Message) => {
        txtContent += `[${new Date(msg.timestamp).toLocaleString()}] ${msg.role.toUpperCase()}\n`;
        txtContent += `${msg.content}\n\n`;
      });
      
      txtContent += '---\n\n';
    });
    
    return txtContent;
  };

  const downloadFile = () => {
    if (exportProgress.downloadUrl) {
      const a = document.createElement('a');
      a.href = exportProgress.downloadUrl;
      a.download = `conversation-export-${new Date().toISOString().split('T')[0]}.${exportOptions.format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(exportProgress.downloadUrl);
      
      // Reset progress
      setExportProgress({
        status: 'idle',
        progress: 0,
        message: ''
      });
    }
  };

  const resetExport = () => {
    setExportProgress({
      status: 'idle',
      progress: 0,
      message: ''
    });
  };

  const toggleConversation = (convId: string) => {
    setExportOptions(prev => ({
      ...prev,
      conversationIds: prev.conversationIds.includes(convId)
        ? prev.conversationIds.filter(id => id !== convId)
        : [...prev.conversationIds, convId]
    }));
  };

  const updateExportOption = <K extends keyof ExportOptions>(
    key: K,
    value: ExportOptions[K]
  ) => {
    setExportOptions(prev => ({ ...prev, [key]: value }));
  };

  const getFormatIcon = (format: string) => {
    switch (format) {
      case 'json':
        return <FileText className="h-4 w-4" />;
      case 'csv':
        return <FileSpreadsheet className="h-4 w-4" />;
      case 'pdf':
        return <FileImage className="h-4 w-4" />;
      case 'txt':
        return <FileText className="h-4 w-4" />;
      default:
        return <FileText className="h-4 w-4" />;
    }
  };

  return (
    <div className={cn('message-export', className)}>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Download className="h-5 w-5" />
            <span>Export Messages</span>
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Export Format Selection */}
          <div className="space-y-3">
            <Label className="text-base font-medium">Export Format</Label>
            <RadioGroup
              value={exportOptions.format}
              onValueChange={(value) => updateExportOption('format', value as any)}
              className="grid grid-cols-2 gap-4"
            >
              {[
                { value: 'json', label: 'JSON', description: 'Structured data format' },
                { value: 'csv', label: 'CSV', description: 'Spreadsheet compatible' },
                { value: 'pdf', label: 'PDF', description: 'Document format' },
                { value: 'txt', label: 'TXT', description: 'Plain text format' }
              ].map(format => (
                <div key={format.value} className="flex items-center space-x-2">
                  <RadioGroupItem value={format.value} id={format.value} />
                  <Label htmlFor={format.value} className="flex items-center space-x-2 cursor-pointer">
                    {getFormatIcon(format.value)}
                    <div>
                      <div className="font-medium">{format.label}</div>
                      <div className="text-sm text-muted-foreground">{format.description}</div>
                    </div>
                  </Label>
                </div>
              ))}
            </RadioGroup>
          </div>

          <Separator />

          {/* Conversation Selection */}
          {!conversationId && (
            <div className="space-y-3">
              <Label className="text-base font-medium">Select Conversations</Label>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {conversations.map(conv => (
                  <div key={conv.id} className="flex items-center space-x-2">
                    <Checkbox
                      id={`conv-${conv.id}`}
                      checked={exportOptions.conversationIds.includes(conv.id)}
                      onCheckedChange={() => toggleConversation(conv.id)}
                    />
                    <Label htmlFor={`conv-${conv.id}`} className="flex-1 cursor-pointer">
                      <div className="flex items-center justify-between">
                        <span>{conv.title}</span>
                        <Badge variant="outline" className="text-xs">
                          {(conv.metadata?.messageCount as number | undefined) || 0} messages
                        </Badge>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {new Date(conv.updatedAt).toLocaleDateString()}
                      </div>
                    </Label>
                  </div>
                ))}
              </div>
            </div>
          )}

          <Separator />

          {/* Export Options */}
          <div className="space-y-3">
            <Label className="text-base font-medium flex items-center space-x-2">
              <Settings className="h-4 w-4" />
              <span>Export Options</span>
            </Label>
            
            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="include-attachments"
                  checked={exportOptions.includeAttachments}
                  onCheckedChange={(checked) => updateExportOption('includeAttachments', !!checked)}
                />
                <Label htmlFor="include-attachments">Include attachments</Label>
              </div>
              
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="include-metadata"
                  checked={exportOptions.includeMetadata}
                  onCheckedChange={(checked) => updateExportOption('includeMetadata', !!checked)}
                />
                <Label htmlFor="include-metadata">Include metadata</Label>
              </div>
            </div>
          </div>

          <Separator />

          {/* Date Range */}
          <div className="space-y-3">
            <Label className="text-base font-medium flex items-center space-x-2">
              <Calendar className="h-4 w-4" />
              <span>Date Range</span>
            </Label>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="start-date">Start Date</Label>
                <Input
                  id="start-date"
                  type="date"
                  value={exportOptions.dateRange.start}
                  onChange={(e) => updateExportOption('dateRange', {
                    ...exportOptions.dateRange,
                    start: e.target.value
                  })}
                />
              </div>
              <div>
                <Label htmlFor="end-date">End Date</Label>
                <Input
                  id="end-date"
                  type="date"
                  value={exportOptions.dateRange.end}
                  onChange={(e) => updateExportOption('dateRange', {
                    ...exportOptions.dateRange,
                    end: e.target.value
                  })}
                />
              </div>
            </div>
          </div>

          <Separator />

          {/* Export Progress */}
          {exportProgress.status !== 'idle' && (
            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                {exportProgress.status === 'completed' && (
                  <CheckCircle className="h-5 w-5 text-green-500" />
                )}
                {exportProgress.status === 'error' && (
                  <AlertCircle className="h-5 w-5 text-red-500" />
                )}
                {(exportProgress.status === 'preparing' || exportProgress.status === 'processing') && (
                  <Loader2 className="h-5 w-5 animate-spin" />
                )}
                <span className="font-medium">{exportProgress.message}</span>
              </div>
              
              {(exportProgress.status === 'preparing' || exportProgress.status === 'processing') && (
                <div className="w-full bg-muted rounded-full h-2">
                  <div
                    className="bg-primary h-2 rounded-full transition-all duration-300"
                    style={{ width: `${exportProgress.progress}%` }}
                  />
                </div>
              )}
              
              {exportProgress.status === 'completed' && (
                <div className="flex space-x-2">
                  <Button onClick={downloadFile} className="flex-1">
                    <Download className="h-4 w-4 mr-2" />
                    Download Export
                  </Button>
                  <Button variant="outline" onClick={resetExport}>
                    New Export
                  </Button>
                </div>
              )}
              
              {exportProgress.status === 'error' && (
                <div className="flex space-x-2">
                  <Button variant="outline" onClick={resetExport} className="flex-1">
                    Try Again
                  </Button>
                </div>
              )}
            </div>
          )}

          {/* Export Button */}
          {exportProgress.status === 'idle' && (
            <Button
              onClick={handleExport}
              disabled={exportOptions.conversationIds.length === 0}
              className="w-full"
            >
              <Download className="h-4 w-4 mr-2" />
              Start Export
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
