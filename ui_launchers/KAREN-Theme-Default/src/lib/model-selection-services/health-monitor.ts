/**
 * Model Health Monitoring Service
 */

import type { Model, ModelHealth } from "../model-utils";
import { getKarenBackend } from "../karen-backend";
import { BaseModelService } from "./base-service";

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
      // 1) Check file existence and accessibility
      if (model.local_path) {
        try {
          const backend = getKarenBackend();
          const response = await this.withTimeout(
            backend.makeRequestPublic(`/api/models/health/file-check`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ path: model.local_path }),
            }),
            this.DEFAULT_TIMEOUT_MS,
            "file-check"
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
          issues.push(`File accessibility check failed: ${String(error)}`);
        }
      }

      // 2) Estimate memory requirements
      memoryRequirement = this.estimateMemoryRequirement(model);

      // 3) Check system memory availability
      const systemMemory = await this.getSystemMemoryInfo();
      if (memoryRequirement > systemMemory.available) {
        issues.push(
          `Insufficient memory: requires ${this.formatMemorySize(
            memoryRequirement
          )}, available ${this.formatMemorySize(systemMemory.available)}`
        );
      }

      // 4) Validate model format compatibility
      const formatValidation = this.validateModelFormat(model);
      if (!formatValidation.valid) {
        issues.push(`Format validation failed: ${formatValidation.reason}`);
      }

      // 5) Provider-specific compatibility
      const providerCompatibility = await this.checkProviderCompatibility(model);
      if (!providerCompatibility.compatible) {
        issues.push(
          `Provider compatibility issue: ${providerCompatibility.reason}`
        );
      }

      // 6) Optional load test (only if system has headroom and no blocking issues)
      if (issues.length === 0 && systemMemory.available > memoryRequirement * 1.5) {
        try {
          const loadTest = await this.performModelLoadTest(model);
          performanceMetrics.load_time_ms = loadTest.loadTime;
          performanceMetrics.memory_usage_mb =
            loadTest.memoryUsage / (1024 * 1024);

          if (loadTest.failed) {
            issues.push(`Load test failed: ${loadTest.error ?? "unknown error"}`);
          }
        } catch (error) {
          // Load test failure is non-fatal; log and continue
          this.logError(`Load test failed for ${model.id}:`, error);
        }
      }

      // 7) Model-specific health indicators
      const modelSpecificHealth = await this.checkModelSpecificHealth(model);
      if (Array.isArray(modelSpecificHealth.issues) && modelSpecificHealth.issues.length > 0) {
        issues.push(...modelSpecificHealth.issues);
      }
      Object.assign(performanceMetrics, modelSpecificHealth.metrics);
    } catch (error) {
      issues.push(`Health check failed: ${String(error)}`);
    }

    const health: ModelHealth = {
      is_healthy: issues.length === 0,
      last_check: new Date().toISOString(),
      issues,
      performance_metrics:
        Object.keys(performanceMetrics).length > 0 ? performanceMetrics : undefined,
      memory_requirement: memoryRequirement,
    };

    // Cache and return
    this.healthCache.set(model.id, health);
    return health;
  }

  /**
   * Get cached health status or perform new check
   */
  async getModelHealthStatus(
    modelId: string,
    model?: Model
  ): Promise<ModelHealth | null> {
    const cached = this.healthCache.get(modelId);
    if (cached && this.isHealthCacheValid(cached)) {
      return cached;
    }
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

    // Overhead by type/subtype
    switch (model.type) {
      case "text":
        if (model.subtype === "llama-cpp") {
          const quantization = String(model.metadata?.quantization || "Q4_K_M");
          if (quantization.includes("Q4")) baseRequirement *= 1.2;
          else if (quantization.includes("Q8")) baseRequirement *= 1.4;
          else baseRequirement *= 1.3;
        } else if (model.subtype === "transformers") {
          baseRequirement *= 1.8; // activations/graphs overhead
        }
        break;

      case "image":
        if (model.subtype === "stable-diffusion") {
          baseRequirement *= 2.0; // UNet/VAE overhead
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

    // Minimum requirement guard
    return Math.max(baseRequirement, 512 * 1024 * 1024);
  }

  /**
   * Get system memory information
   */
  private async getSystemMemoryInfo(): Promise<{
    total: number;
    available: number;
    used: number;
    gpu_memory?: Record<
      string,
      { total: number; available: number; used: number }
    >;
  }> {
    try {
      const backend = getKarenBackend();
      const response = await this.withTimeout(
        backend.makeRequestPublic("/api/system/memory"),
        this.DEFAULT_TIMEOUT_MS,
        "system-memory"
      );

      const memoryInfo = response as {
        total: number;
        available: number;
        used: number;
        gpu_memory?: Record<
          string,
          { total: number; available: number; used: number }
        >;
      };
      return memoryInfo;
    } catch (error) {
      this.logError("Failed to get system memory info:", error);
      // Conservative fallback
      return {
        total: 8 * 1024 * 1024 * 1024,
        available: 4 * 1024 * 1024 * 1024,
        used: 4 * 1024 * 1024 * 1024,
      };
    }
  }

  /**
   * Validate model format compatibility
   */
  private validateModelFormat(model: Model): { valid: boolean; reason?: string } {
    if (!model.format) {
      return { valid: false, reason: "Model format not specified" };
    }

    switch (model.type) {
      case "text":
        if (model.subtype === "llama-cpp" && model.format !== "gguf") {
          return { valid: false, reason: "llama-cpp models must use GGUF format" };
        }
        if (
          model.subtype === "transformers" &&
          !["safetensors", "pytorch"].includes(model.format)
        ) {
          return {
            valid: false,
            reason: "transformers models must use safetensors or pytorch format",
          };
        }
        break;

      case "image":
        if (!["safetensors", "diffusers", "pytorch"].includes(model.format)) {
          return {
            valid: false,
            reason:
              "image models must use safetensors, diffusers, or pytorch format",
          };
        }
        break;

      case "embedding":
        if (!["safetensors", "pytorch"].includes(model.format)) {
          return {
            valid: false,
            reason: "embedding models must use safetensors or pytorch format",
          };
        }
        break;
    }

    return { valid: true };
  }

  /**
   * Check provider-specific compatibility
   */
  private async checkProviderCompatibility(
    model: Model
  ): Promise<{ compatible: boolean; reason?: string }> {
    try {
      const backend = getKarenBackend();
      const response = await this.withTimeout(
        backend.makeRequestPublic("/api/providers/compatibility", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            provider: model.provider,
            model_type: model.type,
            format: model.format,
            metadata: model.metadata,
          }),
        }),
        this.DEFAULT_TIMEOUT_MS,
        "provider-compat"
      );

      const compatibility = response as {
        compatible: boolean;
        reason?: string;
      };

      return {
        compatible: compatibility.compatible,
        reason: compatibility.reason,
      };
    } catch (error) {
      // Assume compatible on check failure; log to avoid blocking model usage
      this.logError(
        `Provider compatibility check failed for ${model.id}:`,
        error
      );
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
      const response = await this.withTimeout(
        backend.makeRequestPublic("/api/models/load-test", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            model_id: model.id,
            timeout_ms: 30_000,
          }),
        }),
        this.DEFAULT_TIMEOUT_MS,
        "model-load-test"
      );

      const loadTest = response as {
        success: boolean;
        memory_usage?: number;
        error?: string;
      };

      return {
        loadTime: Date.now() - startTime,
        memoryUsage: loadTest.memory_usage || 0,
        failed: !loadTest.success,
        error: loadTest.error,
      };
    } catch (error) {
      return {
        loadTime: Date.now() - startTime,
        memoryUsage: 0,
        failed: true,
        error: String(error),
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
      switch (model.type) {
        case "text":
          if (model.subtype === "llama-cpp") {
            if (!model.metadata?.quantization) {
              issues.push("GGUF quantization information missing");
            }
            if (!model.metadata?.architecture) {
              issues.push("Model architecture information missing");
            }
            metrics.estimated_tokens_per_second = this.estimateTokensPerSecond(
              model
            );
          } else if (model.subtype === "transformers") {
            if (!model.metadata?.model_type) {
              issues.push("Transformers model type information missing");
            }
            const architectures = model.metadata?.architectures as unknown[];
            if (!Array.isArray(architectures) || !architectures.length) {
              issues.push("Model architecture information missing");
            }
          }
          break;

        case "image":
          if (model.subtype === "stable-diffusion") {
            if (!model.metadata?.base_model) {
              issues.push("Stable Diffusion base model information missing");
            }
            if (!model.metadata?.resolution) {
              issues.push("Image resolution information missing");
            }
            metrics.estimated_images_per_minute =
              this.estimateImageGenerationSpeed(model);
          } else if (model.subtype === "flux") {
            if (!model.metadata?.variant) {
              issues.push("Flux variant information missing");
            }
          }
          break;

        case "embedding":
          if (
            !model.metadata?.max_position_embeddings &&
            !model.metadata?.model_max_length
          ) {
            issues.push("Embedding model context length information missing");
          }
          break;
      }

      // Common checks
      if (model.size && model.size > 50 * 1024 * 1024 * 1024) {
        issues.push("Model size is unusually large, may cause performance issues");
      }

      const contextLength = Number(model.metadata?.context_length);
      if (contextLength && contextLength > 32768) {
        issues.push("Large context length may require significant memory");
      }
    } catch (error) {
      issues.push(`Model-specific health check failed: ${String(error)}`);
    }

    return { issues, metrics };
  }

  /**
   * Estimate tokens per second for text models
   */
  private estimateTokensPerSecond(model: Model): number {
    const sizeGB = (model.size || 0) / (1024 * 1024 * 1024);
    const quantization = String(model.metadata?.quantization || "Q4_K_M");

    let baseSpeed = 50; // conservative baseline
    if (sizeGB < 1) baseSpeed = 100;
    else if (sizeGB < 3) baseSpeed = 80;
    else if (sizeGB < 7) baseSpeed = 60;
    else if (sizeGB < 15) baseSpeed = 40;
    else baseSpeed = 20;

    if (quantization.includes("Q4")) baseSpeed *= 1.2;
    else if (quantization.includes("Q8")) baseSpeed *= 0.8;
    else if (quantization.includes("Q2")) baseSpeed *= 1.5;

    return Math.round(baseSpeed);
  }

  /**
   * Estimate image generation speed for image models
   */
  private estimateImageGenerationSpeed(model: Model): number {
    const sizeGB = (model.size || 0) / (1024 * 1024 * 1024);
    const baseModel = String(model.metadata?.base_model || "SD 1.5");

    let baseSpeed = 2; // images/min baseline
    if (baseModel.includes("SDXL")) baseSpeed = 1;
    else if (baseModel.includes("SD 2")) baseSpeed = 1.5;

    if (sizeGB > 10) baseSpeed *= 0.7;
    else if (sizeGB < 3) baseSpeed *= 1.3;

    return Math.round(baseSpeed * 10) / 10;
  }

  /**
   * Clear health cache
   */
  clearCache(): void {
    this.healthCache.clear();
  }
}
