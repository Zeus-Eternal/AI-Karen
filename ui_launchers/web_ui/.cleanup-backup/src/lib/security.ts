import DOMPurify from 'dompurify';

// Configure DOMPurify with secure defaults
const purifyConfig = {
  ALLOWED_TAGS: [
    'b', 'i', 'em', 'strong', 'code', 'pre', 'blockquote',
    'p', 'br', 'ul', 'ol', 'li', 'a', 'span'
  ],
  ALLOWED_ATTR: ['href', 'title', 'target', 'rel'],
  ALLOW_DATA_ATTR: false,
  ALLOWED_URI_REGEXP: /^(?:(?:(?:f|ht)tps?|mailto|tel|callto|sms|cid|xmpp):|[^a-z]|[a-z+.\-]+(?:[^a-z+.\-:]|$))/i,
  ADD_ATTR: ['target'],
  FORBID_TAGS: ['script', 'object', 'embed', 'form', 'input', 'textarea', 'select', 'option'],
  FORBID_ATTR: ['onerror', 'onload', 'onclick', 'onmouseover', 'style']
};

/**
 * Sanitizes user input to prevent XSS attacks
 * @param input - The raw input string to sanitize
 * @param allowHtml - Whether to allow safe HTML tags (default: false)
 * @returns Sanitized string safe for rendering
 */
export const sanitizeInput = (input: string, allowHtml: boolean = false): string => {
  if (!input || typeof input !== 'string') {
    return '';
  }

  // For plain text, strip all HTML
  if (!allowHtml) {
    return DOMPurify.sanitize(input, { 
      ALLOWED_TAGS: [], 
      ALLOWED_ATTR: [],
      KEEP_CONTENT: true 
    });
  }

  // For rich text, use configured safe tags
  return DOMPurify.sanitize(input, purifyConfig);
};

/**
 * Sanitizes message content for chat display
 * @param content - Message content to sanitize
 * @returns Sanitized content safe for display
 */
export const sanitizeMessageContent = (content: string): string => {
  return sanitizeInput(content, true);
};

/**
 * Validates and sanitizes file upload data
 * @param file - File object to validate
 * @param allowedTypes - Array of allowed MIME types
 * @param maxSize - Maximum file size in bytes
 * @returns Validation result with sanitized filename
 */
export const validateFileUpload = (
  file: File,
  allowedTypes: string[] = ['image/jpeg', 'image/png', 'image/gif', 'text/plain', 'application/pdf'],
  maxSize: number = 10 * 1024 * 1024 // 10MB default
): { isValid: boolean; error?: string; sanitizedName?: string } => {
  
  // Check file size
  if (file.size > maxSize) {
    return {
      isValid: false,
      error: `File size exceeds maximum allowed size of ${Math.round(maxSize / 1024 / 1024)}MB`
    };
  }

  // Check file type
  if (!allowedTypes.includes(file.type)) {
    return {
      isValid: false,
      error: `File type ${file.type} is not allowed. Allowed types: ${allowedTypes.join(', ')}`
    };
  }

  // Sanitize filename
  const sanitizedName = file.name
    .replace(/[^a-zA-Z0-9.\-_]/g, '_') // Replace special chars with underscore
    .replace(/_{2,}/g, '_') // Replace multiple underscores with single
    .substring(0, 255); // Limit length

  return {
    isValid: true,
    sanitizedName
  };
};

/**
 * Sanitizes URLs to prevent malicious redirects
 * @param url - URL string to validate
 * @returns Sanitized URL or null if invalid
 */
export const sanitizeUrl = (url: string): string | null => {
  try {
    const urlObj = new URL(url);
    
    // Only allow http, https, and mailto protocols
    if (!['http:', 'https:', 'mailto:'].includes(urlObj.protocol)) {
      return null;
    }

    // Block localhost and private IPs in production
    if (process.env.NODE_ENV === 'production') {
      const hostname = urlObj.hostname.toLowerCase();
      if (
        hostname === 'localhost' ||
        hostname.startsWith('127.') ||
        hostname.startsWith('192.168.') ||
        hostname.startsWith('10.') ||
        hostname.match(/^172\.(1[6-9]|2[0-9]|3[0-1])\./)
      ) {
        return null;
      }
    }

    return urlObj.toString();
  } catch {
    return null;
  }
};

/**
 * Escapes special characters for safe inclusion in RegExp
 * @param string - String to escape
 * @returns Escaped string safe for RegExp
 */
export const escapeRegExp = (string: string): string => {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
};

/**
 * Truncates text to specified length with ellipsis
 * @param text - Text to truncate
 * @param maxLength - Maximum length
 * @returns Truncated text
 */
export const truncateText = (text: string, maxLength: number = 1000): string => {
  if (text.length <= maxLength) {
    return text;
  }
  return text.substring(0, maxLength - 3) + '...';
};

export default {
  sanitizeInput,
  sanitizeMessageContent,
  validateFileUpload,
  sanitizeUrl,
  escapeRegExp,
  truncateText
};
