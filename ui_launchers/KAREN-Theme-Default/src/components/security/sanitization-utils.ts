import DOMPurify from 'isomorphic-dompurify';

export const sanitizeText = (text: string, maxLength: number = 10000): string => {
  if (!text) return '';
  const truncated = text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  return DOMPurify.sanitize(truncated, {
    ALLOWED_TAGS: [],
    ALLOWED_ATTR: [],
    KEEP_CONTENT: true,
  });
};

export const sanitizeUrl = (url: string): string => {
  if (!url) return '';
  try {
    const parsed = new URL(url);
    const allowedProtocols = ['http:', 'https:', 'mailto:', 'tel:'];
    if (!allowedProtocols.includes(parsed.protocol)) {
      return '';
    }
    return parsed.toString();
  } catch {
    return '';
  }
};
