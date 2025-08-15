import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { SecureLink, validateUrl, secureExistingLinks } from '../SecureLink';

// Mock the telemetry hook
const mockTrack = vi.fn();
vi.mock('@/hooks/use-telemetry', () => ({
  useTelemetry: () => ({
    track: mockTrack
  })
}));

describe('SecureLink', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Internal Links', () => {
    it('renders internal relative links without security attributes', () => {
      render(
        <SecureLink href="/internal-page">
          Internal Link
        </SecureLink>
      );

      const link = screen.getByRole('link');
      expect(link).toHaveAttribute('href', '/internal-page');
      expect(link).not.toHaveAttribute('target');
      expect(link).not.toHaveAttribute('rel');
      expect(link).toHaveAttribute('data-external', 'false');
      expect(link).toHaveAttribute('data-secure', 'true');
    });

    it('handles hash links correctly', () => {
      render(
        <SecureLink href="#section">
          Hash Link
        </SecureLink>
      );

      const link = screen.getByRole('link');
      expect(link).toHaveAttribute('href', '#section');
      expect(link).toHaveAttribute('data-external', 'false');
    });

    it('handles query parameter links correctly', () => {
      render(
        <SecureLink href="?param=value">
          Query Link
        </SecureLink>
      );

      const link = screen.getByRole('link');
      expect(link).toHaveAttribute('href', '?param=value');
      expect(link).toHaveAttribute('data-external', 'false');
    });
  });

  describe('External Links', () => {
    it('adds security attributes to external HTTPS links', () => {
      render(
        <SecureLink href="https://example.com">
          External Link
        </SecureLink>
      );

      const link = screen.getByRole('link');
      expect(link).toHaveAttribute('href', 'https://example.com/');
      expect(link).toHaveAttribute('target', '_blank');
      expect(link).toHaveAttribute('rel', 'noopener noreferrer');
      expect(link).toHaveAttribute('data-external', 'true');
      expect(link).toHaveAttribute('data-secure', 'true');
    });

    it('handles HTTP links correctly', () => {
      render(
        <SecureLink href="http://example.com">
          HTTP Link
        </SecureLink>
      );

      const link = screen.getByRole('link');
      expect(link).toHaveAttribute('href', 'http://example.com/');
      expect(link).toHaveAttribute('target', '_blank');
      expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    });

    it('respects forceExternal prop', () => {
      render(
        <SecureLink href="/internal" forceExternal>
          Forced External
        </SecureLink>
      );

      const link = screen.getByRole('link');
      expect(link).toHaveAttribute('target', '_blank');
      expect(link).toHaveAttribute('rel', 'noopener noreferrer');
      expect(link).toHaveAttribute('data-external', 'true');
    });
  });

  describe('Security Violations', () => {
    it('blocks javascript: URLs', () => {
      const onSecurityViolation = vi.fn();
      
      render(
        <SecureLink 
          href="javascript:alert('xss')" 
          onSecurityViolation={onSecurityViolation}
        >
          Malicious Link
        </SecureLink>
      );

      expect(screen.queryByRole('link')).not.toBeInTheDocument();
      
      const span = screen.getByText('Malicious Link');
      expect(span.tagName).toBe('SPAN');
      expect(span).toHaveAttribute('data-security-violation', 'true');
      expect(span).toHaveClass('cursor-not-allowed', 'opacity-50');
      
      expect(onSecurityViolation).toHaveBeenCalledWith(
        'Dangerous protocol: javascript:',
        "javascript:alert('xss')"
      );
      
      expect(mockTrack).toHaveBeenCalledWith('secure_link_violation', {
        href: "javascript:alert('xss')",
        reason: 'Dangerous protocol: javascript:',
        isValid: false,
        isSafe: false
      });
    });

    it('blocks data: URLs', () => {
      render(
        <SecureLink href="data:text/html,<script>alert('xss')</script>">
          Data URL
        </SecureLink>
      );

      expect(screen.queryByRole('link')).not.toBeInTheDocument();
      const span = screen.getByText('Data URL');
      expect(span).toHaveAttribute('data-security-violation', 'true');
    });

    it('blocks vbscript: URLs', () => {
      render(
        <SecureLink href="vbscript:msgbox('xss')">
          VBScript URL
        </SecureLink>
      );

      expect(screen.queryByRole('link')).not.toBeInTheDocument();
    });

    it('blocks file: URLs', () => {
      render(
        <SecureLink href="file:///etc/passwd">
          File URL
        </SecureLink>
      );

      expect(screen.queryByRole('link')).not.toBeInTheDocument();
    });

    it('handles invalid URLs', () => {
      render(
        <SecureLink href="not-a-valid-url">
          Invalid URL
        </SecureLink>
      );

      expect(screen.queryByRole('link')).not.toBeInTheDocument();
      const span = screen.getByText('Invalid URL');
      expect(span).toHaveAttribute('data-security-violation', 'true');
    });

    it('handles empty href', () => {
      render(
        <SecureLink href="">
          Empty Link
        </SecureLink>
      );

      expect(screen.queryByRole('link')).not.toBeInTheDocument();
    });
  });

  describe('Safe Protocols', () => {
    it('allows mailto: links', () => {
      render(
        <SecureLink href="mailto:test@example.com">
          Email Link
        </SecureLink>
      );

      const link = screen.getByRole('link');
      expect(link).toHaveAttribute('href', 'mailto:test@example.com');
      expect(link).toHaveAttribute('data-external', 'true');
    });

    it('allows tel: links', () => {
      render(
        <SecureLink href="tel:+1234567890">
          Phone Link
        </SecureLink>
      );

      const link = screen.getByRole('link');
      expect(link).toHaveAttribute('href', 'tel:+1234567890');
      expect(link).toHaveAttribute('data-external', 'true');
    });

    it('allows sms: links', () => {
      render(
        <SecureLink href="sms:+1234567890">
          SMS Link
        </SecureLink>
      );

      const link = screen.getByRole('link');
      expect(link).toHaveAttribute('href', 'sms:+1234567890');
      expect(link).toHaveAttribute('data-external', 'true');
    });
  });

  describe('Custom Allowed Domains', () => {
    it('treats custom domains as internal', () => {
      render(
        <SecureLink 
          href="https://myapp.com/page" 
          allowedDomains={['myapp.com']}
        >
          Custom Domain
        </SecureLink>
      );

      const link = screen.getByRole('link');
      expect(link).toHaveAttribute('data-external', 'false');
      expect(link).not.toHaveAttribute('target');
    });

    it('handles subdomains correctly', () => {
      render(
        <SecureLink 
          href="https://api.myapp.com/endpoint" 
          allowedDomains={['myapp.com']}
        >
          Subdomain
        </SecureLink>
      );

      const link = screen.getByRole('link');
      expect(link).toHaveAttribute('data-external', 'false');
    });
  });

  describe('Props and Styling', () => {
    it('passes through additional props', () => {
      render(
        <SecureLink 
          href="/test" 
          className="custom-class" 
          id="test-link"
          title="Test Title"
        >
          Test Link
        </SecureLink>
      );

      const link = screen.getByRole('link');
      expect(link).toHaveClass('custom-class');
      expect(link).toHaveAttribute('id', 'test-link');
      expect(link).toHaveAttribute('title', 'Test Title');
    });

    it('applies security violation styling', () => {
      render(
        <SecureLink href="javascript:void(0)" className="original-class">
          Blocked Link
        </SecureLink>
      );

      const span = screen.getByText('Blocked Link');
      expect(span).toHaveClass('cursor-not-allowed', 'opacity-50', 'original-class');
    });
  });
});

describe('validateUrl utility', () => {
  it('validates safe URLs correctly', () => {
    const result = validateUrl('https://example.com');
    expect(result).toEqual({
      isValid: true,
      isSafe: true,
      isExternal: true,
      sanitizedUrl: 'https://example.com/',
      reason: 'Valid URL'
    });
  });

  it('rejects dangerous protocols', () => {
    const result = validateUrl('javascript:alert("xss")');
    expect(result).toEqual({
      isValid: false,
      isSafe: false,
      isExternal: true,
      sanitizedUrl: '',
      reason: 'Dangerous protocol: javascript:'
    });
  });

  it('handles relative URLs', () => {
    const result = validateUrl('/internal/page');
    expect(result).toEqual({
      isValid: true,
      isSafe: true,
      isExternal: false,
      sanitizedUrl: '/internal/page',
      reason: 'Internal relative URL'
    });
  });

  it('handles empty URLs', () => {
    const result = validateUrl('');
    expect(result).toEqual({
      isValid: false,
      isSafe: false,
      isExternal: false,
      sanitizedUrl: '',
      reason: 'Empty URL'
    });
  });

  it('respects custom allowed domains', () => {
    const result = validateUrl('https://myapp.com', ['myapp.com']);
    expect(result.isExternal).toBe(false);
  });
});

describe('secureExistingLinks utility', () => {
  it('secures external links in container', () => {
    const container = document.createElement('div');
    container.innerHTML = `
      <a href="https://example.com">External</a>
      <a href="/internal">Internal</a>
      <a href="javascript:alert('xss')">Malicious</a>
    `;

    secureExistingLinks(container);

    const links = container.querySelectorAll('a');
    
    // External link should have security attributes
    expect(links[0]).toHaveAttribute('target', '_blank');
    expect(links[0]).toHaveAttribute('rel', 'noopener noreferrer');
    expect(links[0]).toHaveAttribute('data-external', 'true');
    
    // Internal link should not have external attributes
    expect(links[1]).not.toHaveAttribute('target');
    expect(links[1]).not.toHaveAttribute('rel');
    
    // Malicious link should be disabled
    expect(links[2]).not.toHaveAttribute('href');
    expect(links[2]).toHaveAttribute('data-security-violation', 'true');
    expect(links[2]).toHaveClass('cursor-not-allowed', 'opacity-50');
  });

  it('handles links without href', () => {
    const container = document.createElement('div');
    container.innerHTML = '<a>No href</a>';

    expect(() => secureExistingLinks(container)).not.toThrow();
  });

  it('marks all processed links as secure', () => {
    const container = document.createElement('div');
    container.innerHTML = '<a href="/test">Test</a>';

    secureExistingLinks(container);

    const link = container.querySelector('a');
    expect(link).toHaveAttribute('data-secure', 'true');
  });
});