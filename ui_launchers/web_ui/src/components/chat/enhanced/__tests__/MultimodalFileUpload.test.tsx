
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import MultimodalFileUpload from '../MultimodalFileUpload';
import { Attachment } from '@/types/enhanced-chat';

// Mock the toast hook
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn()
  })
}));

// Mock URL.createObjectURL
global.URL.createObjectURL = vi.fn(() => 'mock-url');
global.URL.revokeObjectURL = vi.fn();

// Mock Image constructor for image dimension testing
global.Image = class {
  width = 800;
  height = 600;
  onload: (() => void) | null = null;
  
  constructor() {
    setTimeout(() => {
      if (this.onload) {
        this.onload();
      }
    }, 0);
  }
  
  set src(value: string) {
    // Trigger onload after setting src
  }
} as any;

describe('MultimodalFileUpload', () => {
  const mockOnFilesUploaded = vi.fn();
  const mockOnFileRemoved = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders upload area with correct text', () => {
    render(
      <MultimodalFileUpload
        onFilesUploaded={mockOnFilesUploaded}
        onFileRemoved={mockOnFileRemoved}
      />
    );

    expect(screen.getByText('Drop files here or click to upload')).toBeInTheDocument();
    expect(screen.getByText('Support for images, documents, code files, and more')).toBeInTheDocument();
    expect(screen.getByText('Max 10MB')).toBeInTheDocument();
    expect(screen.getByText('Up to 5 files')).toBeInTheDocument();
  });

  it('handles file selection through input', async () => {
    render(
      <MultimodalFileUpload
        onFilesUploaded={mockOnFilesUploaded}
        onFileRemoved={mockOnFileRemoved}
      />
    );

    // Create a mock file
    const file = new File(['test content'], 'test.txt', { type: 'text/plain' });
    
    // Get the hidden file input
    const fileInput = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement;
    
    // Mock the files property
    Object.defineProperty(fileInput, 'files', {
      value: [file],
      writable: false,
    });

    // Trigger change event
    fireEvent.change(fileInput);

    // Wait for file processing
    await waitFor(() => {
      expect(mockOnFilesUploaded).toHaveBeenCalledWith(
        expect.arrayContaining([
          expect.objectContaining({
            name: 'test.txt',
            type: 'document',
            size: file.size,
            mimeType: 'text/plain'
          })
        ])
      );
    }, { timeout: 3000 });
  });

  it('validates file size limits', async () => {
    const mockToast = vi.fn();
    vi.mocked(require('@/hooks/use-toast').useToast).mockReturnValue({ toast: mockToast });

    render(
      <MultimodalFileUpload
        onFilesUploaded={mockOnFilesUploaded}
        onFileRemoved={mockOnFileRemoved}
        maxFileSize={1} // 1MB limit
      />
    );

    // Create a large mock file (2MB)
    const largeFile = new File(['x'.repeat(2 * 1024 * 1024)], 'large.txt', { type: 'text/plain' });
    
    const fileInput = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement;
    Object.defineProperty(fileInput, 'files', {
      value: [largeFile],
      writable: false,
    });

    fireEvent.change(fileInput);

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        variant: 'destructive',
        title: 'File Upload Error',
        description: expect.stringContaining('File size exceeds 1MB limit')
      });
    });
  });

  it('validates maximum file count', async () => {
    const mockToast = vi.fn();
    vi.mocked(require('@/hooks/use-toast').useToast).mockReturnValue({ toast: mockToast });

    render(
      <MultimodalFileUpload
        onFilesUploaded={mockOnFilesUploaded}
        onFileRemoved={mockOnFileRemoved}
        maxFiles={2}
      />
    );

    // Create multiple files
    const files = [
      new File(['content1'], 'file1.txt', { type: 'text/plain' }),
      new File(['content2'], 'file2.txt', { type: 'text/plain' }),
      new File(['content3'], 'file3.txt', { type: 'text/plain' })
    ];
    
    const fileInput = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement;
    Object.defineProperty(fileInput, 'files', {
      value: files,
      writable: false,
    });

    fireEvent.change(fileInput);

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        variant: 'destructive',
        title: 'File Upload Error',
        description: expect.stringContaining('Maximum 2 files allowed')
      });
    });
  });

  it('detects file types correctly', async () => {
    render(
      <MultimodalFileUpload
        onFilesUploaded={mockOnFilesUploaded}
        onFileRemoved={mockOnFileRemoved}
      />
    );

    const imageFile = new File(['image data'], 'test.jpg', { type: 'image/jpeg' });
    const codeFile = new File(['console.log("test")'], 'test.js', { type: 'application/javascript' });
    
    const fileInput = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement;
    Object.defineProperty(fileInput, 'files', {
      value: [imageFile, codeFile],
      writable: false,
    });

    fireEvent.change(fileInput);

    await waitFor(() => {
      expect(mockOnFilesUploaded).toHaveBeenCalledWith(
        expect.arrayContaining([
          expect.objectContaining({
            name: 'test.jpg',
            type: 'image'
          }),
          expect.objectContaining({
            name: 'test.js',
            type: 'code'
          })
        ])
      );
    }, { timeout: 3000 });
  });

  it('handles drag and drop', async () => {
    render(
      <MultimodalFileUpload
        onFilesUploaded={mockOnFilesUploaded}
        onFileRemoved={mockOnFileRemoved}
      />
    );

    const uploadArea = screen.getByText('Drop files here or click to upload').closest('div');
    const file = new File(['test content'], 'dropped.txt', { type: 'text/plain' });

    // Mock drag events
    const dragEvent = {
      preventDefault: vi.fn(),
      dataTransfer: {
        files: [file]
      }
    } as any;

    fireEvent.dragOver(uploadArea!, dragEvent);
    fireEvent.drop(uploadArea!, dragEvent);

    await waitFor(() => {
      expect(mockOnFilesUploaded).toHaveBeenCalledWith(
        expect.arrayContaining([
          expect.objectContaining({
            name: 'dropped.txt',
            type: 'document'
          })
        ])
      );
    }, { timeout: 3000 });
  });

  it('shows upload progress', async () => {
    render(
      <MultimodalFileUpload
        onFilesUploaded={mockOnFilesUploaded}
        onFileRemoved={mockOnFileRemoved}
      />
    );

    const file = new File(['test content'], 'test.txt', { type: 'text/plain' });
    const fileInput = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement;
    Object.defineProperty(fileInput, 'files', {
      value: [file],
      writable: false,
    });

    fireEvent.change(fileInput);

    // Should show uploading status
    await waitFor(() => {
      expect(screen.getByText('Uploading...')).toBeInTheDocument();
    });

    // Should show analyzing status
    await waitFor(() => {
      expect(screen.getByText('Analyzing...')).toBeInTheDocument();
    }, { timeout: 2000 });

    // Should complete
    await waitFor(() => {
      expect(screen.getByText('Complete')).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('displays uploaded files with metadata', async () => {
    render(
      <MultimodalFileUpload
        onFilesUploaded={mockOnFilesUploaded}
        onFileRemoved={mockOnFileRemoved}
      />
    );

    const file = new File(['test content'], 'test.txt', { type: 'text/plain' });
    const fileInput = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement;
    Object.defineProperty(fileInput, 'files', {
      value: [file],
      writable: false,
    });

    fireEvent.change(fileInput);

    await waitFor(() => {
      expect(screen.getByText('Attached Files (1)')).toBeInTheDocument();
      expect(screen.getByText('test.txt')).toBeInTheDocument();
      expect(screen.getByText('document')).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('handles file removal', async () => {
    render(
      <MultimodalFileUpload
        onFilesUploaded={mockOnFilesUploaded}
        onFileRemoved={mockOnFileRemoved}
      />
    );

    const file = new File(['test content'], 'test.txt', { type: 'text/plain' });
    const fileInput = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement;
    Object.defineProperty(fileInput, 'files', {
      value: [file],
      writable: false,
    });

    fireEvent.change(fileInput);

    // Wait for file to be uploaded and displayed
    await waitFor(() => {
      expect(screen.getByText('test.txt')).toBeInTheDocument();
    }, { timeout: 3000 });

    // Find and click remove button
    const removeButton = screen.getByRole('button', { name: /remove/i });
    fireEvent.click(removeButton);

    expect(mockOnFileRemoved).toHaveBeenCalled();
  });

  it('handles image files with dimension extraction', async () => {
    render(
      <MultimodalFileUpload
        onFilesUploaded={mockOnFilesUploaded}
        onFileRemoved={mockOnFileRemoved}
        enableImageAnalysis={true}
      />
    );

    const imageFile = new File(['image data'], 'test.jpg', { type: 'image/jpeg' });
    const fileInput = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement;
    Object.defineProperty(fileInput, 'files', {
      value: [imageFile],
      writable: false,
    });

    fireEvent.change(fileInput);

    await waitFor(() => {
      expect(mockOnFilesUploaded).toHaveBeenCalledWith(
        expect.arrayContaining([
          expect.objectContaining({
            name: 'test.jpg',
            type: 'image',
            metadata: expect.objectContaining({
              dimensions: { width: 800, height: 600 }
            })
          })
        ])
      );
    }, { timeout: 3000 });
  });

  it('validates accepted file types', async () => {
    const mockToast = vi.fn();
    vi.mocked(require('@/hooks/use-toast').useToast).mockReturnValue({ toast: mockToast });

    render(
      <MultimodalFileUpload
        onFilesUploaded={mockOnFilesUploaded}
        onFileRemoved={mockOnFileRemoved}
        acceptedTypes={['image/*']}
      />
    );

    const textFile = new File(['test content'], 'test.txt', { type: 'text/plain' });
    const fileInput = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement;
    Object.defineProperty(fileInput, 'files', {
      value: [textFile],
      writable: false,
    });

    fireEvent.change(fileInput);

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        variant: 'destructive',
        title: 'File Upload Error',
        description: expect.stringContaining('File type not supported')
      });
    });
  });
});