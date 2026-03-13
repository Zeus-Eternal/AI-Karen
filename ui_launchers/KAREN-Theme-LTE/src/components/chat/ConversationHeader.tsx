/**
 * Conversation Header Component
 * Header with conversation title and actions
 */

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { Conversation } from '@/types/chat';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  MoreHorizontal,
  Settings,
  Users,
  Share2,
  Archive,
  Trash2,
  Edit,
  Pin,
  PinOff,
  Star,
  StarOff,
  ChevronDown
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

export interface ConversationHeaderProps {
  conversation?: Conversation | null;
  onSettingsClick?: () => void;
  onShareClick?: () => void;
  onArchiveClick?: () => void;
  onDeleteClick?: () => void;
  onRenameClick?: () => void;
  onTogglePin?: () => void;
  onToggleStar?: () => void;
  className?: string;
  showActions?: boolean;
}

export function ConversationHeader({
  conversation,
  onSettingsClick,
  onShareClick,
  onArchiveClick,
  onDeleteClick,
  onRenameClick,
  onTogglePin,
  onToggleStar,
  className,
  showActions = true,
}: ConversationHeaderProps) {
  const [showDropdown, setShowDropdown] = useState(false);

  if (!conversation) {
    return (
      <div className={cn('border-b border-purple-500/20 bg-black/40 backdrop-blur-md p-4', className)}>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-white">New Conversation</h1>
            <p className="text-sm text-purple-400">Start a new conversation with KAREN</p>
          </div>
          {showActions && (
            <Button variant="ghost" size="icon" className="text-purple-400 hover:text-purple-300">
              <MoreHorizontal className="h-5 w-5" />
            </Button>
          )}
        </div>
      </div>
    );
  }

  const getStatusBadge = () => {
    switch (conversation.status) {
      case 'active':
        return <Badge variant="default" className="bg-green-500/20 text-green-400 border-green-500/30">Active</Badge>;
      case 'archived':
        return <Badge variant="secondary" className="bg-gray-500/20 text-gray-400 border-gray-500/30">Archived</Badge>;
      case 'suspended':
        return <Badge variant="destructive" className="bg-orange-500/20 text-orange-400 border-orange-500/30">Suspended</Badge>;
      default:
        return null;
    }
  };

  const formatLastActivity = (date: Date) => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric'
    }).format(date);
  };

  return (
    <div className={cn('border-b border-purple-500/20 bg-black/40 backdrop-blur-md p-4', className)}>
      <div className="flex items-center justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            {conversation.isPinned && (
              <Pin className="h-4 w-4 text-purple-400 fill-current" />
            )}
            <h1 className="text-xl font-semibold text-white truncate">
              {conversation.title}
            </h1>
            {getStatusBadge()}
          </div>
          
          <div className="flex items-center gap-4 text-sm text-purple-400">
            <div className="flex items-center gap-1">
              <Users className="h-4 w-4" />
              <span>{conversation.participants.length} participants</span>
            </div>
            
            <div className="flex items-center gap-1">
              <span>{conversation.messageCount} messages</span>
            </div>
            
            {conversation.unreadCount > 0 && (
              <Badge variant="destructive" className="bg-red-500/20 text-red-400 border-red-500/30 text-xs px-1.5 py-0.5 h-auto">
                {conversation.unreadCount} unread
              </Badge>
            )}
            
            <div className="flex items-center gap-1">
              <span>Last active</span>
              <span>{formatLastActivity(conversation.lastMessageAt || conversation.updatedAt)}</span>
            </div>
          </div>
          
          {conversation.description && (
            <p className="text-sm text-purple-300 mt-1 line-clamp-2">
              {conversation.description}
            </p>
          )}
        </div>

        {showActions && (
          <div className="flex items-center gap-2">
            {/* Quick action buttons */}
            <Button
              variant="ghost"
              size="icon"
              onClick={onSettingsClick}
              className="text-purple-400 hover:text-purple-300"
              title="Conversation settings"
            >
              <Settings className="h-5 w-5" />
            </Button>
            
            <Button
              variant="ghost"
              size="icon"
              onClick={onShareClick}
              className="text-purple-400 hover:text-purple-300"
              title="Share conversation"
            >
              <Share2 className="h-5 w-5" />
            </Button>
            
            {/* More options dropdown */}
            <DropdownMenu open={showDropdown} onOpenChange={setShowDropdown}>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="text-purple-400 hover:text-purple-300"
                  title="More options"
                >
                  <MoreHorizontal className="h-5 w-5" />
                </Button>
              </DropdownMenuTrigger>
              
              <DropdownMenuContent align="end" className="bg-black/90 backdrop-blur-md border-purple-500/30">
                <DropdownMenuItem
                  onClick={onRenameClick}
                  className="text-white hover:bg-purple-500/20 focus:bg-purple-500/20"
                >
                  <Edit className="h-4 w-4 mr-2" />
                  Rename
                </DropdownMenuItem>
                
                <DropdownMenuItem
                  onClick={onTogglePin}
                  className="text-white hover:bg-purple-500/20 focus:bg-purple-500/20"
                >
                  {conversation.isPinned ? (
                    <>
                      <PinOff className="h-4 w-4 mr-2" />
                      Unpin
                    </>
                  ) : (
                    <>
                      <Pin className="h-4 w-4 mr-2" />
                      Pin
                    </>
                  )}
                </DropdownMenuItem>
                
                <DropdownMenuItem
                  onClick={onToggleStar}
                  className="text-white hover:bg-purple-500/20 focus:bg-purple-500/20"
                >
                  {conversation.isPinned ? (
                    <>
                      <StarOff className="h-4 w-4 mr-2" />
                      Unstar
                    </>
                  ) : (
                    <>
                      <Star className="h-4 w-4 mr-2" />
                      Star
                    </>
                  )}
                </DropdownMenuItem>
                
                <DropdownMenuSeparator className="bg-purple-500/20" />
                
                <DropdownMenuItem
                  onClick={onArchiveClick}
                  className="text-white hover:bg-purple-500/20 focus:bg-purple-500/20"
                >
                  <Archive className="h-4 w-4 mr-2" />
                  Archive
                </DropdownMenuItem>
                
                <DropdownMenuItem
                  onClick={onDeleteClick}
                  className="text-red-400 hover:bg-red-500/20 focus:bg-red-500/20"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        )}
      </div>
      
      {/* Tags */}
      {conversation.tags && conversation.tags.length > 0 && (
        <div className="flex items-center gap-1 mt-3 flex-wrap">
          {conversation.tags.map((tag) => (
            <Badge
              key={tag}
              variant="outline"
              className="text-xs bg-purple-500/10 text-purple-300 border-purple-500/20 px-2 py-0.5 h-auto"
            >
              {tag}
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}