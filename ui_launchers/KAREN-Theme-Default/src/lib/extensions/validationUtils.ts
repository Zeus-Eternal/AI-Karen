// Validation utility functions for extension management

import type { ExtensionSetting, ExtensionPermissions, ResourceLimits } from '../../extensions/types';

/**
 * Validates extension manifest structure
 */
export function validateExtensionManifest(manifest: Record<string, unknown>): { valid: boolean; errors: string[] } {
  const errors: string[] = [];
  
  // Required fields
  const requiredFields = [
    'name', 'version', 'display_name', 'description', 'author', 
    'license', 'category', 'api_version', 'kari_min_version'
  ];
  
  for (const field of requiredFields) {
    if (!manifest[field]) {
      errors.push(`Missing required field: ${field}`);
    }
  }
  
  // Version format validation
  if (manifest.version && !isValidVersion(String(manifest.version))) {
    errors.push('Invalid version format. Use semantic versioning (e.g., 1.0.0)');
  }
  
  if (manifest.api_version && !isValidVersion(String(manifest.api_version))) {
    errors.push('Invalid api_version format. Use semantic versioning (e.g., 1.0.0)');
  }
  
  if (manifest.kari_min_version && !isValidVersion(String(manifest.kari_min_version))) {
    errors.push('Invalid kari_min_version format. Use semantic versioning (e.g., 1.0.0)');
  }
  
  // Array fields validation
  if (manifest.tags && !Array.isArray(manifest.tags)) {
    errors.push('Tags must be an array');
  }
  
  // Capabilities validation
  if (manifest.capabilities) {
    const validCapabilities = [
      'provides_ui', 'provides_api', 'provides_background_tasks', 
      'provides_webhooks', 'provides_mcp_tools'
    ];
    
    for (const cap of Object.keys(manifest.capabilities)) {
      if (!validCapabilities.includes(cap)) {
        errors.push(`Invalid capability: ${cap}`);
      }
      if (typeof manifest.capabilities[cap] !== 'boolean') {
        errors.push(`Capability ${cap} must be a boolean`);
      }
    }
  }
  
  return {
    valid: errors.length === 0,
    errors
  };
}

/**
 * Validates semantic version format
 */
export function isValidVersion(version: string): boolean {
  const semverRegex = /^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9-]+))?(?:\+([a-zA-Z0-9-]+))?$/;
  return semverRegex.test(version);
}

/**
 * Validates extension ID format
 */
export function isValidExtensionId(id: string): boolean {
  // Extension IDs should be kebab-case with optional namespace
  const idRegex = /^([a-z0-9-]+\/)?[a-z0-9-]+$/;
  return idRegex.test(id) && id.length >= 3 && id.length <= 100;
}

/**
 * Validates extension name
 */
export function isValidExtensionName(name: string): boolean {
  return name.length >= 3 && name.length <= 100 && name.trim() === name;
}

/**
 * Validates extension description
 */
export function isValidExtensionDescription(description: string): boolean {
  return description.length >= 10 && description.length <= 500;
}

/**
 * Validates extension permissions
 */
export function validateExtensionPermissions(permissions: ExtensionPermissions): { valid: boolean; errors: string[] } {
  const errors: string[] = [];
  
  // Validate filesystem permissions
  if (permissions.filesystem) {
    for (const path of permissions.filesystem) {
      if (!isValidFilesystemPath(path)) {
        errors.push(`Invalid filesystem path: ${path}`);
      }
    }
  }
  
  // Validate network permissions
  if (permissions.network) {
    for (const endpoint of permissions.network) {
      if (!isValidNetworkEndpoint(endpoint)) {
        errors.push(`Invalid network endpoint: ${endpoint}`);
      }
    }
  }
  
  // Validate system permissions
  if (permissions.system) {
    const validSystemPerms = [
      'process.spawn', 'process.kill', 'system.info', 'system.metrics',
      'env.read', 'env.write', 'registry.read', 'registry.write'
    ];
    
    for (const perm of permissions.system) {
      if (!validSystemPerms.includes(perm)) {
        errors.push(`Invalid system permission: ${perm}`);
      }
    }
  }
  
  // Validate data permissions
  if (permissions.data) {
    const validDataPerms = [
      'user.read', 'user.write', 'settings.read', 'settings.write',
      'memory.read', 'memory.write', 'conversations.read', 'conversations.write'
    ];
    
    for (const perm of permissions.data) {
      if (!validDataPerms.includes(perm)) {
        errors.push(`Invalid data permission: ${perm}`);
      }
    }
  }
  
  return {
    valid: errors.length === 0,
    errors
  };
}

/**
 * Validates resource limits
 */
export function validateResourceLimits(limits: ResourceLimits): { valid: boolean; errors: string[] } {
  const errors: string[] = [];
  
  if (limits.max_memory <= 0 || limits.max_memory > 8192) {
    errors.push('max_memory must be between 1 and 8192 MB');
  }
  
  if (limits.max_cpu <= 0 || limits.max_cpu > 100) {
    errors.push('max_cpu must be between 1 and 100 percent');
  }
  
  if (limits.max_storage <= 0 || limits.max_storage > 10240) {
    errors.push('max_storage must be between 1 and 10240 MB');
  }
  
  if (limits.max_network <= 0 || limits.max_network > 10240) {
    errors.push('max_network must be between 1 and 10240 KB/s');
  }
  
  return {
    valid: errors.length === 0,
    errors
  };
}

/**
 * Validates filesystem path
 */
function isValidFilesystemPath(path: string): boolean {
  // Allow relative paths and specific absolute paths
  const allowedPatterns = [
    /^\.\//, // Relative paths starting with ./
    /^\.\.\//, // Relative paths starting with ../
    /^\/tmp\//, // Temp directory
    /^\/var\/tmp\//, // Var temp directory
    /^~\/Documents\//, // User documents
    /^~\/Downloads\//, // User downloads
  ];
  
  return allowedPatterns.some(pattern => pattern.test(path));
}

/**
 * Validates network endpoint
 */
function isValidNetworkEndpoint(endpoint: string): boolean {
  try {
    // Allow specific domains and localhost
    const url = new URL(endpoint);
    const allowedHosts = [
      'localhost',
      '127.0.0.1',
      'api.openai.com',
      'api.anthropic.com',
      'api.cohere.ai',
      'api.huggingface.co',
      'llama.cpp',
    ];
    
    return allowedHosts.some(host => 
      url.hostname === host || 
      url.hostname.endsWith(`.${host}`)
    );
  } catch {
    return false;
  }
}

/**
 * Validates extension setting value
 */
export function validateSettingValue(setting: ExtensionSetting, value: unknown): { valid: boolean; error?: string } {
  const validation = setting.validation;
  
  if (!validation) {
    return { valid: true };
  }
  
  // Required validation
  if (validation.required && (value === undefined || value === null || value === '')) {
    return { valid: false, error: `${setting.label} is required` };
  }
  
  // Skip further validation if value is empty and not required
  if (value === undefined || value === null || value === '') {
    return { valid: true };
  }
  
  // Type-specific validation
  switch (setting.type) {
    case 'number': {
      const numValue = Number(value);
      if (isNaN(numValue)) {
        return { valid: false, error: `${setting.label} must be a number` };
      }
      if (validation.min !== undefined && numValue < validation.min) {
        return { valid: false, error: `${setting.label} must be at least ${validation.min}` };
      }
      if (validation.max !== undefined && numValue > validation.max) {
        return { valid: false, error: `${setting.label} must be at most ${validation.max}` };
      }
      break;
    }
      
    case 'string': {
      if (typeof value !== 'string') {
        return { valid: false, error: `${setting.label} must be a string` };
      }
      if (validation.pattern) {
        const regex = new RegExp(validation.pattern);
        if (!regex.test(value)) {
          return { valid: false, error: `${setting.label} format is invalid` };
        }
      }
      break;
    }
      
    case 'boolean':
      if (typeof value !== 'boolean') {
        return { valid: false, error: `${setting.label} must be a boolean` };
      }
      break;
      
    case 'select': {
      if (validation.options) {
        const validValues = validation.options.map(opt => opt.value);
        if (!validValues.includes(value)) {
          return { valid: false, error: `${setting.label} must be one of: ${validValues.join(', ')}` };
        }
      }
      break;
    }
      
    case 'multiselect': {
      if (!Array.isArray(value)) {
        return { valid: false, error: `${setting.label} must be an array` };
      }
      if (validation.options) {
        const validValues = validation.options.map(opt => opt.value);
        const invalidValues = value.filter(v => !validValues.includes(v));
        if (invalidValues.length > 0) {
          return { valid: false, error: `${setting.label} contains invalid values: ${invalidValues.join(', ')}` };
        }
      }
      break;
    }
  }
  
  return { valid: true };
}

/**
 * Validates API key format
 */
export function isValidApiKey(apiKey: string, provider?: string): boolean {
  if (!apiKey || apiKey.length < 10) {
    return false;
  }
  
  // Provider-specific validation
  switch (provider) {
    case 'openai':
      return apiKey.startsWith('sk-') && apiKey.length >= 40;
    case 'anthropic':
      return apiKey.startsWith('sk-ant-') && apiKey.length >= 40;
    case 'cohere':
      return apiKey.length >= 32;
    case 'huggingface':
      return apiKey.startsWith('hf_') && apiKey.length >= 30;
    default:
      return apiKey.length >= 10 && apiKey.length <= 200;
  }
}

/**
 * Validates URL format
 */
export function isValidUrl(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

/**
 * Validates email format
 */
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Sanitizes user input to prevent XSS
 */
export function sanitizeInput(input: string): string {
  return input
    .replace(/[<>]/g, '') // Remove angle brackets
    .replace(/javascript:/gi, '') // Remove javascript: protocol
    .replace(/on\w+=/gi, '') // Remove event handlers
    .trim();
}

/**
 * Validates extension configuration object
 */
export function validateExtensionConfig(config: Record<string, unknown>): { valid: boolean; errors: string[] } {
  const errors: string[] = [];
  
  if (typeof config !== 'object' || config === null) {
    errors.push('Configuration must be an object');
    return { valid: false, errors };
  }
  
  // Check for dangerous properties
  const dangerousProps = ['__proto__', 'constructor', 'prototype'];
  for (const prop of dangerousProps) {
    if (prop in config) {
      errors.push(`Dangerous property not allowed: ${prop}`);
    }
  }
  
  // Validate nested objects recursively
  for (const [key, value] of Object.entries(config)) {
    if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      const nestedValidation = validateExtensionConfig(value as Record<string, unknown>);
      if (!nestedValidation.valid) {
        errors.push(...nestedValidation.errors.map(err => `${key}.${err}`));
      }
    }
  }
  
  return {
    valid: errors.length === 0,
    errors
  };
}