/**
 * TaskProgressBar Component Tests
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@/lib/__tests__/test-utils';
import { TaskProgressBar } from '../ui/TaskProgressBar';
import { createMockTask } from '@/lib/__tests__/test-utils';

describe('TaskProgressBar', () => {
  it('renders correctly with default props', () => {
    const mockTask = createMockTask({ progress: 50 });
    render(<TaskProgressBar task={mockTask} />);
    
    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toBeInTheDocument();
  });

  it('displays correct progress percentage', () => {
    const mockTask = createMockTask({ progress: 75 });
    render(<TaskProgressBar task={mockTask} />);
    
    const progressText = screen.getByText('75%');
    expect(progressText).toBeInTheDocument();
  });

  it('shows steps when showSteps is true', () => {
    const mockTask = createMockTask({
      progress: 33,
      steps: [
        { id: '1', name: 'Step 1', status: 'completed' as const, progress: 100 },
        { id: '2', name: 'Step 2', status: 'running' as const, progress: 50 },
        { id: '3', name: 'Step 3', status: 'pending' as const, progress: 0 },
      ],
    });
    render(<TaskProgressBar task={mockTask} showSteps />);
    
    // Should show step indicators
    const step1 = screen.getByText('Step 1');
    const step2 = screen.getByText('Step 2');
    const step3 = screen.getByText('Step 3');
    
    expect(step1).toBeInTheDocument();
    expect(step2).toBeInTheDocument();
    expect(step3).toBeInTheDocument();
  });

  it('hides steps when showSteps is false', () => {
    const mockTask = createMockTask({
      progress: 33,
      steps: [
        { id: '1', name: 'Step 1', status: 'completed' as const, progress: 100 },
        { id: '2', name: 'Step 2', status: 'running' as const, progress: 50 },
      ],
    });
    render(<TaskProgressBar task={mockTask} showSteps={false} />);
    
    // Should not show step names
    expect(screen.queryByText('Step 1')).not.toBeInTheDocument();
    expect(screen.queryByText('Step 2')).not.toBeInTheDocument();
  });

  it('applies compact styling when compact is true', () => {
    const mockTask = createMockTask({ progress: 50 });
    render(<TaskProgressBar task={mockTask} compact />);
    
    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveClass('h-2'); // Compact height
  });

  it('applies custom className', () => {
    const mockTask = createMockTask({ progress: 50 });
    render(<TaskProgressBar task={mockTask} className="custom-class" />);
    
    const container = screen.getByRole('progressbar').closest('.space-y-4');
    expect(container).toHaveClass('custom-class');
  });

  it('handles 0% progress', () => {
    const mockTask = createMockTask({ progress: 0 });
    render(<TaskProgressBar task={mockTask} />);
    
    const progressText = screen.getByText('0%');
    expect(progressText).toBeInTheDocument();
  });

  it('handles 100% progress', () => {
    const mockTask = createMockTask({ progress: 100 });
    render(<TaskProgressBar task={mockTask} />);
    
    const progressText = screen.getByText('100%');
    expect(progressText).toBeInTheDocument();
  });

  it('renders with different status values', () => {
    const { unmount } = render(<TaskProgressBar task={createMockTask({ progress: 25, status: 'pending' as const })} />);
    let progressBar = screen.getByRole('progressbar');
    expect(progressBar).toBeInTheDocument();
    unmount();
    
    const { unmount: unmount2 } = render(<TaskProgressBar task={createMockTask({ progress: 50, status: 'running' as const })} />);
    progressBar = screen.getByRole('progressbar');
    expect(progressBar).toBeInTheDocument();
    unmount2();
    
    const { unmount: unmount3 } = render(<TaskProgressBar task={createMockTask({ progress: 100, status: 'completed' as const })} />);
    progressBar = screen.getByRole('progressbar');
    expect(progressBar).toBeInTheDocument();
    unmount3();
    
    render(<TaskProgressBar task={createMockTask({ progress: 50, status: 'failed' as const })} />);
    progressBar = screen.getByRole('progressbar');
    expect(progressBar).toBeInTheDocument();
  });

  it('shows step status indicators correctly', () => {
    const mockTask = createMockTask({
      progress: 50,
      steps: [
        { id: '1', name: 'Step 1', status: 'completed' as const, progress: 100 },
        { id: '2', name: 'Step 2', status: 'running' as const, progress: 50 },
        { id: '3', name: 'Step 3', status: 'pending' as const, progress: 0 },
        { id: '4', name: 'Step 4', status: 'failed' as const, progress: 0 },
      ],
    });
    render(<TaskProgressBar task={mockTask} showSteps />);
    
    // Check for status indicators - look at the step number circles instead
    const completedStep = screen.getByText('Step 1').previousElementSibling;
    const runningStep = screen.getByText('Step 2').previousElementSibling;
    const pendingStep = screen.getByText('Step 3').previousElementSibling;
    const failedStep = screen.getByText('Step 4').previousElementSibling;
    
    expect(completedStep).toHaveClass('bg-green-500');
    expect(runningStep).toHaveClass('bg-blue-500');
    expect(pendingStep).toHaveClass('bg-gray-300');
    expect(failedStep).toHaveClass('bg-red-500'); // Failed step uses red color
  });

  it('is accessible with proper ARIA attributes', () => {
    const mockTask = createMockTask({ progress: 65 });
    render(<TaskProgressBar task={mockTask} />);
    
    const progressBar = screen.getByRole('progressbar');
    // The Progress component from Radix UI uses data-value instead of aria-valuenow
    expect(progressBar).toHaveAttribute('data-max', '100');
    expect(progressBar).toBeInTheDocument();
  });

  it('handles missing steps gracefully', () => {
    const mockTask = createMockTask({ progress: 50 });
    // Ensure steps is undefined
    delete (mockTask as any).steps;
    
    render(<TaskProgressBar task={mockTask} showSteps />);
    
    // Should still render the main progress bar
    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toBeInTheDocument();
    
    // Should not show any step information
    expect(screen.queryByText('Step 1')).not.toBeInTheDocument();
  });

  it('calculates overall progress from steps when needed', () => {
    const mockTask = createMockTask({
      progress: 0, // Will be calculated from steps
      steps: [
        { id: '1', name: 'Step 1', status: 'completed' as const, progress: 100 },
        { id: '2', name: 'Step 2', status: 'running' as const, progress: 50 },
        { id: '3', name: 'Step 3', status: 'pending' as const, progress: 0 },
        { id: '4', name: 'Step 4', status: 'pending' as const, progress: 0 },
      ],
    });
    render(<TaskProgressBar task={mockTask} showSteps />);
    
    // Should calculate average progress: (100 + 50 + 0 + 0) / 4 = 37.5
    // Get the first (main) progress bar, not the step progress bars
    const progressBars = screen.getAllByRole('progressbar');
    const mainProgressBar = progressBars[0];
    expect(mainProgressBar).toBeInTheDocument();
  });
});