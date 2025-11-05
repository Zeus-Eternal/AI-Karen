import { NextRequest, NextResponse } from 'next/server';

/** ---------- Types ---------- */

type IntegerParam = {
  type: 'integer';
  min: number;
  max: number;
  default: number;
  step?: number;
  description: string;
};

type FloatParam = {
  type: 'float';
  min: number;
  max: number;
  default: number;
  description: string;
};

type StringParam = {
  type: 'string';
  required: boolean;
  description: string;
  max_length?: number;
};

interface ImageModelParameters {
  model_id: string;
  model_name: string;
  provider: string;
  supported_modes: string[];
  parameters: {
    prompt: StringParam;
    negative_prompt?: StringParam;
    width: IntegerParam;
    height: IntegerParam;
    steps: IntegerParam;
    guidance_scale: FloatParam;
    seed: IntegerParam;
    batch_size: IntegerParam;
    strength?: FloatParam; // only when img2img available
  };
  presets: Array<{
    name: string;
    description: string;
    parameters: Record<string, any>;
  }>;
  limitations: {
    max_batch_size: number;
    max_resolution: number; // width * height ceiling
    memory_requirement_mb: number;
    estimated_time_per_image: number; // seconds
  };
}

/** ---------- Helpers ---------- */

function hasCap(model: any, cap: string): boolean {
  const caps = Array.isArray(model?.capabilities) ? model.capabilities : [];
  return caps.includes(cap);
}

function isImageModel(model: any): boolean {
  const t = (model?.type || '').toString().toLowerCase();
  return (
    t === 'image' ||
    t === 'image_generation' ||
    hasCap(model, 'text2img') ||
    hasCap(model, 'img2img') ||
    hasCap(model, 'image-generation') ||
    hasCap(model, 'inpainting') ||
    hasCap(model, 'outpainting')
  );
}

/** Build parameter specs based on provider & metadata */
function buildImageModelParameters(model: any): ImageModelParameters['parameters'] {
  const params: ImageModelParameters['parameters'] = {
    prompt: {
      type: 'string',
      required: true,
      description: 'Text description of the image to generate',
      max_length: 1000,
    },
    negative_prompt: {
      type: 'string',
      required: false,
      description: 'Text describing elements to avoid in the image',
      max_length: 500,
    },
    width: {
      type: 'integer',
      min: 256,
      max: 1024,
      default: 512,
      step: 64,
      description: 'Width of the generated image in pixels',
    },
    height: {
      type: 'integer',
      min: 256,
      max: 1024,
      default: 512,
      step: 64,
      description: 'Height of the generated image in pixels',
    },
    steps: {
      type: 'integer',
      min: 1,
      max: 100,
      default: 20,
      description: 'Number of denoising / sampling steps',
    },
    guidance_scale: {
      type: 'float',
      min: 0.0,
      max: 20.0,
      default: 7.5,
      description: 'Prompt adherence strength (higher = closer to prompt)',
    },
    seed: {
      type: 'integer',
      min: -1,
      max: 2147483647,
      default: -1,
      description: 'Random seed (-1 for random)',
    },
    batch_size: {
      type: 'integer',
      min: 1,
      max: 4,
      default: 1,
      description: 'Number of images to generate per batch',
    },
  };

  // img2img strength when supported
  if (hasCap(model, 'img2img')) {
    params.strength = {
      type: 'float',
      min: 0.0,
      max: 1.0,
      default: 0.8,
      description:
        'How much to transform the input image (0 = subtle edits, 1 = heavy transformation)',
    };
  }

  // Provider & base-model tuning
  const provider = (model?.provider || '').toLowerCase();

  if (provider === 'flux') {
    params.width.max = 2048;
    params.height.max = 2048;
    params.guidance_scale.min = 0.0;
    params.guidance_scale.max = 10.0;
    params.guidance_scale.default = 3.5;
  } else if (provider === 'stable-diffusion') {
    const baseModel = (model?.metadata?.base_model || '').toUpperCase();
    if (baseModel === 'SDXL') {
      params.width.max = 1536;
      params.height.max = 1536;
      params.width.default = 1024;
      params.height.default = 1024;
    }
  }

  return params;
}

function getSupportedImageModes(model: any): string[] {
  const modes: string[] = [];
  if (hasCap(model, 'text2img')) modes.push('text2img');
  if (hasCap(model, 'img2img')) modes.push('img2img');
  if (hasCap(model, 'inpainting')) modes.push('inpainting');
  if (hasCap(model, 'outpainting')) modes.push('outpainting');
  return modes.length > 0 ? modes : ['text2img'];
}

function buildImageModelPresets(
  model: any,
): Array<{ name: string; description: string; parameters: Record<string, any> }> {
  const presets = [
    {
      name: 'Quality',
      description: 'High quality with more steps and stronger guidance',
      parameters: { steps: 50, guidance_scale: 12.0, width: 512, height: 512 },
    },
    {
      name: 'Speed',
      description: 'Fast generation with fewer steps',
      parameters: { steps: 10, guidance_scale: 5.0, width: 512, height: 512 },
    },
    {
      name: 'Portrait',
      description: 'Optimized for portrait aspect',
      parameters: { steps: 25, guidance_scale: 8.0, width: 512, height: 768 },
    },
    {
      name: 'Landscape',
      description: 'Optimized for landscape aspect',
      parameters: { steps: 25, guidance_scale: 8.0, width: 768, height: 512 },
    },
  ];

  const provider = (model?.provider || '').toLowerCase();
  if (provider === 'flux') {
    presets.push({
      name: 'Flux High-Res',
      description: 'High resolution generation using Flux defaults',
      parameters: { steps: 20, guidance_scale: 3.5, width: 1024, height: 1024 },
    });
  }

  return presets;
}

function buildImageModelLimitations(model: any): ImageModelParameters['limitations'] {
  const provider = (model?.provider || '').toLowerCase();
  const baseModel = (model?.metadata?.base_model || '').toUpperCase();

  const limitations: ImageModelParameters['limitations'] = {
    max_batch_size: 4,
    max_resolution: 1024 * 1024, // pixels
    memory_requirement_mb: 4000,
    estimated_time_per_image: 30,
  };

  if (provider === 'flux') {
    limitations.max_resolution = 2048 * 2048;
    limitations.memory_requirement_mb = 8000;
    limitations.estimated_time_per_image = 45;
  } else if (provider === 'stable-diffusion' && baseModel === 'SDXL') {
    limitations.max_resolution = 1536 * 1536;
    limitations.memory_requirement_mb = 6000;
    limitations.estimated_time_per_image = 40;
  }

  return limitations;
}

/** ---------- Route Handler ---------- */

export async function GET(
  _request: NextRequest,
  ctx: { params: { model_id: string } },
) {
  try {
    const modelId = ctx?.params?.model_id;
    if (!modelId) {
      return NextResponse.json({ error: 'Missing model_id parameter' }, { status: 400 });
    }

    const { modelSelectionService } = await import('@/lib/model-selection-service');

    // pull available models from the orchestrator
    const models = await modelSelectionService.getAvailableModels();
    const target = (models || []).find((m: any) => m.id === modelId);

    if (!target) {
      return NextResponse.json(
        {
          error: 'Model not found',
          message: `Model with ID '${modelId}' not found in available models`,
        },
        { status: 404 },
      );
    }

    if (!isImageModel(target)) {
      return NextResponse.json(
        {
          error: 'Model does not support image generation',
          message: `Model '${target.name || target.id}' is not an image generation model`,
        },
        { status: 400 },
      );
    }

    const parameters = buildImageModelParameters(target);
    const presets = buildImageModelPresets(target);
    const limitations = buildImageModelLimitations(target);

    const payload: ImageModelParameters = {
      model_id: modelId,
      model_name: target.name || target.id,
      provider: target.provider,
      supported_modes: getSupportedImageModes(target),
      parameters,
      presets,
      limitations,
    };

    return NextResponse.json(payload, {
      status: 200,
      headers: {
        'Cache-Control': 'public, max-age=3600',
        'X-Model-Provider': target.provider,
        'X-Model-Type': (target.type || 'unknown').toString(),
      },
    });
  } catch (err: any) {
    return NextResponse.json(
      {
        error: 'Failed to fetch model parameters',
        message: err?.message || 'Unknown error',
      },
      { status: 500 },
    );
  }
}
