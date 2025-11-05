// ui_launchers/KAREN-Theme-Default/src/components/providers/index.ts
/**
 * Provider Management Components
 * Comprehensive provider configuration and fallback management
 */

import { default as ProviderConfigInterface } from './ProviderConfigInterface';
import { default as FallbackConfigInterface } from './FallbackConfigInterface';

// Re-export types if needed
export type {
  ProviderConfigInterfaceProps, // If these types exist in the corresponding file
  FallbackConfigInterfaceProps, // Add specific type exports from the interface files
} from '@/types/providers';

// Export components for use in other parts of the application
export { ProviderConfigInterface, FallbackConfigInterface };
