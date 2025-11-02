/**
 * Model Selection Services - Modular exports
 */

// Export all types
export * from "./types";

// Export individual services
import { export { ModelHealthMonitor } from "./health-monitor";
import { export { ResourceMonitor } from "./resource-monitor";
import { export { ModelScanner } from "./model-scanner";
import { export { BaseModelService } from "./base-service";
import { export { PreferencesService, getPreferencesService, resetPreferencesService } from "./preferences-service";
import { export type { IPreferencesService } from "./preferences-service";
import { export { ModelRegistryService, ModelRegistry, getModelRegistry, resetModelRegistry } from "./model-registry";
import { export type { IModelRegistry } from "./model-registry";

// Export the main modular service
import { export { ModelSelectionService } from "./main-service";

// Export singleton instance
import { ModelSelectionService } from "./main-service";
export const modelSelectionService = ModelSelectionService.getInstance();