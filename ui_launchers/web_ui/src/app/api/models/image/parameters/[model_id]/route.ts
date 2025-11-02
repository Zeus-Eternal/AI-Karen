import { NextRequest, NextResponse } from 'next/server';
interface ImageModelParameters {
  model_id: string;
  model_name: string;
  provider: string;
  supported_modes: string[];
  parameters: {
    prompt: {
      type: 'string';
      required: true;
      description: string;
      max_length?: number;
    };
    negative_prompt?: {
      type: 'string';
      required: false;
      description: string;
      max_length?: number;
    };
    width: {
      type: 'integer';
      min: number;
      max: number;
      default: number;
      step: number;
      description: string;
    };
    height: {
      type: 'integer';
      min: number;
      max: number;
      default: number;
      step: number;
      description: string;
    };
    steps: {
      type: 'integer';
      min: number;
      max: number;
      default: number;
      description: string;
    };
    guidance_scale: {
      type: 'float';
      min: number;
      max: number;
      default: number;
      description: string;
    };
    seed: {
      type: 'integer';
      min: number;
      max: number;
      default: number;
      description: string;
    };
    batch_size: {
      type: 'integer';
      min: number;
      max: number;
      default: number;
      description: string;
    };
    strength?: {
      type: 'float';
      min: number;
      max: number;
      default: number;
      description: string;
    };
  };
  presets: Array<{
    name: string;
    description: string;
    parameters: Record<string, any>;
  }>;
  limitations: {
    max_batch_size: number;
    max_resolution: number;
    memory_requirement_mb: number;
    estimated_time_per_image: number;
  };
}
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ model_id: string }> }
) {
  try {
    const resolvedParams = await params;
    const modelId = resolvedParams.model_id;
    if (!modelId) {
      return NextResponse.json(
        { error: 'Missing model_id parameter' },
        { status: 400 }
      );
    }
    const { modelSelectionService } = await import('@/lib/model-selection-service');
    try {
      // Get model information
      const models = await modelSelectionService.getAvailableModels();
      const targetModel = models.find(m => m.id === modelId);
      if (!targetModel) {
        return NextResponse.json(
          {
            error: 'Model not found',
            message: `Model with ID '${modelId}' not found in available models`
          },
          { status: 404 }
        );
      }
      // Check if model supports image generation
      const isImageModel = targetModel.type === 'image' || 
                          targetModel.capabilities?.includes('text2img') ||
                          targetModel.capabilities?.includes('image-generation');
      if (!isImageModel) {
        return NextResponse.json(
          {
            error: 'Model does not support image generation',
            message: `Model '${targetModel.name}' is not an image generation model`
          },
          { status: 400 }
        );
      }
      // Build parameter specifications based on model type and provider
      const parameters = buildImageModelParameters(targetModel);
      const presets = buildImageModelPresets(targetModel);
      const limitations = buildImageModelLimitations(targetModel);
      const response: ImageModelParameters = {
        model_id: modelId,
        model_name: targetModel.name,
        provider: targetModel.provider,
        supported_modes: getSupportedImageModes(targetModel),
        parameters,
        presets,
        limitations
      };
      return NextResponse.json(response, {
        headers: {
          'Cache-Control': 'public, max-age=3600', // Cache for 1 hour
          'X-Model-Provider': targetModel.provider,
          'X-Model-Type': targetModel.type || 'unknown'
        }

    } catch (parameterError) {
      return NextResponse.json(
        {
          error: 'Failed to fetch model parameters',
          message: parameterError instanceof Error ? parameterError.message : 'Unknown error',
          model_id: modelId
        },
        { status: 500 }
      );
    }
  } catch (error) {
    return NextResponse.json(
      {
        error: 'Invalid request',
        message: error instanceof Error ? error.message : 'Request processing failed'
      },
      { status: 400 }
    );
  }
}
/**
 * Build parameter specifications for image models
 */
function buildImageModelParameters(model: any): ImageModelParameters['parameters'] {
  const baseParameters: ImageModelParameters['parameters'] = {
    prompt: {
      type: 'string',
      required: true,
      description: 'Text description of the image to generate',
      max_length: 1000
    },
    negative_prompt: {
      type: 'string',
      required: false,
      description: 'Text description of what to avoid in the image',
      max_length: 500
    },
    width: {
      type: 'integer',
      min: 256,
      max: 1024,
      default: 512,
      step: 64,
      description: 'Width of the generated image in pixels'
    },
    height: {
      type: 'integer',
      min: 256,
      max: 1024,
      default: 512,
      step: 64,
      description: 'Height of the generated image in pixels'
    },
    steps: {
      type: 'integer',
      min: 1,
      max: 100,
      default: 20,
      description: 'Number of denoising steps'
    },
    guidance_scale: {
      type: 'float',
      min: 1.0,
      max: 20.0,
      default: 7.5,
      description: 'How closely to follow the prompt (higher = more adherence)'
    },
    seed: {
      type: 'integer',
      min: 0,
      max: 2147483647,
      default: -1,
      description: 'Random seed for reproducible results (-1 for random)'
    },
    batch_size: {
      type: 'integer',
      min: 1,
      max: 4,
      default: 1,
      description: 'Number of images to generate in one batch'
    }
  };
  // Add img2img specific parameters if supported
  if (model.capabilities?.includes('img2img')) {
    baseParameters.strength = {
      type: 'float',
      min: 0.0,
      max: 1.0,
      default: 0.8,
      description: 'How much to transform the input image (0 = no change, 1 = complete transformation)'
    };
  }
  // Adjust parameters based on provider
  if (model.provider === 'flux') {
    // Flux models typically support higher resolutions
    baseParameters.width.max = 2048;
    baseParameters.height.max = 2048;
    baseParameters.guidance_scale.min = 0.0;
    baseParameters.guidance_scale.max = 10.0;
    baseParameters.guidance_scale.default = 3.5;
  } else if (model.provider === 'stable-diffusion') {
    // Standard Stable Diffusion parameters
    if (model.metadata?.base_model === 'SDXL') {
      baseParameters.width.max = 1536;
      baseParameters.height.max = 1536;
      baseParameters.width.default = 1024;
      baseParameters.height.default = 1024;
    }
  }
  return baseParameters;
}
/**
 * Get supported image generation modes for a model
 */
function getSupportedImageModes(model: any): string[] {
  const modes: string[] = [];
  if (model.capabilities?.includes('text2img')) {
    modes.push('text2img');
  }
  if (model.capabilities?.includes('img2img')) {
    modes.push('img2img');
  }
  if (model.capabilities?.includes('inpainting')) {
    modes.push('inpainting');
  }
  if (model.capabilities?.includes('outpainting')) {
    modes.push('outpainting');
  }
  return modes.length > 0 ? modes : ['text2img']; // Default to text2img
}
/**
 * Build preset configurations for image models
 */
function buildImageModelPresets(model: any): Array<{ name: string; description: string; parameters: Record<string, any> }> {
  const presets = [
    {
      name: 'Quality',
      description: 'High quality with more steps and higher guidance',
      parameters: {
        steps: 50,
        guidance_scale: 12.0,
        width: 512,
        height: 512
      }
    },
    {
      name: 'Speed',
      description: 'Fast generation with fewer steps',
      parameters: {
        steps: 10,
        guidance_scale: 5.0,
        width: 512,
        height: 512
      }
    },
    {
      name: 'Portrait',
      description: 'Optimized for portrait images',
      parameters: {
        steps: 25,
        guidance_scale: 8.0,
        width: 512,
        height: 768
      }
    },
    {
      name: 'Landscape',
      description: 'Optimized for landscape images',
      parameters: {
        steps: 25,
        guidance_scale: 8.0,
        width: 768,
        height: 512
      }
    }
  ];
  // Add provider-specific presets
  if (model.provider === 'flux') {
    presets.push({
      name: 'Flux High-Res',
      description: 'High resolution generation with Flux',
      parameters: {
        steps: 20,
        guidance_scale: 3.5,
        width: 1024,
        height: 1024
      }

  }
  return presets;
}
/**
 * Build limitation information for image models
 */
function buildImageModelLimitations(model: any): ImageModelParameters['limitations'] {
  const baseLimitations = {
    max_batch_size: 4,
    max_resolution: 1024 * 1024, // 1MP
    memory_requirement_mb: 4000,
    estimated_time_per_image: 30 // seconds
  };
  // Adjust based on provider
  if (model.provider === 'flux') {
    baseLimitations.max_resolution = 2048 * 2048; // 4MP
    baseLimitations.memory_requirement_mb = 8000;
    baseLimitations.estimated_time_per_image = 45;
  } else if (model.provider === 'stable-diffusion') {
    if (model.metadata?.base_model === 'SDXL') {
      baseLimitations.max_resolution = 1536 * 1536;
      baseLimitations.memory_requirement_mb = 6000;
      baseLimitations.estimated_time_per_image = 40;
    }
  }
  return baseLimitations;
}
