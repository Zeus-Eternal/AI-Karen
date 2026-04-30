import { ApiError } from '@/lib/api';
import { normalizeProviderName } from '@/lib/chat-response';
import { getDegradedResponseMessage } from './getDegradedResponseMessage';

type AssistFailureCategory =
  | 'authorization'
  | 'network'
  | 'timeout'
  | 'server'
  | 'provider_error'
  | 'unknown';

const REQUEST_FAILURE_PROVIDER = 'system';
const REQUEST_FAILURE_MODEL = 'assist_request_error';

const cleanString = (value: unknown): string => {
  return typeof value === 'string' ? value.trim() : '';
};

const getErrorName = (error: unknown): string => {
  if (error instanceof Error && error.name.trim()) {
    return error.name.trim();
  }

  return 'AssistRequestError';
};

const getErrorMessage = (error: unknown): string => {
  if (error instanceof Error && error.message.trim()) {
    return error.message.trim();
  }

  if (typeof error === 'string' && error.trim()) {
    return error.trim();
  }

  return getDegradedResponseMessage(error);
};

const getFailureCategory = (error: unknown): AssistFailureCategory => {
  if (error instanceof ApiError) {
    if (error.status === 401 || error.status === 403) {
      return 'authorization';
    }

    if (error.status === 408 || error.status === 504) {
      return 'timeout';
    }

    if (error.status >= 500) {
      return 'server';
    }

    return 'provider_error';
  }

  if (error instanceof TypeError) {
    return 'network';
  }

  if (error instanceof DOMException && error.name === 'AbortError') {
    return 'timeout';
  }

  if (error instanceof Error) {
    const message = error.message.toLowerCase();

    if (
      message.includes('timeout') ||
      message.includes('timed out') ||
      message.includes('aborted')
    ) {
      return 'timeout';
    }

    if (
      message.includes('network') ||
      message.includes('failed to fetch') ||
      message.includes('connection')
    ) {
      return 'network';
    }
  }

  return 'unknown';
};

const getRoutingRationale = (
  requestedProvider: string,
  requestedModel: string,
): string => {
  if (requestedProvider && requestedModel) {
    return `The request to ${requestedProvider}/${requestedModel} failed before Karen could complete the response.`;
  }

  if (requestedProvider) {
    return `The request to ${requestedProvider} failed before Karen could complete the response.`;
  }

  return 'The chat request failed before Karen could complete the response.';
};

export const getAssistFailureMetadata = (
  error: unknown,
  requestedProvider?: string,
  requestedModel?: string,
): Record<string, unknown> => {
  const detail = getDegradedResponseMessage(error);
  const failureCategory = getFailureCategory(error);

  const rawRequestedProvider = cleanString(requestedProvider);
  const normalizedRequestedProvider =
    normalizeProviderName(rawRequestedProvider) || rawRequestedProvider || '';

  const rawRequestedModel = cleanString(requestedModel);

  const metadata: Record<string, unknown> = {
    degraded_mode: true,
    degradation_reason: 'assist_request_failed',
    failure_category: failureCategory,
    response_source: 'assist_request_error',
    actual_provider: REQUEST_FAILURE_PROVIDER,
    actual_model: REQUEST_FAILURE_MODEL,
    runtime_engine: 'none',
    fallback_level: 'error',
    requested_provider: normalizedRequestedProvider || undefined,
    requested_model: rawRequestedModel || undefined,
    provider_error: {
      name: getErrorName(error),
      message: getErrorMessage(error),
      category: failureCategory,
    },
    orchestrator: {
      used_fallback: false,
      fallback_level: 'error',
      failure_reason: detail,
    },
    llm: {
      provider: REQUEST_FAILURE_PROVIDER,
      model_id: REQUEST_FAILURE_MODEL,
      model_name: REQUEST_FAILURE_MODEL,
      requested_provider: normalizedRequestedProvider || undefined,
      requested_model: rawRequestedModel || undefined,
      actual_provider: REQUEST_FAILURE_PROVIDER,
      actual_model: REQUEST_FAILURE_MODEL,
      runtime_engine: 'none',
      is_degraded: true,
      source: 'assist_request_error',
      response_source: 'assist_request_error',
      fallback_level: 'error',
      failure_reason: detail,
      routing_rationale: getRoutingRationale(
        normalizedRequestedProvider || rawRequestedProvider,
        rawRequestedModel,
      ),
    },
  };

  if (error instanceof ApiError) {
    metadata.http_status = error.status;
    metadata.error_details = error.details;
  }

  return metadata;
};