import { ApiError } from '@/lib/api';

export function formatModelSwitchError(
  error: unknown,
  providerDisplayName: string,
): string {
  if (!(error instanceof ApiError)) {
    if (error instanceof Error && error.message.trim()) {
      return error.message.trim();
    }
    return 'Karen could not update the active provider and model.';
  }

  const detail = error.message?.trim() || '';
  const lowered = detail.toLowerCase();
  const providerLabel = providerDisplayName || 'The selected provider';

  const isCredentialError =
    lowered.includes('api key validation failed') ||
    lowered.includes('token expired') ||
    lowered.includes('incorrect') ||
    lowered.includes('unauthorized') ||
    lowered.includes('forbidden') ||
    lowered.includes('401');

  if (isCredentialError) {
    return `${providerLabel} credential is invalid or expired. Update the API key/token in settings, or switch to llama.cpp/local, then try again.`;
  }

  if (lowered.includes('timed out')) {
    return `${providerLabel} validation timed out. Check provider base URL/network reachability and retry.`;
  }

  if (error.status >= 500) {
    return `${providerLabel} is currently unavailable from the backend. Check runtime health and provider connectivity, then retry.`;
  }

  return detail || 'Karen could not update the active provider and model.';
}
