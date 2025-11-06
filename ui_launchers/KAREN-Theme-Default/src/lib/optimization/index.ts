/**
 * Optimization Module Index - Production Grade
 *
 * Centralized export hub for optimization utilities and types.
 */

export { AutoScaler, AutoScalerError, default as AutoScaler } from './auto-scaler';
export type { ScalingDecision, ScalingStats, ScheduledScalingRule, InstanceMetrics, PredictiveModel, ScalingMetric, ScalingConfig } from './auto-scaler';

export { CacheManager, default as CacheManager } from './cache-manager';
export type { CacheStats, CacheConfig, InvalidationRule, MaybeWorker, CacheStrategy, CacheEntry } from './cache-manager';

