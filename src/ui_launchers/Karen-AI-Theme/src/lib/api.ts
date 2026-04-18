"use client";

// API service for HTTP requests
const SAME_ORIGIN_API_BASE_URL = '';

export class ApiError extends Error {
  status: number;
  details?: unknown;

  constructor(status: number, message: string, details?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

export interface StreamEvent {
  type: 'status' | 'content' | 'error' | 'complete';
  content: string;
  correlation_id: string;
  metadata?: Record<string, unknown>;
}

export interface StreamingMetrics {
  startTime: number;
  chunksReceived: number;
  totalBytes: number;
  lastChunkTime: number;
  connectionHealth: 'excellent' | 'good' | 'poor' | 'critical';
}

export interface AssistStreamCallbacks {
  onStatus?: (message: string, metadata?: Record<string, unknown>) => void;
  onContent?: (token: string) => void;
  onError?: (message: string) => void;
  onComplete?: (metadata?: Record<string, unknown>, content?: string) => void;
  onDone?: () => void;
  onMetrics?: (metrics: StreamingMetrics) => void;
}

class ApiClient {
  private readonly SESSION_MARKER_KEY = 'kari_session_expected';

  private formatApiErrorMessage(payload: unknown, fallback: string): string {
    if (typeof payload === 'string') {
      const trimmed = payload.trim();
      return trimmed || fallback;
    }

    if (payload && typeof payload === 'object') {
      const record = payload as Record<string, unknown>;
      const preferredKeys = ['user_message', 'message', 'detail', 'error'];

      for (const key of preferredKeys) {
        const value = record[key];
        if (typeof value === 'string' && value.trim()) {
          return value.trim();
        }
      }

      try {
        return JSON.stringify(payload);
      } catch {
        return fallback;
      }
    }

    if (payload == null) {
      return fallback;
    }

    return String(payload);
  }

  private async sleep(ms: number): Promise<void> {
    await new Promise((resolve) => setTimeout(resolve, ms));
  }

  private async retryWithExponentialBackoff<T>(
    operation: () => Promise<T>,
    maxRetries: number = 3,
    baseDelay: number = 1000,
    shouldRetry: (error: unknown) => boolean
  ): Promise<T> {
    let lastError: unknown;
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await operation();
      } catch (error) {
        lastError = error;
        if (attempt < maxRetries && shouldRetry(error)) {
          const delay = baseDelay * Math.pow(2, attempt);
          console.log(`[ApiClient] Retrying after ${delay}ms (attempt ${attempt + 1}/${maxRetries + 1})`);
          await this.sleep(delay);
        } else {
          throw error;
        }
      }
    }
    throw lastError;
  }

  private isBrowser(): boolean {
    return typeof window !== 'undefined' && (!!window.document || !!window.navigator);
  }

  private forceBrowserRelativeApiUrl(url: string): string {
    if (!this.isBrowser()) {
      return url;
    }

    if (url.startsWith('/')) {
      return url;
    }

    // Handle protocol-relative URLs (//api:8000/api/auth/me)
    if (url.startsWith('//')) {
      const apiIndex = url.indexOf('/api/');
      if (apiIndex >= 0) {
        return url.slice(apiIndex);
      }
      return url;
    }

    try {
      const parsed = new URL(url, window.location.origin);
      return `${parsed.pathname}${parsed.search}${parsed.hash}`;
    } catch {
      const apiIndex = url.indexOf('/api/');
      if (apiIndex >= 0) {
        return url.slice(apiIndex);
      }
      return url;
    }
  }

  /**
   * Determine the preferred base URL.
   * In a browser context, we return an empty string to force relative paths
   * which are then handled by the Next.js local proxy.
   */
  private getPreferredBaseUrl(): string {
    if (this.isBrowser()) {
      const env = (process as unknown as { env?: Record<string, string> }).env || {};
      console.log('[ApiClient] Browser context, forcing relative URLs');
      return '';
    }

    // Server-side only
    const env = (process as unknown as { env?: Record<string, string> }).env || {};
    if (env.KAREN_DOCKER === 'true' || env.KARI_DOCKER === 'true' || 
        env.HOSTNAME?.includes('api') || env.HOSTNAME?.includes('web')) {
      return 'http://api:8000';
    }
    
    return (env.KAREN_BACKEND_URL || env.NEXT_PUBLIC_API_BASE_URL || env.API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');
  }

  private getFallbackBaseUrl(preferredBaseUrl: string): string | null {
    if (this.isBrowser()) {
      return null;
    }

    const env = (process as unknown as { env?: Record<string, string> }).env || {};
    const configuredBackendUrl = (env.KAREN_BACKEND_URL || env.NEXT_PUBLIC_API_BASE_URL || '').replace(/\/$/, '');
    
    if (preferredBaseUrl === SAME_ORIGIN_API_BASE_URL) {
      return configuredBackendUrl || null;
    }
    
    return SAME_ORIGIN_API_BASE_URL || null;
  }

  private hasFallbackBaseUrl(baseUrl: string | null): baseUrl is string {
    return baseUrl !== null && baseUrl !== '';
  }

  /**
   * Build the final URL, ensuring that Docker-internal hostnames are stripped
   * when running in a browser context to avoid ERR_NAME_NOT_RESOLVED.
   */
  private buildUrl(baseUrl: string | null, endpoint: string): string {
    const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    
    // Aggressive browser-side URL hardening
    if (this.isBrowser()) {
      const dockerHostPattern = /https?:\/\/(api|api-copilot|172\.\d+\.\d+\.\d+|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|localhost:8000|host\.docker\.internal)(:\d+)?/gi;
      
      let finalUrl = baseUrl ? `${baseUrl}${normalizedEndpoint}` : normalizedEndpoint;
      console.log(`[ApiClient] buildUrl - Base: ${baseUrl}, Endpoint: ${endpoint}, Initial: ${finalUrl}`);
      
      // If it's an absolute URL pointing to internal Docker hosts, strip it
      if (finalUrl.startsWith('http')) {
        finalUrl = finalUrl.replace(dockerHostPattern, '');
        console.log(`[ApiClient] buildUrl - After stripping Docker hosts: ${finalUrl}`);
      }
      
      // If we are in the browser and the URL is still absolute to 'api', force it to relative
      if (finalUrl.includes('://api')) {
         finalUrl = finalUrl.substring(finalUrl.indexOf('/api/'));
         console.log(`[ApiClient] buildUrl - After forcing relative API path: ${finalUrl}`);
      }

      // Ensure it starts with /api if it's a relative path to our backend
      if (!finalUrl.startsWith('http') && !finalUrl.startsWith('/')) {
        finalUrl = '/' + finalUrl;
        console.log(`[ApiClient] buildUrl - After ensuring leading slash: ${finalUrl}`);
      }
      
      return finalUrl;
    }

    // Server-side logic
    if (endpoint.startsWith('http://') || endpoint.startsWith('https://')) {
      return endpoint;
    }

    return `${baseUrl || ''}${normalizedEndpoint}`;
  }

  private shouldRetryWithSameOrigin(error: unknown): boolean {
    return this.isBrowser() && error instanceof TypeError;
  }

  private shouldRetryWithDirectBackend(response: Response, fallbackBaseUrl: string | null): boolean {
    return (
      this.isBrowser() &&
      this.hasFallbackBaseUrl(fallbackBaseUrl) &&
      response.status >= 500
    );
  }

  private shouldRetryMissingApiRoute(endpoint: string, response: Response, fallbackBaseUrl: string | null): boolean {
    return (
      this.isBrowser() &&
      this.hasFallbackBaseUrl(fallbackBaseUrl) &&
      endpoint.startsWith('/api/') &&
      response.status === 404
    );
  }

  private shouldRetryAssistServerError(endpoint: string, response: Response): boolean {
    return (
      this.isBrowser() &&
      endpoint === '/api/copilot/assist' &&
      response.status >= 500
    );
  }

  private hasSessionMarker(): boolean {
    if (typeof window === 'undefined') return false;
    try {
      return localStorage.getItem(this.SESSION_MARKER_KEY) === 'true';
    } catch {
      return false;
    }
  }

  private shouldPreferCookieSession(): boolean {
    return this.isBrowser() && this.hasSessionMarker();
  }

  private async getAuthHeaders(): Promise<Record<string, string>> {
    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json'
      };

      const accessToken = localStorage.getItem('access_token');
      console.log('[ApiClient] getAuthHeaders called; token present:', !!accessToken);

      if (accessToken) {
        if (this.isTokenExpired(accessToken)) {
          console.log('[ApiClient] Access token expired, attempting refresh');
          try {
            await this.refreshAccessToken();
            const newToken = localStorage.getItem('access_token');
            if (newToken) headers['Authorization'] = `Bearer ${newToken}`;
          } catch {
            console.warn('Failed to refresh token, using existing token for this request');
            // Do not silently drop auth headers on refresh failure; let backend
            // return an explicit 401 and keep client auth state intact.
            headers['Authorization'] = `Bearer ${accessToken}`;
          }
        } else {
          console.log('[ApiClient] Using access token for Authorization header');
          headers['Authorization'] = `Bearer ${accessToken}`;
        }
      } else {
        console.log('[ApiClient] No access token available; relying on cookie session if present');
      }
      return headers;
    } catch {
      return { 'Content-Type': 'application/json' };
    }
  }

  private isTokenExpired(token: string): boolean {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.exp < Date.now() / 1000;
    } catch {
      return true;
    }
  }

  private async refreshAccessToken(): Promise<void> {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) throw new Error('No refresh token available');

      const sendRefresh = async (baseUrl: string | null): Promise<Response> =>
        fetch(this.buildUrl(baseUrl, '/api/auth/refresh'), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ refresh_token: refreshToken }),
        });

      const preferredBaseUrl = this.getPreferredBaseUrl();
      const fallbackBaseUrl = this.getFallbackBaseUrl(preferredBaseUrl);

      let response: Response;
      try {
        response = await sendRefresh(preferredBaseUrl);
      } catch (error) {
        if (!this.shouldRetryWithSameOrigin(error) || !fallbackBaseUrl) throw error;
        response = await sendRefresh(fallbackBaseUrl);
      }

      if (!response.ok) throw new Error('Token refresh failed');
      const data = await response.json();
      localStorage.setItem('access_token', data.access_token);
    } catch (error) {
      // Do not clear auth state here; callers decide how to handle 401.
      // This prevents accidental hard logout during transient refresh issues.
      throw error;
    }
  }

  private async request<T>(endpoint: string, init: RequestInit = {}, skipAuth: boolean = false): Promise<T> {
    const send = async (baseUrl: string | null): Promise<Response> => {
      const authHeaders = skipAuth ? {} : await this.getAuthHeaders();
      const requestHeaders = {
        ...authHeaders,
        ...((init.headers as Record<string, string> | undefined) || {}),
      };

      const url = this.forceBrowserRelativeApiUrl(this.buildUrl(baseUrl, endpoint));
      console.log(`[ApiClient] Request: ${url} (Base: ${baseUrl}, Endpoint: ${endpoint})`);
      
      try {
        return await fetch(url, {
          ...init,
          headers: requestHeaders,
          credentials: 'include',
        });
      } catch (err) {
        console.error(`[ApiClient] Network error for ${url}:`, err);
        throw err;
      }
    };

    const preferredBaseUrl = this.getPreferredBaseUrl();
    const fallbackBaseUrl: string | null = this.getFallbackBaseUrl(preferredBaseUrl) || null;

    let response: Response;
    try {
      response = await send(preferredBaseUrl);
    } catch (error) {
      if (!this.shouldRetryWithSameOrigin(error) || !this.hasFallbackBaseUrl(fallbackBaseUrl)) throw error;
      response = await send(fallbackBaseUrl);
    }

    // Logic for retries (500s or 404s on API routes)
    if (this.shouldRetryWithDirectBackend(response, fallbackBaseUrl) ||
        this.shouldRetryMissingApiRoute(endpoint, response, fallbackBaseUrl)) {
      response = await send(fallbackBaseUrl);
    }

    // 401 Handling
    if (response.status === 401) {
      try {
        await this.refreshAccessToken();
        response = await send(preferredBaseUrl);
        if (this.shouldRetryWithDirectBackend(response, fallbackBaseUrl) ||
            this.shouldRetryMissingApiRoute(endpoint, response, fallbackBaseUrl)) {
          response = await send(fallbackBaseUrl);
        }
      } catch {}
    }

    // 500 Retry for Copilot Assist
    if (!response.ok && this.shouldRetryAssistServerError(endpoint, response)) {
      await this.sleep(250);
      response = await send(preferredBaseUrl);
    }

    // 502 Retry with backoff for startup timing issues
    if (response.status === 502) {
      console.log('[ApiClient] 502 Bad Gateway detected, retrying with backoff for startup timing');
      await this.sleep(2000); // Wait 2s before retry
      try {
        response = await send(preferredBaseUrl);
        if (this.shouldRetryWithDirectBackend(response, fallbackBaseUrl) ||
            this.shouldRetryMissingApiRoute(endpoint, response, fallbackBaseUrl)) {
          response = await send(fallbackBaseUrl);
        }
      } catch (retryError) {
        console.warn('[ApiClient] Retry after 502 failed:', retryError);
        // Continue with original 502 response for error handling
      }
    }

    if (!response.ok) {
      const rawText = await response.text().catch(() => '');
      let errorData: Record<string, unknown> = {};
      try {
        errorData = JSON.parse(rawText);
      } catch {
        errorData = { detail: rawText.trim() };
      }
      const fallbackMessage = `HTTP ${response.status}: ${response.statusText}`;
      const errorPayload = errorData.detail ?? errorData.message ?? errorData.error ?? rawText;

      // Handle 401 errors by redirecting to login
      if (response.status === 401 && typeof window !== 'undefined') {
        console.warn('[ApiClient] Authentication failed, redirecting to login');
        // Clear any remaining auth data
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_data');
        // Redirect to login page
        window.location.href = '/login';
        // Don't throw error, let the redirect happen
        return undefined as T;
      }

      // Provide user-friendly message for 502 Bad Gateway (startup timing)
      const errorMessage = response.status === 502
        ? 'The backend service is starting up. Please wait a moment and try again.'
        : this.formatApiErrorMessage(errorPayload, fallbackMessage);

      throw new ApiError(
        response.status,
        errorMessage,
        errorData,
      );
    }

    if (response.status === 204) return undefined as T;
    const text = await response.text();
    return (text ? JSON.parse(text) : undefined) as T;
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint);
  }

  async getUnauthenticated<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, {}, true);
  }

  async post<T>(endpoint: string, data?: unknown, init: RequestInit = {}): Promise<T> {
    return this.request<T>(endpoint, {
      ...init,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined
    });
  }

  async put<T>(endpoint: string, data?: unknown, init: RequestInit = {}): Promise<T> {
    return this.request<T>(endpoint, {
      ...init,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'DELETE',
    });
  }

  async postStream(
    endpoint: string,
    data?: unknown,
    callbacks?: AssistStreamCallbacks,
    signal?: AbortSignal,
  ): Promise<void> {
    const preferredBaseUrl = this.getPreferredBaseUrl();
    const url = this.forceBrowserRelativeApiUrl(this.buildUrl(preferredBaseUrl, endpoint));

    // Streaming configuration
    // Local runtimes (ollama/llama.cpp) can take a while to emit first tokens.
    const STREAMING_TIMEOUT = 300000; // 5 minutes total
    const FIRST_CONTENT_TIMEOUT = 360000; // 6 minutes for model warmup/status-only phases
    const CHUNK_TIMEOUT = 120000; // 120 seconds between content chunks once content starts
    let timeoutId: NodeJS.Timeout;
    let heartbeatId: NodeJS.Timeout;
    let lastChunkTime = Date.now();
    let lastContentChunkTime = Date.now();
    let collectedContent = '';
    let chunksReceived = 0;
    let contentChunksReceived = 0;
    let statusEventsReceived = 0;
    let lastStatusEventTime = Date.now();
    let totalBytes = 0;
    let streamAbortReason: string | null = null;
    const streamController = new AbortController();
    let externalAbortListener: (() => void) | null = null;

    if (signal) {
      if (signal.aborted) {
        streamController.abort();
      } else {
        externalAbortListener = () => streamController.abort();
        signal.addEventListener('abort', externalAbortListener, { once: true });
      }
    }

    const abortStreamWithReason = (reason: string) => {
      if (!streamAbortReason) {
        streamAbortReason = reason;
        callbacks?.onError?.(reason);
      }
      if (!streamController.signal.aborted) {
        streamController.abort();
      }
    };

    // Initialize metrics
    const startTime = Date.now();
    const metrics: StreamingMetrics = {
      startTime,
      chunksReceived: 0,
      totalBytes: 0,
      lastChunkTime: startTime,
      connectionHealth: 'excellent',
    };

    const updateMetrics = () => {
      const now = Date.now();
      const timeSinceLastChunk = now - lastChunkTime;
      
      // Update connection health based on chunk reception
      if (timeSinceLastChunk > CHUNK_TIMEOUT * 2) {
        metrics.connectionHealth = 'critical';
      } else if (timeSinceLastChunk > CHUNK_TIMEOUT) {
        metrics.connectionHealth = 'poor';
      } else if (timeSinceLastChunk > CHUNK_TIMEOUT / 2) {
        metrics.connectionHealth = 'good';
      } else {
        metrics.connectionHealth = 'excellent';
      }
      
      metrics.lastChunkTime = now;
      callbacks?.onMetrics?.(metrics);
    };

    const setupTimeouts = () => {
      timeoutId = setTimeout(() => {
        cleanup();
        abortStreamWithReason('Stream timeout - total session exceeded limit');
      }, STREAMING_TIMEOUT);

      heartbeatId = setInterval(() => {
        const now = Date.now();

        // Warmup guard:
        // 1) If there are no status or content events for too long, abort.
        // 2) If status events are arriving, allow longer warmup and only abort on silence.
        if (contentChunksReceived === 0) {
          const warmupExceeded = now - startTime > FIRST_CONTENT_TIMEOUT;
          if (warmupExceeded && statusEventsReceived === 0) {
            cleanup();
            abortStreamWithReason('Stream warmup timeout - no stream progress received');
            return;
          }

          if (statusEventsReceived > 0 && now - lastStatusEventTime > CHUNK_TIMEOUT) {
            cleanup();
            abortStreamWithReason('Stream stalled during warmup - no status updates received');
            return;
          }
        }

        // Stall guard: once content starts, enforce no-content-chunk timeout.
        if (contentChunksReceived > 0 && now - lastContentChunkTime > CHUNK_TIMEOUT) {
          cleanup();
          abortStreamWithReason('Stream stalled - no content chunks received');
        }
      }, 1000);
    };

    const cleanup = () => {
      clearTimeout(timeoutId);
      clearInterval(heartbeatId);
      if (signal && externalAbortListener) {
        signal.removeEventListener('abort', externalAbortListener);
        externalAbortListener = null;
      }
    };

    const sendStreamRequest = async (): Promise<Response> => {
      const authHeaders = await this.getAuthHeaders();
      return fetch(url, {
        method: 'POST',
        headers: {
          ...authHeaders,
          'Accept': 'text/event-stream',
          'Cache-Control': 'no-cache',
        },
        credentials: 'include',
        body: data ? JSON.stringify(data) : undefined,
        signal: streamController.signal,
      });
    };

    let response = await sendStreamRequest();
    if (response.status === 401) {
      try {
        await this.refreshAccessToken();
        response = await sendStreamRequest();
      } catch {
        // Keep original 401 response path below.
      }
    }

    if (!response.ok) {
      cleanup();
      const rawText = await response.text().catch(() => '');
      let errorData: Record<string, unknown> = {};
      try {
        errorData = JSON.parse(rawText);
      } catch {
        errorData = { detail: rawText.trim() };
      }
      throw new ApiError(
        response.status,
        this.formatApiErrorMessage(errorData, `HTTP ${response.status}: ${response.statusText}`),
        errorData,
      );
    }

    const reader = response.body?.getReader();
    if (!reader) {
      cleanup();
      throw new ApiError(0, 'No readable stream available');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    setupTimeouts();

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        lastChunkTime = Date.now();
        chunksReceived++;
        totalBytes += value?.length || 0;
        
        // Update metrics
        metrics.chunksReceived = chunksReceived;
        metrics.totalBytes = totalBytes;
        updateMetrics();

        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed || !trimmed.startsWith('data: ')) continue;

          const payload = trimmed.slice(6);
          if (payload === '[DONE]') {
            cleanup();
            callbacks?.onDone?.();
            return;
          }

          let parsed: StreamEvent;
          try {
            parsed = JSON.parse(payload);
          } catch {
            continue;
          }

          switch (parsed.type) {
            case 'status':
              statusEventsReceived++;
              lastStatusEventTime = Date.now();
              callbacks?.onStatus?.(parsed.content, parsed.metadata);
              break;
            case 'content':
              collectedContent += parsed.content;
              lastContentChunkTime = Date.now();
              contentChunksReceived++;
              // Prevent memory bloat with reasonable limits
              if (collectedContent.length > 100000) { // 100k chars
                collectedContent = collectedContent.slice(-50000); // Keep last 50k
              }
              callbacks?.onContent?.(parsed.content);
              break;
            case 'error':
              cleanup();
              callbacks?.onError?.(parsed.content);
              return;
            case 'complete':
              cleanup();
              callbacks?.onComplete?.(parsed.metadata, parsed.content);
              return;
          }
        }
      }
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError' && streamAbortReason) {
        // Timeout/stall aborts are surfaced via onError callback above.
        return;
      }
      throw error;
    } finally {
      cleanup();
      reader.releaseLock();
    }
  }

  /**
   * Check if the backend is healthy and ready to accept requests.
   * Useful for handling startup timing issues.
   */
  async healthCheck(): Promise<boolean> {
    try {
      await this.getUnauthenticated('/api/health');
      return true;
    } catch {
      return false;
    }
  }
}

export const apiClient = new ApiClient();
export default apiClient;
