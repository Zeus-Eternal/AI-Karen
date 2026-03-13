/**
 * Conversation List Component - Display list of conversations
 */

import React, { useState } from 'react';
import { Conversation } from '../../types/conversation';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Card, CardContent } from '../ui/card';
import { 
  MessageSquare, 
  Pin, 
  Archive, 
  Trash2, 
  MoreVertical,
  Clock,
  Tag
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu';
import { cn } from '../../lib/utils';

export interface ConversationListProps {
  conversations: Conversation[];
  selectedConversationId?: string;
  onSelectConversation: (conversation: Conversation) => void;
  onDeleteConversation: (conversationId: string) => Promise<void>;
  onArchiveConversation: (conversationId: string) => Promise<void>;
  onPinConversation: (conversationId: string, pinned: boolean) => Promise<void>;
  loading?: boolean;
  error?: string | null;
  className?: string;
}

export const ConversationList: React.FC<ConversationListProps> = ({
  conversations,
  selectedConversationId,
  onSelectConversation,
  onDeleteConversation,
  onArchiveConversation,
  onPinConversation,
  loading = false,
  error = null,
  className = ''
}) => {
  const [hoveredConversation, setHoveredConversation] = useState<string | null>(null);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
      if (diffHours === 0) {
        const diffMins = Math.floor(diffMs / (1000 * 60));
        return diffMins <= 1 ? 'Just now' : `${diffMins} minutes ago`;
      }
      return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    } else if (diffDays === 1) {
      return 'Yesterday';
    } else if (diffDays < 7) {
      return `${diffDays} days ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  const handleDeleteConversation = async (e: React.MouseEvent, conversationId: string) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this conversation?')) {
      await onDeleteConversation(conversationId);
    }
  };

  const handleArchiveConversation = async (e: React.MouseEvent, conversationId: string) => {
    e.stopPropagation();
    await onArchiveConversation(conversationId);
  };

  const handlePinConversation = async (e: React.MouseEvent, conversationId: string, pinned: boolean) => {
    e.stopPropagation();
    await onPinConversation(conversationId, !pinned);
  };

  if (loading) {
    return (
      <div className={cn('conversation-list loading', className)}>
        <div className="flex items-center justify-center p-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <span className="ml-2 text-muted-foreground">Loading conversations...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn('conversation-list error', className)}>
        <div className="flex items-center justify-center p-8">
          <div className="text-center">
            <Trash2 className="h-8 w-8 mx-auto mb-2 text-destructive" />
            <p className="text-destructive font-medium">Error loading conversations</p>
            <p className="text-sm text-muted-foreground mt-1">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (conversations.length === 0) {
    return (
      <div className={cn('conversation-list empty', className)}>
        <div className="flex items-center justify-center p-8">
          <div className="text-center">
            <MessageSquare className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
            <p className="text-lg font-medium text-muted-foreground">No conversations yet</p>
            <p className="text-sm text-muted-foreground mt-1">
              Start a new conversation to see it here
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={cn('conversation-list', className)}>
      <div className="space-y-2">
        {conversations.map((conversation) => (
          <Card
            key={conversation.id}
            className={cn(
              'cursor-pointer transition-all hover:shadow-md',
              selectedConversationId === conversation.id 
                ? 'border-primary bg-primary/5' 
                : 'border-border hover:border-primary/50',
              hoveredConversation === conversation.id && 'shadow-sm'
            )}
            onClick={() => onSelectConversation(conversation)}
            onMouseEnter={() => setHoveredConversation(conversation.id)}
            onMouseLeave={() => setHoveredConversation(null)}
          >
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-1">
                    <h3 className="font-medium truncate text-sm">
                      {conversation.title}
                    </h3>
                    {conversation.pinned && (
                      <Pin className="h-3 w-3 text-primary" fill="currentColor" />
                    )}
                    {conversation.archived && (
                      <Badge variant="secondary" className="text-xs">
                        Archived
                      </Badge>
                    )}
                  </div>
                  
                  <div className="flex items-center space-x-2 text-xs text-muted-foreground mb-2">
                    <Clock className="h-3 w-3" />
                    <span>{formatDate(conversation.updatedAt)}</span>
                  </div>

                  {conversation.metadata?.tags && conversation.metadata.tags.length > 0 && (
                    <div className="flex items-center space-x-1 mb-2">
                      <Tag className="h-3 w-3" />
                      <div className="flex flex-wrap gap-1">
                        {conversation.metadata.tags.slice(0, 3).map((tag, index) => (
                          <Badge key={index} variant="outline" className="text-xs">
                            {tag}
                          </Badge>
                        ))}
                        {conversation.metadata.tags.length > 3 && (
                          <Badge variant="outline" className="text-xs">
                            +{conversation.metadata.tags.length - 3}
                          </Badge>
                        )}
                      </div>
                    </div>
                  )}

                  {conversation.metadata?.provider && (
                    <div className="flex items-center space-x-1">
                      <Badge variant="secondary" className="text-xs">
                        {conversation.metadata.provider}
                      </Badge>
                      {conversation.metadata?.model && (
                        <Badge variant="outline" className="text-xs">
                          {conversation.metadata.model}
                        </Badge>
                      )}
                    </div>
                  )}
                </div>

                <div className="flex items-center space-x-1 ml-2">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 w-8 p-0"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem
                        onClick={(e) => handlePinConversation(e, conversation.id, conversation.pinned || false)}
                      >
                        <Pin className="h-4 w-4 mr-2" />
                        {conversation.pinned ? 'Unpin' : 'Pin'}
                      </DropdownMenuItem>
                      
                      <DropdownMenuItem
                        onClick={(e) => handleArchiveConversation(e, conversation.id)}
                      >
                        <Archive className="h-4 w-4 mr-2" />
                        Archive
                      </DropdownMenuItem>
                      
                      <DropdownMenuSeparator />
                      
                      <DropdownMenuItem
                        onClick={(e) => handleDeleteConversation(e, conversation.id)}
                        className="text-destructive focus:text-destructive"
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};