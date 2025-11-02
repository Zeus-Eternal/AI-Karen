/**
 * Model-specific utility functions
 */

import type { Model } from "../../model-utils";

/**
 * Generate model ID from filename and type
 */
export function generateModelId(filename: string, type: string): string {
  // Remove file extension and create a clean ID
  const baseName = filename.replace(/\.(gguf|bin|safetensors)$/i, '');
  const cleanName = baseName.toLowerCase()
    .replace(/[^a-z0-9.-]/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
  
  return `${type}-${cleanName}`;
}

/**
 * Generate human-readable model name from filename and metadata
 */
export function generateModelName(filename: string, metadata: Record<string, any>): string {
  // Remove file extension
  let name = filename.replace(/\.(gguf|bin|safetensors)$/i, '');
  
  // Clean up common patterns
  name = name.replace(/[._-]/g, ' ');
  name = name.replace(/\s+/g, ' ');
  
  // Capitalize words
  name = name.split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
  
  // Add quantization info if available
  if (metadata.quantization) {
    name += ` (${metadata.quantization})`;
  }
  
  return name.trim();
}

/**
 * Generate model description from metadata
 */
export function generateModelDescription(metadata: Record<string, any>, type: string): string {
  const parts: string[] = [];
  
  if (metadata.parameter_count) {
    parts.push(`${metadata.parameter_count} parameter model`);
  }
  
  if (metadata.architecture) {
    parts.push(`based on ${metadata.architecture} architecture`);
  }
  
  if (metadata.quantization) {
    parts.push(`with ${metadata.quantization} quantization`);
  }
  
  if (metadata.context_length) {
    parts.push(`supporting ${metadata.context_length} token context`);
  }
  
  const description = parts.join(', ');
  return description.charAt(0).toUpperCase() + description.slice(1);
}

/**
 * Extract model metadata from filename patterns
 */
export function extractModelMetadataFromFilename(filename: string): Partial<Record<string, any>> {
  const metadata: Record<string, any> = {};
  
  // Extract quantization info (Q4_0, Q8_0, etc.)
  const quantMatch = filename.match(/[Qq](\d+)_(\d+)/);
  if (quantMatch) {
    metadata.quantization = `Q${quantMatch[1]}_${quantMatch[2]}`;
  }
  
  // Extract parameter count (7B, 13B, etc.)
  const paramMatch = filename.match(/(\d+(?:\.\d+)?)[Bb]/);
  if (paramMatch) {
    metadata.parameter_count = `${paramMatch[1]}B`;
  }
  
  // Extract model architecture hints
  if (filename.toLowerCase().includes('llama')) {
    metadata.architecture = 'LLaMA';
  } else if (filename.toLowerCase().includes('mistral')) {
    metadata.architecture = 'Mistral';
  } else if (filename.toLowerCase().includes('codellama')) {
    metadata.architecture = 'Code Llama';
  }
  
  return metadata;
}

/**
 * Compare models for sorting purposes
 */
export function compareModels(a: Model, b: Model, sortBy: string = 'name'): number {
  switch (sortBy) {
    case 'name':
      return a.name.localeCompare(b.name);
    case 'size':
      return (a.size || 0) - (b.size || 0);
    case 'type':
      return (a.type || '').localeCompare(b.type || '');
    case 'provider':
      return (a.provider || '').localeCompare(b.provider || '');
    default:
      return 0;
  }
}

/**
 * Filter models by various criteria
 */
export function filterModels(
  models: Model[], 
  filters: {
    type?: string;
    provider?: string;
    capability?: string;
    status?: string;
    healthyOnly?: boolean;
  }
): Model[] {
  return models.filter(model => {
    if (filters.type && model.type !== filters.type) {
      return false;
    }
    
    if (filters.provider && model.provider !== filters.provider) {
      return false;
    }
    
    if (filters.capability && !model.capabilities?.includes(filters.capability)) {
      return false;
    }
    
    if (filters.status) {
      const isLocal = model.status === 'local';
      const isAvailable = model.status === 'available';
      const isDownloading = model.status === 'downloading';
      
      switch (filters.status) {
        case 'local':
          if (!isLocal) return false;
          break;
        case 'available':
          if (!isAvailable) return false;
          break;
        case 'downloading':
          if (!isDownloading) return false;
          break;
      }
    }
    
    if (filters.healthyOnly && model.health && 'status' in model.health && model.health.status !== 'healthy') {
      return false;
    }
    
    return true;

}

/**
 * Group models by a specific property
 */
export function groupModelsByProperty<T extends keyof Model>(
  models: Model[], 
  property: T
): Record<string, Model[]> {
  const groups: Record<string, Model[]> = {};
  
  models.forEach(model => {
    const value = String(model[property] || 'unknown');
    if (!groups[value]) {
      groups[value] = [];
    }
    groups[value].push(model);

  return groups;
}

/**
 * Calculate model efficiency score based on performance metrics
 */
export function calculateModelEfficiencyScore(model: Model): number {
  let score = 0;
  let factors = 0;
  
  // Health factor (40% weight)
  if (model.health && 'status' in model.health) {
    if (model.health.status === 'healthy') {
      score += 40;
    } else if (model.health.status === 'warning') {
      score += 20;
    }
  }
  factors += 40;
  
  // Size factor (20% weight) - smaller is better for efficiency
  if (model.size) {
    const sizeGB = model.size / (1024 * 1024 * 1024);
    if (sizeGB < 1) {
      score += 20;
    } else if (sizeGB < 5) {
      score += 15;
    } else if (sizeGB < 10) {
      score += 10;
    } else {
      score += 5;
    }
  }
  factors += 20;
  
  // Local availability factor (20% weight)
  if (model.status === 'local') {
    score += 20;
  } else if (model.status === 'available') {
    score += 10;
  }
  factors += 20;
  
  // Capability factor (20% weight)
  const capabilityCount = model.capabilities?.length || 0;
  if (capabilityCount >= 3) {
    score += 20;
  } else if (capabilityCount >= 2) {
    score += 15;
  } else if (capabilityCount >= 1) {
    score += 10;
  }
  factors += 20;
  
  return factors > 0 ? Math.round((score / factors) * 100) : 0;
}