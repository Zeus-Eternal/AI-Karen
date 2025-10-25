import React from 'react';
import { render, screen } from '@testing-library/react';
import { ProgressAnimation } from '../progress-animation';
import { MicroInteractionProvider } from '../micro-interaction-provider';

import { vi } from 'vitest';

// Mock framer-motion
vi.mock('framer-motion', () => ({
  motion: {
    div: React.forwardRef<HTMLDivElement, any>(({ children, ...props }, ref) => (
      <div ref={ref} {...props}>{children}</div>
    )),
    circle: React.forwardRef<SVGCircleElement, any>(({ children, ...props }, ref) => (
      <circle ref={ref} {...props}>{children}</circle>
    ))
  }
}));

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <MicroInteractionProvider>
    {children}
  </MicroInteractionProvider>
);

describe('ProgressAnimation', () => {
  it('renders linear progress correctly', () => {
    render(
      <TestWrapper>
        <ProgressAnimation progress={50} data-testid="progress" />
      </TestWrapper>
    );
    
    expect(screen.getByTestId('progress')).toBeInTheDocument();
  });

  it('renders circular progress correctly', () => {
    render(
      <TestWrapper>
        <ProgressAnimation 
          progress={75} 
          variant="circular" 
          data-testid="circular-progress" 
        />
      </TestWrapper>
    );
    
    const progress = screen.getByTestId('circular-progress');
    expect(progress).toBeInTheDocument();
    expect(progress.querySelector('svg')).toBeInTheDocument();
  });

  it('renders dots progress correctly', () => {
    render(
      <TestWrapper>
        <ProgressAnimation 
          progress={30} 
          variant="dots" 
          data-testid="dots-progress" 
        />
      </TestWrapper>
    );
    
    const progress = screen.getByTestId('dots-progress');
    expect(progress).toBeInTheDocument();
    // Should have 10 dots
    expect(progress.children).toHaveLength(10);
  });

  it('shows percentage when enabled', () => {
    render(
      <TestWrapper>
        <ProgressAnimation 
          progress={65} 
          showPercentage 
          data-testid="progress-with-percentage" 
        />
      </TestWrapper>
    );
    
    expect(screen.getByText('65%')).toBeInTheDocument();
  });

  it('shows percentage for circular variant', () => {
    render(
      <TestWrapper>
        <ProgressAnimation 
          progress={80} 
          variant="circular"
          showPercentage 
          data-testid="circular-progress-with-percentage" 
        />
      </TestWrapper>
    );
    
    expect(screen.getByText('80%')).toBeInTheDocument();
  });

  it('clamps progress values correctly', () => {
    render(
      <TestWrapper>
        <ProgressAnimation 
          progress={150} 
          showPercentage 
          data-testid="clamped-progress" 
        />
      </TestWrapper>
    );
    
    // Should clamp to 100%
    expect(screen.getByText('100%')).toBeInTheDocument();
  });

  it('handles negative progress values', () => {
    render(
      <TestWrapper>
        <ProgressAnimation 
          progress={-20} 
          showPercentage 
          data-testid="negative-progress" 
        />
      </TestWrapper>
    );
    
    // Should clamp to 0%
    expect(screen.getByText('0%')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    render(
      <TestWrapper>
        <ProgressAnimation 
          progress={50} 
          className="custom-class" 
          data-testid="custom-progress" 
        />
      </TestWrapper>
    );
    
    expect(screen.getByTestId('custom-progress')).toHaveClass('custom-class');
  });

  it('applies size classes correctly', () => {
    render(
      <TestWrapper>
        <ProgressAnimation 
          progress={50} 
          size="lg" 
          data-testid="large-progress" 
        />
      </TestWrapper>
    );
    
    const progressBar = screen.getByTestId('large-progress').querySelector('.bg-muted');
    expect(progressBar).toHaveClass('h-4');
  });
});