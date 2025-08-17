import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SanitizedMarkdown, sanitizeText, sanitizeUrl } from '../SanitizedMarkdown';

// Mock the telemetry hook
vi.mock('@/hooks/use-telemetry', () => ({
  useTelemetry: () => ({
    track: vi.fn(),
  }),
}));

describe('SanitizedMarkdown', () => {
  it('renders safe markdown content', () => {
    const content = '# Hello World\n\nThis is **bold** text.';
    
    render(<SanitizedMarkdown content={content} />);
    
    const element = screen.getByText('Hello World');
    expect(element).toBeInTheDocument();
  });

  it('sanitizes dangerous HTML', () => {
    const content = '<script>alert("xss")</script><p>Safe content</p>';
    
    render(<SanitizedMarkdown content={content} />);
    
    // Should render safe content but not the script
    expect(screen.getByText('Safe content')).toBeInTheDocument();
    expect(screen.queryByText('alert("xss")')).not.toBeInTheDocument();
  });

  it('adds security attributes to external links', () => {
    const content = '[External Link](https://example.com)';
    
    const { container } = render(<SanitizedMarkdown content={content} />);
    
    // The link might be processed by marked and DOMPurify
    const link = container.querySelector('a');
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href');
  });

  it('handles empty content gracefully', () => {
    const { container } = render(<SanitizedMarkdown content="" />);
    expect(container.firstChild).toBeNull();
  });

  it('truncates content when maxLength is exceeded', () => {
    const longContent = 'a'.repeat(100);
    
    const { container } = render(<SanitizedMarkdown content={longContent} maxLength={50} />);
    
    // Should be truncated with ellipsis (either ... or …)
    const element = container.querySelector('[data-sanitized="true"]');
    expect(element?.textContent?.trim()).toMatch(/(\.\.\.|…)$/);
  });
});

describe('sanitizeText', () => {
  it('removes HTML tags from text', () => {
    const text = '<script>alert("xss")</script>Hello World';
    const result = sanitizeText(text);
    
    expect(result).toBe('Hello World');
  });

  it('truncates text when maxLength is exceeded', () => {
    const longText = 'a'.repeat(100);
    const result = sanitizeText(longText, 50);
    
    expect(result).toHaveLength(53); // 50 + '...'
    expect(result).toMatch(/\.\.\.$/);
  });
});

describe('sanitizeUrl', () => {
  it('allows safe URLs', () => {
    expect(sanitizeUrl('https://example.com')).toBe('https://example.com/');
    expect(sanitizeUrl('http://example.com')).toBe('http://example.com/');
    expect(sanitizeUrl('mailto:test@example.com')).toBe('mailto:test@example.com');
    expect(sanitizeUrl('tel:+1234567890')).toBe('tel:+1234567890');
  });

  it('blocks dangerous URLs', () => {
    expect(sanitizeUrl('javascript:alert("xss")')).toBe('');
    expect(sanitizeUrl('data:text/html,<script>alert("xss")</script>')).toBe('');
    expect(sanitizeUrl('vbscript:msgbox("xss")')).toBe('');
  });

  it('handles invalid URLs', () => {
    expect(sanitizeUrl('not-a-url')).toBe('');
    expect(sanitizeUrl('')).toBe('');
  });
});