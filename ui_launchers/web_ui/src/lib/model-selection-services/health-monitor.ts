/**
 * Model Health Monitoring Service
 */

import type { Model, ModelHealth } from "../model-utils";
import { getKarenBackend } from "../karen-backend";
import { BaseModelService } from "./base-service";
import { SystemResourceInfo } from "./types";

export class ModelHealthMonitor extends BaseModelService {
  private healthCache: Map<string, ModelHealth> = new Map();

  /**
   * Perform comprehensive health check on a model
   */
  async performComprehensiveHealthCheck(model: Model): Promise<ModelHealth> {
    const issues: string[] = [];
    const performanceMetrics: Record<string, number> = {};
    let memoryRequirement = 0;

    try {
      // Check file existence and accessibility
      if (model.local_path) {
        try {
          const backend = getKarenBackend();
          const response = await backend.makeRequestPublic(
            `/api/models/health/file-check`,
            {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ path: model.local_path }),
            }
          );
          const fileCheck = response as {
            exists: boolean;
            readable: boolean;
            corrupted: boolean;
          };

          if (!fileCheck.exists) {
            issues.push("Model file not found at specified path");
          } else if (!fileCheck.readable) {
            issues.push("Model file is not readable");
          } else if (fileCheck.corrupted) {
            issues.push("Model file appears to be corrupted");
          }
        } catch (error) {
          issues.push(`File accessibility check failed: ${error}`);
        }
      }

      // Estimate memory requirements based on model type and size
      memoryRequirement = this.estimateMemoryRequirement(model);
      
      // Check system memory availability
      const systemMemory = await this.getSystemMemoryInfo();
      if (memoryRequirement > systemMemory.available) {
        issues.push(`Insufficient memory: requires ${this.formatMemorySize(memoryRequirement)}, available ${this.formatMemorySize(systemMemory.available)}`);
      }

      // Validate model format compatibility
      const formatValidation = this.validateModelFormat(model);
      if (!formatValidation.valid) {
        issues.push(`Format validation failed: ${formatValidation.reason}`);
      }

      // Check provider-specific compatibility
      const providerCompatibility = await this.checkProviderCompatibility(model);
      if (!providerCompatibility.compatible) {
        issues.push(`Provider compatibility issue: ${providerCompatibility.reason}`);
      }

      // Perform load test if model is critical and system has resources
      if (issues.length === 0 && systemMemory.available > memoryRequirement * 1.5) {
        try {
          const loadTest = await this.performModelLoadTest(model);
          performanceMetrics.load_time_ms = loadTest.loadTime;
          performanceMetrics.memory_usage_mb = loadTest.memoryUsage / (1024 * 1024);
          
          if (loadTest.failed) {
            issues.push(`Load test failed: ${loadTest.error}`);
          }
        } catch (error) {
          // Load test failure is not critical for health status
          this.logError(`Load test failed for ${model.id}:`, error);
        }
      }

      // Check model-specific health indicators
      const modelSpecificHealth = await this.checkModelSpecificHealth(model);
      if (modelSpecificHealth.issues.length > 0) {
        issues.push(...modelSpecificHealth.issues);
      }
      Object.assign(performanceMetrics, modelSpecificHealth.metrics);

    } catch (error) {
      issues.push(`Health check failed: ${error}`);
    }

    const health: ModelHealth = {
      is_healthy: issues.length === 0,
      last_check: new Date().toISOString(),
      issues,
      performance_metrics: Object.keys(performanceMetrics).length > 0 ? performanceMetrics : undefined,
      memory_requirement: memoryRequirement
    };

    // Cache the health result
    this.healthCache.set(model.id, health);
    return health;
  }

  /**
   * Get cached health status or perform new check
   */
  async getModelHealthStatus(modelId: string, model?: Model): Promise<ModelHealth | null> {
    // Check cache first
    const cached = this.healthCache.get(modelId);
    if (cached && this.isHealthCacheValid(cached)) {
      return cached;
    }

    // Perform new health check if model is provided
    if (model) {
      return this.performComprehensiveHealthCheck(model);
    }

    return null;
  }

  /**
   * Check if cached health data is still valid
   */
  private isHealthCacheValid(health: ModelHealth): boolean {
    const cacheAge = Date.now() - new Date(health.last_check).getTime();
    return cacheAge < this.CACHE_DURATION;
  }

  /**
   * Estimate memory requirement for a model
   */
  private estimateMemoryRequirement(model: Model): number {
    let baseRequirement = model.size || 0;
    
    // Add overhead based on model type and format
    switch (model.type) {
      case 'text':
        if (model.subtype === 'llama-cpp') {
          // GGUF models need less memory due to quantization
          const quantization = model.metadata?.quantization || 'Q4_K_M';
          if (quantization.includes('Q4')) {
            baseRequirement *= 1.2; // 20% overhead
          } else if (quantization.includes('Q8')) {
            baseRequirement *= 1.4; // 40% overhead
          } else {
            baseRequirement *= 1.3; // 30% default overhead
          }
        } else if (model.subtype === 'transformers') {
          // Transformers models need more memory for inference
          baseRequirement *= 1.8; // 80% overhead for activations and gradients
        }
        break;
        
      case 'image':
        if (model.subtype === 'stable-diffusion') {
          // SD models need significant memory for image generation
          baseRequirement *= 2.0; // 100% overhead for VAE, UNet, etc.
        } else if (model.subtype === 'flux') {
          // Flux models are more memory efficient
          baseRequirement *= 1.6; // 60% overhead
        }
        break;
        
      case 'embedding':
        // Embedding models are typically more memory efficient
        baseRequirement *= 1.1; // 10% overhead
        break;
        
      default:
        baseRequirement *= 1.5; // 50% default overhead
    }
    
    // Minimum memory requirement
    return Math.max(baseRequirement, 512 * 1024 * 1024); // At least 512MB
  }

  /**
   * Get system memory information
   */
  private async getSystemMemoryInfo(): Promise<{
    total: number;
    available: number;
    used: number;
    gpu_memory?: Record<string, { total: number; available: number; used: number }>;
  }> {
    try {
      const backend = getKarenBackend();
      const response = await backend.makeRequestPublic("/api/system/memory");
      const memoryInfo = response as {
        total: number;
        available: number;
        used: number;
        gpu_memory?: Record<string, { total: number; available: number; used: number }>;
      };
      return memoryInfo;
    } catch (error) {
      this.logError("Failed to get system memory info:", error);
      // Return conservative estimates
      return {
        total: 8 * 1024 * 1024 * 1024, // 8GB
        available: 4 * 1024 * 1024 * 1024, // 4GB available
        used: 4 * 1024 * 1024 * 1024, // 4GB used
      };
    }
  }

  /**
   * Validate model format compatibility
   */
  private validateModelFormat(model: Model): { valid: boolean; reason?: string } {
    if (!model.format) {
      return { valid: false, reason: 'Model format not specified' };
    }

    // Check format compatibility with model type
    switch (model.type) {
      case 'text':
        if (model.subtype === 'llama-cpp' && model.format !== 'gguf') {
          return { valid: false, reason: 'llama-cpp models must use GGUF format' };
        }
        if (model.subtype === 'transformers' && !['safetensors', 'pytorch'].includes(model.format)) {
          return { valid: false, reason: 'transformers models must use safetensors or pytorch format' };
        }
        break;
        
      case 'image':
        if (!['safetensors', 'diffusers', 'pytorch'].includes(model.format)) {
          return { valid: false, reason: 'image models must use safetensors, diffusers, or pytorch format' };
        }
        break;
        
      case 'embedding':
        if (!['safetensors', 'pytorch'].includes(model.format)) {
          return { valid: false, reason: 'embedding models must use safetensors or pytorch format' };
        }
        break;
    }

    return { valid: true };
  }

  /**
   * Check provider-specific compatibility
   */
  private async checkProviderCompatibility(model: Model): Promise<{ compatible: boolean; reason?: string }> {
    try {
      const backend = getKarenBackend();
      const response = await backend.makeRequestPublic('/api/providers/compatibility', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider: model.provider,
          model_type: model.type,
          format: model.format,
          metadata: model.metadata
        })

      const compatibility = response as {
        compatible: boolean;
        reason?: string;
      };
      
      return {
        compatible: compatibility.compatible,
        reason: compatibility.reason
      };
    } catch (error) {
      // If compatibility check fails, assume compatible but log warning
      this.logError(`Provider compatibility check failed for ${model.id}:`, error);
      return { compatible: true };
    }
  }

  /**
   * Perform model load test
   */
  private async performModelLoadTest(model: Model): Promise<{
    loadTime: number;
    memoryUsage: number;
    failed: boolean;
    error?: string;
  }> {
    const startTime = Date.now();
    
    try {
      const backend = getKarenBackend();
      const response = await backend.makeRequestPublic('/api/models/load-test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model_id: model.id,
          timeout_ms: 30000 // 30 second timeout
        })

      const loadTest = response as {
        success: boolean;
        memory_usage?: number;
        error?: string;
      };
      
      return {
        loadTime: Date.now() - startTime,
        memoryUsage: loadTest.memory_usage || 0,
        failed: !loadTest.success,
        error: loadTest.error
      };
    } catch (error) {
      return {
        loadTime: Date.now() - startTime,
        memoryUsage: 0,
        failed: true,
        error: String(error)
      };
    }
  }

  /**
   * Check model-specific health indicators
   */
  private async checkModelSpecificHealth(model: Model): Promise<{
    issues: string[];
    metrics: Record<string, number>;
  }> {
    const issues: string[] = [];
    const metrics: Record<string, number> = {};

    try {
      // Check model-specific requirements based on type
      switch (model.type) {
        case 'text':
          if (model.subtype === 'llama-cpp') {
            // Check GGUF-specific health
            if (!model.metadata?.quantization) {
              issues.push('GGUF quantization information missing');
            }
            if (!model.metadata?.architecture) {
              issues.push('Model architecture information missing');
            }
            // Estimate tokens per second based on model size
            const tokensPerSecond = this.estimateTokensPerSecond(model);
            metrics.estimated_tokens_per_second = tokensPerSecond;
          } else if (model.subtype === 'transformers') {
            // Check transformers-specific health
            if (!model.metadata?.model_type) {
              issues.push('Transformers model type information missing');
            }
            if (!model.metadata?.architectures?.length) {
              issues.push('Model architecture information missing');
            }
          }
          break;
          
        case 'image':
          if (model.subtype === 'stable-diffusion') {
            // Check SD-specific health
            if (!model.metadata?.base_model) {
              issues.push('Stable Diffusion base model information missing');
            }
            if (!model.metadata?.resolution) {
              issues.push('Image resolution information missing');
            }
            // Estimate generation speed
            const imagesPerMinute = this.estimateImageGenerationSpeed(model);
            metrics.estimated_images_per_minute = imagesPerMinute;
          } else if (model.subtype === 'flux') {
            // Check Flux-specific health
            if (!model.metadata?.variant) {
              issues.push('Flux variant information missing');
            }
          }
          break;
          
        case 'embedding':
          // Check embedding-specific health
          if (!model.metadata?.max_position_embeddings && !model.metadata?.model_max_length) {
            issues.push('Embedding model context length information missing');
          }
          break;
      }

      // Check for common issues
      if (model.size && model.size > 50 * 1024 * 1024 * 1024) { // > 50GB
        issues.push('Model size is unusually large, may cause performance issues');
      }

      if (model.metadata?.context_length && model.metadata.context_length > 32768) {
        issues.push('Large context length may require significant memory');
      }

    } catch (error) {
      issues.push(`Model-specific health check failed: ${error}`);
    }

    return { issues, metrics };
  }

  /**
   * Estimate tokens per second for text models
   */
  private estimateTokensPerSecond(model: Model): number {
    const sizeGB = (model.size || 0) / (1024 * 1024 * 1024);
    const quantization = model.metadata?.quantization || 'Q4_K_M';
    
    // Base estimation (tokens/sec) - these are rough estimates
    let baseSpeed = 50; // Conservative baseline
    
    // Adjust for model size (smaller models are faster)
    if (sizeGB < 1) baseSpeed = 100;
    else if (sizeGB < 3) baseSpeed = 80;
    else if (sizeGB < 7) baseSpeed = 60;
    else if (sizeGB < 15) baseSpeed = 40;
    else baseSpeed = 20;
    
    // Adjust for quantization (lower quantization is faster)
    if (quantization.includes('Q4')) baseSpeed *= 1.2;
    else if (quantization.includes('Q8')) baseSpeed *= 0.8;
    else if (quantization.includes('Q2')) baseSpeed *= 1.5;
    
    return Math.round(baseSpeed);
  }

  /**
   * Estimate image generation speed for image models
   */
  private estimateImageGenerationSpeed(model: Model): number {
    const sizeGB = (model.size || 0) / (1024 * 1024 * 1024);
    const baseModel = model.metadata?.base_model || 'SD 1.5';
    
    // Base estimation (images/minute) - these are rough estimates
    let baseSpeed = 2; // Conservative baseline
    
    // Adjust for base model
    if (baseModel.includes('SDXL')) baseSpeed = 1; // SDXL is slower
    else if (baseModel.includes('SD 2')) baseSpeed = 1.5;
    else baseSpeed = 2; // SD 1.5
    
    // Adjust for model size
    if (sizeGB > 10) baseSpeed *= 0.7; // Large models are slower
    else if (sizeGB < 3) baseSpeed *= 1.3; // Small models are faster
    
    return Math.round(baseSpeed * 10) / 10; // Round to 1 decimal
  }

  /**
   * Clear health cache
   */
  clearCache(): void {
    this.healthCache.clear();
  }
}