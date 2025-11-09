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
  private performanceHistory: Map<string, PerformanceHistoryEntry[]> = new Map();
  private readonly MAX_HISTORY_ENTRIES = 100;
  protected readonly PERFORMANCE_CACHE_DURATION = 60_000; // 1 minute

  /**
   * Record performance data for a model
   */
  recordPerformanceData(
    modelId: string,
    modelName: string,
    data: {
      load_time_ms?: number;
      memory_usage_mb?: number;
      inference_speed?: number; // tokens/sec
      generation_time_ms?: number;
      gpu_utilization_percent?: number;
      cpu_utilization_percent?: number;
      // Optional image path: images/min (if your ModelPerformanceData supports it)
      inference_speed_images_per_minute?: number;
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
      // carry optional images/min if present in your type
      inference_speed_images_per_minute:
        data.inference_speed_images_per_minute ??
        existing?.inference_speed_images_per_minute,
      gpu_utilization_percent:
        data.gpu_utilization_percent ?? existing?.gpu_utilization_percent,
      cpu_utilization_percent:
        data.cpu_utilization_percent ?? existing?.cpu_utilization_percent ?? 0,
      generation_count:
        (existing?.generation_count ?? 0) + (data.generation_time_ms ? 1 : 0),
      total_generation_time_ms:
        (existing?.total_generation_time_ms ?? 0) +
        (data.generation_time_ms ?? 0),
      average_generation_time_ms: 0, // computed below
      last_used: now,
      performance_score: 0, // computed below
      efficiency_rating: "fair", // computed below
    };

    // Average generation time
    if (performanceData.generation_count > 0) {
      performanceData.average_generation_time_ms =
        performanceData.total_generation_time_ms /
        performanceData.generation_count;
    }

    // Score & rating
    performanceData.performance_score =
      this.calculatePerformanceScore(performanceData);
    performanceData.efficiency_rating = this.calculateEfficiencyRating(
      performanceData.performance_score
    );

    this.performanceData.set(modelId, performanceData);

    // Append to history
    this.addToHistory(modelId, {
      timestamp: now,
      load_time_ms: data.load_time_ms ?? existing?.load_time_ms ?? 0,
      memory_usage_mb: data.memory_usage_mb ?? existing?.memory_usage_mb ?? 0,
      inference_speed: data.inference_speed ?? undefined,
      generation_time_ms: data.generation_time_ms ?? undefined,
      resource_utilization: {
        cpu_percent: data.cpu_utilization_percent ?? 0,
        gpu_percent: data.gpu_utilization_percent ?? undefined,
        memory_percent: this.calculateMemoryPercent(
          data.memory_usage_mb ?? existing?.memory_usage_mb ?? 0
        ),
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
    return { model_id: modelId, entries, summary };
  }

  /**
   * Get performance comparison between models
   */
  getModelPerformanceComparison(modelIds: string[]): ModelPerformanceComparison {
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

    const sortedBySpeed = [...models].sort(
      (a, b) =>
        (b.inference_speed_tokens_per_second ?? 0) -
        (a.inference_speed_tokens_per_second ?? 0)
    );

    const sortedByMemory = [...models].sort(
      (a, b) => (a.memory_usage_mb ?? Number.MAX_SAFE_INTEGER) - (b.memory_usage_mb ?? Number.MAX_SAFE_INTEGER)
    );

    const sortedByOverall = [...models].sort(
      (a, b) => (b.performance_score ?? 0) - (a.performance_score ?? 0)
    );

    const rankedModels = models.map((model) => {
      const speedRank =
        sortedBySpeed.findIndex((m) => m.model_id === model.model_id) + 1;
      const memoryRank =
        sortedByMemory.findIndex((m) => m.model_id === model.model_id) + 1;
      const loadTimeRank =
        [...models]
          .sort((a, b) => (a.load_time_ms ?? Number.MAX_SAFE_INTEGER) - (b.load_time_ms ?? Number.MAX_SAFE_INTEGER))
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
      allModels.reduce((sum, m) => sum + (m.load_time_ms ?? 0), 0) /
      allModels.length;

    const averageMemoryUsage =
      allModels.reduce((sum, m) => sum + (m.memory_usage_mb ?? 0), 0) /
      allModels.length;

    const totalMemoryRequirement = allModels.reduce(
      (sum, m) => sum + (m.memory_usage_mb ?? 0),
      0
    );

    // Performance tiers
    const performanceTiers = { fast: 0, medium: 0, slow: 0 as number };
    allModels.forEach((model) => {
      const score = model.performance_score ?? 0;
      if (score >= 80) performanceTiers.fast++;
      else if (score >= 60) performanceTiers.medium++;
      else performanceTiers.slow++;
    });

    // Estimated capacity
    const textModels = allModels.filter(
      (m) => m.inference_speed_tokens_per_second !== undefined
    );
    const imageModels = allModels.filter(
      (m) => m.inference_speed_images_per_minute !== undefined
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
      healthCheckDuration: 0, // hook if you measure healthcheck timings
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

    const modelsWithPerformance = models.filter((model) => {
      const perfData = this.performanceData.get(model.id);
      if (!perfData) return false;
      if (typeof maxMemoryUsage === "number" && perfData.memory_usage_mb > maxMemoryUsage) {
        return false;
      }
      if ((perfData.performance_score ?? 0) < minPerformanceScore) {
        return false;
      }
      return true;
    });

    return modelsWithPerformance.sort((a, b) => {
      const aPerf = this.performanceData.get(a.id)!;
      const bPerf = this.performanceData.get(b.id)!;

      if (prioritizeSpeed) {
        const aSpeed = aPerf.inference_speed_tokens_per_second ?? 0;
        const bSpeed = bPerf.inference_speed_tokens_per_second ?? 0;
        if (aSpeed !== bSpeed) return bSpeed - aSpeed;
      }

      if (prioritizeMemoryEfficiency) {
        const aMem = aPerf.memory_usage_mb ?? Number.MAX_SAFE_INTEGER;
        const bMem = bPerf.memory_usage_mb ?? Number.MAX_SAFE_INTEGER;
        if (aMem !== bMem) return aMem - bMem;
      }

      // Default to overall performance score
      return (bPerf.performance_score ?? 0) - (aPerf.performance_score ?? 0);
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

  // ------- internals -------

  private calculatePerformanceScore(data: ModelPerformanceData): number {
    let score = 50; // base

    // Load time factor (faster is better)
    if ((data.load_time_ms ?? Number.MAX_SAFE_INTEGER) < 5000) score += 20;
    else if ((data.load_time_ms ?? Number.MAX_SAFE_INTEGER) < 10_000) score += 10;
    else if ((data.load_time_ms ?? 0) > 30_000) score -= 20;

    // Memory efficiency (lower is better)
    const mem = data.memory_usage_mb ?? Number.MAX_SAFE_INTEGER;
    if (mem < 2000) score += 15;
    else if (mem < 4000) score += 10;
    else if (mem > 8000) score -= 15;

    // Inference speed factor
    const tkps = data.inference_speed_tokens_per_second ?? 0;
    if (tkps > 50) score += 15;
    else if (tkps > 20) score += 10;
    else if (tkps > 0 && tkps < 5) score -= 10;

    // CPU utilization (balanced)
    const cpu = data.cpu_utilization_percent ?? 0;
    if (cpu > 0) {
      if (cpu < 80) score += 5;
      else if (cpu > 95) score -= 10;
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
    // Baseline assumption; you can wire in real system RAM
    const systemMemoryMb = 16 * 1024;
    return Math.min(100, (memoryUsageMb / systemMemoryMb) * 100);
  }

  private addToHistory(modelId: string, entry: PerformanceHistoryEntry): void {
    if (!this.performanceHistory.has(modelId)) {
      this.performanceHistory.set(modelId, []);
    }
    const history = this.performanceHistory.get(modelId)!;
    history.push(entry);
    // prune to max
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

    const avg = (nums: number[]) =>
      nums.length ? nums.reduce((s, n) => s + n, 0) / nums.length : 0;

    const averages = {
      load_time_ms: avg(entries.map((e) => e.load_time_ms ?? 0)),
      memory_usage_mb: avg(entries.map((e) => e.memory_usage_mb ?? 0)),
      inference_speed:
        avg(entries.filter((e) => e.inference_speed !== undefined).map((e) => e.inference_speed ?? 0)) || undefined,
      generation_time_ms:
        avg(entries.filter((e) => e.generation_time_ms !== undefined).map((e) => e.generation_time_ms ?? 0)) || undefined,
    };

    // Trends: compare first half vs. second half
    const mid = Math.floor(sortedEntries.length / 2);
    const firstHalf = sortedEntries.slice(0, mid);
    const secondHalf = sortedEntries.slice(mid);

    const trends = {
      load_time_trend: this.calculateTrend(
        avg(firstHalf.map((e) => e.load_time_ms ?? 0)),
        avg(secondHalf.map((e) => e.load_time_ms ?? 0))
      ),
      memory_trend: this.calculateTrend(
        avg(firstHalf.map((e) => e.memory_usage_mb ?? 0)),
        avg(secondHalf.map((e) => e.memory_usage_mb ?? 0))
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
    // lower is better (load time, memory)
    if (oldValue === 0) return "stable";
    const change = (newValue - oldValue) / oldValue;
    const threshold = 0.1; // 10%
    if (Math.abs(change) < threshold) return "stable";
    return change < 0 ? "improving" : "degrading";
  }

  private calculateSpeedTrend(
    firstHalf: PerformanceHistoryEntry[],
    secondHalf: PerformanceHistoryEntry[]
  ): "improving" | "stable" | "degrading" {
    const fh = firstHalf.filter((e) => e.inference_speed !== undefined);
    const sh = secondHalf.filter((e) => e.inference_speed !== undefined);
    if (fh.length === 0 || sh.length === 0) return "stable";

    const avg = (arr: PerformanceHistoryEntry[]) =>
      arr.reduce((s, e) => s + (e.inference_speed ?? 0), 0) / arr.length;

    const oldSpeed = avg(fh);
    const newSpeed = avg(sh);
    if (oldSpeed === 0) return "stable";

    const change = (newSpeed - oldSpeed) / oldSpeed;
    const threshold = 0.1; // 10%
    if (Math.abs(change) < threshold) return "stable";
    return change > 0 ? "improving" : "degrading"; // higher speed is better
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
      (model.inference_speed_tokens_per_second ?? 0) > 30
    ) {
      return `Good choice for speed-critical applications (${model.inference_speed_tokens_per_second} tokens/sec)`;
    }
    if ((model.memory_usage_mb ?? Number.MAX_SAFE_INTEGER) < 4000) {
      return `Memory-efficient option using only ${model.memory_usage_mb}MB`;
    }
    if ((model.load_time_ms ?? Number.MAX_SAFE_INTEGER) < 10_000) {
      return `Quick to load (${model.load_time_ms}ms startup time)`;
    }
    return `Balanced performance with ${model.efficiency_rating} efficiency rating`;
  }
}
