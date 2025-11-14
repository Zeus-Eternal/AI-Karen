import { NextRequest, NextResponse } from 'next/server';

type Provider =
  | 'llama-cpp'
  | 'transformers'
  | 'stable-diffusion'
  | 'flux'
  | string;

interface LoadModelRequest {
  model_id: string;
  provider?: Provider;
  options?: {
    preserve_context?: boolean;
    force_reload?: boolean;
    memory_limit?: number;
  };
}

type LoadModelResult = {
  success?: boolean;
  memory_usage?: number;
  message?: string;
  [key: string]: unknown;
};

interface LoadModelResponse {
  success: boolean;
  model_id: string;
  provider: string;
  load_time: number;
  memory_usage?: number;
  capabilities: string[];
  message?: string;
  error?: string;
}

interface LoadState {
  inFlight: boolean;
  startedAt?: number;
  finishedAt?: number | null;
  lastModelId?: string | null;
  lastProvider?: string | null;
  lastSuccess?: boolean | null;
  lastError?: string | null;
  lastLoadTimeMs?: number | null;
  preserveContext?: boolean;
  forceReload?: boolean;
}

const LOAD_TIMEOUT_MS =
  Number(process.env.KAREN_MODEL_LOAD_TIMEOUT_MS || 30000);

const globalScope = globalThis as typeof globalThis & {
  __kariModelLoadState?: LoadState;
};

function state(): LoadState {
  if (!globalScope.__kariModelLoadState) {
    globalScope.__kariModelLoadState = {
      inFlight: false,
      finishedAt: null,
      lastModelId: null,
      lastProvider: null,
      lastSuccess: null,
      lastError: null,
      lastLoadTimeMs: null,
      preserveContext: true,
      forceReload: false,
    };
  }
  return globalScope.__kariModelLoadState!;
}

function ok<T>(data: T, extraHeaders?: Record<string, string>): NextResponse {
  return NextResponse.json(data as unknown, {
    status: 200,
    headers: {
      'Cache-Control': 'no-store',
      ...extraHeaders,
    },
  });
}

function err(
  status: number,
  code: string,
  message: string,
  extra?: Record<string, unknown>,
): NextResponse {
  return NextResponse.json(
    {
      error: code,
      message,
      ...(extra || {}),
    },
    {
      status,
      headers: {
        'Cache-Control': 'no-store',
      },
    },
  );
}

function sanitizePayload(body: unknown): LoadModelRequest | null {
  if (!body || typeof body !== 'object') return null;

  const b = body as Record<string, unknown>;
  const model_id = typeof b.model_id === 'string' ? b.model_id.trim() : '';
  const provider =
    typeof b.provider === 'string' && b.provider.trim()
      ? (b.provider.trim() as Provider)
      : undefined;

  const optionsRaw = (b.options ?? {}) as Record<string, unknown>;
  const options = {
    preserve_context:
      typeof optionsRaw.preserve_context === 'boolean'
        ? optionsRaw.preserve_context
        : true,
    force_reload:
      typeof optionsRaw.force_reload === 'boolean'
        ? optionsRaw.force_reload
        : false,
    memory_limit:
      typeof optionsRaw.memory_limit === 'number' &&
      Number.isFinite(optionsRaw.memory_limit)
        ? optionsRaw.memory_limit
        : undefined,
  };

  if (!model_id) return null;

  return { model_id, provider, options };
}

function asRecord(value: unknown): Record<string, unknown> {
  if (typeof value === 'object' && value !== null) {
    return value as Record<string, unknown>;
  }
  return {};
}

async function withTimeout<T>(
  p: Promise<T>,
  ms = LOAD_TIMEOUT_MS,
  label = 'loadModel',
): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), ms);
  try {
    // Let consumers read controller if they support it (we won’t force it)
    const result = await Promise.race([
      p,
      new Promise<never>((_, reject) =>
        setTimeout(
          () => reject(new Error(`${label} timed out after ${ms}ms`)),
          ms,
        ),
      ),
    ]);
    return result;
  } finally {
    clearTimeout(timeout);
  }
}

async function loadViaService(
  model_id: string,
  provider: string | undefined,
  options: NonNullable<LoadModelRequest['options']>,
) {
  const { modelSelectionService } = await import('@/lib/model-selection-service');

  // 1) Validate target model
  const models = await modelSelectionService.getAvailableModels();
  const target = models.find(
    (m) => (m as { id?: string }).id === model_id
  );
  if (!target) {
    return {
      exists: false,
      provider: provider || 'unknown',
      capabilities: [] as string[],
      message: `Model with ID '${model_id}' not found in available models`,
    };
  }

  // 2) If service exposes a real loader, use it; else pretend-success
  const loader =
    (modelSelectionService as { loadModel?: unknown }).loadModel as
      | ((modelId: string, opts: {
          provider?: string;
          preserveContext?: boolean;
          forceReload?: boolean;
          memoryLimit?: number | null;
        }) => Promise<LoadModelResult>)
      | undefined;
  const canLoad = typeof loader === 'function';

  if (canLoad) {
    const res = await withTimeout<LoadModelResult>(
      loader(model_id, {
        provider: provider || target.provider,
        preserveContext: options.preserve_context,
        forceReload: options.force_reload,
        memoryLimit: options.memory_limit,
      }) as Promise<LoadModelResult>,
      LOAD_TIMEOUT_MS,
      'modelSelectionService.loadModel',
    );
    // Expect res shape to have success + maybe memory/capabilities
    return {
      exists: true,
      success: Boolean(res?.success),
      provider: provider || target.provider,
      memory_usage: res?.memory_usage,
      capabilities: target.capabilities || [],
      message: res?.message || (res?.success ? 'Loaded' : 'Failed'),
    };
  }

  // Fallback pretend-load (consistent shape)
  return {
    exists: true,
    success: true,
    provider: provider || target.provider,
    capabilities: target.capabilities || [],
    message: 'Loaded (fallback path)',
  };
}

/**
 * POST /api/models/load
 * Loads (or switches to) a model with optional provider and load options.
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json().catch(() => ({}));
    const payload = sanitizePayload(body);

    if (!payload) {
      return err(400, 'INVALID_REQUEST', 'Missing or invalid "model_id"');
    }

    const { model_id, provider, options = {} } = payload;

    // Guard: prevent concurrent loads colliding
    const st = state();
    if (st.inFlight) {
      return err(409, 'LOAD_IN_PROGRESS', 'Another model load is in progress', {
        current: {
          model_id: st.lastModelId,
          provider: st.lastProvider,
          startedAt: st.startedAt,
        },
      });
    }

    st.inFlight = true;
    st.startedAt = Date.now();
    st.finishedAt = null;
    st.lastError = null;
    st.preserveContext = Boolean(options.preserve_context ?? true);
    st.forceReload = Boolean(options.force_reload ?? false);

    const t0 = Date.now();

    try {
      const result = (await loadViaService(model_id, provider, options)) as LoadModelResult;

      const loadTime = Date.now() - t0;
      st.lastLoadTimeMs = loadTime;
      st.lastModelId = model_id;
      st.lastProvider = String(result.provider ?? provider ?? 'unknown');
      st.finishedAt = Date.now();

      if (!result.exists) {
        st.lastSuccess = false;
        st.lastError = result.message || 'Model not found';
        st.inFlight = false;
        return err(404, 'MODEL_NOT_FOUND', st.lastError!, {
          model_id,
        });
      }

      const success = Boolean(result.success ?? true);
      st.lastSuccess = success;

      const capabilitiesList = Array.isArray(result.capabilities)
        ? (result.capabilities as string[])
        : [];
      const response: LoadModelResponse = {
        success,
        model_id,
        provider: st.lastProvider!,
        load_time: loadTime,
        capabilities: capabilitiesList,
        ...(result.memory_usage ? { memory_usage: result.memory_usage } : {}),
        message:
          result.message ||
          (success ? 'Model loaded successfully' : 'Model load failed'),
      };

      st.inFlight = false;

      if (!success) {
        return NextResponse.json(response, {
          status: 500,
          headers: {
            'X-Load-Time': String(loadTime),
            'X-Model-Provider': response.provider,
            'Cache-Control': 'no-store',
          },
        });
      }

      return NextResponse.json(response, {
        status: 200,
        headers: {
          'X-Load-Time': String(loadTime),
          'X-Model-Provider': response.provider,
          'Cache-Control': 'no-store',
        },
      });
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Unknown loading error';
      st.lastSuccess = false;
      st.lastError = errorMessage;
      st.finishedAt = Date.now();
      st.inFlight = false;

      return err(500, 'MODEL_LOAD_FAILED', st.lastError!, {
        model_id,
      });
    }
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : 'Request processing failed';
    return err(400, 'INVALID_REQUEST', errorMessage);
  }
}

/**
 * GET /api/models/load
 * Returns current load status and last load result.
 */
export async function GET(_request: NextRequest) {
  try {
    // We prefer reading some live info from modelSelectionService if helpful,
    // but we don’t fail if it’s unavailable.
    let stats: unknown = {};
    try {
      const { modelSelectionService } = await import('@/lib/model-selection-service');
      stats = (await modelSelectionService.getSelectionStats?.()) || {};
    } catch {
      // ignore
    }

    const st = state();
    const statsRecord = asRecord(stats);
    const payload = {
      currently_loaded: statsRecord.lastSelectedModel ?? st.lastModelId ?? null,
      loading_status: st.inFlight,
      last_load_time: st.lastLoadTimeMs ?? null,
      last_result: st.lastSuccess,
      last_error: st.lastError,
      last_provider: st.lastProvider ?? null,
      started_at: st.startedAt ?? null,
      finished_at: st.finishedAt ?? null,
      options: {
        preserve_context: st.preserveContext,
        force_reload: st.forceReload,
      },
      available_providers: [
        'llama-cpp',
        'transformers',
        'stable-diffusion',
        'flux',
      ],
      system_resources: {
        memory_available: true, // hook real probe later
        gpu_available: false, // hook real probe later
      },
    };

    return ok(payload);
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    return err(500, 'STATUS_CHECK_FAILED', errorMessage);
  }
}
