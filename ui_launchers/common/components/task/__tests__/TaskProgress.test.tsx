import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { TaskProgress } from '../TaskProgress';
import { Task } from '../../../types/task';

// Mock Task type
const mockTask: Task = {
  id: 'test-task-id',
  sessionId: 'test-session-id',
  type: 'text_transform',
  title: 'Test Task',
  description: 'Test task description',
  parameters: {},
  executionMode: 'native',
  priority: 'medium',
  status: 'running',
  createdAt: new Date(),
  progress: {
    percentage: 50,
    currentStep: 'Processing data',
    totalSteps: 5,
    currentStepNumber: 3,
    estimatedTimeRemaining: 120
  }
};

describe('TaskProgress Component', () => {
  const mockOnTaskCancelled = jest.fn();
  const mockOnTaskCompleted = jest.fn();

  beforeEach(() => {
    mockOnTaskCancelled.mockClear();
    mockOnTaskCompleted.mockClear();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('renders without crashing', () => {
    render(
      <TaskProgress 
        task={mockTask}
        onTaskCancelled={mockOnTaskCancelled}
        onTaskCompleted={mockOnTaskCompleted}
      />
    );
    
    expect(screen.getByText('Task Progress')).toBeInTheDocument();
  });

  it('displays task information correctly', () => {
    render(
      <TaskProgress 
        task={mockTask}
        onTaskCancelled={mockOnTaskCancelled}
        onTaskCompleted={mockOnTaskCompleted}
      />
    );
    
    expect(screen.getByText('Test Task')).toBeInTheDocument();
    expect(screen.getByText('Test task description')).toBeInTheDocument();
    expect(screen.getByText('Type: text_transform')).toBeInTheDocument();
    expect(screen.getByText('Priority: medium')).toBeInTheDocument();
    expect(screen.getByText('Execution Mode: native')).toBeInTheDocument();
  });

  it('displays progress bar with correct percentage', () => {
    render(
      <TaskProgress 
        task={mockTask}
        onTaskCancelled={mockOnTaskCancelled}
        onTaskCompleted={mockOnTaskCompleted}
      />
    );
    
    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-valuenow', '50');
    expect(screen.getByText('50%')).toBeInTheDocument();
  });

  it('displays progress details correctly', () => {
    render(
      <TaskProgress 
        task={mockTask}
        onTaskCancelled={mockOnTaskCancelled}
        onTaskCompleted={mockOnTaskCompleted}
      />
    );
    
    expect(screen.getByText('Current Step:')).toBeInTheDocument();
    expect(screen.getByText('Processing data')).toBeInTheDocument();
    expect(screen.getByText('Progress:')).toBeInTheDocument();
    expect(screen.getByText('3 of 5 steps')).toBeInTheDocument();
    expect(screen.getByText('Estimated Time Remaining:')).toBeInTheDocument();
    expect(screen.getByText('2 minutes')).toBeInTheDocument();
  });

  it('displays task result when completed', () => {
    const completedTask = {
      ...mockTask,
      status: 'completed' as const,
      result: {
        summary: 'Task completed successfully',
        output: 'Sample output data',
        timestamp: new Date().toISOString()
      }
    };
    
    render(
      <TaskProgress 
        task={completedTask}
        onTaskCancelled={mockOnTaskCancelled}
        onTaskCompleted={mockOnTaskCompleted}
      />
    );
    
    expect(screen.getByText('Task Result')).toBeInTheDocument();
    expect(screen.getByText('Task completed successfully')).toBeInTheDocument();
    expect(screen.getByText('Sample output data')).toBeInTheDocument();
  });

  it('displays error message when task failed', () => {
    const failedTask = {
      ...mockTask,
      status: 'failed' as const,
      error: 'Task execution failed due to an error'
    };
    
    render(
      <TaskProgress 
        task={failedTask}
        onTaskCancelled={mockOnTaskCancelled}
        onTaskCompleted={mockOnTaskCompleted}
      />
    );
    
    expect(screen.getByText('Task Failed')).toBeInTheDocument();
    expect(screen.getByText('Task execution failed due to an error')).toBeInTheDocument();
  });

  it('calls onTaskCancelled when cancel button is clicked', async () => {
    render(
      <TaskProgress 
        task={mockTask}
        onTaskCancelled={mockOnTaskCancelled}
        onTaskCompleted={mockOnTaskCompleted}
      />
    );
    
    const cancelButton = screen.getByText('Cancel Task');
    fireEvent.click(cancelButton);
    
    await waitFor(() => {
      expect(mockOnTaskCancelled).toHaveBeenCalledWith(mockTask.id);
    });
  });

  it('shows cancelling state during cancellation', async () => {
    render(
      <TaskProgress 
        task={mockTask}
        onTaskCancelled={mockOnTaskCancelled}
        onTaskCompleted={mockOnTaskCompleted}
      />
    );
    
    const cancelButton = screen.getByText('Cancel Task');
    fireEvent.click(cancelButton);
    
    expect(screen.getByText('Cancelling...')).toBeInTheDocument();
    expect(cancelButton).toBeDisabled();
  });

  it('simulates progress updates for running tasks', async () => {
    render(
      <TaskProgress 
        task={mockTask}
        onTaskCancelled={mockOnTaskCancelled}
        onTaskCompleted={mockOnTaskCompleted}
      />
    );
    
    // Initial progress
    expect(screen.getByText('50%')).toBeInTheDocument();
    
    // Fast forward timers to simulate progress updates
    jest.advanceTimersByTime(2000);
    
    // Progress should have increased
    await waitFor(() => {
      const progressBar = screen.getByRole('progressbar');
      const newValue = parseInt(progressBar.getAttribute('aria-valuenow') || '0');
      expect(newValue).toBeGreaterThan(50);
    });
  });

  it('calls onTaskCompleted when progress reaches 100%', async () => {
    const completedTask = {
      ...mockTask,
      progress: {
        ...mockTask.progress!,
        percentage: 100
      }
    };
    
    render(
      <TaskProgress 
        task={completedTask}
        onTaskCancelled={mockOnTaskCancelled}
        onTaskCompleted={mockOnTaskCompleted}
      />
    );
    
    // Fast forward timers to trigger completion
    jest.advanceTimersByTime(1000);
    
    await waitFor(() => {
      expect(mockOnTaskCompleted).toHaveBeenCalledWith(
        completedTask.id,
        expect.objectContaining({
          summary: 'Task completed successfully'
        })
      );
    });
  });

  it('does not show cancel button for completed tasks', () => {
    const completedTask = {
      ...mockTask,
      status: 'completed' as const
    };
    
    render(
      <TaskProgress 
        task={completedTask}
        onTaskCancelled={mockOnTaskCancelled}
        onTaskCompleted={mockOnTaskCompleted}
      />
    );
    
    expect(screen.queryByText('Cancel Task')).not.toBeInTheDocument();
  });

  it('does not show cancel button for cancelled tasks', () => {
    const cancelledTask = {
      ...mockTask,
      status: 'cancelled' as const
    };
    
    render(
      <TaskProgress 
        task={cancelledTask}
        onTaskCancelled={mockOnTaskCancelled}
        onTaskCompleted={mockOnTaskCompleted}
      />
    );
    
    expect(screen.queryByText('Cancel Task')).not.toBeInTheDocument();
  });

  it('is accessible', () => {
    render(
      <TaskProgress 
        task={mockTask}
        onTaskCancelled={mockOnTaskCancelled}
        onTaskCompleted={mockOnTaskCompleted}
      />
    );
    
    // Check for proper ARIA attributes
    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-valuemin', '0');
    expect(progressBar).toHaveAttribute('aria-valuemax', '100');
    expect(progressBar).toHaveAttribute('aria-label', 'Task progress');
    
    // Check for status indicators
    expect(screen.getByText('Running')).toBeInTheDocument();
  });
});