/**
 * Common types and interfaces for extension components
 */

export type ExtensionStatus = 'active' | 'inactive' | 'loading' | 'error' | 'disabled';

export type ExtensionHealth = 'green' | 'yellow' | 'red' | 'unknown';

export type ExtensionCategory =
  | 'security'
  | 'performance'
  | 'monitoring'
  | 'data'
  | 'integration'
  | 'ui'
  | 'automation'
  | 'analytics'
  | 'uncategorized';

export interface BaseExtension {
  id: string;
  name: string;
  displayName?: string;
  description: string;
  version: string;
  status: ExtensionStatus;
  enabled: boolean;
  author?: string;
  category?: string;
  tags?: string[];
}

export interface ExtensionWithHealth extends BaseExtension {
  health: ExtensionHealth;
  lastHealthCheck?: Date;
  errorMessage?: string | null;
}

export interface ExtensionManifest {
  name: string;
  display_name?: string;
  description?: string;
  version: string;
  author?: string;
  category?: ExtensionCategory;
  tags?: string[];
  capabilities?: Record<string, boolean>;
  permissions?: string[];
  resources?: {
    cpu?: number;
    memory?: number;
    disk?: number;
  };
  dependencies?: string[];
}

export interface ExtensionCapability {
  id: string;
  name: string;
  enabled: boolean;
  description?: string;
}

export interface ExtensionPermission {
  id: string;
  name: string;
  granted: boolean;
  description?: string;
  required?: boolean;
}

export interface ExtensionResource {
  type: 'cpu' | 'memory' | 'disk' | 'network';
  current: number;
  limit?: number;
  unit: string;
}

export interface ExtensionHealthMetrics {
  responseTime?: number;
  successRate?: number;
  errorCount?: number;
  lastError?: string;
  uptime?: number;
}

export interface ExtensionSummary {
  total: number;
  active: number;
  inactive: number;
  error: number;
  loading: number;
  disabled: number;
}

export interface ExtensionFilter {
  status?: ExtensionStatus[];
  category?: string[];
  health?: ExtensionHealth[];
  enabled?: boolean;
  search?: string;
}

export interface ExtensionSort {
  field: 'name' | 'version' | 'status' | 'category' | 'health';
  direction: 'asc' | 'desc';
}

// Action types for extension management
export type ExtensionAction =
  | 'enable'
  | 'disable'
  | 'configure'
  | 'remove'
  | 'update'
  | 'reload'
  | 'restart';

export interface ExtensionActionResult {
  success: boolean;
  message?: string;
  error?: string;
}
