/**
 * Resource calculation and management utilities
 */

import { SystemResourceInfo, ResourceLoadabilityCheck } from "../types";

/**
 * Format memory size in human readable format
 */
export function formatMemorySize(bytes: number): string {
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let size = bytes;
  let unitIndex = 0;
  
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }
  
  return `${Math.round(size * 10) / 10} ${units[unitIndex]}`;
}

/**
 * Convert memory size string to bytes
 */
export function parseMemorySize(sizeStr: string): number {
  const match = sizeStr.match(/^(\d+(?:\.\d+)?)\s*(B|KB|MB|GB|TB)$/i);
  if (!match) {
    return 0;
  }
  
  const value = parseFloat(match[1]);
  const unit = match[2].toUpperCase();
  
  const multipliers: Record<string, number> = {
    'B': 1,
    'KB': 1024,
    'MB': 1024 * 1024,
    'GB': 1024 * 1024 * 1024,
    'TB': 1024 * 1024 * 1024 * 1024
  };
  
  return Math.round(value * (multipliers[unit] || 1));
}

/**
 * Calculate memory usage percentage
 */
export function calculateMemoryUsagePercentage(used: number, total: number): number {
  if (total === 0) return 0;
  return Math.round((used / total) * 100);
}

/**
 * Estimate model memory requirements based on size and type
 */
export function estimateModelMemoryRequirements(
  modelSize: number, 
  modelType: string = 'text'
): { memory: number; gpu_memory?: number; disk_space: number } {
  // Base memory requirement is typically 1.2-1.5x model size for loading
  const baseMemoryMultiplier = 1.3;
  const memory = Math.round(modelSize * baseMemoryMultiplier);
  
  // GPU memory requirements (if GPU acceleration is available)
  let gpu_memory: number | undefined;
  if (modelType === 'text' || modelType === 'multimodal') {
    // Text models can benefit from GPU acceleration
    gpu_memory = Math.round(modelSize * 1.1); // Slightly less than system memory
  } else if (modelType === 'image') {
    // Image models typically require more GPU memory
    gpu_memory = Math.round(modelSize * 1.4);
  }
  
  // Disk space requirement includes model file plus temporary files
  const disk_space = Math.round(modelSize * 1.1);
  
  return {
    memory,
    gpu_memory,
    disk_space
  };
}

/**
 * Check if system resources can handle a model
 */
export function checkResourceFeasibility(
  modelSize: number,
  modelType: string,
  systemResources: SystemResourceInfo
): ResourceLoadabilityCheck {
  const requirements = estimateModelMemoryRequirements(modelSize, modelType);
  
  // Check system memory
  const memoryAvailable = systemResources.memory.available;
  const canLoadInMemory = memoryAvailable >= requirements.memory;
  
  // Check GPU memory if available
  let gpuMemoryAvailable = 0;
  if (systemResources.gpu.length > 0 && requirements.gpu_memory) {
    gpuMemoryAvailable = Math.max(...systemResources.gpu.map(gpu => gpu.memory_available));
  }
  
  // Check disk space
  const diskAvailable = systemResources.disk.available;
  const hasEnoughDiskSpace = diskAvailable >= requirements.disk_space;
  
  // Determine if model can be loaded
  const canLoad = canLoadInMemory && hasEnoughDiskSpace;
  
  let reason: string | undefined;
    if (!canLoad) {
      const reasons: string[] = [];
      if (!canLoadInMemory) {
        reasons.push(`Insufficient memory: need ${formatMemorySize(requirements.memory)}, have ${formatMemorySize(memoryAvailable)}`);
      }
      if (!hasEnoughDiskSpace) {
        reasons.push(`Insufficient disk space: need ${formatMemorySize(requirements.disk_space)}, have ${formatMemorySize(diskAvailable)}`);
      }
      if (requirements.gpu_memory && !canLoadInGPU) {
        reasons.push(
          `Insufficient GPU memory: need ${formatMemorySize(requirements.gpu_memory)}, have ${formatMemorySize(gpuMemoryAvailable)}`
        );
      }
      reason = reasons.join('; ');
    }
  
  return {
    canLoad,
    reason,
    resourceRequirements: requirements,
    systemResources: {
      memory_available: memoryAvailable,
      gpu_memory_available: gpuMemoryAvailable > 0 ? gpuMemoryAvailable : undefined,
      disk_available: diskAvailable
    }
  };
}

/**
 * Calculate resource utilization score (0-100)
 */
export function calculateResourceUtilizationScore(resources: SystemResourceInfo): number {
  let totalScore = 0;
  let components = 0;
  
  // CPU utilization (lower is better)
  const cpuScore = Math.max(0, 100 - resources.cpu.usage_percent);
  totalScore += cpuScore;
  components++;
  
  // Memory utilization (lower is better)
  const memoryScore = Math.max(0, 100 - resources.memory.usage_percent);
  totalScore += memoryScore;
  components++;
  
  // GPU utilization (average across all GPUs, lower is better)
  if (resources.gpu.length > 0) {
    const avgGpuUtilization = resources.gpu.reduce((sum, gpu) => sum + gpu.utilization_percent, 0) / resources.gpu.length;
    const gpuScore = Math.max(0, 100 - avgGpuUtilization);
    totalScore += gpuScore;
    components++;
  }
  
  // Disk utilization (lower is better)
  const diskScore = Math.max(0, 100 - resources.disk.usage_percent);
  totalScore += diskScore;
  components++;
  
  return components > 0 ? Math.round(totalScore / components) : 0;
}

/**
 * Get resource recommendations based on current usage
 */
export function getResourceRecommendations(resources: SystemResourceInfo): string[] {
  const recommendations: string[] = [];
  
  // Memory recommendations
  if (resources.memory.usage_percent > 85) {
    recommendations.push("High memory usage detected. Consider closing unused applications or using smaller models.");
  } else if (resources.memory.usage_percent > 70) {
    recommendations.push("Memory usage is elevated. Monitor for potential issues with larger models.");
  }
  
  // CPU recommendations
  if (resources.cpu.usage_percent > 90) {
    recommendations.push("High CPU usage detected. Consider reducing concurrent operations.");
  }
  
  // GPU recommendations
  if (resources.gpu.length > 0) {
    const highUtilizationGPUs = resources.gpu.filter(gpu => gpu.utilization_percent > 85);
    if (highUtilizationGPUs.length > 0) {
      recommendations.push(`High GPU utilization detected on ${highUtilizationGPUs.length} GPU(s). Consider load balancing or using CPU inference.`);
    }
    
    const lowMemoryGPUs = resources.gpu.filter(gpu => (gpu.memory_available / gpu.memory_total) < 0.2);
    if (lowMemoryGPUs.length > 0) {
      recommendations.push(`Low GPU memory available on ${lowMemoryGPUs.length} GPU(s). Consider using smaller models or quantized versions.`);
    }
  }
  
  // Disk recommendations
  if (resources.disk.usage_percent > 90) {
    recommendations.push("Disk space is critically low. Consider cleaning up unused model files.");
  } else if (resources.disk.usage_percent > 80) {
    recommendations.push("Disk space is running low. Monitor storage usage when downloading new models.");
  }
  
  return recommendations;
}

/**
 * Calculate optimal batch size based on available memory
 */
export function calculateOptimalBatchSize(
  availableMemory: number,
  modelMemoryUsage: number,
  itemMemoryUsage: number = 1024 * 1024 // 1MB per item default
): number {
  const safeMemory = availableMemory * 0.8; // Use 80% of available memory for safety
  const memoryForBatch = safeMemory - modelMemoryUsage;
  
  if (memoryForBatch <= 0) {
    return 1; // Minimum batch size
  }
  
  const maxBatchSize = Math.floor(memoryForBatch / itemMemoryUsage);
  return Math.max(1, Math.min(maxBatchSize, 32)); // Cap at 32 for practical reasons
}

/**
 * Estimate inference time based on model size and system resources
 */
export function estimateInferenceTime(
  modelSize: number,
  systemResources: SystemResourceInfo,
  useGPU: boolean = false
): number {
  // Base inference time per GB of model (in milliseconds)
  let baseTimePerGB = 1000; // 1 second per GB on CPU
  
  if (useGPU && systemResources.gpu.length > 0) {
    // GPU inference is typically 5-10x faster
    baseTimePerGB = 150; // 150ms per GB on GPU
  }
  
  // Adjust based on CPU performance (rough estimation)
  const cpuFactor = Math.max(0.5, (100 - systemResources.cpu.usage_percent) / 100);
  
  const modelSizeGB = modelSize / (1024 * 1024 * 1024);
  const estimatedTime = modelSizeGB * baseTimePerGB * (1 / cpuFactor);
  
  return Math.round(estimatedTime);
}