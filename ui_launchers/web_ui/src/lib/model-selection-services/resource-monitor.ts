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
  ModelRecommendation,
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

      // Defensive normalization
      return {
        ...resourceInfo,
        gpu: Array.isArray(resourceInfo.gpu) ? resourceInfo.gpu : [],
      };
    } catch (error) {
      this.logError("Failed to get system resource info:", error);
      // Return conservative estimates
      return {
        cpu: {
          cores: 4,
          usage_percent: 50,
        },
        memory: {
          total: 8 * 1024 * 1024 * 1024,
          available: 4 * 1024 * 1024 * 1024,
          used: 4 * 1024 * 1024 * 1024,
          usage_percent: 50,
        },
        gpu: [],
        disk: {
          total: 500 * 1024 * 1024 * 1024,
          available: 250 * 1024 * 1024 * 1024,
          used: 250 * 1024 * 1024 * 1024,
          usage_percent: 50,
        },
      };
    }
  }

  /**
   * Check if system has sufficient resources to load a model
   */
  async canLoadModel(model: Model): Promise<ResourceLoadabilityCheck> {
    const systemResources = await this.getSystemResourceInfo();
    const gpuList = Array.isArray(systemResources.gpu) ? systemResources.gpu : [];

    const memoryRequirement = this.estimateMemoryRequirement(model);
    const gpuMemoryRequirement = this.estimateGPUMemoryRequirement(model);
    const diskSpaceRequirement = model.size || 0;

    const toRR = {
      memory: memoryRequirement,
      gpu_memory: gpuMemoryRequirement,
      disk_space: diskSpaceRequirement,
    } as const;

    const toSR = {
      memory_available: systemResources.memory.available,
      gpu_memory_available:
        gpuList.length > 0
          ? Math.max(...gpuList.map((g) => g.memory_available))
          : undefined,
      disk_available: systemResources.disk.available,
    } as const;

    // Check memory availability
    if (memoryRequirement > systemResources.memory.available) {
      return {
        canLoad: false,
        reason: `Insufficient system memory: requires ${this.formatMemorySize(
          memoryRequirement
        )}, available ${this.formatMemorySize(systemResources.memory.available)}`,
        resourceRequirements: { ...toRR },
        systemResources: { ...toSR },
      };
    }

    // Check GPU memory if required AND GPU presence
    if (gpuMemoryRequirement > 0) {
      if (gpuList.length === 0) {
        return {
          canLoad: false,
          reason:
            "No GPU detected but the model requires GPU memory for optimal operation.",
          resourceRequirements: { ...toRR },
          systemResources: { ...toSR },
        };
      }
      const availableGPUMemory = Math.max(
        ...gpuList.map((gpu) => gpu.memory_available)
      );
      if (gpuMemoryRequirement > availableGPUMemory) {
        return {
          canLoad: false,
          reason: `Insufficient GPU memory: requires ${this.formatMemorySize(
            gpuMemoryRequirement
          )}, available ${this.formatMemorySize(availableGPUMemory)}`,
          resourceRequirements: { ...toRR },
          systemResources: { ...toSR },
        };
      }
    }

    // Check disk space (for temporary files during loading)
    const requiredDiskSpace = diskSpaceRequirement * 0.1; // 10% of model size for temp files
    if (requiredDiskSpace > systemResources.disk.available) {
      return {
        canLoad: false,
        reason: `Insufficient disk space: requires ${this.formatMemorySize(
          requiredDiskSpace
        )} for temporary files, available ${this.formatMemorySize(
          systemResources.disk.available
        )}`,
        resourceRequirements: { ...toRR },
        systemResources: { ...toSR },
      };
    }

    return {
      canLoad: true,
      resourceRequirements: { ...toRR },
      systemResources: { ...toSR },
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
    const gpuList = Array.isArray(systemResources.gpu) ? systemResources.gpu : [];
    const gpuMemoryRequirement = this.estimateGPUMemoryRequirement(model);

    // If no GPU memory required, return null
    if (gpuMemoryRequirement === 0) {
      return {
        gpu_id: null,
        reason: "Model does not require GPU",
        memory_available: 0,
      };
    }

    if (gpuList.length === 0) {
      return {
        gpu_id: null,
        reason: "No GPU available on this system.",
        memory_available: 0,
      };
    }

    // Find GPU with most available memory that can fit the model
    const suitableGPUs = gpuList
      .filter((gpu) => gpu.memory_available >= gpuMemoryRequirement)
      .sort((a, b) => b.memory_available - a.memory_available);

    if (suitableGPUs.length === 0) {
      const maxAvail = Math.max(...gpuList.map((g) => g.memory_available), 0);
      return {
        gpu_id: null,
        reason: `No GPU has sufficient memory (requires ${this.formatMemorySize(
          gpuMemoryRequirement
        )}, best available ${this.formatMemorySize(maxAvail)})`,
        memory_available: maxAvail,
      };
    }

    const optimalGPU = suitableGPUs[0];
    return {
      gpu_id: optimalGPU.id,
      gpu_name: optimalGPU.name,
      reason: `Selected GPU ${optimalGPU.id} (${optimalGPU.name}) with ${this.formatMemorySize(
        optimalGPU.memory_available
      )} available`,
      memory_available: optimalGPU.memory_available,
    };
  }

  /**
   * Monitor resource usage during model operations
   */
  async monitorResourceUsage(
    modelId: string,
    operation: "loading" | "inference" | "generation"
  ): Promise<{
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

    // Lightweight snapshot. In production, wire a sampler/observer to stream deltas.
    const monitoringData = {
      start_time: startTime.toISOString(),
      peak_memory_usage: startResources.memory.used,
      peak_gpu_memory_usage: startResources.gpu[0]?.memory_used,
      average_cpu_usage: startResources.cpu.usage_percent,
      average_gpu_utilization: startResources.gpu[0]?.utilization_percent,
    };

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
      const usage = (response || {}) as {
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
  async getResourceUsageHistory(
    timeRange: "1h" | "24h" | "7d" | "30d" = "24h"
  ): Promise<ResourceUsageHistoryEntry[]> {
    try {
      const backend = getKarenBackend();
      const response = await backend.makeRequestPublic(
        `/api/models/resource-usage/history?range=${timeRange}`
      );
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

        const efficiencyScore = this.calculateEfficiencyScore({
          average_memory_usage: typedEntry.average_memory_usage,
          average_cpu_usage: typedEntry.average_cpu_usage,
          total_inference_time_ms: typedEntry.total_inference_time_ms,
          inference_count: typedEntry.inference_count,
        });

        const result: ResourceUsageHistoryEntry = {
          model_id: typedEntry.model_id,
          model_name: typedEntry.model_id, // caller can enrich with friendly names
          average_memory_usage: typedEntry.average_memory_usage,
          peak_memory_usage: typedEntry.peak_memory_usage,
          average_gpu_memory_usage: typedEntry.average_gpu_memory_usage,
          peak_gpu_memory_usage: typedEntry.peak_gpu_memory_usage,
          average_cpu_usage: typedEntry.average_cpu_usage,
          peak_cpu_usage: typedEntry.peak_cpu_usage,
          total_inference_time_ms: typedEntry.total_inference_time_ms,
          inference_count: typedEntry.inference_count,
          efficiency_score: efficiencyScore,
        };

        return result;
      });
    } catch (error) {
      this.logError("Failed to get resource usage history:", error);
      return [];
    }
  }

  /**
   * Get system resource recommendations for optimal model selection
   */
  async getResourceRecommendations(models: Model[]): Promise<ResourceRecommendations> {
    const systemResources = await this.getSystemResourceInfo();
    const gpuList = Array.isArray(systemResources.gpu) ? systemResources.gpu : [];

    const recommendations: ModelRecommendation[] = [];
    const optimizationTips: string[] = [];
    const warnings: string[] = [];

    const maxAvailGpuMem =
      gpuList.length > 0
        ? Math.max(...gpuList.map((g) => g.memory_available))
        : 0;

    // Analyze each model's resource fit
    for (const model of models.filter((m) => m.status === "local")) {
      const memoryRequirement = this.estimateMemoryRequirement(model);
      const gpuMemoryRequirement = this.estimateGPUMemoryRequirement(model);

      const memoryRatio =
        systemResources.memory.available > 0
          ? memoryRequirement / systemResources.memory.available
          : Infinity;
      const gpuMemoryRatio =
        gpuMemoryRequirement > 0 && maxAvailGpuMem > 0
          ? gpuMemoryRequirement / maxAvailGpuMem
          : 0;

      let resourceFit: "excellent" | "good" | "acceptable" | "poor";
      let reason: string;

      if (memoryRatio < 0.3 && gpuMemoryRatio < 0.3) {
        resourceFit = "excellent";
        reason = "Low resource usage; excellent performance expected.";
      } else if (memoryRatio < 0.6 && gpuMemoryRatio < 0.6) {
        resourceFit = "good";
        reason = "Moderate resource usage; good performance expected.";
      } else if (memoryRatio < 0.8 && gpuMemoryRatio < 0.8) {
        resourceFit = "acceptable";
        reason = "High resource usage; may impact system performance.";
      } else {
        resourceFit = "poor";
        reason = "Very high resource usage; may cause system instability.";
      }

      recommendations.push({
        model_id: model.id,
        model_name: model.name,
        reason,
        resource_fit: resourceFit,
      });
    }

    // Optimization tips
    if (systemResources.memory.usage_percent > 80) {
      optimizationTips.push(
        "Consider closing other applications to free system memory."
      );
    }
    if (gpuList.some((gpu) => gpu.utilization_percent > 90)) {
      optimizationTips.push(
        "GPU heavily utilized; consider smaller models, lower batch sizes, or CPU inference."
      );
    }
    if (systemResources.cpu.usage_percent > 90) {
      optimizationTips.push(
        "CPU is heavily loaded; expect slower inference or reduce concurrency."
      );
    }

    // Warnings
    if (systemResources.memory.available < 2 * 1024 * 1024 * 1024) {
      warnings.push("Low available memory may prevent loading larger models.");
    }
    if (gpuList.length === 0) {
      warnings.push("No GPU detected; image generation models may be unavailable.");
    }
    if (systemResources.disk.usage_percent > 90) {
      warnings.push(
        "Low disk space may affect model loading and temporary file creation."
      );
    }

    // Sort recommendations by resource fit
    const fitOrder: Record<ModelRecommendation["resource_fit"], number> = {
      excellent: 0,
      good: 1,
      acceptable: 2,
      poor: 3,
    };
    recommendations.sort(
      (a, b) => fitOrder[a.resource_fit] - fitOrder[b.resource_fit]
    );

    return {
      recommended_models: recommendations.slice(0, 10),
      system_optimization_tips: optimizationTips,
      resource_warnings: warnings,
    };
  }

  /**
   * Estimate memory requirement for a model
   */
  private estimateMemoryRequirement(model: Model): number {
    let baseRequirement = model.size || 0;

    // Add overhead based on model type and format
    switch (model.type) {
      case "text":
        if (model.subtype === "llama-cpp") {
          // GGUF quantization overheads (rough guidance)
          const quantization = model.metadata?.quantization || "Q4_K_M";
          if (typeof quantization === "string" && quantization.includes("Q4")) {
            baseRequirement *= 1.2;
          } else if (
            typeof quantization === "string" &&
            quantization.includes("Q8")
          ) {
            baseRequirement *= 1.4;
          } else {
            baseRequirement *= 1.3;
          }
        } else if (model.subtype === "transformers") {
          baseRequirement *= 1.8; // activations / attention KV
        }
        break;

      case "image":
        if (model.subtype === "stable-diffusion") {
          baseRequirement *= 2.0; // VAE/UNet/attention blocks
        } else if (model.subtype === "flux") {
          baseRequirement *= 1.6;
        }
        break;

      case "embedding":
        baseRequirement *= 1.1;
        break;

      default:
        baseRequirement *= 1.5;
    }

    // Minimum memory requirement
    return Math.max(baseRequirement, 512 * 1024 * 1024); // At least 512MB
  }

  /**
   * Estimate GPU memory requirement for a model
   */
  private estimateGPUMemoryRequirement(model: Model): number {
    // Only image models typically require GPU memory
    if (model.type !== "image") return 0;

    let baseRequirement = model.size || 0;

    if (model.subtype === "stable-diffusion") {
      const baseModel = model.metadata?.base_model || "SD 1.5";
      if (typeof baseModel === "string" && baseModel.includes("SDXL")) {
        baseRequirement = Math.max(baseRequirement, 8 * 1024 * 1024 * 1024); // ≥ 8GB
      } else {
        baseRequirement = Math.max(baseRequirement, 4 * 1024 * 1024 * 1024); // ≥ 4GB
      }
    } else if (model.subtype === "flux") {
      baseRequirement = Math.max(baseRequirement, 6 * 1024 * 1024 * 1024); // ≥ 6GB
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
    const avgInferenceTime = usage.total_inference_time_ms / usage.inference_count; // ms
    const memoryGB = (usage.average_memory_usage || 0) / (1024 * 1024 * 1024);

    // Inverse scalers: the lower the consumption, the higher the score
    const memoryEfficiency = 1 / (memoryGB + 1);
    const cpuEfficiency = 1 / ((usage.average_cpu_usage || 0) / 100 + 1);
    const speedEfficiency = 1 / (avgInferenceTime / 1000 + 1);

    // Weighted score (0-100)
    const score = (memoryEfficiency * 0.3 + cpuEfficiency * 0.2 + speedEfficiency * 0.5) * 100;
    return Math.round(score * 10) / 10; // 1 decimal place
  }
}

export default ResourceMonitor;
