// Chat Interface Constants
export const DEFAULT_PROCESSING_MESSAGE = 'Karen is working on your request...';
export const STREAMING_ERROR_MESSAGE = 'Connection issue - please try again';
export const STREAM_TIMEOUT_MESSAGE = 'Request timed out - please try again';

export const PROCESSING_STATUS_MESSAGE_VARIANTS: Record<string, string[]> = {
  initializing: [
    'Karen is preparing your workspace...',
    'Karen is initializing the request pipeline...',
  ],
  processing: [
    'Karen is analyzing your message...',
    'Karen is understanding what you need...',
  ],
  extracting_context: [
    'Karen is retrieving relevant context and memories...',
    'Karen is gathering useful conversation context...',
  ],
  generating_response: [
    'Karen is generating a response...',
    'Karen is drafting your answer...',
  ],
  streaming: [
    'Karen is composing the response...',
    'Karen is streaming the response...',
  ],
  executing_tools: [
    'Karen is executing tools and integrations...',
    'Karen is running supporting tasks...',
  ],
  recording_memory: [
    'Karen is recording insights from this conversation...',
    'Karen is saving useful context for next time...',
  ],
  post_processing: [
    'Karen is finalizing the response...',
    'Karen is polishing the final output...',
  ],
  retrying: [
    'Karen is retrying with an alternative provider...',
    'Karen is recovering from a temporary issue...',
  ],
  degraded: [
    'Karen is running in degraded mode...',
    'Karen is operating with limited capabilities...',
  ],
  completed: ['Response complete.'],
  failed: ['Processing failed. Retrying or falling back...'],
  cancelled: ['Request was cancelled.'],
};

export const normalizeProcessingStatusKey = (status: unknown): string => {
  if (status == null) return '';
  if (typeof status === 'string') {
    return status.trim().toLowerCase().replace(/[\s-]+/g, '_');
  }
  if (typeof status === 'object' && status !== null && 'value' in status) {
    const value = (status as { value?: unknown }).value;
    if (typeof value === 'string') {
      return value.trim().toLowerCase().replace(/[\s-]+/g, '_');
    }
  }
  return String(status).trim().toLowerCase().replace(/[\s-]+/g, '_');
};

export const resolveProcessingStatusMessage = (
  status: unknown,
  fallbackMessage?: string,
  variantIndex: number = 0,
): string => {
  const statusKey = normalizeProcessingStatusKey(status);
  const variants = PROCESSING_STATUS_MESSAGE_VARIANTS[statusKey];
  if (variants && variants.length > 0) {
    return variants[Math.abs(variantIndex) % variants.length];
  }

  if (typeof fallbackMessage === 'string' && fallbackMessage.trim()) {
    return fallbackMessage.trim();
  }

  if (statusKey) {
    return `Karen is ${statusKey.replace(/_/g, ' ')}...`;
  }
  return DEFAULT_PROCESSING_MESSAGE;
};

// UI Constants
export const MAX_RECENT_MESSAGES = 6;
export const SESSION_TIMEOUT = 30 * 60 * 1000; // 30 minutes
export const RENEWAL_INTERVAL = 5 * 60 * 1000; // 5 minutes
export const CLEANUP_INTERVAL = 24 * 60 * 60 * 1000; // 24 hours
export const INACTIVE_THRESHOLD = 7 * 24 * 60 * 60 * 1000; // 7 days
export const STICK_TO_BOTTOM_THRESHOLD = 120; // pixels
