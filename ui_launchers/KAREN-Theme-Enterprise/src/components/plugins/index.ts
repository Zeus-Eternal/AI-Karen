/**
 * Plugin Components Index - Production Grade
 *
 * Centralized export hub for all plugin management, marketplace,
 * configuration, security, and monitoring components.
 */

// ============================================================================
// Core Plugin Management Components
// ============================================================================

// Plugin Manager
export { default as PluginManager } from "./PluginManager";
export type { PluginCardProps } from "./PluginManager";

// Plugin Marketplace
export { default as PluginMarketplace } from "./PluginMarketplace";
export type { PluginMarketplaceProps } from "./PluginMarketplace";

// Enhanced Plugin Marketplace
export { EnhancedPluginMarketplace } from "./EnhancedPluginMarketplace";
export type {
  PluginReview,
  MarketplaceFilters,
  EnhancedPluginMarketplaceProps,
} from "./EnhancedPluginMarketplace";

// Plugin Metrics
export { default as PluginMetrics } from "./PluginMetrics";
export type { PluginMetricsProps } from "./PluginMetrics";

// Plugin Overview Page
export { default as PluginOverviewPage } from "./PluginOverviewPage";

// ============================================================================
// Plugin Installation & Configuration
// ============================================================================

// Plugin Installation Wizard
export { default as PluginInstallationWizard } from "./PluginInstallationWizard";
export type {
  InstallationStep,
  PermissionLevel,
  PermissionCategory,
  Permission as InstallationPermission,
  PluginDependency,
  ConfigFieldType,
  PluginConfigField,
  PluginManifest,
  PluginMarketplaceEntry,
  PluginConfig,
  PluginInstallationRequest,
  PluginInstallationWizardProps,
  InstallationState,
} from "./PluginInstallationWizard";

// Plugin Configuration Manager
export { default as PluginConfigurationManager } from "./PluginConfigurationManager";
export type {
  ValidationError as ConfigValidationError,
  ConfigurationSection,
  PluginConfigurationManagerProps,
} from "./PluginConfigurationManager";

// Dynamic Plugin Config Form
export { DynamicPluginConfigForm } from "./DynamicPluginConfigForm";
export type {
  ValidationError as FormValidationError,
  FieldGroup,
  DynamicPluginConfigFormProps,
} from "./DynamicPluginConfigForm";

// Plugin Configuration Security Integration
export { PluginConfigurationSecurityIntegration } from "./PluginConfigurationSecurityIntegration";
export type {
  ValidationError as SecurityValidationError,
  InfoItemProps,
} from "./PluginConfigurationSecurityIntegration";

// ============================================================================
// Plugin Security & Monitoring
// ============================================================================

// Plugin Security Manager
export { default as PluginSecurityManager } from "./PluginSecurityManager";
export type {
  IsolationLevel,
  PolicyToggleProps,
  NumberFieldProps,
} from "./PluginSecurityManager";

// Plugin Health Monitor
export { PluginHealthMonitor } from "./PluginHealthMonitor";
export type {
  HealthStatus,
  EventType,
  Severity as HealthSeverity,
  HealthCheck,
  HealthEvent,
  RecoveryType,
  RecoveryAction,
  PluginHealthMonitorProps,
} from "./PluginHealthMonitor";

// Plugin Audit Logger
export { default as PluginAuditLogger } from "./PluginAuditLogger";
export type {
  AuditSummary,
  ComplianceReport,
  PluginAuditLoggerProps,
} from "./PluginAuditLogger";

// Plugin Log Analyzer
export { default as PluginLogAnalyzer } from "./PluginLogAnalyzer";
export type {
  LogLevel,
  Source as LogSource,
  LogFilter,
  LogAnalytics,
} from "./PluginLogAnalyzer";

// Plugin Detail View
export { PluginDetailView } from "./PluginDetailView";
export type {
  Permission as DetailPermission,
  LogEntryT,
  PluginDetailViewProps,
} from "./PluginDetailView";

// ============================================================================
// Plugin-Specific Pages
// ============================================================================

// Book Details Plugin
export { default as BookDetailsPluginPage } from "./BookDetailsPluginPage";

// Database Connector Plugin
export { default as DatabaseConnectorPluginPage } from "./DatabaseConnectorPluginPage";

// DateTime Plugin
export { default as DateTimePluginPage } from "./DateTimePluginPage";
export { default as DateTimePluginPageMinimal } from "./DateTimePluginPage.minimal";

// Facebook Plugin
export { default as FacebookPluginPage } from "./FacebookPluginPage";

// Gmail Plugin
export { default as GmailPluginPage } from "./GmailPluginPage";

// Weather Plugin
export { default as WeatherPluginPage } from "./WeatherPluginPage";
