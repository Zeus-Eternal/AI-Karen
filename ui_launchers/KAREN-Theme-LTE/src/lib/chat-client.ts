/**
 * Client-side chat transport with validation, retries, and timeouts.
 */

export type ChatHistoryEntry = {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
};

export type ChatClientRequest = {
  message: string;
  conversationHistory: ChatHistoryEntry[];
  settings?: {
    personalityTone?: 'friendly' | 'professional' | 'casual';
    personalityVerbosity?: 'concise' | 'balanced' | 'detailed';
    memoryDepth?: 'minimal' | 'medium' | 'comprehensive';
  };
  sessionId?: string;
};

export type ChatClientResponse = {
  message: string;
  requestId?: string;
  fallbackUsed?: boolean;
  metadata?: {
    confidence?: number;
    intent?: string;
    model?: string;
    backend?: string;
  };
};

type ChatProxyResponse = {
  success: boolean;
  message?: string;
  error?: string;
  code?: string;
  requestId?: string;
  metadata?: Record<string, unknown>;
  fallbackUsed?: boolean;
};

export class ChatClientError extends Error {
  status?: number;
  code?: string;
  retryable: boolean;
  data?: unknown;
  userMessage: string;

  constructor(message: string, options: {
    status?: number;
    code?: string;
    retryable?: boolean;
    data?: unknown;
    userMessage?: string;
  } = {}) {
    super(message);
    this.name = 'ChatClientError';
    this.status = options.status;
    this.code = options.code;
    this.retryable = options.retryable ?? false;
    this.data = options.data;
    this.userMessage = options.userMessage || message;
  }
}

const CONTROL_CHARS = /[\u0000-\u001F\u007F]/g;
const DISALLOWED_PATTERNS = [
  /<script/i,
  /javascript:/i,
  /onerror\s*=/i,
  /onload\s*=/i
];

const RETRYABLE_STATUS = new Set([408, 425, 429, 500, 502, 503, 504]);

const DEFAULT_TIMEOUT_MS = parseInt(process.env.NEXT_PUBLIC_CHAT_TIMEOUT_MS || '25000', 10);
const DEFAULT_RETRIES = parseInt(process.env.NEXT_PUBLIC_CHAT_RETRIES || '2', 10);
const DEFAULT_BACKOFF_BASE_MS = parseInt(process.env.NEXT_PUBLIC_CHAT_RETRY_BASE_MS || '350', 10);
const DEFAULT_BACKOFF_MAX_MS = parseInt(process.env.NEXT_PUBLIC_CHAT_RETRY_MAX_MS || '3500', 10);
const MAX_MESSAGE_LENGTH = parseInt(process.env.NEXT_PUBLIC_CHAT_MAX_MESSAGE_LENGTH || '4000', 10);

const sanitizeText = (value: string) => value.replace(CONTROL_CHARS, '').trim();

const validateText = (value: string) => {
  if (!value) {
    throw new ChatClientError('Message cannot be empty.', {
      code: 'EMPTY_MESSAGE',
      userMessage: 'Please enter a message before sending.',
    });
  }
  if (value.length > MAX_MESSAGE_LENGTH) {
    throw new ChatClientError('Message is too long.', {
      code: 'MESSAGE_TOO_LONG',
      userMessage: `Please keep messages under ${MAX_MESSAGE_LENGTH} characters.`,
    });
  }
  for (const pattern of DISALLOWED_PATTERNS) {
    if (pattern.test(value)) {
      throw new ChatClientError('Message failed security validation.', {
        code: 'MESSAGE_INVALID',
        userMessage: 'Your message contains unsupported content. Please rephrase and try again.',
      });
    }
  }
};

export const sanitizeChatInput = (value: string) => {
  const sanitized = sanitizeText(value);
  validateText(sanitized);
  return sanitized;
};

const sanitizeHistory = (history: ChatHistoryEntry[]) => {
  return history
    .map((entry) => ({
      role: entry.role,
      content: sanitizeText(entry.content),
      timestamp: entry.timestamp,
    }))
    .filter((entry) => entry.content.length > 0)
    .slice(-50);
};

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

const getRetryDelay = (attempt: number) => {
  const baseDelay = Math.min(DEFAULT_BACKOFF_MAX_MS, DEFAULT_BACKOFF_BASE_MS * (2 ** attempt));
  const jitter = Math.floor(Math.random() * 100);
  return baseDelay + jitter;
};

const parseResponse = (text: string) => {
  if (!text) return null;
  try {
    return JSON.parse(text) as ChatProxyResponse;
  } catch {
    return { success: false, error: text } satisfies ChatProxyResponse;
  }
};

const isRetryableError = (error: unknown) => {
  return error instanceof TypeError || (error instanceof Error && error.name === 'AbortError');
};

const fetchWithRetry = async (
  input: RequestInfo,
  init: RequestInit,
  options?: {
    timeoutMs?: number;
    retries?: number;
  }
) => {
  const timeoutMs = options?.timeoutMs ?? DEFAULT_TIMEOUT_MS;
  const retries = options?.retries ?? DEFAULT_RETRIES;

  let attempt = 0;
  let lastError: ChatClientError | null = null;

  for (attempt = 0; attempt <= retries; attempt += 1) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(input, { ...init, signal: controller.signal });
      const text = await response.text();
      const data = parseResponse(text);

      if (response.ok && data?.success !== false) {
        return { response, data, attempts: attempt + 1 };
      }

      const errorMessage = data?.error || data?.message || response.statusText || 'Request failed';
      const error = new ChatClientError(errorMessage, {
        status: response.status,
        code: data?.code,
        data,
        retryable: RETRYABLE_STATUS.has(response.status),
        userMessage: errorMessage || 'We could not reach the service. Please try again.',
      });

      lastError = error;
      if (!error.retryable || attempt >= retries) {
        throw error;
      }

      await sleep(getRetryDelay(attempt));
      continue;
    } catch (error) {
      const fallbackError = error instanceof ChatClientError
        ? error
        : new ChatClientError('Network error', {
          retryable: isRetryableError(error),
          userMessage: 'Network issue detected. Please check your connection and try again.',
        });

      lastError = fallbackError;
      if (!fallbackError.retryable || attempt >= retries) {
        throw fallbackError;
      }

      await sleep(getRetryDelay(attempt));
    } finally {
      clearTimeout(timeoutId);
    }
  }

  throw lastError || new ChatClientError('Request failed');
};

export const sendChatMessage = async (payload: ChatClientRequest) => {
  const sanitizedMessage = sanitizeChatInput(payload.message);

  const sanitizedHistory = sanitizeHistory(payload.conversationHistory);

  const requestBody = {
    message: sanitizedMessage,
    conversationHistory: sanitizedHistory,
    settings: payload.settings,
    sessionId: payload.sessionId,
  };

  const result = await fetchWithRetry('/api/ai/conversation-processing', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(requestBody),
  });

  const data = result.data as ChatProxyResponse | null;
  if (!data?.message) {
    throw new ChatClientError('Empty response from server', {
      code: 'EMPTY_RESPONSE',
      retryable: false,
      data,
      userMessage: 'The service returned an empty response. Please try again.',
    });
  }

  return {
    message: data.message,
    requestId: data.requestId,
    fallbackUsed: data.fallbackUsed,
    metadata: {
      confidence: data.metadata?.confidence as number | undefined,
      intent: data.metadata?.intent as string | undefined,
      model: data.metadata?.model as string | undefined,
      backend: data.metadata?.backend as string | undefined,
    },
  } satisfies ChatClientResponse;
};
