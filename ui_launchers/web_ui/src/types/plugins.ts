/**
 * Plugin Management Types
 * 
 * Type definitions for the plugin and extension management system.
 * Based on requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 9.1, 9.2
 */

// Plugin Status Types
export type PluginStatus = 'active' | 'inactive' | 'error' | 'installing' | 'updating' | 'uninstalling';

// Plugin Permission Types
export interface Permission {
  id: string;
  name: string;
  description: string;
  category: 'system' | 'data' | 'network' | 'ui' | 'storage';
  level: 'read' | 'write' | 'admin';
  required: boolean;
}

// Plugin Dependency Types
export interface PluginDependency {
  id: string;
  name: string;
  version: string;
  versionConstraint: string;
  optional: boolean;
  installed: boolean;
  compatible: boolean;
}

// Plugin Metrics Types
export interface PluginMetrics {
  performance: {
    averageExecutionTime: number;
    totalExecutions: number;
    errorRate: number;
    lastExecution: Date | null;
  };
  resources: {
    memoryUsage: number;
    cpuUsage: number;
    diskUsage: number;
    networkUsage: number;
  };
  health: {
    status: 'healthy' | 'warning' | 'critical';
    uptime: number;
    lastHealthCheck: Date;
    issues: string[];
  };
}

// Plugin Configuration Types
export interface PluginConfigField {
  key: string;
  type: 'string' | 'number' | 'boolean' | 'select' | 'multiselect' | 'json' | 'password';
  label: string;
  description?: string;
  required: boolean;
  default?: any;
  options?: Array<{ label: string; value: any }>;
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    custom?: (value: any) => string | null;
  };
}

export interface PluginConfig {
  [key: string]: any;
}

// Plugin Manifest Types
export interface PluginManifest {
  id: string;
  name: string;
  version: string;
  description: string;
  author: {
    name: string;
    email?: string;
    url?: string;
  };
  license: string;
  homepage?: string;
  repository?: string;
  keywords: string[];
  category: 'ai' | 'integration' | 'utility' | 'analytics' | 'security' | 'workflow';
  
  // Technical specifications
  runtime: {
    platform: string[];
    nodeVersion?: string;
    pythonVersion?: string;
  };
  
  // Dependencies and requirements
  dependencies: PluginDependency[];
  systemRequirements: {
    minMemory?: number;
    minDisk?: number;
    requiredServices?: string[];
  };
  
  // Permissions and security
  permissions: Permission[];
  sandboxed: boolean;
  securityPolicy: {
    allowNetworkAccess: boolean;
    allowFileSystemAccess: boolean;
    allowSystemCalls: boolean;
    trustedDomains?: string[];
  };
  
  // Configuration schema
  configSchema: PluginConfigField[];
  
  // API and integration points
  apiVersion: string;
  endpoints?: Array<{
    path: string;
    method: string;
    description: string;
  }>;
  hooks?: Array<{
    event: string;
    handler: string;
    priority: number;
  }>;
  
  // UI components
  ui?: {
    hasSettings: boolean;
    hasDashboard: boolean;
    hasWidget: boolean;
    customRoutes?: Array<{
      path: string;
      component: string;
      title: string;
    }>;
  };
}

// Plugin Information Types
export interface PluginInfo {
  id: string;
  name: string;
  version: string;
  status: PluginStatus;
  manifest: PluginManifest;
  config: PluginConfig;
  permissions: Permission[];
  metrics: PluginMetrics;
  
  // Installation metadata
  installedAt: Date;
  updatedAt: Date;
  installedBy: string;
  
  // Runtime information
  enabled: boolean;
  autoStart: boolean;
  restartCount: number;
  lastError?: {
    message: string;
    timestamp: Date;
    stack?: string;
  };
  
  // Dependency status
  dependencyStatus: {
    satisfied: boolean;
    missing: PluginDependency[];
    conflicts: Array<{
      dependency: PluginDependency;
      conflictsWith: string;
      reason: string;
    }>;
  };
}

// Plugin Installation Types
export interface PluginInstallationRequest {
  source: 'marketplace' | 'file' | 'url' | 'git';
  identifier: string; // marketplace ID, file path, URL, or git repo
  version?: string;
  config?: PluginConfig;
  permissions?: string[]; // Permission IDs to grant
  autoStart?: boolean;
}

export interface PluginInstallationProgress {
  stage: 'downloading' | 'validating' | 'resolving' | 'installing' | 'configuring' | 'starting' | 'complete' | 'error';
  progress: number; // 0-100
  message: string;
  details?: string;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
}

// Plugin Marketplace Types
export interface PluginMarketplaceEntry {
  id: string;
  name: string;
  description: string;
  version: string;
  author: {
    name: string;
    verified: boolean;
  };
  category: string;
  tags: string[];
  
  // Marketplace metadata
  downloads: number;
  rating: number;
  reviewCount: number;
  featured: boolean;
  verified: boolean;
  
  // Compatibility
  compatibility: {
    minVersion: string;
    maxVersion?: string;
    platforms: string[];
  };
  
  // Media
  icon?: string;
  screenshots: string[];
  
  // Pricing (for future commercial plugins)
  pricing: {
    type: 'free' | 'paid' | 'freemium';
    price?: number;
    currency?: string;
  };
  
  // Installation info
  installUrl: string;
  manifest: PluginManifest;
}

// Plugin Log Types
export interface PluginLogEntry {
  id: string;
  pluginId: string;
  timestamp: Date;
  level: 'debug' | 'info' | 'warn' | 'error';
  message: string;
  context?: Record<string, any>;
  source: string;
  userId?: string;
}

// Plugin Audit Types
export interface PluginAuditEntry {
  id: string;
  pluginId: string;
  timestamp: Date;
  action: 'install' | 'uninstall' | 'enable' | 'disable' | 'configure' | 'update' | 'permission_grant' | 'permission_revoke';
  userId: string;
  details: Record<string, any>;
  ipAddress?: string;
  userAgent?: string;
}

// Plugin Filter and Search Types
export interface PluginFilter {
  status?: PluginStatus[];
  category?: string[];
  author?: string[];
  hasUpdates?: boolean;
  enabled?: boolean;
  hasErrors?: boolean;
}

export interface PluginSearchOptions {
  query?: string;
  filter?: PluginFilter;
  sortBy?: 'name' | 'status' | 'version' | 'installedAt' | 'lastUsed' | 'performance';
  sortOrder?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}

// Plugin Management API Types
export interface PluginManagementAPI {
  // Plugin CRUD operations
  listPlugins(options?: PluginSearchOptions): Promise<PluginInfo[]>;
  getPlugin(id: string): Promise<PluginInfo>;
  installPlugin(request: PluginInstallationRequest): Promise<string>; // Returns installation ID
  uninstallPlugin(id: string): Promise<void>;
  updatePlugin(id: string, version?: string): Promise<string>; // Returns installation ID
  
  // Plugin control operations
  enablePlugin(id: string): Promise<void>;
  disablePlugin(id: string): Promise<void>;
  restartPlugin(id: string): Promise<void>;
  configurePlugin(id: string, config: PluginConfig): Promise<void>;
  
  // Plugin monitoring
  getPluginMetrics(id: string): Promise<PluginMetrics>;
  getPluginLogs(id: string, options?: { limit?: number; level?: string; since?: Date }): Promise<PluginLogEntry[]>;
  getPluginAuditLog(id: string, options?: { limit?: number; since?: Date }): Promise<PluginAuditEntry[]>;
  
  // Installation tracking
  getInstallationProgress(installationId: string): Promise<PluginInstallationProgress>;
  cancelInstallation(installationId: string): Promise<void>;
  
  // Marketplace operations
  searchMarketplace(query: string, options?: { category?: string; limit?: number }): Promise<PluginMarketplaceEntry[]>;
  getMarketplacePlugin(id: string): Promise<PluginMarketplaceEntry>;
  
  // Dependency management
  checkDependencies(pluginId: string): Promise<PluginDependency[]>;
  resolveDependencies(pluginId: string): Promise<PluginDependency[]>;
  
  // Permission management
  grantPermission(pluginId: string, permissionId: string): Promise<void>;
  revokePermission(pluginId: string, permissionId: string): Promise<void>;
  checkPermission(pluginId: string, permissionId: string): Promise<boolean>;
}

// Plugin Store State Types
export interface PluginStoreState {
  plugins: PluginInfo[];
  selectedPlugin: PluginInfo | null;
  installations: Record<string, PluginInstallationProgress>;
  marketplacePlugins: PluginMarketplaceEntry[];
  
  // UI state
  loading: {
    plugins: boolean;
    installation: boolean;
    marketplace: boolean;
    [key: string]: boolean;
  };
  
  errors: {
    plugins: string | null;
    installation: string | null;
    marketplace: string | null;
    [key: string]: string | null;
  };
  
  // Filters and search
  searchQuery: string;
  filters: PluginFilter;
  sortBy: 'name' | 'status' | 'version' | 'installedAt' | 'lastUsed' | 'performance';
  sortOrder: 'asc' | 'desc';
  
  // View state
  view: 'list' | 'grid' | 'details';
  showInstallationWizard: boolean;
  showMarketplace: boolean;
}

export interface PluginStoreActions {
  // Plugin operations
  loadPlugins: () => Promise<void>;
  selectPlugin: (plugin: PluginInfo | null) => void;
  installPlugin: (request: PluginInstallationRequest) => Promise<string>;
  uninstallPlugin: (id: string) => Promise<void>;
  enablePlugin: (id: string) => Promise<void>;
  disablePlugin: (id: string) => Promise<void>;
  configurePlugin: (id: string, config: PluginConfig) => Promise<void>;
  
  // Marketplace operations
  loadMarketplacePlugins: (query?: string) => Promise<void>;
  
  // UI operations
  setSearchQuery: (query: string) => void;
  setFilters: (filters: Partial<PluginFilter>) => void;
  setSorting: (sortBy: string, sortOrder: 'asc' | 'desc') => void;
  setView: (view: 'list' | 'grid' | 'details') => void;
  setShowInstallationWizard: (show: boolean) => void;
  setShowMarketplace: (show: boolean) => void;
  
  // Error handling
  setError: (key: string, error: string | null) => void;
  clearErrors: () => void;
}

export type PluginStore = PluginStoreState & PluginStoreActions;