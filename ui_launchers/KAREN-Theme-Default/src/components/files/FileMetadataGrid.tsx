// ui_launchers/KAREN-Theme-Default/src/components/files/FileMetadataGrid.tsx
"use client";

import React, { useMemo, useCallback, useState, useRef, useEffect } from 'react';
import { AgGridReact } from 'ag-grid-react';
import type {
  CellClickedEvent,
  ColDef,
  GridReadyEvent,
  ICellRendererParams,
  RowClassParams,
  RowStyle,
  SelectionChangedEvent,
} from 'ag-grid-community';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';

import {
  Image,
  Video,
  Music,
  FileText,
  Code,
  Archive,
  File,
  MoreHorizontal,
  Eye,
  Download,
  Trash2,
  HardDrive,
  Tag,
  Calendar
} from 'lucide-react';

import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator
} from '@/components/ui/dropdown-menu';

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
  analysis_results?: Record<string, unknown>;
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
  viewMode?: 'grid' | 'list';
}

const formatFileSize = (bytes: number): string => {
  if (!Number.isFinite(bytes) || bytes <= 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.min(sizes.length - 1, Math.floor(Math.log(bytes) / Math.log(k)));
  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
};

const formatDate = (dateString: string): string => {
  try {
    const d = new Date(dateString);
    if (isNaN(d.getTime())) return dateString;
    return d.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
  } catch {
    return dateString;
  }
};

// Custom cell renderers
const FileIconRenderer: React.FC<{ data: FileMetadata }> = ({ data }) => {
  const getIcon = () => {
    switch (data.file_type) {
      case 'image': return <Image className="h-4 w-4 text-green-600" />;
      case 'video': return <Video className="h-4 w-4 text-purple-600" />;
      case 'audio': return <Music className="h-4 w-4 text-blue-600" />;
      case 'document': return <FileText className="h-4 w-4 text-gray-600" />;
      case 'code': return <Code className="h-4 w-4 text-orange-600" />;
      case 'archive': return <Archive className="h-4 w-4 text-yellow-600" />;
      default: return <File className="h-4 w-4 text-gray-400" />;
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

const StatusRenderer: React.FC<{ data: FileMetadata }> = ({ data }) => {
  const getStatusColor = (status: FileMetadata['processing_status']) => {
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

const SecurityRenderer: React.FC<{ data: FileMetadata }> = ({ data }) => {
  if (!data.security_scan_result) return null;

  const getSecurityColor = (result: NonNullable<FileMetadata['security_scan_result']>) => {
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

const ActionsRenderer: React.FC<{
  data: FileMetadata;
  onDownload?: (fileId: string) => void;
  onPreview?: (fileId: string) => void;
  onDelete?: (fileId: string) => void;
}> = ({ data, onDownload, onPreview, onDelete }) => {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
          <MoreHorizontal className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="min-w-40">
        {data.preview_available && onPreview && (
          <DropdownMenuItem onClick={() => onPreview(data.file_id)}>
            <Eye className="mr-2 h-4 w-4" />
            Preview
          </DropdownMenuItem>
        )}
        {onDownload && (
          <DropdownMenuItem onClick={() => onDownload(data.file_id)}>
            <Download className="mr-2 h-4 w-4" />
            Download
          </DropdownMenuItem>
        )}
        <DropdownMenuSeparator />
        {onDelete && (
          <DropdownMenuItem
            onClick={() => onDelete(data.file_id)}
            className="text-destructive"
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Delete
          </DropdownMenuItem>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

const TagsRenderer: React.FC<{ data: FileMetadata }> = ({ data }) => {
  if (!data.tags || data.tags.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-1">
      {data.tags.slice(0, 3).map((tag, index) => (
        <Badge key={index} variant="outline" className="text-[10px] sm:text-xs md:text-sm">
          {tag}
        </Badge>
      ))}
      {data.tags.length > 3 && (
        <Badge variant="outline" className="text-[10px] sm:text-xs md:text-sm">
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
  enableSorting = true,
  viewMode = 'grid'
}) => {
  const [selectedFiles, setSelectedFiles] = useState<FileMetadata[]>([]);
  const gridRef = useRef<AgGridReact<FileMetadata>>(null);

  // Handle grid overlay for loading state
  useEffect(() => {
    const api = gridRef.current?.api;
    if (!api) return;
    if (loading) {
      api.showLoadingOverlay();
    } else {
      if (!files || files.length === 0) api.showNoRowsOverlay();
      else api.hideOverlay();
    }
  }, [loading, files]);

  // Column defs
  const columnDefs = useMemo<ColDef<FileMetadata>[]>(() => [
    {
      headerName: 'File',
      field: 'filename',
      cellRenderer: FileIconRenderer as unknown as ColDef<FileMetadata>["cellRenderer"],
      flex: 2,
      minWidth: 220,
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
      width: 110,
      sortable: enableSorting,
      filter: enableFiltering ? 'agSetColumnFilter' : false,
      cellRenderer: ({ value }: { value: string }) => (
        <Badge variant="outline" className="capitalize">{value}</Badge>
      )
    },
    {
      headerName: 'Size',
      field: 'file_size',
      width: 110,
      sortable: enableSorting,
      filter: enableFiltering ? 'agNumberColumnFilter' : false,
      valueFormatter: ({ value }) => formatFileSize(Number(value || 0)),
      comparator: (a: number, b: number) => (a ?? 0) - (b ?? 0),
    },
    {
      headerName: 'Status',
      field: 'processing_status',
      width: 130,
      sortable: enableSorting,
      filter: enableFiltering ? 'agSetColumnFilter' : false,
      cellRenderer: StatusRenderer as unknown as ColDef<FileMetadata>["cellRenderer"],
    },
    {
      headerName: 'Security',
      field: 'security_scan_result',
      width: 120,
      sortable: enableSorting,
      filter: enableFiltering ? 'agSetColumnFilter' : false,
      cellRenderer: SecurityRenderer as unknown as ColDef<FileMetadata>["cellRenderer"],
    },
    {
      headerName: 'Uploaded',
      field: 'upload_timestamp',
      width: 180,
      sortable: enableSorting,
      filter: enableFiltering ? 'agDateColumnFilter' : false,
      valueGetter: ({ data }) => (data?.upload_timestamp ? new Date(data.upload_timestamp) : null),
      valueFormatter: ({ data }) => (data?.upload_timestamp ? formatDate(data.upload_timestamp) : ''),
      filterParams: {
        comparator: (filterLocalDateAtMidnight: Date, cellValue: Date) => {
          if (!cellValue) return -1;
          const d = new Date(cellValue.getFullYear(), cellValue.getMonth(), cellValue.getDate()).getTime();
          const f = new Date(filterLocalDateAtMidnight.getFullYear(), filterLocalDateAtMidnight.getMonth(), filterLocalDateAtMidnight.getDate()).getTime();
          if (d === f) return 0;
          return d < f ? -1 : 1;
        }
      },
      sort: 'desc'
    },
    {
      headerName: 'Tags',
      field: 'tags',
      width: 170,
      sortable: false,
      filter: false,
      cellRenderer: TagsRenderer as unknown as ColDef<FileMetadata>["cellRenderer"],
    },
    {
      headerName: 'Features',
      width: 140,
      sortable: false,
      filter: false,
      cellRenderer: ({ data }: { data: FileMetadata }) => (
        <div className="flex items-center gap-1">
          {data.has_thumbnail && (
            <Badge variant="outline" className="text-[10px] sm:text-xs md:text-sm">
              <Image className="mr-1 h-3 w-3" /> Thumb
            </Badge>
          )}
          {data.extracted_content_available && (
            <Badge variant="outline" className="text-[10px] sm:text-xs md:text-sm">
              <FileText className="mr-1 h-3 w-3" /> OCR
            </Badge>
          )}
        </div>
      )
    },
    {
      headerName: 'Actions',
      width: 90,
      sortable: false,
      filter: false,
      pinned: 'right',
      cellRenderer: ({ data }: ICellRendererParams<FileMetadata>) =>
        data ? (
          <ActionsRenderer
            data={data}
            onDownload={onFileDownload}
            onPreview={onFilePreview}
            onDelete={onFileDelete}
          />
        ) : null
    }
  ], [enableSorting, enableFiltering, onFileDownload, onFilePreview, onFileDelete]);

  const defaultColDef = useMemo<ColDef<FileMetadata>>(
    () => ({
      resizable: true,
      sortable: enableSorting,
      filter: enableFiltering,
      floatingFilter: enableFiltering,
      suppressHeaderMenuButton: false
    }),
    [enableSorting, enableFiltering]
  );

  const onGridReady = useCallback((params: GridReadyEvent) => {
    params.api.sizeColumnsToFit();
    if (loading) params.api.showLoadingOverlay();
    else if (!files || files.length === 0) params.api.showNoRowsOverlay();
    else params.api.hideOverlay();
  }, [loading, files]);

  const onSelectionChanged = useCallback((event: SelectionChangedEvent) => {
    const selectedRows = event.api.getSelectedRows() as FileMetadata[];
    setSelectedFiles(selectedRows);
    onFilesSelected?.(selectedRows);
  }, [onFilesSelected]);

  const onCellClicked = useCallback((event: CellClickedEvent) => {
    if (event.colDef.field !== 'actions' && onFileSelect) {
      onFileSelect(event.data as FileMetadata);
    }
  }, [onFileSelect]);

  const getRowStyle = useCallback((params: RowClassParams<FileMetadata>): RowStyle | undefined => {
    const file = params.data as FileMetadata;
    if (!file) return undefined;
    if (file.security_scan_result === 'malicious' || file.processing_status === 'quarantined') {
      return { backgroundColor: '#fef2f2' }; // red-50
    }
    if (file.security_scan_result === 'suspicious') {
      return { backgroundColor: '#fffbeb' }; // amber-50
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
    rowHeight: viewMode === 'list' ? 44 : 64,
  }), [enableSelection, getRowStyle, viewMode]);

  // Statistics
  const stats = useMemo(() => {
    const totalSize = files.reduce((sum, file) => sum + (Number(file.file_size) || 0), 0);
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
              <File className="h-4 w-4 text-muted-foreground" />
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
              <HardDrive className="h-4 w-4 text-muted-foreground" />
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
              <Tag className="h-4 w-4 text-muted-foreground" />
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
              <Calendar className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium md:text-base lg:text-lg">Most Common</p>
                <p className="text-lg font-bold capitalize">
                  {Object.entries(stats.typeCount).sort(([, a], [, b]) => (b as number) - (a as number))[0]?.[0] || 'None'}
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
            <File className="h-5 w-5" />
            File Metadata ({files.length} files)
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0 sm:p-4 md:p-6">
          <div
            className="ag-theme-alpine w-full"
            style={{ height: `${height}px` }}
          >
            <AgGridReact<FileMetadata>
              ref={gridRef}
              rowData={files}
              columnDefs={columnDefs}
              defaultColDef={defaultColDef}
              gridOptions={gridOptions}
              onGridReady={onGridReady}
              onSelectionChanged={onSelectionChanged}
              onCellClicked={onCellClicked}
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default FileMetadataGrid;
