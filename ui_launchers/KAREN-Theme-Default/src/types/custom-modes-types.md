# Custom Modes Configuration Types

## Overview
This document outlines the TypeScript interfaces needed to properly type the custom_modes.yaml file used by the Kilo Code extension.

## Type Definitions

### Base Interfaces

```typescript
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
  groups: string[];
  /** Detailed instructions for the mode's behavior */
  customInstructions: string;
}

/**
 * Custom Modes Configuration
 * Root interface for the custom_modes.yaml file
 */
export interface CustomModesConfig {
  /** Array of custom mode definitions */
  customModes: CustomMode[];
}
```

### Group Types

The `groups` property in the CustomMode interface should be restricted to specific permission groups:

```typescript
export type PermissionGroup = 
  | 'read'
  | 'edit'
  | 'browser'
  | 'command'
  | 'mcp';
```

## Implementation Steps

1. **Create the TypeScript file**
   Create a new file `src/types/custom-modes.ts` with the interfaces defined above.

2. **Update the types index**
   Add an export to `src/types/index.ts`:
   ```typescript
   export * from './custom-modes';
   ```

3. **Fix the YAML file**
   Ensure the custom_modes.yaml file conforms to the defined types.

4. **Create a validation utility**
   Optionally create a utility to validate the YAML file against the TypeScript types.

## File Structure

The custom_modes.yaml file should follow this structure:

```yaml
customModes:
  - slug: string
    name: string
    roleDefinition: |
      Multi-line string describing the role
    groups:
      - read
      - edit
      - browser
      - command
      - mcp
    customInstructions: |
      Multi-line string with detailed instructions
```

## Validation

To ensure type safety, consider implementing a validation function:

```typescript
import { CustomModesConfig } from './custom-modes';

export function validateCustomModesConfig(config: unknown): CustomModesConfig {
  if (typeof config !== 'object' || config === null) {
    throw new Error('Invalid custom modes configuration: must be an object');
  }

  const configObj = config as Record<string, unknown>;
  
  if (!Array.isArray(configObj.customModes)) {
    throw new Error('Invalid custom modes configuration: customModes must be an array');
  }

  // Additional validation can be added here

  return configObj as CustomModesConfig;
}
```

## Integration

Once the types are defined, they can be used throughout the codebase to ensure type safety when working with custom modes configuration.