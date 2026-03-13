/**
 * File Upload Hook
 * Handles file uploads with progress tracking and validation
 */

'use client';

import { useState, useCallback, useRef } from 'react';
import { auditLogger } from '@/lib/audit-logger';

// File upload state
export interface FileUploadState {
  files: FileUploadItem[];
  isUploading: boolean;
  totalProgress: number;
  currentFile?: FileUploadItem;
  error?: string;
  maxFileSize: number;
  allowedTypes: string[];
  maxFiles: number;
}

// File upload item
export interface FileUploadItem {
  id: string;
  file: File;
  name: string;
  size: number;
  type: string;
  progress: number;
  status: 'pending' | 'uploading' | 'success' | 'error';
  error?: string;
  url?: string;
  metadata?: Record<string, unknown>;
}

// File upload options
export interface FileUploadOptions {
  maxFileSize?: number;
  allowedTypes?: string[];
  maxFiles?: number;
  autoUpload?: boolean;
  compressionLevel?: 'none' | 'low' | 'medium' | 'high';
  generateThumbnails?: boolean;
  analyzeContent?: boolean;
}

// Hook return type
export interface UseFileUploadReturn {
  state: FileUploadState;
  uploadFile: (file: File, options?: Partial<FileUploadOptions>) => Promise<string>;
  removeFile: (fileId: string) => void;
  clearAll: () => void;
  retryUpload: (fileId: string) => void;
  getUploadUrl: (fileId: string) => string;
  cancelUpload: () => void;
}

export function useFileUpload(options: FileUploadOptions = {}): UseFileUploadReturn {
  const [state, setState] = useState<FileUploadState>({
    files: [],
    isUploading: false,
    totalProgress: 0,
    error: undefined,
    maxFileSize: options.maxFileSize || 50 * 1024 * 1024, // 50MB default
    allowedTypes: options.allowedTypes || [
      'image/jpeg',
      'image/png',
      'image/gif',
      'image/webp',
      'application/pdf',
      'text/plain',
      'application/json',
      'text/csv',
    ],
    maxFiles: options.maxFiles || 5,
  });
  
  const abortControllerRef = useRef<AbortController | null>(null);
  
  // Generate unique file ID
  const generateFileId = useCallback((): string => {
    return `file_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }, []);
  
  // Validate file
  const validateFile = useCallback((file: File): { valid: boolean; error?: string } => {
    // Check file size
    if (file.size > state.maxFileSize) {
      return {
        valid: false,
        error: `File size ${(file.size / 1024 / 1024).toFixed(2)}MB exceeds maximum of ${(state.maxFileSize / 1024 / 1024).toFixed(2)}MB`,
      };
    }
    
    // Check file type
    if (!state.allowedTypes.includes(file.type)) {
      return {
        valid: false,
        error: `File type ${file.type} is not allowed. Allowed types: ${state.allowedTypes.join(', ')}`,
      };
    }
    
    // Check total file count
    if (state.files.length >= state.maxFiles) {
      return {
        valid: false,
        error: `Maximum number of files (${state.maxFiles}) reached`,
      };
    }
    
    return { valid: true };
  }, [state.maxFileSize, state.allowedTypes, state.maxFiles, state.files.length]);
  
  // Upload single file
  const uploadFile = useCallback(async (file: File, uploadOptions: Partial<FileUploadOptions> = {}): Promise<string> => {
    const validation = validateFile(file);
    if (!validation.valid) {
      setState(prev => ({ ...prev, error: validation.error }));
      throw new Error(validation.error || 'Invalid file');
    }
    
    const fileId = generateFileId();
    const fileItem: FileUploadItem = {
      id: fileId,
      file,
      name: file.name,
      size: file.size,
      type: file.type,
      progress: 0,
      status: 'pending',
    };
    
    setState(prev => ({
      ...prev,
      files: [...prev.files, fileItem],
      isUploading: true,
      currentFile: fileItem,
      error: undefined,
    }));
    
    try {
      // Create FormData for upload
      const formData = new FormData();
      formData.append('file', file);
      formData.append('fileId', fileId);
      
      if (uploadOptions.compressionLevel) {
        formData.append('compression', uploadOptions.compressionLevel);
      }
      
      if (uploadOptions.generateThumbnails) {
        formData.append('generateThumbnails', 'true');
      }
      
      if (uploadOptions.analyzeContent) {
        formData.append('analyzeContent', 'true');
      }
      
      // Create abort controller for cancellation
      const abortController = new AbortController();
      abortControllerRef.current = abortController;
      
      // Upload with progress tracking
      const xhr = new XMLHttpRequest();
      xhr.open('POST', '/api/files/upload', true);
      
      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const progress = (event.loaded / event.total) * 100;
          
          setState(prev => {
            const updatedFiles = prev.files.map(f => 
              f.id === fileId ? { ...f, progress } : f
            );
            
            const totalProgress = updatedFiles.reduce((sum, f) => sum + f.progress, 0) / updatedFiles.length;
            
            return {
              ...prev,
              files: updatedFiles,
          totalProgress,
          currentFile: prev.currentFile?.id === fileId 
            ? { ...prev.currentFile, progress } as FileUploadItem
            : prev.currentFile,
        };
      });
        }
      };
      
      xhr.onload = () => {
        try {
          const response = JSON.parse(xhr.responseText);
          
          if (response.success) {
            setState(prev => {
              const updatedFiles = prev.files.map(f =>
                f.id === fileId ? { ...f, status: 'success' as const, url: response.url } : f
              );
              
              return {
                ...prev,
                files: updatedFiles,
                isUploading: false,
                totalProgress: 100,
                currentFile: undefined,
              };
            });
            
            auditLogger.log('INFO', 'FILE_UPLOAD_SUCCESS', {
              fileId,
              fileName: file.name,
              fileSize: file.size,
              fileType: file.type,
              uploadTime: Date.now(),
            });
          } else {
            setState(prev => {
              const updatedFiles = prev.files.map(f =>
                f.id === fileId ? { ...f, status: 'error' as const, error: response.error } : f
              );
              
              return {
                ...prev,
                files: updatedFiles,
                isUploading: false,
                error: response.error,
                currentFile: undefined,
              };
            });
            
            auditLogger.log('ERROR', 'FILE_UPLOAD_ERROR', {
              fileId,
              fileName: file.name,
              error: response.error,
              uploadTime: Date.now(),
            });
          }
        } catch (error) {
          setState(prev => ({
            ...prev,
            files: prev.files.map(f =>
              f.id === fileId ? { ...f, status: 'error' as const, error: error instanceof Error ? error.message : 'Upload failed' } : f
            ),
            isUploading: false,
            error: error instanceof Error ? error.message : 'Upload failed',
            currentFile: undefined,
          }));
          
          auditLogger.log('ERROR', 'FILE_UPLOAD_ERROR', {
            fileId,
            fileName: file.name,
            error: error instanceof Error ? error.message : 'Upload failed',
            uploadTime: Date.now(),
          });
        }
      };
      
      xhr.onerror = () => {
        setState(prev => ({
          ...prev,
          files: prev.files.map(f =>
            f.id === fileId ? { ...f, status: 'error' as const, error: 'Network error occurred' } : f
          ),
          isUploading: false,
          error: 'Network error occurred',
          currentFile: undefined,
        }));
        
        auditLogger.log('ERROR', 'FILE_UPLOAD_ERROR', {
          fileId,
          fileName: file.name,
          error: 'Network error occurred',
          uploadTime: Date.now(),
        });
      };
      
      // Set headers
      xhr.setRequestHeader('Authorization', `Bearer ${localStorage.getItem('authToken') || ''}`);
      xhr.setRequestHeader('X-File-ID', fileId);
      
      // Send request
      xhr.send(formData);
      
      return fileId;
    } catch (error) {
      setState(prev => ({
        ...prev,
        isUploading: false,
        error: error instanceof Error ? error.message : 'Upload failed',
        currentFile: undefined,
      }));
      
      auditLogger.log('ERROR', 'FILE_UPLOAD_ERROR', {
        error: error instanceof Error ? error.message : 'Upload failed',
        uploadTime: Date.now(),
      });
      
      throw error;
    }
  }, [validateFile, generateFileId]);
  
  // Remove file
  const removeFile = useCallback((fileId: string) => {
    setState(prev => ({
      ...prev,
      files: prev.files.filter(f => f.id !== fileId),
    }));
    
    auditLogger.log('INFO', 'FILE_REMOVED', { fileId });
  }, []);
  
  // Clear all files
  const clearAll = useCallback(() => {
    setState(prev => ({
      ...prev,
      files: [],
      isUploading: false,
      totalProgress: 0,
      currentFile: undefined,
      error: undefined,
    }));
  }, []);
  
  // Retry upload
  const retryUpload = useCallback(async (fileId: string) => {
    const file = state.files.find(f => f.id === fileId);
    if (!file) return;
    
    try {
      await uploadFile(file.file);
    } catch (error) {
      auditLogger.log('ERROR', 'FILE_RETRY_ERROR', {
        fileId,
        error: error instanceof Error ? error.message : 'Retry failed',
      });
    }
  }, [state.files, uploadFile]);
  
  // Get upload URL for a file
  const getUploadUrl = useCallback((fileId: string): string => {
    const file = state.files.find(f => f.id === fileId);
    return file?.url || '';
  }, [state.files]);
  
  // Cancel current upload
  const cancelUpload = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    
    setState(prev => ({
      ...prev,
      isUploading: false,
      currentFile: undefined,
    }));
  }, []);
  
  return {
    state,
    uploadFile,
    removeFile,
    clearAll,
    retryUpload,
    getUploadUrl,
    cancelUpload,
  };
}
