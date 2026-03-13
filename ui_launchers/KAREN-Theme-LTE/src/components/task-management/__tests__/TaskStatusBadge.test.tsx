/**
 * TaskStatusBadge Component Tests
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@/lib/__tests__/test-utils';
import { TaskStatusBadge, TaskPriorityBadge, TaskExecutionModeBadge } from '../ui/TaskStatusBadge';

describe('TaskStatusBadge', () => {
  it('renders correctly with default props', () => {
    render(<TaskStatusBadge status={'pending' as const} />);
    
    const badge = screen.getByRole('status');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveAttribute('aria-label', 'Task status: Pending');
    expect(screen.getByText('Pending')).toBeInTheDocument();
  });

  it('renders with different status values', () => {
    const { unmount } = render(<TaskStatusBadge status={'running' as const} />);
    let badge = screen.getByRole('status');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveAttribute('aria-label', 'Task status: Running');
    expect(screen.getByText('Running')).toBeInTheDocument();
    unmount();
    
    const { unmount: unmount2 } = render(<TaskStatusBadge status={'completed' as const} />);
    badge = screen.getByRole('status');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveAttribute('aria-label', 'Task status: Completed');
    expect(screen.getByText('Completed')).toBeInTheDocument();
    unmount2();
    
    const { unmount: unmount3 } = render(<TaskStatusBadge status={'failed' as const} />);
    badge = screen.getByRole('status');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveAttribute('aria-label', 'Task status: Failed');
    expect(screen.getByText('Failed')).toBeInTheDocument();
    unmount3();
    
    render(<TaskStatusBadge status={'cancelled' as const} />);
    badge = screen.getByRole('status');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveAttribute('aria-label', 'Task status: Cancelled');
    expect(screen.getByText('Cancelled')).toBeInTheDocument();
  });

  it('applies size variants correctly', () => {
    const { unmount } = render(<TaskStatusBadge status={'pending' as const} size={'sm'} />);
    let badge = screen.getByRole('status');
    expect(badge).toHaveClass('px-2', 'py-0.5', 'text-xs');
    unmount();
    
    const { unmount: unmount2 } = render(<TaskStatusBadge status={'pending' as const} size={'md'} />);
    badge = screen.getByRole('status');
    expect(badge).toHaveClass('px-2.5', 'py-0.5', 'text-xs');
    unmount2();
    
    render(<TaskStatusBadge status={'pending' as const} size={'lg'} />);
    badge = screen.getByRole('status');
    expect(badge).toHaveClass('px-3', 'py-1', 'text-sm');
  });

  it('shows icon when showIcon is true', () => {
    render(<TaskStatusBadge status={'pending' as const} showIcon={true} />);
    
    const badge = screen.getByRole('status');
    const icon = badge.querySelector('svg');
    expect(icon).toBeInTheDocument();
  });

  it('hides icon when showIcon is false', () => {
    render(<TaskStatusBadge status={'pending' as const} showIcon={false} />);
    
    const badge = screen.getByRole('status');
    const icon = badge.querySelector('svg');
    expect(icon).not.toBeInTheDocument();
  });

  it('shows label when showLabel is true', () => {
    render(<TaskStatusBadge status={'pending' as const} showLabel={true} />);
    
    expect(screen.getByText('Pending')).toBeInTheDocument();
  });

  it('hides label when showLabel is false', () => {
    render(<TaskStatusBadge status={'pending' as const} showLabel={false} />);
    
    expect(screen.queryByText('Pending')).not.toBeInTheDocument();
  });

  it('applies custom className', () => {
    render(<TaskStatusBadge status={'pending' as const} className="custom-class" />);
    
    const badge = screen.getByRole('status');
    expect(badge).toHaveClass('custom-class');
  });

  it('applies correct status colors', () => {
    const { unmount } = render(<TaskStatusBadge status={'pending' as const} />);
    let badge = screen.getByRole('status');
    expect(badge).toHaveClass('bg-yellow-100', 'text-yellow-800', 'border-yellow-200');
    unmount();
    
    const { unmount: unmount2 } = render(<TaskStatusBadge status={'running' as const} />);
    badge = screen.getByRole('status');
    expect(badge).toHaveClass('bg-blue-100', 'text-blue-800', 'border-blue-200', 'animate-pulse');
    unmount2();
    
    const { unmount: unmount3 } = render(<TaskStatusBadge status={'completed' as const} />);
    badge = screen.getByRole('status');
    expect(badge).toHaveClass('bg-green-100', 'text-green-800', 'border-green-200');
    unmount3();
    
    const { unmount: unmount4 } = render(<TaskStatusBadge status={'failed' as const} />);
    badge = screen.getByRole('status');
    expect(badge).toHaveClass('bg-red-100', 'text-red-800', 'border-red-200');
    unmount4();
    
    render(<TaskStatusBadge status={'cancelled' as const} />);
    badge = screen.getByRole('status');
    expect(badge).toHaveClass('bg-gray-100', 'text-gray-800', 'border-gray-200');
  });
});

describe('TaskPriorityBadge', () => {
  it('renders correctly with default props', () => {
    render(<TaskPriorityBadge priority={'medium' as const} />);
    
    const badge = screen.getByRole('status');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveAttribute('aria-label', 'Task priority: Medium');
    expect(screen.getByText('Medium')).toBeInTheDocument();
  });

  it('renders with different priority values', () => {
    const { unmount } = render(<TaskPriorityBadge priority={'low' as const} />);
    let badge = screen.getByRole('status');
    expect(badge).toHaveAttribute('aria-label', 'Task priority: Low');
    expect(screen.getByText('Low')).toBeInTheDocument();
    unmount();
    
    const { unmount: unmount2 } = render(<TaskPriorityBadge priority={'high' as const} />);
    badge = screen.getByRole('status');
    expect(badge).toHaveAttribute('aria-label', 'Task priority: High');
    expect(screen.getByText('High')).toBeInTheDocument();
    unmount2();
    
    render(<TaskPriorityBadge priority={'critical' as const} />);
    badge = screen.getByRole('status');
    expect(badge).toHaveAttribute('aria-label', 'Task priority: Critical');
    expect(screen.getByText('Critical')).toBeInTheDocument();
  });

  it('applies correct priority colors', () => {
    const { unmount } = render(<TaskPriorityBadge priority={'low' as const} />);
    let badge = screen.getByRole('status');
    expect(badge).toHaveClass('bg-gray-100', 'text-gray-800', 'border-gray-200');
    unmount();
    
    const { unmount: unmount2 } = render(<TaskPriorityBadge priority={'medium' as const} />);
    badge = screen.getByRole('status');
    expect(badge).toHaveClass('bg-blue-100', 'text-blue-800', 'border-blue-200');
    unmount2();
    
    const { unmount: unmount3 } = render(<TaskPriorityBadge priority={'high' as const} />);
    badge = screen.getByRole('status');
    expect(badge).toHaveClass('bg-orange-100', 'text-orange-800', 'border-orange-200');
    unmount3();
    
    render(<TaskPriorityBadge priority={'critical' as const} />);
    badge = screen.getByRole('status');
    expect(badge).toHaveClass('bg-red-100', 'text-red-800', 'border-red-200');
  });
});

describe('TaskExecutionModeBadge', () => {
  it('renders correctly with default props', () => {
    render(<TaskExecutionModeBadge executionMode={'native' as const} />);
    
    const badge = screen.getByRole('status');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveAttribute('aria-label', 'Task execution mode: Native');
    expect(screen.getByText('Native')).toBeInTheDocument();
  });

  it('renders with different execution modes', () => {
    const { unmount } = render(<TaskExecutionModeBadge executionMode={'native' as const} />);
    let badge = screen.getByRole('status');
    expect(badge).toHaveAttribute('aria-label', 'Task execution mode: Native');
    expect(screen.getByText('Native')).toBeInTheDocument();
    unmount();
    
    const { unmount: unmount2 } = render(<TaskExecutionModeBadge executionMode={'langgraph' as const} />);
    badge = screen.getByRole('status');
    expect(badge).toHaveAttribute('aria-label', 'Task execution mode: LangGraph');
    expect(screen.getByText('LangGraph')).toBeInTheDocument();
    unmount2();
    
    render(<TaskExecutionModeBadge executionMode={'deepagents' as const} />);
    badge = screen.getByRole('status');
    expect(badge).toHaveAttribute('aria-label', 'Task execution mode: DeepAgents');
    expect(screen.getByText('DeepAgents')).toBeInTheDocument();
  });

  it('applies correct execution mode colors', () => {
    const { unmount } = render(<TaskExecutionModeBadge executionMode={'native' as const} />);
    let badge = screen.getByRole('status');
    expect(badge).toHaveClass('bg-purple-100', 'text-purple-800', 'border-purple-200');
    unmount();
    
    const { unmount: unmount2 } = render(<TaskExecutionModeBadge executionMode={'langgraph' as const} />);
    badge = screen.getByRole('status');
    expect(badge).toHaveClass('bg-indigo-100', 'text-indigo-800', 'border-indigo-200');
    unmount2();
    
    render(<TaskExecutionModeBadge executionMode={'deepagents' as const} />);
    badge = screen.getByRole('status');
    expect(badge).toHaveClass('bg-teal-100', 'text-teal-800', 'border-teal-200');
  });
});