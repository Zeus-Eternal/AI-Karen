import { NextRequest, NextResponse } from 'next/server';

import { getBackendCandidates, withBackendPath } from '@/app/api/_utils/backend';
import { logger } from '@/lib/logger';

const API_PATH = '/api/system/config/models';
const REQUEST_TIMEOUT_MS = 15000;
const RETRYABLE_STATUS = new Set([500, 502, 503, 504]);
const ALLOWED_FIELDS = [
  'defaultModel',
  'fallbackModel',
  'autoSelectEnabled',
  'preferLocalModels',
  'allowedProviders',
  'maxConcurrentModels',
  'modelSelectionTimeout',
  'enableModelCaching',
  'cacheExpirationTime',
] as const;

type AllowedField = (typeof ALLOWED_FIELDS)[number];

type SanitizedPayload = Partial<Record<AllowedField, unknown>>;

type BackendResult = {
  response: Response;
  url: string;
};

function buildForwardHeaders(
  request: NextRequest,
  overrides: Record<string, string> = {},
): Record<string, string> {
  const headers: Record<string, string> = {
    Accept: 'application/json',
    ...overrides,
  };

  const authorization = request.headers.get('authorization');
  const cookie = request.headers.get('cookie');
  const requestId = request.headers.get('x-request-id');

  if (authorization) {
    headers.Authorization = authorization;
  }

  if (cookie) {
    headers.Cookie = cookie;
  }

  if (requestId) {
    headers['X-Request-ID'] = requestId;
  }

  return headers;
}

function sanitizePayload(body: unknown): SanitizedPayload {
  if (!body || typeof body !== 'object') {
    return {};
  }

  const payload: SanitizedPayload = {};

  for (const field of ALLOWED_FIELDS) {
    const value = (body as Record<string, unknown>)[field];

    if (value === undefined || value === null) {
      continue;
    }

    if (field === 'allowedProviders' && Array.isArray(value)) {
      const providers = value
        .map((provider) =>
          typeof provider === 'string' ? provider.trim() : String(provider),
        )
        .filter((provider) => provider.length > 0);

      if (providers.length > 0) {
        payload.allowedProviders = Array.from(new Set(providers));
      }
      continue;
    }

    if (typeof value === 'number') {
      if (Number.isFinite(value)) {
        payload[field] = value;
      }
      continue;
    }

    if (typeof value === 'boolean') {
      payload[field] = value;
      continue;
    }

    if (typeof value === 'string') {
      const trimmed = value.trim();
      if (trimmed) {
        payload[field] = trimmed;
      }
      continue;
    }

    payload[field] = value;
  }

  return payload;
}

async function parseResponseBody(response: Response): Promise<unknown> {
  const raw = await response.text();

  if (!raw) {
    return {};
  }

  try {
    return JSON.parse(raw);
  } catch (error) {
    logger.warn('Received non-JSON payload from system configuration API', {
      status: response.status,
      error: error instanceof Error ? error.message : String(error),

    return { message: raw };
  }
}

async function forwardToBackend(
  request: NextRequest,
  init: RequestInit,
): Promise<BackendResult> {
  const candidates = getBackendCandidates();
  const attempts: Array<{ url: string; error: string }> = [];
  let lastResponse: BackendResult | null = null;

  for (const base of candidates) {
    const url = withBackendPath(API_PATH, base);
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

    try {
      const response = await fetch(url, {
        ...init,
        signal: controller.signal,

      clearTimeout(timeout);

      if (RETRYABLE_STATUS.has(response.status)) {
        attempts.push({ url, error: `HTTP ${response.status}` });
        lastResponse = { response, url };
        continue;
      }

      return { response, url };
    } catch (error) {
      clearTimeout(timeout);
      const message = error instanceof Error ? error.message : String(error);
      attempts.push({ url, error: message });
      logger.warn('System configuration backend request failed', {
        url,
        message,

    }
  }

  if (lastResponse) {
    logger.warn('All backend candidates returned server errors', {
      attempts,

    return lastResponse;
  }

  const failureDetails = attempts.map((attempt) => `${attempt.url}: ${attempt.error}`);
  throw new Error(
    failureDetails.length > 0
      ? `All backend candidates failed: ${failureDetails.join('; ')}`
      : 'No backend candidates available for system configuration',
  );
}

export async function GET(request: NextRequest) {
  try {
    const { response, url } = await forwardToBackend(request, {
      method: 'GET',
      headers: buildForwardHeaders(request),

    const payload = await parseResponseBody(response);

    logger.info('System model configuration retrieved', {
      url,
      status: response.status,

    return NextResponse.json(payload ?? {}, {
      status: response.status,
      headers: {
        'Cache-Control': response.ok ? 'private, max-age=30' : 'no-store',
      },

  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    logger.error('Unable to retrieve system configuration from backend', {
      message,

    return NextResponse.json(
      {
        error: 'System configuration unavailable',
        message:
          'Kari could not reach the orchestration backend for system model configuration. Verify the API is healthy and reachable.',
      },
      { status: 503 },
    );
  }
}

export async function PUT(request: NextRequest) {
  try {
    let body: unknown = {};

    try {
      body = await request.json();
    } catch (error) {
      logger.warn('System configuration update received malformed JSON', {
        error: error instanceof Error ? error.message : String(error),

    }

    const payload = sanitizePayload(body);

    const { response, url } = await forwardToBackend(request, {
      method: 'PUT',
      headers: buildForwardHeaders(request, {
        'Content-Type': 'application/json',
      }),
      body: JSON.stringify(payload),

    const responseBody = await parseResponseBody(response);

    logger.info('System model configuration updated', {
      url,
      status: response.status,

    return NextResponse.json(responseBody ?? { success: response.ok }, {
      status: response.status,
      headers: {
        'Cache-Control': 'no-store',
      },

  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    logger.error('Failed to update system configuration', { message });

    return NextResponse.json(
      {
        error: 'Failed to update system configuration',
        message:
          'The Kari backend rejected the configuration update. Review the supplied fields and ensure the backend is reachable.',
      },
      { status: 502 },
    );
  }
}
