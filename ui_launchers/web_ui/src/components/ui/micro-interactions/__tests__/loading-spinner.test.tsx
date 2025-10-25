import React from 'react';
import { render, screen } from '@testing-library/react';
import { LoadingSpinner } from '../loading-spinner';
import { MicroInteractionProvider } from '../micro-interaction-provider';

import { vi } from 'vitest';

// Mock framer-motion
vi.mock('framer-motion', () => ({
  motion: {
    div: React.forwardRef<HTMLDivElement, any>(({ children, ...props }, ref) => (
      <div ref={ref} {...props}>{children}</div>
    ))
  }
}));

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <MicroInteractionProvider>
    {children}
  </MicroInteractionProvider>
);

describe('LoadingSpinner', () => {
  it('renders default spinner correctly', () => {
    render(
      <TestWrapper>
        <LoadingSpinner data-testid="spinner" />
      </TestWrapper>
    );
    
    expect(screen.getByTestId('spinner')).toBeInTheDocument();
  });

  it('renders dots variant correctly', () => {
    render(
      <TestWrapper>
        <LoadingSpinner variant="dots" data-testid="dots-spinner" />
      </TestWrapper>
    );
    
    const spinner = screen.getByTestId('dots-spinner');
    expect(spinner).toBeInTheDocument();
    // Should have 3 dots
    expect(spinner.children).toHaveLength(3);
  });

  it('renders pulse variant correctly', () => {
    render(
      <TestWrapper>
        <LoadingSpinner variant="pulse" data-testid="pulse-spinner" />
      </TestWrapper>
    );
    
    expect(screen.getByTestId('pulse-spinner')).toBeInTheDocument();
  });

  it('renders bars variant correctly', () => {
    render(
      <TestWrapper>
        <LoadingSpinner variant="bars" data-testid="bars-spinner" />
      </TestWrapper>
    );
    
    const spinner = screen.getByTestId('bars-spinner');
    expect(spinner).toBeInTheDocument();
    // Should have 4 bars
    expect(spinner.children).toHaveLength(4);
  });

  it('applies size classes correctly', () => {
    render(
      <TestWrapper>
        <LoadingSpinner size="lg" data-testid="large-spinner" />
      </TestWrapper>
    );
    
    expect(screen.getByTestId('large-spinner')).toHaveClass('w-8', 'h-8');
  });

  it('applies color classes correctly', () => {
    render(
      <TestWrapper>
        <LoadingSpinner color="secondary" data-testid="colored-spinner" />
      </TestWrapper>
    );
    
    expect(screen.getByTestId('colored-spinner')).toHaveClass('text-secondary');
  });

  it('applies custom className', () => {
    render(
      <TestWrapper>
        <LoadingSpinner className="custom-class" data-testid="custom-spinner" />
      </TestWrapper>
    );
    
    expect(screen.getByTestId('custom-spinner')).toHaveClass('custom-class');
  });
});