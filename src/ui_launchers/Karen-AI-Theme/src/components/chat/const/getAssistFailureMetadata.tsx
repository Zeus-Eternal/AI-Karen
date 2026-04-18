import { useCallback } from 'react';
import { ApiError } from '@/lib/api';
import { getDegradedResponseMessage } from './getDegradedResponseMessage';
import { normalizeProviderName } from '@/lib/chat-response';

export const getAssistFailureMetadata = (
  error: unknown,
  requestedProvider?: string,
  requestedModel?: string,
): Record<string, unknown> => {
    const detail = getDegradedResponseMessage(error);
    const normalizedProvider = normalizeProviderName(requestedProvider) || 'system';
    const failureCategory =
      error instanceof ApiError && (error.status === 401 || error.status === 403)
        ? 'authorization'
        : error instanceof TypeError
          ? 'network'
          : 'provider_error';

    const metadata: Record<string, unknown> = {
      degraded_mode: true,
      failure_category: failureCategory,
      orchestrator: {
        used_fallback: true,
      },
      llm: {
        provider: normalizedProvider,
        model_id: requestedModel ? `${normalizedProvider}:${requestedModel}` : normalizedProvider,
        model_name: requestedModel || undefined,
        requested_provider: requestedProvider || undefined,
        requested_model: requestedModel || undefined,
        is_degraded: true,
        source: 'assist_request_error',
        fallback_level: 'error',
        failure_reason: detail,
        routing_rationale:
          requestedProvider && requestedModel
            ? `The request to ${requestedProvider}/${requestedModel} failed before Karen could complete the response.`
            : 'The chat request failed before Karen could complete the response.',
      },
    };

    if (error instanceof ApiError) {
      metadata.http_status = error.status;
      metadata.error_details = error.details;
    }

  return metadata;
};