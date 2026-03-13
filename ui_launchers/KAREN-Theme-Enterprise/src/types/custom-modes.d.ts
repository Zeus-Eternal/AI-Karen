/**
 * Permission groups that can be assigned to custom modes
 */
type PermissionGroup =
  | 'read'
  | 'edit'
  | 'browser'
  | 'command'
  | 'mcp';

/**
 * Custom Mode Configuration
 * Defines the structure for a custom AI assistant mode
 */
interface CustomMode {
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
interface CustomModesConfig {
  /** Array of custom mode definitions */
  customModes: CustomMode[];
}

declare module '*.yaml' {
  const content: CustomModesConfig;
  export default content;
}

declare module '*.yml' {
  const content: CustomModesConfig;
  export default content;
}