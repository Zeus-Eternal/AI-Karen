import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { InteractiveInput } from '../interactive-input';
import { MicroInteractionProvider } from '../micro-interaction-provider';

import { vi } from 'vitest';

// Mock framer-motion
vi.mock('framer-motion', () => ({
  motion: {
    input: React.forwardRef<HTMLInputElement, any>(({ children, ...props }, ref) => (
      <input ref={ref} {...props} aria-label="Input">{children}</input>
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

describe('InteractiveInput', () => {
  beforeEach(() => {
    vi.clearAllMocks();

  it('renders correctly', () => {
    render(
      <TestWrapper>
        <InteractiveInput placeholder="Enter text" />
      </TestWrapper>
    );
    
    expect(screen.getByPlaceholderText('Enter text')).toBeInTheDocument();

  it('handles focus and blur events', async () => {
    const handleFocus = vi.fn();
    const handleBlur = vi.fn();
    const user = userEvent.setup();
    
    render(
      <TestWrapper>
        <InteractiveInput 
          placeholder="Enter text"
          onFocus={handleFocus}
          onBlur={handleBlur}
        />
      </TestWrapper>
    );
    
    const input = screen.getByPlaceholderText('Enter text');
    
    await user.click(input);
    expect(handleFocus).toHaveBeenCalledTimes(1);
    
    await user.tab();
    expect(handleBlur).toHaveBeenCalledTimes(1);

  it('applies error styling when error prop is true', () => {
    render(
      <TestWrapper>
        <InteractiveInput error placeholder="Enter text" />
      </TestWrapper>
    );
    
    const input = screen.getByPlaceholderText('Enter text');
    expect(input).toHaveClass('border-destructive');

  it('applies success styling when success prop is true', () => {
    render(
      <TestWrapper>
        <InteractiveInput success placeholder="Enter text" />
      </TestWrapper>
    );
    
    const input = screen.getByPlaceholderText('Enter text');
    expect(input).toHaveClass('border-green-500');

  it('applies custom className', () => {
    render(
      <TestWrapper>
        <InteractiveInput className="custom-class" placeholder="Enter text" />
      </TestWrapper>
    );
    
    expect(screen.getByPlaceholderText('Enter text')).toHaveClass('custom-class');

  it('forwards ref correctly', () => {
    const ref = React.createRef<HTMLInputElement>();
    
    render(
      <TestWrapper>
        <InteractiveInput ref={ref} placeholder="Enter text" />
      </TestWrapper>
    );
    
    expect(ref.current).toBeInstanceOf(HTMLInputElement);

  it('handles value changes', async () => {
    const user = userEvent.setup();
    
    render(
      <TestWrapper>
        <InteractiveInput placeholder="Enter text" />
      </TestWrapper>
    );
    
    const input = screen.getByPlaceholderText('Enter text');
    await user.type(input, 'Hello World');
    
    expect(input).toHaveValue('Hello World');

