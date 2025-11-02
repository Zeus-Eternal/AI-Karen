import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { vi } from 'vitest';
import DownloadManager from '../DownloadManager';
import { useDownloadStatus } from '@/hooks/use-download-status';
import { useToast } from '@/hooks/use-toast';

// Mock the hooks
vi.mock('@/hooks/use-download-status');
vi.mock('@/hooks/use-toast');

const mockToast = vi.fn();
(useToast as any).mockReturnValue({ toast: mockToast });

const mockDownloadTasks = [
  {
    id: 'task-1',
    modelId: 'tinyllama-1.1b-chat-q4',
    modelName: 'TinyLlama 1.1B Chat Q4_K_M',
    status: 'downloading' as const,
    progress: 45.5,
    downloadedBytes: 304857600, // ~291 MB
    totalBytes: 669000000, // ~638 MB
    speed: 5242880, // 5 MB/s
    estimatedTimeRemaining: 69, // 69 seconds
    startTime: Date.now() / 1000 - 100,
    lastUpdateTime: Date.now() / 1000,
  },
  {
    id: 'task-2',
    modelId: 'phi-2-q4',
    modelName: 'Microsoft Phi-2 Q4_K_M',
    status: 'completed' as const,
    progress: 100,
    downloadedBytes: 1600000000,
    totalBytes: 1600000000,
    speed: 0,
    estimatedTimeRemaining: 0,
    startTime: Date.now() / 1000 - 300,
    lastUpdateTime: Date.now() / 1000 - 10,
  },
  {
    id: 'task-3',
    modelId: 'failed-model',
    modelName: 'Failed Model',
    status: 'error' as const,
    progress: 25,
    downloadedBytes: 250000000,
    totalBytes: 1000000000,
    speed: 0,
    estimatedTimeRemaining: 0,
    startTime: Date.now() / 1000 - 200,
    lastUpdateTime: Date.now() / 1000 - 50,
    error: 'Network connection failed',
  },
  {
    id: 'task-4',
    modelId: 'paused-model',
    modelName: 'Paused Model',
    status: 'paused' as const,
    progress: 60,
    downloadedBytes: 600000000,
    totalBytes: 1000000000,
    speed: 0,
    estimatedTimeRemaining: 0,
    startTime: Date.now() / 1000 - 150,
    lastUpdateTime: Date.now() / 1000 - 30,
  }
];

const mockUseDownloadStatus = useDownloadStatus as any;

describe('DownloadManager', () => {
  const mockCancelDownload = vi.fn();
  const mockPauseDownload = vi.fn();
  const mockResumeDownload = vi.fn();
  const mockRetryDownload = vi.fn();
  const mockClearCompleted = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    
    mockUseDownloadStatus.mockReturnValue({
      tasks: mockDownloadTasks,
      cancelDownload: mockCancelDownload,
      pauseDownload: mockPauseDownload,
      resumeDownload: mockResumeDownload,
      retryDownload: mockRetryDownload,
      clearCompleted: mockClearCompleted,
      isLoading: false,
      error: null,
    });
  });

  it('renders download manager with tasks', () => {
    render(<DownloadManager />);
    
    expect(screen.getByText('Download Manager')).toBeInTheDocument();
    expect(screen.getByText('TinyLlama 1.1B Chat Q4_K_M')).toBeInTheDocument();
    expect(screen.getByText('Microsoft Phi-2 Q4_K_M')).toBeInTheDocument();
    expect(screen.getByText('Failed Model')).toBeInTheDocument();
    expect(screen.getByText('Paused Model')).toBeInTheDocument();
  });

  it('displays download statistics', () => {
    render(<DownloadManager />);
    
    expect(screen.getByText('4 downloads')).toBeInTheDocument();
    expect(screen.getByText('1 active')).toBeInTheDocument();
    expect(screen.getByText('1 completed')).toBeInTheDocument();
    expect(screen.getByText('1 failed')).toBeInTheDocument();
  });

  it('shows downloading task with progress', () => {
    render(<DownloadManager />);
    
    const downloadingTask = screen.getByText('TinyLlama 1.1B Chat Q4_K_M').closest('[data-testid="download-task"]');
    expect(downloadingTask).toBeInTheDocument();
    
    if (downloadingTask) {
      expect(downloadingTask).toHaveTextContent('45.5%');
      expect(downloadingTask).toHaveTextContent('Downloading');
      expect(downloadingTask).toHaveTextContent('5.00 MB/s');
      expect(downloadingTask).toHaveTextContent('1m 9s');
    }
  });

  it('shows completed task', () => {
    render(<DownloadManager />);
    
    const completedTask = screen.getByText('Microsoft Phi-2 Q4_K_M').closest('[data-testid="download-task"]');
    expect(completedTask).toBeInTheDocument();
    
    if (completedTask) {
      expect(completedTask).toHaveTextContent('100%');
      expect(completedTask).toHaveTextContent('Completed');
    }
  });

  it('shows error task with error message', () => {
    render(<DownloadManager />);
    
    const errorTask = screen.getByText('Failed Model').closest('[data-testid="download-task"]');
    expect(errorTask).toBeInTheDocument();
    
    if (errorTask) {
      expect(errorTask).toHaveTextContent('Error');
      expect(errorTask).toHaveTextContent('Network connection failed');
    }
  });

  it('shows paused task', () => {
    render(<DownloadManager />);
    
    const pausedTask = screen.getByText('Paused Model').closest('[data-testid="download-task"]');
    expect(pausedTask).toBeInTheDocument();
    
    if (pausedTask) {
      expect(pausedTask).toHaveTextContent('60%');
      expect(pausedTask).toHaveTextContent('Paused');
    }
  });

  it('cancels download when cancel button is clicked', async () => {
    render(<DownloadManager />);
    
    const cancelButton = screen.getByRole('button', { name: /cancel.*tinyllama/i });
    fireEvent.click(cancelButton);
    
    await waitFor(() => {
      expect(mockCancelDownload).toHaveBeenCalledWith('task-1');
    });
  });

  it('pauses download when pause button is clicked', async () => {
    render(<DownloadManager />);
    
    const pauseButton = screen.getByRole('button', { name: /pause.*tinyllama/i });
    fireEvent.click(pauseButton);
    
    await waitFor(() => {
      expect(mockPauseDownload).toHaveBeenCalledWith('task-1');
    });
  });

  it('resumes download when resume button is clicked', async () => {
    render(<DownloadManager />);
    
    const resumeButton = screen.getByRole('button', { name: /resume.*paused/i });
    fireEvent.click(resumeButton);
    
    await waitFor(() => {
      expect(mockResumeDownload).toHaveBeenCalledWith('task-4');
    });
  });

  it('retries download when retry button is clicked', async () => {
    render(<DownloadManager />);
    
    const retryButton = screen.getByRole('button', { name: /retry.*failed/i });
    fireEvent.click(retryButton);
    
    await waitFor(() => {
      expect(mockRetryDownload).toHaveBeenCalledWith('task-3');
    });
  });

  it('clears completed downloads when clear button is clicked', async () => {
    render(<DownloadManager />);
    
    const clearButton = screen.getByRole('button', { name: /clear completed/i });
    fireEvent.click(clearButton);
    
    await waitFor(() => {
      expect(mockClearCompleted).toHaveBeenCalled();
    });
  });

  it('filters tasks by status', async () => {
    render(<DownloadManager />);
    
    const statusFilter = screen.getByRole('combobox', { name: /filter by status/i });
    fireEvent.click(statusFilter);
    
    await waitFor(() => {
      const downloadingOption = screen.getByText('Downloading');
      fireEvent.click(downloadingOption);
    });
    
    await waitFor(() => {
      expect(screen.getByText('TinyLlama 1.1B Chat Q4_K_M')).toBeInTheDocument();
      expect(screen.queryByText('Microsoft Phi-2 Q4_K_M')).not.toBeInTheDocument();
    });
  });

  it('sorts tasks by different criteria', async () => {
    render(<DownloadManager />);
    
    const sortSelect = screen.getByRole('combobox', { name: /sort by/i });
    fireEvent.click(sortSelect);
    
    await waitFor(() => {
      const progressOption = screen.getByText('Progress');
      fireEvent.click(progressOption);
    });
    
    // Tasks should be reordered by progress
    const taskElements = screen.getAllByTestId('download-task');
    expect(taskElements).toHaveLength(4);
  });

  it('shows empty state when no tasks', () => {
    mockUseDownloadStatus.mockReturnValue({
      tasks: [],
      cancelDownload: mockCancelDownload,
      pauseDownload: mockPauseDownload,
      resumeDownload: mockResumeDownload,
      retryDownload: mockRetryDownload,
      clearCompleted: mockClearCompleted,
      isLoading: false,
      error: null,
    });
    
    render(<DownloadManager />);
    
    expect(screen.getByText('No downloads')).toBeInTheDocument();
    expect(screen.getByText('No download tasks found')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    mockUseDownloadStatus.mockReturnValue({
      tasks: [],
      cancelDownload: mockCancelDownload,
      pauseDownload: mockPauseDownload,
      resumeDownload: mockResumeDownload,
      retryDownload: mockRetryDownload,
      clearCompleted: mockClearCompleted,
      isLoading: true,
      error: null,
    });
    
    render(<DownloadManager />);
    
    expect(screen.getByText('Loading downloads...')).toBeInTheDocument();
  });

  it('shows error state', () => {
    mockUseDownloadStatus.mockReturnValue({
      tasks: [],
      cancelDownload: mockCancelDownload,
      pauseDownload: mockPauseDownload,
      resumeDownload: mockResumeDownload,
      retryDownload: mockRetryDownload,
      clearCompleted: mockClearCompleted,
      isLoading: false,
      error: 'Failed to load downloads',
    });
    
    render(<DownloadManager />);
    
    expect(screen.getByText('Error loading downloads')).toBeInTheDocument();
    expect(screen.getByText('Failed to load downloads')).toBeInTheDocument();
  });

  it('shows compact view when enabled', () => {
    render(<DownloadManager compact={true} />);
    
    expect(screen.getByText('TinyLlama 1.1B Chat Q4_K_M')).toBeInTheDocument();
    
    // In compact mode, some details might be hidden
    const compactTask = screen.getByText('TinyLlama 1.1B Chat Q4_K_M').closest('[data-testid="download-task"]');
    expect(compactTask).toHaveClass('compact');
  });

  it('refreshes downloads when refresh button is clicked', async () => {
    const mockRefresh = vi.fn();
    mockUseDownloadStatus.mockReturnValue({
      tasks: mockDownloadTasks,
      cancelDownload: mockCancelDownload,
      pauseDownload: mockPauseDownload,
      resumeDownload: mockResumeDownload,
      retryDownload: mockRetryDownload,
      clearCompleted: mockClearCompleted,
      refresh: mockRefresh,
      isLoading: false,
      error: null,
    });
    
    render(<DownloadManager />);
    
    const refreshButton = screen.getByRole('button', { name: /refresh/i });
    fireEvent.click(refreshButton);
    
    await waitFor(() => {
      expect(mockRefresh).toHaveBeenCalled();
    });
  });

  it('displays total download progress', () => {
    render(<DownloadManager />);
    
    // Should show overall progress across all downloads
    expect(screen.getByText(/overall progress/i)).toBeInTheDocument();
    
    // Calculate expected overall progress: (45.5 + 100 + 25 + 60) / 4 = 57.625%
    expect(screen.getByText(/57.6%/)).toBeInTheDocument();
  });

  it('shows download speed for active downloads', () => {
    render(<DownloadManager />);
    
    const downloadingTask = screen.getByText('TinyLlama 1.1B Chat Q4_K_M').closest('[data-testid="download-task"]');
    expect(downloadingTask).toHaveTextContent('5.00 MB/s');
  });

  it('shows estimated time remaining for active downloads', () => {
    render(<DownloadManager />);
    
    const downloadingTask = screen.getByText('TinyLlama 1.1B Chat Q4_K_M').closest('[data-testid="download-task"]');
    expect(downloadingTask).toHaveTextContent('1m 9s');
  });

  it('handles task actions with confirmation for destructive actions', async () => {
    render(<DownloadManager />);
    
    // Cancel should show confirmation
    const cancelButton = screen.getByRole('button', { name: /cancel.*tinyllama/i });
    fireEvent.click(cancelButton);
    
    await waitFor(() => {
      expect(screen.getByText('Cancel Download')).toBeInTheDocument();
      expect(screen.getByText(/are you sure you want to cancel/i)).toBeInTheDocument();
    });
    
    const confirmButton = screen.getByRole('button', { name: /confirm/i });
    fireEvent.click(confirmButton);
    
    await waitFor(() => {
      expect(mockCancelDownload).toHaveBeenCalledWith('task-1');
    });
  });

  it('shows task details when expanded', async () => {
    render(<DownloadManager />);
    
    const expandButton = screen.getByRole('button', { name: /expand.*tinyllama/i });
    fireEvent.click(expandButton);
    
    await waitFor(() => {
      expect(screen.getByText('Download Details')).toBeInTheDocument();
      expect(screen.getByText('Start Time')).toBeInTheDocument();
      expect(screen.getByText('Downloaded')).toBeInTheDocument();
      expect(screen.getByText('Total Size')).toBeInTheDocument();
    });
  });

  it('groups tasks by status', async () => {
    render(<DownloadManager />);
    
    const groupButton = screen.getByRole('button', { name: /group by status/i });
    fireEvent.click(groupButton);
    
    await waitFor(() => {
      expect(screen.getByText('Active Downloads')).toBeInTheDocument();
      expect(screen.getByText('Completed Downloads')).toBeInTheDocument();
      expect(screen.getByText('Failed Downloads')).toBeInTheDocument();
      expect(screen.getByText('Paused Downloads')).toBeInTheDocument();
    });
  });

  it('handles keyboard navigation', async () => {
    render(<DownloadManager />);
    
    const firstTask = screen.getAllByTestId('download-task')[0];
    firstTask.focus();
    
    // Test keyboard navigation
    fireEvent.keyDown(firstTask, { key: 'ArrowDown' });
    
    const secondTask = screen.getAllByTestId('download-task')[1];
    expect(secondTask).toHaveFocus();
  });

  it('shows task context menu on right click', async () => {
    render(<DownloadManager />);
    
    const task = screen.getByText('TinyLlama 1.1B Chat Q4_K_M').closest('[data-testid="download-task"]');
    fireEvent.contextMenu(task!);
    
    await waitFor(() => {
      expect(screen.getByText('Cancel Download')).toBeInTheDocument();
      expect(screen.getByText('Pause Download')).toBeInTheDocument();
      expect(screen.getByText('View Details')).toBeInTheDocument();
    });
  });

  it('persists filter and sort preferences', async () => {
    render(<DownloadManager />);
    
    // Apply filter
    const statusFilter = screen.getByRole('combobox', { name: /filter by status/i });
    fireEvent.click(statusFilter);
    
    await waitFor(() => {
      const downloadingOption = screen.getByText('Downloading');
      fireEvent.click(downloadingOption);
    });
    
    // Preferences should be saved to localStorage
    expect(localStorage.setItem).toHaveBeenCalledWith(
      'downloadManager.preferences',
      expect.stringContaining('downloading')
    );
  });

  it('handles bulk actions', async () => {
    render(<DownloadManager />);
    
    // Select multiple tasks
    const checkboxes = screen.getAllByRole('checkbox');
    fireEvent.click(checkboxes[0]); // Select first task
    fireEvent.click(checkboxes[1]); // Select second task
    
    await waitFor(() => {
      expect(screen.getByText('2 selected')).toBeInTheDocument();
    });
    
    // Bulk cancel
    const bulkCancelButton = screen.getByRole('button', { name: /cancel selected/i });
    fireEvent.click(bulkCancelButton);
    
    await waitFor(() => {
      expect(mockCancelDownload).toHaveBeenCalledTimes(2);
    });
  });
});