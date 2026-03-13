/**
 * File Management Types
 * Aligned with backend schemas
 */

export interface FileInfo {
  id: string;
  filename: string;
  original_filename: string;
  content_type: string;
  size: number;
  upload_date: string;
  user_id: string;
  metadata: Record<string, unknown>;
  tags: string[];
  processing_status: 'pending' | 'processing' | 'completed' | 'failed';
  thumbnail_url?: string;
  download_url: string;
}

export interface FileUploadRequest {
  file: File;
  metadata?: Record<string, unknown>;
  tags?: string[];
}

export interface FileUploadResponse {
  file_id: string;
  filename: string;
  size: number;
  content_type: string;
  upload_date: string;
  download_url: string;
  thumbnail_url?: string;
  processing_status: string;
}

export interface FileListResponse {
  files: FileInfo[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
  total_size: number;
}

export interface MultimediaCapabilities {
  supported_formats: {
    images: string[];
    videos: string[];
    audio: string[];
    documents: string[];
  };
  max_file_size: number;
  processing_features: string[];
}
