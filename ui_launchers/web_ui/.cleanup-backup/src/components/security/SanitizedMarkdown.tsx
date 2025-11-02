'use client';

import React, { useMemo } from 'react';
import DOMPurify from 'dompurify';
import { marked } from 'marked';
import { useTelemetry } from '@/hooks/use-telemetry';

interface SanitizedMarkdownProps {
  content: string;
  allowedTags?: string[];
  allowedAttributes?: Record<string, string[]>;
  linkTarget?: '_blank' | '_self';
  className?: string;
  maxLength?: number;
}

// Strict allowlist for HTML tags
const DEFAULT_ALLOWED_TAGS = [
  'p', 'br', 'strong', 'em', 'u', 'code', 'pre',
  'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
  'ul', 'ol', 'li',
  'blockquote',
  'a',
  'span'
];

// Allowed attributes for each tag
const DEFAULT_ALLOWED_ATTRIBUTES = {
  'a': ['href', 'title', 'target', 'rel'],
  'code': ['class'],
  'pre': ['class'],
  'span': ['class'],
  '*': ['class'] // Allow class on all elements for styling
};

// Configure marked with security settings
const configureMarked = (linkTarget: '_blank' | '_self' = '_blank') => {
  const renderer = new marked.Renderer();
  
  // Override link renderer to add security attributes
  renderer.link = (href, title, text) => {
    const isExternal = href && (href.startsWith('http') || href.startsWith('//'));
    const target = isExternal ? linkTarget : '_self';
    const rel = isExternal ? 'noopener noreferrer' : '';
    
    return `<a href="${href}"${title ? ` title="${title}"` : ''}${target ? ` target="${target}"` : ''}${rel ? ` rel="${rel}"` : ''}>${text}</a>`;
  };
  
  // Override code renderer for syntax highlighting classes
  renderer.code = (code, language) => {
    const validLanguage = language && /^[a-zA-Z0-9-_]+$/.test(language) ? language : '';
    return `<pre><code${validLanguage ? ` class="language-${validLanguage}"` : ''}>${code}</code></pre>`;
  };
  
  return marked.setOptions({
    renderer,
    gfm: true,
    breaks: true
    // Many options like sanitize, smartLists, smartypants, xhtml were removed in newer versions of marked
  });
};

export const SanitizedMarkdown: React.FC<SanitizedMarkdownProps> = ({
  content,
  allowedTags = DEFAULT_ALLOWED_TAGS,
  allowedAttributes = DEFAULT_ALLOWED_ATTRIBUTES,
  linkTarget = '_blank',
  className = '',
  maxLength = 50000 // Prevent extremely large content
}) => {
  const { track } = useTelemetry();
  
  const sanitizedHtml = useMemo(() => {
    if (!content || content.length === 0) {
      return '';
    }
    
    // Truncate content if too long
    const truncatedContent = content.length > maxLength 
      ? content.substring(0, maxLength) + '...' 
      : content;
    
    try {
      // Configure marked
      configureMarked(linkTarget);
      
      // Convert markdown to HTML synchronously
      const rawHtml = marked(truncatedContent) as string;
      
      // Configure DOMPurify
      const purifyConfig = {
        ALLOWED_TAGS: allowedTags,
        ALLOWED_ATTR: Object.keys(allowedAttributes).reduce((acc, tag) => {
          const attributes = allowedAttributes[tag as keyof typeof allowedAttributes];
          if (attributes) {
            acc.push(...attributes);
          }
          return acc;
        }, [] as string[]),
        ALLOW_DATA_ATTR: false,
        ALLOW_UNKNOWN_PROTOCOLS: false,
        ALLOWED_URI_REGEXP: /^(?:(?:(?:f|ht)tps?|mailto|tel|callto|cid|xmpp|xxx):|[^a-z]|[a-z+.\-]+(?:[^a-z+.\-:]|$))/i,
        ADD_TAGS: [],
        ADD_ATTR: [],
        FORBID_TAGS: ['script', 'object', 'embed', 'form', 'input', 'button'],
        FORBID_ATTR: ['onerror', 'onload', 'onclick', 'onmouseover', 'onfocus', 'onblur'],
        USE_PROFILES: { html: true },
        WHOLE_DOCUMENT: false,
        RETURN_DOM: false,
        RETURN_DOM_FRAGMENT: false,
        RETURN_TRUSTED_TYPE: false,
        SANITIZE_DOM: true,
        KEEP_CONTENT: true,
        IN_PLACE: false,
        ALLOWED_NAMESPACES: ['http://www.w3.org/1999/xhtml'],
        CUSTOM_ELEMENT_HANDLING: {
          tagNameCheck: null,
          attributeNameCheck: null,
          allowCustomizedBuiltInElements: false,
        }
      };
      
      // Sanitize the HTML
      const cleanHtml = DOMPurify.sanitize(rawHtml, purifyConfig);
      
      // Track sanitization metrics
      track('markdown_sanitized', {
        originalLength: content.length,
        truncated: content.length > maxLength,
        sanitizedLength: cleanHtml.length,
        removedContent: rawHtml.length - cleanHtml.length > 0
      });
      
      return cleanHtml;
      
    } catch (error) {
      console.error('Markdown sanitization error:', error);
      track('markdown_sanitization_error', {
        error: error instanceof Error ? error.message : 'Unknown error',
        contentLength: content.length
      });
      
      // Fallback to plain text
      return DOMPurify.sanitize(content, { 
        ALLOWED_TAGS: [], 
        ALLOWED_ATTR: [] 
      });
    }
  }, [content, allowedTags, allowedAttributes, linkTarget, maxLength, track]);
  
  if (!sanitizedHtml) {
    return null;
  }
  
  return (
    <div 
      className={`prose prose-sm max-w-none dark:prose-invert ${className}`}
      dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
      data-sanitized="true"
    />
  );
};

// Utility function for sanitizing plain text (no markdown)
export const sanitizeText = (text: string, maxLength: number = 10000): string => {
  if (!text) return '';
  
  const truncated = text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  
  return DOMPurify.sanitize(truncated, {
    ALLOWED_TAGS: [],
    ALLOWED_ATTR: [],
    KEEP_CONTENT: true
  });
};

// Utility function for sanitizing URLs
export const sanitizeUrl = (url: string): string => {
  if (!url) return '';
  
  try {
    const parsed = new URL(url);
    
    // Only allow safe protocols
    const allowedProtocols = ['http:', 'https:', 'mailto:', 'tel:'];
    if (!allowedProtocols.includes(parsed.protocol)) {
      return '';
    }
    
    return parsed.toString();
  } catch {
    return '';
  }
};

export default SanitizedMarkdown;