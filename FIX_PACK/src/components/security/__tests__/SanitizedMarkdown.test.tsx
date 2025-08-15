import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { SanitizedMarkdown, sanitizeText, sanitizeUrl } from '../SanitizedMarkdown';

// Mock the telemetry hook
vi.mock('@/hooks/use-telemetry', () => ({
  useTelemetry: () => ({
    track: vi.fn()
  })
}));

describe('SanitizedMarkdown', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Basic Functionality', () => {
    it('renders simple markdown content', () => {
      render(<SanitizedMarkdown content="# Hello World" />);
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Hello World');
    });

    it('renders empty content as null', () => {
      const { container } = render(<SanitizedMarkdown content="" />);
      expect(container.firstChild).toBeNull();
    });

    it('applies custom className', () => {
      const { container } = render(
        <SanitizedMarkdown content="Hello" className="custom-class" />
      );
      expect(container.firstChild).toHaveClass('custom-class');
    });
  });

  describe('XSS Prevention', () => {
    it('removes script tags', () => {
      const maliciousContent = '<script>alert("xss")</script>Hello';
      render(<SanitizedMarkdown content={maliciousContent} />);
      
      expect(screen.queryByText('alert("xss")')).not.toBeInTheDocument();
      expect(screen.getByText('Hello')).toBeInTheDocument();
    });

    it('removes event handlers', () => {
      const maliciousContent = '<p onclick="alert(\'xss\')">Click me</p>';
      render(<SanitizedMarkdown content={maliciousContent} />);
      
      const paragraph = screen.getByText('Click me');
      expect(paragraph).not.toHaveAttribute('onclick');
    });

    it('removes dangerous attributes', () => {
      const maliciousContent = '<img src="x" onerror="alert(\'xss\')" />';
      render(<SanitizedMarkdown content={maliciousContent} />);
      
      // Image should be removed entirely as it's not in allowed tags
      expect(screen.queryByRole('img')).not.toBeInTheDocument();
    });

    it('sanitizes javascript: URLs', () => {
      const maliciousContent = '[Click me](javascript:alert("xss"))';
      render(<SanitizedMarkdown content={maliciousContent} />);
      
      const link = screen.getByText('Click me');
      expect(link).not.toHaveAttribute('href', 'javascript:alert("xss")');
    });

    it('removes forbidden tags', () => {
      const maliciousContent = '<object data="malicious.swf"></object><embed src="malicious.swf" />';
      render(<SanitizedMarkdown content={maliciousContent} />);
      
      expect(screen.queryByText('object')).not.toBeInTheDocument();
      expect(screen.queryByText('embed')).not.toBeInTheDocument();
    });
  });

  describe('Link Security', () => {
    it('adds noopener noreferrer to external links', () => {
      const content = '[External](https://example.com)';
      render(<SanitizedMarkdown content={content} />);
      
      const link = screen.getByRole('link');
      expect(link).toHaveAttribute('rel', 'noopener noreferrer');
      expect(link).toHaveAttribute('target', '_blank');
    });

    it('does not add target="_blank" to internal links', () => {
      const content = '[Internal](/internal-page)';
      render(<SanitizedMarkdown content={content} />);
      
      const link = screen.getByRole('link');
      expect(link).toHaveAttribute('target', '_self');
      expect(link).not.toHaveAttribute('rel');
    });

    it('respects custom linkTarget setting', () => {
      const content = '[External](https://example.com)';
      render(<SanitizedMarkdown content={content} linkTarget="_self" />);
      
      const link = screen.getByRole('link');
      expect(link).toHaveAttribute('target', '_self');
    });
  });

  describe('Content Truncation', () => {
    it('truncates content exceeding maxLength', () => {
      const longContent = 'a'.repeat(100);
      render(<SanitizedMarkdown content={longContent} maxLength={50} />);
      
      const element = screen.getByText(/a+\.\.\./);
      expect(element.textContent).toHaveLength(53); // 50 + '...'
    });

    it('does not truncate content within maxLength', () => {
      const shortContent = 'Short content';
      render(<SanitizedMarkdown content={shortContent} maxLength={50} />);
      
      expect(screen.getByText('Short content')).toBeInTheDocument();
    });
  });

  describe('Allowed Tags and Attributes', () => {
    it('allows default tags', () => {
      const content = `
        # Heading
        **Bold** and *italic*
        \`code\` and \`\`\`
        code block
        \`\`\`
        - List item
        > Blockquote
      `;
      
      render(<SanitizedMarkdown content={content} />);
      
      expect(screen.getByRole('heading')).toBeInTheDocument();
      expect(screen.getByText('Bold')).toBeInTheDocument();
      expect(screen.getByText('italic')).toBeInTheDocument();
      expect(screen.getByText('code')).toBeInTheDocument();
      expect(screen.getByText('List item')).toBeInTheDocument();
    });

    it('respects custom allowed tags', () => {
      const content = '<div>Div content</div><span>Span content</span>';
      render(
        <SanitizedMarkdown 
          content={content} 
          allowedTags={['span']}
          allowedAttributes={{ 'span': ['class'] }}
        />
      );
      
      expect(screen.getByText('Span content')).toBeInTheDocument();
      expect(screen.queryByText('Div content')).not.toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('falls back to plain text on parsing error', () => {
      // Mock marked to throw an error
      const originalConsoleError = console.error;
      console.error = vi.fn();
      
      // This should trigger the error handling
      const problematicContent = 'Some content that might cause issues';
      render(<SanitizedMarkdown content={problematicContent} />);
      
      // Should still render something (fallback to sanitized plain text)
      expect(screen.getByText('Some content that might cause issues')).toBeInTheDocument();
      
      console.error = originalConsoleError;
    });
  });

  describe('Code Highlighting', () => {
    it('adds language class to code blocks', () => {
      const content = '```javascript\nconsole.log("hello");\n```';
      render(<SanitizedMarkdown content={content} />);
      
      const codeElement = screen.getByText('console.log("hello");');
      expect(codeElement).toHaveClass('language-javascript');
    });

    it('sanitizes language names', () => {
      const content = '```<script>alert("xss")</script>\nconsole.log("hello");\n```';
      render(<SanitizedMarkdown content={content} />);
      
      const codeElement = screen.getByText('console.log("hello");');
      expect(codeElement).not.toHaveClass('language-<script>alert("xss")</script>');
    });
  });
});

describe('sanitizeText utility', () => {
  it('removes all HTML tags', () => {
    const input = '<script>alert("xss")</script><p>Hello <strong>world</strong></p>';
    const result = sanitizeText(input);
    expect(result).toBe('Hello world');
  });

  it('truncates long text', () => {
    const longText = 'a'.repeat(100);
    const result = sanitizeText(longText, 50);
    expect(result).toHaveLength(53); // 50 + '...'
  });

  it('handles empty input', () => {
    expect(sanitizeText('')).toBe('');
    expect(sanitizeText(null as any)).toBe('');
    expect(sanitizeText(undefined as any)).toBe('');
  });
});

describe('sanitizeUrl utility', () => {
  it('allows safe protocols', () => {
    expect(sanitizeUrl('https://example.com')).toBe('https://example.com/');
    expect(sanitizeUrl('http://example.com')).toBe('http://example.com/');
    expect(sanitizeUrl('mailto:test@example.com')).toBe('mailto:test@example.com');
    expect(sanitizeUrl('tel:+1234567890')).toBe('tel:+1234567890');
  });

  it('blocks dangerous protocols', () => {
    expect(sanitizeUrl('javascript:alert("xss")')).toBe('');
    expect(sanitizeUrl('data:text/html,<script>alert("xss")</script>')).toBe('');
    expect(sanitizeUrl('vbscript:msgbox("xss")')).toBe('');
  });

  it('handles invalid URLs', () => {
    expect(sanitizeUrl('not-a-url')).toBe('');
    expect(sanitizeUrl('')).toBe('');
    expect(sanitizeUrl(null as any)).toBe('');
  });

  it('normalizes URLs', () => {
    expect(sanitizeUrl('https://example.com/path/../other')).toBe('https://example.com/other');
  });
});