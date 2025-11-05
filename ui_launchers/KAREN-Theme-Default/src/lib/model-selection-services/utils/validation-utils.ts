/**
 * Validation utilities for model selection services
 */

/**
 * Type guard for checking if a value is a string
 */
export function isString(value: any): value is string {
  return typeof value === 'string';
}

/**
 * Type guard for checking if a value is a number
 */
export function isNumber(value: any): value is number {
  return typeof value === 'number' && !isNaN(value);
}

/**
 * Type guard for checking if a value is a boolean
 */
export function isBoolean(value: any): value is boolean {
  return typeof value === 'boolean';
}

/**
 * Type guard for checking if a value is an object
 */
export function isObject(value: any): value is Record<string, any> {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

/**
 * Type guard for checking if a value is an array
 */
export function isArray(value: any): value is any[] {
  return Array.isArray(value);
}

/**
 * Validate that a string is not empty
 */
export function isNonEmptyString(value: any): value is string {
  return isString(value) && value.trim().length > 0;
}

/**
 * Validate that a number is positive
 */
export function isPositiveNumber(value: any): value is number {
  return isNumber(value) && value > 0;
}

/**
 * Validate that a number is non-negative
 */
export function isNonNegativeNumber(value: any): value is number {
  return isNumber(value) && value >= 0;
}

/**
 * Validate that a value is within a range
 */
export function isInRange(value: any, min: number, max: number): value is number {
  return isNumber(value) && value >= min && value <= max;
}

/**
 * Validate that a string matches a pattern
 */
export function matchesPattern(value: any, pattern: RegExp): value is string {
  return isString(value) && pattern.test(value);
}

/**
 * Validate that an object has required properties
 */
export function hasRequiredProperties<T extends Record<string, any>>(
  value: any,
  requiredProps: (keyof T)[]
): value is T {
  if (!isObject(value)) {
    return false;
  }
  
  return requiredProps.every(prop => prop in value && value[prop as string] !== undefined);
}

/**
 * Validate that an array contains only items of a specific type
 */
export function isArrayOf<T>(
  value: any,
  itemValidator: (item: any) => item is T
): value is T[] {
  if (!isArray(value)) {
    return false;
  }
  
  return value.every(itemValidator);
}

/**
 * Validate file path format
 */
export function isValidFilePath(value: any): value is string {
  if (!isString(value)) {
    return false;
  }
  
  // Basic file path validation - no empty string, no null bytes
  return value.length > 0 && !value.includes('\0');
}

/**
 * Validate directory path format
 */
export function isValidDirectoryPath(value: any): value is string {
  if (!isValidFilePath(value)) {
    return false;
  }
  
  // Directory paths should not end with a file extension
  return !value.match(/\.[a-zA-Z0-9]+$/);
}

/**
 * Validate model ID format
 */
export function isValidModelId(value: any): value is string {
  if (!isString(value)) {
    return false;
  }
  
  // Model IDs should be alphanumeric with hyphens and underscores
  return /^[a-zA-Z0-9_-]+$/.test(value) && value.length > 0;
}

/**
 * Validate URL format
 */
export function isValidUrl(value: any): value is string {
  if (!isString(value)) {
    return false;
  }
  
  try {
    new URL(value);
    return true;
  } catch {
    return false;
  }
}

/**
 * Validate email format
 */
export function isValidEmail(value: any): value is string {
  if (!isString(value)) {
    return false;
  }
  
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(value);
}

/**
 * Validate that a value is one of the allowed options
 */
export function isOneOf<T>(value: any, allowedValues: T[]): value is T {
  return allowedValues.includes(value);
}

/**
 * Sanitize string input by removing potentially dangerous characters
 */
export function sanitizeString(value: string): string {
  return value
    .replace(/[<>]/g, '') // Remove angle brackets
    .replace(/['"]/g, '') // Remove quotes
    .replace(/[&]/g, '&amp;') // Escape ampersands
    .trim();
}

/**
 * Sanitize file path by removing dangerous characters
 */
export function sanitizeFilePath(value: string): string {
  return value
    .replace(/[<>:"|?*]/g, '') // Remove Windows-forbidden characters
    .replace(/\.\./g, '') // Remove parent directory references
    .replace(/^\/+/, '') // Remove leading slashes
    .trim();
}

/**
 * Validate and sanitize configuration object
 */
export function validateAndSanitizeConfig<T extends Record<string, any>>(
  config: any,
  schema: {
    [K in keyof T]: {
      required?: boolean;
      validator: (value: any) => value is T[K];
      sanitizer?: (value: T[K]) => T[K];
      default?: T[K];
    };
  }
): T {
  const result = {} as T;
  
  for (const [key, rules] of Object.entries(schema)) {
    const value = config[key];
    
    // Check if required field is missing
    if (rules.required && (value === undefined || value === null)) {
      throw new Error(`Missing required configuration field: ${key}`);
    }
    
    // Use default value if not provided
    if (value === undefined || value === null) {
      if (rules.default !== undefined) {
        result[key as keyof T] = rules.default;
      }
      continue;
    }
    
    // Validate the value
    if (!rules.validator(value)) {
      throw new Error(`Invalid value for configuration field "${key}": ${value}`);
    }
    
    // Sanitize if sanitizer is provided
    const finalValue = rules.sanitizer ? rules.sanitizer(value) : value;
    result[key as keyof T] = finalValue;
  }
  
  return result;
}

/**
 * Create a validator that checks multiple conditions
 */
export function createCompositeValidator<T>(
  ...validators: Array<(value: any) => value is T>
): (value: any) => value is T {
  return (value: any): value is T => {
    return validators.every(validator => validator(value));
  };
}

/**
 * Create a validator that checks if value passes any of the conditions
 */
export function createUnionValidator<T>(
  ...validators: Array<(value: any) => value is T>
): (value: any) => value is T {
  return (value: any): value is T => {
    return validators.some(validator => validator(value));
  };
}