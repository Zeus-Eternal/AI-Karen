/**
 * Custom Modes Configuration Types
 * 
 * This file defines TypeScript interfaces for the custom modes configuration
 * used by the Kilo Code extension to define specialized AI assistant modes.
 */

/**
 * Permission groups that can be assigned to custom modes
 */
export type PermissionGroup =
  | 'read'
  | 'edit'
  | 'browser'
  | 'command'
  | 'mcp';

/**
 * Custom Mode Configuration
 * Defines the structure for a custom AI assistant mode
 */
export interface CustomMode {
  /** Unique identifier for the mode */
  slug: string;
  /** Display name for the mode */
  name: string;
  /** Role definition that describes the AI's personality and purpose */
  roleDefinition: string;
  /** Permission groups that this mode has access to */
  groups: PermissionGroup[];
  /** Detailed instructions for the mode's behavior */
  customInstructions?: string;
  /** Source of the mode configuration */
  source?: string;
}

/**
 * Custom Modes Configuration
 * Root interface for the custom_modes.yaml file
 */
export interface CustomModesConfig {
  /** Array of custom mode definitions */
  customModes: CustomMode[];
}

/**
 * Validates that a given object conforms to the CustomModesConfig interface
 */
export function validateCustomModesConfig(config: unknown): CustomModesConfig {
  if (typeof config !== 'object' || config === null) {
    throw new Error('Invalid custom modes configuration: must be an object');
  }

  const configObj = config as Record<string, unknown>;
  
  if (!Array.isArray(configObj.customModes)) {
    throw new Error('Invalid custom modes configuration: customModes must be an array');
  }

  // Validate each custom mode
  for (const mode of configObj.customModes) {
    if (typeof mode !== 'object' || mode === null) {
      throw new Error('Invalid custom mode: must be an object');
    }

    const modeObj = mode as Record<string, unknown>;
    
    if (typeof modeObj.slug !== 'string') {
      throw new Error('Invalid custom mode: slug must be a string');
    }
    
    if (typeof modeObj.name !== 'string') {
      throw new Error('Invalid custom mode: name must be a string');
    }
    
    if (typeof modeObj.roleDefinition !== 'string') {
      throw new Error('Invalid custom mode: roleDefinition must be a string');
    }
    
    if (!Array.isArray(modeObj.groups)) {
      throw new Error('Invalid custom mode: groups must be an array');
    }
    
    // Validate groups
    for (const group of modeObj.groups) {
      if (typeof group !== 'string') {
        throw new Error('Invalid custom mode: groups must be strings');
      }
      
      if (!['read', 'edit', 'browser', 'command', 'mcp'].includes(group)) {
        throw new Error(`Invalid custom mode: unknown permission group '${group}'`);
      }
    }
    
    if (modeObj.customInstructions !== undefined && typeof modeObj.customInstructions !== 'string') {
      throw new Error('Invalid custom mode: customInstructions must be a string');
    }

    if (modeObj.source !== undefined && typeof modeObj.source !== 'string') {
      throw new Error('Invalid custom mode: source must be a string');
    }
  }

  return config as CustomModesConfig;
}