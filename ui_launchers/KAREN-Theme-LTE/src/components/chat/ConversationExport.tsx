/**
 * Conversation Export Component - Export conversations in various formats
 */

import React, { useState } from 'react';
import { Conversation, ExportOptions } from '../../types/conversation';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Input } from '../ui/input';
import { 
  Download, 
  FileText, 
  Calendar,
  Filter,
  Settings,
  Check,
  X
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu';
import { cn } from '../../lib/utils';

interface ConversationExportProps {
  userId: string;
  className?: string;
}

export const ConversationExport: React.FC<ConversationExportProps> = ({
  userId,
  className = ''
}) => {
  const [selectedConversations, setSelectedConversations] = useState<string[]>([]);
  const [exportOptions, setExportOptions] = useState<ExportOptions>({
    format: 'json',
    includeAttachments: true,
    includeMetadata: true
  });
  const [isExporting, setIsExporting] = useState(false);
  const [exportProgress, setExportProgress] = useState(0);

  // Mock data - in real implementation, this would fetch from API
  const [conversations, setConversations] = useState<Conversation[]>([
    {
      id: '1',
      userId,
      title: 'Project Planning Session',
      createdAt: '2023-12-01T10:00:00Z',
      updatedAt: '2023-12-01T15:30:00Z',
      archived: false,
      metadata: {
        tags: ['project', 'planning'],
        provider: 'OpenAI',
        model: 'gpt-4'
      }
    },
    {
      id: '2',
      userId,
      title: 'Research Notes',
      createdAt: '2023-12-02T14:20:00Z',
      updatedAt: '2023-12-02T09:15:00Z',
      archived: false,
      metadata: {
        tags: ['research', 'notes'],
        provider: 'Anthropic',
        model: 'claude-2'
      }
    },
    {
      id: '3',
      userId,
      title: 'Team Meeting Notes',
      createdAt: '2023-12-03T11:45:00Z',
      updatedAt: '2023-12-03T16:30:00Z',
      archived: false,
      metadata: {
        tags: ['meeting', 'team'],
        provider: 'Google',
        model: 'gemini-pro'
      }
    }
  ]);

  const handleSelectConversation = (id: string) => {
    setSelectedConversations(prev => 
      prev.includes(id) 
        ? prev.filter(selectedId => selectedId !== id)
        : [...prev, id]
    );
  };

  const handleSelectAll = () => {
    setSelectedConversations(conversations.map(c => c.id));
  };

  const handleClearSelection = () => {
    setSelectedConversations([]);
  };

  const handleExport = async () => {
    if (selectedConversations.length === 0) {
      alert('Please select at least one conversation to export');
      return;
    }

    setIsExporting(true);
    setExportProgress(0);

    try {
      // Mock export process
      const totalSteps = selectedConversations.length * 3; // Mock: 3 steps per conversation
      
      for (let i = 0; i <= totalSteps; i++) {
        await new Promise(resolve => setTimeout(resolve, 50)); // Simulate processing time
        setExportProgress(Math.round((i / totalSteps) * 100));
      }

      // Mock download
      const blob = new Blob([JSON.stringify({
        conversations: conversations.filter(c => selectedConversations.includes(c.id)),
        options: exportOptions,
        exportedAt: new Date().toISOString()
      })], { type: 'application/json' });

      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `conversations.${exportOptions.format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      alert(`Exported ${selectedConversations.length} conversations in ${exportOptions.format} format`);
    } catch (error) {
      console.error('Export failed:', error);
      alert('Export failed. Please try again.');
    } finally {
      setIsExporting(false);
      setExportProgress(0);
    }
  };

  const formatDateRange = (start: Date, end: Date) => {
    return `${start.toLocaleDateString()} - ${end.toLocaleDateString()}`;
  };

  return (
    <div className={cn('conversation-export', className)}>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Download className="h-5 w-5" />
            <span>Export Conversations</span>
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Export Options */}
          <div className="space-y-4 p-4 bg-muted rounded-lg">
            <h3 className="text-lg font-medium mb-4">Export Options</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Format Selection */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Format</label>
                <div className="flex space-x-2">
                  {['json', 'csv', 'pdf', 'txt'].map(format => (
                    <Button
                      key={format}
                      variant={exportOptions.format === format ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setExportOptions(prev => ({ ...prev, format: format as ExportOptions['format'] }))}
                    >
                      <FileText className="h-4 w-4 mr-2" />
                      {format.toUpperCase()}
                    </Button>
                  ))}
                </div>
              </div>

              {/* Include Options */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Include</label>
                <div className="space-y-3">
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={exportOptions.includeAttachments}
                      onChange={(e) => setExportOptions(prev => ({ 
                        ...prev, 
                        includeAttachments: e.target.checked 
                      }))}
                    />
                    <span>Attachments</span>
                  </label>
                  
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={exportOptions.includeMetadata}
                      onChange={(e) => setExportOptions(prev => ({ 
                        ...prev, 
                        includeMetadata: e.target.checked 
                      }))}
                    />
                    <span>Metadata</span>
                  </label>
                </div>
              </div>

              {/* Date Range */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Date Range</label>
                <div className="flex items-center space-x-2">
                  <Input
                    type="date"
                    value={exportOptions.dateRange?.start?.toISOString().split('T')[0] || ''}
                    onChange={(e) => {
                      const start = new Date(e.target.value);
                      const end = exportOptions.dateRange?.end || new Date();
                      setExportOptions(prev => ({ 
                        ...prev, 
                        dateRange: { start, end } 
                      }));
                    }}
                    className="flex-1"
                  />
                  <span className="mx-2">to</span>
                  <Input
                    type="date"
                    value={exportOptions.dateRange?.end?.toISOString().split('T')[0] || ''}
                    onChange={(e) => {
                      const end = new Date(e.target.value);
                      const start = exportOptions.dateRange?.start || new Date();
                      setExportOptions(prev => ({ 
                        ...prev, 
                        dateRange: { start, end } 
                      }));
                    }}
                    className="flex-1"
                  />
                </div>
                {exportOptions.dateRange?.start && exportOptions.dateRange?.end && (
                  <div className="text-xs text-muted-foreground mt-1">
                    {formatDateRange(exportOptions.dateRange.start, exportOptions.dateRange.end)}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Conversation Selection */}
          <div className="space-y-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium">Select Conversations</h3>
              <div className="flex space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleSelectAll}
                >
                  <Check className="h-4 w-4 mr-2" />
                  Select All ({conversations.length})
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleClearSelection}
                >
                  <X className="h-4 w-4 mr-2" />
                  Clear Selection
                </Button>
              </div>
              
              <Badge variant="secondary">
                {selectedConversations.length} of {conversations.length} selected
              </Badge>
            </div>

            {/* Conversation List */}
            <div className="border rounded-lg max-h-60 overflow-y-auto">
              {conversations.map((conversation) => (
                <div
                  key={conversation.id}
                  className={cn(
                    'flex items-center p-4 border-b cursor-pointer hover:bg-muted',
                    selectedConversations.includes(conversation.id) && 'bg-primary/10'
                  )}
                  onClick={() => handleSelectConversation(conversation.id)}
                >
                  <input
                    type="checkbox"
                    checked={selectedConversations.includes(conversation.id)}
                    onChange={() => handleSelectConversation(conversation.id)}
                    className="mr-3"
                  />
                  
                  <div className="flex-1">
                    <h4 className="font-medium">{conversation.title}</h4>
                    <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                      <Calendar className="h-3 w-3" />
                      <span>{new Date(conversation.createdAt).toLocaleDateString()}</span>
                    </div>
                    
                    {conversation.metadata?.tags && (
                      <div className="flex flex-wrap gap-1">
                        {conversation.metadata.tags.map((tag: string) => (
                          <Badge key={tag} variant="outline" className="text-xs">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Export Button */}
          <div className="flex justify-center mt-6">
            <Button
              onClick={handleExport}
              disabled={selectedConversations.length === 0 || isExporting}
              className="px-8 py-3"
            >
              {isExporting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary mr-3"></div>
                  Exporting... {exportProgress}%
                </>
              ) : (
                <>
                  <Download className="h-4 w-4 mr-2" />
                  Export {selectedConversations.length} Conversations
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};