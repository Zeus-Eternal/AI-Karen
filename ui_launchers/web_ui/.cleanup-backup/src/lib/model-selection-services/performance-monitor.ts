/**
 * Performance Monitor Service - Tracks model performance metrics and history
 */

import type { Model } from "../model-utils";
import { BaseModelService } from "./base-service";
import {
  ModelPerformanceData,
  PerformanceHistory,
  PerformanceHistoryEntry,
  PerformanceHistorySummary,
  ModelPerformanceComparison,
  PerformanceMetrics,
} from "./types";

export class PerformanceMonitor extends BaseModelService {
  private performanceData: Map<string, ModelPerformanceData> = new Map();
  private performanceHistory: Map<string, PerformanceHistoryEntry[]> =
    new Map();
  private readonly MAX_HISTORY_ENTRIES = 100;
  protected readonly PERFORMANCE_CACHE_DURATION = 60000; // 1 minute

  /**
   * Record performance data for a model
   */
  recordPerformanceData(
    modelId: string,
    modelName: string,
    data: {
      load_time_ms?: number;
      memory_usage_mb?: number;
      inference_speed?: number;
      generation_time_ms?: number;
      gpu_utilization_percent?: number;
      cpu_utilization_percent?: number;
    }
  ): void {
    const existing = this.performanceData.get(modelId);
    const now = new Date().toISOString();

    // Update or create performance data
    const performanceData: ModelPerformanceData = {
      model_id: modelId,
      model_name: modelName,
      load_time_ms: data.load_time_ms ?? existing?.load_time_ms ?? 0,
      memory_usage_mb: data.memory_usage_mb ?? existing?.memory_usage_mb ?? 0,
      inference_speed_tokens_per_second:
        data.inference_speed ?? existing?.inference_speed_tokens_per_second,
      gpu_utilization_percent:
        data.gpu_utilization_percent ?? existing?.gpu_utilization_percent,
      cpu_utilization_percent:
        data.cpu_utilization_percent ?? existing?.cpu_utilization_percent ?? 0,
      generation_count:
        (existing?.generation_count ?? 0) + (data.generation_time_ms ? 1 : 0),
      total_generation_time_ms:
        (existing?.total_generation_time_ms ?? 0) +
        (data.generation_time_ms ?? 0),
      average_generation_time_ms: 0, // Will be calculated below
      last_used: now,
      performance_score: 0, // Will be calculated below
      efficiency_rating: "fair", // Will be calculated below
    };

    // Calculate average generation time
    if (performanceData.generation_count > 0) {
      performanceData.average_generation_time_ms =
        performanceData.total_generation_time_ms /
        performanceData.generation_count;
    }

    // Calculate performance score (0-100)
    performanceData.performance_score =
      this.calculatePerformanceScore(performanceData);
    performanceData.efficiency_rating = this.calculateEfficiencyRating(
      performanceData.performance_score
    );

    this.performanceData.set(modelId, performanceData);

    // Add to history
    this.addToHistory(modelId, {
      timestamp: now,
      load_time_ms: data.load_time_ms ?? 0,
      memory_usage_mb: data.memory_usage_mb ?? 0,
      inference_speed: data.inference_speed,
      generation_time_ms: data.generation_time_ms,
      resource_utilization: {
        cpu_percent: data.cpu_utilization_percent ?? 0,
        gpu_percent: data.gpu_utilization_percent,
        memory_percent: this.calculateMemoryPercent(data.memory_usage_mb ?? 0),
      },
    });
  }

  /**
   * Get performance data for a specific model
   */
  getModelPerformanceData(modelId: string): ModelPerformanceData | null {
    return this.performanceData.get(modelId) || null;
  }

  /**
   * Get performance history for a model
   */
  getModelPerformanceHistory(modelId: string): PerformanceHistory | null {
    const entries = this.performanceHistory.get(modelId);
    if (!entries || entries.length === 0) {
      return null;
    }

    const summary = this.calculateHistorySummary(entries);

    return {
      model_id: modelId,
      entries,
      summary,
    };
  }

  /**
   * Get performance comparison between models
   */
  getModelPerformanceComparison(
    modelIds: string[]
  ): ModelPerformanceComparison {
    const models = modelIds
      .map((id) => this.performanceData.get(id))
      .filter(Boolean) as ModelPerformanceData[];

    if (models.length === 0) {
      return {
        models: [],
        best_for_speed: "",
        best_for_memory: "",
        best_overall: "",
      };
    }

    // Sort models by different criteria
    const sortedBySpeed = [...models].sort(
      (a, b) =>
        (b.inference_speed_tokens_per_second ?? 0) -
        (a.inference_speed_tokens_per_second ?? 0)
    );

    const sortedByMemory = [...models].sort(
      (a, b) => a.memory_usage_mb - b.memory_usage_mb
    );

    const sortedByOverall = [...models].sort(
      (a, b) => b.performance_score - a.performance_score
    );

    // Create ranking data
    const rankedModels = models.map((model) => {
      const speedRank =
        sortedBySpeed.findIndex((m) => m.model_id === model.model_id) + 1;
      const memoryRank =
        sortedByMemory.findIndex((m) => m.model_id === model.model_id) + 1;
      const loadTimeRank =
        [...models]
          .sort((a, b) => a.load_time_ms - b.load_time_ms)
          .findIndex((m) => m.model_id === model.model_id) + 1;
      const overallRank =
        sortedByOverall.findIndex((m) => m.model_id === model.model_id) + 1;

      return {
        model_id: model.model_id,
        model_name: model.model_name,
        performance_score: model.performance_score,
        load_time_rank: loadTimeRank,
        memory_efficiency_rank: memoryRank,
        speed_rank: speedRank,
        overall_rank: overallRank,
        recommendation_reason: this.generateRecommendationReason(
          model,
          overallRank,
          models.length
        ),
      };
    });

    return {
      models: rankedModels,
      best_for_speed: sortedBySpeed[0]?.model_id ?? "",
      best_for_memory: sortedByMemory[0]?.model_id ?? "",
      best_overall: sortedByOverall[0]?.model_id ?? "",
    };
  }

  /**
   * Get aggregated performance metrics for all models
   */
  getAggregatedPerformanceMetrics(): PerformanceMetrics {
    const allModels = Array.from(this.performanceData.values());

    if (allModels.length === 0) {
      return {
        averageLoadTime: 0,
        averageMemoryUsage: 0,
        totalMemoryRequirement: 0,
        healthCheckDuration: 0,
        modelsByPerformanceTier: { fast: 0, medium: 0, slow: 0 },
        estimatedCapacity: { textTokensPerSecond: 0, imagesPerMinute: 0 },
      };
    }

    const averageLoadTime =
      allModels.reduce((sum, m) => sum + m.load_time_ms, 0) / allModels.length;
    const averageMemoryUsage =
      allModels.reduce((sum, m) => sum + m.memory_usage_mb, 0) /
      allModels.length;
    const totalMemoryRequirement = allModels.reduce(
      (sum, m) => sum + m.memory_usage_mb,
      0
    );

    // Categorize models by performance tiers
    const performanceTiers = { fast: 0, medium: 0, slow: 0 };
    allModels.forEach((model) => {
      if (model.performance_score >= 80) {
        performanceTiers.fast++;
      } else if (model.performance_score >= 60) {
        performanceTiers.medium++;
      } else {
        performanceTiers.slow++;
      }
    });

    // Calculate estimated capacity
    const textModels = allModels.filter(
      (m) => m.inference_speed_tokens_per_second
    );
    const imageModels = allModels.filter(
      (m) => m.inference_speed_images_per_minute
    );

    const avgTextSpeed =
      textModels.length > 0
        ? textModels.reduce(
            (sum, m) => sum + (m.inference_speed_tokens_per_second ?? 0),
            0
          ) / textModels.length
        : 0;

    const avgImageSpeed =
      imageModels.length > 0
        ? imageModels.reduce(
            (sum, m) => sum + (m.inference_speed_images_per_minute ?? 0),
            0
          ) / imageModels.length
        : 0;

    return {
      averageLoadTime,
      averageMemoryUsage,
      totalMemoryRequirement,
      healthCheckDuration: 0, // This would be tracked separately
      modelsByPerformanceTier: performanceTiers,
      estimatedCapacity: {
        textTokensPerSecond: avgTextSpeed,
        imagesPerMinute: avgImageSpeed,
      },
    };
  }

  /**
   * Get performance-based model recommendations
   */
  getPerformanceBasedRecommendations(
    models: Model[],
    criteria: {
      prioritizeSpeed?: boolean;
      prioritizeMemoryEfficiency?: boolean;
      maxMemoryUsage?: number;
      minPerformanceScore?: number;
    } = {}
  ): Model[] {
    const {
      prioritizeSpeed = false,
      prioritizeMemoryEfficiency = false,
      maxMemoryUsage,
      minPerformanceScore = 0,
    } = criteria;

    // Filter models that have performance data
    const modelsWithPerformance = models.filter((model) => {
      const perfData = this.performanceData.get(model.id);
      if (!perfData) return false;

      if (maxMemoryUsage && perfData.memory_usage_mb > maxMemoryUsage)
        return false;
      if (perfData.performance_score < minPerformanceScore) return false;

      return true;
    });

    // Sort based on criteria
    return modelsWithPerformance.sort((a, b) => {
      const aPerfData = this.performanceData.get(a.id)!;
      const bPerfData = this.performanceData.get(b.id)!;

      if (prioritizeSpeed) {
        const aSpeed = aPerfData.inference_speed_tokens_per_second ?? 0;
        const bSpeed = bPerfData.inference_speed_tokens_per_second ?? 0;
        if (aSpeed !== bSpeed) return bSpeed - aSpeed;
      }

      if (prioritizeMemoryEfficiency) {
        if (aPerfData.memory_usage_mb !== bPerfData.memory_usage_mb) {
          return aPerfData.memory_usage_mb - bPerfData.memory_usage_mb;
        }
      }

      // Default to overall performance score
      return bPerfData.performance_score - aPerfData.performance_score;
    });
  }

  /**
   * Clear performance data for a model
   */
  clearModelPerformanceData(modelId: string): void {
    this.performanceData.delete(modelId);
    this.performanceHistory.delete(modelId);
  }

  /**
   * Clear all performance data
   */
  clearAllPerformanceData(): void {
    this.performanceData.clear();
    this.performanceHistory.clear();
  }

  private calculatePerformanceScore(data: ModelPerformanceData): number {
    let score = 50; // Base score

    // Load time factor (faster is better)
    if (data.load_time_ms < 5000) score += 20;
    else if (data.load_time_ms < 10000) score += 10;
    else if (data.load_time_ms > 30000) score -= 20;

    // Memory efficiency factor (lower usage is better for efficiency)
    if (data.memory_usage_mb < 2000) score += 15;
    else if (data.memory_usage_mb < 4000) score += 10;
    else if (data.memory_usage_mb > 8000) score -= 15;

    // Inference speed factor
    if (data.inference_speed_tokens_per_second) {
      if (data.inference_speed_tokens_per_second > 50) score += 15;
      else if (data.inference_speed_tokens_per_second > 20) score += 10;
      else if (data.inference_speed_tokens_per_second < 5) score -= 10;
    }

    // Resource utilization factor (balanced usage is better)
    if (data.cpu_utilization_percent > 0) {
      if (data.cpu_utilization_percent < 80) score += 5;
      else if (data.cpu_utilization_percent > 95) score -= 10;
    }

    return Math.max(0, Math.min(100, score));
  }

  private calculateEfficiencyRating(
    score: number
  ): "excellent" | "good" | "fair" | "poor" {
    if (score >= 85) return "excellent";
    if (score >= 70) return "good";
    if (score >= 50) return "fair";
    return "poor";
  }

  private calculateMemoryPercent(memoryUsageMb: number): number {
    // Assume 16GB system memory as baseline
    const systemMemoryMb = 16 * 1024;
    return Math.min(100, (memoryUsageMb / systemMemoryMb) * 100);
  }

  private addToHistory(modelId: string, entry: PerformanceHistoryEntry): void {
    if (!this.performanceHistory.has(modelId)) {
      this.performanceHistory.set(modelId, []);
    }

    const history = this.performanceHistory.get(modelId)!;
    history.push(entry);

    // Keep only the most recent entries
    if (history.length > this.MAX_HISTORY_ENTRIES) {
      history.splice(0, history.length - this.MAX_HISTORY_ENTRIES);
    }
  }

  private calculateHistorySummary(
    entries: PerformanceHistoryEntry[]
  ): PerformanceHistorySummary {
    if (entries.length === 0) {
      return {
        total_entries: 0,
        date_range: { start: "", end: "" },
        averages: { load_time_ms: 0, memory_usage_mb: 0 },
        trends: {
          load_time_trend: "stable",
          memory_trend: "stable",
          speed_trend: "stable",
        },
      };
    }

    const sortedEntries = [...entries].sort(
      (a, b) =>
        new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );

    const averages = {
      load_time_ms:
        entries.reduce((sum, e) => sum + e.load_time_ms, 0) / entries.length,
      memory_usage_mb:
        entries.reduce((sum, e) => sum + e.memory_usage_mb, 0) / entries.length,
      inference_speed:
        entries.filter((e) => e.inference_speed).length > 0
          ? entries.reduce((sum, e) => sum + (e.inference_speed ?? 0), 0) /
            entries.filter((e) => e.inference_speed).length
          : undefined,
      generation_time_ms:
        entries.filter((e) => e.generation_time_ms).length > 0
          ? entries.reduce((sum, e) => sum + (e.generation_time_ms ?? 0), 0) /
            entries.filter((e) => e.generation_time_ms).length
          : undefined,
    };

    // Calculate trends by comparing first half vs second half of entries
    const midPoint = Math.floor(entries.length / 2);
    const firstHalf = sortedEntries.slice(0, midPoint);
    const secondHalf = sortedEntries.slice(midPoint);

    const trends = {
      load_time_trend: this.calculateTrend(
        firstHalf.reduce((sum, e) => sum + e.load_time_ms, 0) /
          firstHalf.length,
        secondHalf.reduce((sum, e) => sum + e.load_time_ms, 0) /
          secondHalf.length
      ),
      memory_trend: this.calculateTrend(
        firstHalf.reduce((sum, e) => sum + e.memory_usage_mb, 0) /
          firstHalf.length,
        secondHalf.reduce((sum, e) => sum + e.memory_usage_mb, 0) /
          secondHalf.length
      ),
      speed_trend: this.calculateSpeedTrend(firstHalf, secondHalf),
    };

    return {
      total_entries: entries.length,
      date_range: {
        start: sortedEntries[0].timestamp,
        end: sortedEntries[sortedEntries.length - 1].timestamp,
      },
      averages,
      trends,
    };
  }

  private calculateTrend(
    oldValue: number,
    newValue: number
  ): "improving" | "stable" | "degrading" {
    const threshold = 0.1; // 10% threshold
    const change = (newValue - oldValue) / oldValue;

    if (Math.abs(change) < threshold) return "stable";
    return change < 0 ? "improving" : "degrading"; // For load time and memory, lower is better
  }

  private calculateSpeedTrend(
    firstHalf: PerformanceHistoryEntry[],
    secondHalf: PerformanceHistoryEntry[]
  ): "improving" | "stable" | "degrading" {
    const firstHalfSpeeds = firstHalf.filter((e) => e.inference_speed);
    const secondHalfSpeeds = secondHalf.filter((e) => e.inference_speed);

    if (firstHalfSpeeds.length === 0 || secondHalfSpeeds.length === 0) {
      return "stable";
    }

    const oldSpeed =
      firstHalfSpeeds.reduce((sum, e) => sum + (e.inference_speed ?? 0), 0) /
      firstHalfSpeeds.length;
    const newSpeed =
      secondHalfSpeeds.reduce((sum, e) => sum + (e.inference_speed ?? 0), 0) /
      secondHalfSpeeds.length;

    const threshold = 0.1; // 10% threshold
    const change = (newSpeed - oldSpeed) / oldSpeed;

    if (Math.abs(change) < threshold) return "stable";
    return change > 0 ? "improving" : "degrading"; // For speed, higher is better
  }

  private generateRecommendationReason(
    model: ModelPerformanceData,
    rank: number,
    totalModels: number
  ): string {
    if (rank === 1) {
      return `Best overall performance with score of ${model.performance_score}`;
    }

    if (rank <= Math.ceil(totalModels * 0.3)) {
      return `High performance model with ${model.efficiency_rating} efficiency rating`;
    }

    if (
      model.inference_speed_tokens_per_second &&
      model.inference_speed_tokens_per_second > 30
    ) {
      return `Good choice for speed-critical applications (${model.inference_speed_tokens_per_second} tokens/sec)`;
    }

    if (model.memory_usage_mb < 4000) {
      return `Memory-efficient option using only ${model.memory_usage_mb}MB`;
    }

    if (model.load_time_ms < 10000) {
      return `Quick to load (${model.load_time_ms}ms startup time)`;
    }

    return `Balanced performance with ${model.efficiency_rating} efficiency rating`;
  }
}
