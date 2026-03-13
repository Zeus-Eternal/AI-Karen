/**
 * Conversation processing proxy route.
 * Validates and sanitizes input, forwards to backend with retries, timeouts, and fallback URLs.
 */

import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { randomUUID } from 'crypto';

export const runtime = 'nodejs';

const HistoryItemSchema = z.object({
  role: z.enum(['user', 'assistant', 'system']),
  content: z.string().min(1).max(4000),
  timestamp: z.string().optional()
});

const RequestSchema = z.object({
  message: z.string().min(1).max(4000),
  conversationHistory: z.array(HistoryItemSchema).max(50).optional().default([]),
  settings: z.object({
    personalityTone: z.enum(['friendly', 'professional', 'casual']).optional(),
    personalityVerbosity: z.enum(['concise', 'balanced', 'detailed']).optional(),
    memoryDepth: z.enum(['minimal', 'medium', 'comprehensive']).optional(),
  }).optional(),
  sessionId: z.string().optional()
});

const CONTROL_CHARS = /[\u0000-\u001F\u007F]/g;
const DISALLOWED_PATTERNS = [
  /<script/i,
  /javascript:/i,
  /onerror\s*=/i,
  /onload\s*=/i
];

const RETRYABLE_STATUS = new Set([408, 425, 429, 500, 502, 503, 504]);

const DEFAULT_TIMEOUT_MS = parseInt(process.env.KAREN_API_TIMEOUT_MS || '30000', 10);
const DEFAULT_RETRIES = parseInt(process.env.KAREN_API_RETRIES || '2', 10);
const DEFAULT_BACKOFF_BASE_MS = parseInt(process.env.KAREN_API_RETRY_BASE_MS || '400', 10);
const DEFAULT_BACKOFF_MAX_MS = parseInt(process.env.KAREN_API_RETRY_MAX_MS || '4000', 10);

const PRIMARY_BACKEND_URL = process.env.KAREN_BACKEND_URL
  || process.env.NEXT_PUBLIC_KAREN_BACKEND_URL
  || 'http://localhost:8000';

const FALLBACK_URLS = (process.env.KAREN_FALLBACK_BACKEND_URLS || '')
  .split(',')
  .map((value) => value.trim())
  .filter(Boolean);

const BACKEND_API_KEY = process.env.KAREN_BACKEND_API_KEY || process.env.KAREN_API_KEY;

type BackendResponse = {
  response?: string;
  finalResponse?: string;
  message?: string;
  confidence_score?: number;
  ai_data?: {
    confidence?: number;
    intent?: string;
    model?: string;
  };
  model_used?: string;
  metadata?: Record<string, unknown>;
};

type ProxyResponse = {
  success: boolean;
  message?: string;
  error?: string;
  code?: string;
  requestId: string;
  metadata?: Record<string, unknown>;
  fallbackUsed?: boolean;
  attempts?: number;
};

const sanitizeText = (value: string) => value.replace(CONTROL_CHARS, '').trim();

const validateText = (value: string) => {
  for (const pattern of DISALLOWED_PATTERNS) {
    if (pattern.test(value)) {
      return false;
    }
  }
  return true;
};

const normalizeBaseUrl = (value: string) => {
  const trimmed = value.replace(/\/+$/, '');
  return trimmed.endsWith('/api') ? trimmed : `${trimmed}/api`;
};

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

const getRetryDelay = (attempt: number) => {
  const baseDelay = Math.min(DEFAULT_BACKOFF_MAX_MS, DEFAULT_BACKOFF_BASE_MS * (2 ** attempt));
  const jitter = Math.floor(Math.random() * 100);
  return baseDelay + jitter;
};

const parseRetryAfter = (value: string | null) => {
  if (!value) return null;
  const seconds = Number(value);
  if (!Number.isNaN(seconds)) {
    return Math.min(DEFAULT_BACKOFF_MAX_MS, seconds * 1000);
  }
  const date = Date.parse(value);
  if (!Number.isNaN(date)) {
    return Math.max(0, Math.min(DEFAULT_BACKOFF_MAX_MS, date - Date.now()));
  }
  return null;
};

const parseResponseBody = (text: string): BackendResponse | { raw: string } | null => {
  if (!text) return null;
  try {
    return JSON.parse(text) as BackendResponse;
  } catch {
    return { raw: text };
  }
};

const buildHeaders = (requestId: string) => {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'X-Request-Id': requestId,
  };
  if (BACKEND_API_KEY) {
    headers.Authorization = `Bearer ${BACKEND_API_KEY}`;
  }
  return headers;
};

const isRetryableError = (error: unknown) => {
  return error instanceof TypeError || (error instanceof Error && error.name === 'AbortError');
};

const fetchWithRetry = async (
  url: string,
  body: Record<string, unknown>,
  requestId: string
) => {
  let lastError: Error | null = null;
  let attempt = 0;

  for (attempt = 0; attempt <= DEFAULT_RETRIES; attempt += 1) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: buildHeaders(requestId),
        body: JSON.stringify(body),
        signal: controller.signal,
      });

      const text = await response.text();
      const data = parseResponseBody(text);

      if (response.ok) {
        return { response, data, attempts: attempt + 1 };
      }

      const retryAfter = parseRetryAfter(response.headers.get('retry-after'));
      const retryDelay = retryAfter ?? getRetryDelay(attempt);

      if (RETRYABLE_STATUS.has(response.status) && attempt < DEFAULT_RETRIES) {
        await sleep(retryDelay);
        continue;
      }

      const errorMessage = typeof (data as BackendResponse | null)?.message === 'string'
        ? (data as BackendResponse).message
        : typeof (data as BackendResponse | null)?.response === 'string'
          ? (data as BackendResponse).response
          : (data && 'raw' in data ? data.raw : response.statusText);

      const error = new Error(errorMessage || 'Upstream request failed');
      (error as any).status = response.status;
      (error as any).data = data;
      throw error;
    } catch (error) {
      lastError = error as Error;

      if (attempt >= DEFAULT_RETRIES || !isRetryableError(error)) {
        throw lastError;
      }

      await sleep(getRetryDelay(attempt));
    } finally {
      clearTimeout(timeoutId);
    }
  }

  throw lastError || new Error('Upstream request failed');
};

export async function POST(request: NextRequest) {
  const requestId = request.headers.get('x-request-id') || randomUUID();

  let payload: z.infer<typeof RequestSchema> | null = null;
  try {
    const body = await request.json();
    const parsed = RequestSchema.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json<ProxyResponse>({
        success: false,
        error: 'Invalid request payload',
        code: 'INVALID_REQUEST',
        requestId,
      }, { status: 400 });
    }
    payload = parsed.data;
  } catch {
    return NextResponse.json<ProxyResponse>({
      success: false,
      error: 'Malformed JSON payload',
      code: 'INVALID_JSON',
      requestId,
    }, { status: 400 });
  }

  if (!payload) {
    return NextResponse.json<ProxyResponse>({
      success: false,
      error: 'Request payload missing',
      code: 'INVALID_REQUEST',
      requestId,
    }, { status: 400 });
  }

  const sanitizedMessage = sanitizeText(payload.message);
  if (!sanitizedMessage || !validateText(sanitizedMessage)) {
    return NextResponse.json<ProxyResponse>({
      success: false,
      error: 'Message content failed validation checks',
      code: 'INVALID_MESSAGE',
      requestId,
    }, { status: 400 });
  }

  const sanitizedHistory = payload.conversationHistory.map((entry) => ({
    role: entry.role,
    content: sanitizeText(entry.content),
    timestamp: entry.timestamp,
  })).filter((entry) => entry.content.length > 0);

  const userSettings = {
    personality_tone: payload.settings?.personalityTone || 'friendly',
    personality_verbosity: payload.settings?.personalityVerbosity || 'balanced',
    memory_depth: payload.settings?.memoryDepth || 'medium',
  };

  const requestBody = {
    prompt: sanitizedMessage,
    conversation_history: sanitizedHistory,
    user_settings: userSettings,
    context: {
      ui_source: 'karen-theme-default',
      request_id: requestId,
    },
    session_id: payload.sessionId,
    include_memories: true,
    include_insights: true,
  };

  const backendUrls = [PRIMARY_BACKEND_URL, ...FALLBACK_URLS]
    .map(normalizeBaseUrl)
    .filter((value, index, self) => self.indexOf(value) === index);

  if (!backendUrls.length) {
    return NextResponse.json<ProxyResponse>({
      success: false,
      error: 'No backend endpoints configured',
      code: 'NO_BACKEND',
      requestId,
    }, { status: 500 });
  }

  let lastError: Error | null = null;
  for (const [index, baseUrl] of backendUrls.entries()) {
    // The backend router is mounted at /api/ai prefix, so we need to call /api/ai/conversation-processing
    // However, normalizeBaseUrl() already appends /api, so we just need /ai/conversation-processing
    const endpoint = `${baseUrl}/ai/conversation-processing`;
    try {
      const result = await fetchWithRetry(endpoint, requestBody, requestId);
      const data = result.data as BackendResponse | null;

      const message = data?.response || data?.finalResponse || data?.message || '';
      if (!message) {
        throw new Error('Upstream response missing content');
      }

      return NextResponse.json<ProxyResponse>({
        success: true,
        message,
        requestId,
        attempts: result.attempts,
        fallbackUsed: index > 0,
        metadata: {
          confidence: data?.confidence_score ?? data?.ai_data?.confidence,
          intent: data?.ai_data?.intent,
          model: data?.model_used ?? data?.ai_data?.model,
          backend: baseUrl,
        },
      }, {
        headers: {
          'X-Request-Id': requestId,
          'X-Backend-Url': baseUrl,
        },
      });
    } catch (error) {
      lastError = error as Error;
      const status = (error as any)?.status;
      if (typeof status === 'number' && !RETRYABLE_STATUS.has(status)) {
        break;
      }
    }
  }

  return NextResponse.json<ProxyResponse>({
    success: false,
    error: lastError?.message || 'Upstream service unavailable',
    code: 'UPSTREAM_ERROR',
    requestId,
  }, { status: 502 });
}
