# Custom Modes TypeScript Errors Fix Plan

## Problem Statement
The custom_modes.yaml file located at `/home/zeus/.config/Code/User/globalStorage/kilocode.kilo-code/settings/custom_modes.yaml` is causing TypeScript errors due to missing type definitions.

## Solution Approach

### Phase 1: Create TypeScript Type Definitions
1. **Create the type definition file**
   - Create `src/types/custom-modes.ts` with the interfaces defined in the custom-modes-types.md file
   - This will provide type safety for the custom modes configuration

2. **Update the types index**
   - Add an export to `src/types/index.ts` to make the types available throughout the codebase
   - This ensures the types can be imported where needed

### Phase 2: Fix the YAML File
1. **Validate the YAML structure**
   - Ensure the custom_modes.yaml file conforms to the defined types
   - Check for any structural issues that might cause TypeScript errors

2. **Create a type declaration file**
   - Create a `.d.ts` file that declares the shape of the YAML configuration
   - This will help TypeScript understand the structure of the YAML file

### Phase 3: Integration and Testing
1. **Update any imports/references**
   - Ensure any files that use the custom modes configuration import the types correctly
   - This will provide type safety throughout the codebase

2. **Test the fixes**
   - Run the TypeScript compiler to verify the errors are resolved
   - Ensure the application builds without type errors

## Implementation Details

### Step 1: Create Type Definitions
Create `src/types/custom-modes.ts` with the following content:

```typescript
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
    
    if (typeof modeObj.customInstructions !== 'string') {
      throw new Error('Invalid custom mode: customInstructions must be a string');
    }
  }

  return configObj as CustomModesConfig;
}
```

### Step 2: Update Types Index
Add the following line to `src/types/index.ts`:

```typescript
export * from './custom-modes';
```

### Step 3: Create Type Declaration for YAML
Create a type declaration file that maps the YAML structure to TypeScript types. This can be done in a new file `src/types/custom-modes.d.ts`:

```typescript
declare module '*/custom_modes.yaml' {
  import { CustomModesConfig } from './custom-modes';
  const config: CustomModesConfig;
  export default config;
}
```

### Step 4: Validate YAML Structure
Ensure the custom_modes.yaml file conforms to the defined types. The file should have this structure:

```yaml
customModes:
  - slug: code-skeptic
    name: Code Skeptic
    roleDefinition: |
      You are Kilo Code, a SKEPTICAL and CRITICAL code quality inspector who questions EVERYTHING. Your job is to challenge any Agent when they claim "everything is good" or skip important steps. You are the voice of doubt that ensures nothing is overlooked.
    groups:
      - read
      - edit
      - browser
      - command
      - mcp
    customInstructions: |
      You will:
      # ... rest of the instructions
```

## Testing
1. Run `npm run typecheck` to verify TypeScript errors are resolved
2. Build the application to ensure everything compiles correctly
3. Test the functionality that uses the custom modes configuration

## Expected Outcome
After implementing these changes, the TypeScript errors in the custom_modes.yaml file should be resolved, and the codebase will have proper type definitions for the custom modes configuration.