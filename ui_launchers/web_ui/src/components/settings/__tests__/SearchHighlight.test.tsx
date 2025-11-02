
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import SearchHighlight from '../SearchHighlight';

describe('SearchHighlight', () => {
  it('renders text without highlighting when no search query', () => {
    render(<SearchHighlight text="Hello World" searchQuery="" />);
    expect(screen.getByText('Hello World')).toBeInTheDocument();
    expect(screen.queryByRole('mark')).not.toBeInTheDocument();
  });

  it('highlights matching text case-insensitively', () => {
    render(<SearchHighlight text="Hello World" searchQuery="hello" />);
    const highlighted = screen.getByText('Hello');
    expect(highlighted.tagName).toBe('MARK');
    expect(highlighted).toHaveClass('bg-yellow-200');
  });

  it('highlights multiple matches', () => {
    render(<SearchHighlight text="Hello Hello World" searchQuery="hello" />);
    const highlights = screen.getAllByText('Hello');
    expect(highlights).toHaveLength(2);
    highlights.forEach(highlight => {
      expect(highlight.tagName).toBe('MARK');
    });
  });

  it('handles special regex characters', () => {
    render(<SearchHighlight text="Price: $10.99" searchQuery="$10.99" />);
    const highlighted = screen.getByText('$10.99');
    expect(highlighted.tagName).toBe('MARK');
  });

  it('renders with custom className', () => {
    render(<SearchHighlight text="Hello World" searchQuery="" className="custom-class" />);
    const element = screen.getByText('Hello World');
    expect(element).toHaveClass('custom-class');
  });
});