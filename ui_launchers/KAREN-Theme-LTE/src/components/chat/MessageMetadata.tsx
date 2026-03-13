/**
 * Message Metadata Component - Display detailed message metadata
 */

import React, { useState } from 'react';
import { Message } from '../../types/conversation';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Separator } from '../ui/separator';
import { 
  Info,
  Copy,
  ExternalLink,
  Clock,
  Zap,
  Database,
  Cpu,
  HardDrive,
  Network,
  CheckCircle,
  AlertTriangle,
  XCircle
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { formatDistanceToNow } from 'date-fns';

interface MessageMetadataProps {
  message: Message;
  className?: string;
}

interface MetadataItem {
  label: string;
  value: string | number | boolean;
  icon?: React.ReactNode;
  type?: 'text' | 'number' | 'boolean' | 'status';
  copyable?: boolean;
}

export const MessageMetadata: React.FC<MessageMetadataProps> = ({
  message,
  className = ''
}) => {
  const [copiedItem, setCopiedItem] = useState<string | null>(null);

  const copyToClipboard = (text: string, itemLabel: string) => {
    navigator.clipboard.writeText(text);
    setCopiedItem(itemLabel);
    setTimeout(() => setCopiedItem(null), 2000);
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Info className="h-4 w-4 text-blue-500" />;
    }
  };

  const getMetadataItems = (): MetadataItem[] => {
    const items: MetadataItem[] = [];

    // Basic message information
    items.push(
      {
        label: 'Message ID',
        value: message.id,
        icon: <Database className="h-4 w-4" />,
        type: 'text',
        copyable: true
      },
      {
        label: 'Conversation ID',
        value: message.conversationId,
        icon: <ExternalLink className="h-4 w-4" />,
        type: 'text',
        copyable: true
      },
      {
        label: 'Role',
        value: message.role,
        icon: message.role === 'user' ? 
          <div className="h-4 w-4 bg-blue-500 rounded-full" /> : 
          <div className="h-4 w-4 bg-green-500 rounded-full" />,
        type: 'text'
      },
      {
        label: 'Created',
        value: formatDistanceToNow(new Date(message.timestamp), { addSuffix: true }),
        icon: <Clock className="h-4 w-4" />,
        type: 'text'
      },
      {
        label: 'Timestamp',
        value: new Date(message.timestamp).toISOString(),
        icon: <Clock className="h-4 w-4" />,
        type: 'text',
        copyable: true
      }
    );

    // Content metrics
    const wordCount = message.content.split(/\s+/).length;
    const charCount = message.content.length;
    
    items.push(
      {
        label: 'Word Count',
        value: wordCount,
        icon: <Info className="h-4 w-4" />,
        type: 'number'
      },
      {
        label: 'Character Count',
        value: charCount,
        icon: <Info className="h-4 w-4" />,
        type: 'number'
      }
    );

    // Processing metadata (if available)
    if (message.metadata) {
      const { metadata } = message;
      
      if (metadata.tokens) {
        items.push({
          label: 'Tokens',
          value: metadata.tokens,
          icon: <Zap className="h-4 w-4" />,
          type: 'number'
        });
      }

      if (metadata.processingTime) {
        items.push({
          label: 'Processing Time',
          value: `${metadata.processingTime}s`,
          icon: <Cpu className="h-4 w-4" />,
          type: 'text'
        });
      }

      if (metadata.provider) {
        items.push({
          label: 'Provider',
          value: metadata.provider,
          icon: <Network className="h-4 w-4" />,
          type: 'text'
        });
      }

      if (metadata.model) {
        items.push({
          label: 'Model',
          value: metadata.model,
          icon: <Cpu className="h-4 w-4" />,
          type: 'text'
        });
      }

      if (metadata.temperature !== undefined) {
        items.push({
          label: 'Temperature',
          value: metadata.temperature,
          icon: <Zap className="h-4 w-4" />,
          type: 'number'
        });
      }

      if (metadata.maxTokens) {
        items.push({
          label: 'Max Tokens',
          value: metadata.maxTokens as number,
          icon: <HardDrive className="h-4 w-4" />,
          type: 'number'
        });
      }

      if (metadata.cost) {
        items.push({
          label: 'Cost',
          value: `$${metadata.cost.toFixed(6)}`,
          icon: <Database className="h-4 w-4" />,
          type: 'text'
        });
      }

      if (metadata.status) {
        items.push({
          label: 'Status',
          value: metadata.status as string,
          icon: getStatusIcon(metadata.status as string),
          type: 'status'
        });
      }

      if (metadata.error) {
        items.push({
          label: 'Error',
          value: metadata.error as string,
          icon: <XCircle className="h-4 w-4" />,
          type: 'text'
        });
      }

      if (metadata.version) {
        items.push({
          label: 'API Version',
          value: metadata.version as string,
          icon: <Info className="h-4 w-4" />,
          type: 'text'
        });
      }

      if (metadata.endpoint) {
        items.push({
          label: 'API Endpoint',
          value: metadata.endpoint as string,
          icon: <ExternalLink className="h-4 w-4" />,
          type: 'text',
          copyable: true
        });
      }
    }

    return items;
  };

  const metadataItems = getMetadataItems();

  const renderMetadataValue = (item: MetadataItem) => {
    let valueElement: React.ReactNode;

    switch (item.type) {
      case 'boolean':
        valueElement = (
          <Badge variant={item.value ? 'default' : 'secondary'}>
            {item.value ? 'Yes' : 'No'}
          </Badge>
        );
        break;
      case 'number':
        valueElement = (
          <span className="font-mono text-sm">
            {typeof item.value === 'number' ? item.value.toLocaleString() : item.value}
          </span>
        );
        break;
      case 'status':
        valueElement = (
          <div className="flex items-center space-x-2">
            {item.icon}
            <Badge variant="outline">{item.value}</Badge>
          </div>
        );
        break;
      default:
        valueElement = (
          <span className="font-mono text-sm break-all">
            {item.value}
          </span>
        );
    }

    return (
      <div className="flex items-center justify-between">
        {valueElement}
        {item.copyable && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => copyToClipboard(String(item.value), item.label)}
            className="h-6 w-6 p-0"
          >
            {copiedItem === item.label ? (
              <CheckCircle className="h-3 w-3 text-green-500" />
            ) : (
              <Copy className="h-3 w-3" />
            )}
          </Button>
        )}
      </div>
    );
  };

  return (
    <div className={cn('message-metadata', className)}>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Info className="h-5 w-5" />
            <span>Message Metadata</span>
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Message Preview */}
          <div className="p-3 bg-muted rounded-lg">
            <div className="text-sm font-medium mb-2">Message Preview</div>
            <div className="text-sm text-muted-foreground line-clamp-3">
              {message.content}
            </div>
            <div className="text-xs text-muted-foreground mt-2">
              {message.content.length > 150 && `(${message.content.length} characters total)`}
            </div>
          </div>

          <Separator />

          {/* Metadata Items */}
          <div className="space-y-3">
            {metadataItems.map((item, index) => (
              <div key={index} className="space-y-1">
                <div className="flex items-center space-x-2 text-sm font-medium">
                  {item.icon}
                  <span>{item.label}</span>
                </div>
                <div className="ml-6">
                  {renderMetadataValue(item)}
                </div>
              </div>
            ))}
          </div>

          {/* Raw Metadata */}
          {message.metadata && (
            <>
              <Separator />
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="text-sm font-medium">Raw Metadata</div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => copyToClipboard(JSON.stringify(message.metadata, null, 2), 'Raw Metadata')}
                    className="h-6 px-2"
                  >
                    <Copy className="h-3 w-3 mr-1" />
                    Copy JSON
                  </Button>
                </div>
                <pre className="text-xs bg-muted p-3 rounded-md overflow-x-auto">
                  {JSON.stringify(message.metadata, null, 2)}
                </pre>
              </div>
            </>
          )}

          {/* Actions */}
          <Separator />
          <div className="flex space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => copyToClipboard(JSON.stringify(message, null, 2), 'Full Message')}
              className="flex-1"
            >
              <Copy className="h-4 w-4 mr-2" />
              Copy Full Message
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => copyToClipboard(message.id, 'Message ID')}
            >
              <Copy className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
