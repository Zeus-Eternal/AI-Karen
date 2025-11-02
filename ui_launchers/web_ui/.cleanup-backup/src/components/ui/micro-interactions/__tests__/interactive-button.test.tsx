import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { InteractiveButton } from '../interactive-button';
import { MicroInteractionProvider } from '../micro-interaction-provider';

import { vi } from 'vitest';

// Mock framer-motion
vi.mock('framer-motion', () => ({
  motion: {
    button: React.forwardRef<HTMLButtonElement, any>(({ children, ...props }, ref) => (
      <button ref={ref} {...props}>{children}</button>
    ))
  }
}));

// Mock haptic feedback
vi.mock('../haptic-feedback', () => ({
  triggerHapticFeedback: vi.fn(),
  isHapticSupported: () => true,
  isHapticEnabled: () => true,
  setHapticEnabled: vi.fn()
}));

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <MicroInteractionProvider>
    {children}
  </MicroInteractionProvider>
);

describe('InteractiveButton', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders correctly', () => {
    render(
      <TestWrapper>
        <InteractiveButton>Click me</InteractiveButton>
      </TestWrapper>
    );
    
    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument();
  });

  it('shows loading state correctly', () => {
    render(
      <TestWrapper>
        <InteractiveButton loading loadingText="Loading...">
          Click me
        </InteractiveButton>
      </TestWrapper>
    );
    
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('handles click events', async () => {
    const handleClick = vi.fn();
    const user = userEvent.setup();
    
    render(
      <TestWrapper>
        <InteractiveButton onClick={handleClick}>
          Click me
        </InteractiveButton>
      </TestWrapper>
    );
    
    await user.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('does not trigger click when loading', async () => {
    const handleClick = vi.fn();
    const user = userEvent.setup();
    
    render(
      <TestWrapper>
        <InteractiveButton loading onClick={handleClick}>
          Click me
        </InteractiveButton>
      </TestWrapper>
    );
    
    await user.click(screen.getByRole('button'));
    expect(handleClick).not.toHaveBeenCalled();
  });

  it('does not trigger click when disabled', async () => {
    const handleClick = vi.fn();
    const user = userEvent.setup();
    
    render(
      <TestWrapper>
        <InteractiveButton disabled onClick={handleClick}>
          Click me
        </InteractiveButton>
      </TestWrapper>
    );
    
    await user.click(screen.getByRole('button'));
    expect(handleClick).not.toHaveBeenCalled();
  });

  it('applies custom className', () => {
    render(
      <TestWrapper>
        <InteractiveButton className="custom-class">
          Click me
        </InteractiveButton>
      </TestWrapper>
    );
    
    expect(screen.getByRole('button')).toHaveClass('custom-class');
  });

  it('forwards ref correctly', () => {
    const ref = React.createRef<HTMLButtonElement>();
    
    render(
      <TestWrapper>
        <InteractiveButton ref={ref}>
          Click me
        </InteractiveButton>
      </TestWrapper>
    );
    
    expect(ref.current).toBeInstanceOf(HTMLButtonElement);
  });
});