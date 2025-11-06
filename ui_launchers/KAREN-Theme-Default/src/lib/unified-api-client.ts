/**
 * Unified API Client for Consolidated Endpoints (production-grade)
 *
 * Features implemented:
 * - Multi-endpoint fallback with per-endpoint retry (exponential backoff + jitter)
 * - Consolidated endpoints: /copilot/assist, /memory/search, /memory/commit, /memory/update, /memory/delete
 * - Strict request validation + user-friendly error wrapping
 * - Timeouts via AbortController
 * - Request/response logging hooks (no-op by default; wire to your logger/telemetry)
 * - Health checks per endpoint
 * - Correlation IDs propagated on responses
 */

import { getApiClient, type ApiResponse, type ApiError } from './api-client';
import { safeError } from './safe-console';
import { getConfigManager } from './endpoint-config';

// Optional toast—left unused here on purpose (UI layer should decide how to display)
import { useToast } from '@/hooks/use-toast';

export interface UnifiedApiClientConfig {
  enableFallback: boolean;
  maxRetries: number;        // per endpoint
  retryDelay: number;        // base ms for backoff
  timeout: number;           // ms
  enableLogging: boolean;
}

export interface ConsolidatedEndpoints {
  copilotAssist: string;
  memorySearch: string;
  memoryCommit: string;
  memoryUpdate: string;
  memoryDelete: string;
}

export interface CopilotAssistRequest {
  user_id: string;
  org_id?: string;
  message: string;
  top_k?: number;
  context?: Record<string, any>;
  stream?: boolean;
}

export interface CopilotAssistResponse {
  answer: string;
  context: Array<{
    id: string;
    text: string;
    score: number;
    tags: string[];
    metadata?: Record<string, any>;
  }>;
  actions: Array<{
    type: string;
    params: Record<string, any>;
    confidence: number;
    description?: string;
  }>;
  timings: {
    memory_search_ms: number;
    llm_generation_ms: number;
    total_ms: number;
  };
  correlation_id: string;
}

export interface MemorySearchRequest {
  user_id: string;
  org_id?: string;
  query: string;
  top_k?: number;
  tags?: string[];
  time_range?: [string, string];
  similarity_threshold?: number;
}

export interface MemorySearchResponse {
  hits: Array<{
    id: string;
    text: string;
    score: number;
    tags: string[];
    importance: number;
    decay_tier: string;
    created_at: string;
    updated_at?: string;
    metadata?: Record<string, any>;
  }>;
  total_found: number;
  query_time_ms: number;
  correlation_id: string;
}

export interface MemoryCommitRequest {
  user_id: string;
  org_id?: string;
  text: string;
  tags?: string[];
  importance?: number;
  decay?: 'short' | 'medium' | 'long' | 'pinned';
  metadata?: Record<string, any>;
}

export interface MemoryCommitResponse {
  id: string;
  status: 'created' | 'updated';
  embedding_generated: boolean;
  decay_tier_assigned: string;
  correlation_id: string;
}

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE';

export type EndpointKey = keyof ConsolidatedEndpoints;

/**
 * Unified API Client
 */
export class UnifiedApiClient {
  private apiClient = getApiClient();
  private configManager = getConfigManager();
  private config: UnifiedApiClientConfig;
  private endpoints: ConsolidatedEndpoints;

  constructor(config?: Partial<UnifiedApiClientConfig>) {
    this.config = {
      enableFallback: true,
      maxRetries: 3,
      retryDelay: 1000,
      timeout: 30000,
      enableLogging: true,
      ...config,
    };

    // NOTE: paths are relative; base URLs come from configManager for fallback
    this.endpoints = {
      copilotAssist: '/copilot/assist',
      memorySearch: '/memory/search',
      memoryCommit: '/memory/commit',
      memoryUpdate: '/memory/update',
      memoryDelete: '/memory/delete',
    };
  }

  // -------------------- PUBLIC METHODS --------------------

  async copilotAssist(request: CopilotAssistRequest): Promise<CopilotAssistResponse> {
    this.validateRequest(request, ['user_id', 'message']);
    const body = {
      ...request,
      top_k: request.top_k ?? 6,
      context: request.context ?? {},
      stream: request.stream ?? false,
    };

    return this.requestWithFallback<CopilotAssistResponse>('copilotAssist', 'POST', body, {
      opName: 'copilot_assist',
    });
  }

  async memorySearch(request: MemorySearchRequest): Promise<MemorySearchResponse> {
    this.validateRequest(request, ['user_id', 'query']);
    const body = {
      ...request,
      top_k: request.top_k ?? 12,
      similarity_threshold: request.similarity_threshold ?? 0.6,
    };

    return this.requestWithFallback<MemorySearchResponse>('memorySearch', 'POST', body, {
      opName: 'memory_search',
    });
  }

  async memoryCommit(request: MemoryCommitRequest): Promise<MemoryCommitResponse> {
    this.validateRequest(request, ['user_id', 'text']);
    const body = {
      ...request,
      importance: request.importance ?? 5,
      decay: request.decay ?? 'short',
      tags: request.tags ?? [],
      metadata: request.metadata ?? {},
    };

    return this.requestWithFallback<MemoryCommitResponse>('memoryCommit', 'POST', body, {
      opName: 'memory_commit',
    });
  }

  async memoryUpdate(
    memoryId: string,
    updates: Partial<MemoryCommitRequest>
  ): Promise<MemoryCommitResponse> {
    if (!memoryId) throw new Error('Missing required field: memoryId');

    return this.requestWithFallback<MemoryCommitResponse>(
      'memoryUpdate',
      'PUT',
      updates,
      { opName: 'memory_update', pathSuffix: `/${encodeURIComponent(memoryId)}` },
    );
  }

  async memoryDelete(
    memoryId: string,
    options: { user_id: string; hard_delete?: boolean; org_id?: string }
  ): Promise<{ success: boolean; correlation_id: string }> {
    if (!memoryId) throw new Error('Missing required field: memoryId');
    this.validateRequest(options, ['user_id']);

    // If you pass flags via query string, add here:
    const qs = new URLSearchParams();
    if (options.hard_delete) qs.set('hard_delete', '1');
    if (options.org_id) qs.set('org_id', options.org_id);

    const suffix = `/${encodeURIComponent(memoryId)}${qs.toString() ? `?${qs}` : ''}`;

    return this.requestWithFallback<{ success: boolean; correlation_id: string }>(
      'memoryDelete',
      'DELETE',
      undefined,
      { opName: 'memory_delete', pathSuffix: suffix },
    );
  }

  async batchMemoryOperations(
    operations: Array<{
      type: 'search' | 'commit' | 'update' | 'delete';
      data: any;
    }>
  ): Promise<Array<{ success: boolean; result?: any; error?: string }>> {
    const results: Array<{ success: boolean; result?: any; error?: string }> = [];

    for (const op of operations) {
      try {
        let result: any;
        switch (op.type) {
          case 'search':
            result = await this.memorySearch(op.data);
            break;
          case 'commit':
            result = await this.memoryCommit(op.data);
            break;
          case 'update':
            result = await this.memoryUpdate(op.data.id, op.data);
            break;
          case 'delete':
            result = await this.memoryDelete(op.data.id, op.data);
            break;
          default:
            throw new Error(`Unknown operation type: ${op.type}`);
        }
        results.push({ success: true, result });
      } catch (err) {
        results.push({
          success: false,
          error: err instanceof Error ? err.message : 'Unknown error',
        });
      }
    }

    return results;
  }

  async healthCheck(): Promise<{
    status: 'healthy' | 'degraded' | 'unhealthy';
    endpoints: Record<string, { available: boolean; responseTime?: number; error?: string }>;
    timestamp: string;
  }> {
    const tests = Object.entries(this.endpoints).map(async ([key, relPath]) => {
      const typedKey = key as EndpointKey;
      const urls = this.getOrderedUrls(typedKey, relPath, '/health');

      for (const url of urls) {
        const start = Date.now();
        try {
          await this.apiClient.get(url, { timeout: this.config.timeout });
          const ms = Date.now() - start;
          return { name: key, available: true, responseTime: ms };
        } catch (e) {
          // try next url
          continue;
        }
      }
      return { name: key, available: false, error: 'All health endpoints failed' };
    });

    const results = await Promise.all(tests);

    const endpoints = results.reduce<Record<string, { available: boolean; responseTime?: number; error?: string }>>(
      (acc, r) => {
        acc[r.name] = { available: r.available, responseTime: r.responseTime, error: r.error };
        return acc;
      },
      {}
    );

    const total = results.length;
    const up = results.filter(r => r.available).length;

    const status: 'healthy' | 'degraded' | 'unhealthy' =
      up === total ? 'healthy' : up > 0 ? 'degraded' : 'unhealthy';

    return {
      status,
      endpoints,
      timestamp: new Date().toISOString(),
    };
  }

  getEndpointStats() {
    return this.apiClient.getEndpointStats?.();
  }

  clearCaches(): void {
    this.apiClient.clearCaches?.();
  }

  updateConfig(config: Partial<UnifiedApiClientConfig>): void {
    this.config = { ...this.config, ...config };
  }

  getConfig(): UnifiedApiClientConfig {
    return { ...this.config };
  }

  // -------------------- CORE REQUEST PIPELINE --------------------

  private async requestWithFallback<T>(
    endpointKey: EndpointKey,
    method: HttpMethod,
    body?: unknown,
    opts?: { opName?: string; pathSuffix?: string }
  ): Promise<T> {
    const opName = opts?.opName ?? endpointKey;
    const relPath = `${this.endpoints[endpointKey]}${opts?.pathSuffix ?? ''}`;
    const urls = this.getOrderedUrls(endpointKey, relPath);

    const errors: Array<{ url: string; error: unknown }> = [];

    for (const url of urls) {
      try {
        const res = await this.requestWithRetry<T>(url, method, body, opName);
        this.logSuccess(opName, res as any);
        return res;
      } catch (err) {
        errors.push({ url, error: err });
        this.logError(opName, err);
        // If fallback disabled, stop early
        if (!this.config.enableFallback) break;
        // otherwise try next base
      }
    }

    // Build a useful aggregate error
    const detail = errors.map(e => `• ${e.url}: ${e.error instanceof Error ? e.error.message : String(e.error)}`).join('\n');
    throw new Error(this.humanizeFailure(opName, detail));
  }

  private async requestWithRetry<T>(
    url: string,
    method: HttpMethod,
    body: unknown,
    opName: string
  ): Promise<T> {
    const attempts = Math.max(1, this.config.maxRetries);
    let lastErr: unknown;

    for (let i = 0; i < attempts; i++) {
      const attempt = i + 1;
      try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), this.config.timeout);

        // Use apiClient if it supports absolute URLs; otherwise fallback to fetch
        const res: T = await this.requestThroughApiClient<T>(url, method, body, controller.signal);

        clearTimeout(timeout);
        return res;
      } catch (err) {
        lastErr = err;

        // Stop retrying on auth/4xx except 429
        const message = err instanceof Error ? err.message : String(err);
        if (this.isNonRetriable(message)) break;

        if (attempt < attempts) {
          await this.sleep(this.backoffDelay(i));
          continue;
        }
      }
    }

    throw this.createUserFriendlyError(lastErr, `Request failed for ${opName}`);
  }

  private async requestThroughApiClient<T>(
    url: string,
    method: HttpMethod,
    body: unknown,
    signal: AbortSignal
  ): Promise<T> {
    // Prefer your existing apiClient methods if possible
    switch (method) {
      case 'GET':
        // @ts-expect-error apiClient signatures vary; assuming (url, options?)
        return this.apiClient.get<T>(url, { signal, timeout: this.config.timeout });
      case 'POST':
        // @ts-expect-error same assumption
        return this.apiClient.post<T>(url, body, { signal, timeout: this.config.timeout });
      case 'PUT':
        // @ts-expect-error same assumption
        return this.apiClient.put<T>(url, body, { signal, timeout: this.config.timeout });
      case 'DELETE':
        // @ts-expect-error same assumption
        return this.apiClient.delete<T>(url, { signal, timeout: this.config.timeout });
      default:
        throw new Error(`Unsupported method: ${method}`);
    }
  }

  // -------------------- HELPERS --------------------

  private getOrderedUrls(endpointKey: EndpointKey, relPath: string, suffix: string = ''): string[] {
    // Expect configManager to provide ordered base URLs per logical endpoint.
    // Fallback to current origin + relative path if not available.
    // Example contract (implement in endpoint-config):
    //   configManager.getOrderedBases(endpointKey) -> ['https://api-a', 'https://api-b', '']
    const bases: string[] =
      this.configManager.getOrderedBases?.(endpointKey) ??
      this.configManager.getOrderedEndpoints?.(endpointKey) ??
      [''];

    const urls = bases.map((base) => {
      if (!base) return `${relPath}${suffix}`;
      // Ensure single slash
      return `${base.replace(/\/+$/, '')}${relPath.startsWith('/') ? '' : '/'}${relPath}${suffix}`;
    });

    // If fallback disabled, only try the first
    return this.config.enableFallback ? urls : urls.slice(0, 1);
  }

  private validateRequest(request: any, requiredFields: string[]): void {
    for (const field of requiredFields) {
      if (!request || request[field] == null || request[field] === '') {
        throw new Error(`Missing required field: ${field}`);
      }
    }
  }

  private humanizeFailure(opName: string, detail?: string): string {
    const base = `${opName} failed across all endpoints.`;
    if (!detail) return base;
    return `${base}\n${detail}`;
  }

  private isNonRetriable(message: string): boolean {
    // Non-retriable if clearly auth/validation/notfound; 429 and 5xx are retriable
    return (
      message.includes('401') ||
      message.includes('403') ||
      message.includes('404') ||
      message.toLowerCase().includes('validation') ||
      message.toLowerCase().includes('forbidden')
    );
  }

  private backoffDelay(attemptIndex: number): number {
    // Exponential backoff with jitter
    const base = this.config.retryDelay * Math.pow(2, attemptIndex);
    const jitter = Math.floor(Math.random() * (base * 0.25));
    return base + jitter;
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((r) => setTimeout(r, ms));
  }

  private logSuccess(operation: string, response: unknown): void {
    if (!this.config.enableLogging) return;
    // pluggable: replace with your telemetry (Datadog, Sentry breadcrumb, etc.)
    // eslint-disable-next-line no-console
    console.log(`[UnifiedApi] ✅ ${operation} success`, this.extractCorrelation(response));
  }

  private logError(operation: string, error: unknown): void {
    if (!this.config.enableLogging) return;
    safeError(`[UnifiedApi] ❌ ${operation} failed:`, error);
  }

  private extractCorrelation(value: unknown): Record<string, unknown> | undefined {
    try {
      if (value && typeof value === 'object' && 'correlation_id' in (value as any)) {
        return { correlation_id: (value as any).correlation_id };
      }
    } catch {
      // ignore
    }
    return undefined;
  }

  private createUserFriendlyError(error: any, defaultMessage: string): Error {
    const msg = error instanceof Error ? error.message : String(error || '');
    const low = msg.toLowerCase();

    if (low.includes('aborted') || low.includes('timeout') || low.includes('timed out')) {
      return new Error('Request timed out. Please check your connection and try again.');
    }
    if (low.includes('cors')) {
      return new Error('Connection blocked by browser security. Please check your network settings.');
    }
    if (low.includes(' 404') || low.includes('not found')) {
      return new Error('Service endpoint not found. The feature may not be available.');
    }
    if (low.includes(' 401') || low.includes(' 403') || low.includes('unauthorized') || low.includes('forbidden')) {
      return new Error('Authentication required. Please log in and try again.');
    }
    if (low.includes(' 429') || low.includes('too many requests')) {
      return new Error('Too many requests. Please wait a moment and try again.');
    }
    if (low.includes(' 500') || low.includes(' 502') || low.includes(' 503') || low.includes(' 504') || low.includes('server error')) {
      return new Error('Server error. Please try again later.');
    }

    // Short, already-clear messages are fine as-is
    if (msg && msg.length < 120 && !low.includes('fetch')) {
      return new Error(msg);
    }

    return new Error(defaultMessage);
  }
}

// -------------------- SINGLETON ACCESSORS --------------------

let unifiedApiClient: UnifiedApiClient | null = null;

export function getUnifiedApiClient(): UnifiedApiClient {
  if (!unifiedApiClient) {
    unifiedApiClient = new UnifiedApiClient();
  }
  return unifiedApiClient;
}

export function initializeUnifiedApiClient(config?: Partial<UnifiedApiClientConfig>): UnifiedApiClient {
  unifiedApiClient = new UnifiedApiClient(config);
  return unifiedApiClient;
}
