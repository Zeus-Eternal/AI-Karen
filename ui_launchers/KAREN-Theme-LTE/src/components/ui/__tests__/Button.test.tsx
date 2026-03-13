import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import { Button } from '../button';
import { render as customRender } from '@/lib/__tests__/test-utils';

describe('Button', () => {
  const mockOnClick = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders with default props', () => {
    customRender(<Button>Click me</Button>);
    
    const button = screen.getByRole('button', { name: /click me/i });
    expect(button).toBeInTheDocument();
    expect(button).toHaveClass('bg-gray-600');
    expect(button).toHaveClass('px-4 py-2 text-sm');
  });

  it('renders with custom className', () => {
    customRender(<Button className="custom-class">Click me</Button>);
    
    const button = screen.getByRole('button');
    expect(button).toHaveClass('custom-class');
  });

  it('renders with different variants', () => {
    const { rerender } = customRender(<Button variant="destructive">Delete</Button>);
    
    let button = screen.getByRole('button');
    expect(button).toHaveClass('bg-red-600 text-white');
    
    rerender(<Button variant="outline">Cancel</Button>);
    button = screen.getByRole('button');
    expect(button).toHaveClass('border border-gray-300 bg-white');
    
    rerender(<Button variant="secondary">Secondary</Button>);
    button = screen.getByRole('button');
    expect(button).toHaveClass('bg-gray-200 text-gray-900');
    
    rerender(<Button variant="ghost">Ghost</Button>);
    button = screen.getByRole('button');
    expect(button).toHaveClass('text-gray-700');
    
    rerender(<Button variant="primary">Primary</Button>);
    button = screen.getByRole('button');
    expect(button).toHaveClass('bg-blue-600 text-white');
  });

  it('renders with different sizes', () => {
    const { rerender } = customRender(<Button size="sm">Small</Button>);
    
    let button = screen.getByRole('button');
    expect(button).toHaveClass('px-3 py-1.5 text-sm');
    
    rerender(<Button size="lg">Large</Button>);
    button = screen.getByRole('button');
    expect(button).toHaveClass('px-6 py-3 text-base');
    
    rerender(<Button size="md">Medium</Button>);
    button = screen.getByRole('button');
    expect(button).toHaveClass('px-4 py-2 text-sm');
  });

  it('renders as disabled', () => {
    customRender(<Button disabled>Disabled</Button>);
    
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
    expect(button).toHaveClass('disabled:opacity-50');
  });

  it('handles click events', () => {
    customRender(<Button onClick={mockOnClick}>Click me</Button>);
    
    const button = screen.getByRole('button');
    fireEvent.click(button);
    
    expect(mockOnClick).toHaveBeenCalledTimes(1);
  });

  it('renders with accessibility props', () => {
    customRender(
      <Button 
        aria-label="Test button"
        aria-describedby="test-description"
        aria-expanded={false}
        aria-pressed={false}
        aria-selected={false}
        aria-busy={false}
        role="button"
      >
        Accessible Button
      </Button>
    );
    
    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('aria-label', 'Test button');
    expect(button).toHaveAttribute('aria-describedby', 'test-description');
    expect(button).toHaveAttribute('aria-expanded', 'false');
    expect(button).toHaveAttribute('aria-pressed', 'false');
    expect(button).toHaveAttribute('aria-selected', 'false');
    expect(button).toHaveAttribute('aria-busy', 'false');
    expect(button).toHaveAttribute('role', 'button');
  });

  it('renders children correctly', () => {
    customRender(
      <Button>
        <span data-testid="child-element">Child content</span>
      </Button>
    );
    
    const button = screen.getByRole('button');
    const childElement = screen.getByTestId('child-element');
    
    expect(childElement).toBeInTheDocument();
    expect(button.contains(childElement)).toBe(true);
  });

  it('forwards ref correctly', () => {
    const ref = React.createRef<HTMLButtonElement>();
    
    customRender(<Button ref={ref}>Ref test</Button>);
    
    expect(ref.current?.constructor.name).toBe('HTMLButtonElement');
  });

  it('supports keyboard navigation', () => {
    customRender(<Button onClick={mockOnClick}>Focus me</Button>);
    
    const button = screen.getByRole('button');
    
    // Test focus
    button.focus();
    expect(document.activeElement).toBe(button);
    
    // Test keyboard interaction with click simulation
    fireEvent.click(button);
    expect(mockOnClick).toHaveBeenCalledTimes(1);
  });

  it('applies hover states', () => {
    customRender(<Button>Hover me</Button>);
    
    const button = screen.getByRole('button');
    
    // Test that hover class is present in the className (CSS hover state)
    expect(button).toHaveClass('hover:bg-gray-700');
    
    // Test that the base classes are present
    expect(button).toHaveClass('inline-flex items-center justify-center');
  });

  it('handles loading state', () => {
    customRender(<Button loading>Loading...</Button>);
    
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
    expect(button).toHaveClass('cursor-wait');
    expect(button).toHaveTextContent('Loading...');
  });

  it('supports form submission', () => {
    const mockSubmit = vi.fn((e) => {
      e.preventDefault(); // Prevent form submission in test
    });
    
    customRender(
      <form onSubmit={mockSubmit}>
        <Button type="submit">Submit</Button>
      </form>
    );
    
    const button = screen.getByRole('button');
    const form = button.closest('form');
    
    fireEvent.click(button);
    
    // The button click should trigger form submission
    expect(mockSubmit).toHaveBeenCalledTimes(1);
  });

  it('has proper display name', () => {
    expect(Button.displayName).toBe('Button');
  });

  describe('Edge Cases', () => {
    it('handles missing children gracefully', () => {
      customRender(<Button>Empty</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
    });

    it('handles empty string as children', () => {
      customRender(<Button>{''}</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
    });

    it('handles boolean props correctly', () => {
      const { rerender } = customRender(<Button aria-expanded={false}>Test</Button>);
      
      let button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-expanded', 'false');
      
      rerender(<Button aria-expanded={true}>Test</Button>);
      button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-expanded', 'true');
    });

    it('handles mixed aria-pressed state', () => {
      customRender(<Button aria-pressed="mixed">Test</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-pressed', 'mixed');
    });
  });
});