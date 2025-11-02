// Extension utility functions

import type { ExtensionBase, ExtensionPlugin, ExtensionProvider, ExtensionModel, SystemExtension, HealthStatus, ResourceUsage, ExtensionSetting, ExtensionControl } from '../../extensions/types';
import {  HEALTH_STATUS, LIFECYCLE_STATUS, EXTENSION_ICONS, DEFAULT_RESOURCE_LIMITS } from './constants';

/**
 * Formats extension version for display
 */
export function formatVersion(version: string): string {
  // Handle semantic versioning
  const semverRegex = /^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9-]+))?(?:\+([a-zA-Z0-9-]+))?$/;
  const match = version.match(semverRegex);
  
  if (match) {
    const [, major, minor, patch, prerelease] = match;
    let formatted = `${major}.${minor}.${patch}`;
    if (prerelease) {
      formatted += `-${prerelease}`;
    }
    return formatted;
  }
  
  return version;
}

/**
 * Gets the appropriate icon for an extension type
 */
export function getExtensionIcon(extension: ExtensionBase): string {
  if ('type' in extension) {
    switch (extension.type) {
      case 'plugin':
        return EXTENSION_ICONS.plugin;
      case 'provider':
        const provider = extension as ExtensionProvider;
        return EXTENSION_ICONS[provider.providerType] || EXTENSION_ICONS.plugin;
      case 'model':
        return EXTENSION_ICONS.plugin;
      case 'system_extension':
        const systemExt = extension as SystemExtension;
        return EXTENSION_ICONS[systemExt.extensionType] || EXTENSION_ICONS.extension;
    }
  }
  
  return EXTENSION_ICONS.extension;
}

/**
 * Calculates health score from 0-100
 */
export function calculateHealthScore(health: HealthStatus, resources: ResourceUsage): number {
  let score = 100;
  
  // Health status impact
  switch (health.status) {
    case HEALTH_STATUS.HEALTHY:
      score -= 0;
      break;
    case HEALTH_STATUS.WARNING:
      score -= 20;
      break;
    case HEALTH_STATUS.ERROR:
      score -= 50;
      break;
    case HEALTH_STATUS.UNKNOWN:
      score -= 10;
      break;
  }
  
  // Resource usage impact
  if (resources.cpu > 80) score -= 15;
  else if (resources.cpu > 60) score -= 10;
  else if (resources.cpu > 40) score -= 5;
  
  if (resources.memory > DEFAULT_RESOURCE_LIMITS.max_memory * 0.8) score -= 15;
  else if (resources.memory > DEFAULT_RESOURCE_LIMITS.max_memory * 0.6) score -= 10;
  else if (resources.memory > DEFAULT_RESOURCE_LIMITS.max_memory * 0.4) score -= 5;
  
  return Math.max(0, Math.min(100, score));
}

/**
 * Formats resource usage for display
 */
export function formatResourceUsage(resources: ResourceUsage): {
  cpu: string;
  memory: string;
  network: string;
  storage: string;
} {
  return {
    cpu: `${resources.cpu.toFixed(1)}%`,
    memory: formatBytes(resources.memory * 1024 * 1024),
    network: `${formatBytes(resources.network * 1024)}/s`,
    storage: formatBytes(resources.storage * 1024 * 1024),
  };
}

/**
 * Formats bytes to human readable format
 */
export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

/**
 * Formats uptime duration
 */
export function formatUptime(uptimeSeconds: number): string {
  const days = Math.floor(uptimeSeconds / 86400);
  const hours = Math.floor((uptimeSeconds % 86400) / 3600);
  const minutes = Math.floor((uptimeSeconds % 3600) / 60);
  
  if (days > 0) {
    return `${days}d ${hours}h ${minutes}m`;
  } else if (hours > 0) {
    return `${hours}h ${minutes}m`;
  } else {
    return `${minutes}m`;
  }
}

/**
 * Checks if an extension is compatible with current system
 */
export function isExtensionCompatible(extension: ExtensionBase): boolean {
  // This would check against system requirements, API versions, etc.
  // For now, return true as a placeholder
  return true;
}

/**
 * Gets extension status color class
 */
export function getStatusColorClass(status: string): string {
  const colorMap: Record<string, string> = {
    [LIFECYCLE_STATUS.ENABLED]: 'text-green-600 bg-green-50',
    [LIFECYCLE_STATUS.DISABLED]: 'text-gray-600 bg-gray-50',
    [LIFECYCLE_STATUS.UPDATING]: 'text-blue-600 bg-blue-50',
    [LIFECYCLE_STATUS.ERROR]: 'text-red-600 bg-red-50',
    [LIFECYCLE_STATUS.INSTALLED]: 'text-yellow-600 bg-yellow-50',
  };
  
  return colorMap[status] || 'text-gray-600 bg-gray-50';
}

/**
 * Validates extension settings
 */
export function validateExtensionSettings(
  settings: ExtensionSetting[],
  values: Record<string, any>
): { valid: boolean; errors: Record<string, string> } {
  const errors: Record<string, string> = {};
  
  for (const setting of settings) {
    const value = values[setting.key];
    const validation = setting.validation;
    
    if (!validation) continue;
    
    // Required validation
    if (validation.required && (value === undefined || value === null || value === '')) {
      errors[setting.key] = `${setting.label} is required`;
      continue;
    }
    
    // Skip further validation if value is empty and not required
    if (value === undefined || value === null || value === '') {
      continue;
    }
    
    // Type-specific validation
    switch (setting.type) {
      case 'number':
        const numValue = Number(value);
        if (isNaN(numValue)) {
          errors[setting.key] = `${setting.label} must be a number`;
        } else {
          if (validation.min !== undefined && numValue < validation.min) {
            errors[setting.key] = `${setting.label} must be at least ${validation.min}`;
          }
          if (validation.max !== undefined && numValue > validation.max) {
            errors[setting.key] = `${setting.label} must be at most ${validation.max}`;
          }
        }
        break;
        
      case 'string':
        if (validation.pattern) {
          const regex = new RegExp(validation.pattern);
          if (!regex.test(value)) {
            errors[setting.key] = `${setting.label} format is invalid`;
          }
        }
        break;
        
      case 'select':
        if (validation.options) {
          const validValues = validation.options.map(opt => opt.value);
          if (!validValues.includes(value)) {
            errors[setting.key] = `${setting.label} must be one of: ${validValues.join(', ')}`;
          }
        }
        break;
        
      case 'multiselect':
        if (validation.options && Array.isArray(value)) {
          const validValues = validation.options.map(opt => opt.value);
          const invalidValues = value.filter(v => !validValues.includes(v));
          if (invalidValues.length > 0) {
            errors[setting.key] = `${setting.label} contains invalid values: ${invalidValues.join(', ')}`;
          }
        }
        break;
    }
  }
  
  return {
    valid: Object.keys(errors).length === 0,
    errors,
  };
}

/**
 * Groups extension settings by category
 */
export function groupExtensionSettings(settings: ExtensionSetting[]): Record<string, ExtensionSetting[]> {
  const groups: Record<string, ExtensionSetting[]> = {};
  
  for (const setting of settings) {
    const group = setting.group || 'General';
    if (!groups[group]) {
      groups[group] = [];
    }
    groups[group].push(setting);
  }
  
  return groups;
}

/**
 * Sorts extensions by various criteria
 */
export function sortExtensions<T extends ExtensionBase>(
  extensions: T[],
  sortBy: 'name' | 'version' | 'author' | 'updated' | 'enabled',
  order: 'asc' | 'desc' = 'asc'
): T[] {
  const sorted = [...extensions].sort((a, b) => {
    let comparison = 0;
    
    switch (sortBy) {
      case 'name':
        comparison = a.name.localeCompare(b.name);
        break;
      case 'version':
        comparison = a.version.localeCompare(b.version);
        break;
      case 'author':
        comparison = a.author.localeCompare(b.author);
        break;
      case 'updated':
        comparison = new Date(a.updatedAt).getTime() - new Date(b.updatedAt).getTime();
        break;
      case 'enabled':
        comparison = (a.enabled ? 1 : 0) - (b.enabled ? 1 : 0);
        break;
    }
    
    return order === 'desc' ? -comparison : comparison;

  return sorted;
}

/**
 * Filters extensions by search query
 */
export function filterExtensions<T extends ExtensionBase>(
  extensions: T[],
  query: string
): T[] {
  if (!query.trim()) return extensions;
  
  const searchTerm = query.toLowerCase().trim();
  
  return extensions.filter(extension => 
    extension.name.toLowerCase().includes(searchTerm) ||
    extension.description.toLowerCase().includes(searchTerm) ||
    extension.author.toLowerCase().includes(searchTerm) ||
    extension.tags?.some(tag => tag.toLowerCase().includes(searchTerm))
  );
}

/**
 * Checks if extension has pending updates
 */
export function hasUpdates(extension: ExtensionBase): boolean {
  if ('lifecycle' in extension) {
    const plugin = extension as ExtensionPlugin;
    return plugin.lifecycle.updateAvailable || false;
  }
  return false;
}

/**
 * Gets extension display name with fallback
 */
export function getExtensionDisplayName(extension: ExtensionBase): string {
  return extension.name || extension.id;
}

/**
 * Calculates extension trust score based on various factors
 */
export function calculateTrustScore(extension: ExtensionBase): number {
  let score = 50; // Base score
  
  // Author reputation (placeholder logic)
  if (extension.author === 'AI Karen Team') {
    score += 30;
  } else if (extension.author.includes('verified')) {
    score += 20;
  }
  
  // Version stability
  if (extension.version.includes('beta') || extension.version.includes('alpha')) {
    score -= 15;
  }
  
  // Dependencies (fewer is better)
  if (extension.dependencies) {
    score -= Math.min(extension.dependencies.length * 2, 20);
  }
  
  // Marketplace data for plugins
  if ('marketplace' in extension) {
    const plugin = extension as ExtensionPlugin;
    if (plugin.marketplace) {
      score += Math.min(plugin.marketplace.rating * 10, 30);
      if (plugin.marketplace.verified) {
        score += 20;
      }
    }
  }
  
  return Math.max(0, Math.min(100, score));
}