import { NextRequest, NextResponse } from 'next/server';

/** ---------------- Types ---------------- */

interface ModelCapability {
  name: string;
  description: string;
  supported_parameters?: string[];
  requirements?: {
    memory_mb?: number;
    gpu_required?: boolean;
    dependencies?: string[];
  };
}

interface CapabilitiesResponse {
  model_id: string;
  model_name: string;
  provider: string;
  type: string;
  capabilities: ModelCapability[];
  supported_modes: string[];
  parameters: {
    text_generation?: Record<string, unknown>;
    image_generation?: Record<string, unknown>;
    embedding?: Record<string, unknown>;
  };
  compatibility: {
    multimodal: boolean;
    streaming: boolean;
    batch_processing: boolean;
  };
}

/** ---------------- Utilities ---------------- */

function arr(val: unknown): unknown[] {
  return Array.isArray(val) ? val : [];
}

function getCapabilities(model: unknown): unknown[] {
  if (typeof model === 'object' && model !== null && 'capabilities' in model) {
    return arr((model as { capabilities?: unknown }).capabilities);
  }
  return [];
}

function hasCap(model: unknown, cap: string): boolean {
  return getCapabilities(model).includes(cap);
}

function normType(model: unknown): string {
  if (typeof model === 'object' && model !== null && 'type' in model) {
    return String((model as { type?: unknown }).type ?? 'unknown');
  }
  return 'unknown';
}

/** Build detailed capabilities for a model based on its type and metadata */
function buildModelCapabilities(model: unknown): ModelCapability[] {
  const capabilities: ModelCapability[] = [];
  const caps = getCapabilities(model).filter(
    (item): item is string => typeof item === "string"
  );

  for (const cap of caps) {
    switch (cap) {
      case 'chat':
        capabilities.push({
          name: 'chat',
          description: 'Interactive conversational AI',
          supported_parameters: ['temperature', 'top_p', 'max_tokens', 'stop_sequences'],
        });
        break;

      case 'text-generation':
        capabilities.push({
          name: 'text-generation',
          description: 'Generate text based on prompts',
          supported_parameters: ['temperature', 'top_p', 'top_k', 'max_tokens', 'repeat_penalty'],
        });
        break;

      case 'text2img':
        capabilities.push({
          name: 'text2img',
          description: 'Generate images from text descriptions',
          supported_parameters: ['width', 'height', 'steps', 'guidance_scale', 'seed', 'batch_size'],
          requirements: {
            memory_mb: 4000,
            gpu_required: true,
            dependencies: ['diffusers', 'torch'],
          },
        });
        break;

      case 'img2img':
        capabilities.push({
          name: 'img2img',
          description: 'Transform existing images based on text prompts',
          supported_parameters: ['strength', 'width', 'height', 'steps', 'guidance_scale', 'batch_size'],
          requirements: {
            memory_mb: 4000,
            gpu_required: true,
            dependencies: ['diffusers', 'torch', 'PIL'],
          },
        });
        break;

      case 'embedding':
        capabilities.push({
          name: 'embedding',
          description: 'Generate vector embeddings for text',
          supported_parameters: ['normalize', 'batch_size'],
        });
        break;

      case 'code':
        capabilities.push({
          name: 'code',
          description: 'Code generation and analysis',
          supported_parameters: ['language', 'max_tokens', 'temperature'],
        });
        break;

      default:
        capabilities.push({
          name: cap,
          description: `${cap} capability`,
          supported_parameters: [],
        });
        break;
    }
  }

  // If model exposes no declared caps, infer a minimum based on type
  if (capabilities.length === 0) {
    const t = normType(model);
    if (t === 'text' || t === 'text_generation') {
      capabilities.push({
        name: 'text-generation',
        description: 'Generate text based on prompts',
        supported_parameters: ['temperature', 'top_p', 'top_k', 'max_tokens', 'repeat_penalty'],
      });
    } else if (t === 'image' || t === 'image_generation') {
      capabilities.push({
        name: 'text2img',
        description: 'Generate images from text descriptions',
        supported_parameters: ['width', 'height', 'steps', 'guidance_scale', 'seed', 'batch_size'],
        requirements: { memory_mb: 4000, gpu_required: true, dependencies: ['diffusers', 'torch'] },
      });
    } else if (t === 'embedding') {
      capabilities.push({
        name: 'embedding',
        description: 'Generate vector embeddings for text',
        supported_parameters: ['normalize', 'batch_size'],
      });
    }
  }

  return capabilities;
}

/** Get supported interaction modes for a model */
function getSupportedModes(model: unknown): string[] {
  const modes: string[] = [];
  const t = normType(model);

  if (t === 'text' || t === 'text_generation') {
    modes.push('text');
    if (hasCap(model, 'chat')) modes.push('chat');
  }
  if (t === 'image' || t === 'image_generation') {
    modes.push('image');
    if (hasCap(model, 'text2img')) modes.push('text2img');
    if (hasCap(model, 'img2img')) modes.push('img2img');
  }
  if (t === 'embedding') {
    modes.push('embedding');
  }

  // If none inferred but capabilities exist, map a sane default
  if (modes.length === 0) {
    if (hasCap(model, 'text2img') || hasCap(model, 'img2img')) modes.push('image');
    if (hasCap(model, 'text-generation') || hasCap(model, 'chat')) modes.push('text');
    if (hasCap(model, 'embedding')) modes.push('embedding');
  }

  return Array.from(new Set(modes));
}

/** Build parameter specifications for different model types */
function buildParameterSpecs(model: unknown): Record<string, any> {
  const params: Record<string, any> = {};
  const t = normType(model);

  if (t === 'text' || t === 'text_generation' || hasCap(model, 'text-generation') || hasCap(model, 'chat')) {
    params.text_generation = {
      temperature: { type: 'float', min: 0.0, max: 2.0, default: 0.7 },
      top_p: { type: 'float', min: 0.0, max: 1.0, default: 0.9 },
      top_k: { type: 'integer', min: 1, max: 100, default: 40 },
      max_tokens: { type: 'integer', min: 1, max: 4096, default: 512 },
      repeat_penalty: { type: 'float', min: 0.0, max: 2.0, default: 1.1 },
      stop_sequences: { type: 'array', items: 'string', default: [] },
    };
  }

  if (t === 'image' || t === 'image_generation' || hasCap(model, 'text2img') || hasCap(model, 'img2img')) {
    params.image_generation = {
      width: { type: 'integer', min: 256, max: 1024, default: 512, step: 64 },
      height: { type: 'integer', min: 256, max: 1024, default: 512, step: 64 },
      steps: { type: 'integer', min: 1, max: 100, default: 20 },
      guidance_scale: { type: 'float', min: 1.0, max: 20.0, default: 7.5 },
      seed: { type: 'integer', min: -1, max: 2147483647, default: -1 },
      batch_size: { type: 'integer', min: 1, max: 4, default: 1 },
    };
    if (hasCap(model, 'img2img')) {
      params.image_generation.strength = { type: 'float', min: 0.0, max: 1.0, default: 0.8 };
    }

    // Provider-aware tuning examples
    const provider = String(
      (model as { provider?: unknown })?.provider ?? ''
    ).toLowerCase();
    const baseModel = String(
      (model as { metadata?: { base_model?: unknown } })?.metadata?.base_model ?? ''
    ).toUpperCase();

    if (provider === 'flux') {
      params.image_generation.guidance_scale.min = 0.0;
      params.image_generation.guidance_scale.max = 10.0;
      params.image_generation.guidance_scale.default = 3.5;
      params.image_generation.width.max = 2048;
      params.image_generation.height.max = 2048;
    } else if (provider === 'stable-diffusion' && baseModel === 'SDXL') {
      params.image_generation.width.max = 1536;
      params.image_generation.height.max = 1536;
      params.image_generation.width.default = 1024;
      params.image_generation.height.default = 1024;
    }
  }

  if (t === 'embedding' || hasCap(model, 'embedding')) {
    params.embedding = {
      normalize: { type: 'boolean', default: true },
      batch_size: { type: 'integer', min: 1, max: 64, default: 16 },
    };
  }

  return params;
}

/** Build compatibility information for a model */
function buildCompatibilityInfo(model: unknown): {
  multimodal: boolean;
  streaming: boolean;
  batch_processing: boolean;
} {
  const provider = String(
    (model as { provider?: unknown })?.provider ?? ''
  ).toLowerCase();
  const t = normType(model);

  // Heuristics: many image backends don’t stream tokens; text often can.
  const streaming =
    t === 'text' || t === 'text_generation' || hasCap(model, 'chat') || hasCap(model, 'text-generation')
      ? true
      : !(provider === 'stable-diffusion' || provider === 'flux');

  return {
    multimodal: hasCap(model, 'multimodal') || (hasCap(model, 'text2img') && (hasCap(model, 'chat') || hasCap(model, 'text-generation'))) || false,
    streaming,
    batch_processing: true,
  };
}

/** ---------------- Route ---------------- */

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const modelId = searchParams.get('model_id');
    const includeParameters = searchParams.get('include_parameters') === 'true';
    const includeCompatibility = searchParams.get('include_compatibility') === 'true';

    if (!modelId) {
      return NextResponse.json({ error: 'Missing required parameter: model_id' }, { status: 400 });
    }

    const { modelSelectionService } = await import('@/lib/model-selection-service');

    // Fetch available models and locate target
    const models = await modelSelectionService.getAvailableModels();
    const targetModel = (models || []).find(
      (m) => (m as { id?: string }).id === modelId
    );

    if (!targetModel) {
      return NextResponse.json(
        {
          error: 'Model not found',
          message: `Model with ID '${modelId}' not found in available models`,
        },
        { status: 404 },
      );
    }

    const capabilities = buildModelCapabilities(targetModel);
    const supportedModes = getSupportedModes(targetModel);

    const response: CapabilitiesResponse = {
      model_id: modelId,
      model_name: targetModel.name || modelId,
      provider: targetModel.provider,
      type: normType(targetModel),
      capabilities,
      supported_modes: supportedModes,
      parameters: includeParameters ? buildParameterSpecs(targetModel) : {},
      compatibility: includeCompatibility
        ? buildCompatibilityInfo(targetModel)
        : { multimodal: false, streaming: false, batch_processing: false },
    };

    return NextResponse.json(response, {
      status: 200,
      headers: {
        'Cache-Control': 'public, max-age=3600',
        'X-Model-Type': response.type,
        'X-Model-Provider': response.provider,
      },
    });
  } catch (capabilityError: unknown) {
    const capabilityMessage =
      capabilityError instanceof Error ? capabilityError.message : 'Unknown error';
    return NextResponse.json(
      {
        error: 'Failed to fetch model capabilities',
        message: capabilityMessage,
      },
      { status: 500 },
    );
  }
}
