import React, { useState, useEffect, useCallback } from 'react';
import { ErrorBoundary } from '@/components/error-handling/ErrorBoundary';
import { 
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';
import FileUploadDropzone from './FileUploadDropzone';
import FileMetadataGrid, { FileMetadata } from './FileMetadataGrid';
import MultimediaPreview from './MultimediaPreview';
import FilePermissionManager, { FilePermission } from './FilePermissionManager';
'use client';


  Files, 
  Upload, 
  Grid, 
  List, 
  Eye, 
  Settings, 
  Filter,
  Search,
  RefreshCw,
  Download,
  Trash2,
  Share2,
  MoreHorizontal
} from 'lucide-react';





  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger,
  DropdownMenuSeparator
} from '@/components/ui/dropdown-menu';




// Import our custom components




interface FileManagementInterfaceProps {
  conversationId?: string;
  userId: string;
  className?: string;
  onFileSelect?: (file: FileMetadata) => void;
  onFileUpload?: (files: File[]) => void;
  readOnly?: boolean;
}
interface UploadProgress {
  fileId: string;
  fileName: string;
  progress: number;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  error?: string;
}
interface FileStats {
  totalFiles: number;
  totalSize: string;
  processingFiles: number;
  failedFiles: number;
  typeDistribution: Record<string, number>;
}
export const FileManagementInterface: React.FC<FileManagementInterfaceProps> = ({
  conversationId,
  userId,
  className,
  onFileSelect,
  onFileUpload,
  readOnly = false
}) => {
  const { toast } = useToast();
  // State management
  const [files, setFiles] = useState<FileMetadata[]>([]);
  const [selectedFile, setSelectedFile] = useState<FileMetadata | null>(null);
  const [selectedFiles, setSelectedFiles] = useState<FileMetadata[]>([]);
  const [uploadProgress, setUploadProgress] = useState<UploadProgress[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [activeTab, setActiveTab] = useState('files');
  const [fileStats, setFileStats] = useState<FileStats>({
    totalFiles: 0,
    totalSize: '0 B',
    processingFiles: 0,
    failedFiles: 0,
    typeDistribution: {}
  });
  // Mock data for permissions (in real app, this would come from API)
  const [availableUsers] = useState([
    { id: 'user1', name: 'John Doe', email: 'john@example.com', roles: ['user'] },
    { id: 'user2', name: 'Jane Smith', email: 'jane@example.com', roles: ['admin'] },
    { id: 'user3', name: 'Bob Wilson', email: 'bob@example.com', roles: ['editor'] }
  ]);
  const [availableRoles] = useState([
    { id: 'admin', name: 'Administrator', description: 'Full access to all files' },
    { id: 'editor', name: 'Editor', description: 'Can edit and manage files' },
    { id: 'viewer', name: 'Viewer', description: 'Can only view files' },
    { id: 'user', name: 'User', description: 'Standard user access' }
  ]);
  const [filePermissions, setFilePermissions] = useState<Record<string, FilePermission[]>>({});
  // Load files on component mount
  useEffect(() => {
    loadFiles();
  }, [conversationId, userId]);
  // Filter files based on search query
  const filteredFiles = files.filter(file =>
    file.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
    file.file_type.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (file.tags && file.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase())))
  );
  const loadFiles = async () => {
    setLoading(true);
    try {
      // In a real app, this would be an API call
      const response = await fetch(`/api/files/enhanced/?${new URLSearchParams({
        ...(conversationId && { conversation_id: conversationId }),
        user_id: userId,
        include_analysis: 'true',
        ag_grid_format: 'true'
      })}`);
      if (response.ok) {
        const data = await response.json();
        setFiles(data.files || []);
        // Update statistics
        setFileStats({
          totalFiles: data.total_count || 0,
          totalSize: data.statistics?.total_size_formatted || '0 B',
          processingFiles: data.files?.filter((f: FileMetadata) => f.processing_status === 'processing').length || 0,
          failedFiles: data.files?.filter((f: FileMetadata) => f.processing_status === 'failed').length || 0,
          typeDistribution: data.statistics?.type_distribution || {}
        });
      } else {
        toast({
          title: "Error",
          description: "Failed to load files",
          variant: "destructive"
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to load files",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };
  const handleFilesSelected = useCallback((selectedFiles: File[]) => {
    onFileUpload?.(selectedFiles);
    // Initialize upload progress
    const newProgress: UploadProgress[] = selectedFiles.map(file => ({
      fileId: `temp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      fileName: file.name,
      progress: 0,
      status: 'uploading'
    }));
    setUploadProgress(prev => [...prev, ...newProgress]);
  }, [onFileUpload]);
  const handleFileUpload = async (uploadItems: any[]) => {
    for (const item of uploadItems) {
      try {
        // Update progress to uploading
        setUploadProgress(prev => prev.map(p => 
          p.fileName === item.file.name 
            ? { ...p, status: 'uploading', progress: 0 }
            : p
        ));
        // Create form data
        const formData = new FormData();
        formData.append('file', item.file);
        formData.append('metadata', JSON.stringify({
          conversation_id: conversationId || 'default',
          user_id: userId,
          description: `Uploaded file: ${item.file.name}`,
          tags: [],
          enable_hooks: true,
          processing_options: {},
          ui_context: { source: 'file_management_interface' }
        }));
        // Simulate upload progress
        const progressInterval = setInterval(() => {
          setUploadProgress(prev => prev.map(p => 
            p.fileName === item.file.name && p.progress < 90
              ? { ...p, progress: p.progress + 10 }
              : p
          ));
        }, 200);
        // Upload file
        const response = await fetch('/api/files/enhanced/upload', {
          method: 'POST',
          body: formData
        });
        clearInterval(progressInterval);
        if (response.ok) {
          const result = await response.json();
          // Update progress to processing
          setUploadProgress(prev => prev.map(p => 
            p.fileName === item.file.name 
              ? { ...p, status: 'processing', progress: 100 }
              : p
          ));
          // Wait a bit then mark as completed
          setTimeout(() => {
            setUploadProgress(prev => prev.map(p => 
              p.fileName === item.file.name 
                ? { ...p, status: 'completed', progress: 100 }
                : p
            ));
            // Remove from progress after a delay
            setTimeout(() => {
              setUploadProgress(prev => prev.filter(p => p.fileName !== item.file.name));
            }, 2000);
          }, 1000);
          // Reload files
          loadFiles();
          toast({
            title: "Success",
            description: `File "${item.file.name}" uploaded successfully`
          });
        } else {
          throw new Error('Upload failed');
        }
      } catch (error) {
        setUploadProgress(prev => prev.map(p => 
          p.fileName === item.file.name 
            ? { ...p, status: 'error', error: 'Upload failed' }
            : p
        ));
        toast({
          title: "Error",
          description: `Failed to upload "${item.file.name}"`,
          variant: "destructive"
        });
      }
    }
  };
  const handleFileRemove = (fileId: string) => {
    setUploadProgress(prev => prev.filter(p => p.fileId !== fileId));
  };
  const handleFileSelectFromGrid = (file: FileMetadata) => {
    setSelectedFile(file);
    setActiveTab('preview');
    onFileSelect?.(file);
  };
  const handleFilesSelectedFromGrid = (files: FileMetadata[]) => {
    setSelectedFiles(files);
  };
  const handleFileDownload = async (fileId: string) => {
    try {
      const response = await fetch(`/api/files/${fileId}/download`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = files.find(f => f.file_id === fileId)?.filename || 'download';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to download file",
        variant: "destructive"
      });
    }
  };
  const handleFileDelete = async (fileId: string) => {
    try {
      const response = await fetch(`/api/files/${fileId}`, {
        method: 'DELETE'
      });
      if (response.ok) {
        setFiles(prev => prev.filter(f => f.file_id !== fileId));
        if (selectedFile?.file_id === fileId) {
          setSelectedFile(null);
        }
        toast({
          title: "Success",
          description: "File deleted successfully"
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to delete file",
        variant: "destructive"
      });
    }
  };
  const handleBulkAction = async (action: string) => {
    if (selectedFiles.length === 0) return;
    try {
      switch (action) {
        case 'download':
          for (const file of selectedFiles) {
            await handleFileDownload(file.file_id);
          }
          break;
        case 'delete':
          for (const file of selectedFiles) {
            await handleFileDelete(file.file_id);
          }
          break;
        default:
          break;
      }
    } catch (error) {
      toast({
        title: "Error",
        description: `Failed to ${action} selected files`,
        variant: "destructive"
      });
    }
  };
  const handlePermissionUpdate = (fileId: string, permissions: FilePermission[]) => {
    setFilePermissions(prev => ({
      ...prev,
      [fileId]: permissions
    }));
  };
  return (
    <ErrorBoundary fallback={<div>Something went wrong in FileManagementInterface</div>}>
      <div className={cn('w-full h-full flex flex-col space-y-6', className)}>
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Files className="h-5 w-5 sm:w-auto md:w-full" />
                File Management
              </CardTitle>
              <p className="text-sm text-muted-foreground mt-1 md:text-base lg:text-lg">
                Upload, manage, and organize your files with advanced multimedia processing
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button
                variant="outline"
                size="sm"
                onClick={loadFiles}
                disabled={loading}
               aria-label="Button">
                <RefreshCw className={cn("mr-2 h-4 w-4", loading && "animate-spin")} />
                Refresh
              </Button>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button variant="outline" size="sm" aria-label="Button">
                    <MoreHorizontal className="h-4 w-4 sm:w-auto md:w-full" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}>
                    {viewMode === 'grid' ? <List className="mr-2 h-4 w-4 sm:w-auto md:w-full" /> : <Grid className="mr-2 h-4 w-4 sm:w-auto md:w-full" />}
                    {viewMode === 'grid' ? 'List View' : 'Grid View'}
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => handleBulkAction('download')} disabled={selectedFiles.length === 0}>
                    <Download className="mr-2 h-4 w-4 sm:w-auto md:w-full" />
                    Download Selected
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => handleBulkAction('delete')} disabled={selectedFiles.length === 0}>
                    <Trash2 className="mr-2 h-4 w-4 sm:w-auto md:w-full" />
                    Delete Selected
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </CardHeader>
      </Card>
      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 sm:p-4 md:p-6">
            <div className="flex items-center gap-2">
              <Files className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
              <div>
                <p className="text-sm font-medium md:text-base lg:text-lg">Total Files</p>
                <p className="text-2xl font-bold">{fileStats.totalFiles}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 sm:p-4 md:p-6">
            <div className="flex items-center gap-2">
              <Upload className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
              <div>
                <p className="text-sm font-medium md:text-base lg:text-lg">Total Size</p>
                <p className="text-2xl font-bold">{fileStats.totalSize}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 sm:p-4 md:p-6">
            <div className="flex items-center gap-2">
              <Settings className="h-4 w-4 text-blue-600 sm:w-auto md:w-full" />
              <div>
                <p className="text-sm font-medium md:text-base lg:text-lg">Processing</p>
                <p className="text-2xl font-bold text-blue-600">{fileStats.processingFiles}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 sm:p-4 md:p-6">
            <div className="flex items-center gap-2">
              <Trash2 className="h-4 w-4 text-red-600 sm:w-auto md:w-full" />
              <div>
                <p className="text-sm font-medium md:text-base lg:text-lg">Failed</p>
                <p className="text-2xl font-bold text-red-600">{fileStats.failedFiles}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
      {/* Upload Progress */}
      {uploadProgress.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm md:text-base lg:text-lg">Upload Progress</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {uploadProgress.map((progress) => (
              <div key={progress.fileId} className="space-y-2">
                <div className="flex items-center justify-between text-sm md:text-base lg:text-lg">
                  <span className="truncate">{progress.fileName}</span>
                  <Badge 
                    variant={
                      progress.status === 'completed' ? 'default' :
                      progress.status === 'error' ? 'destructive' : 'secondary'
                    }
                  >
                    {progress.status}
                  </Badge>
                </div>
                <Progress value={progress.progress} className="h-2" />
                {progress.error && (
                  <p className="text-xs text-destructive sm:text-sm md:text-base">{progress.error}</p>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}
      {/* Search and Filters */}
      <Card>
        <CardContent className="p-4 sm:p-4 md:p-6">
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
                <input
                  placeholder="Search files by name, type, or tags..."
                  value={searchQuery}
                  onChange={(e) = aria-label="Input"> setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <button variant="outline" size="sm" aria-label="Button">
              <Filter className="mr-2 h-4 w-4 sm:w-auto md:w-full" />
              Filters
            </Button>
          </div>
        </CardContent>
      </Card>
      {/* Main Content */}
      <div className="flex-1">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="upload">Upload</TabsTrigger>
            <TabsTrigger value="files">Files ({filteredFiles.length})</TabsTrigger>
            <TabsTrigger value="preview" disabled={!selectedFile}>Preview</TabsTrigger>
            <TabsTrigger value="permissions" disabled={!selectedFile}>Permissions</TabsTrigger>
          </TabsList>
          <TabsContent value="upload" className="mt-6">
            <FileUploadDropzone
              onFilesSelected={handleFilesSelected}
              onFileRemove={handleFileRemove}
              onUploadStart={handleFileUpload}
              disabled={readOnly}
            />
          </TabsContent>
          <TabsContent value="files" className="mt-6">
            <FileMetadataGrid
              files={filteredFiles}
              loading={loading}
              onFileSelect={handleFileSelectFromGrid}
              onFileDownload={handleFileDownload}
              onFileDelete={readOnly ? undefined : handleFileDelete}
              onFilesSelected={handleFilesSelectedFromGrid}
              enableSelection={!readOnly}
              height={600}
            />
          </TabsContent>
          <TabsContent value="preview" className="mt-6">
            {selectedFile ? (
              <MultimediaPreview
                file={selectedFile}
                onDownload={handleFileDownload}
                onFullscreen={(fileId) => {
                  // Handle fullscreen preview
                }}
              />
            ) : (
              <Card>
                <CardContent className="p-8 text-center sm:p-4 md:p-6">
                  <Eye className="h-12 w-12 mx-auto mb-4 text-muted-foreground sm:w-auto md:w-full" />
                  <p className="text-muted-foreground">
                    Select a file to preview its content
                  </p>
                </CardContent>
              </Card>
            )}
          </TabsContent>
          <TabsContent value="permissions" className="mt-6">
            {selectedFile ? (
              <FilePermissionManager
                fileId={selectedFile.file_id}
                fileName={selectedFile.filename}
                currentPermissions={filePermissions[selectedFile.file_id] || []}
                availableUsers={availableUsers}
                availableRoles={availableRoles}
                permissionRules={[]}
                onPermissionUpdate={(permissions) => handlePermissionUpdate(selectedFile.file_id, permissions)}
                onRuleUpdate={() => {}}
                readOnly={readOnly}
              />
            ) : (
              <Card>
                <CardContent className="p-8 text-center sm:p-4 md:p-6">
                  <Share2 className="h-12 w-12 mx-auto mb-4 text-muted-foreground sm:w-auto md:w-full" />
                  <p className="text-muted-foreground">
                    Select a file to manage its permissions
                  </p>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
    </ErrorBoundary>
  );
};
export default FileManagementInterface;
