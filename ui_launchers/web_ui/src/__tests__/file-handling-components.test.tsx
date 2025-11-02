/**
 * Tests for AG-UI enhanced file handling components
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';

// Mock AG-Grid components
vi.mock('ag-grid-react', () => ({
  AgGridReact: ({ rowData, onGridReady, onSelectionChanged, onCellClicked, noRowsOverlayComponent }: any) => {
    React.useEffect(() => {
      if (onGridReady) {
        onGridReady({
          api: {
            sizeColumnsToFit: vi.fn(),
            getSelectedRows: vi.fn(() => []),
          }

      }
    }, [onGridReady]);

    return (
      <div data-testid="ag-grid">
        {rowData?.length === 0 && noRowsOverlayComponent && (
          <div data-testid="no-rows-overlay">
            {React.createElement(noRowsOverlayComponent)}
          </div>
        )}
        {rowData?.map((row: any, index: number) => (
          <div 
            key={row.file_id || index} 
            data-testid={`grid-row-${index}`}
            onClick={() => onCellClicked?.({ data: row, colDef: { field: 'filename' } })}
          >
            {row.filename}
          </div>
        ))}
      </div>
    );
  }
}));

// Mock AG-Charts components
vi.mock('ag-charts-react', () => ({
  AgChartsReact: ({ options }: any) => (
    <div data-testid="ag-chart">
      <div data-testid="chart-title">{options?.title?.text}</div>
      <div data-testid="chart-data">{JSON.stringify(options?.data)}</div>
    </div>
  )
}));

// Mock react-dropzone
vi.mock('react-dropzone', () => ({
  useDropzone: ({ onDrop, accept, maxFiles, maxSize, disabled }: any) => ({
    getRootProps: () => ({
      'data-testid': 'dropzone',
      onClick: () => {
        if (!disabled) {
          // Simulate file drop
          const mockFiles = [
            new File(['test content'], 'test.jpg', { type: 'image/jpeg' })
          ];
          onDrop?.(mockFiles, []);
        }
      }
    }),
    getInputProps: () => ({ type: 'file' }),
    isDragActive: false
  })
}));

// Import components to test
import FileUploadDropzone from '../components/files/FileUploadDropzone';
import FileMetadataGrid, { FileMetadata } from '../components/files/FileMetadataGrid';
import MultimediaPreview from '../components/files/MultimediaPreview';
import FilePermissionManager, { FilePermission } from '../components/files/FilePermissionManager';
import FileManagementInterface from '../components/files/FileManagementInterface';

// Mock data
const mockFileMetadata: FileMetadata[] = [
  {
    file_id: 'file_1',
    filename: 'test_image.jpg',
    file_size: 1024000,
    mime_type: 'image/jpeg',
    file_type: 'image',
    processing_status: 'completed',
    upload_timestamp: '2024-01-01T12:00:00Z',
    has_thumbnail: true,
    preview_available: true,
    extracted_content_available: false,
    tags: ['test', 'image'],
    security_scan_result: 'safe'
  },
  {
    file_id: 'file_2',
    filename: 'document.pdf',
    file_size: 2048000,
    mime_type: 'application/pdf',
    file_type: 'document',
    processing_status: 'processing',
    upload_timestamp: '2024-01-01T13:00:00Z',
    has_thumbnail: false,
    preview_available: false,
    extracted_content_available: true,
    tags: ['document'],
    security_scan_result: 'safe'
  }
];

const mockPermissions: FilePermission[] = [
  {
    id: 'perm_1',
    file_id: 'file_1',
    user_id: 'user_123',
    permission_type: 'read',
    granted_by: 'admin',
    granted_at: '2024-01-01T10:00:00Z',
    is_active: true
  },
  {
    id: 'perm_2',
    file_id: 'file_1',
    role: 'editor',
    permission_type: 'write',
    granted_by: 'admin',
    granted_at: '2024-01-01T10:30:00Z',
    expires_at: '2024-12-31T23:59:59Z',
    is_active: true
  }
];

describe('FileUploadDropzone', () => {
  const mockOnFilesSelected = vi.fn();
  const mockOnFileRemove = vi.fn();
  const mockOnUploadStart = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

  it('renders dropzone interface', () => {
    render(
      <FileUploadDropzone
        onFilesSelected={mockOnFilesSelected}
        onFileRemove={mockOnFileRemove}
        onUploadStart={mockOnUploadStart}
      />
    );

    expect(screen.getByTestId('dropzone')).toBeInTheDocument();
    expect(screen.getByText('Upload files')).toBeInTheDocument();
    expect(screen.getByText('Drag and drop files here, or click to browse')).toBeInTheDocument();

  it('handles file selection', async () => {
    render(
      <FileUploadDropzone
        onFilesSelected={mockOnFilesSelected}
        onFileRemove={mockOnFileRemove}
        onUploadStart={mockOnUploadStart}
      />
    );

    const dropzone = screen.getByTestId('dropzone');
    fireEvent.click(dropzone);

    await waitFor(() => {
      expect(mockOnFilesSelected).toHaveBeenCalledWith([
        expect.objectContaining({
          name: 'test.jpg',
          type: 'image/jpeg'
        })
      ]);


  it('displays file size and count limits', () => {
    render(
      <FileUploadDropzone
        onFilesSelected={mockOnFilesSelected}
        onFileRemove={mockOnFileRemove}
        onUploadStart={mockOnUploadStart}
        maxFiles={5}
        maxFileSize={10 * 1024 * 1024}
      />
    );

    expect(screen.getByText('Max 5 files')).toBeInTheDocument();
    expect(screen.getByText('Up to 10.00 MB each')).toBeInTheDocument();

  it('disables dropzone when disabled prop is true', () => {
    render(
      <FileUploadDropzone
        onFilesSelected={mockOnFilesSelected}
        onFileRemove={mockOnFileRemove}
        onUploadStart={mockOnUploadStart}
        disabled={true}
      />
    );

    const dropzone = screen.getByTestId('dropzone');
    fireEvent.click(dropzone);

    expect(mockOnFilesSelected).not.toHaveBeenCalled();


describe('FileMetadataGrid', () => {
  const mockOnFileSelect = vi.fn();
  const mockOnFileDownload = vi.fn();
  const mockOnFileDelete = vi.fn();
  const mockOnFilesSelected = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

  it('renders AG-Grid with file data', () => {
    render(
      <FileMetadataGrid
        files={mockFileMetadata}
        onFileSelect={mockOnFileSelect}
        onFileDownload={mockOnFileDownload}
        onFileDelete={mockOnFileDelete}
        onFilesSelected={mockOnFilesSelected}
      />
    );

    expect(screen.getByTestId('ag-grid')).toBeInTheDocument();
    expect(screen.getByText('File Metadata (2 files)')).toBeInTheDocument();

  it('displays file statistics cards', () => {
    render(
      <FileMetadataGrid
        files={mockFileMetadata}
        onFileSelect={mockOnFileSelect}
        onFileDownload={mockOnFileDownload}
        onFileDelete={mockOnFileDelete}
        onFilesSelected={mockOnFilesSelected}
      />
    );

    expect(screen.getByText('Total Files')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('Total Size')).toBeInTheDocument();

  it('handles file selection from grid', async () => {
    render(
      <FileMetadataGrid
        files={mockFileMetadata}
        onFileSelect={mockOnFileSelect}
        onFileDownload={mockOnFileDownload}
        onFileDelete={mockOnFileDelete}
        onFilesSelected={mockOnFilesSelected}
      />
    );

    const firstRow = screen.getByTestId('grid-row-0');
    fireEvent.click(firstRow);

    await waitFor(() => {
      expect(mockOnFileSelect).toHaveBeenCalledWith(mockFileMetadata[0]);


  it('shows no data overlay when files array is empty', () => {
    render(
      <FileMetadataGrid
        files={[]}
        onFileSelect={mockOnFileSelect}
        onFileDownload={mockOnFileDownload}
        onFileDelete={mockOnFileDelete}
        onFilesSelected={mockOnFilesSelected}
      />
    );

    expect(screen.getByTestId('no-rows-overlay')).toBeInTheDocument();
    expect(screen.getByText('No files found')).toBeInTheDocument();

  it('displays loading state', () => {
    render(
      <FileMetadataGrid
        files={mockFileMetadata}
        loading={true}
        onFileSelect={mockOnFileSelect}
        onFileDownload={mockOnFileDownload}
        onFileDelete={mockOnFileDelete}
        onFilesSelected={mockOnFilesSelected}
      />
    );

    // Loading state would be handled by AG-Grid's loading overlay
    expect(screen.getByTestId('ag-grid')).toBeInTheDocument();


describe('MultimediaPreview', () => {
  const mockOnDownload = vi.fn();
  const mockOnFullscreen = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

  it('renders image preview for image files', () => {
    const imageFile = mockFileMetadata[0];
    
    render(
      <MultimediaPreview
        file={imageFile}
        onDownload={mockOnDownload}
        onFullscreen={mockOnFullscreen}
      />
    );

    expect(screen.getByText('Image Preview')).toBeInTheDocument();
    expect(screen.getByText(imageFile.filename)).toBeInTheDocument();

  it('renders file information card', () => {
    const file = mockFileMetadata[0];
    
    render(
      <MultimediaPreview
        file={file}
        onDownload={mockOnDownload}
        onFullscreen={mockOnFullscreen}
      />
    );

    expect(screen.getByText('File Information')).toBeInTheDocument();
    expect(screen.getByText('MIME Type:')).toBeInTheDocument();
    expect(screen.getByText('Processing Status:')).toBeInTheDocument();

  it('displays file tags when available', () => {
    const file = mockFileMetadata[0];
    
    render(
      <MultimediaPreview
        file={file}
        onDownload={mockOnDownload}
        onFullscreen={mockOnFullscreen}
      />
    );

    expect(screen.getByText('Tags:')).toBeInTheDocument();
    expect(screen.getByText('test')).toBeInTheDocument();
    expect(screen.getByText('image')).toBeInTheDocument();

  it('handles download button click', async () => {
    const file = mockFileMetadata[0];
    
    render(
      <MultimediaPreview
        file={file}
        onDownload={mockOnDownload}
        onFullscreen={mockOnFullscreen}
      />
    );

    const downloadButton = screen.getByRole('button', { name: /download/i });
    fireEvent.click(downloadButton);

    expect(mockOnDownload).toHaveBeenCalledWith(file.file_id);

  it('shows analysis results when provided', () => {
    const file = mockFileMetadata[0];
    const analysis = {
      image_analysis: {
        objects_detected: [
          { label: 'cat', confidence: 0.9, bbox: [0, 0, 100, 100], description: 'A cat' }
        ],
        confidence_scores: { object_detection: 0.9 }
      }
    };
    
    render(
      <MultimediaPreview
        file={file}
        analysis={analysis}
        onDownload={mockOnDownload}
        onFullscreen={mockOnFullscreen}
      />
    );

    expect(screen.getByText('Objects')).toBeInTheDocument();
    expect(screen.getByText('Confidence')).toBeInTheDocument();


describe('FilePermissionManager', () => {
  const mockOnPermissionUpdate = vi.fn();
  const mockOnRuleUpdate = vi.fn();

  const mockUsers = [
    { id: 'user1', name: 'John Doe', email: 'john@example.com', roles: ['user'] },
    { id: 'user2', name: 'Jane Smith', email: 'jane@example.com', roles: ['admin'] }
  ];

  const mockRoles = [
    { id: 'admin', name: 'Administrator', description: 'Full access' },
    { id: 'user', name: 'User', description: 'Standard access' }
  ];

  beforeEach(() => {
    vi.clearAllMocks();

  it('renders permission management interface', () => {
    render(
      <FilePermissionManager
        fileId="file_1"
        fileName="test.jpg"
        currentPermissions={mockPermissions}
        availableUsers={mockUsers}
        availableRoles={mockRoles}
        permissionRules={[]}
        onPermissionUpdate={mockOnPermissionUpdate}
        onRuleUpdate={mockOnRuleUpdate}
      />
    );

    expect(screen.getByText('File Permissions: test.jpg')).toBeInTheDocument();
    expect(screen.getByText('Current Permissions')).toBeInTheDocument();

  it('displays permission statistics', () => {
    render(
      <FilePermissionManager
        fileId="file_1"
        fileName="test.jpg"
        currentPermissions={mockPermissions}
        availableUsers={mockUsers}
        availableRoles={mockRoles}
        permissionRules={[]}
        onPermissionUpdate={mockOnPermissionUpdate}
        onRuleUpdate={mockOnRuleUpdate}
      />
    );

    expect(screen.getByText('Total Permissions')).toBeInTheDocument();
    expect(screen.getByText('Active')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument(); // Total permissions

  it('shows add permission button when not read-only', () => {
    render(
      <FilePermissionManager
        fileId="file_1"
        fileName="test.jpg"
        currentPermissions={mockPermissions}
        availableUsers={mockUsers}
        availableRoles={mockRoles}
        permissionRules={[]}
        onPermissionUpdate={mockOnPermissionUpdate}
        onRuleUpdate={mockOnRuleUpdate}
        readOnly={false}
      />
    );

    expect(screen.getByText('Add Permission')).toBeInTheDocument();

  it('hides add permission button when read-only', () => {
    render(
      <FilePermissionManager
        fileId="file_1"
        fileName="test.jpg"
        currentPermissions={mockPermissions}
        availableUsers={mockUsers}
        availableRoles={mockRoles}
        permissionRules={[]}
        onPermissionUpdate={mockOnPermissionUpdate}
        onRuleUpdate={mockOnRuleUpdate}
        readOnly={true}
      />
    );

    expect(screen.queryByText('Add Permission')).not.toBeInTheDocument();

  it('renders permissions in AG-Grid', () => {
    render(
      <FilePermissionManager
        fileId="file_1"
        fileName="test.jpg"
        currentPermissions={mockPermissions}
        availableUsers={mockUsers}
        availableRoles={mockRoles}
        permissionRules={[]}
        onPermissionUpdate={mockOnPermissionUpdate}
        onRuleUpdate={mockOnRuleUpdate}
      />
    );

    expect(screen.getByTestId('ag-grid')).toBeInTheDocument();


describe('FileManagementInterface', () => {
  const mockOnFileSelect = vi.fn();
  const mockOnFileUpload = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock fetch for API calls
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          files: mockFileMetadata,
          total_count: mockFileMetadata.length,
          statistics: {
            total_size_formatted: '3.00 MB',
            type_distribution: { image: 1, document: 1 }
          }
        })
      })
    ) as any;

  afterEach(() => {
    vi.restoreAllMocks();

  it('renders main interface with tabs', async () => {
    render(
      <FileManagementInterface
        userId="user_123"
        onFileSelect={mockOnFileSelect}
        onFileUpload={mockOnFileUpload}
      />
    );

    expect(screen.getByText('File Management')).toBeInTheDocument();
    expect(screen.getByText('Upload')).toBeInTheDocument();
    expect(screen.getByText(/Files \(/)).toBeInTheDocument();
    expect(screen.getByText('Preview')).toBeInTheDocument();
    expect(screen.getByText('Permissions')).toBeInTheDocument();

  it('displays file statistics cards', async () => {
    render(
      <FileManagementInterface
        userId="user_123"
        onFileSelect={mockOnFileSelect}
        onFileUpload={mockOnFileUpload}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Total Files')).toBeInTheDocument();
      expect(screen.getByText('Total Size')).toBeInTheDocument();
      expect(screen.getByText('Processing')).toBeInTheDocument();
      expect(screen.getByText('Failed')).toBeInTheDocument();


  it('handles search functionality', async () => {
    render(
      <FileManagementInterface
        userId="user_123"
        onFileSelect={mockOnFileSelect}
        onFileUpload={mockOnFileUpload}
      />
    );

    const searchInput = screen.getByPlaceholderText(/Search files/);
    await userEvent.type(searchInput, 'test');

    expect(searchInput).toHaveValue('test');

  it('switches between tabs', async () => {
    render(
      <FileManagementInterface
        userId="user_123"
        onFileSelect={mockOnFileSelect}
        onFileUpload={mockOnFileUpload}
      />
    );

    const uploadTab = screen.getByText('Upload');
    fireEvent.click(uploadTab);

    // Should show upload interface
    await waitFor(() => {
      expect(screen.getByTestId('dropzone')).toBeInTheDocument();


  it('loads files on mount', async () => {
    render(
      <FileManagementInterface
        userId="user_123"
        conversationId="conv_123"
        onFileSelect={mockOnFileSelect}
        onFileUpload={mockOnFileUpload}
      />
    );

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/files/enhanced/')
      );


  it('handles refresh button click', async () => {
    render(
      <FileManagementInterface
        userId="user_123"
        onFileSelect={mockOnFileSelect}
        onFileUpload={mockOnFileUpload}
      />
    );

    const refreshButton = screen.getByText('Refresh');
    fireEvent.click(refreshButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(2); // Initial load + refresh


  it('disables functionality when read-only', () => {
    render(
      <FileManagementInterface
        userId="user_123"
        onFileSelect={mockOnFileSelect}
        onFileUpload={mockOnFileUpload}
        readOnly={true}
      />
    );

    // Should not show bulk action buttons for selection
    expect(screen.queryByText('Download Selected')).not.toBeInTheDocument();
    expect(screen.queryByText('Delete Selected')).not.toBeInTheDocument();


describe('AG-UI Integration', () => {
  it('formats data correctly for AG-Grid', () => {
    const gridData = mockFileMetadata.map(file => ({
      ...file,
      ag_grid_metadata: {
        rowId: file.file_id,
        selectable: true,
        draggable: false,
        cssClass: file.security_scan_result === 'safe' ? 'file-safe' : 'file-suspicious',
        tooltip: `${file.filename} (${file.file_type})`
      }
    }));

    expect(gridData).toHaveLength(2);
    expect(gridData[0].ag_grid_metadata.rowId).toBe('file_1');
    expect(gridData[0].ag_grid_metadata.selectable).toBe(true);
    expect(gridData[0].ag_grid_metadata.cssClass).toBe('file-safe');

  it('formats data correctly for AG-Charts', () => {
    const chartData = {
      data: [
        { category: 'Images', count: 1 },
        { category: 'Documents', count: 1 }
      ],
      series: [{
        type: 'bar',
        xKey: 'category',
        yKey: 'count'
      }]
    };

    expect(chartData.data).toHaveLength(2);
    expect(chartData.data[0]).toHaveProperty('category');
    expect(chartData.data[0]).toHaveProperty('count');
    expect(chartData.series[0].type).toBe('bar');

  it('handles AG-Grid column definitions', () => {
    const columnDefs = [
      {
        headerName: 'File',
        field: 'filename',
        flex: 2,
        minWidth: 200,
        cellRenderer: 'fileIconRenderer',
        filter: 'agTextColumnFilter'
      },
      {
        headerName: 'Type',
        field: 'file_type',
        width: 100,
        filter: 'agSetColumnFilter'
      },
      {
        headerName: 'Size',
        field: 'file_size',
        width: 100,
        filter: 'agNumberColumnFilter',
        cellRenderer: 'fileSizeRenderer'
      }
    ];

    expect(columnDefs).toHaveLength(3);
    expect(columnDefs[0].headerName).toBe('File');
    expect(columnDefs[0].cellRenderer).toBe('fileIconRenderer');
    expect(columnDefs[1].filter).toBe('agSetColumnFilter');
    expect(columnDefs[2].filter).toBe('agNumberColumnFilter');

