'use client';

import React, { useState, useCallback, useRef } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Upload,
  File,
  Image,
  Code,
  FileText,
  Music,
  Video,
  X,
  Eye,
  Download,
  AlertCircle,
  CheckCircle
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import {
  Attachment,
  AttachmentMetadata,
  AttachmentAnalysis
} from '@/types/enhanced-chat';

interface MultimodalFileUploadProps {
  onFilesUploaded: (attachments: Attachment[]) => void;
  onFileRemoved: (attachmentId: string) => void;
  maxFileSize?: number; // in MB
  maxFiles?: number;
  acceptedTypes?: string[];
  enableImageAnalysis?: boolean;
  enableCodeAnalysis?: boolean;
  className?: string;
}

interface UploadProgress {
  fileId: string;
  progress: number;
  status: 'uploading' | 'analyzing' | 'completed' | 'error';
  error?: string;
}

export const MultimodalFileUpload: React.FC<MultimodalFileUploadProps> = ({
  onFilesUploaded,
  onFileRemoved,
  maxFileSize = 10, // 10MB default
  maxFiles = 5,
  acceptedTypes = ['image/*', 'text/*', 'application/pdf', '.js', '.ts', '.tsx', '.jsx', '.py', '.java', '.cpp', '.c', '.html', '.css', '.json', '.xml', '.md'],
  enableImageAnalysis = true,
  enableCodeAnalysis = true,
  className = ''
}) => {
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<UploadProgress[]>([]);
  const [attachments, setAttachments] = useState<Attachment[]>([]);

  // File type detection
  const getFileType = (file: File): Attachment['type'] => {
    if (file.type.startsWith('image/')) return 'image';
    if (file.type.startsWith('video/')) return 'video';
    if (file.type.startsWith('audio/')) return 'audio';
    if (file.type.includes('pdf') || file.type.includes('document') || file.type.includes('text')) return 'document';
    
    // Check by extension for code files
    const extension = file.name.split('.').pop()?.toLowerCase();
    const codeExtensions = ['js', 'ts', 'tsx', 'jsx', 'py', 'java', 'cpp', 'c', 'html', 'css', 'json', 'xml', 'md', 'yml', 'yaml'];
    if (extension && codeExtensions.includes(extension)) return 'code';
    
    return 'document';
  };

  // File icon component
  const getFileIcon = (type: Attachment['type']) => {
    switch (type) {
      case 'image':
        return Image;
      case 'video':
        return Video;
      case 'audio':
        return Music;
      case 'code':
        return Code;
      case 'document':
      default:
        return FileText;
    }
  };

  // Validate file
  const validateFile = (file: File): string | null => {
    if (file.size > maxFileSize * 1024 * 1024) {
      return `File size exceeds ${maxFileSize}MB limit`;
    }

    if (attachments.length >= maxFiles) {
      return `Maximum ${maxFiles} files allowed`;
    }

    // Check accepted types
    const isAccepted = acceptedTypes.some(type => {
      if (type.includes('*')) {
        return file.type.startsWith(type.replace('*', ''));
      }
      if (type.startsWith('.')) {
        return file.name.toLowerCase().endsWith(type.toLowerCase());
      }
      return file.type === type;
    });

    if (!isAccepted) {
      return 'File type not supported';
    }

    return null;
  };

  // Simulate file analysis
  const analyzeFile = async (file: File, type: Attachment['type']): Promise<AttachmentAnalysis | undefined> => {
    // Simulate analysis delay
    await new Promise(resolve => setTimeout(resolve, 1000));

    if (type === 'image' && enableImageAnalysis) {
      return {
        summary: 'Image contains objects and text elements',
        entities: ['person', 'building', 'text'],
        topics: ['architecture', 'urban'],
        sentiment: 'neutral',
        confidence: 0.85,
        extractedText: 'Sample extracted text from image'
      };
    }

    if (type === 'code' && enableCodeAnalysis) {
      return {
        summary: 'Code file with functions and imports',
        entities: ['function', 'import', 'variable'],
        topics: ['programming', 'javascript'],
        sentiment: 'neutral',
        confidence: 0.9,
        extractedText: await file.text()
      };
    }

    if (type === 'document') {
      return {
        summary: 'Document with structured content',
        entities: ['heading', 'paragraph', 'list'],
        topics: ['documentation'],
        sentiment: 'neutral',
        confidence: 0.8,
        extractedText: file.type.includes('text') ? await file.text() : 'Text extraction not available'
      };
    }

    return undefined;
  };

  // Process uploaded files
  const processFiles = useCallback(async (files: FileList) => {
    const fileArray = Array.from(files);
    const validFiles: File[] = [];
    
    // Validate all files first
    for (const file of fileArray) {
      const error = validateFile(file);
      if (error) {
        toast({
          variant: 'destructive',
          title: 'File Upload Error',
          description: `${file.name}: ${error}`
        });
        continue;
      }
      validFiles.push(file);
    }

    if (validFiles.length === 0) return;

    // Initialize progress tracking
    const progressItems: UploadProgress[] = validFiles.map(file => ({
      fileId: `${file.name}-${Date.now()}`,
      progress: 0,
      status: 'uploading'
    }));
    setUploadProgress(progressItems);

    const newAttachments: Attachment[] = [];

    // Process each file
    for (let i = 0; i < validFiles.length; i++) {
      const file = validFiles[i];
      const progressItem = progressItems[i];
      
      try {
        // Simulate upload progress
        for (let progress = 0; progress <= 100; progress += 20) {
          setUploadProgress(prev => 
            prev.map(item => 
              item.fileId === progressItem.fileId 
                ? { ...item, progress }
                : item
            )
          );
          await new Promise(resolve => setTimeout(resolve, 100));
        }

        // Update status to analyzing
        setUploadProgress(prev => 
          prev.map(item => 
            item.fileId === progressItem.fileId 
              ? { ...item, status: 'analyzing' }
              : item
          )
        );

        const fileType = getFileType(file);
        const fileUrl = URL.createObjectURL(file);
        
        // Get file metadata
        const metadata: AttachmentMetadata = {
          encoding: file.type
        };

        if (fileType === 'image') {
          // Get image dimensions
          const img = document.createElement('img');
          img.src = fileUrl;
          await new Promise(resolve => { img.onload = resolve; });
          metadata.dimensions = { width: img.width, height: img.height };
        }

        // Analyze file content
        const analysis = await analyzeFile(file, fileType);

        const attachment: Attachment = {
          id: progressItem.fileId,
          name: file.name,
          type: fileType,
          size: file.size,
          url: fileUrl,
          mimeType: file.type,
          metadata,
          analysis
        };

        newAttachments.push(attachment);

        // Update status to completed
        setUploadProgress(prev => 
          prev.map(item => 
            item.fileId === progressItem.fileId 
              ? { ...item, status: 'completed', progress: 100 }
              : item
          )
        );

      } catch (error) {
        setUploadProgress(prev => 
          prev.map(item => 
            item.fileId === progressItem.fileId 
              ? { ...item, status: 'error', error: 'Upload failed' }
              : item
          )
        );
        
        toast({
          variant: 'destructive',
          title: 'Upload Failed',
          description: `Failed to upload ${file.name}`
        });
      }
    }

    // Update attachments and notify parent
    setAttachments(prev => [...prev, ...newAttachments]);
    onFilesUploaded(newAttachments);

    // Clear progress after a delay
    setTimeout(() => {
      setUploadProgress([]);
    }, 2000);
  }, [attachments.length, maxFiles, maxFileSize, acceptedTypes, enableImageAnalysis, enableCodeAnalysis, onFilesUploaded, toast]);

  // Handle drag and drop
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      processFiles(files);
    }
  }, [processFiles]);

  // Handle file input change
  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      processFiles(files);
    }
    // Reset input value to allow same file selection
    e.target.value = '';
  }, [processFiles]);

  // Handle file removal
  const handleRemoveFile = useCallback((attachmentId: string) => {
    setAttachments(prev => {
      const updated = prev.filter(att => att.id !== attachmentId);
      return updated;
    });
    onFileRemoved(attachmentId);
  }, [onFileRemoved]);

  // Format file size
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Upload Area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <Card 
          className={`border-2 border-dashed transition-colors cursor-pointer ${
            isDragOver 
              ? 'border-primary bg-primary/5' 
              : 'border-muted-foreground/25 hover:border-primary/50'
          }`}
        >
        <CardContent className="p-6 text-center">
          <Upload className="h-8 w-8 mx-auto mb-4 text-muted-foreground" />
          <p className="text-sm font-medium mb-2">
            Drop files here or click to upload
          </p>
          <p className="text-xs text-muted-foreground mb-4">
            Support for images, documents, code files, and more
          </p>
          <div className="flex flex-wrap gap-2 justify-center">
            <Badge variant="secondary" className="text-xs">
              Max {maxFileSize}MB
            </Badge>
            <Badge variant="secondary" className="text-xs">
              Up to {maxFiles} files
            </Badge>
          </div>
        </CardContent>
        </Card>
      </div>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept={acceptedTypes.join(',')}
        onChange={handleFileInputChange}
        className="hidden"
      />

      {/* Upload Progress */}
      {uploadProgress.length > 0 && (
        <div className="space-y-2">
          {uploadProgress.map((progress) => (
            <Card key={progress.fileId}>
              <CardContent className="p-3">
                <div className="flex items-center gap-3">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium">
                        {progress.fileId.split('-')[0]}
                      </span>
                      <div className="flex items-center gap-2">
                        {progress.status === 'completed' && (
                          <CheckCircle className="h-4 w-4 text-green-600" />
                        )}
                        {progress.status === 'error' && (
                          <AlertCircle className="h-4 w-4 text-red-600" />
                        )}
                        <span className="text-xs text-muted-foreground">
                          {progress.status === 'uploading' && 'Uploading...'}
                          {progress.status === 'analyzing' && 'Analyzing...'}
                          {progress.status === 'completed' && 'Complete'}
                          {progress.status === 'error' && progress.error}
                        </span>
                      </div>
                    </div>
                    {progress.status !== 'error' && (
                      <Progress value={progress.progress} className="h-2" />
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Uploaded Files */}
      {attachments.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium">Attached Files ({attachments.length})</h4>
          {attachments.map((attachment) => {
            const IconComponent = getFileIcon(attachment.type);
            return (
              <Card key={attachment.id}>
                <CardContent className="p-3">
                  <div className="flex items-center gap-3">
                    <IconComponent className="h-8 w-8 text-muted-foreground flex-shrink-0" />
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-medium truncate">
                          {attachment.name}
                        </span>
                        <Badge variant="outline" className="text-xs">
                          {attachment.type}
                        </Badge>
                      </div>
                      
                      <div className="flex items-center gap-4 text-xs text-muted-foreground">
                        <span>{formatFileSize(attachment.size)}</span>
                        {attachment.metadata?.dimensions && (
                          <span>
                            {attachment.metadata.dimensions.width} × {attachment.metadata.dimensions.height}
                          </span>
                        )}
                        {attachment.analysis && (
                          <Badge variant="secondary" className="text-xs">
                            Analyzed
                          </Badge>
                        )}
                      </div>

                      {attachment.analysis?.summary && (
                        <p className="text-xs text-muted-foreground mt-1 line-clamp-1">
                          {attachment.analysis.summary}
                        </p>
                      )}
                    </div>

                    <div className="flex items-center gap-1">
                      {attachment.type === 'image' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => window.open(attachment.url, '_blank')}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                      )}
                      
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          const a = document.createElement('a');
                          a.href = attachment.url;
                          a.download = attachment.name;
                          a.click();
                        }}
                      >
                        <Download className="h-4 w-4" />
                      </Button>
                      
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRemoveFile(attachment.id)}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default MultimodalFileUpload;