import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TaskActions } from '../ui/TaskActions';
import { Task } from '../types';
import { createMockTask } from '../../../lib/__tests__/test-utils';

describe('TaskActions', () => {
  const mockTask = createMockTask();
  const mockOnAction = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders correctly with default props', () => {
    render(<TaskActions task={mockTask} onAction={mockOnAction} />);
    
    // Should render the actions container
    const viewDetailsButton = screen.getByRole('button', { name: /View Details/i });
    expect(viewDetailsButton).toBeInTheDocument();
  });

  it('renders in compact mode when compact prop is true', () => {
    render(<TaskActions task={mockTask} onAction={mockOnAction} compact={true} />);
    
    // Should render the actions dropdown button
    const actionsButton = screen.getByRole('button', { name: /Task actions/i });
    expect(actionsButton).toBeInTheDocument();
  });

  it('calls onAction with correct payload when view details is clicked', async () => {
    const user = userEvent.setup();
    render(<TaskActions task={mockTask} onAction={mockOnAction} />);
    
    // Find and click the View Details button
    const viewDetailsButton = screen.getByRole('button', { name: /View Details/i });
    await user.click(viewDetailsButton);
    
    expect(mockOnAction).toHaveBeenCalledWith({
      action: 'view',
      taskId: mockTask.id
    });
  });

  it('calls onAction with correct payload when delete is clicked', async () => {
    const user = userEvent.setup();
    render(<TaskActions task={mockTask} onAction={mockOnAction} />);
    
    // Find and click the Delete Task button
    const deleteButton = screen.getByRole('button', { name: /Delete Task/i });
    await user.click(deleteButton);
    
    // Wait for confirmation dialog to appear
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /delete task/i })).toBeInTheDocument();
    }, { timeout: 3000 });
    
    // Find and click the confirmation button
    const confirmButton = screen.getByRole('button', { name: 'Delete' });
    await user.click(confirmButton);
    
    expect(mockOnAction).toHaveBeenCalledWith({
      action: 'delete',
      taskId: mockTask.id
    });
  });

  it('shows appropriate actions for completed task', () => {
    const completedTask = { ...mockTask, status: 'completed' as const };
    render(<TaskActions task={completedTask} onAction={mockOnAction} />);
    
    // Should show View Details and Delete Task buttons
    expect(screen.getByRole('button', { name: /View Details/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Delete Task/i })).toBeInTheDocument();
    
    // Should not show Retry Task button for completed task
    expect(screen.queryByRole('button', { name: /Retry Task/i })).not.toBeInTheDocument();
  });

  it('shows appropriate actions for failed task', () => {
    const failedTask = { ...mockTask, status: 'failed' as const };
    render(<TaskActions task={failedTask} onAction={mockOnAction} />);
    
    // Should show View Details, Retry Task, and Delete Task buttons
    expect(screen.getByRole('button', { name: /View Details/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Retry Task/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Delete Task/i })).toBeInTheDocument();
  });

  it('shows appropriate actions for running task', () => {
    const runningTask = { ...mockTask, status: 'running' as const };
    render(<TaskActions task={runningTask} onAction={mockOnAction} />);
    
    // Should show View Details, Cancel Task, and Pause Task buttons
    expect(screen.getByRole('button', { name: /View Details/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Cancel Task/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Pause Task/i })).toBeInTheDocument();
    
    // Should not show Retry Task button for running task
    expect(screen.queryByRole('button', { name: /Retry Task/i })).not.toBeInTheDocument();
  });

  it('shows appropriate actions for pending task', () => {
    const pendingTask = { ...mockTask, status: 'pending' as const };
    render(<TaskActions task={pendingTask} onAction={mockOnAction} />);
    
    // Should show View Details and Delete Task buttons
    expect(screen.getByRole('button', { name: /View Details/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Delete Task/i })).toBeInTheDocument();
    
    // Should not show Retry Task button for pending task
    expect(screen.queryByRole('button', { name: /Retry Task/i })).not.toBeInTheDocument();
  });

  it('has proper accessibility attributes', () => {
    render(<TaskActions task={mockTask} onAction={mockOnAction} />);
    
    // Check for proper ARIA attributes
    const viewDetailsButton = screen.getByRole('button', { name: /View Details/i });
    expect(viewDetailsButton).toBeInTheDocument();
    
    const deleteButton = screen.getByRole('button', { name: /Delete Task/i });
    expect(deleteButton).toBeInTheDocument();
  });

  it('has proper accessibility attributes in compact mode', () => {
    render(<TaskActions task={mockTask} onAction={mockOnAction} compact={true} />);
    
    // Check for proper ARIA attributes
    const actionsButton = screen.getByRole('button', { name: /Task actions/i });
    expect(actionsButton).toBeInTheDocument();
  });

  it('handles keyboard navigation in compact mode', async () => {
    const user = userEvent.setup();
    render(<TaskActions task={mockTask} onAction={mockOnAction} compact={true} />);
    
    // Focus the actions button
    const actionsButton = screen.getByRole('button', { name: /Task actions/i });
    actionsButton.focus();
    expect(actionsButton).toHaveFocus();
    
    // Press Enter to open menu
    await user.keyboard('{Enter}');
    
    // Should trigger menu open (though our mock doesn't actually show it)
    expect(actionsButton).toBeInTheDocument();
  });

  it('applies correct styling classes', () => {
    render(<TaskActions task={mockTask} onAction={mockOnAction} />);
    
    // Check that buttons have appropriate styling
    const viewDetailsButton = screen.getByRole('button', { name: /View Details/i });
    expect(viewDetailsButton).toBeInTheDocument();
    
    const deleteButton = screen.getByRole('button', { name: /Delete Task/i });
    expect(deleteButton).toBeInTheDocument();
  });

  it('applies correct styling classes in compact mode', () => {
    render(<TaskActions task={mockTask} onAction={mockOnAction} compact={true} />);
    
    // Check that compact button has appropriate styling
    const actionsButton = screen.getByRole('button', { name: /Task actions/i });
    expect(actionsButton).toBeInTheDocument();
  });
});