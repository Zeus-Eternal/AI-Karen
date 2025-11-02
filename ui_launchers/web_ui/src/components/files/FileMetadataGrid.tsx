import React, { useMemo, useCallback, useState } from 'react';
import { AgGridReact } from 'ag-grid-react';
import { ColDef, GridReadyEvent, SelectionChangedEvent, CellClickedEvent } from 'ag-grid-community';
import { 
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';
'use client';





  File, 
  Image, 
  Video, 
  Music, 
  Archive, 
  Code, 
  FileText, 
  Download, 
  Eye, 
  Trash2,
  MoreHorizontal,
  Calendar,
  HardDrive,
  Tag
} from 'lucide-react';



  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger,
  DropdownMenuSeparator
} from '@/components/ui/dropdown-menu';



// AG-Grid theme imports



export interface FileMetadata {
  file_id: string;
  filename: string;
  file_size: number;
  mime_type: string;
  file_type: 'document' | 'image' | 'audio' | 'video' | 'code' | 'archive' | 'unknown';
  processing_status: 'pending' | 'processing' | 'completed' | 'failed' | 'quarantined';
  upload_timestamp: string;
  has_thumbnail: boolean;
  preview_available: boolean;
  extracted_content_available: boolean;
  tags?: string[];
  conversation_id?: string;
  user_id?: string;
  security_scan_result?: 'safe' | 'suspicious' | 'malicious' | 'scan_failed';
  analysis_results?: Record<string, any>;
}

interface FileMetadataGridProps {
  files: FileMetadata[];
  loading?: boolean;
  onFileSelect?: (file: FileMetadata) => void;
  onFileDownload?: (fileId: string) => void;
  onFilePreview?: (fileId: string) => void;
  onFileDelete?: (fileId: string) => void;
  onFilesSelected?: (files: FileMetadata[]) => void;
  className?: string;
  height?: number;
  enableSelection?: boolean;
  enableFiltering?: boolean;
  enableSorting?: boolean;
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const formatDate = (dateString: string): string => {
  try {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch {
    return dateString;
  }
};

// Custom cell renderers
const FileIconRenderer = ({ data }: { data: FileMetadata }) => {
  const getIcon = () => {
    switch (data.file_type) {
      case 'image': return <Image className="h-4 w-4 text-green-600 sm:w-auto md:w-full" />;
      case 'video': return <Video className="h-4 w-4 text-purple-600 sm:w-auto md:w-full" />;
      case 'audio': return <Music className="h-4 w-4 text-blue-600 sm:w-auto md:w-full" />;
      case 'document': return <FileText className="h-4 w-4 text-gray-600 sm:w-auto md:w-full" />;
      case 'code': return <Code className="h-4 w-4 text-orange-600 sm:w-auto md:w-full" />;
      case 'archive': return <Archive className="h-4 w-4 text-yellow-600 sm:w-auto md:w-full" />;
      default: return <File className="h-4 w-4 text-gray-400 sm:w-auto md:w-full" />;
    }
  };

  return (
    <div className="flex items-center gap-2">
      {getIcon()}
      <span className="truncate" title={data.filename}>
        {data.filename}
      </span>
    </div>
  );
};

const StatusRenderer = ({ data }: { data: FileMetadata }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'processing': return 'bg-blue-100 text-blue-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'failed': return 'bg-red-100 text-red-800';
      case 'quarantined': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <Badge variant="secondary" className={getStatusColor(data.processing_status)}>
      {data.processing_status}
    </Badge>
  );
};

const SecurityRenderer = ({ data }: { data: FileMetadata }) => {
  if (!data.security_scan_result) return null;

  const getSecurityColor = (result: string) => {
    switch (result) {
      case 'safe': return 'bg-green-100 text-green-800';
      case 'suspicious': return 'bg-yellow-100 text-yellow-800';
      case 'malicious': return 'bg-red-100 text-red-800';
      case 'scan_failed': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <Badge variant="secondary" className={getSecurityColor(data.security_scan_result)}>
      {data.security_scan_result}
    </Badge>
  );
};

const ActionsRenderer = ({ 
  data, 
  onDownload, 
  onPreview, 
  onDelete 
}: { 
  data: FileMetadata;
  onDownload?: (fileId: string) => void;
  onPreview?: (fileId: string) => void;
  onDelete?: (fileId: string) => void;
}) => {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button variant="ghost" size="sm" className="h-8 w-8 p-0 sm:w-auto md:w-full" aria-label="Button">
          <MoreHorizontal className="h-4 w-4 sm:w-auto md:w-full" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {data.preview_available && onPreview && (
          <DropdownMenuItem onClick={() => onPreview(data.file_id)}>
            <Eye className="mr-2 h-4 w-4 sm:w-auto md:w-full" />
            Preview
          </DropdownMenuItem>
        )}
        {onDownload && (
          <DropdownMenuItem onClick={() => onDownload(data.file_id)}>
            <Download className="mr-2 h-4 w-4 sm:w-auto md:w-full" />
            Download
          </DropdownMenuItem>
        )}
        <DropdownMenuSeparator />
        {onDelete && (
          <DropdownMenuItem 
            onClick={() => onDelete(data.file_id)}
            className="text-destructive"
          >
            <Trash2 className="mr-2 h-4 w-4 sm:w-auto md:w-full" />
            Delete
          </DropdownMenuItem>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

const TagsRenderer = ({ data }: { data: FileMetadata }) => {
  if (!data.tags || data.tags.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-1">
      {data.tags.slice(0, 3).map((tag, index) => (
        <Badge key={index} variant="outline" className="text-xs sm:text-sm md:text-base">
          {tag}
        </Badge>
      ))}
      {data.tags.length > 3 && (
        <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
          +{data.tags.length - 3}
        </Badge>
      )}
    </div>
  );
};

export const FileMetadataGrid: React.FC<FileMetadataGridProps> = ({
  files,
  loading = false,
  onFileSelect,
  onFileDownload,
  onFilePreview,
  onFileDelete,
  onFilesSelected,
  className,
  height = 400,
  enableSelection = true,
  enableFiltering = true,
  enableSorting = true
}) => {
  const [selectedFiles, setSelectedFiles] = useState<FileMetadata[]>([]);

  const columnDefs = useMemo<ColDef[]>(() => [
    {
      headerName: 'File',
      field: 'filename',
      cellRenderer: FileIconRenderer,
      flex: 2,
      minWidth: 200,
      sortable: enableSorting,
      filter: enableFiltering ? 'agTextColumnFilter' : false,
      filterParams: {
        filterOptions: ['contains', 'startsWith', 'endsWith'],
        suppressAndOrCondition: true,
      }
    },
    {
      headerName: 'Type',
      field: 'file_type',
      width: 100,
      sortable: enableSorting,
      filter: enableFiltering ? 'agSetColumnFilter' : false,
      cellRenderer: ({ value }: { value: string }) => (
        <Badge variant="outline" className="capitalize">
          {value}
        </Badge>
      )
    },
    {
      headerName: 'Size',
      field: 'file_size',
      width: 100,
      sortable: enableSorting,
      filter: enableFiltering ? 'agNumberColumnFilter' : false,
      cellRenderer: ({ value }: { value: number }) => formatFileSize(value),
      comparator: (valueA: number, valueB: number) => valueA - valueB
    },
    {
      headerName: 'Status',
      field: 'processing_status',
      width: 120,
      sortable: enableSorting,
      filter: enableFiltering ? 'agSetColumnFilter' : false,
      cellRenderer: StatusRenderer
    },
    {
      headerName: 'Security',
      field: 'security_scan_result',
      width: 100,
      sortable: enableSorting,
      filter: enableFiltering ? 'agSetColumnFilter' : false,
      cellRenderer: SecurityRenderer
    },
    {
      headerName: 'Uploaded',
      field: 'upload_timestamp',
      width: 150,
      sortable: enableSorting,
      filter: enableFiltering ? 'agDateColumnFilter' : false,
      cellRenderer: ({ value }: { value: string }) => formatDate(value),
      sort: 'desc' // Default sort by newest first
    },
    {
      headerName: 'Tags',
      field: 'tags',
      width: 150,
      sortable: false,
      filter: false,
      cellRenderer: TagsRenderer
    },
    {
      headerName: 'Features',
      field: 'features',
      width: 120,
      sortable: false,
      filter: false,
      cellRenderer: ({ data }: { data: FileMetadata }) => (
        <div className="flex gap-1">
          {data.has_thumbnail && (
            <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
              <Image className="mr-1 h-3 w-3 sm:w-auto md:w-full" />
              Thumb
            </Badge>
          )}
          {data.extracted_content_available && (
            <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
              <FileText className="mr-1 h-3 w-3 sm:w-auto md:w-full" />
              Text
            </Badge>
          )}
        </div>
      )
    },
    {
      headerName: 'Actions',
      field: 'actions',
      width: 80,
      sortable: false,
      filter: false,
      pinned: 'right',
      cellRenderer: (params: any) => (
        <ActionsRenderer
          data={params.data}
          onDownload={onFileDownload}
          onPreview={onFilePreview}
          onDelete={onFileDelete}
        />
      )
    }
  ], [enableSorting, enableFiltering, onFileDownload, onFilePreview, onFileDelete]);

  const defaultColDef = useMemo(() => ({
    resizable: true,
    sortable: enableSorting,
    filter: enableFiltering,
    floatingFilter: enableFiltering,
  }), [enableSorting, enableFiltering]);

  const onGridReady = useCallback((params: GridReadyEvent) => {
    params.api.sizeColumnsToFit();
  }, []);

  const onSelectionChanged = useCallback((event: SelectionChangedEvent) => {
    const selectedRows = event.api.getSelectedRows();
    setSelectedFiles(selectedRows);
    onFilesSelected?.(selectedRows);
  }, [onFilesSelected]);

  const onCellClicked = useCallback((event: CellClickedEvent) => {
    if (event.colDef.field !== 'actions' && onFileSelect) {
      onFileSelect(event.data);
    }
  }, [onFileSelect]);

  const getRowStyle = useCallback((params: any) => {
    const file = params.data as FileMetadata;
    if (file.security_scan_result === 'malicious' || file.processing_status === 'quarantined') {
      return { backgroundColor: '#fef2f2' }; // Light red background
    }
    if (file.security_scan_result === 'suspicious') {
      return { backgroundColor: '#fffbeb' }; // Light yellow background
    }
    return undefined;
  }, []);

  const gridOptions = useMemo(() => ({
    rowSelection: enableSelection ? ('multiple' as const) : undefined,
    suppressRowClickSelection: true,
    rowMultiSelectWithClick: enableSelection,
    getRowStyle,
    animateRows: true,
    enableCellTextSelection: true,
    suppressMenuHide: true,
    suppressMovableColumns: false,
  }), [enableSelection, getRowStyle]);

  // Statistics
  const stats = useMemo(() => {
    const totalSize = files.reduce((sum, file) => sum + file.file_size, 0);
    const typeCount = files.reduce((acc, file) => {
      acc[file.file_type] = (acc[file.file_type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    
    return {
      totalFiles: files.length,
      totalSize: formatFileSize(totalSize),
      typeCount
    };
  }, [files]);

  return (
    <div className={cn('w-full space-y-4', className)}>
      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 sm:p-4 md:p-6">
            <div className="flex items-center gap-2">
              <File className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
              <div>
                <p className="text-sm font-medium md:text-base lg:text-lg">Total Files</p>
                <p className="text-2xl font-bold">{stats.totalFiles}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4 sm:p-4 md:p-6">
            <div className="flex items-center gap-2">
              <HardDrive className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
              <div>
                <p className="text-sm font-medium md:text-base lg:text-lg">Total Size</p>
                <p className="text-2xl font-bold">{stats.totalSize}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4 sm:p-4 md:p-6">
            <div className="flex items-center gap-2">
              <Tag className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
              <div>
                <p className="text-sm font-medium md:text-base lg:text-lg">Selected</p>
                <p className="text-2xl font-bold">{selectedFiles.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4 sm:p-4 md:p-6">
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
              <div>
                <p className="text-sm font-medium md:text-base lg:text-lg">Most Common</p>
                <p className="text-lg font-bold capitalize">
                  {Object.entries(stats.typeCount).sort(([,a], [,b]) => b - a)[0]?.[0] || 'None'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* AG-Grid */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <File className="h-5 w-5 sm:w-auto md:w-full" />
            File Metadata ({files.length} files)
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0 sm:p-4 md:p-6">
          <div 
            className="ag-theme-alpine w-full"
            style={{ height: `${height}px` }}
          >
            <AgGridReact
              rowData={files}
              columnDefs={columnDefs}
              defaultColDef={defaultColDef}
              gridOptions={gridOptions}
              onGridReady={onGridReady}
              onSelectionChanged={onSelectionChanged}
              onCellClicked={onCellClicked}
              loading={loading}
              loadingOverlayComponent={() => (
                <div className="flex items-center justify-center h-full">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary sm:w-auto md:w-full"></div>
                </div>
              )}
              noRowsOverlayComponent={() => (
                <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                  <File className="h-12 w-12 mb-2 sm:w-auto md:w-full" />
                  <p>No files found</p>
                </div>
              )}
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default FileMetadataGrid;