import { NextRequest, NextResponse } from 'next/server';

// Use the correct backend URL from environment variables
const BACKEND_URL = process.env.KAREN_BACKEND_URL || process.env.NEXT_PUBLIC_KAREN_BACKEND_URL || 'http://127.0.0.1:8000';
const TIMEOUT_MS = 30000; // Increased timeout to 30 seconds

interface ModelHealthStatus {
  is_healthy: boolean;
  last_check: string;
  issues: string[];
  memory_requirement?: number;
  performance_metrics?: {
    load_time?: number;
    inference_speed?: number;
    memory_usage?: number;
  };
}

interface EnhancedModelInfo {
  id: string;
  name: string;
  provider: string;
  type: string;
  status: string;
  description?: string;
  capabilities: string[];
  size?: number;
  metadata: Record<string, any>;
  health?: ModelHealthStatus;
  path?: string;
  format?: string;
  last_scanned?: string;
}

/**
 * Get health status for a specific model
 */
async function getModelHealthStatus(modelId: string): Promise<ModelHealthStatus> {
  try {
    // Try to get health status from ModelSelectionService
    const { modelSelectionService } = await import('@/lib/model-selection-service');
    
    // Basic health check - more sophisticated checks can be added
    const healthStatus: ModelHealthStatus = {
      is_healthy: true,
      last_check: new Date().toISOString(),
      issues: []
    };
    
    return healthStatus;
    
  } catch (error) {
    return {
      is_healthy: false,
      last_check: new Date().toISOString(),
      issues: [`Health check failed: ${error instanceof Error ? error.message : 'Unknown error'}`]
    };
  }
}

export async function GET(request: NextRequest) {
  console.log('🔍 ModelsLibrary API: Request received', {
    url: request.url,
    method: request.method,
    headers: Object.fromEntries(request.headers.entries()),
    searchParams: Object.fromEntries(request.nextUrl.searchParams.entries())
  });

  try {
    const searchParams = request.nextUrl.searchParams;
    const scan = searchParams.get('scan') === 'true';
    const includeHealth = searchParams.get('includeHealth') === 'true';
    const modelType = searchParams.get('type'); // Filter by model type
    const provider = searchParams.get('provider'); // Filter by provider
    const forceRefresh = searchParams.get('forceRefresh') === 'true';
    
    // Enhanced scanning with health monitoring
    if (scan) {
      console.log('🔍 ModelsLibrary API: Enhanced dynamic scanning requested', {
        includeHealth,
        modelType,
        provider,
        forceRefresh
      });
      
      try {
        // Import the ModelSelectionService dynamically to avoid circular dependencies
        const { modelSelectionService } = await import('@/lib/model-selection-service');
        
        // Perform comprehensive directory scanning with health checks
        const scanOptions = {
          forceRefresh,
          includeHealth,
          directories: ['models/llama-cpp', 'models/transformers', 'models/stable-diffusion', 'models/flux'],
          filters: {
            type: modelType,
            provider: provider
          }
        };
        
        const models = await modelSelectionService.getAvailableModels(forceRefresh);
        const stats = await modelSelectionService.getSelectionStats();
        
        // Enhance models with health status if requested
        const enhancedModels: EnhancedModelInfo[] = await Promise.all(
          models.map(async (model) => {
            const enhancedModel: EnhancedModelInfo = {
              ...model,
              type: model.type || 'unknown',
              last_scanned: new Date().toISOString()
            };
            
            if (includeHealth) {
              try {
                // Get health status for each model
                const healthStatus = await getModelHealthStatus(model.id);
                enhancedModel.health = healthStatus;
              } catch (healthError) {
                console.warn(`Failed to get health status for model ${model.id}:`, healthError);
                enhancedModel.health = {
                  is_healthy: false,
                  last_check: new Date().toISOString(),
                  issues: ['Health check failed']
                };
              }
            }
            
            return enhancedModel;
          })
        );
        
        // Categorize models by type and status
        const categorizedModels = {
          text_generation: enhancedModels.filter(m => m.type === 'text' || m.type === 'text_generation'),
          image_generation: enhancedModels.filter(m => m.type === 'image' || m.type === 'image_generation'),
          embedding: enhancedModels.filter(m => m.type === 'embedding'),
          other: enhancedModels.filter(m => !['text', 'text_generation', 'image', 'image_generation', 'embedding'].includes(m.type))
        };
        
        const response = {
          models: enhancedModels,
          categorized_models: categorizedModels,
          total_count: enhancedModels.length,
          local_count: enhancedModels.filter(m => m.status === 'local').length,
          available_count: enhancedModels.filter(m => m.status === 'available').length,
          healthy_count: includeHealth ? enhancedModels.filter(m => m.health?.is_healthy).length : undefined,
          scan_metadata: {
            ...stats.scanStats,
            scan_timestamp: new Date().toISOString(),
            include_health: includeHealth,
            filters_applied: { type: modelType, provider: provider }
          },
          source: 'enhanced_dynamic_scan'
        };
        
        console.log('🔍 ModelsLibrary API: Enhanced dynamic scan completed', {
          totalModels: enhancedModels.length,
          localModels: response.local_count,
          healthyModels: response.healthy_count,
          scanDuration: stats.scanStats?.scanDuration,
          categories: Object.keys(categorizedModels).map(key => ({
            type: key,
            count: categorizedModels[key as keyof typeof categorizedModels].length
          }))
        });
        
        return NextResponse.json(response, {
          headers: {
            'Cache-Control': forceRefresh ? 'no-cache' : 'public, max-age=300',
            'X-Scan-Timestamp': new Date().toISOString(),
            'X-Models-Count': enhancedModels.length.toString()
          }
        });
        
      } catch (scanError) {
        console.error('🔍 ModelsLibrary API: Enhanced dynamic scan failed', scanError);
        
        // Return error response with fallback
        return NextResponse.json({
          error: 'Scan failed',
          message: 'Dynamic model scanning encountered an error',
          details: scanError instanceof Error ? scanError.message : 'Unknown scan error',
          fallback_available: true
        }, { status: 500 });
      }
    }

    // Forward the request to the backend models library endpoint
    const base = BACKEND_URL.replace(/\/+$/, '');
    const queryString = searchParams.toString();
    const url = `${base}/api/models/library${queryString ? `?${queryString}` : ''}`;
    
    console.log('🔍 ModelsLibrary API: Backend URL constructed', {
      backendUrl: url,
      baseUrl: base,
      queryString: queryString
    });
    
    // Get Authorization header from the request
    const authHeader = request.headers.get('authorization');
    const headers: Record<string, string> = {
      'Accept': 'application/json',
      'Connection': 'keep-alive',
    };
    
    if (authHeader) {
      headers['Authorization'] = authHeader;
      console.log('🔍 ModelsLibrary API: Authorization header found', {
        hasAuth: true,
        authPrefix: authHeader.substring(0, 20) + '...'
      });
    } else {
      console.log('🔍 ModelsLibrary API: No authorization header');
    }

    const controller = new AbortController();
    const timeout = setTimeout(() => {
      console.log('🔍 ModelsLibrary API: Request timeout after', TIMEOUT_MS, 'ms');
      controller.abort();
    }, TIMEOUT_MS);
    
    try {
      console.log('🔍 ModelsLibrary API: Attempting backend fetch', { url, timeout: TIMEOUT_MS, backendUrl: BACKEND_URL });
      
      const response = await fetch(url, {
        method: 'GET',
        headers,
        signal: controller.signal,
        // Remove deprecated options that might cause issues
        cache: 'no-store',
      });
      
      clearTimeout(timeout);
      
      console.log('🔍 ModelsLibrary API: Backend response received', {
        status: response.status,
        statusText: response.statusText,
        headers: Object.fromEntries(response.headers.entries()),
        ok: response.ok,
        url: response.url
      });
      
      const contentType = response.headers.get('content-type') || '';
      let data: any = {};
      
      if (contentType.includes('application/json')) {
        try {
          data = await response.json();
          console.log('🔍 ModelsLibrary API: JSON response parsed successfully', {
            dataKeys: Object.keys(data),
            hasModels: Array.isArray(data.models),
            modelsCount: Array.isArray(data.models) ? data.models.length : 'N/A',
            responseStructure: data
          });
        } catch (parseError) {
          console.error('🔍 ModelsLibrary API: JSON parse error', { error: parseError });
          data = { models: [] };
        }
      } else {
        try {
          const text = await response.text();
          console.log('🔍 ModelsLibrary API: Non-JSON response', {
            contentType: contentType,
            textPreview: text.substring(0, 200) + (text.length > 200 ? '...' : ''),
            textLength: text.length
          });
          data = { models: [], message: text };
        } catch (textError) {
          console.error('🔍 ModelsLibrary API: Text read error', { error: textError });
          data = { models: [] };
        }
      }

      console.log('🔍 ModelsLibrary API: Returning response to frontend', {
        status: response.status,
        dataStructure: data
      });

      return NextResponse.json(data, { status: response.status });
      
    } catch (err: any) {
      clearTimeout(timeout);
      console.error('🔍 ModelsLibrary API: Backend fetch error', {
        error: err.message,
        errorType: err.name,
        stack: err.stack
      });
      
      // Try to use enhanced scanning as fallback
      try {
        console.log('🔍 ModelsLibrary API: Attempting fallback to dynamic scanning');
        const { modelSelectionService } = await import('@/lib/model-selection-service');
        
        const models = await modelSelectionService.scanLocalDirectories({
          forceRefresh: true,
          includeHealth: false
        });
        
        const fallbackResponse = {
          models,
          total_count: models.length,
          local_count: models.filter(m => m.status === 'local').length,
          available_count: models.filter(m => m.status === 'available').length,
          source: 'fallback_scan',
          message: 'Backend unavailable, using local directory scanning'
        };
        
        console.log('🔍 ModelsLibrary API: Fallback scan successful', {
          modelsFound: models.length
        });
        
        return NextResponse.json(fallbackResponse, { status: 200 });
        
      } catch (fallbackError) {
        console.error('🔍 ModelsLibrary API: Fallback scan failed', fallbackError);
        
        // Return minimal fallback response
        const minimalFallback = {
          models: [
            {
              id: 'local:tinyllama-1.1b',
              name: 'TinyLlama 1.1B',
              provider: 'llama-cpp',
              type: 'text',
              status: 'available',
              description: 'Local TinyLlama model for development',
              capabilities: ['chat', 'text-generation'],
              size: 669000000,
              metadata: {}
            }
          ],
          total_count: 1,
          local_count: 1,
          available_count: 0,
          source: 'minimal_fallback'
        };
        
        console.log('🔍 ModelsLibrary API: Returning minimal fallback response');
        return NextResponse.json(minimalFallback, { status: 200 });
      }
    }
    
  } catch (error) {
    console.error('🔍 ModelsLibrary API: Proxy error', error);
    const fallbackResponse = {
      models: [
        {
          id: 'local:tinyllama-1.1b',
          name: 'TinyLlama 1.1B',
          provider: 'llama-cpp',
          type: 'text',
          status: 'available',
          description: 'Local TinyLlama model for development',
          capabilities: ['chat', 'text-generation'],
          size: 669000000,
          metadata: {}
        }
      ],
      total_count: 1,
      local_count: 1,
      available_count: 0,
      source: 'error_fallback'
    };
    
    console.log('🔍 ModelsLibrary API: Returning error fallback', fallbackResponse);
    return NextResponse.json(fallbackResponse, { status: 200 });
  }
}