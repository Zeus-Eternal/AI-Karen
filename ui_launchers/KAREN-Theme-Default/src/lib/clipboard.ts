/**
 * Clipboard utility with fallback support for older browsers and insecure contexts
 */
export interface CopyToClipboardOptions {
  onSuccess?: () => void;
  onError?: (error: Error) => void;
  showToast?: boolean;
}
/**
 * Copy text to clipboard with fallback support
 * @param text - Text to copy to clipboard
 * @param options - Options for success/error handling
 * @returns Promise that resolves when copy is complete
 */
export async function copyToClipboard(
  text: string, 
  options: CopyToClipboardOptions = {}
): Promise<void> {
  const { onSuccess, onError } = options;
  try {
    // Check if modern Clipboard API is available
    if (typeof navigator !== 'undefined' && navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
      await navigator.clipboard.writeText(text);
      if (onSuccess) onSuccess();
      return;
    }
    // Fallback for older browsers or insecure contexts (HTTP)
    const textArea = document.createElement('textarea');
    textArea.value = text;
    // Make the textarea invisible but focusable
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    textArea.style.opacity = '0';
    textArea.setAttribute('readonly', '');
    document.body.appendChild(textArea);
    try {
      // Focus and select the text
      textArea.focus();
      textArea.select();
      textArea.setSelectionRange(0, text.length);
      // Use the legacy execCommand API
      const successful = document.execCommand('copy');
      if (!successful) {
        throw new Error('execCommand copy failed');
      }
      if (onSuccess) onSuccess();
    } finally {
      // Always clean up the temporary element
      document.body.removeChild(textArea);
    }
  } catch (error) {
    const copyError = error instanceof Error ? error : new Error('Copy operation failed');
    if (onError) {
      onError(copyError);
    } else {
      // Error will be thrown below
    }
    throw copyError;
  }
}
/**
 * Check if clipboard functionality is available
 * @returns true if clipboard is available, false otherwise
 */
export function isClipboardAvailable(): boolean {
  // Check for modern Clipboard API
  if (typeof navigator !== 'undefined' && navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
    return true;
  }
  // Check for legacy execCommand support
  try {
    return document.queryCommandSupported?.('copy') ?? false;
  } catch {
    return false;
  }
}
/**
 * Get the appropriate clipboard method description for user feedback
 * @returns Description of available clipboard method
 */
export function getClipboardMethodInfo(): string {
  if (typeof navigator !== 'undefined' && navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
    return 'Using modern Clipboard API';
  } else if (document.queryCommandSupported?.('copy')) {
    return 'Using legacy copy command';
  } else {
    return 'Clipboard not available';
  }
}
