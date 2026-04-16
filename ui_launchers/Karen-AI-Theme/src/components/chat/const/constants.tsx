// Chat Interface Constants
export const DEFAULT_PROCESSING_MESSAGE = 'Karen is working on your request...';
export const STREAMING_ERROR_MESSAGE = 'Connection issue - please try again';
export const STREAM_TIMEOUT_MESSAGE = 'Request timed out - please try again';

// UI Constants
export const MAX_RECENT_MESSAGES = 6;
export const SESSION_TIMEOUT = 30 * 60 * 1000; // 30 minutes
export const RENEWAL_INTERVAL = 5 * 60 * 1000; // 5 minutes
export const CLEANUP_INTERVAL = 24 * 60 * 60 * 1000; // 24 hours
export const INACTIVE_THRESHOLD = 7 * 24 * 60 * 60 * 1000; // 7 days
export const STICK_TO_BOTTOM_THRESHOLD = 120; // pixels