/**
 * Enhanced Button Component Tests
 * 
 * Tests for enhanced button component with design token integration.
 * Based on requirements: 1.1, 1.2, 1.3, 11.4
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import { EnhancedButton } from '../button';

describe('EnhancedButton', () => {
  it('should render with default props', () => {
    render(<EnhancedButton>Click me</EnhancedButton>);
    
    const button = screen.getByRole('button', { name: 'Click me' });
    expect(button).toBeInTheDocument();
    expect(button).toHaveClass('inline-flex', 'items-center', 'justify-center');
  });

  it('should apply variant classes correctly', () => {
    const { rerender } = render(<EnhancedButton variant="destructive">Delete</EnhancedButton>);
    
    let button = screen.getByRole('button');
    expect(button).toHaveClass('bg-[var(--color-error-500)]');

    rerender(<EnhancedButton variant="outline">Outline</EnhancedButton>);
    button = screen.getByRole('button');
    expect(button).toHaveClass('border', 'border-[var(--color-neutral-300)]');

    rerender(<EnhancedButton variant="ghost">Ghost</EnhancedButton>);
    button = screen.getByRole('button');
    expect(button).toHaveClass('bg-transparent');
  });

  it('should apply size classes correctly', () => {
    const { rerender } = render(<EnhancedButton size="sm">Small</EnhancedButton>);
    
    let button = screen.getByRole('button');
    expect(button).toHaveClass('h-8', 'px-[var(--space-sm)]');

    rerender(<EnhancedButton size="lg">Large</EnhancedButton>);
    button = screen.getByRole('button');
    expect(button).toHaveClass('h-12', 'px-[var(--space-lg)]');

    rerender(<EnhancedButton size="icon">Icon</EnhancedButton>);
    button = screen.getByRole('button');
    expect(button).toHaveClass('h-10', 'w-10', 'p-0');
  });

  it('should handle loading state', () => {
    render(<EnhancedButton loading>Loading</EnhancedButton>);
    
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute('aria-disabled', 'true');
    expect(button).toHaveClass('cursor-wait');
    
    // Should show loading spinner
    const spinner = button.querySelector('svg');
    expect(spinner).toBeInTheDocument();
    expect(spinner).toHaveClass('animate-spin');
  });

  it('should show loading text when provided', () => {
    render(
      <EnhancedButton loading loadingText="Saving...">
        Save
      </EnhancedButton>
    );
    
    expect(screen.getByText('Saving...')).toBeInTheDocument();
    expect(screen.queryByText('Save')).not.toBeInTheDocument();
  });

  it('should render left and right icons', () => {
    const LeftIcon = () => <span data-testid="left-icon">←</span>;
    const RightIcon = () => <span data-testid="right-icon">→</span>;
    
    render(
      <EnhancedButton 
        leftIcon={<LeftIcon />} 
        rightIcon={<RightIcon />}
      >
        Button with icons
      </EnhancedButton>
    );
    
    expect(screen.getByTestId('left-icon')).toBeInTheDocument();
    expect(screen.getByTestId('right-icon')).toBeInTheDocument();
  });

  it('should hide icons when loading', () => {
    const LeftIcon = () => <span data-testid="left-icon">←</span>;
    const RightIcon = () => <span data-testid="right-icon">→</span>;
    
    render(
      <EnhancedButton 
        loading
        leftIcon={<LeftIcon />} 
        rightIcon={<RightIcon />}
      >
        Loading button
      </EnhancedButton>
    );
    
    expect(screen.queryByTestId('left-icon')).not.toBeInTheDocument();
    expect(screen.queryByTestId('right-icon')).not.toBeInTheDocument();
  });

  it('should handle disabled state', () => {
    render(<EnhancedButton disabled>Disabled</EnhancedButton>);
    
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute('aria-disabled', 'true');
    expect(button).toHaveClass('disabled:opacity-60');
  });

  it('should handle click events', () => {
    const handleClick = vi.fn();
    render(<EnhancedButton onClick={handleClick}>Click me</EnhancedButton>);
    
    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('should not handle click events when disabled', () => {
    const handleClick = vi.fn();
    render(
      <EnhancedButton disabled onClick={handleClick}>
        Disabled
      </EnhancedButton>
    );
    
    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).not.toHaveBeenCalled();
  });

  it('should not handle click events when loading', () => {
    const handleClick = vi.fn();
    render(
      <EnhancedButton loading onClick={handleClick}>
        Loading
      </EnhancedButton>
    );
    
    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).not.toHaveBeenCalled();
  });

  it('should apply custom className', () => {
    render(<EnhancedButton className="custom-class">Custom</EnhancedButton>);
    
    const button = screen.getByRole('button');
    expect(button).toHaveClass('custom-class');
  });

  it('should forward ref correctly', () => {
    const ref = React.createRef<HTMLButtonElement>();
    render(<EnhancedButton ref={ref}>Ref button</EnhancedButton>);
    
    expect(ref.current).toBeInstanceOf(HTMLButtonElement);
  });

  it('should render as child component when asChild is true', () => {
    render(
      <EnhancedButton asChild>
        <a href="/test">Link button</a>
      </EnhancedButton>
    );
    
    const link = screen.getByRole('link');
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', '/test');
    expect(link).toHaveClass('inline-flex', 'items-center');
  });

  it('should have proper accessibility attributes', () => {
    render(<EnhancedButton>Accessible button</EnhancedButton>);
    
    const button = screen.getByRole('button');
    expect(button).toHaveClass('focus-visible:outline-none');
    expect(button).toHaveClass('focus-visible:ring-2');
    expect(button).toHaveClass('focus-visible:ring-[var(--focus-ring-color)]');
  });

  it('should apply design token classes', () => {
    render(<EnhancedButton>Token button</EnhancedButton>);
    
    const button = screen.getByRole('button');
    expect(button).toHaveClass('rounded-[var(--radius-md)]');
    expect(button).toHaveClass('[transition-duration:var(--duration-fast)]');
    expect(button).toHaveClass('[transition-timing-function:var(--ease-standard)]');
    expect(button).toHaveClass('bg-[var(--color-primary-500)]');
  });
});
