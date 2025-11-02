import { NextRequest, NextResponse } from 'next/server';
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
    text_generation?: Record<string, any>;
    image_generation?: Record<string, any>;
    embedding?: Record<string, any>;
  };
  compatibility: {
    multimodal: boolean;
    streaming: boolean;
    batch_processing: boolean;
  };
}
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const modelId = searchParams.get('model_id');
    const includeParameters = searchParams.get('include_parameters') === 'true';
    const includeCompatibility = searchParams.get('include_compatibility') === 'true';
    if (!modelId) {
      return NextResponse.json(
        { error: 'Missing required parameter: model_id' },
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
      // Build detailed capabilities based on model type and provider
      const capabilities = buildModelCapabilities(targetModel);
      const supportedModes = getSupportedModes(targetModel);
      const response: CapabilitiesResponse = {
        model_id: modelId,
        model_name: targetModel.name,
        provider: targetModel.provider,
        type: targetModel.type || 'unknown',
        capabilities,
        supported_modes: supportedModes,
        parameters: includeParameters ? buildParameterSpecs(targetModel) : {},
        compatibility: includeCompatibility ? buildCompatibilityInfo(targetModel) : {
          multimodal: false,
          streaming: false,
          batch_processing: false
        }
      };
      return NextResponse.json(response, {
        headers: {
          'Cache-Control': 'public, max-age=3600', // Cache for 1 hour
          'X-Model-Type': targetModel.type || 'unknown',
          'X-Model-Provider': targetModel.provider
        }
      });
    } catch (capabilityError) {
      return NextResponse.json(
        {
          error: 'Failed to fetch model capabilities',
          message: capabilityError instanceof Error ? capabilityError.message : 'Unknown error',
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
 * Build detailed capabilities for a model based on its type and metadata
 */
function buildModelCapabilities(model: any): ModelCapability[] {
  const capabilities: ModelCapability[] = [];
  // Base capabilities from model.capabilities array
  if (model.capabilities) {
    model.capabilities.forEach((cap: string) => {
      switch (cap) {
        case 'chat':
          capabilities.push({
            name: 'chat',
            description: 'Interactive conversational AI',
            supported_parameters: ['temperature', 'top_p', 'max_tokens', 'stop_sequences']
          });
          break;
        case 'text-generation':
          capabilities.push({
            name: 'text-generation',
            description: 'Generate text based on prompts',
            supported_parameters: ['temperature', 'top_p', 'top_k', 'max_tokens', 'repeat_penalty']
          });
          break;
        case 'text2img':
          capabilities.push({
            name: 'text2img',
            description: 'Generate images from text descriptions',
            supported_parameters: ['width', 'height', 'steps', 'guidance_scale', 'seed'],
            requirements: {
              memory_mb: 4000,
              gpu_required: true,
              dependencies: ['diffusers', 'torch']
            }
          });
          break;
        case 'img2img':
          capabilities.push({
            name: 'img2img',
            description: 'Transform existing images based on text prompts',
            supported_parameters: ['strength', 'width', 'height', 'steps', 'guidance_scale'],
            requirements: {
              memory_mb: 4000,
              gpu_required: true,
              dependencies: ['diffusers', 'torch', 'PIL']
            }
          });
          break;
        case 'embedding':
          capabilities.push({
            name: 'embedding',
            description: 'Generate vector embeddings for text',
            supported_parameters: ['normalize', 'batch_size']
          });
          break;
        case 'code':
          capabilities.push({
            name: 'code',
            description: 'Code generation and analysis',
            supported_parameters: ['language', 'max_tokens', 'temperature']
          });
          break;
        default:
          capabilities.push({
            name: cap,
            description: `${cap} capability`,
            supported_parameters: []
          });
      }
    });
  }
  return capabilities;
}
/**
 * Get supported interaction modes for a model
 */
function getSupportedModes(model: any): string[] {
  const modes: string[] = [];
  if (model.type === 'text' || model.type === 'text_generation') {
    modes.push('text');
    if (model.capabilities?.includes('chat')) {
      modes.push('chat');
    }
  }
  if (model.type === 'image' || model.type === 'image_generation') {
    modes.push('image');
    if (model.capabilities?.includes('text2img')) {
      modes.push('text2img');
    }
    if (model.capabilities?.includes('img2img')) {
      modes.push('img2img');
    }
  }
  if (model.type === 'embedding') {
    modes.push('embedding');
  }
  return modes;
}
/**
 * Build parameter specifications for different model types
 */
function buildParameterSpecs(model: any): Record<string, any> {
  const parameters: Record<string, any> = {};
  if (model.type === 'text' || model.type === 'text_generation') {
    parameters.text_generation = {
      temperature: { type: 'float', min: 0.0, max: 2.0, default: 0.7 },
      top_p: { type: 'float', min: 0.0, max: 1.0, default: 0.9 },
      top_k: { type: 'integer', min: 1, max: 100, default: 40 },
      max_tokens: { type: 'integer', min: 1, max: 4096, default: 512 },
      repeat_penalty: { type: 'float', min: 0.0, max: 2.0, default: 1.1 }
    };
  }
  if (model.type === 'image' || model.type === 'image_generation') {
    parameters.image_generation = {
      width: { type: 'integer', min: 256, max: 1024, default: 512, step: 64 },
      height: { type: 'integer', min: 256, max: 1024, default: 512, step: 64 },
      steps: { type: 'integer', min: 1, max: 100, default: 20 },
      guidance_scale: { type: 'float', min: 1.0, max: 20.0, default: 7.5 },
      seed: { type: 'integer', min: 0, max: 2147483647, default: -1 },
      batch_size: { type: 'integer', min: 1, max: 4, default: 1 }
    };
  }
  if (model.type === 'embedding') {
    parameters.embedding = {
      normalize: { type: 'boolean', default: true },
      batch_size: { type: 'integer', min: 1, max: 32, default: 8 }
    };
  }
  return parameters;
}
/**
 * Build compatibility information for a model
 */
function buildCompatibilityInfo(model: any): { multimodal: boolean; streaming: boolean; batch_processing: boolean } {
  return {
    multimodal: model.capabilities?.includes('multimodal') || false,
    streaming: model.provider !== 'stable-diffusion' && model.provider !== 'flux', // Image models typically don't stream
    batch_processing: true // Most models support batch processing
  };
}
