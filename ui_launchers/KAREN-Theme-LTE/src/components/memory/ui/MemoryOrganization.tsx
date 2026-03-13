"use client";

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { MemoryOrganizationProps } from '../types';

// Icon components
const FolderPlus = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>
);

const FolderOpen = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
  </svg>
);

const Tag = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
  </svg>
);

const Hash = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
  </svg>
);

const Layers = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
  </svg>
);

const Plus = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
  </svg>
);

const X = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
  </svg>
);

export function MemoryOrganization({
  folders,
  collections,
  tags,
  categories,
  onFolderCreate,
  onCollectionCreate,
  onFolderSelect,
  onCollectionSelect,
  onTagSelect,
  onCategorySelect,
  className
}: MemoryOrganizationProps) {
  const [activeTab, setActiveTab] = useState<'folders' | 'collections' | 'tags' | 'categories'>('folders');
  const [newFolderName, setNewFolderName] = useState('');
  const [newCollectionName, setNewCollectionName] = useState('');
  const [showNewFolderForm, setShowNewFolderForm] = useState(false);
  const [showNewCollectionForm, setShowNewCollectionForm] = useState(false);

  const handleCreateFolder = () => {
    if (newFolderName.trim()) {
      onFolderCreate(newFolderName.trim());
      setNewFolderName('');
      setShowNewFolderForm(false);
    }
  };

  const handleCreateCollection = () => {
    if (newCollectionName.trim()) {
      onCollectionCreate(newCollectionName.trim());
      setNewCollectionName('');
      setShowNewCollectionForm(false);
    }
  };

  const tabs: Array<{
    id: 'folders' | 'collections' | 'tags' | 'categories';
    label: string;
    icon: React.FC<{ className?: string }>;
    count: number;
  }> = [
    { id: 'folders', label: 'Folders', icon: FolderOpen, count: folders.length },
    { id: 'collections', label: 'Collections', icon: Layers, count: collections.length },
    { id: 'tags', label: 'Tags', icon: Tag, count: tags.length },
    { id: 'categories', label: 'Categories', icon: Hash, count: categories.length },
  ];

  return (
    <div className={cn("bg-card rounded-lg border", className)}>
      {/* Header with tabs */}
      <div className="border-b p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Memory Organization</h2>
          <div className="flex items-center gap-2">
            {activeTab === 'folders' && (
              <button
                className={cn(
                  "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 hover:bg-primary hover:text-primary-foreground h-8 px-3 gap-1"
                )}
                onClick={() => setShowNewFolderForm(!showNewFolderForm)}
              >
                <FolderPlus className="h-4 w-4" />
                New Folder
              </button>
            )}
            {activeTab === 'collections' && (
              <button
                className={cn(
                  "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 hover:bg-primary hover:text-primary-foreground h-8 px-3 gap-1"
                )}
                onClick={() => setShowNewCollectionForm(!showNewCollectionForm)}
              >
                <Plus className="h-4 w-4" />
                New Collection
              </button>
            )}
          </div>
        </div>

        {/* Tab navigation */}
        <div className="flex space-x-1">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              className={cn(
                "flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-md transition-colors",
                activeTab === tab.id
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted"
              )}
              onClick={() => setActiveTab(tab.id)}
            >
              <tab.icon className="h-4 w-4" />
              {tab.label}
              <span className="text-xs bg-muted text-muted-foreground px-2 py-0.5 rounded-full">
                {tab.count}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Content area */}
      <div className="p-4">
        {/* New folder form */}
        {activeTab === 'folders' && showNewFolderForm && (
          <div className="mb-4 p-3 bg-muted rounded-md">
            <div className="flex items-center gap-2">
              <input
                type="text"
                placeholder="Enter folder name..."
                className="flex-1 px-3 py-2 text-sm bg-background border rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                value={newFolderName}
                onChange={(e) => setNewFolderName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleCreateFolder()}
                autoFocus
              />
              <button
                className={cn(
                  "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-8 px-3"
                )}
                onClick={handleCreateFolder}
              >
                Create
              </button>
              <button
                className={cn(
                  "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 hover:bg-accent hover:text-accent-foreground h-8 px-3"
                )}
                onClick={() => {
                  setShowNewFolderForm(false);
                  setNewFolderName('');
                }}
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}

        {/* New collection form */}
        {activeTab === 'collections' && showNewCollectionForm && (
          <div className="mb-4 p-3 bg-muted rounded-md">
            <div className="flex items-center gap-2">
              <input
                type="text"
                placeholder="Enter collection name..."
                className="flex-1 px-3 py-2 text-sm bg-background border rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                value={newCollectionName}
                onChange={(e) => setNewCollectionName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleCreateCollection()}
                autoFocus
              />
              <button
                className={cn(
                  "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-8 px-3"
                )}
                onClick={handleCreateCollection}
              >
                Create
              </button>
              <button
                className={cn(
                  "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 hover:bg-accent hover:text-accent-foreground h-8 px-3"
                )}
                onClick={() => {
                  setShowNewCollectionForm(false);
                  setNewCollectionName('');
                }}
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}

        {/* Folders tab */}
        {activeTab === 'folders' && (
          <div className="space-y-2">
            {folders.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <FolderOpen className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>No folders yet</p>
                <p className="text-sm">Create your first folder to organize memories</p>
              </div>
            ) : (
              folders.map((folder) => (
                <div
                  key={folder}
                  className="flex items-center justify-between p-3 rounded-md hover:bg-muted cursor-pointer transition-colors"
                  onClick={() => onFolderSelect(folder)}
                >
                  <div className="flex items-center gap-2">
                    <FolderOpen className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm font-medium">{folder}</span>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {/* This would show the count of memories in this folder */}
                    0 memories
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Collections tab */}
        {activeTab === 'collections' && (
          <div className="space-y-2">
            {collections.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Layers className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>No collections yet</p>
                <p className="text-sm">Create your first collection to group related memories</p>
              </div>
            ) : (
              collections.map((collection) => (
                <div
                  key={collection}
                  className="flex items-center justify-between p-3 rounded-md hover:bg-muted cursor-pointer transition-colors"
                  onClick={() => onCollectionSelect(collection)}
                >
                  <div className="flex items-center gap-2">
                    <Layers className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm font-medium">{collection}</span>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {/* This would show the count of memories in this collection */}
                    0 memories
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Tags tab */}
        {activeTab === 'tags' && (
          <div className="space-y-2">
            {tags.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Tag className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>No tags yet</p>
                <p className="text-sm">Tags will appear here as you add them to memories</p>
              </div>
            ) : (
              <div className="flex flex-wrap gap-2">
                {tags.map((tag) => (
                  <button
                    key={tag}
                    className={cn(
                      "inline-flex items-center gap-1 px-3 py-1 text-sm bg-muted hover:bg-muted/80 rounded-full transition-colors"
                    )}
                    onClick={() => onTagSelect(tag)}
                  >
                    <Tag className="h-3 w-3" />
                    {tag}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Categories tab */}
        {activeTab === 'categories' && (
          <div className="space-y-2">
            {categories.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Hash className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>No categories yet</p>
                <p className="text-sm">Categories will appear here as you add them to memories</p>
              </div>
            ) : (
              <div className="flex flex-wrap gap-2">
                {categories.map((category) => (
                  <button
                    key={category}
                    className={cn(
                      "inline-flex items-center gap-1 px-3 py-1 text-sm bg-muted hover:bg-muted/80 rounded-full transition-colors"
                    )}
                    onClick={() => onCategorySelect(category)}
                  >
                    <Hash className="h-3 w-3" />
                    {category}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default MemoryOrganization;
