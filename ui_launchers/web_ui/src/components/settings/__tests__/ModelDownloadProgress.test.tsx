
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { vi } from 'vitest';
import ModelDownloadProgress from '../ModelDownloadProgress';
import { DownloadTask } from '@/hooks/use-download-status';

// Mock the useToast hook
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

const mockDownloadTask: DownloadTask = {
  id: 'test-task-1',
  modelId: 'test-model',
  modelName: 'Test Model',
  status: 'downloading',
  progress: 45,
  downloadedBytes: 450000000,
  totalBytes: 1000000000,
  speed: 5000000, // 5MB/s
  estimatedTimeRemaining: 110, // 110 seconds
  startTime: Date.now() / 1000 - 100,
  lastUpdateTime: Date.now() / 1000,
};

describe('ModelDownloadProgress', () => {
  const mockOnCancel = vi.fn();
  const mockOnPause = vi.fn();
  const mockOnResume = vi.fn();
  const mockOnRetry = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders downloading task correctly', () => {
    render(
      <ModelDownloadProgress
        task={mockDownloadTask}
        onCancel={mockOnCancel}
        onPause={mockOnPause}
        onResume={mockOnResume}
      />
    );

    expect(screen.getByText('Test Model')).toBeInTheDocument();
    expect(screen.getByText('45%')).toBeInTheDocument();
    expect(screen.getByText('Downloading')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /pause/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
  });

  it('renders compact view correctly', () => {
    render(
      <ModelDownloadProgress
        task={mockDownloadTask}
        onCancel={mockOnCancel}
        compact={true}
      />
    );

    expect(screen.getByText('Test Model')).toBeInTheDocument();
    expect(screen.getByText('45%')).toBeInTheDocument();
  });

  it('renders error state correctly', () => {
    const errorTask: DownloadTask = {
      ...mockDownloadTask,
      status: 'error',
      error: 'Network connection failed',
    };

    render(
      <ModelDownloadProgress
        task={errorTask}
        onCancel={mockOnCancel}
        onRetry={mockOnRetry}
      />
    );

    expect(screen.getByText('Error')).toBeInTheDocument();
    expect(screen.getByText('Network connection failed')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });

  it('renders completed state correctly', () => {
    const completedTask: DownloadTask = {
      ...mockDownloadTask,
      status: 'completed',
      progress: 100,
    };

    render(
      <ModelDownloadProgress
        task={completedTask}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getByText('Completed')).toBeInTheDocument();
    expect(screen.getByText('Download completed successfully')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /remove/i })).toBeInTheDocument();
  });

  it('calls onCancel when cancel button is clicked', async () => {
    render(
      <ModelDownloadProgress
        task={mockDownloadTask}
        onCancel={mockOnCancel}
      />
    );

    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    fireEvent.click(cancelButton);

    await waitFor(() => {
      expect(mockOnCancel).toHaveBeenCalledWith('test-task-1');
    });
  });

  it('calls onPause when pause button is clicked', async () => {
    render(
      <ModelDownloadProgress
        task={mockDownloadTask}
        onCancel={mockOnCancel}
        onPause={mockOnPause}
      />
    );

    const pauseButton = screen.getByRole('button', { name: /pause/i });
    fireEvent.click(pauseButton);

    await waitFor(() => {
      expect(mockOnPause).toHaveBeenCalledWith('test-task-1');
    });
  });

  it('formats bytes correctly', () => {
    render(
      <ModelDownloadProgress
        task={mockDownloadTask}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getByText(/429.15 MB \/ 953.67 MB/)).toBeInTheDocument();
  });

  it('formats speed correctly', () => {
    render(
      <ModelDownloadProgress
        task={mockDownloadTask}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getByText(/4.77 MB\/s/)).toBeInTheDocument();
  });

  it('formats time correctly', () => {
    render(
      <ModelDownloadProgress
        task={mockDownloadTask}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getByText(/2m/)).toBeInTheDocument();
  });
});