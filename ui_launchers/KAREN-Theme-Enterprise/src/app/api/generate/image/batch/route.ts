// app/api/image/generate/batch/route.ts
import { NextRequest, NextResponse } from 'next/server';

// Static export detection
function isStaticExport(): boolean {
  return (
    process.env.NEXT_PHASE === 'phase-production-build' ||
    process.env.NEXT_EXPORT === 'true' ||
    process.env.STATIC_EXPORT === 'true' ||
    (typeof window === 'undefined' && process.env.NODE_ENV === 'production')
  );
}

interface SingleImageReq {
  id?: string;
  prompt: string;
  negative_prompt?: string;
  model_id?: string;
  width?: number;
  height?: number;
  steps?: number;
  guidance_scale?: number;
  seed?: number;
  strength?: number;
  init_image?: string;
  batch_size?: number; // per-request override (defaults to 1)
}

interface BatchImageGenerationRequest {
  requests: SingleImageReq[];
  global_model_id?: string;
  priority?: 'low' | 'normal' | 'high';
  callback_url?: string;
}

interface ImageRecord {
  url?: string;
  base64?: string;
  seed: number;
  width: number;
  height: number;
}

interface BatchResultItem {
  request_id: string;
  success: boolean;
  images?: ImageRecord[];
  generation_info?: {
    model_id: string;
    provider: string;
    prompt: string;
    parameters: Record<string, unknown>;
    generation_time: number;
  };
  error?: string;
}

interface BatchImageGenerationResponse {
  success: boolean;
  batch_id: string;
  total_requests: number;
  estimated_completion_time: number; // seconds
  status: 'queued' | 'processing' | 'completed' | 'failed';
  results?: BatchResultItem[];
  error?: string;
  message?: string;
}

const LIMITS = {
  MAX_REQS: 20,
  MAX_PER_REQ_BATCH: 4,
  MIN_SIZE: 64,
  MAX_SIZE: 1536,
  MAX_AREA: 1_572_864, // ~1536x1024
  MIN_STEPS: 1,
  MAX_STEPS: 150,
  MIN_GUIDANCE: 0,
  MAX_GUIDANCE: 50,
  MIN_STRENGTH: 0,
  MAX_STRENGTH: 1,
};

const DEFAULTS = {
  WIDTH: 512,
  HEIGHT: 512,
  STEPS: 20,
  GUIDANCE: 7.5,
  PER_REQ_BATCH: 1,
  AVG_TIME_PER_IMAGE_SEC: 30, // coarse estimate
  PROCESS_TIMEOUT_MS: 60_000, // per single request generation cap (sim path uses random < 5s)
};

const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v));
const isFiniteNum = (v: unknown) => typeof v === 'number' && Number.isFinite(v);

function sanitizeDims(width?: number, height?: number) {
  const wRaw = isFiniteNum(width) ? Math.round(width as number) : DEFAULTS.WIDTH;
  const hRaw = isFiniteNum(height) ? Math.round(height as number) : DEFAULTS.HEIGHT;
  const w = clamp(wRaw, LIMITS.MIN_SIZE, LIMITS.MAX_SIZE);
  const h = clamp(hRaw, LIMITS.MIN_SIZE, LIMITS.MAX_SIZE);
  const area = w * h;
  if (area > LIMITS.MAX_AREA) {
    const scale = Math.sqrt(LIMITS.MAX_AREA / area);
    return {
      width: Math.max(LIMITS.MIN_SIZE, Math.floor(w * scale)),
      height: Math.max(LIMITS.MIN_SIZE, Math.floor(h * scale)),
    };
  }
  return { width: w, height: h };
}

function normalizeInitImage(s?: string) {
  if (!s) return undefined;
  const trimmed = s.trim();
  if (trimmed.startsWith('data:image/')) return trimmed;
  if (/^[A-Za-z0-9+/=\s]+$/.test(trimmed)) {
    return `data:image/png;base64,${trimmed.replace(/\s+/g, '')}`;
  }
  return undefined;
}

// ---------- In-memory job store (prod: move to DB/queue) ----------
type BatchStatus = 'queued' | 'processing' | 'completed' | 'failed';

const batchJobs = new Map<
  string,
  {
    id: string;
    status: BatchStatus;
    requests: (SingleImageReq & { id: string })[];
    results: BatchResultItem[];
    created_at: Date;
    completed_at?: Date;
    estimated_completion: Date;
    priority: 'low' | 'normal' | 'high';
    callback_url?: string;
  }
>();

function newBatchId() {
  return `batch_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
}

// ---------- Simulation / Provider stubs ----------
async function simulateOneRequest(req: SingleImageReq): Promise<BatchResultItem> {
  const started = Date.now();

  // Fake generation delay (2-5s), cancellable in real provider path
  const delay = 2_000 + Math.random() * 3_000;
  await new Promise((res) => setTimeout(res, delay));

  const dims = sanitizeDims(req.width, req.height);
  const perReqBatch = clamp(
    isFiniteNum(req.batch_size) ? (req.batch_size as number) : DEFAULTS.PER_REQ_BATCH,
    1,
    LIMITS.MAX_PER_REQ_BATCH
  );

  const baseSeed =
    req.seed === -1 || !isFiniteNum(req.seed)
      ? Math.floor(Math.random() * 2_147_483_647)
      : Math.floor(req.seed as number);

  const images: ImageRecord[] = [];
  for (let i = 0; i < perReqBatch; i++) {
    images.push({
      base64:
        'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==',
      seed: baseSeed + i,
      width: dims.width,
      height: dims.height,
    });
  }

  const generation_time = Date.now() - started;
  return {
    request_id: req.id!,
    success: true,
    images,
    generation_info: {
      model_id: String(req.model_id ?? 'sim-model'),
      provider: 'simulated',
      prompt: req.prompt,
      parameters: {
        width: dims.width,
        height: dims.height,
        steps: clamp(isFiniteNum(req.steps) ? (req.steps as number) : DEFAULTS.STEPS, LIMITS.MIN_STEPS, LIMITS.MAX_STEPS),
        guidance_scale: clamp(
          isFiniteNum(req.guidance_scale) ? (req.guidance_scale as number) : DEFAULTS.GUIDANCE,
          LIMITS.MIN_GUIDANCE,
          LIMITS.MAX_GUIDANCE
        ),
        seed: baseSeed,
        batch_size: perReqBatch,
        strength:
          req.init_image != null
            ? clamp(isFiniteNum(req.strength) ? (req.strength as number) : 0.65, LIMITS.MIN_STRENGTH, LIMITS.MAX_STRENGTH)
            : undefined,
        init_image: normalizeInitImage(req.init_image),
      },
      generation_time,
    },
  };
}

// ---------- Route handlers ----------
export async function POST(request: NextRequest) {
  // Skip image generation during static export
  if (isStaticExport()) {
    return NextResponse.json(
      {
        error: 'Image generation unavailable during static export',
        message: 'This endpoint is not available during static site generation'
      },
      { status: 503 }
    );
  }

  // Parse body
  let body: BatchImageGenerationRequest;
  try {
    body = (await request.json()) as BatchImageGenerationRequest;
  } catch (e) {
    return NextResponse.json(
      { error: 'Invalid request', message: e instanceof Error ? e.message : 'Malformed JSON' },
      { status: 400 }
    );
  }

  const { requests, global_model_id, priority = 'normal', callback_url } = body ?? {};
  if (!Array.isArray(requests) || requests.length === 0) {
    return NextResponse.json({ error: 'Missing or empty requests array' }, { status: 400 });
  }
  if (requests.length > LIMITS.MAX_REQS) {
    return NextResponse.json({ error: `Batch size cannot exceed ${LIMITS.MAX_REQS} requests` }, { status: 400 });
  }

  // Validate minimal fields & clamp per-request batch sizes
  for (let i = 0; i < requests.length; i++) {
    const r = requests[i];
    if (!r?.prompt || typeof r.prompt !== 'string' || !r.prompt.trim()) {
      return NextResponse.json({ error: `Request ${i + 1} is missing required field: prompt` }, { status: 400 });
    }
    if (isFiniteNum(r.batch_size) && (r.batch_size! < 1 || r.batch_size! > LIMITS.MAX_PER_REQ_BATCH)) {
      return NextResponse.json(
        { error: `Request ${i + 1} batch_size must be between 1 and ${LIMITS.MAX_PER_REQ_BATCH}` },
        { status: 400 }
      );
    }
  }

  // Discover available image models (contract check)
  try {
    const { modelSelectionService } = await import('@/lib/model-selection-service');
    const models = await modelSelectionService.getAvailableModels();
    const imageModels = (models || []).filter((item) => {
      const candidate = item as {
        type?: string;
        capabilities?: unknown;
      };
      const caps = Array.isArray(candidate.capabilities)
        ? (candidate.capabilities as string[])
        : [];
      return (
        candidate.type === 'image' ||
        caps.includes('text2img') ||
        caps.includes('image-generation')
      );
    });
    if (!imageModels.length) {
      return NextResponse.json(
        {
          error: 'No image generation models available',
          message: 'Ensure Stable Diffusion / Flux (local Januxis) is installed and enabled',
        },
        { status: 503 }
      );
    }
  } catch (err) {
    return NextResponse.json(
      { error: 'Batch setup failed', message: err instanceof Error ? err.message : 'Model discovery error' },
      { status: 500 }
    );
  }

  // Prepare batch
  const batchId = newBatchId();
  // Estimate: count total output images (sum of per-request batch_size, default 1)
  const totalImages = requests.reduce((acc, r) => acc + (isFiniteNum(r.batch_size) ? (r.batch_size as number) : 1), 0);
  const estimatedTimeSec = totalImages * DEFAULTS.AVG_TIME_PER_IMAGE_SEC;
  const estimatedCompletion = new Date(Date.now() + estimatedTimeSec * 1000);

  const normalizedRequests = requests.map((req, idx) => {
    const id = req.id || `req_${idx + 1}`;
    const perReqBatch = clamp(
      isFiniteNum(req.batch_size) ? (req.batch_size as number) : DEFAULTS.PER_REQ_BATCH,
      1,
      LIMITS.MAX_PER_REQ_BATCH
    );
    return {
      ...req,
      id,
      batch_size: perReqBatch,
      model_id: req.model_id || global_model_id || 'sim-model',
    };
  });

  batchJobs.set(batchId, {
    id: batchId,
    status: 'queued',
    requests: normalizedRequests,
    results: [],
    created_at: new Date(),
    estimated_completion: estimatedCompletion,
    priority,
    callback_url,
  });

  // Fire-and-forget processing (prod: move to worker/queue)
  processBatchAsync(batchId).catch(() => {
    const job = batchJobs.get(batchId);
    if (job) {
      job.status = 'failed';
      batchJobs.set(batchId, job);
    }
  });

  const resp: BatchImageGenerationResponse = {
    success: true,
    batch_id: batchId,
    total_requests: requests.length,
    estimated_completion_time: estimatedTimeSec,
    status: 'queued',
  };

  return new NextResponse(JSON.stringify(resp), {
    status: 202,
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'no-store',
      'X-Batch-ID': batchId,
      'X-Estimated-Time': String(estimatedTimeSec),
      Location: `/api/image/generate/batch?batch_id=${encodeURIComponent(batchId)}`,
    },
  });
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const batchId = searchParams.get('batch_id');

    if (!batchId) {
      // List recent batches
      const recent = Array.from(batchJobs.values())
        .sort((a, b) => b.created_at.getTime() - a.created_at.getTime())
        .slice(0, 10)
        .map((job) => ({
          batch_id: job.id,
          status: job.status,
          total_requests: job.requests.length,
          completed_requests: job.results.length,
          created_at: job.created_at.toISOString(),
          completed_at: job.completed_at?.toISOString(),
          estimated_completion: job.estimated_completion.toISOString(),
          priority: job.priority,
        }));

      return NextResponse.json(
        {
          recent_batches: recent,
          active_batches: recent.filter((b) => b.status === 'processing' || b.status === 'queued').length,
        },
        { status: 200 }
      );
    }

    const job = batchJobs.get(batchId);
    if (!job) {
      return NextResponse.json({ error: 'Batch not found', batch_id: batchId }, { status: 404 });
    }

    const resp: BatchImageGenerationResponse = {
      success: true,
      batch_id: job.id,
      total_requests: job.requests.length,
      estimated_completion_time: Math.max(0, Math.floor((job.estimated_completion.getTime() - Date.now()) / 1000)),
      status: job.status,
      results: job.results,
    };
    return NextResponse.json(resp, { status: 200 });
  } catch (e) {
    return NextResponse.json(
      { error: 'Status check failed', message: e instanceof Error ? e.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

// ---------- Batch processor (simulation; replace with real provider dispatch) ----------
async function processBatchAsync(batchId: string): Promise<void> {
  const job = batchJobs.get(batchId);
  if (!job) return;

  job.status = 'processing';
  batchJobs.set(batchId, job);

  const results: BatchResultItem[] = [];

  for (const req of job.requests) {
    try {
      const started = Date.now();

      // In production: pick provider by model_id/provider, enforce timeout with AbortController
      // Here: simulate
      const item = await simulateOneRequest(req);

      // Update per-request timing guardrail (soft; sim below 5s anyway)
      const elapsed = Date.now() - started;
      if (elapsed > DEFAULTS.PROCESS_TIMEOUT_MS) {
        results.push({
          request_id: req.id,
          success: false,
          error: `Generation exceeded ${Math.round(DEFAULTS.PROCESS_TIMEOUT_MS / 1000)}s limit`,
        });
      } else {
        results.push(item);
      }
    } catch (err) {
      results.push({
        request_id: req.id,
        success: false,
        error: err instanceof Error ? err.message : 'Unknown error',
      });
    }

    // Persist partial progress
    job.results = results.slice();
    batchJobs.set(batchId, job);
  }

  job.status = 'completed';
  job.completed_at = new Date();
  batchJobs.set(batchId, job);

  // Optional webhook callback
  if (job.callback_url) {
    try {
      await fetch(job.callback_url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          batch_id: batchId,
          status: job.status,
          results,
          completed_at: job.completed_at?.toISOString(),
        }),
      });
    } catch {
      // swallow callback errors; job is completed regardless
    }
  }
}
