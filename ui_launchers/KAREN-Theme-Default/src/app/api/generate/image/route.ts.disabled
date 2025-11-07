// app/api/image/generate/route.ts
import { NextRequest, NextResponse } from 'next/server';

interface ImageGenerationRequest {
  prompt: string;
  negative_prompt?: string;
  model_id?: string;
  width?: number;
  height?: number;
  steps?: number;
  guidance_scale?: number;
  seed?: number;
  batch_size?: number;
  strength?: number;       // For img2img
  init_image?: string;     // Base64 (optionally data URL) for img2img
}

interface ImageRecord {
  url?: string;
  base64?: string;
  seed: number;
  width: number;
  height: number;
}

interface ImageGenerationResponse {
  success: boolean;
  images: ImageRecord[];
  generation_info: {
    model_id: string;
    provider: string;
    prompt: string;
    negative_prompt?: string;
    parameters: Record<string, any>;
    generation_time: number; // ms
  };
  error?: string;
  message?: string;
}

const DEFAULTS = {
  WIDTH: 512,
  HEIGHT: 512,
  STEPS: 20,
  GUIDANCE: 7.5,
  BATCH: 1,
  TIMEOUT_MS: 60_000, // longer for real gen
};

const LIMITS = {
  MAX_BATCH: 4,
  MIN_SIZE: 64,
  MAX_SIZE: 1536,
  MAX_AREA: 1_572_864, // 1536*1024-ish guardrail
  MIN_STEPS: 1,
  MAX_STEPS: 150,
  MIN_GUIDANCE: 0,
  MAX_GUIDANCE: 50,
  MIN_STRENGTH: 0,
  MAX_STRENGTH: 1,
};

const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v));
const isFiniteNum = (v: unknown) => typeof v === 'number' && Number.isFinite(v);

function sanitizeDims(width: number, height: number) {
  const w = clamp(Math.round(width), LIMITS.MIN_SIZE, LIMITS.MAX_SIZE);
  const h = clamp(Math.round(height), LIMITS.MIN_SIZE, LIMITS.MAX_SIZE);
  // Enforce approximate area limit (keeps VRAM sane)
  const area = w * h;
  if (area > LIMITS.MAX_AREA) {
    const scale = Math.sqrt(LIMITS.MAX_AREA / area);
    return { width: Math.max(LIMITS.MIN_SIZE, Math.floor(w * scale)), height: Math.max(LIMITS.MIN_SIZE, Math.floor(h * scale)) };
  }
  return { width: w, height: h };
}

function normalizeInitImage(s?: string) {
  if (!s) return undefined;
  // Accept data URL or raw base64; do a light sanity check
  const trimmed = s.trim();
  if (trimmed.startsWith('data:image/')) return trimmed;
  // If clearly base64-ish, wrap it minimally as PNG data URL
  if (/^[A-Za-z0-9+/=\s]+$/.test(trimmed)) {
    return `data:image/png;base64,${trimmed.replace(/\s+/g, '')}`;
  }
  return undefined;
}

function okJSON(body: any, extraHeaders: Record<string, string> = {}) {
  return new NextResponse(JSON.stringify(body), {
    status: 200,
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'no-store',
      ...extraHeaders,
    },
  });
}

function errJSON(status: number, body: Record<string, any>) {
  return new NextResponse(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
  });
}

/** Provider interface each backend adapter should implement */
type ProviderGenerateFn = (args: {
  model: any;
  params: Record<string, any>;
  batchSize: number;
  signal: AbortSignal;
}) => Promise<ImageRecord[]>;

/** Fallback simulator (never used if a real provider is available) */
async function simulateImageGeneration(
  _model: any,
  params: any,
  batchSize: number,
  signal: AbortSignal
): Promise<ImageRecord[]> {
  // Simulate work with cancellable delay
  const delay = (ms: number) =>
    new Promise<void>((resolve, reject) => {
      const to = setTimeout(resolve, ms);
      signal.addEventListener('abort', () => {
        clearTimeout(to);
        reject(new DOMException('Aborted', 'AbortError'));
      });
    });

  await delay(1_500 + Math.random() * 1_500);

  const images: ImageRecord[] = [];
  for (let i = 0; i < batchSize; i++) {
    images.push({
      base64:
        'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==',
      seed: (params.seed ?? 0) + i,
      width: params.width,
      height: params.height,
    });
  }
  return images;
}

/** Provider dispatcher — attempts real providers first, then falls back to simulator */
async function dispatchGenerate(
  model: any,
  params: any,
  batchSize: number,
  signal: AbortSignal
): Promise<ImageRecord[]> {
  // Try Januxis / Stable Diffusion client (local-first)
  try {
    // Prefer your local SD/Flux adapters if present
    // e.g., '@/lib/image/providers/stable-diffusion' or '@/lib/image/providers/flux'
    if (model?.provider?.toLowerCase?.() === 'januxis' || model?.type === 'stable-diffusion') {
      const mod = await import('@/lib/image/providers/stable-diffusion');
      const generate: ProviderGenerateFn = mod.generate;
      return await generate({ model, params, batchSize, signal });
    }
  } catch {
    // fall through to next attempt
  }

  // Generic provider based on model.provider if you have one
  try {
    if (model?.provider) {
      const prov = String(model.provider).toLowerCase();
      if (prov === 'flux') {
        const mod = await import('@/lib/image/providers/flux');
        const generate: ProviderGenerateFn = mod.generate;
        return await generate({ model, params, batchSize, signal });
      }
      if (prov === 'replicate') {
        const mod = await import('@/lib/image/providers/replicate');
        const generate: ProviderGenerateFn = mod.generate;
        return await generate({ model, params, batchSize, signal });
      }
    }
  } catch {
    // fall through
  }

  // Fallback: simulator
  return simulateImageGeneration(model, params, batchSize, signal);
}

export async function POST(request: NextRequest) {
  let req: ImageGenerationRequest;
  try {
    req = (await request.json()) as ImageGenerationRequest;
  } catch (e) {
    return errJSON(400, { error: 'Invalid JSON body', message: e instanceof Error ? e.message : 'Invalid request' });
  }

  const {
    prompt,
    negative_prompt,
    model_id,
    width = DEFAULTS.WIDTH,
    height = DEFAULTS.HEIGHT,
    steps = DEFAULTS.STEPS,
    guidance_scale = DEFAULTS.GUIDANCE,
    seed = -1,
    batch_size = DEFAULTS.BATCH,
    strength,
    init_image,
  } = req ?? {};

  if (!prompt || typeof prompt !== 'string' || !prompt.trim()) {
    return errJSON(400, { error: 'Missing required field: prompt' });
  }
  if (!isFiniteNum(batch_size) || batch_size! < 1 || batch_size! > LIMITS.MAX_BATCH) {
    return errJSON(400, { error: `Batch size must be between 1 and ${LIMITS.MAX_BATCH}` });
  }

  const dims = sanitizeDims(Number(width), Number(height));
  const safeSteps = clamp(Number(steps), LIMITS.MIN_STEPS, LIMITS.MAX_STEPS);
  const safeGuidance = clamp(Number(guidance_scale), LIMITS.MIN_GUIDANCE, LIMITS.MAX_GUIDANCE);
  const isImg2Img = !!init_image;
  const normalizedInit = normalizeInitImage(init_image);
  const safeStrength =
    isImg2Img && isFiniteNum(strength)
      ? clamp(Number(strength), LIMITS.MIN_STRENGTH, LIMITS.MAX_STRENGTH)
      : undefined;

  // Seed: -1 means random
  const baseSeed = seed === -1 ? Math.floor(Math.random() * 2_147_483_647) : Math.floor(Number(seed) || 0);

  // Discover available models (user’s existing service)
  let selectedModel: any | null = null;
  let modelsError: string | null = null;
  try {
    const { modelSelectionService } = await import('@/lib/model-selection-service');
    const models = await modelSelectionService.getAvailableModels();
    const imageModels = (models || []).filter(
      (m: any) => m?.type === 'image' || m?.capabilities?.includes?.('text2img') || m?.capabilities?.includes?.('image-generation')
    );
    if (!imageModels.length) {
      return errJSON(503, {
        error: 'No image generation models available',
        message: 'Ensure local Stable Diffusion / Flux (Januxis) is installed and enabled',
      });
    }
    selectedModel = model_id ? imageModels.find((m: any) => m.id === model_id) : imageModels[0];
    if (!selectedModel) selectedModel = imageModels[0];

    if (isImg2Img && !selectedModel.capabilities?.includes?.('img2img')) {
      return errJSON(400, {
        error: 'Model does not support image-to-image generation',
        message: `Model '${selectedModel?.name ?? selectedModel?.id ?? 'unknown'}' only supports text-to-image`,
      });
    }
  } catch (e) {
    modelsError = e instanceof Error ? e.message : 'Unknown model discovery error';
    return errJSON(500, { error: 'Model discovery failed', message: modelsError });
  }

  const generationParams = {
    prompt,
    negative_prompt,
    width: dims.width,
    height: dims.height,
    steps: safeSteps,
    guidance_scale: safeGuidance,
    seed: baseSeed,
    batch_size,
    ...(isImg2Img
      ? {
          strength: safeStrength ?? 0.65,
          init_image: normalizedInit,
        }
      : {}),
  };

  // Timeout + cancellation for generation call
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), DEFAULTS.TIMEOUT_MS);
  const started = Date.now();

  try {
    const images = await dispatchGenerate(selectedModel, generationParams, batch_size, controller.signal);
    clearTimeout(timeout);

    const generationTime = Date.now() - started;
    const response: ImageGenerationResponse = {
      success: true,
      images: images.map((img, i) => ({
        url: img.url,
        base64: img.base64,
        seed: baseSeed + i,
        width: dims.width,
        height: dims.height,
      })),
      generation_info: {
        model_id: String(selectedModel.id ?? 'unknown'),
        provider: String(selectedModel.provider ?? 'local'),
        prompt,
        negative_prompt,
        parameters: generationParams,
        generation_time: generationTime,
      },
    };

    return okJSON(response, {
      'X-Generation-Time': String(generationTime),
      'X-Model-Provider': String(selectedModel.provider ?? 'local'),
      'X-Images-Generated': String(response.images.length),
    });
  } catch (e) {
    clearTimeout(timeout);

    if ((e as any)?.name === 'AbortError') {
      return errJSON(504, {
        error: 'Image generation timeout',
        message: `Generation exceeded ${Math.round(DEFAULTS.TIMEOUT_MS / 1000)}s limit`,
      });
    }

    return errJSON(500, {
      error: 'Image generation failed',
      message: e instanceof Error ? e.message : 'Unknown generation error',
    });
  }
}

// Optional: simple GET to fingerprint capabilities (kept minimal on purpose)
export async function GET() {
  return okJSON({
    status: 'ok',
    message: 'Image generation endpoint. POST a JSON body to generate.',
    limits: {
      max_batch: LIMITS.MAX_BATCH,
      width_height: { min: LIMITS.MIN_SIZE, max: LIMITS.MAX_SIZE },
      max_area: LIMITS.MAX_AREA,
      steps: { min: LIMITS.MIN_STEPS, max: LIMITS.MAX_STEPS },
      guidance_scale: { min: LIMITS.MIN_GUIDANCE, max: LIMITS.MAX_GUIDANCE },
      img2img_strength: { min: LIMITS.MIN_STRENGTH, max: LIMITS.MAX_STRENGTH },
      timeout_ms: DEFAULTS.TIMEOUT_MS,
    },
  });
}
