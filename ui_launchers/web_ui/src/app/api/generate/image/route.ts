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
  strength?: number; // For img2img
  init_image?: string; // Base64 encoded image for img2img
}
interface ImageGenerationResponse {
  success: boolean;
  images: Array<{
    url?: string;
    base64?: string;
    seed: number;
    width: number;
    height: number;
  }>;
  generation_info: {
    model_id: string;
    provider: string;
    prompt: string;
    negative_prompt?: string;
    parameters: Record<string, any>;
    generation_time: number;
  };
  error?: string;
  message?: string;
}
export async function POST(request: NextRequest) {
  try {
    const body: ImageGenerationRequest = await request.json();
    const {
      prompt,
      negative_prompt,
      model_id,
      width = 512,
      height = 512,
      steps = 20,
      guidance_scale = 7.5,
      seed = -1,
      batch_size = 1,
      strength,
      init_image
    } = body;
    if (!prompt) {
      return NextResponse.json(
        { error: 'Missing required field: prompt' },
        { status: 400 }
      );
    }
    if (batch_size > 4) {
      return NextResponse.json(
        { error: 'Batch size cannot exceed 4 images' },
        { status: 400 }
      );
    }
    console.log('🎨 Image Generation API: Generating images', {
      prompt: prompt.substring(0, 100) + (prompt.length > 100 ? '...' : ''),
      modelId: model_id,
      dimensions: `${width}x${height}`,
      steps,
      guidanceScale: guidance_scale,
      batchSize: batch_size,
      hasInitImage: !!init_image

    const { modelSelectionService } = await import('@/lib/model-selection-service');
    const startTime = Date.now();
    try {
      // Get available models to find image generation models
      const models = await modelSelectionService.getAvailableModels();
      const imageModels = models.filter(m => 
        m.type === 'image' || 
        m.capabilities?.includes('text2img') ||
        m.capabilities?.includes('image-generation')
      );
      if (imageModels.length === 0) {
        return NextResponse.json(
          {
            error: 'No image generation models available',
            message: 'Please ensure Stable Diffusion or Flux models are installed and available'
          },
          { status: 503 }
        );
      }
      // Select model - use specified model_id or first available image model
      let selectedModel = model_id 
        ? imageModels.find(m => m.id === model_id)
        : imageModels[0];
      if (!selectedModel) {
        selectedModel = imageModels[0];
      }
      // Validate model capabilities
      const isImg2Img = !!init_image;
      if (isImg2Img && !selectedModel.capabilities?.includes('img2img')) {
        return NextResponse.json(
          {
            error: 'Model does not support image-to-image generation',
            message: `Model '${selectedModel.name}' only supports text-to-image generation`
          },
          { status: 400 }
        );
      }
      // Generate parameters object
      const generationParams = {
        prompt,
        negative_prompt,
        width,
        height,
        steps,
        guidance_scale,
        seed: seed === -1 ? Math.floor(Math.random() * 2147483647) : seed,
        batch_size,
        ...(isImg2Img && { strength, init_image })
      };
      // For now, simulate image generation since we don't have actual providers integrated
      // In a real implementation, this would call the appropriate provider
      const generatedImages = await simulateImageGeneration(
        selectedModel,
        generationParams,
        batch_size
      );
      const generationTime = Date.now() - startTime;
      const response: ImageGenerationResponse = {
        success: true,
        images: generatedImages,
        generation_info: {
          model_id: selectedModel.id,
          provider: selectedModel.provider,
          prompt,
          negative_prompt,
          parameters: generationParams,
          generation_time: generationTime
        }
      };
      return NextResponse.json(response, {
        headers: {
          'X-Generation-Time': generationTime.toString(),
          'X-Model-Provider': selectedModel.provider,
          'X-Images-Generated': generatedImages.length.toString()
        }

    } catch (generationError) {
      return NextResponse.json(
        {
          error: 'Image generation failed',
          message: generationError instanceof Error ? generationError.message : 'Unknown generation error'
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
 * Simulate image generation for testing purposes
 * In a real implementation, this would call the actual image generation providers
 */
async function simulateImageGeneration(
  model: any,
  params: any,
  batchSize: number
): Promise<Array<{ url?: string; base64?: string; seed: number; width: number; height: number }>> {
  // Simulate generation time
  await new Promise(resolve => setTimeout(resolve, 2000 + Math.random() * 3000));
  const images = [];
  for (let i = 0; i < batchSize; i++) {
    images.push({
      base64: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==', // 1x1 transparent PNG
      seed: params.seed + i,
      width: params.width,
      height: params.height

  }
  return images;
}
