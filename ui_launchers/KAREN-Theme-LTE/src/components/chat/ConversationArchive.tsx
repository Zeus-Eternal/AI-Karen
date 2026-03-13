/**
 * Conversation Archive Component - Manage archived conversations
 */

import React, { useState } from 'react';
import { Conversation } from '../../types/conversation';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Input } from '../ui/input';
import { 
  Archive, 
  ArchiveRestore, 
  Search, 
  Calendar, 
  MoreVertical,
  Trash2
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu';
import { cn } from '../../lib/utils';

interface ConversationArchiveProps {
  userId: string;
  onRestore?: (conversation: Conversation) => void;
  className?: string;
}

export const ConversationArchive: React.FC<ConversationArchiveProps> = ({
  userId,
  onRestore,
  className = ''
}) => {
  const [archivedConversations, setArchivedConversations] = useState<Conversation[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedConversations, setSelectedConversations] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  // Mock data - in real implementation, this would fetch from API
  React.useEffect(() => {
    const mockArchivedConversations: Conversation[] = [
      {
        id: '1',
        userId,
        title: 'Project Planning Session',
        createdAt: '2023-12-01T10:00:00Z',
        updatedAt: '2023-12-01T15:30:00Z',
        archived: true,
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
        archived: true,
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
        archived: true,
        metadata: {
          tags: ['meeting', 'team'],
          provider: 'Google',
          model: 'gemini-pro'
        }
      }
    ];

    setArchivedConversations(mockArchivedConversations);
  }, [userId]);

  const handleRestore = (conversation: Conversation) => {
    if (onRestore) {
      onRestore(conversation);
    }
  };

  const handleBulkRestore = () => {
    selectedConversations.forEach(id => {
      const conversation = archivedConversations.find(c => c.id === id);
      if (conversation) {
        handleRestore(conversation);
      }
    });
    setSelectedConversations([]);
  };

  const handleBulkDelete = async () => {
    if (window.confirm(`Are you sure you want to delete ${selectedConversations.length} archived conversations?`)) {
      setLoading(true);
      
      // Mock API call
      setTimeout(() => {
        setArchivedConversations(prev => 
          prev.filter(c => !selectedConversations.includes(c.id))
        );
        setSelectedConversations([]);
        setLoading(false);
      }, 1000);
    }
  };

  const handleSelectConversation = (id: string) => {
    setSelectedConversations(prev => 
      prev.includes(id) 
        ? prev.filter(selectedId => selectedId !== id)
        : [...prev, id]
    );
  };

  const filteredConversations = archivedConversations.filter(conv =>
    conv.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  return (
    <div className={cn('conversation-archive', className)}>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Archive className="h-5 w-5" />
            <span>Archived Conversations</span>
            <Badge variant="secondary" className="ml-2">
              {archivedConversations.length}
            </Badge>
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Search */}
          <div className="relative mb-6">
            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search archived conversations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Actions */}
          {selectedConversations.length > 0 && (
            <div className="flex items-center justify-between mb-4 p-4 bg-muted rounded-lg">
              <span className="text-sm">
                {selectedConversations.length} conversations selected
              </span>
              <div className="flex space-x-2">
                <Button
                  variant="default"
                  size="sm"
                  onClick={handleBulkRestore}
                  disabled={loading}
                >
                  <ArchiveRestore className="h-4 w-4 mr-2" />
                  Restore Selected
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={handleBulkDelete}
                  disabled={loading}
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete Selected
                </Button>
              </div>
            </div>
          )}

          {/* Conversation list */}
          <div className="space-y-3">
            {filteredConversations.length === 0 ? (
              <div className="text-center py-12">
                <Archive className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <p className="text-lg font-medium mb-2">No archived conversations</p>
                <p className="text-muted-foreground">
                  {searchQuery 
                    ? `No conversations found matching "${searchQuery}"`
                    : 'No conversations have been archived yet'
                  }
                </p>
              </div>
            ) : (
              filteredConversations.map((conversation) => (
                <Card
                  key={conversation.id}
                  className={cn(
                    'cursor-pointer hover:shadow-md transition-all',
                    selectedConversations.includes(conversation.id) && 'ring-2 ring-primary ring-offset-2'
                  )}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="font-medium mb-2">
                          {conversation.title}
                        </h3>
                        
                        <div className="flex items-center space-x-4 text-sm text-muted-foreground mb-3">
                          <div className="flex items-center space-x-1">
                            <Calendar className="h-3 w-3" />
                            <span>{formatDate(conversation.createdAt)}</span>
                          </div>
                          
                          <Badge variant="outline" className="text-xs">
                            Archived {formatDate(conversation.updatedAt)}
                          </Badge>
                        </div>

                        {conversation.metadata?.tags && (
                          <div className="flex flex-wrap gap-1 mb-2">
                            {conversation.metadata.tags.map((tag: string) => (
                              <Badge key={tag} variant="outline" className="text-xs">
                                {tag}
                              </Badge>
                            ))}
                          </div>
                        )}

                        {conversation.metadata?.provider && (
                          <div className="flex items-center space-x-2 mb-3">
                            <Badge variant="secondary" className="text-xs">
                              {conversation.metadata.provider}
                            </Badge>
                            {conversation.metadata?.model && (
                              <Badge variant="outline" className="text-xs ml-2">
                                {conversation.metadata.model}
                              </Badge>
                            )}
                          </div>
                        )}

                        <p className="text-sm text-muted-foreground line-clamp-2">
                          {conversation.metadata?.description || 'No description available'}
                        </p>
                      </div>

                      <div className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={selectedConversations.includes(conversation.id)}
                          onChange={() => handleSelectConversation(conversation.id)}
                          className="h-4 w-4"
                        />
                        
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-6 w-6 p-0"
                            >
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => handleRestore(conversation)}>
                              <ArchiveRestore className="h-4 w-4 mr-2" />
                              Restore
                            </DropdownMenuItem>
                            <DropdownMenuItem 
                              onClick={() => {
                                if (window.confirm(`Delete "${conversation.title}"? This action cannot be undone.`)) {
                                  // Handle delete
                                  setArchivedConversations(prev => 
                                    prev.filter(c => c.id !== conversation.id)
                                  );
                                }
                              }}
                              className="text-destructive focus:text-destructive"
                            >
                              <Trash2 className="h-4 w-4 mr-2" />
                              Delete Permanently
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};