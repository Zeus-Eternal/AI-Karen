/**
 * Utility functions for model management and display
 */

export interface Model {
  id: string;
  name: string;
  provider: string;
  size: number;
  description: string;
  capabilities: string[];
  status: 'local' | 'available' | 'downloading';
  download_progress?: number;
  metadata: Record<string, any>;
  local_path?: string;
  download_url?: string;
  checksum?: string;
  disk_usage?: number;
  last_used?: string;
  download_date?: string;
  // Enhanced multi-modal support
  type?: 'text' | 'image' | 'embedding' | 'multimodal';
  subtype?: 'llama-cpp' | 'transformers' | 'stable-diffusion' | 'flux';
  format?: 'gguf' | 'safetensors' | 'pytorch' | 'diffusers';
  health?: ModelHealth;
  last_scanned?: string;
}

export interface ModelHealth {
  is_healthy: boolean;
  last_check: string;
  issues: string[];
  performance_metrics?: Record<string, number>;
  memory_requirement?: number;
}

export interface ModelScanResult {
  models: Model[];
  scan_metadata: {
    last_scan: string;
    scan_version: string;
    directories_scanned: string[];
    total_models_found: number;
    scan_duration_ms: number;
  };
}

export interface DirectoryScanOptions {
  includeHealth?: boolean;
  forceRefresh?: boolean;
  directories?: string[];
}

export interface ModelLibraryResponse {
  models: Model[];
  total_count: number;
  local_count: number;
  available_count: number;
}

/**
 * Format file size in human readable format
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

/**
 * Get provider icon based on provider name
 */
export function getProviderIcon(provider: string): string {
  switch (provider.toLowerCase()) {
    case 'transformers':
      return '🤖';
    case 'llama-cpp':
      return '🦙';
    case 'openai':
      return '🧠';
    case 'anthropic':
      return '🎭';
    case 'safetensors':
      return '🔒';
    case 'bin':
      return '📦';
    default:
      return '⚡';
  }
}

/**
 * Get provider icon as JSX element (for React components)
 */
export function getProviderIconJSX(provider: string): React.ReactNode {
  // This will be implemented in the component file since it needs React imports
  return null;
}

/**
 * Get status color for model status
 */
export function getStatusColor(status: string): string {
  switch (status) {
    case 'local':
      return 'text-green-600 dark:text-green-400';
    case 'available':
      return 'text-blue-600 dark:text-blue-400';
    case 'downloading':
      return 'text-yellow-600 dark:text-yellow-400';
    default:
      return 'text-gray-600 dark:text-gray-400';
  }
}

/**
 * Get status badge variant
 */
export function getStatusBadgeVariant(status: string): 'default' | 'secondary' | 'destructive' | 'outline' {
  switch (status) {
    case 'local':
      return 'default';
    case 'available':
      return 'secondary';
    case 'downloading':
      return 'outline';
    case 'incompatible':
      return 'outline';
    case 'error':
      return 'destructive';
    default:
      return 'outline';
  }
}

/**
 * Group models by provider
 */
export function groupModelsByProvider(models: Model[]): Record<string, Model[]> {
  return models.reduce((groups, model) => {
    const provider = model.provider || 'unknown';
    if (!groups[provider]) {
      groups[provider] = [];
    }
    groups[provider].push(model);
    return groups;
  }, {} as Record<string, Model[]>);
}

/**
 * Sort models by relevance (local first, then by size)
 */
export function sortModelsByRelevance(models: Model[]): Model[] {
  return [...models].sort((a, b) => {
    // Local models first
    if (a.status === 'local' && b.status !== 'local') return -1;
    if (b.status === 'local' && a.status !== 'local') return 1;
    
    // Then by size (smaller first for better performance)
    return (a.size || 0) - (b.size || 0);
  });
}

/**
 * Filter models by search query
 */
export function filterModels(models: Model[], query: string): Model[] {
  if (!query.trim()) return models;
  
  const searchTerm = query.toLowerCase();
  return models.filter(model => 
    model.name.toLowerCase().includes(searchTerm) ||
    model.description.toLowerCase().includes(searchTerm) ||
    model.provider.toLowerCase().includes(searchTerm) ||
    model.capabilities.some(cap => cap.toLowerCase().includes(searchTerm))
  );
}

/**
 * Get model display name (truncated if too long)
 */
export function getModelDisplayName(model: Model, maxLength: number = 30): string {
  if (model.name.length <= maxLength) return model.name;
  return model.name.substring(0, maxLength - 3) + '...';
}

/**
 * Check if model has specific capability
 */
export function hasCapability(model: Model, capability: string): boolean {
  if (!model.capabilities || model.capabilities.length === 0) {
    // If no capabilities are set, infer from model name and provider
    const name = model.name?.toLowerCase() || '';
    const provider = model.provider?.toLowerCase() || '';
    
    switch (capability) {
      case 'chat':
        return name.includes('chat') || name.includes('instruct') || name.includes('dialog') || 
               provider.includes('llama') || name.endsWith('.gguf');
      case 'text-generation':
        return provider.includes('llama') || provider === 'transformers' || name.endsWith('.gguf') ||
               name.includes('gpt') || name.includes('llama') || name.includes('phi');
      case 'code':
        return name.includes('code') || name.includes('codellama');
      case 'analysis':
      case 'classification':
        return name.includes('bert') || provider === 'transformers';
      default:
        return true; // Be permissive for unknown capabilities
    }
  }
  return model.capabilities.includes(capability);
}

/**
 * Get model performance tier based on size and capabilities
 */
export function getModelTier(model: Model): 'small' | 'medium' | 'large' | 'xl' {
  const size = model.size || 0;
  
  if (size < 1e9) return 'small';      // < 1GB
  if (size < 5e9) return 'medium';     // < 5GB
  if (size < 20e9) return 'large';     // < 20GB
  return 'xl';                         // >= 20GB
}

/**
 * Get recommended models for different use cases
 */
export function getRecommendedModels(models: Model[], useCase: 'chat' | 'code' | 'analysis'): Model[] {
  const filtered = models.filter(model => {
    switch (useCase) {
      case 'chat':
        return hasCapability(model, 'chat') || hasCapability(model, 'text-generation') || 
               model.name.toLowerCase().includes('chat') || model.name.toLowerCase().includes('instruct') ||
               model.name.endsWith('.gguf') || model.provider?.includes('llama');
      case 'code':
        return hasCapability(model, 'code') || model.name.toLowerCase().includes('code');
      case 'analysis':
        return hasCapability(model, 'analysis') || hasCapability(model, 'classification') ||
               model.name.toLowerCase().includes('bert');
      default:
        return true;
    }
  });
  
  return sortModelsByRelevance(filtered);
}