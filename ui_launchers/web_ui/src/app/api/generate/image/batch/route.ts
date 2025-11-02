import { NextRequest, NextResponse } from 'next/server';
interface BatchImageGenerationRequest {
  requests: Array<{
    id?: string; // Optional ID for tracking individual requests
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
  }>;
  global_model_id?: string; // Model to use for all requests if not specified individually
  priority?: 'low' | 'normal' | 'high';
  callback_url?: string; // URL to POST results to when complete
}
interface BatchImageGenerationResponse {
  success: boolean;
  batch_id: string;
  total_requests: number;
  estimated_completion_time: number; // seconds
  status: 'queued' | 'processing' | 'completed' | 'failed';
  results?: Array<{
    request_id: string;
    success: boolean;
    images?: Array<{
      url?: string;
      base64?: string;
      seed: number;
      width: number;
      height: number;
    }>;
    generation_info?: {
      model_id: string;
      provider: string;
      prompt: string;
      parameters: Record<string, any>;
      generation_time: number;
    };
    error?: string;
  }>;
  error?: string;
  message?: string;
}
// In-memory batch tracking (in production, this would be in a database)
const batchJobs = new Map<string, {
  id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  requests: any[];
  results: any[];
  created_at: Date;
  completed_at?: Date;
  estimated_completion: Date;
}>();
export async function POST(request: NextRequest) {
  try {
    const body: BatchImageGenerationRequest = await request.json();
    const { requests, global_model_id, priority = 'normal', callback_url } = body;
    if (!requests || !Array.isArray(requests) || requests.length === 0) {
      return NextResponse.json(
        { error: 'Missing or empty requests array' },
        { status: 400 }
      );
    }
    if (requests.length > 20) {
      return NextResponse.json(
        { error: 'Batch size cannot exceed 20 requests' },
        { status: 400 }
      );
    }
    // Validate each request
    for (let i = 0; i < requests.length; i++) {
      const req = requests[i];
      if (!req.prompt) {
        return NextResponse.json(
          { error: `Request ${i + 1} is missing required field: prompt` },
          { status: 400 }
        );
      }
    }
    const { modelSelectionService } = await import('@/lib/model-selection-service');
    try {
      // Get available image models
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
      // Generate batch ID
      const batchId = `batch_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      // Estimate completion time (rough calculation)
      const avgTimePerImage = 30; // seconds
      const totalImages = requests.length; // Each request generates 1 image
      const estimatedTime = totalImages * avgTimePerImage;
      const estimatedCompletion = new Date(Date.now() + estimatedTime * 1000);
      // Create batch job
      const batchJob = {
        id: batchId,
        status: 'queued' as const,
        requests: requests.map((req, index) => ({
          ...req,
          id: req.id || `req_${index + 1}`,
          model_id: req.model_id || global_model_id || imageModels[0].id
        })),
        results: [],
        created_at: new Date(),
        estimated_completion: estimatedCompletion
      };
      batchJobs.set(batchId, batchJob);
      // Start processing batch asynchronously
      processBatchAsync(batchId, callback_url).catch(error => {
        const job = batchJobs.get(batchId);
        if (job) {
          job.status = 'failed';
          batchJobs.set(batchId, job);
        }
      });
      const response: BatchImageGenerationResponse = {
        success: true,
        batch_id: batchId,
        total_requests: requests.length,
        estimated_completion_time: estimatedTime,
        status: 'queued'
      };
      return NextResponse.json(response, {
        status: 202, // Accepted
        headers: {
          'X-Batch-ID': batchId,
          'X-Estimated-Time': estimatedTime.toString(),
          'Location': `/api/generate/image/batch/${batchId}`
        }
      });
    } catch (batchError) {
      return NextResponse.json(
        {
          error: 'Batch setup failed',
          message: batchError instanceof Error ? batchError.message : 'Unknown batch error'
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
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const batchId = searchParams.get('batch_id');
    if (!batchId) {
      // Return list of recent batches
      const recentBatches = Array.from(batchJobs.values())
        .sort((a, b) => b.created_at.getTime() - a.created_at.getTime())
        .slice(0, 10)
        .map(job => ({
          batch_id: job.id,
          status: job.status,
          total_requests: job.requests.length,
          completed_requests: job.results.length,
          created_at: job.created_at.toISOString(),
          completed_at: job.completed_at?.toISOString(),
          estimated_completion: job.estimated_completion.toISOString()
        }));
      return NextResponse.json({
        recent_batches: recentBatches,
        active_batches: recentBatches.filter(b => b.status === 'processing' || b.status === 'queued').length
      });
    }
    // Return specific batch status
    const batchJob = batchJobs.get(batchId);
    if (!batchJob) {
      return NextResponse.json(
        { error: 'Batch not found', batch_id: batchId },
        { status: 404 }
      );
    }
    const response: BatchImageGenerationResponse = {
      success: true,
      batch_id: batchId,
      total_requests: batchJob.requests.length,
      estimated_completion_time: Math.max(0, Math.floor((batchJob.estimated_completion.getTime() - Date.now()) / 1000)),
      status: batchJob.status,
      results: batchJob.results
    };
    return NextResponse.json(response);
  } catch (error) {
    return NextResponse.json(
      {
        error: 'Status check failed',
        message: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}
/**
 * Process batch requests asynchronously
 */
async function processBatchAsync(batchId: string, callbackUrl?: string): Promise<void> {
  const batchJob = batchJobs.get(batchId);
  if (!batchJob) return;
  batchJob.status = 'processing';
  batchJobs.set(batchId, batchJob);
  const results = [];
  for (const request of batchJob.requests) {
    try {
      // Simulate image generation (in real implementation, call actual generation)
      const startTime = Date.now();
      // Simulate processing time
      await new Promise(resolve => setTimeout(resolve, 2000 + Math.random() * 3000));
      const batchSize = request.batch_size || 1;
      const images = [];
      for (let i = 0; i < batchSize; i++) {
        images.push({
          base64: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==',
          seed: (request.seed || Math.floor(Math.random() * 2147483647)) + i,
          width: request.width || 512,
          height: request.height || 512
        });
      }
      const generationTime = Date.now() - startTime;
      results.push({
        request_id: request.id,
        success: true,
        images,
        generation_info: {
          model_id: request.model_id,
          provider: 'simulated',
          prompt: request.prompt,
          parameters: {
            width: request.width || 512,
            height: request.height || 512,
            steps: request.steps || 20,
            guidance_scale: request.guidance_scale || 7.5,
            seed: request.seed || -1
          },
          generation_time: generationTime
        }
      });
    } catch (error) {
      results.push({
        request_id: request.id,
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
    // Update batch job with current results
    batchJob.results = results;
    batchJobs.set(batchId, batchJob);
  }
  // Mark batch as completed
  batchJob.status = 'completed';
  batchJob.completed_at = new Date();
  batchJobs.set(batchId, batchJob);
  console.log('🎨 Batch processing completed:', batchId, {
    totalRequests: batchJob.requests.length,
    successfulResults: results.filter(r => r.success).length
  });
  // Send callback if provided
  if (callbackUrl) {
    try {
      await fetch(callbackUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          batch_id: batchId,
          status: 'completed',
          results
        })
      });
    } catch (callbackError) {
    }
  }
}
