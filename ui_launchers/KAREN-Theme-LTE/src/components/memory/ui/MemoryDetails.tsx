"use client";

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { cn } from '@/lib/utils';
import { formatDate, formatRelativeTime, truncateText } from '@/lib/utils';
import { 
  Memory, 
  MemoryDetailsProps, 
  MemoryActionPayload,
  MemoryType,
  MemoryStatus,
  MemoryPriority,
  MemorySource
} from '../types';

// Utility function for type color
function getTypeColor(type: Memory['type']): string {
  switch (type) {
    case 'conversation': return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
    case 'case': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
    case 'unified': return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200';
    case 'fact': return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200';
    case 'preference': return 'bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-200';
    case 'context': return 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200';
    default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
  }
}

// Utility function for status color
function getStatusColor(status: Memory['status']): string {
  switch (status) {
    case 'active': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
    case 'archived': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
    case 'deleted': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
    case 'processing': return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
    default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
  }
}

// Utility function for priority color
function getPriorityColor(priority: Memory['priority']): string {
  switch (priority) {
    case 'critical': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
    case 'high': return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200';
    case 'medium': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
    case 'low': return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
  }
}

// Type icon component
const TypeIcon = ({ type, className }: { type: Memory['type']; className?: string }) => {
  switch (type) {
    case 'conversation':
      return (
        <svg className={cn("h-4 w-4", className)} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
      );
    case 'case':
      return (
        <svg className={cn("h-4 w-4", className)} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
      );
    case 'unified':
      return (
        <svg className={cn("h-4 w-4", className)} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      );
    case 'fact':
      return (
        <svg className={cn("h-4 w-4", className)} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      );
    case 'preference':
      return (
        <svg className={cn("h-4 w-4", className)} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364L7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636L-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
        </svg>
      );
    case 'context':
      return (
        <svg className={cn("h-4 w-4", className)} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8 1.79 8 4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
        </svg>
      );
    default:
      return (
        <svg className={cn("h-4 w-4", className)} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
      );
  }
};

// Status icon component
const StatusIcon = ({ status, className }: { status: Memory['status']; className?: string }) => {
  switch (status) {
    case 'active':
      return (
        <svg className={cn("h-4 w-4", className)} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      );
    case 'archived':
      return (
        <svg className={cn("h-4 w-4", className)} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
        </svg>
      );
    case 'deleted':
      return (
        <svg className={cn("h-4 w-4", className)} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>
      );
    case 'processing':
      return (
        <svg className={cn("h-4 w-4", className)} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      );
    default:
      return (
        <svg className={cn("h-4 w-4", className)} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
      );
  }
};

// Priority icon component
const PriorityIcon = ({ priority, className }: { priority: Memory['priority']; className?: string }) => {
  switch (priority) {
    case 'critical':
      return (
        <svg className={cn("h-4 w-4", className)} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      );
    case 'high':
      return (
        <svg className={cn("h-4 w-4", className)} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
      );
    case 'medium':
      return (
        <svg className={cn("h-4 w-4", className)} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      );
    case 'low':
      return (
        <svg className={cn("h-4 w-4", className)} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
        </svg>
      );
    default:
      return (
        <svg className={cn("h-4 w-4", className)} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
        </svg>
      );
  }
};

export function MemoryDetails({ 
  memory, 
  onClose, 
  onAction, 
  onEdit,
  showActions = true, 
  className 
}: MemoryDetailsProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(memory.content);

  const handleAction = (action: MemoryActionPayload['action'], data?: Record<string, unknown> | unknown) => {
    onAction?.({ memoryId: memory.id, action, data });
  };

  const handleEdit = () => {
    setIsEditing(true);
    setEditContent(memory.content);
    onEdit?.(memory);
  };

  const handleSave = () => {
    handleAction('edit', { content: editContent });
    setIsEditing(false);
  };

  const handleCancel = () => {
    setIsEditing(false);
    setEditContent(memory.content);
  };

  const isExpired = memory.expiresAt && new Date(memory.expiresAt).getTime() < Date.now();
  const isNearExpiry = memory.expiresAt &&
    new Date(memory.expiresAt).getTime() > Date.now() &&
    new Date(memory.expiresAt).getTime() < Date.now() + (7 * 24 * 60 * 60 * 1000);

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3 flex-1">
              <TypeIcon type={memory.type} />
              <div>
                <CardTitle className="text-lg">{memory.title || 'Memory Details'}</CardTitle>
                <div className="flex items-center gap-2 mt-1">
                  <Badge className={cn("text-xs", getTypeColor(memory.type))}>
                    {memory.type}
                  </Badge>
                  <Badge className={cn("text-xs", getStatusColor(memory.status))}>
                    <StatusIcon status={memory.status} className="h-3 w-3 mr-1" />
                    {memory.status}
                  </Badge>
                  <Badge className={cn("text-xs", getPriorityColor(memory.priority))}>
                    <PriorityIcon priority={memory.priority} className="h-3 w-3 mr-1" />
                    {memory.priority}
                  </Badge>
                  {memory.metadata.isEncrypted && (
                    <Badge className="text-xs bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200">
                      <svg className="h-3 w-3 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                      </svg>
                      Encrypted
                    </Badge>
                  )}
                  {isExpired && (
                    <Badge className="text-xs bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
                      <svg className="h-3 w-3 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                      </svg>
                      Expired
                    </Badge>
                  )}
                  {isNearExpiry && !isExpired && (
                    <Badge className="text-xs bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200">
                      <svg className="h-3 w-3 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      Expires Soon
                    </Badge>
                  )}
                </div>
              </div>
            </div>
            
            {showActions && (
              <div className="flex items-center gap-2">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" size="sm">
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                      </svg>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => handleAction('view')}>
                      <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                      View Details
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={handleEdit}>
                      <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828L8.586-8.586z" />
                      </svg>
                      Edit
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={() => handleAction('copy')}>
                      <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                      Copy
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => handleAction('export')}>
                      <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      Export
                    </DropdownMenuItem>
                    {memory.status === 'active' && (
                      <DropdownMenuItem onClick={() => handleAction('archive')}>
                        <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
                        </svg>
                        Archive
                      </DropdownMenuItem>
                    )}
                    {memory.status === 'archived' && (
                      <DropdownMenuItem onClick={() => handleAction('restore')}>
                        <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
                        </svg>
                        Restore
                      </DropdownMenuItem>
                    )}
                    <DropdownMenuSeparator />
                    <DropdownMenuItem 
                      onClick={() => handleAction('delete')}
                      className="text-destructive"
                    >
                      <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                      Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
                
                {onClose && (
                  <Button variant="outline" size="sm" onClick={onClose}>
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                    Close
                  </Button>
                )}
              </div>
            )}
          </div>
        </CardHeader>
      </Card>

      {/* Content */}
      <Card>
        <CardHeader>
          <CardTitle>Content</CardTitle>
        </CardHeader>
        <CardContent>
          {isEditing ? (
            <div className="space-y-4">
              <textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                className="w-full min-h-[200px] p-3 border rounded-md resize-none focus:outline-none focus:ring-2 focus:ring-ring"
                rows={8}
              />
              <div className="flex gap-2">
                <Button onClick={handleSave}>
                  <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7l-7-7-4 4z" />
                  </svg>
                  Save
                </Button>
                <Button variant="outline" onClick={handleCancel}>
                  <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  Cancel
                </Button>
              </div>
            </div>
          ) : (
            <div className="whitespace-pre-wrap break-words text-sm">
              {memory.content}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Metadata */}
      <Card>
        <CardHeader>
          <CardTitle>Metadata</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Basic Info */}
            <div className="space-y-3">
              <h3 className="font-medium">Basic Information</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="font-medium">ID:</span>
                  <span className="font-mono text-muted-foreground">{memory.id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-medium">Version:</span>
                  <span className="font-mono text-muted-foreground">{memory.version}</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-medium">Size:</span>
                  <span className="font-mono text-muted-foreground">
                    {memory.size > 1024 
                      ? `${(memory.size / 1024).toFixed(1)}KB`
                      : `${memory.size}B`
                    }
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="font-medium">Hash:</span>
                  <span className="font-mono text-muted-foreground text-xs">{memory.hash}</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-medium">User ID:</span>
                  <span className="font-mono text-muted-foreground">{memory.userId}</span>
                </div>
                {memory.tenantId && (
                  <div className="flex justify-between">
                    <span className="font-medium">Tenant ID:</span>
                    <span className="font-mono text-muted-foreground">{memory.tenantId}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Dates */}
            <div className="space-y-3">
              <h3 className="font-medium">Dates</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="font-medium">Created:</span>
                  <span className="text-muted-foreground">{formatDate(memory.createdAt)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-medium">Updated:</span>
                  <span className="text-muted-foreground">{formatDate(memory.updatedAt)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-medium">Accessed:</span>
                  <span className="text-muted-foreground">
                    {memory.accessedAt ? formatDate(memory.accessedAt) : 'Never'}
                  </span>
                </div>
                {memory.expiresAt && (
                  <div className="flex justify-between">
                    <span className="font-medium">Expires:</span>
                    <span className={cn(
                      "text-muted-foreground",
                      isExpired && "text-destructive",
                      isNearExpiry && !isExpired && "text-orange-500"
                    )}>
                      {formatDate(memory.expiresAt)}
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Memory Metrics */}
            <div className="space-y-3">
              <h3 className="font-medium">Memory Metrics</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="font-medium">Confidence:</span>
                  <div className="flex items-center gap-2">
                    <div className="w-24 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div 
                        className={cn(
                          "h-2 rounded-full",
                          memory.metadata.confidence && memory.metadata.confidence >= 0.8 ? "bg-green-500" :
                          memory.metadata.confidence && memory.metadata.confidence >= 0.6 ? "bg-yellow-500" :
                          memory.metadata.confidence && memory.metadata.confidence >= 0.4 ? "bg-orange-500" :
                          "bg-red-500"
                        )}
                        style={{ width: `${(memory.metadata.confidence || 0) * 100}%` }}
                      />
                    </div>
                    <span className="text-muted-foreground">
                      {memory.metadata.confidence ? `${Math.round(memory.metadata.confidence * 100)}%` : 'N/A'}
                    </span>
                  </div>
                </div>
                <div className="flex justify-between">
                  <span className="font-medium">Importance:</span>
                  <div className="flex items-center gap-2">
                    <div className="w-24 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div 
                        className={cn(
                          "h-2 rounded-full",
                          memory.metadata.importance && memory.metadata.importance >= 0.8 ? "bg-purple-500" :
                          memory.metadata.importance && memory.metadata.importance >= 0.6 ? "bg-blue-500" :
                          memory.metadata.importance && memory.metadata.importance >= 0.4 ? "bg-indigo-500" :
                          "bg-gray-500"
                        )}
                        style={{ width: `${(memory.metadata.importance || 0) * 100}%` }}
                      />
                    </div>
                    <span className="text-muted-foreground">
                      {memory.metadata.importance ? `${Math.round(memory.metadata.importance * 100)}%` : 'N/A'}
                    </span>
                  </div>
                </div>
                <div className="flex justify-between">
                  <span className="font-medium">Access Count:</span>
                  <span className="text-muted-foreground">{memory.metadata.accessCount || 0}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Organization */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Source */}
            <div className="space-y-3">
              <h3 className="font-medium">Source</h3>
              <div className="text-sm text-muted-foreground">
                {memory.metadata.source || 'Unknown'}
              </div>
            </div>

            {/* Category */}
            <div className="space-y-3">
              <h3 className="font-medium">Category</h3>
              <div className="text-sm text-muted-foreground">
                {memory.metadata.category || 'None'}
              </div>
            </div>

            {/* Folder */}
            <div className="space-y-3">
              <h3 className="font-medium">Folder</h3>
              <div className="text-sm text-muted-foreground">
                {memory.metadata.folder || 'None'}
              </div>
            </div>

            {/* Collection */}
            <div className="space-y-3">
              <h3 className="font-medium">Collection</h3>
              <div className="text-sm text-muted-foreground">
                {memory.metadata.collection || 'None'}
              </div>
            </div>
          </div>

          {/* Tags */}
          {memory.metadata.tags && memory.metadata.tags.length > 0 && (
            <div className="space-y-3">
              <h3 className="font-medium">Tags</h3>
              <div className="flex flex-wrap gap-2">
                {memory.metadata.tags.map(tag => (
                  <Badge key={tag} className="text-xs bg-secondary text-secondary-foreground">
                    {tag}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Related IDs */}
          {memory.metadata.relatedIds && memory.metadata.relatedIds.length > 0 && (
            <div className="space-y-3">
              <h3 className="font-medium">Related Memories</h3>
              <div className="space-y-1">
                {memory.metadata.relatedIds.slice(0, 5).map(relatedId => (
                  <div key={relatedId} className="flex items-center gap-2 text-sm">
                    <span className="font-mono text-muted-foreground">{relatedId}</span>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => handleAction('view', { relatedId })}
                    >
                      <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    </Button>
                  </div>
                ))}
                {memory.metadata.relatedIds.length > 5 && (
                  <div className="text-sm text-muted-foreground">
                    +{memory.metadata.relatedIds.length - 5} more related memories
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Additional Metadata */}
          {memory.metadata.context && (
            <div className="space-y-3">
              <h3 className="font-medium">Context</h3>
              <div className="text-sm text-muted-foreground">
                {memory.metadata.context}
              </div>
            </div>
          )}

          {memory.metadata.extractionMethod && (
            <div className="space-y-3">
              <h3 className="font-medium">Extraction Method</h3>
              <div className="text-sm text-muted-foreground">
                {memory.metadata.extractionMethod}
              </div>
            </div>
          )}

          {memory.metadata.processingStatus && (
            <div className="space-y-3">
              <h3 className="font-medium">Processing Status</h3>
              <div className="flex items-center gap-2">
                <Badge className={cn(
                  "text-xs",
                  memory.metadata.processingStatus === 'completed' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' :
                  memory.metadata.processingStatus === 'processing' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' :
                  memory.metadata.processingStatus === 'failed' ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' :
                  'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
                )}>
                  {memory.metadata.processingStatus}
                </Badge>
                {memory.metadata.processingError && (
                  <span className="text-sm text-destructive">
                    {memory.metadata.processingError}
                  </span>
                )}
              </div>
            </div>
          )}

          {memory.metadata.indexingStatus && (
            <div className="space-y-3">
              <h3 className="font-medium">Indexing Status</h3>
              <div className="flex items-center gap-2">
                <Badge className={cn(
                  "text-xs",
                  memory.metadata.indexingStatus === 'indexed' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' :
                  memory.metadata.indexingStatus === 'indexing' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' :
                  memory.metadata.indexingStatus === 'failed' ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' :
                  'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
                )}>
                  {memory.metadata.indexingStatus}
                </Badge>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default MemoryDetails;
