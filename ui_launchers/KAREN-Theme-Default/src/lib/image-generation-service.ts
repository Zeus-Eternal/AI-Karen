// ui_launchers/web_ui/src/lib/image-generation-service.ts
/**
 * ImageGenerationService
 *
 * Production-grade, local-first image generation/orchestration for the Web UI.
 * - Defaults to local SD (Januxis) via your backend proxy
 * - Optional providers: SD WebUI, Gemini, Stability, Unsplash fallback (placeholder)
 * - Prompt-first inputs, deterministic safety, idempotent retries
 * - Observability: correlation_id, timing, trace hooks
 * - Abortable, with hard timeouts per step
 *
 * NOTE: No API keys live in the browser. All calls hit your backend proxy routes.
 */

export type Provider =
  | 'januxis-local'     // your local Stable Diffusion pipeline (default)
  | 'sd-webui'          // AUTOMATIC1111 proxy on backend
  | 'gemini'            // backend proxy to Google’s image gen
  | 'stability'         // backend proxy to Stability AI
  | 'unsplash-fallback' // last-resort stock image fallback (proxy)
;

export interface GenerationInput {
  prompt: string;
  negative_prompt?: string;
  width?: number;            // default 768
  height?: number;           // default 768
  steps?: number;            // default 30
  guidance_scale?: number;   // default 7
  seed?: number | 'random';
  sampler?: string;          // e.g., "Euler a"
  style_preset?: string;     // optional style routing
  cfg?: number;              // alias of guidance_scale
  loras?: Array<{ model: string; weight?: number }>;
  clip_skip?: number;
  hrfix?: boolean;
  enhance_prompt?: boolean;  // provider may rewrite prompt
  safety?: { nsfw?: boolean; violence?: boolean; sensitive?: boolean };
  user_tags?: string[];      // for analytics
  correlation_id?: string;   // injected/overridden by service if omitted
  timeout_ms?: number;       // per-attempt timeout
}

export interface GenerationResult {
  ok: true;
  provider: Provider;
  correlation_id: string;
  duration_ms: number;
  seed?: number;
  image_url: string;     // returned from backend storage (e.g., /media/... or signed URL)
  mime_type: string;     // 'image/png', 'image/webp', 'image/jpeg'
  width: number;
  height: number;
  stats?: Record<string, any>;
}

export interface GenerationError {
  ok: false;
  provider: Provider;
  correlation_id: string;
  duration_ms: number;
  status?: number;
  code?: string;
  message: string;
  details?: any;
}

export type GenerationResponse = GenerationResult | GenerationError;

function isErrorResponse(response: GenerationResponse): response is GenerationError {
  return response.ok === false;
}

export interface TraceEvent {
  phase: 'start' | 'attempt' | 'success' | 'failure' | 'fallback' | 'done' | 'timeout';
  provider?: Provider;
  correlation_id: string;
  attempt?: number;
  status?: number;
  error?: string;
  data?: unknown;
  elapsed_ms: number;
  duration_ms?: number;
  providers?: Provider[];
  code?: string;
}

type TraceExtras = Partial<Omit<TraceEvent, 'phase' | 'correlation_id' | 'elapsed_ms'>> & {
  elapsed_ms?: number;
};

export interface ServiceConfig {
  // Backend proxy endpoints (all server-side key handling)
  endpoints: {
    januxis: string;       // e.g., '/api/images/januxis/generate'
    sd_webui?: string;     // e.g., '/api/images/sd-webui/generate'
    gemini?: string;       // e.g., '/api/images/gemini/generate'
    stability?: string;    // e.g., '/api/images/stability/generate'
    unsplash?: string;     // e.g., '/api/images/unsplash/search'
  };
  default_provider?: Provider;           // 'januxis-local'
  fallback_chain?: Provider[];           // tried when a provider fails or is 4xx/5xx
  hard_timeout_ms?: number;              // outer deadline across retries/providers
  max_attempts_per_provider?: number;    // default 2
  initial_backoff_ms?: number;           // default 350
  max_backoff_ms?: number;               // default 3000
  // Optional hook for global headers (e.g., auth cookie not needed; use same-origin)
  buildHeaders?: () => HeadersInit;
  // Observability hooks
  onTrace?: (event: TraceEvent) => void;
}

export class ImageGenerationService {
  private cfg: Required<Omit<ServiceConfig,
    'buildHeaders' | 'onTrace' | 'endpoints'>> & {
      endpoints: ServiceConfig['endpoints'];
      buildHeaders?: ServiceConfig['buildHeaders'];
      onTrace?: ServiceConfig['onTrace'];
    };

  constructor(config: ServiceConfig) {
    this.cfg = {
      endpoints: config.endpoints,
      default_provider: config.default_provider ?? 'januxis-local',
      fallback_chain: config.fallback_chain ?? ['sd-webui', 'gemini', 'stability', 'unsplash-fallback'],
      hard_timeout_ms: config.hard_timeout_ms ?? 45_000,
      max_attempts_per_provider: config.max_attempts_per_provider ?? 2,
      initial_backoff_ms: config.initial_backoff_ms ?? 350,
      max_backoff_ms: config.max_backoff_ms ?? 3_000,
      buildHeaders: config.buildHeaders,
      onTrace: config.onTrace
    };
  }

  /**
   * Public API: generate an image with local-first routing + fallbacks.
   */
  async generate(
    input: GenerationInput,
    preferredProvider?: Provider,
    signal?: AbortSignal
  ): Promise<GenerationResponse> {
    const started = Date.now();
    const correlation = input.correlation_id ?? this.newCorrelationId();
    const providers = this.buildPlan(preferredProvider ?? this.cfg.default_provider);

    this.trace('start', correlation, { providers, elapsed_ms: 0 });

    const controller = new AbortController();
    const outerTimer = setTimeout(() => controller.abort(), this.cfg.hard_timeout_ms);
    const combinedSignal = this.mergeSignals(signal, controller.signal);

    try {
      for (const provider of providers) {
        const result = await this.tryProviderWithRetries(provider, input, correlation, combinedSignal, started);
        if (!isErrorResponse(result)) {
          const totalDuration = Date.now() - started;
          this.trace('done', correlation, { provider, duration_ms: totalDuration, elapsed_ms: totalDuration });
          return result;
        }
        const errorResult = result;
        // Log and continue to next provider in chain
        this.trace('fallback', correlation, {
          provider,
          error: errorResult.message,
          code: errorResult.code,
          elapsed_ms: Date.now() - started
        });
      }

      return {
        ok: false,
        provider: providers[providers.length - 1]!,
        correlation_id: correlation,
        duration_ms: Date.now() - started,
        code: 'ALL_PROVIDERS_FAILED',
        message: 'All providers in the fallback chain failed to generate an image.'
      };
    } catch (err: any) {
      const elapsed = Date.now() - started;
      const message = (err?.name === 'AbortError')
        ? 'Overall image generation timed out.'
        : (err?.message ?? String(err));
      this.trace('timeout', correlation, { error: message, elapsed_ms: elapsed });
      return {
        ok: false,
        provider: providers[0]!,
        correlation_id: correlation,
        duration_ms: elapsed,
        code: err?.name === 'AbortError' ? 'HARD_TIMEOUT' : 'UNCAUGHT_ERROR',
        message
      };
    } finally {
      clearTimeout(outerTimer);
    }
  }

  // -------------------------- Internals --------------------------

  private buildPlan(first: Provider): Provider[] {
    const seen = new Set<Provider>();
    const plan: Provider[] = [];
    const push = (p: Provider) => { if (!seen.has(p)) { seen.add(p); plan.push(p); } };
    push(first);
    for (const p of this.cfg.fallback_chain) push(p);
    return plan;
  }

  private async tryProviderWithRetries(
    provider: Provider,
    input: GenerationInput,
    correlation_id: string,
    signal: AbortSignal,
    started: number
  ): Promise<GenerationResponse> {
    let attempt = 0;
    let backoff = this.cfg.initial_backoff_ms;

    while (attempt < this.cfg.max_attempts_per_provider) {
      attempt++;
      const t0 = Date.now();
      this.trace('attempt', correlation_id, { provider, attempt, elapsed_ms: Date.now() - started });

      try {
        const res = await this.invokeProvider(provider, input, correlation_id, signal);
        const elapsed = Date.now() - t0;

        if (!isErrorResponse(res)) {
          const totalDuration = Date.now() - started;
          this.trace('success', correlation_id, {
            provider,
            attempt,
            elapsed_ms: elapsed,
            duration_ms: totalDuration
          });
          return { ...res, duration_ms: totalDuration };
        }
        const errorResponse = res;

        // Retry only for transient classes
        if (this.isTransient(errorResponse.status, errorResponse.code)) {
          this.trace('failure', correlation_id, {
            provider,
            attempt,
            status: errorResponse.status,
            error: errorResponse.message,
            elapsed_ms: elapsed
          });
          await this.sleep(backoff, signal);
          backoff = Math.min(backoff * 2, this.cfg.max_backoff_ms);
          continue;
        }

        // Non-transient → stop retrying this provider
        this.trace('failure', correlation_id, {
          provider,
          attempt,
          status: errorResponse.status,
          error: errorResponse.message,
          elapsed_ms: elapsed
        });
        return { ...errorResponse, duration_ms: Date.now() - started };
      } catch (err: any) {
        const elapsed = Date.now() - t0;
        if (err?.name === 'AbortError') {
          return {
            ok: false,
            provider,
            correlation_id,
            duration_ms: Date.now() - started,
            code: 'ATTEMPT_TIMEOUT',
            message: 'Provider attempt aborted or timed out.'
          };
        }
        // Treat as transient and retry
        this.trace('failure', correlation_id, {
          provider,
          attempt,
          error: String(err),
          elapsed_ms: elapsed
        });
        await this.sleep(backoff, signal);
        backoff = Math.min(backoff * 2, this.cfg.max_backoff_ms);
      }
    }

    // Out of attempts
    return {
      ok: false,
      provider,
      correlation_id,
      duration_ms: Date.now() - started,
      code: 'RETRY_EXHAUSTED',
      message: `Provider ${provider} failed after ${this.cfg.max_attempts_per_provider} attempts.`
    };
  }

  private async invokeProvider(
    provider: Provider,
    input: GenerationInput,
    correlation_id: string,
    signal: AbortSignal
  ): Promise<GenerationResult | GenerationError> {
    const perAttemptTimeout = input.timeout_ms ?? 20_000;
    const endpoint = this.resolveEndpoint(provider);
    if (!endpoint) {
      return {
        ok: false,
        provider,
        correlation_id,
        duration_ms: 0,
        code: 'NO_ENDPOINT',
        message: `No endpoint configured for provider: ${provider}`
      };
    }

    // Provider-specific shaping (prompt-first)
    const payload = this.buildPayload(provider, input);

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), perAttemptTimeout);
    const combined = this.mergeSignals(signal, controller.signal);

    try {
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
        'X-Correlation-Id': correlation_id,
        ...(this.cfg.buildHeaders ? this.cfg.buildHeaders() : {})
      };

      const res = await fetch(endpoint, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
        signal: combined,
        credentials: 'same-origin'
      });

      const status = res.status;
      if (!res.ok) {
        let details: any;
        try { details = await res.json(); } catch { details = await res.text(); }
        return {
          ok: false,
          provider,
          correlation_id,
          duration_ms: 0,
          status,
          code: this.classifyHttp(status),
          message: `Provider ${provider} HTTP ${status}`,
          details
        };
      }

      // Expected normalized response from backend
      const data = await res.json();
      const result: GenerationResult = {
        ok: true,
        provider,
        correlation_id,
        duration_ms: 0,
        seed: data.seed,
        image_url: data.image_url,
        mime_type: data.mime_type ?? 'image/png',
        width: data.width ?? payload.width ?? 768,
        height: data.height ?? payload.height ?? 768,
        stats: data.stats
      };
      return result;
    } finally {
      clearTimeout(timer);
    }
  }

  private trace(phase: TraceEvent['phase'], correlationId: string, extra: TraceExtras = {}): void {
    if (!this.cfg.onTrace) return;
    const { elapsed_ms = 0, phase: _ignoredPhase, correlation_id: _ignoredCorrelation, ...rest } = extra as TraceExtras & {
      phase?: TraceEvent['phase'];
      correlation_id?: string;
    };

    const event: TraceEvent = {
      phase,
      correlation_id: correlationId,
      elapsed_ms,
      ...(rest as Partial<Omit<TraceEvent, 'phase' | 'correlation_id' | 'elapsed_ms'>>)
    };

    this.cfg.onTrace(event);
  }

  private buildPayload(provider: Provider, input: GenerationInput): Record<string, any> {
    // Normalize aliases
    const guidance = input.guidance_scale ?? input.cfg ?? 7;

    const base = {
      prompt: input.prompt,
      negative_prompt: input.negative_prompt ?? '',
      width: input.width ?? 768,
      height: input.height ?? 768,
      steps: input.steps ?? 30,
      guidance_scale: guidance,
      seed: input.seed === 'random' || input.seed == null ? Math.floor(Math.random() * 2_147_483_647) : input.seed,
      sampler: input.sampler ?? 'Euler a',
      style_preset: input.style_preset,
      loras: input.loras ?? [],
      clip_skip: input.clip_skip,
      hrfix: Boolean(input.hrfix),
      enhance_prompt: Boolean(input.enhance_prompt),
      safety: input.safety ?? {},
      user_tags: input.user_tags ?? []
    };

    switch (provider) {
      case 'januxis-local':
        // Januxis backend expects SD-like payload; keep names stable
        return base;
      case 'sd-webui':
        // AUTOMATIC1111 mapping (done server-side ideally, but keep parity)
        return {
          ...base,
          enable_hr: base.hrfix,
          cfg_scale: base.guidance_scale,
          hr_scale: base.hrfix ? 1.5 : undefined
        };
      case 'gemini':
        // High-level prompt wrapper; server handles Gemini specifics
        return {
          ...base,
          model_hint: 'gemini-image-1.5',
          safety_toggles: base.safety
        };
      case 'stability':
        return {
          ...base,
          engine: 'stable-diffusion-xl-1024-v1-0'
        };
      case 'unsplash-fallback':
        return {
          query: base.prompt,
          orientation: (base.width ?? 768) >= (base.height ?? 768) ? 'landscape' : 'portrait'
        };
      default:
        return base;
    }
  }

  private resolveEndpoint(provider: Provider): string | undefined {
    switch (provider) {
      case 'januxis-local':     return this.cfg.endpoints.januxis;
      case 'sd-webui':          return this.cfg.endpoints.sd_webui;
      case 'gemini':            return this.cfg.endpoints.gemini;
      case 'stability':         return this.cfg.endpoints.stability;
      case 'unsplash-fallback': return this.cfg.endpoints.unsplash;
      default: return undefined;
    }
  }

  private classifyHttp(status?: number): string | undefined {
    if (status == null) return undefined;
    if (status === 401 || status === 403) return 'AUTHZ_ERROR';
    if (status === 408) return 'TIMEOUT';
    if (status >= 500) return 'PROVIDER_5XX';
    if (status >= 400) return 'PROVIDER_4XX';
    return 'UNKNOWN_HTTP';
  }

  private isTransient(status?: number, code?: string): boolean {
    if (status === 429) return true;
    if (status && status >= 500) return true;
    if (code === 'PROVIDER_5XX' || code === 'TIMEOUT') return true;
    return false;
  }

  private sleep(ms: number, signal?: AbortSignal): Promise<void> {
    if (!ms) return Promise.resolve();
    return new Promise((resolve, reject) => {
      const t = setTimeout(() => {
        cleanup();
        resolve();
      }, ms);
      const onAbort = () => {
        cleanup();
        reject(Object.assign(new Error('Sleep aborted'), { name: 'AbortError' }));
      };
      const cleanup = () => {
        clearTimeout(t);
        signal?.removeEventListener('abort', onAbort);
      };
      if (signal) signal.addEventListener('abort', onAbort);
    });
  }

  private mergeSignals(a?: AbortSignal, b?: AbortSignal): AbortSignal {
    if (!a) return b ?? new AbortController().signal;
    if (!b) return a;
    const c = new AbortController();
    const onAbort = () => c.abort();
    if (a.aborted || b.aborted) c.abort();
    a.addEventListener('abort', onAbort, { once: true });
    b.addEventListener('abort', onAbort, { once: true });
    return c.signal;
    // NOTE: We don't remove listeners because controller lifetime == request.
  }

  private newCorrelationId(): string {
    // Lightweight, stable-enough correlation id
    const s4 = () => Math.floor((1 + Math.random()) * 0x10000).toString(16).slice(1);
    return `img-${s4()}${s4()}-${s4()}-${s4()}-${s4()}${s4()}${s4()}`;
  }
}

// ---------- Convenience singleton & factory ----------

let _singleton: ImageGenerationService | null = null;

export function getImageGenerationService(): ImageGenerationService {
  if (_singleton) return _singleton;

  // Default wiring (aligns with your local-first philosophy)
  _singleton = new ImageGenerationService({
    endpoints: {
      januxis: '/api/images/januxis/generate',
      sd_webui: '/api/images/sd-webui/generate',
      gemini: '/api/images/gemini/generate',
      stability: '/api/images/stability/generate',
      unsplash: '/api/images/unsplash/search'
    },
    default_provider: 'januxis-local',
    fallback_chain: ['sd-webui', 'gemini', 'stability', 'unsplash-fallback'],
    hard_timeout_ms: 45_000,
    max_attempts_per_provider: 2,
    initial_backoff_ms: 350,
    max_backoff_ms: 3_000,
    buildHeaders: () => ({
      // Example: attach CSRF header if your backend uses it
      // 'X-CSRF-Token': getCsrfToken(),
    }),
    onTrace: (evt) => {
      // Minimal breadcrumbs; wire this to your telemetry bus/Prometheus if desired
      if (process.env.NODE_ENV !== 'production') {
        // eslint-disable-next-line no-console
        console.debug('[ImageGenTrace]', evt);
      }
    }
  });

  return _singleton;
}
