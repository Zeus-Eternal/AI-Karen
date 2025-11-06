/**
 * Model Organization and Management Components - Production Grade
 * Comprehensive UI components for model discovery, organization, and management
 */

// ============================================================================
// Component Exports
// ============================================================================

// Intelligent Selection & Recommendations
export { default as IntelligentModelSelector } from './IntelligentModelSelector';
export type {
  ModelOption,
  ContextAnalysis,
  UserPreferences,
  ModelRecommendation,
  IntelligentModelSelectorProps,
} from './IntelligentModelSelector';

export { default as EnhancedModelSelector } from './EnhancedModelSelector';
export type {
  SelectorModel,
  EnhancedModelSelectorProps,
} from './EnhancedModelSelector';

// Cost Management & Tracking
export { default as CostTrackingSystem } from './CostTrackingSystem';
export type {
  CostEntry,
  BudgetConfig,
  CostSummary,
  CostTrackingSystemProps,
} from './CostTrackingSystem';

export { default as ModelUsageAnalytics } from './ModelUsageAnalytics';
export type {
  UsageData,
  ModelUsageAnalyticsProps,
} from './ModelUsageAnalytics';

// Metrics & Performance Monitoring
export { default as ModelMetricsDashboard } from './ModelMetricsDashboard';
export type {
  ModelMetric,
  ModelMetricsDashboardProps,
} from './ModelMetricsDashboard';

export { default as ModelStatusMonitor } from './ModelStatusMonitor';
export type {
  ModelStatus,
  ModelStatusMonitorProps,
} from './ModelStatusMonitor';

export { default as ModelPerformanceComparison } from './ModelPerformanceComparison';
export type {
  PerformanceMetric,
  ModelPerformanceComparisonProps,
} from './ModelPerformanceComparison';

export { default as IntegratedModelDisplay } from './IntegratedModelDisplay';
export type {
  DisplayModel,
  IntegratedModelDisplayProps,
} from './IntegratedModelDisplay';

// Provider Management
export { default as ModelProviderManagementHub } from './ModelProviderManagementHub';
export type {
  Provider,
  ModelProviderManagementHubProps,
} from './ModelProviderManagementHub';

// Model Discovery & Browsing
export { default as ModelBrowser } from './ModelBrowser';
export type {
  Model,
  ModelBrowserProps,
} from './ModelBrowser';

export { default as ModelGrid } from './ModelGrid';
export type {
  GridModel,
  ModelGridProps,
} from './ModelGrid';

export { default as ModelsModelCard } from './ModelCard';
export type {
  CardModel,
  ModelCardProps,
} from './ModelCard';

export { default as ModelFilters } from './ModelFilters';
export type {
  FilterState,
  ModelFiltersProps,
} from './ModelFilters';

// Configuration & Settings
export { default as ModelConfigurationPanel } from './ModelConfigurationPanel';
export type {
  ModelConfig,
  ModelConfigurationPanelProps,
} from './ModelConfigurationPanel';

// Dialogs & Modals
export { default as ModelDetailModal } from './ModelDetailModal';
export type {
  DetailModel,
  ModelDetailModalProps,
} from './ModelDetailModal';

export { default as ModelDownloadDialog } from './ModelDownloadDialog';
export type {
  DownloadState,
  ModelDownloadDialogProps,
} from './ModelDownloadDialog';

export { default as LicenseDialog } from './LicenseDialog';
export type {
  License,
  LicenseDialogProps,
} from './LicenseDialog';

// Comparison & Analysis
export { default as ModelComparisonInterface } from './ModelComparisonInterface';
export type {
  ComparisonModel,
  ModelComparisonInterfaceProps,
} from './ModelComparisonInterface';

// License & Compliance
export { default as LicenseCompliancePanel } from './LicenseCompliancePanel';
export type {
  LicenseInfo,
  LicenseCompliancePanelProps,
} from './LicenseCompliancePanel';

export { default as ModelCompatibilityBadge } from './ModelCompatibilityBadge';
export type {
  CompatibilityStatus,
  ModelCompatibilityBadgeProps,
} from './ModelCompatibilityBadge';

// Migration & Operations
export { default as ModelMigrationWizard } from './ModelMigrationWizard';
export type {
  MigrationStep,
  ModelMigrationWizardProps,
} from './ModelMigrationWizard';

export { default as OperationProgress } from './OperationProgress';
export type {
  Operation,
  OperationProgressProps,
} from './OperationProgress';

// Management Pages
export { default as ModelManagementPage } from './ModelManagementPage';
export type {
  ModelManagementPageProps,
} from './ModelManagementPage';

// ============================================================================
// Re-exports from other directories (for backward compatibility)
// ============================================================================
export { default as ModelCard } from '../settings/ModelCard';
export { default as ModelDetailsDialog } from '../settings/ModelDetailsDialog';
export { default as ModelSelector } from '../chat/ModelSelector';

// ============================================================================
// Shared Types and Interfaces
// ============================================================================

export interface ModelInfo {
  id: string;
  name: string;
  display_name: string;
  provider: string;
  type: string;
  category: string;
  size: number;
  description: string;
  capabilities: string[];
  modalities: Array<{
    type: string;
    input_supported: boolean;
    output_supported: boolean;
    formats: string[];
  }>;
  status: 'available' | 'downloading' | 'local' | 'error';
  download_progress?: number;
  metadata: {
    parameters?: string;
    quantization?: string;
    memory_requirement?: string;
    context_length?: number;
    license?: string;
    tags?: string[];
    specialization?: string[];
    performance_metrics?: {
      inference_speed?: string;
      memory_efficiency?: string;
      quality_score?: string;
      recommendation_score?: number;
    };
  };
  local_path?: string;
  download_url?: string;
  checksum?: string;
  disk_usage?: number;
  last_used?: number;
  download_date?: number;
  recommendation?: {
    score: number;
    reasoning: string;
    use_cases: string[];
  };
}

export interface ModelDiscoveryResponse {
  models: ModelInfo[];
  total_count: number;
  categories: Record<string, number>;
  providers: Record<string, number>;
  modalities: Record<string, number>;
  specializations: Record<string, number>;
  status_counts: Record<string, number>;
  discovery_status: string;
  last_updated: number;
}

export interface ModelStatusInfo {
  model_id: string;
  model_name: string;
  provider: string;
  status: 'online' | 'offline' | 'loading' | 'error' | 'maintenance';
  availability: number;
  response_time: number;
  memory_usage: number;
  cpu_usage: number;
  gpu_usage?: number;
  active_connections: number;
  requests_per_minute: number;
  error_rate: number;
  last_request: number;
  uptime: number;
  health_score: number;
  issues: Array<{
    severity: 'info' | 'warning' | 'error';
    message: string;
    timestamp: number;
  }>;
  performance_trend: 'up' | 'down' | 'stable';
}

export interface ModelPerformanceMetrics {
  model_id: string;
  model_name: string;
  provider: string;
  metrics: {
    response_time_avg: number;
    response_time_p95: number;
    throughput: number;
    success_rate: number;
    memory_usage: number;
    cpu_usage: number;
    gpu_usage?: number;
    quality_score: number;
    user_satisfaction: number;
    total_requests: number;
    error_rate: number;
    uptime: number;
  };
  recommendations: {
    score: number;
    reasoning: string;
    use_cases: string[];
  };
}

export interface OptimizationSettings {
  // Response Optimization
  enable_content_optimization: boolean;
  enable_progressive_streaming: boolean;
  enable_smart_caching: boolean;
  enable_cuda_acceleration: boolean;
  // Performance Settings
  max_cpu_usage_percent: number;
  max_memory_usage_gb: number;
  response_timeout_seconds: number;
  cache_ttl_minutes: number;
  // Quality Settings
  content_relevance_threshold: number;
  response_quality_threshold: number;
  enable_redundancy_elimination: boolean;
  enable_format_optimization: boolean;
  // Routing Settings
  routing_strategy: 'performance' | 'quality' | 'balanced' | 'custom';
  enable_fallback_routing: boolean;
  fallback_timeout_ms: number;
  // Advanced Settings
  enable_reasoning_preservation: boolean;
  enable_performance_monitoring: boolean;
  enable_ab_testing: boolean;
  log_level: '' | 'warning' | 'error';
}

// ============================================================================
// Utility Functions
// ============================================================================

export const formatFileSize = (bytes: number): string => {
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  if (bytes === 0) return '0 B';
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
};

export const getStatusBadgeVariant = (status: string) => {
  switch (status) {
    case 'local':
      return 'default';
    case 'downloading':
      return 'secondary';
    case 'available':
      return 'outline';
    case 'error':
      return 'destructive';
    default:
      return 'outline';
  }
};

export const getProviderIcon = (provider: string) => {
  switch (provider.toLowerCase()) {
    case 'llama-cpp':
    case 'local':
      return 'HardDrive';
    case 'transformers':
    case 'huggingface':
      return 'Brain';
    case 'openai':
      return 'Zap';
    default:
      return 'Cpu';
  }
};

export const getModalityIcon = (modality: string) => {
  switch (modality.toLowerCase()) {
    case 'text':
      return 'FileText';
    case 'image':
      return 'Image';
    case 'audio':
      return 'Mic';
    case 'video':
      return 'Video';
    default:
      return 'Eye';
  }
};

export const getCapabilityIcon = (capability: string) => {
  const cap = capability.toLowerCase();
  if (cap.includes('chat') || cap.includes('conversation')) {
    return 'MessageSquare';
  } else if (cap.includes('code') || cap.includes('programming')) {
    return 'Code';
  } else if (cap.includes('reasoning') || cap.includes('analysis')) {
    return 'Lightbulb';
  } else {
    return 'Brain';
  }
};
