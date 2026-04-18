import { ApiError } from '@/lib/api';

export const getDegradedResponseMessage = (error: unknown): string => {
  if (error instanceof ApiError) {
    const errorPayload = error.details as Record<string, unknown>;
    const runtimeMode = typeof errorPayload?.mode === 'string' ? errorPayload.mode : '';

    if (
      (runtimeMode === 'maintenance' ||
        runtimeMode === 'emergency_fallback' ||
        runtimeMode === 'degraded') &&
      typeof errorPayload?.message === 'string'
    ) {
      return errorPayload.message;
    }

    const detail = error.message?.trim();

    // If we have a specific informative detail, prioritize it.
    // We no longer strip the "HTTP [code]:" prefix if it contains useful info.
    if (detail && detail.length > 3) {
      return detail;
    }

     // If we have detailed error content in the response body, use it specifically.
     if (errorPayload?.detail && typeof errorPayload.detail === 'string') {
       return errorPayload.detail;
     }
     if (errorPayload?.error && typeof errorPayload.error === 'string') {
       return errorPayload.error;
     }

     if (error.status >= 500) {
       return detail || 'Karen is running in degraded mode right now. Model routing is currently unavailable or misconfigured.';
     }

     if (error.status === 401 || error.status === 403) {
       return 'Karen could not use the requested provider with your current session permissions. Sign in again or switch to an available model.';
     }

     return detail || 'Karen encountered an API error while processing your request.';
   }

   if (error instanceof Error) {
     return error.message;
   }

   return 'Karen is running in degraded mode right now and could not complete this message. Check model availability and try again.';
 };