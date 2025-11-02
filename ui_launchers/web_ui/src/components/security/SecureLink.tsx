"use client";

import React, { useMemo } from 'react';
import { useTelemetry } from '@/hooks/use-telemetry';

interface SecureLinkProps extends Omit<React.AnchorHTMLAttributes<HTMLAnchorElement>, 'href' | 'target' | 'rel'> {
  href: string;
  children: React.ReactNode;
  external?: boolean;
  forceExternal?: boolean;
  allowedDomains?: string[];
  onSecurityViolation?: (reason: string, href: string) => void;
  className?: string;
}

// Default allowed domains for internal links
const DEFAULT_ALLOWED_DOMAINS = [
  'localhost',
  '127.0.0.1',
  '0.0.0.0'
];

// Dangerous protocols that should be blocked
const DANGEROUS_PROTOCOLS = [
  'javascript:',
  'data:',
  'vbscript:',
  'file:',
  'ftp:'
];

// Safe protocols that are allowed
const SAFE_PROTOCOLS = [
  'http:',
  'https:',
  'mailto:',
  'tel:',
  'sms:'
];

export const SecureLink: React.FC<SecureLinkProps> = ({
  href,
  children,
  external,
  forceExternal = false,
  allowedDomains = DEFAULT_ALLOWED_DOMAINS,
  onSecurityViolation,
  className = '',
  ...props
}) => {
  const { track } = useTelemetry();

  const linkAnalysis = useMemo(() => {
    if (!href) {
      return {
        isValid: false,
        isSafe: false,
        isExternal: false,
        sanitizedHref: '',
        reason: 'Empty href'
      };
    }

    try {
      // Handle relative URLs
      if (href.startsWith('/') || href.startsWith('#') || href.startsWith('?')) {
        return {
          isValid: true,
          isSafe: true,
          isExternal: false,
          sanitizedHref: href,
          reason: 'Internal relative URL'
        };
      }

      // Parse the URL
      const url = new URL(href);
      
      // Check for dangerous protocols
      if (DANGEROUS_PROTOCOLS.some(protocol => url.protocol === protocol)) {
        return {
          isValid: false,
          isSafe: false,
          isExternal: true,
          sanitizedHref: '',
          reason: `Dangerous protocol: ${url.protocol}`
        };
      }

      // Check for safe protocols
      if (!SAFE_PROTOCOLS.includes(url.protocol)) {
        return {
          isValid: false,
          isSafe: false,
          isExternal: true,
          sanitizedHref: '',
          reason: `Unsupported protocol: ${url.protocol}`
        };
      }

      // Determine if external
      const isExternalLink = external !== undefined 
        ? external 
        : !allowedDomains.some(domain => 
            url.hostname === domain || 
            url.hostname.endsWith(`.${domain}`)
          );

      return {
        isValid: true,
        isSafe: true,
        isExternal: isExternalLink || forceExternal,
        sanitizedHref: url.toString(),
        reason: 'Valid URL'
      };

    } catch (error) {
      return {
        isValid: false,
        isSafe: false,
        isExternal: false,
        sanitizedHref: '',
        reason: `Invalid URL: ${error instanceof Error ? error.message : 'Unknown error'}`
      };
    }
  }, [href, external, forceExternal, allowedDomains]);

  // Handle security violations
  if (!linkAnalysis.isSafe || !linkAnalysis.isValid) {
    track('secure_link_violation', {
      href,
      reason: linkAnalysis.reason,
      isValid: linkAnalysis.isValid,
      isSafe: linkAnalysis.isSafe

    onSecurityViolation?.(linkAnalysis.reason, href);

    // Return a span instead of a link for security violations
    return (
      <span 
        className={`cursor-not-allowed opacity-50 ${className}`}
        title={`Link blocked: ${linkAnalysis.reason}`}
        data-security-violation="true"
        {...(props as any)}
      >
        {children}
      </span>
    );
  }

  // Track valid link usage
  track('secure_link_rendered', {
    href: linkAnalysis.sanitizedHref,
    isExternal: linkAnalysis.isExternal,
    protocol: new URL(linkAnalysis.sanitizedHref).protocol

  // Render secure link
  const linkProps: React.AnchorHTMLAttributes<HTMLAnchorElement> = {
    href: linkAnalysis.sanitizedHref,
    className,
    ...props
  };

  // Add security attributes for external links
  if (linkAnalysis.isExternal) {
    linkProps.target = '_blank';
    linkProps.rel = 'noopener noreferrer';
  }

  return (
    <a 
      {...linkProps}
      data-external={linkAnalysis.isExternal}
      data-secure="true"
    >
      {children}
    </a>
  );
};

// Utility function to validate and sanitize URLs
export const validateUrl = (url: string, allowedDomains?: string[]): {
  isValid: boolean;
  isSafe: boolean;
  isExternal: boolean;
  sanitizedUrl: string;
  reason: string;
} => {
  if (!url) {
    return {
      isValid: false,
      isSafe: false,
      isExternal: false,
      sanitizedUrl: '',
      reason: 'Empty URL'
    };
  }

  try {
    // Handle relative URLs
    if (url.startsWith('/') || url.startsWith('#') || url.startsWith('?')) {
      return {
        isValid: true,
        isSafe: true,
        isExternal: false,
        sanitizedUrl: url,
        reason: 'Internal relative URL'
      };
    }

    const parsedUrl = new URL(url);
    
    // Check for dangerous protocols
    if (DANGEROUS_PROTOCOLS.some(protocol => parsedUrl.protocol === protocol)) {
      return {
        isValid: false,
        isSafe: false,
        isExternal: true,
        sanitizedUrl: '',
        reason: `Dangerous protocol: ${parsedUrl.protocol}`
      };
    }

    // Check for safe protocols
    if (!SAFE_PROTOCOLS.includes(parsedUrl.protocol)) {
      return {
        isValid: false,
        isSafe: false,
        isExternal: true,
        sanitizedUrl: '',
        reason: `Unsupported protocol: ${parsedUrl.protocol}`
      };
    }

    // Determine if external
    const domains = allowedDomains || DEFAULT_ALLOWED_DOMAINS;
    const isExternal = !domains.some(domain => 
      parsedUrl.hostname === domain || 
      parsedUrl.hostname.endsWith(`.${domain}`)
    );

    return {
      isValid: true,
      isSafe: true,
      isExternal,
      sanitizedUrl: parsedUrl.toString(),
      reason: 'Valid URL'
    };

  } catch (error) {
    return {
      isValid: false,
      isSafe: false,
      isExternal: false,
      sanitizedUrl: '',
      reason: `Invalid URL: ${error instanceof Error ? error.message : 'Unknown error'}`
    };
  }
};

// Utility function to add security attributes to existing links
export const secureExistingLinks = (container: HTMLElement): void => {
  const links = container.querySelectorAll('a[href]');
  
  links.forEach((link) => {
    const href = link.getAttribute('href');
    if (!href) return;

    const validation = validateUrl(href);
    
    if (!validation.isSafe || !validation.isValid) {
      // Remove dangerous links
      link.removeAttribute('href');
      link.setAttribute('data-security-violation', 'true');
      link.setAttribute('title', `Link blocked: ${validation.reason}`);
      link.classList.add('cursor-not-allowed', 'opacity-50');
      return;
    }

    // Add security attributes for external links
    if (validation.isExternal) {
      link.setAttribute('target', '_blank');
      link.setAttribute('rel', 'noopener noreferrer');
      link.setAttribute('data-external', 'true');
    }

    link.setAttribute('data-secure', 'true');

};

// React hook for secure link handling
export const useSecureLinks = (containerRef: React.RefObject<HTMLElement>) => {
  React.useEffect(() => {
    if (containerRef.current) {
      secureExistingLinks(containerRef.current);
    }
  }, [containerRef]);
};

export default SecureLink;