/**
 * Conversation Manager Component - Main interface for managing conversations
 */

import React, { useState, useEffect } from 'react';
import { Conversation, Message } from '@/types/conversation';
import { ConversationList } from './ConversationList';
import { MessageHistory } from './MessageHistory';
import { ConversationSearch } from './ConversationSearch';
import { ConversationArchive } from './ConversationArchive';
import { ConversationExport } from './ConversationExport';
import { ConversationStats } from './ConversationStats';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Badge } from '../ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../ui/dialog';
import {
  MessageSquare,
  Search,
  Archive,
  Download,
  BarChart3,
  Plus,
  Settings,
  Filter,
  MoreVertical
} from 'lucide-react';

interface ConversationManagerProps {
  userId: string;
  className?: string;
}

export const ConversationManager: React.FC<ConversationManagerProps> = ({
  userId,
  className = ''
}) => {
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [activeTab, setActiveTab] = useState('conversations');
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [newConversationTitle, setNewConversationTitle] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [showArchived, setShowArchived] = useState(false);

  // Mock data for demonstration
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversationsLoading, setConversationsLoading] = useState(false);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [conversationsError, setConversationsError] = useState<string | null>(null);
  const [messagesError, setMessagesError] = useState<string | null>(null);

  // Load messages when conversation is selected
  useEffect(() => {
    if (selectedConversation) {
      // Mock loading messages
      setMessagesLoading(true);
      setTimeout(() => {
        setMessages([]);
        setMessagesLoading(false);
      }, 500);
    }
  }, [selectedConversation]);

  // Handle conversation creation
  const handleCreateConversation = async () => {
    if (!newConversationTitle.trim()) return;

    try {
      const newConv: Conversation = {
        id: Date.now().toString(),
        title: newConversationTitle.trim(),
        userId,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        metadata: {
          tags: []
        }
      };

      setConversations([...conversations, newConv]);
      setSelectedConversation(newConv);
      setNewConversationTitle('');
      setIsCreateDialogOpen(false);
    } catch (error) {
      console.error('Failed to create conversation:', error);
    }
  };

  // Handle conversation selection
  const handleSelectConversation = (conversation: Conversation) => {
    setSelectedConversation(conversation);
  };

  // Handle conversation deletion
  const handleDeleteConversation = async (conversationId: string) => {
    try {
      setConversations(conversations.filter(c => c.id !== conversationId));
      if (selectedConversation?.id === conversationId) {
        setSelectedConversation(null);
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error);
    }
  };

  // Handle conversation archiving
  const handleArchiveConversation = async (conversationId: string) => {
    try {
      setConversations(conversations.map(c =>
        c.id === conversationId ? { ...c, archived: true } : c
      ));
      if (selectedConversation?.id === conversationId) {
        setSelectedConversation(null);
      }
    } catch (error) {
      console.error('Failed to archive conversation:', error);
    }
  };

  // Handle conversation pinning
  const handlePinConversation = async (conversationId: string, pinned: boolean) => {
    try {
      setConversations(conversations.map(c =>
        c.id === conversationId ? { ...c, pinned } : c
      ));
    } catch (error) {
      console.error('Failed to update conversation pin status:', error);
    }
  };

  // Filter conversations based on search and archived status
  const filteredConversations = conversations.filter((conv: Conversation) => {
    const matchesSearch = conv.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         conv.metadata?.tags?.some((tag: string) =>
                           tag.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesArchive = showArchived ? (conv.archived ?? false) : !(conv.archived ?? false);
    return matchesSearch && matchesArchive;
  });

  // Sort conversations: pinned first, then by last updated
  const sortedConversations = [...filteredConversations].sort((a, b) => {
    if ((a.pinned ?? false) && !(b.pinned ?? false)) return -1;
    if (!(a.pinned ?? false) && (b.pinned ?? false)) return 1;
    return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime();
  });

  return (
    <div className={`conversation-manager ${className}`}>
      <Card className="h-full">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <CardTitle className="text-lg font-semibold">Conversations</CardTitle>

          <div className="flex items-center space-x-2">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search conversations..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 w-64"
              />
            </div>

            {/* Filter toggle */}
            <Button
              variant={showArchived ? "default" : "outline"}
              size="sm"
              onClick={() => setShowArchived(!showArchived)}
            >
              <Archive className="h-4 w-4 mr-2" />
              {showArchived ? 'Active' : 'Archived'}
            </Button>

            {/* Create new conversation */}
            <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button size="sm">
                  <Plus className="h-4 w-4 mr-2" />
                  New Conversation
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Create New Conversation</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <Input
                    placeholder="Conversation title..."
                    value={newConversationTitle}
                    onChange={(e) => setNewConversationTitle(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleCreateConversation()}
                  />
                  <div className="flex justify-end space-x-2">
                    <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                      Cancel
                    </Button>
                    <Button onClick={handleCreateConversation}>
                      Create
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </CardHeader>

        <CardContent className="p-0">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full">
            <TabsList className="grid w-full grid-cols-5">
              <TabsTrigger value="conversations" className="flex items-center space-x-2">
                <MessageSquare className="h-4 w-4" />
                <span>Conversations</span>
              </TabsTrigger>
              <TabsTrigger value="search" className="flex items-center space-x-2">
                <Search className="h-4 w-4" />
                <span>Search</span>
              </TabsTrigger>
              <TabsTrigger value="archive" className="flex items-center space-x-2">
                <Archive className="h-4 w-4" />
                <span>Archive</span>
              </TabsTrigger>
              <TabsTrigger value="export" className="flex items-center space-x-2">
                <Download className="h-4 w-4" />
                <span>Export</span>
              </TabsTrigger>
              <TabsTrigger value="stats" className="flex items-center space-x-2">
                <BarChart3 className="h-4 w-4" />
                <span>Stats</span>
              </TabsTrigger>
            </TabsList>

            <div className="mt-4">
              <TabsContent value="conversations" className="m-0">
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 h-full">
                  {/* Conversation List */}
                  <div className="lg:col-span-1 border-r">
                    <ConversationList
                      conversations={sortedConversations}
                      selectedConversationId={selectedConversation?.id ?? undefined}
                      onSelectConversation={handleSelectConversation}
                      onDeleteConversation={handleDeleteConversation}
                      onArchiveConversation={handleArchiveConversation}
                      onPinConversation={handlePinConversation}
                      loading={conversationsLoading}
                      error={conversationsError}
                    />
                  </div>

                  {/* Message History */}
                  <div className="lg:col-span-2">
                    {selectedConversation ? (
                      <MessageHistory
                        conversationId={selectedConversation.id}
                        userId={userId}
                      />
                    ) : (
                      <div className="flex items-center justify-center h-full text-muted-foreground">
                        <div className="text-center">
                          <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
                          <p>Select a conversation to view messages</p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="search" className="m-0">
                <ConversationSearch userId={userId} />
              </TabsContent>

              <TabsContent value="archive" className="m-0">
                <ConversationArchive
                  userId={userId}
                  onRestore={(conversation) => {
                    setSelectedConversation(conversation);
                    setActiveTab('conversations');
                  }}
                />
              </TabsContent>

              <TabsContent value="export" className="m-0">
                <ConversationExport userId={userId} />
              </TabsContent>

              <TabsContent value="stats" className="m-0">
                <ConversationStats userId={userId} />
              </TabsContent>
            </div>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};
