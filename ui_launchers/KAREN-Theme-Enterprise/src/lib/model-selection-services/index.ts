/**
 * Model Selection Services - Modular exports
 */

// Export all types
export * from './types';

// Export individual services
export { ModelHealthMonitor } from './health-monitor';
export { ResourceMonitor } from './resource-monitor';
export { ModelScanner } from './model-scanner';
export { BaseModelService } from './base-service';
export { PreferencesService, getPreferencesService, resetPreferencesService } from './preferences-service';
export type { IPreferencesService } from './preferences-service';
export { ModelRegistryService, ModelRegistry, getModelRegistry, resetModelRegistry } from './model-registry';
export type { IModelRegistry } from './model-registry';

// Export the main modular service
export { ModelSelectionService } from './main-service';

// Export singleton instance
import { ModelSelectionService as MainModelSelectionService } from './main-service';
export const modelSelectionService = MainModelSelectionService.getInstance();
