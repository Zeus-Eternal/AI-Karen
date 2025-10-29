/**
 * System Resource Monitoring Service
 */

import type { Model } from "../model-utils";
import { getKarenBackend } from "../karen-backend";
import { BaseModelService } from "./base-service";
import { 
  SystemResourceInfo, 
  ResourceLoadabilityCheck, 
  ModelResourceUsage, 
  ResourceUsageHistoryEntry,
  ResourceRecommendations,
  ModelRecommendation
} from "./types";

export class ResourceMonitor extends BaseModelService {
  /**
   * Get detailed system resource information including CPU, memory, and GPU
   */
  async getSystemResourceInfo(): Promise<SystemResourceInfo> {
    try {
      const backend = getKarenBackend();
      const response = await backend.makeRequestPublic("/api/system/resources");
      const resourceInfo = response as SystemResourceInfo;
      return resourceInfo;
    } catch (error) {
      this.logError("Failed to get system resource info:", error);
      // Return conservative estimates
      return {
        cpu: {
          cores: 4,
          usage_percent: 50
        },
        memory: {
          total: 8 * 1024 * 1024 * 1024,
          available: 4 * 1024 * 1024 * 1024,
          used: 4 * 1024 * 1024 * 1024,
          usage_percent: 50
        },
        gpu: [],
        disk: {
          total: 500 * 1024 * 1024 * 1024,
          available: 250 * 1024 * 1024 * 1024,
          used: 250 * 1024 * 1024 * 1024,
          usage_percent: 50
        }
      };
    }
  }

  /**
   * Check if system has sufficient resources to load a model
   */
  async canLoadModel(model: Model): Promise<ResourceLoadabilityCheck> {
    const systemResources = await this.getSystemResourceInfo();
    const memoryRequirement = this.estimateMemoryRequirement(model);
    const gpuMemoryRequirement = this.estimateGPUMemoryRequirement(model);
    const diskSpaceRequirement = model.size || 0;

    // Check memory availability
    if (memoryRequirement > systemResources.memory.available) {
      return {
        canLoad: false,
        reason: `Insufficient system memory: requires ${this.formatMemorySize(memoryRequirement)}, available ${this.formatMemorySize(systemResources.memory.available)}`,
        resourceRequirements: {
          memory: memoryRequirement,
          gpu_memory: gpuMemoryRequirement,
          disk_space: diskSpaceRequirement
        },
        systemResources: {
          memory_available: systemResources.memory.available,
          gpu_memory_available: systemResources.gpu[0]?.memory_available,
          disk_available: systemResources.disk.available
        }
      };
    }

    // Check GPU memory if required
    if (gpuMemoryRequirement > 0) {
      const availableGPUMemory = systemResources.gpu.reduce((max, gpu) => 
        Math.max(max, gpu.memory_available), 0);
      
      if (gpuMemoryRequirement > availableGPUMemory) {
        return {
          canLoad: false,
          reason: `Insufficient GPU memory: requires ${this.formatMemorySize(gpuMemoryRequirement)}, available ${this.formatMemorySize(availableGPUMemory)}`,
          resourceRequirements: {
            memory: memoryRequirement,
            gpu_memory: gpuMemoryRequirement,
            disk_space: diskSpaceRequirement
          },
          systemResources: {
            memory_available: systemResources.memory.available,
            gpu_memory_available: availableGPUMemory,
            disk_available: systemResources.disk.available
          }
        };
      }
    }

    // Check disk space (for temporary files during loading)
    const requiredDiskSpace = diskSpaceRequirement * 0.1; // 10% of model size for temp files
    if (requiredDiskSpace > systemResources.disk.available) {
      return {
        canLoad: false,
        reason: `Insufficient disk space: requires ${this.formatMemorySize(requiredDiskSpace)} for temporary files, available ${this.formatMemorySize(systemResources.disk.available)}`,
        resourceRequirements: {
          memory: memoryRequirement,
          gpu_memory: gpuMemoryRequirement,
          disk_space: diskSpaceRequirement
        },
        systemResources: {
          memory_available: systemResources.memory.available,
          gpu_memory_available: systemResources.gpu[0]?.memory_available,
          disk_available: systemResources.disk.available
        }
      };
    }

    return {
      canLoad: true,
      resourceRequirements: {
        memory: memoryRequirement,
        gpu_memory: gpuMemoryRequirement,
        disk_space: diskSpaceRequirement
      },
      systemResources: {
        memory_available: systemResources.memory.available,
        gpu_memory_available: systemResources.gpu[0]?.memory_available,
        disk_available: systemResources.disk.available
      }
    };
  }

  /**
   * Get optimal GPU for model loading
   */
  async getOptimalGPU(model: Model): Promise<{
    gpu_id: number | null;
    gpu_name?: string;
    reason: string;
    memory_available: number;
  }> {
    const systemResources = await this.getSystemResourceInfo();
    const gpuMemoryRequirement = this.estimateGPUMemoryRequirement(model);

    // If no GPU memory required, return null
    if (gpuMemoryRequirement === 0) {
      return {
        gpu_id: null,
        reason: "Model does not require GPU",
        memory_available: 0
      };
    }

    // Find GPU with most available memory that can fit the model
    const suitableGPUs = systemResources.gpu
      .filter(gpu => gpu.memory_available >= gpuMemoryRequirement)
      .sort((a, b) => b.memory_available - a.memory_available);

    if (suitableGPUs.length === 0) {
      return {
        gpu_id: null,
        reason: `No GPU has sufficient memory (requires ${this.formatMemorySize(gpuMemoryRequirement)})`,
        memory_available: Math.max(...systemResources.gpu.map(gpu => gpu.memory_available), 0)
      };
    }

    const optimalGPU = suitableGPUs[0];
    return {
      gpu_id: optimalGPU.id,
      gpu_name: optimalGPU.name,
      reason: `Selected GPU ${optimalGPU.id} (${optimalGPU.name}) with ${this.formatMemorySize(optimalGPU.memory_available)} available`,
      memory_available: optimalGPU.memory_available
    };
  }

  /**
   * Monitor resource usage during model operations
   */
  async monitorResourceUsage(modelId: string, operation: 'loading' | 'inference' | 'generation'): Promise<{
    start_time: string;
    end_time?: string;
    duration_ms?: number;
    peak_memory_usage: number;
    peak_gpu_memory_usage?: number;
    average_cpu_usage: number;
    average_gpu_utilization?: number;
  }> {
    const startTime = new Date();
    const startResources = await this.getSystemResourceInfo();

    // Store monitoring data (in a real implementation, this would be more sophisticated)
    const monitoringData = {
      start_time: startTime.toISOString(),
      peak_memory_usage: startResources.memory.used,
      peak_gpu_memory_usage: startResources.gpu[0]?.memory_used,
      average_cpu_usage: startResources.cpu.usage_percent,
      average_gpu_utilization: startResources.gpu[0]?.utilization_percent
    };

    // Return monitoring data (in a real implementation, this would be updated continuously)
    return monitoringData;
  }

  /**
   * Track resource usage for a specific model
   */
  async trackModelResourceUsage(modelId: string): Promise<ModelResourceUsage | null> {
    try {
      const backend = getKarenBackend();
      const response = await backend.makeRequestPublic(
        `/api/models/resource-usage/${encodeURIComponent(modelId)}`
      );
      const usage = response as {
        memory_usage?: number;
        gpu_memory_usage?: number;
        cpu_usage?: number;
        gpu_utilization?: number;
        load_time_ms?: number;
        inference_time_ms?: number;
      };
      return {
        model_id: modelId,
        memory_usage: usage.memory_usage || 0,
        gpu_memory_usage: usage.gpu_memory_usage,
        cpu_usage: usage.cpu_usage || 0,
        gpu_utilization: usage.gpu_utilization,
        load_time_ms: usage.load_time_ms,
        inference_time_ms: usage.inference_time_ms,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      this.logError(`Failed to track resource usage for ${modelId}:`, error);
      return null;
    }
  }

  /**
   * Get resource usage history for all models
   */
  async getResourceUsageHistory(timeRange: '1h' | '24h' | '7d' | '30d' = '24h'): Promise<ResourceUsageHistoryEntry[]> {
    try {
      const backend = getKarenBackend();
      const response = await backend.makeRequestPublic(`/api/models/resource-usage/history?range=${timeRange}`);
      const history = Array.isArray(response) ? response : [];
      
      return history.map((entry: unknown) => {
        const typedEntry = entry as {
          model_id: string;
          average_memory_usage: number;
          peak_memory_usage: number;
          average_gpu_memory_usage?: number;
          peak_gpu_memory_usage?: number;
          average_cpu_usage: number;
          peak_cpu_usage: number;
          total_inference_time_ms: number;
          inference_count: number;
        };
        
        const efficiencyScore = this.calculateEfficiencyScore(typedEntry);
        
        return {
          ...typedEntry,
          model_name: typedEntry.model_id, // Will be enhanced with actual name by caller
          efficiency_score: efficiencyScore,
        };
      });
    } catch (error) {
      this.logError('Failed to get resource usage history:', error);
      return [];
    }
  }

  /**
   * Get system resource recommendations for optimal model selection
   */
  async getResourceRecommendations(models: Model[]): Promise<ResourceRecommendations> {
    const systemResources = await this.getSystemResourceInfo();
    const recommendations: ModelRecommendation[] = [];
    const optimizationTips: string[] = [];
    const warnings: string[] = [];

    // Analyze each model's resource fit
    for (const model of models.filter(m => m.status === 'local')) {
      const memoryRequirement = this.estimateMemoryRequirement(model);
      const gpuMemoryRequirement = this.estimateGPUMemoryRequirement(model);
      
      const memoryRatio = memoryRequirement / systemResources.memory.available;
      const gpuMemoryRatio = gpuMemoryRequirement > 0 && systemResources.gpu.length > 0
        ? gpuMemoryRequirement / Math.max(...systemResources.gpu.map(g => g.memory_available))
        : 0;

      let resourceFit: 'excellent' | 'good' | 'acceptable' | 'poor';
      let reason: string;

      if (memoryRatio < 0.3 && gpuMemoryRatio < 0.3) {
        resourceFit = 'excellent';
        reason = 'Low resource usage, excellent performance expected';
      } else if (memoryRatio < 0.6 && gpuMemoryRatio < 0.6) {
        resourceFit = 'good';
        reason = 'Moderate resource usage, good performance expected';
      } else if (memoryRatio < 0.8 && gpuMemoryRatio < 0.8) {
        resourceFit = 'acceptable';
        reason = 'High resource usage, may impact system performance';
      } else {
        resourceFit = 'poor';
        reason = 'Very high resource usage, may cause system instability';
      }

      recommendations.push({
        model_id: model.id,
        model_name: model.name,
        reason,
        resource_fit: resourceFit
      });
    }

    // Generate optimization tips
    if (systemResources.memory.usage_percent > 80) {
      optimizationTips.push('Consider closing other applications to free up system memory');
    }
    
    if (systemResources.gpu.some(gpu => gpu.utilization_percent > 90)) {
      optimizationTips.push('GPU is heavily utilized, consider using smaller models or CPU inference');
    }
    
    if (systemResources.cpu.usage_percent > 90) {
      optimizationTips.push('CPU is heavily loaded, model inference may be slower');
    }

    // Generate warnings
    if (systemResources.memory.available < 2 * 1024 * 1024 * 1024) { // Less than 2GB
      warnings.push('Low available memory may prevent loading larger models');
    }
    
    if (systemResources.gpu.length === 0) {
      warnings.push('No GPU detected, image generation models will not be available');
    }
    
    if (systemResources.disk.usage_percent > 90) {
      warnings.push('Low disk space may affect model loading and temporary file creation');
    }

    // Sort recommendations by resource fit
    const fitOrder = { excellent: 0, good: 1, acceptable: 2, poor: 3 };
    recommendations.sort((a, b) => fitOrder[a.resource_fit] - fitOrder[b.resource_fit]);

    return {
      recommended_models: recommendations.slice(0, 10), // Top 10 recommendations
      system_optimization_tips: optimizationTips,
      resource_warnings: warnings
    };
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
   * Estimate GPU memory requirement for a model
   */
  private estimateGPUMemoryRequirement(model: Model): number {
    // Only image models typically require GPU memory
    if (model.type !== 'image') {
      return 0;
    }

    let baseRequirement = model.size || 0;

    // GPU memory requirements for image models
    if (model.subtype === 'stable-diffusion') {
      // SD models need significant GPU memory
      const baseModel = model.metadata?.base_model || 'SD 1.5';
      if (baseModel.includes('SDXL')) {
        baseRequirement = Math.max(baseRequirement, 8 * 1024 * 1024 * 1024); // At least 8GB for SDXL
      } else {
        baseRequirement = Math.max(baseRequirement, 4 * 1024 * 1024 * 1024); // At least 4GB for SD 1.5/2.x
      }
    } else if (model.subtype === 'flux') {
      // Flux models are more memory efficient but still need substantial GPU memory
      baseRequirement = Math.max(baseRequirement, 6 * 1024 * 1024 * 1024); // At least 6GB for Flux
    }

    return baseRequirement;
  }

  /**
   * Calculate efficiency score for a model based on resource usage
   */
  private calculateEfficiencyScore(usage: {
    average_memory_usage: number;
    average_cpu_usage: number;
    total_inference_time_ms: number;
    inference_count: number;
  }): number {
    if (!usage || usage.inference_count === 0) return 0;
    
    // Calculate metrics with safe defaults
    const avgInferenceTime = usage.total_inference_time_ms / usage.inference_count;
    const memoryEfficiency = 1 / ((usage.average_memory_usage || 0) / (1024 * 1024 * 1024) + 1); // Inverse of GB usage
    const cpuEfficiency = 1 / ((usage.average_cpu_usage || 0) / 100 + 1); // Inverse of CPU usage percentage
    const speedEfficiency = 1 / (avgInferenceTime / 1000 + 1); // Inverse of seconds per inference
    
    // Weighted score (0-100)
    const score = (memoryEfficiency * 0.3 + cpuEfficiency * 0.2 + speedEfficiency * 0.5) * 100;
    return Math.round(score * 10) / 10; // Round to 1 decimal place
  }
}