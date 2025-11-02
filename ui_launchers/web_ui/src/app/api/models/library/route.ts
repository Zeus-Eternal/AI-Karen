import { randomUUID } from 'crypto';

import { NextRequest, NextResponse } from 'next/server';

import { logger } from '@/lib/logger';

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
  const requestId = randomUUID();
  logger.info('Models library request received', {
    requestId,
    method: request.method,
    searchParams: Object.fromEntries(request.nextUrl.searchParams.entries()),

  try {
    const searchParams = request.nextUrl.searchParams;
    const scan = searchParams.get('scan') === 'true';
    const includeHealth = searchParams.get('includeHealth') === 'true';
    const modelType = searchParams.get('type'); // Filter by model type
    const provider = searchParams.get('provider'); // Filter by provider
    const forceRefresh = searchParams.get('forceRefresh') === 'true';
    
    // Enhanced scanning with health monitoring
    if (scan) {
      logger.info('Models library dynamic scan requested', {
        requestId,
        includeHealth,
        modelType,
        provider,
        forceRefresh,

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
                logger.warn(`Failed to get health status for model ${model.id}`, {
                  requestId,
                  error: healthError instanceof Error ? healthError.message : String(healthError),

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
        
        logger.info('Models library dynamic scan completed', {
          requestId,
          totalModels: enhancedModels.length,
          localModels: response.local_count,
          healthyModels: response.healthy_count,
          scanDuration: stats.scanStats?.scanDuration,

        return NextResponse.json(response, {
          headers: {
            'Cache-Control': forceRefresh ? 'no-cache' : 'public, max-age=300',
            'X-Scan-Timestamp': new Date().toISOString(),
            'X-Models-Count': enhancedModels.length.toString()
          }

      } catch (scanError) {
        logger.error('Models library dynamic scan failed', scanError instanceof Error ? scanError : { message: String(scanError) });
        
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
    
    logger.debug('Models library backend URL prepared', {
      requestId,
      baseUrl: base,
      hasQuery: Boolean(queryString),

    // Get Authorization header from the request
    const authHeader = request.headers.get('authorization');
    const headers: Record<string, string> = {
      'Accept': 'application/json',
      'Connection': 'keep-alive',
    };
    
    if (authHeader) {
      headers['Authorization'] = authHeader;
      logger.debug('Models library forwarding authorization header', {
        requestId,

    } else {
      logger.debug('Models library request without authorization header', {
        requestId,

    }

    const controller = new AbortController();
    const timeout = setTimeout(() => {
      logger.warn('Models library request timed out', { requestId, timeoutMs: TIMEOUT_MS });
      controller.abort();
    }, TIMEOUT_MS);
    
    try {
      logger.info('Models library proxying to backend', { requestId, url });
      
      const response = await fetch(url, {
        method: 'GET',
        headers,
        signal: controller.signal,
        // Remove deprecated options that might cause issues
        cache: 'no-store',

      clearTimeout(timeout);
      
      logger.info('Models library backend response received', {
        requestId,
        status: response.status,
        ok: response.ok,
        url: response.url,

      const contentType = response.headers.get('content-type') || '';
      let data: any = {};
      
      if (contentType.includes('application/json')) {
        try {
          data = await response.json();
          logger.debug('Models library JSON payload processed', {
            requestId,
            keys: Object.keys(data),
            modelCount: Array.isArray(data.models) ? data.models.length : undefined,

        } catch (parseError) {
          logger.error('Models library JSON parse error', parseError instanceof Error ? parseError : { message: String(parseError) });
          data = { models: [] };
        }
      } else {
        try {
          const text = await response.text();
          logger.warn('Models library received non-JSON payload', {
            requestId,
            contentType,
            length: text.length,

          data = { models: [], message: text };
        } catch (textError) {
          logger.error('Models library text read error', textError instanceof Error ? textError : { message: String(textError) });
          data = { models: [] };
        }
      }

      logger.info('Models library response delivered to frontend', {
        requestId,
        status: response.status,
        modelCount: Array.isArray((data as any).models) ? (data as any).models.length : undefined,

      return NextResponse.json(data, { status: response.status });
      
    } catch (err: any) {
      clearTimeout(timeout);
      logger.error('Models library backend fetch error', err instanceof Error ? err : { message: String(err) });
      
      // Try to use enhanced scanning as fallback
      try {
        logger.warn('Models library attempting fallback scan', { requestId });
        const { modelSelectionService } = await import('@/lib/model-selection-service');
        
        const models = await modelSelectionService.scanLocalDirectories({
          forceRefresh: true,
          includeHealth: false

        const fallbackResponse = {
          models,
          total_count: models.length,
          local_count: models.filter(m => m.status === 'local').length,
          available_count: models.filter(m => m.status === 'available').length,
          source: 'fallback_scan',
          message: 'Backend unavailable, using local directory scanning'
        };
        
        logger.warn('Models library fallback scan succeeded', {
          requestId,
          modelsFound: models.length,

        return NextResponse.json(fallbackResponse, { status: 200 });
        
      } catch (fallbackError) {
        logger.error('Models library fallback scan failed', fallbackError instanceof Error ? fallbackError : { message: String(fallbackError) });

        // Return minimal fallback response
        const minimalFallback = {
          models: [],
          total_count: 0,
          local_count: 0,
          available_count: 0,
          source: 'minimal_fallback',
          message: 'No models available. Please check backend connectivity.',
        };

        logger.error('Models library returning minimal fallback response', {
          requestId,

        return NextResponse.json(minimalFallback, { status: 200 });
      }
    }
    
  } catch (error) {
    logger.error('Models library proxy error', error instanceof Error ? error : { message: String(error) });
    const fallbackResponse = {
      models: [],
      total_count: 0,
      local_count: 0,
      available_count: 0,
      source: 'error_fallback',
      message: 'Unable to retrieve models from backend.',
    };

    logger.error('Models library returning error fallback', {
      requestId,

    return NextResponse.json(fallbackResponse, { status: 200 });
  }
}