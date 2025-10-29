import { NextRequest, NextResponse } from 'next/server';

interface LoadModelRequest {
  model_id: string;
  provider?: string;
  options?: {
    preserve_context?: boolean;
    force_reload?: boolean;
    memory_limit?: number;
  };
}

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

export async function POST(request: NextRequest) {
  console.log('🔄 Model Load API: Request received');

  try {
    const body: LoadModelRequest = await request.json();
    const { model_id, provider, options = {} } = body;

    if (!model_id) {
      return NextResponse.json(
        { error: 'Missing required field: model_id' },
        { status: 400 }
      );
    }

    console.log('🔄 Model Load API: Loading model', {
      modelId: model_id,
      provider,
      options
    });

    // Import ModelSelectionService for model loading
    const { modelSelectionService } = await import('@/lib/model-selection-service');

    const startTime = Date.now();

    try {
      // Get model information first
      const models = await modelSelectionService.getAvailableModels();
      const targetModel = models.find(m => m.id === model_id);

      if (!targetModel) {
        return NextResponse.json(
          { 
            error: 'Model not found',
            message: `Model with ID '${model_id}' not found in available models`
          },
          { status: 404 }
        );
      }

      // Note: Model loading status check would go here in a full implementation

      // Note: Model loading would be implemented here
      // For now, we'll simulate a successful load
      const loadResult: { success: boolean; model?: any; error?: string } = {
        success: true,
        model: targetModel
      };

      const loadTime = Date.now() - startTime;

      if (loadResult.success) {
        const response: LoadModelResponse = {
          success: true,
          model_id,
          provider: targetModel.provider,
          load_time: loadTime,
          capabilities: targetModel.capabilities || [],
          message: 'Model loaded successfully'
        };

        console.log('🔄 Model Load API: Model loaded successfully', {
          modelId: model_id,
          loadTime,
          provider: targetModel.provider
        });

        return NextResponse.json(response, {
          headers: {
            'X-Load-Time': loadTime.toString(),
            'X-Model-Provider': targetModel.provider
          }
        });
      } else {
        return NextResponse.json(
          {
            error: 'Model loading failed',
            message: loadResult.error || 'Unknown loading error',
            model_id
          },
          { status: 500 }
        );
      }

    } catch (loadError) {
      console.error('🔄 Model Load API: Loading error', loadError);
      
      return NextResponse.json(
        {
          error: 'Model loading failed',
          message: loadError instanceof Error ? loadError.message : 'Unknown loading error',
          model_id
        },
        { status: 500 }
      );
    }

  } catch (error) {
    console.error('🔄 Model Load API: Request error', error);
    
    return NextResponse.json(
      {
        error: 'Invalid request',
        message: error instanceof Error ? error.message : 'Request processing failed'
      },
      { status: 400 }
    );
  }
}

export async function GET(request: NextRequest) {
  console.log('🔄 Model Load API: Status check requested');

  try {
    // Get current model loading status
    const { modelSelectionService } = await import('@/lib/model-selection-service');
    const stats = await modelSelectionService.getSelectionStats();

    const response = {
      currently_loaded: stats.lastSelectedModel || null,
      loading_status: false, // This would be tracked separately
      last_load_time: null, // This would be tracked separately
      available_providers: ['llama-cpp', 'transformers', 'stable-diffusion', 'flux'],
      system_resources: {
        // Basic system info - can be enhanced with actual resource monitoring
        memory_available: true,
        gpu_available: false // This would be determined by actual system checks
      }
    };

    return NextResponse.json(response);

  } catch (error) {
    console.error('🔄 Model Load API: Status check error', error);
    
    return NextResponse.json(
      {
        error: 'Status check failed',
        message: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}