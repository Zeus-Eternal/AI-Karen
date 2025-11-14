/**
 * Settings Components Index - Production Grade
 *
 * Centralized export hub for all settings and configuration components.
 */

// ============================================================================
// Component Exports
// ============================================================================

// AdvancedModelConfig
export { default as AdvancedModelConfig } from './AdvancedModelConfig';
export type {
  ModelConfig,
  BenchmarkResult,
  ModelStats,
  AdvancedModelConfigProps,
} from './AdvancedModelConfig';

// AdvancedModelManagement
export { default as AdvancedModelManagement } from './AdvancedModelManagement';
export type {
  StorageInfo as AdvancedModelStorageInfo,
  SystemHealth,
} from './AdvancedModelManagement';

// AdvancedTrainingConfig
export { default as AdvancedTrainingConfig } from './AdvancedTrainingConfig';
export type {
  HyperparameterRange,
  TrainingLogicConfig,
  OptimizationConfig,
  MonitoringConfig,
  AlertThreshold,
  HyperparameterSweepConfig,
  OptimizationConstraint,
  ABTestConfig,
  FederatedLearningConfig,
  TransferLearningConfig,
  ModelCompressionConfig,
  XAIConfig,
  SecurityConfig,
  AdvancedTrainingConfig as AdvancedTrainingConfigSchema,
  TrainingMetrics,
  AIAssistanceResponse,
  RealTimeMetrics,
} from './AdvancedTrainingConfig';

// ApiKeyManager
export { default as ApiKeyManager } from './ApiKeyManager';

// BasicTrainingMode
export { default as BasicTrainingMode } from './BasicTrainingMode';
export type {
  BasicTrainingPreset,
  TrainingProgress,
  TrainingResult,
  SystemBackup,
} from './BasicTrainingMode';

// BehaviorSettings
export { default as BehaviorSettings } from './BehaviorSettings';

// CopilotKitSettings
export { default as CopilotKitSettings } from './CopilotKitSettings';
export type {
  CopilotKitConfig,
} from './CopilotKitSettings';

// DownloadManager
export { default as DownloadManager } from './DownloadManager';
export type {
  DownloadManagerProps,
} from './DownloadManager';

// EnhancedModelBrowser
export { default as EnhancedModelBrowser } from './EnhancedModelBrowser';
export type {
  TrainableModel,
  CompatibilityReport,
  EnhancedDownloadJob,
  TrainingFilters,
  TabKey,
  CategoryItem,
} from './EnhancedModelBrowser';

// ErrorMessageDisplay
export { default as ErrorMessageDisplay } from './ErrorMessageDisplay';
export type {
  ErrorContext,
  ErrorSolution,
  ErrorInfo,
  ErrorMessageDisplayProps,
} from './ErrorMessageDisplay';

// JobCenter
export { default as JobCenter } from './JobCenter';
export type {
  Job as JobCenterJob,
  JobCenterProps,
} from './JobCenter';

// JobManager
export { default as JobManager } from './JobManager';
export type {
  Job as JobManagerJob,
  JobStats,
  StorageInfo as JobManagerStorageInfo,
  JobManagerProps,
} from './JobManager';

// LLMSettings
export { default as LLMSettings } from './LLMSettings';
export type {
  LLMProvider,
  ModelInfo,
  LLMProfile,
  ProviderStats,
} from './types';

// ModelBrowser
export { default as ModelBrowser } from './ModelBrowser';
export type {
  ModelInfo as ModelBrowserModelInfo,
  LLMProvider as ModelBrowserProvider,
} from './types';
export type {
  ModelBrowserProps,
} from './ModelBrowser';

// ModelCard
export { default as ModelCard } from './ModelCard';

// ModelConfiguration
export { default as ModelConfiguration } from './ModelConfiguration';
export type {
  SystemModelConfig as ModelConfigurationSystemModelConfig,
  SystemModelSummary,
  ModelConfigurationProps,
} from './ModelConfiguration';

// ModelDetailsDialog
export { default as ModelDetailsDialog } from './ModelDetailsDialog';

// ModelDownloadProgress
export { default as ModelDownloadProgress } from './ModelDownloadProgress';
export type {
  DownloadTask,
  ModelDownloadProgressProps,
} from './ModelDownloadProgress';

// ModelLibrary
export { default as ModelLibrary } from './ModelLibrary';
export type {
  ModelInfo as ModelLibraryModelInfo,
  ModelMetadata,
  ModelLibraryStats,
  SortOption,
  SortOrder,
} from './ModelLibrary';

// ModelProviderIntegration
export { default as ModelProviderIntegration } from './ModelProviderIntegration';
export type {
  ProviderModelSuggestions,
  ModelProviderIntegrationProps,
} from './ModelProviderIntegration';

// ModelUploadInterface
export { default as ModelUploadInterface } from './ModelUploadInterface';
export type {
  UploadJob,
  ConversionJob as ModelUploadConversionJob,
  ModelUploadInterfaceProps,
} from './ModelUploadInterface';

// ModelUploadManager
export { default as ModelUploadManager } from './ModelUploadManager';
export type {
  UploadFile,
  ConversionJob as UploadManagerConversionJob,
  ModelUploadManagerProps,
} from './ModelUploadManager';

// NotificationSettings
export { default as NotificationSettings } from './NotificationSettings';

// PersonaSettings
export { default as PersonaSettings } from './PersonaSettings';

// PersonalFactsSettings
export { default as PersonalFactsSettings } from './PersonalFactsSettings';

// PrivacySettings
export { default as PrivacySettings } from './PrivacySettings';

// ProfileManager
export { default as ProfileManager } from './ProfileManager';
export type {
  LLMProvider as ProfileManagerLLMProvider,
  LLMProfile as ProfileManagerLLMProfile,
} from './types';
export type {
  ProfileManagerProps,
} from './ProfileManager';

// ProviderConfigurationGuide
export { default as ProviderConfigurationGuide } from './ProviderConfigurationGuide';
export type {
  ConfigurationStep,
  ProviderGuide,
  ProviderConfigurationGuideProps,
} from './ProviderConfigurationGuide';

// ProviderDiagnosticsPage
export { default as ProviderDiagnosticsPage } from './ProviderDiagnosticsPage';
export type {
  DiagnosticInfo,
  RepairAction,
  ProviderDiagnosticsPageProps,
} from './ProviderDiagnosticsPage';

// ProviderManagement
export { default as ProviderManagement } from './ProviderManagement';
export type {
  ModelRecommendationsProps,
  ApiKeyValidationResult,
  ProviderManagementProps,
} from './ProviderManagement';
export type {
  LLMProvider as ProviderManagementLLMProvider,
  ProviderStats as ProviderManagementStats,
} from './types';

// ProviderNotificationSystem
export { default as ProviderNotificationSystem } from './ProviderNotificationSystem';
export type {
  NotificationSettings as ProviderNotificationSettings,
  ProviderNotification,
  ProviderNotificationSystemProps,
} from './ProviderNotificationSystem';

// ProviderStatusIndicator
export { default as ProviderStatusIndicator } from './ProviderStatusIndicator';
export type {
  ProviderStatus,
  ProviderStatusIndicatorProps,
} from './ProviderStatusIndicator';

// ProviderTestingInterface
export { default as ProviderTestingInterface } from './ProviderTestingInterface';
export type {
  TestResult,
  ValidationResult,
  ProviderTestingInterfaceProps,
} from './ProviderTestingInterface';

// SearchHighlight
export { default as SearchHighlight } from './SearchHighlight';
export type {
  SearchHighlightProps,
} from './SearchHighlight';

// SettingsDialog
export { default as SettingsDialog } from './SettingsDialog';

// SystemModelConfig
export { default as SystemModelConfig } from './SystemModelConfig';
export type {
  TransformerConfig,
  SystemModelInfo,
  HardwareRecommendations,
  PerformanceMetrics,
  SystemModelConfigProps,
} from './SystemModelConfig';

// TransformerModelConfig
export { default as TransformerModelConfig } from './TransformerModelConfig';
export type {
  TransformerConfig as TransformerModelTransformerConfig,
  HardwareRecommendations as TransformerModelHardwareRecommendations,
  MultiGpuConfig,
  TransformerModelConfigProps,
} from './TransformerModelConfig';

// VoiceSettings
export { default as VoiceSettings } from './VoiceSettings';
