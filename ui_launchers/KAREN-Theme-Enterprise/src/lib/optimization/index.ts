/**
 * Optimization Module Index - Production Grade
 *
 * Centralized export hub for optimization utilities and types.
 */

import AutoScalerDefault, { AutoScaler as AutoScalerClass, AutoScalerError } from "./auto-scaler";
import CacheManagerDefault, { CacheManager as CacheManagerClass } from "./cache-manager";

export { AutoScalerClass as AutoScaler, AutoScalerError };
export type {
  ScalingDecision,
  ScalingStats,
  ScheduledScalingRule,
  InstanceMetrics,
  PredictiveModel,
  ScalingMetric,
  ScalingConfig,
} from "./auto-scaler";

export { CacheManagerClass as CacheManager };
export type {
  CacheStats,
  CacheConfig,
  InvalidationRule,
  MaybeWorker,
  CacheStrategy,
  CacheEntry,
} from "./cache-manager";

export const OptimizationModules = {
  AutoScaler: AutoScalerDefault,
  CacheManager: CacheManagerDefault,
};

export default OptimizationModules;
