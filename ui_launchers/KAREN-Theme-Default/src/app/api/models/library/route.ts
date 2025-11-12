import { randomUUID } from 'crypto';
import { NextRequest, NextResponse } from 'next/server';

import { logger } from '@/lib/logger';
import { getBackendCandidates, withBackendPath } from '@/app/api/_utils/backend';

const DEFAULT_TIMEOUT_MS = Number(process.env.KAREN_API_PROXY_LONG_TIMEOUT_MS || 30000);

interface ModelHealthStatus {
  is_healthy: boolean;
  last_check: string;
  issues: string[];
  memory_requirement?: number;
  performance_metrics?: {
    load_time?: number;
    inference_speed?: number;
    memory_usage?: number;
  };
}

interface EnhancedModelInfo {
  id: string;
  name: string;
  provider: string;
  type: string;
  status: string;
  description?: string;
  capabilities: string[];
  size?: number;
  metadata: Record<string, unknown>;
  health?: ModelHealthStatus;
  path?: string;
  format?: string;
  last_scanned?: string;
}

type LibraryResponse = {
  models: EnhancedModelInfo[];
  categorized_models?: {
    text_generation: EnhancedModelInfo[];
    image_generation: EnhancedModelInfo[];
    embedding: EnhancedModelInfo[];
    other: EnhancedModelInfo[];
  };
  total_count: number;
  local_count: number;
  available_count: number;
  healthy_count?: number;
  scan_metadata?: Record<string, unknown>;
  source: 'backend' | 'enhanced_dynamic_scan' | 'fallback_scan' | 'minimal_fallback' | 'error_fallback';
  message?: string;
};

function okJson(data: unknown, status = 200, headers: Record<string, string> = {}) {
  return NextResponse.json(data, {
    status,
    headers: {
      'Cache-Control': status === 200 ? 'public, max-age=300' : 'no-store',
      ...headers,
    },
  });
}

function errJson(status: number, error: string, message: string, extra?: Record<string, unknown>) {
  return NextResponse.json(
    { error, message, ...(extra || {}) },
    { status, headers: { 'Cache-Control': 'no-store' } },
  );
}

function sanitizeParam(value: string | null, allowList?: string[]): string | undefined {
  if (!value) return undefined;
  const v = value.trim();
  if (!v) return undefined;
  if (allowList && !allowList.includes(v)) return undefined;
  return v;
}

async function getModelHealthStatus(modelId: string): Promise<ModelHealthStatus> {
  try {
    const { modelSelectionService } = await import('@/lib/model-selection-service');
    // Hook in real checks when available (GPU mem, warmup ping, etc.)
    const status: ModelHealthStatus = {
      is_healthy: true,
      last_check: new Date().toISOString(),
      issues: [],
    };
    void modelSelectionService; // keep import for future wiring
    if (typeof logger.debug === 'function') {
      logger.debug('Model health status stub returning healthy result', { modelId });
    }
    return status;
  } catch (error) {
    return {
      is_healthy: false,
      last_check: new Date().toISOString(),
      issues: [
        `Health check failed for ${modelId}: ${error instanceof Error ? error.message : 'Unknown error'}`,
      ],
    };
  }
}

function categorize(models: EnhancedModelInfo[]) {
  return {
    text_generation: models.filter((m) => m.type === 'text' || m.type === 'text_generation'),
    image_generation: models.filter((m) => m.type === 'image' || m.type === 'image_generation'),
    embedding: models.filter((m) => m.type === 'embedding'),
    other: models.filter(
      (m) => !['text', 'text_generation', 'image', 'image_generation', 'embedding'].includes(m.type),
    ),
  };
}

export async function GET(request: NextRequest) {
  const requestId = randomUUID();
  const url = request.nextUrl;
  const q = url.searchParams;

  // Query sanitization
  const scan = q.get('scan') === 'true';
  const includeHealth = q.get('includeHealth') === 'true';
  const forceRefresh = q.get('forceRefresh') === 'true';
  const modelType = sanitizeParam(q.get('type'));
  const providerFilter = sanitizeParam(q.get('provider'));
  const timeoutMs = Number(q.get('timeoutMs') || DEFAULT_TIMEOUT_MS) || DEFAULT_TIMEOUT_MS;

  logger.info('Models library request received', {
    requestId,
    method: request.method,
    scan,
    includeHealth,
    forceRefresh,
    modelType,
    provider: providerFilter,
    timeoutMs,
  });

  // If caller explicitly requests dynamic scan, do it here (best-effort)
  if (scan) {
    try {
      const { modelSelectionService } = await import('@/lib/model-selection-service');
      const modelsRaw = await modelSelectionService.getAvailableModels(forceRefresh);

      // Optional narrow by type/provider (client-side filter)
      let models = (modelsRaw || []).map((m: unknown) => ({
        ...m,
        type: m.type || 'unknown',
        last_scanned: new Date().toISOString(),
      })) as EnhancedModelInfo[];

      if (modelType) models = models.filter((m) => (m.type || '').includes(modelType));
      if (providerFilter) models = models.filter((m) => (m.provider || '') === providerFilter);

      if (includeHealth) {
        models = await Promise.all(
          models.map(async (m) => ({
            ...m,
            health: await getModelHealthStatus(m.id),
          })),
        );
      }

      const categorized = categorize(models);
      const healthyCount = includeHealth ? models.filter((m) => m.health?.is_healthy).length : undefined;

      const stats = await modelSelectionService.getSelectionStats().catch(() => ({} as unknown));
      const response: LibraryResponse = {
        models,
        categorized_models: categorized,
        total_count: models.length,
        local_count: models.filter((m) => m.status === 'local').length,
        available_count: models.filter((m) => m.status === 'available').length,
        healthy_count: healthyCount,
        scan_metadata: {
          ...(stats?.scanStats || {}),
          scan_timestamp: new Date().toISOString(),
          include_health: includeHealth,
          filters_applied: { type: modelType, provider: providerFilter },
        },
        source: 'enhanced_dynamic_scan',
      };

      logger.info('Models library dynamic scan completed', {
        requestId,
        totalModels: response.total_count,
        localModels: response.local_count,
        healthyModels: response.healthy_count,
      });

      return okJson(response, 200, {
        'X-Scan-Timestamp': new Date().toISOString(),
        'X-Models-Count': String(response.total_count),
      });
    } catch (scanError) {
      logger.error('Models library dynamic scan failed', {
        requestId,
        error: scanError instanceof Error ? scanError.message : String(scanError),
      });

      return errJson(
        500,
        'SCAN_FAILED',
        'Dynamic model scanning encountered an error',
        { fallback_available: true },
      );
    }
  }

  // Otherwise, proxy to backend with multi-candidate failover
  const candidates = getBackendCandidates();
  const authHeader = request.headers.get('authorization') || undefined;
  const headers: Record<string, string> = { Accept: 'application/json', Connection: 'keep-alive' };
  if (authHeader) headers.Authorization = authHeader;

  const queryString = url.searchParams.toString();
  let lastError: string | null = null;
  let resp: Response | null = null;
  let usedUrl = '';

  for (const base of candidates) {
    const target = withBackendPath('/api/models/library', base);
    const fullUrl = queryString ? `${target}?${queryString}` : target;

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);

    logger.info('Models library proxying to backend candidate', { requestId, fullUrl });

    try {
      resp = await fetch(fullUrl, {
        method: 'GET',
        headers,
        signal: controller.signal,
        cache: 'no-store',
      });
      clearTimeout(timer);

      if (resp.ok) {
        usedUrl = fullUrl;
        break;
      }

      // Retry on 5xx; on 4xx we still try next candidate (in case auth differs per backend)
      lastError = `HTTP ${resp.status}`;
      logger.warn('Backend candidate responded non-OK', {
        requestId,
        fullUrl,
        status: resp.status,
      });
    } catch (error: unknown) {
      clearTimeout(timer);
      const message = error instanceof Error ? error.message : String(error);
      lastError = message || 'Fetch failed';
      logger.warn('Backend candidate fetch error', { requestId, fullUrl, error: lastError });
    }
  }

  if (resp) {
    const contentType = resp.headers.get('content-type') || '';
    let data: unknown;

    try {
      if (contentType.includes('application/json')) {
        data = await resp.json();
      } else {
        const text = await resp.text();
        data = resp.ok ? { message: text } : { error: text };
        logger.warn('Received non-JSON from backend models library', {
          requestId,
          usedUrl,
          contentType,
        });
      }
    } catch (parseErr: unknown) {
      logger.error('Failed to parse backend payload', {
        requestId,
        usedUrl,
        error: parseErr?.message || String(parseErr),
      });
      data = { models: [] };
    }

    logger.info('Models library backend response forwarded', {
      requestId,
      usedUrl,
      status: resp.status,
      ok: resp.ok,
      modelCount: Array.isArray(data?.models) ? data.models.length : undefined,
    });

    // If backend returns a plain array or different shape, normalize minimally
    if (Array.isArray(data)) {
      data = { models: data, source: 'backend' };
    } else if (data && typeof data === 'object' && !('source' in data)) {
      (data as Record<string, unknown>).source = 'backend';
    }

    return NextResponse.json(data, {
      status: resp.status,
      headers: {
        'Cache-Control': resp.ok ? 'public, max-age=300' : 'no-store',
      },
    });
  }

  // Backend completely unreachable — try local fallback scan
  try {
    logger.warn('Backend unavailable; attempting fallback scan', { requestId });
    const { modelSelectionService } = await import('@/lib/model-selection-service');
    const fallbackModels = await modelSelectionService.scanLocalDirectories({
      forceRefresh: true,
      includeHealth: false,
    });

    const normalizedModels: EnhancedModelInfo[] = (fallbackModels || []).map((m: unknown) => ({
      ...m,
      type: m.type || 'unknown',
      last_scanned: new Date().toISOString(),
    }));

    const filteredModels = normalizedModels.filter((model) => {
      const matchesType = modelType ? (model.type || '').includes(modelType) : true;
      const matchesProvider = providerFilter ? (model.provider || '') === providerFilter : true;
      return matchesType && matchesProvider;
    });

    const response: LibraryResponse = {
      models: filteredModels,
      total_count: filteredModels.length,
      local_count: filteredModels.filter((m) => m.status === 'local').length,
      available_count: filteredModels.filter((m) => m.status === 'available').length,
      source: 'fallback_scan',
      message: 'Backend unavailable, using local directory scanning',
    };

    logger.warn('Fallback scan succeeded', {
      requestId,
      modelsFound: response.total_count,
    });

    return okJson(response, 200, { 'X-Models-Count': String(response.total_count) });
  } catch (fallbackErr: unknown) {
    logger.error('Fallback local scan failed', {
      requestId,
      error: fallbackErr?.message || String(fallbackErr),
      lastBackendError: lastError,
    });

    const minimal: LibraryResponse = {
      models: [],
      total_count: 0,
      local_count: 0,
      available_count: 0,
      source: 'minimal_fallback',
      message: 'No models available. Please check backend connectivity.',
    };

    return okJson(minimal, 200);
  }
}
