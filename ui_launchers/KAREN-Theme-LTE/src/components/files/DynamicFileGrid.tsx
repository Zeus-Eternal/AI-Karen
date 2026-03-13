"use client";

import { useState, useEffect, useMemo, useCallback, type DragEvent } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Plus,
  Download,
  Trash2,
  RefreshCw,
  FileText,
  FileImage,
  FileVideo,
  FileAudio,
  FileCode,
  FileArchive,
  Upload,
  Folder,
  Calendar,
  User,
  HardDrive,
  Clock,
  X
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { generateRandomId } from '@/lib/id-generator';

// File data types
interface FileEntry {
  id: string;
  name: string;
  type: 'document' | 'image' | 'video' | 'audio' | 'code' | 'archive' | 'other';
  mimeType: string;
  size: number;
  url?: string;
  path: string;
  folder: string;
  tags: string[];
  permissions: {
    read: string[];
    write: string[];
    admin: string[];
  };
  uploadedBy: string;
  uploadedByName: string;
  createdAt: string;
  updatedAt: string;
  lastAccessed: string;
  accessCount: number;
  isPublic: boolean;
  metadata: {
    checksum?: string;
    version?: number;
    description?: string;
  };
}

interface FileUploadProgress {
  id: string;
  name: string;
  progress: number;
  status: 'uploading' | 'completed' | 'error';
  error?: string;
}

interface FileGridProps {
  className?: string;
}

type FileSortBy = 'createdAt' | 'updatedAt' | 'name' | 'size';
type FileSortOrder = 'asc' | 'desc';

const isFileSortBy = (value: string): value is FileSortBy =>
  value === 'createdAt' || value === 'updatedAt' || value === 'name' || value === 'size';

const isFileSortOrder = (value: string): value is FileSortOrder =>
  value === 'asc' || value === 'desc';

// Utility function for date formatting
function formatDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'UTC'
  });
}

// Utility function for file size formatting
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Utility function for file type icon
function getFileIcon(type: string) {
  switch (type) {
    case 'document': return FileText;
    case 'image': return FileImage;
    case 'video': return FileVideo;
    case 'audio': return FileAudio;
    case 'code': return FileCode;
    case 'archive': return FileArchive;
    default: return FileText;
  }
}

// Utility function for file type color
function getFileTypeColor(type: string): string {
  switch (type) {
    case 'document': return 'bg-blue-100 text-blue-800';
    case 'image': return 'bg-green-100 text-green-800';
    case 'video': return 'bg-purple-100 text-purple-800';
    case 'audio': return 'bg-orange-100 text-orange-800';
    case 'code': return 'bg-red-100 text-red-800';
    case 'archive': return 'bg-gray-100 text-gray-800';
    default: return 'bg-gray-100 text-gray-800';
  }
}

export default function DynamicFileGrid({ className }: FileGridProps) {
  const [files, setFiles] = useState<FileEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [filterType, setFilterType] = useState<string>('all');
  const [filterFolder, setFilterFolder] = useState<string>('all');
  const [sortBy, setSortBy] = useState<FileSortBy>('createdAt');
  const [sortOrder, setSortOrder] = useState<FileSortOrder>('desc');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [uploadProgress, setUploadProgress] = useState<FileUploadProgress[]>([]);
  const [dragActive, setDragActive] = useState(false);

  // Mock data - replace with actual API call
  useEffect(() => {
    const mockFiles: FileEntry[] = [
      {
        id: '1',
        name: 'Project Proposal.pdf',
        type: 'document',
        mimeType: 'application/pdf',
        size: 2048576,
        url: '/files/project-proposal.pdf',
        path: '/documents/projects/',
        folder: 'projects',
        tags: ['proposal', 'project', 'q1-2024'],
        permissions: {
          read: ['user-123', 'user-456', 'admin'],
          write: ['user-123', 'admin'],
          admin: ['admin']
        },
        uploadedBy: 'user-123',
        uploadedByName: 'John Doe',
        createdAt: new Date(Date.now() - 86400000).toISOString(),
        updatedAt: new Date(Date.now() - 3600000).toISOString(),
        lastAccessed: new Date(Date.now() - 1800000).toISOString(),
        accessCount: 15,
        isPublic: false,
        metadata: {
          checksum: 'sha256:abc123...',
          version: 1,
          description: 'Q1 2024 project proposal document'
        }
      },
      {
        id: '2',
        name: 'Team Photo.jpg',
        type: 'image',
        mimeType: 'image/jpeg',
        size: 3145728,
        url: '/files/team-photo.jpg',
        path: '/images/events/',
        folder: 'events',
        tags: ['team', 'photo', 'event'],
        permissions: {
          read: ['user-123', 'user-456', 'user-789', 'admin'],
          write: ['user-123', 'admin'],
          admin: ['admin']
        },
        uploadedBy: 'user-456',
        uploadedByName: 'Jane Smith',
        createdAt: new Date(Date.now() - 172800000).toISOString(),
        updatedAt: new Date(Date.now() - 86400000).toISOString(),
        lastAccessed: new Date(Date.now() - 7200000).toISOString(),
        accessCount: 8,
        isPublic: true,
        metadata: {
          checksum: 'sha256:def456...',
          version: 1,
          description: 'Team building event photo'
        }
      },
      {
        id: '3',
        name: 'Demo Video.mp4',
        type: 'video',
        mimeType: 'video/mp4',
        size: 52428800,
        url: '/files/demo-video.mp4',
        path: '/videos/demos/',
        folder: 'demos',
        tags: ['demo', 'video', 'presentation'],
        permissions: {
          read: ['user-123', 'admin'],
          write: ['user-123', 'admin'],
          admin: ['admin']
        },
        uploadedBy: 'user-123',
        uploadedByName: 'John Doe',
        createdAt: new Date(Date.now() - 259200000).toISOString(),
        updatedAt: new Date(Date.now() - 172800000).toISOString(),
        lastAccessed: new Date(Date.now() - 3600000).toISOString(),
        accessCount: 12,
        isPublic: false,
        metadata: {
          checksum: 'sha256:ghi789...',
          version: 2,
          description: 'Product demonstration video'
        }
      },
      {
        id: '4',
        name: 'Source Code.zip',
        type: 'archive',
        mimeType: 'application/zip',
        size: 10485760,
        url: '/files/source-code.zip',
        path: '/archives/source/',
        folder: 'source',
        tags: ['source', 'code', 'backup'],
        permissions: {
          read: ['user-123', 'user-789', 'admin'],
          write: ['user-123', 'admin'],
          admin: ['admin']
        },
        uploadedBy: 'user-789',
        uploadedByName: 'Bob Johnson',
        createdAt: new Date(Date.now() - 604800000).toISOString(),
        updatedAt: new Date(Date.now() - 86400000).toISOString(),
        lastAccessed: new Date(Date.now() - 10800000).toISOString(),
        accessCount: 6,
        isPublic: false,
        metadata: {
          checksum: 'sha256:jkl012...',
          version: 1,
          description: 'Source code backup'
        }
      },
      {
        id: '5',
        name: 'Configuration.json',
        type: 'code',
        mimeType: 'application/json',
        size: 4096,
        url: '/files/configuration.json',
        path: '/config/',
        folder: 'config',
        tags: ['config', 'settings', 'json'],
        permissions: {
          read: ['user-123', 'admin'],
          write: ['admin'],
          admin: ['admin']
        },
        uploadedBy: 'admin',
        uploadedByName: 'System Admin',
        createdAt: new Date(Date.now() - 432000000).toISOString(),
        updatedAt: new Date(Date.now() - 172800000).toISOString(),
        lastAccessed: new Date(Date.now() - 900000).toISOString(),
        accessCount: 20,
        isPublic: false,
        metadata: {
          checksum: 'sha256:mno345...',
          version: 3,
          description: 'Application configuration file'
        }
      }
    ];

    setFiles(mockFiles);
    setLoading(false);
  }, []);

  // Get unique folders
  const folders = useMemo(() => {
    const folders = new Set(files.map(f => f.folder));
    return Array.from(folders);
  }, [files]);

  // Filter and sort files
  const filteredFiles = useMemo(() => {
    let filtered = files;

    // Apply search filter
    if (searchQuery) {
      filtered = filtered.filter(file =>
        file.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        file.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase())) ||
        file.folder.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Apply type filter
    if (filterType !== 'all') {
      filtered = filtered.filter(file => file.type === filterType);
    }

    // Apply folder filter
    if (filterFolder !== 'all') {
      filtered = filtered.filter(file => file.folder === filterFolder);
    }

    // Apply sorting
    filtered.sort((a, b) => {
      const aValue = a[sortBy];
      const bValue = b[sortBy];
      
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortOrder === 'asc' 
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }
      
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortOrder === 'asc' ? aValue - bValue : bValue - aValue;
      }
      
      return 0;
    });

    return filtered;
  }, [files, searchQuery, filterType, filterFolder, sortBy, sortOrder]);

  // Drag and drop handlers
  const handleDrag = useCallback((e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  }, []);

  const handleFiles = (fileList: FileList) => {
    const newUploads: FileUploadProgress[] = Array.from(fileList).map(file => ({
      id: generateRandomId('upload'),
      name: file.name,
      progress: 0,
      status: 'uploading' as const
    }));
    
    setUploadProgress(prev => [...prev, ...newUploads]);
    
    // Simulate upload progress
    newUploads.forEach(upload => {
      const interval = setInterval(() => {
        setUploadProgress(prev => 
          prev.map(u => {
            if (u.id === upload.id) {
              const newProgress = u.progress + 10;
              if (newProgress >= 100) {
                clearInterval(interval);
                return { ...u, progress: 100, status: 'completed' as const };
              }
              return { ...u, progress: newProgress };
            }
            return u;
          })
        );
      }, 200);
    });
  };

  const handleRefresh = () => {
    setLoading(true);
    // Simulate refresh
    setTimeout(() => {
      // In real implementation, this would fetch fresh data
      setLoading(false);
    }, 1000);
  };

  const handleExport = () => {
    // In real implementation, this would export file data
    const data = {
      files: filteredFiles,
      exportedAt: new Date().toISOString(),
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `file-data-${formatDate(new Date())}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleDeleteSelected = () => {
    // In real implementation, this would delete selected files
    setFiles(files.filter(f => !selectedFiles.includes(f.id)));
    setSelectedFiles([]);
  };

  const toggleFileSelection = (fileId: string) => {
    setSelectedFiles(prev =>
      prev.includes(fileId)
        ? prev.filter(id => id !== fileId)
        : [...prev, fileId]
    );
  };

  const toggleAllSelection = () => {
    if (selectedFiles.length === filteredFiles.length) {
      setSelectedFiles([]);
    } else {
      setSelectedFiles(filteredFiles.map(f => f.id));
    }
  };

  const removeUploadProgress = (id: string) => {
    setUploadProgress(prev => prev.filter(u => u.id !== id));
  };

  return (
    <div className={cn("space-y-6", className)}>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Dynamic File Grid
          </CardTitle>
          <CardDescription>
            Advanced file management with drag-and-drop upload and permission controls
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* File Upload Area */}
          <div className="mb-6">
            <div
              className={cn(
                "border-2 border-dashed rounded-lg p-6 text-center transition-colors",
                dragActive ? "border-primary bg-primary/5" : "border-border"
              )}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <Upload className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
              <p className="text-sm text-muted-foreground mb-2">
                Drag and drop files here, or click to browse
              </p>
              <Button variant="outline" size="sm">
                <Plus className="h-4 w-4 mr-2" />
                Select Files
              </Button>
            </div>
            
            {/* Upload Progress */}
            {uploadProgress.length > 0 && (
              <div className="mt-4 space-y-2">
                <h4 className="text-sm font-medium">Upload Progress</h4>
                {uploadProgress.map(upload => (
                  <div key={upload.id} className="flex items-center gap-2 p-2 border rounded">
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm">{upload.name}</span>
                        <span className="text-xs text-muted-foreground">
                          {upload.status === 'uploading' ? `${upload.progress}%` : 
                           upload.status === 'completed' ? 'Completed' : 'Error'}
                        </span>
                      </div>
                      <Progress value={upload.progress} className="h-1" />
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeUploadProgress(upload.id)}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* File Controls */}
          <div className="flex flex-col gap-4 mb-6">
            <div className="flex gap-2">
              <Input
                placeholder="Search files..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="flex-1"
              />
              
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                disabled={loading}
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                onClick={handleExport}
              >
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
            </div>
            
            <div className="flex flex-wrap gap-2">
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="px-3 py-1 border border-border rounded-md text-sm"
              >
                <option value="all">All Types</option>
                <option value="document">Documents</option>
                <option value="image">Images</option>
                <option value="video">Videos</option>
                <option value="audio">Audio</option>
                <option value="code">Code</option>
                <option value="archive">Archives</option>
              </select>
              
              <select
                value={filterFolder}
                onChange={(e) => setFilterFolder(e.target.value)}
                className="px-3 py-1 border border-border rounded-md text-sm"
              >
                <option value="all">All Folders</option>
                {folders.map(folder => (
                  <option key={folder} value={folder}>{folder}</option>
                ))}
              </select>
              
              <select
                value={`${sortBy}-${sortOrder}`}
                onChange={(e) => {
                  const [sort, order] = e.target.value.split('-');

                  if (isFileSortBy(sort)) {
                    setSortBy(sort);
                  }

                  if (isFileSortOrder(order)) {
                    setSortOrder(order);
                  }
                }}
                className="px-3 py-1 border border-border rounded-md text-sm"
              >
                <option value="createdAt-desc">Newest First</option>
                <option value="createdAt-asc">Oldest First</option>
                <option value="name-asc">Name (A-Z)</option>
                <option value="name-desc">Name (Z-A)</option>
                <option value="size-desc">Largest First</option>
                <option value="size-asc">Smallest First</option>
              </select>
              
              <div className="flex gap-1 ml-auto">
                <Button
                  variant={viewMode === 'grid' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setViewMode('grid')}
                >
                  Grid
                </Button>
                <Button
                  variant={viewMode === 'list' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setViewMode('list')}
                >
                  List
                </Button>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={toggleAllSelection}
                disabled={filteredFiles.length === 0}
              >
                {selectedFiles.length === filteredFiles.length ? 'Deselect All' : 'Select All'}
              </Button>
              
              {selectedFiles.length > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleDeleteSelected}
                  className="text-destructive"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete Selected ({selectedFiles.length})
                </Button>
              )}
              
              <Badge className="text-xs bg-secondary text-secondary-foreground">
                {filteredFiles.length} files
              </Badge>
            </div>
          </div>

          {/* File Grid/List */}
          {viewMode === 'grid' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredFiles.map((file) => {
                const FileIcon = getFileIcon(file.type);
                return (
                  <Card 
                    key={file.id} 
                    className={cn(
                      "cursor-pointer transition-all hover:shadow-md",
                      selectedFiles.includes(file.id) && "ring-2 ring-primary"
                    )}
                    onClick={() => toggleFileSelection(file.id)}
                  >
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-2">
                          <FileIcon className="h-5 w-5 text-muted-foreground" />
                          <Badge className={cn("text-xs", getFileTypeColor(file.type))}>
                            {file.type}
                          </Badge>
                          {file.isPublic && (
                            <Badge className="text-xs bg-green-100 text-green-800">
                              Public
                            </Badge>
                          )}
                        </div>
                        <input
                          type="checkbox"
                          checked={selectedFiles.includes(file.id)}
                          onChange={() => toggleFileSelection(file.id)}
                          className="rounded"
                        />
                      </div>
                    </CardHeader>
                    <CardContent className="pt-0">
                      <h4 className="font-medium text-sm mb-2 truncate">{file.name}</h4>
                      
                      <div className="flex flex-wrap gap-1 mb-3">
                        {file.tags.slice(0, 2).map(tag => (
                          <Badge key={tag} className="text-xs border border-current">
                            {tag}
                          </Badge>
                        ))}
                        {file.tags.length > 2 && (
                          <Badge className="text-xs border border-current">
                            +{file.tags.length - 2}
                          </Badge>
                        )}
                      </div>
                      
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <HardDrive className="h-3 w-3" />
                          {formatFileSize(file.size)}
                        </div>
                        <div className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {formatDate(file.createdAt)}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          ) : (
            <div className="space-y-2">
              {filteredFiles.map((file) => {
                const FileIcon = getFileIcon(file.type);
                return (
                  <Card 
                    key={file.id} 
                    className={cn(
                      "cursor-pointer transition-all hover:shadow-md",
                      selectedFiles.includes(file.id) && "ring-2 ring-primary"
                    )}
                    onClick={() => toggleFileSelection(file.id)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-3 flex-1">
                          <FileIcon className="h-5 w-5 text-muted-foreground" />
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <h4 className="font-medium text-sm">{file.name}</h4>
                              <Badge className={cn("text-xs", getFileTypeColor(file.type))}>
                                {file.type}
                              </Badge>
                              {file.isPublic && (
                                <Badge className="text-xs bg-green-100 text-green-800">
                                  Public
                                </Badge>
                              )}
                            </div>
                            
                            <div className="flex items-center gap-4 text-xs text-muted-foreground">
                              <div className="flex items-center gap-1">
                                <Folder className="h-3 w-3" />
                                {file.folder}
                              </div>
                              <div className="flex items-center gap-1">
                                <HardDrive className="h-3 w-3" />
                                {formatFileSize(file.size)}
                              </div>
                              <div className="flex items-center gap-1">
                                <User className="h-3 w-3" />
                                {file.uploadedByName}
                              </div>
                              <div className="flex items-center gap-1">
                                <Calendar className="h-3 w-3" />
                                {formatDate(file.createdAt)}
                              </div>
                              <div className="flex items-center gap-1">
                                <Clock className="h-3 w-3" />
                                {file.accessCount} accesses
                              </div>
                            </div>
                          </div>
                        </div>
                        
                        <input
                          type="checkbox"
                          checked={selectedFiles.includes(file.id)}
                          onChange={() => toggleFileSelection(file.id)}
                          className="rounded ml-4"
                        />
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}

          {/* Empty State */}
          {filteredFiles.length === 0 && !loading && (
            <div className="text-center py-8">
              <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium">No files found</h3>
              <p className="text-muted-foreground">
                {searchQuery 
                  ? `No files matching "${searchQuery}"`
                  : 'No files available'
                }
              </p>
              <Button onClick={handleRefresh} className="mt-4">
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh Data
              </Button>
            </div>
          )}

          {/* Loading State */}
          {loading && (
            <div className="text-center py-8">
              <RefreshCw className="h-8 w-8 mx-auto animate-spin text-muted-foreground" />
              <p className="text-muted-foreground mt-2">Loading files...</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
