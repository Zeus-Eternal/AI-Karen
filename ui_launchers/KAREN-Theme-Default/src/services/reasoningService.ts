/**
 * Reasoning Service - Connects to the backend reasoning system with fallbacks
 */
import { enhancedApiClient } from '@/lib/enhanced-api-client';
import { safeError } from '@/lib/safe-console';

export interface ReasoningRequest {
  input: string;
  context?: {
    user_id?: string;
    conversation_id?: string;
    [key: string]: unknown;
  };
}

export interface ReasoningResponse {
  success: boolean;
  response: {
    content: string;
    type: string;
    metadata?: {
      fallback_mode?: boolean;
      local_processing?: boolean;
      [key: string]: unknown;
    };
  };
  reasoning_method: string;
  fallback_used: boolean;
  errors?: {
    ai_error?: string;
    fallback_error?: string;
  };
}

export interface ReasoningSystemStatus {
  degraded: boolean;
  components: string[];
  fallback_systems_active: boolean;
  local_models_available: boolean;
  ai_status?: unknown;
  failed_providers?: string[];
  reason?: string;
}

export type FetchOptions = {
  timeoutMs?: number;
  retries?: number;
  retryBackoffMs?: number;
  method?: 'GET' | 'POST';
  headers?: Record<string, string>;
  body?: unknown;
};

class ReasoningService {
  // Prefer proxy routes; fallback to direct backend host
  private readonly PROXY_ANALYZE = '/api/karen/api/reasoning/analyze';
  private readonly PROXY_DEGRADED = '/api/health/degraded-mode';

  constructor() {
    // Initialize with enhanced API client
  }


  private async fetchJSON<T = unknown>(url: string, opts: FetchOptions = {}): Promise<T> {
    const {
      timeoutMs = 15000,
      retries = 1,
      retryBackoffMs = 400,
      method = 'GET',
      headers = {},
      body,
    } = opts;

    let lastErr: unknown;

    for (let attempt = 0; attempt <= retries; attempt++) {
      const controller = new AbortController();
      const t = setTimeout(() => controller.abort(), timeoutMs);

      try {
        const res = await fetch(url, {
          method,
          headers: {
            'Content-Type': 'application/json',
            ...headers,
          },
          body: body != null ? JSON.stringify(body) : undefined,
          signal: controller.signal,
        });

        clearTimeout(t);

        if (!res.ok) {
          // Retry on 5xx; otherwise throw immediately
          const isRetryable = res.status >= 500 && res.status < 600;
          const text = await res.text().catch(() => '');
          const err = new Error(`HTTP ${res.status} ${res.statusText}${text ? `: ${text}` : ''}`);
          if (isRetryable && attempt < retries) {
            await new Promise(r => setTimeout(r, retryBackoffMs * Math.pow(2, attempt)));
            continue;
          }
          throw err;
        }

        // Try parse JSON safely; empty body -> {} as unknown
        const contentType = res.headers.get('content-type') || '';
        if (!contentType.includes('application/json')) {
          // attempt text -> try to parse, else wrap into object
          const txt = await res.text().catch(() => '');
          try {
            return JSON.parse(txt) as T;
          } catch {
            return { raw: txt } as unknown as T;
          }
        }

        return (await res.json()) as T;
      } catch (err) {
        clearTimeout(t);
        lastErr = err;
        // Retry only on network/abort errors
        const msg = (err as Error)?.message || '';
        const isAbort = msg.includes('aborted') || msg.includes('signal');
        const isNetwork = msg.includes('Failed to fetch') || msg.includes('NetworkError') || msg.includes('TypeError');
        if ((isAbort || isNetwork) && attempt < retries) {
          await new Promise(r => setTimeout(r, retryBackoffMs * Math.pow(2, attempt)));
          continue;
        }
        break;
      }
    }

    throw lastErr instanceof Error ? lastErr : new Error('Unknown fetch error');
  }

  private fallbackResponse(input: string, error?: unknown): ReasoningResponse {
    return {
      success: true,
      response: {
        content: `I'm having trouble connecting to the reasoning system right now. However, I can see you're asking about: "${input}". I'm running in offline mode but still here to help as best I can.`,
        type: 'text',
        metadata: {
          fallback_mode: true,
          local_processing: true,
          connection_error: true,
        },
      },
      reasoning_method: 'client_fallback',
      fallback_used: true,
      errors: {
        ai_error: error instanceof Error ? error.message : 'Unknown error',
      },
    };
  }

  /**
   * Analyze using proxy first; if it fails, fall back to direct backend.
   */
  async analyze(request: ReasoningRequest): Promise<ReasoningResponse> {
    // 1) Proxy route (same-origin, handles cookies, headers, etc.)
    try {
      const data = await this.fetchJSON<ReasoningResponse>(this.PROXY_ANALYZE, {
        method: 'POST',
        body: request,
        timeoutMs: 20000,
        retries: 1,
      });
      return data;
    } catch (proxyErr) {
      safeError('Reasoning proxy error:', proxyErr);
    }

    // 2) Direct backend fallback
    try {
      const directUrl = '/api/reasoning/analyze';
      const data = await this.fetchJSON<ReasoningResponse>(directUrl, {
        method: 'POST',
        body: request,
        timeoutMs: 20000,
        retries: 1,
      });
      return {
        ...data,
        // ensure we surface that we used the direct backend
        reasoning_method: data.reasoning_method || 'backend_direct',
        fallback_used: data.fallback_used || false,
      };
    } catch (backendErr) {
      safeError('Reasoning backend error:', backendErr);
      return this.fallbackResponse(request.input, backendErr);
    }
  }

  /**
   * Quick health probe (proxy first, then backend)
   */
  async testConnection(): Promise<boolean> {
    // proxy
    try {
      const response = await enhancedApiClient.get<unknown>(this.PROXY_DEGRADED, { timeout: 8000 });
      return !!response.data;
    } catch {
      // fallback to backend
    }
    try {
      // Temporarily set the base URL for the direct backend call
      const client = enhancedApiClient as unknown as { baseURL?: string };
      const originalBaseURL = client.baseURL;
      client.baseURL = ''; // This will use the current domain without /api prefix
      
      const response = await enhancedApiClient.get<unknown>('/health/degraded-mode', { timeout: 8000 });
      
      // Restore the original base URL
      client.baseURL = originalBaseURL;
      
      return !!response.data;
    } catch {
      return false;
    }
  }

  /**
   * Returns a normalized system status shape
   */
  async getSystemStatus(): Promise<ReasoningSystemStatus> {
    interface DegradedModeData {
      is_active?: boolean;
      infrastructure_issues?: string[];
      core_helpers_available?: {
        fallback_responses?: boolean;
        total_ai_capabilities?: boolean;
      };
      ai_status?: unknown;
      failed_providers?: string[];
      reason?: string;
    }

    const mapDegraded = (degradedModeData: unknown): ReasoningSystemStatus => {
      const data = degradedModeData as DegradedModeData;
      return {
        degraded: !!data?.is_active,
        components: data?.infrastructure_issues || [],
        fallback_systems_active: !!data?.core_helpers_available?.fallback_responses,
        local_models_available: !!data?.core_helpers_available?.total_ai_capabilities,
        ai_status: data?.ai_status,
        failed_providers: data?.failed_providers || [],
        reason: data?.reason,
      };
    };

    // proxy first
    try {
      const response = await enhancedApiClient.get<unknown>(this.PROXY_DEGRADED, { timeout: 10000 });
      return mapDegraded(response.data);
    } catch (proxyErr) {
      safeError('Degraded-mode (proxy) check failed:', proxyErr);
    }

    // backend fallback
    try {
      // Temporarily set the base URL for the direct backend call
      const client = enhancedApiClient as unknown as { baseURL?: string };
      const originalBaseURL = client.baseURL;
      client.baseURL = ''; // This will use the current domain without /api prefix
      
      const response = await enhancedApiClient.get<unknown>('/health/degraded-mode', { timeout: 10000 });
      
      // Restore the original base URL
      client.baseURL = originalBaseURL;
      
      return mapDegraded(response.data);
    } catch (backendErr) {
      safeError('Degraded-mode (backend) check failed:', backendErr);
    }

    // safe default
    return {
      degraded: true,
      components: ['connection'],
      fallback_systems_active: true,
      local_models_available: false,
    };
  }
}

export const reasoningService = new ReasoningService();
export default reasoningService;
