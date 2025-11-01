/**
 * Enhanced Badge Component Tests
 * 
 * Tests for enhanced badge component with design token integration.
 * Based on requirements: 1.1, 1.2, 1.3, 11.4
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import { EnhancedBadge, EnhancedBadgeGroup } from '../badge';

describe('EnhancedBadge', () => {
  it('should render with default props', () => {
    render(<EnhancedBadge data-testid="badge">Default Badge</EnhancedBadge>);
    
    const badge = screen.getByTestId('badge');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('inline-flex', 'items-center');
    expect(screen.getByText('Default Badge')).toBeInTheDocument();
  });

  it('should apply variant classes correctly', () => {
    const { rerender } = render(<EnhancedBadge variant="destructive" data-testid="badge">Error</EnhancedBadge>);
    
    let badge = screen.getByTestId('badge');
    expect(badge).toHaveClass('bg-[var(--color-error-500)]');

    rerender(<EnhancedBadge variant="success" data-testid="badge">Success</EnhancedBadge>);
    badge = screen.getByTestId('badge');
    expect(badge).toHaveClass('bg-[var(--color-success-500)]');

    rerender(<EnhancedBadge variant="outline" data-testid="badge">Outline</EnhancedBadge>);
    badge = screen.getByTestId('badge');
    expect(badge).toHaveClass('border-[var(--color-neutral-300)]', 'bg-transparent');

    rerender(<EnhancedBadge variant="ghost" data-testid="badge">Ghost</EnhancedBadge>);
    badge = screen.getByTestId('badge');
    expect(badge).toHaveClass('border-transparent', 'bg-transparent');
  });

  it('should apply size classes correctly', () => {
    const { rerender } = render(<EnhancedBadge size="sm" data-testid="badge">Small</EnhancedBadge>);
    
    let badge = screen.getByTestId('badge');
    expect(badge).toHaveClass('px-[var(--space-xs)]', 'py-[var(--space-3xs)]');

    rerender(<EnhancedBadge size="lg" data-testid="badge">Large</EnhancedBadge>);
    badge = screen.getByTestId('badge');
    expect(badge).toHaveClass('px-[var(--space-md)]', 'py-[var(--space-xs)]');
  });

  it('should render with left and right icons', () => {
    const LeftIcon = () => <span data-testid="left-icon">←</span>;
    const RightIcon = () => <span data-testid="right-icon">→</span>;
    
    render(
      <EnhancedBadge 
        leftIcon={<LeftIcon />} 
        rightIcon={<RightIcon />}
      >
        Badge with icons
      </EnhancedBadge>
    );
    
    expect(screen.getByTestId('left-icon')).toBeInTheDocument();
    expect(screen.getByTestId('right-icon')).toBeInTheDocument();
  });

  it('should render with dot indicator', () => {
    render(<EnhancedBadge dot data-testid="badge">Badge with dot</EnhancedBadge>);
    
    const badge = screen.getByTestId('badge');
    const dot = badge.querySelector('span[aria-hidden="true"]');
    expect(dot).toBeInTheDocument();
    expect(dot).toHaveClass('h-2', 'w-2', 'rounded-full');
  });

  it('should render with custom dot color', () => {
    render(<EnhancedBadge dotColor="#ff0000" data-testid="badge">Badge with red dot</EnhancedBadge>);
    
    const badge = screen.getByTestId('badge');
    const dot = badge.querySelector('span[aria-hidden="true"]');
    expect(dot).toBeInTheDocument();
    expect(dot).toHaveStyle({ backgroundColor: '#ff0000' });
  });

  it('should handle interactive state', () => {
    const handleClick = vi.fn();
    render(
      <EnhancedBadge onClick={handleClick} interactive data-testid="badge">
        Interactive Badge
      </EnhancedBadge>
    );
    
    const badge = screen.getByTestId('badge');
    expect(badge).toHaveClass('cursor-pointer');
    expect(badge).toHaveAttribute('role', 'button');
    expect(badge).toHaveAttribute('tabIndex', '0');
    
    fireEvent.click(badge);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('should handle keyboard interaction', () => {
    const handleClick = vi.fn();
    render(
      <EnhancedBadge onClick={handleClick} data-testid="badge">
        Keyboard Badge
      </EnhancedBadge>
    );
    
    const badge = screen.getByTestId('badge');
    
    // Test Enter key
    fireEvent.keyDown(badge, { key: 'Enter' });
    expect(handleClick).toHaveBeenCalledTimes(1);
    
    // Test Space key
    fireEvent.keyDown(badge, { key: ' ' });
    expect(handleClick).toHaveBeenCalledTimes(2);
  });

  it('should render removable badge', () => {
    const handleRemove = vi.fn();
    render(
      <EnhancedBadge removable onRemove={handleRemove}>
        Removable Badge
      </EnhancedBadge>
    );
    
    const removeButton = screen.getByRole('button', { name: 'Remove' });
    expect(removeButton).toBeInTheDocument();
    
    fireEvent.click(removeButton);
    expect(handleRemove).toHaveBeenCalledTimes(1);
  });

  it('should prevent event propagation on remove', () => {
    const handleClick = vi.fn();
    const handleRemove = vi.fn();
    
    render(
      <EnhancedBadge onClick={handleClick} removable onRemove={handleRemove}>
        Removable Badge
      </EnhancedBadge>
    );
    
    const removeButton = screen.getByRole('button', { name: 'Remove' });
    fireEvent.click(removeButton);
    
    expect(handleRemove).toHaveBeenCalledTimes(1);
    expect(handleClick).not.toHaveBeenCalled();
  });

  it('should apply design token classes', () => {
    render(<EnhancedBadge data-testid="badge">Token Badge</EnhancedBadge>);
    
    const badge = screen.getByTestId('badge');
    expect(badge).toHaveClass('rounded-[var(--radius-full)]');
    expect(badge).toHaveClass('px-[var(--space-sm)]');
    expect(badge).toHaveClass('text-[var(--text-xs)]');
    expect(badge).toHaveClass('[transition-duration:var(--duration-fast)]');
    expect(badge).toHaveClass('bg-[var(--color-primary-500)]');
  });

  it('should truncate long text', () => {
    render(
      <EnhancedBadge data-testid="badge">
        This is a very long badge text that should be truncated
      </EnhancedBadge>
    );
    
    const badge = screen.getByTestId('badge');
    const textSpan = badge.querySelector('span.truncate');
    expect(textSpan).toBeInTheDocument();
  });
});

describe('EnhancedBadgeGroup', () => {
  it('should render with default props', () => {
    render(
      <EnhancedBadgeGroup>
        <EnhancedBadge>Badge 1</EnhancedBadge>
        <EnhancedBadge>Badge 2</EnhancedBadge>
      </EnhancedBadgeGroup>
    );
    
    expect(screen.getByText('Badge 1')).toBeInTheDocument();
    expect(screen.getByText('Badge 2')).toBeInTheDocument();
  });

  it('should apply spacing classes correctly', () => {
    const { rerender } = render(
      <EnhancedBadgeGroup spacing="sm" data-testid="badge-group">
        <EnhancedBadge>Badge 1</EnhancedBadge>
      </EnhancedBadgeGroup>
    );
    
    let group = screen.getByTestId('badge-group');
    expect(group).toHaveClass('gap-[var(--space-xs)]');

    rerender(
      <EnhancedBadgeGroup spacing="lg" data-testid="badge-group">
        <EnhancedBadge>Badge 1</EnhancedBadge>
      </EnhancedBadgeGroup>
    );
    
    group = screen.getByTestId('badge-group');
    expect(group).toHaveClass('gap-[var(--space-md)]');
  });

  it('should handle wrap property', () => {
    const { rerender } = render(
      <EnhancedBadgeGroup wrap={false} data-testid="badge-group">
        <EnhancedBadge>Badge 1</EnhancedBadge>
      </EnhancedBadgeGroup>
    );
    
    let group = screen.getByTestId('badge-group');
    expect(group).not.toHaveClass('flex-wrap');

    rerender(
      <EnhancedBadgeGroup wrap={true} data-testid="badge-group">
        <EnhancedBadge>Badge 1</EnhancedBadge>
      </EnhancedBadgeGroup>
    );
    
    group = screen.getByTestId('badge-group');
    expect(group).toHaveClass('flex-wrap');
  });

  it('should apply custom className', () => {
    render(
      <EnhancedBadgeGroup className="custom-class" data-testid="badge-group">
        <EnhancedBadge>Badge 1</EnhancedBadge>
      </EnhancedBadgeGroup>
    );
    
    const group = screen.getByTestId('badge-group');
    expect(group).toHaveClass('custom-class');
  });
});
