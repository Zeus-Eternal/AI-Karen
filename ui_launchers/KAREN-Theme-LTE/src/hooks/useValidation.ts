/**
 * Validation Hook for AI-Karen Production Chat System
 * Provides comprehensive input validation functionality for React components.
 */

import { useCallback, useEffect, useRef, useState } from 'react';

// Validation rule interface
export interface ValidationRule {
  id: string;
  name: string;
  type: 'required' | 'minLength' | 'maxLength' | 'pattern' | 'custom' | 'email' | 'url' | 'number' | 'range' | 'async';
  message?: string;
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  pattern?: RegExp;
  custom?: (value: unknown) => boolean | Promise<boolean>;
  min?: number;
  max?: number;
  async?: boolean;
  debounceMs?: number;
}

// Validation result interface
export interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
}

// Validation error interface
export interface ValidationError {
  id: string;
  field: string;
  message: string;
  code: string;
  severity: 'error' | 'warning' | 'info';
  value?: unknown;
  rule?: string;
}

// Validation warning interface
export interface ValidationWarning {
  id: string;
  field: string;
  message: string;
  code: string;
  value?: unknown;
  rule?: string;
}

// Validation state interface
export interface ValidationState {
  isValid: boolean;
  isDirty: boolean;
  isTouched: boolean;
  isPending: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
  value: unknown;
  originalValue: unknown;
}

// Form validation state interface
export interface FormValidationState {
  [fieldName: string]: ValidationState;
}

// Validation hook options interface
export interface ValidationOptions {
  validateOnChange?: boolean;
  validateOnBlur?: boolean;
  debounceMs?: number;
  showWarnings?: boolean;
  stopOnFirstError?: boolean;
  customRules?: ValidationRule[];
}

// Built-in validation rules
export const ValidationRules = {
  required: (message?: string): ValidationRule => ({
    id: 'required',
    name: 'required',
    type: 'required',
    message,
    custom: (value: unknown) => {
      if (value === null || value === undefined || value === '') {
        return false;
      }
      if (typeof value === 'string' && value.trim() === '') {
        return false;
      }
      if (Array.isArray(value) && value.length === 0) {
        return false;
      }
      return true;
    }
  }),

  minLength: (min: number, message?: string): ValidationRule => ({
    id: `minLength-${min}`,
    name: 'maxLength',
    type: 'minLength',
    message,
    custom: (value: unknown) => {
      if (value === null || value === undefined) {
        return true;
      }
      if (typeof value === 'string') {
        return value.length >= min;
      }
      if (Array.isArray(value)) {
        return value.length >= min;
      }
      return true;
    }
  }),

  maxLength: (max: number, message?: string): ValidationRule => ({
    id: `maxLength-${max}`,
    name: 'maxLength',
    type: 'maxLength',
    message,
    maxLength: max,
    custom: (value: unknown) => {
      if (value === null || value === undefined) {
        return true;
      }
      if (typeof value === 'string') {
        return value.length <= max;
      }
      if (Array.isArray(value)) {
        return value.length <= max;
      }
      return true;
    }
  }),

  pattern: (regex: RegExp, message?: string): ValidationRule => ({
    id: `pattern-${regex.toString()}`,
    name: 'pattern',
    type: 'pattern',
    message,
    pattern: regex,
    custom: (value: unknown) => {
      if (value === null || value === undefined) {
        return true;
      }
      if (typeof value === 'string') {
        return regex.test(value);
      }
      return true;
    }
  }),

  email: (message?: string): ValidationRule => ({
    id: 'email',
    name: 'email',
    type: 'email',
    message,
    pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
    custom: (value: unknown) => {
      if (value === null || value === undefined || value === '') {
        return true;
      }
      return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(value));
    }
  }),

  url: (message?: string): ValidationRule => ({
    id: 'url',
    name: 'url',
    type: 'url',
    message,
    pattern: /^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)?$/,
    custom: (value: unknown) => {
      if (value === null || value === undefined || value === '') {
        return true;
      }
      try {
        new URL(String(value));
        return true;
      } catch {
        return false;
      }
    }
  }),

  number: (message?: string): ValidationRule => ({
    id: 'number',
    name: 'number',
    type: 'number',
    message,
    custom: (value: unknown) => {
      if (value === null || value === undefined || value === '') {
        return true;
      }
      return !isNaN(Number(value));
    }
  }),

  range: (min: number, max: number, message?: string): ValidationRule => ({
    id: `range-${min}-${max}`,
    name: 'range',
    type: 'range',
    message,
    min,
    custom: (value: unknown) => {
      if (value === null || value === undefined || value === '') {
        return true;
      }
      const num = Number(value);
      return !isNaN(num) && num >= min && num <= max;
    }
  }),

  custom: (validator: (value: unknown) => boolean | Promise<boolean>, message?: string): ValidationRule => ({
    id: 'custom',
    name: 'custom',
    type: 'custom',
    message,
    custom: validator,
    async: validator.constructor.name === 'AsyncFunction'
  })
};

/**
 * Hook for field validation
 *
 * Provides:
 * - Real-time validation
 * - Debounced validation for performance
 * - Custom validation rules
 * - Validation state management
 * - Error message formatting
 *
 * @param value - Value to validate
 * @param rules - Validation rules to apply
 * @param options - Configuration options for validation
 * @returns - Validation state and utilities
 */
export const useValidation = (
  value: unknown,
  rules: ValidationRule[] = [],
  options: ValidationOptions = {}
) => {
  const {
    validateOnChange = true,
    validateOnBlur = true,
    debounceMs = 300,
    showWarnings = true,
    stopOnFirstError = false,
    customRules = []
  } = options;

  const [validationState, setValidationState] = useState<ValidationState>({
    isValid: true,
    isDirty: false,
    isTouched: false,
    isPending: false,
    errors: [],
    warnings: [],
    value,
    originalValue: value
  });

  const [isDebouncing, setIsDebouncing] = useState(false);
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  const validateValue = useCallback(async (val: unknown): Promise<ValidationResult> => {
    setIsDebouncing(true);

    try {
      const allRules = [...rules, ...customRules];
      const errors: ValidationError[] = [];
      const warnings: ValidationWarning[] = [];
      let isValid = true;

      for (const rule of allRules) {
        try {
          let result: boolean;

          if (rule.async) {
            const asyncResult = await rule.custom!(val);
            result = await asyncResult;
          } else {
            const syncResult = rule.custom!(val);
            result = syncResult instanceof Promise ? await syncResult : syncResult;
          }

          if (!result) {
            const error: ValidationError = {
              id: `${rule.id}-${Date.now()}`,
              field: '',
              message: getErrorMessage(rule),
              code: rule.name,
              severity: 'error',
              value: val,
              rule: rule.id
            };
            errors.push(error);
            isValid = false;

            if (stopOnFirstError) {
              break;
            }
          }
        } catch (error) {
          const validationError: ValidationError = {
            id: `validation-error-${Date.now()}`,
            field: '',
            message: `Validation error: ${error}`,
            code: 'validation_error',
            severity: 'error',
            value: val,
            rule: rule.id
          };
          errors.push(validationError);
          isValid = false;

          if (stopOnFirstError) {
            break;
          }
        }
      }

      setIsDebouncing(false);
      return {
        isValid,
        errors,
        warnings
      };
    } catch (error) {
      setIsDebouncing(false);
      return {
        isValid: false,
        errors: [{
          id: `validation-error-${Date.now()}`,
          field: '',
          message: `Validation error: ${error}`,
          code: 'validation_error',
          severity: 'error',
          value: val
        }],
        warnings: []
      };
    }
  }, [rules, customRules, stopOnFirstError]);

  // Get error message for rule
  const getErrorMessage = (rule: ValidationRule): string => {
    if (rule.message) {
      return rule.message;
    }

    switch (rule.type) {
      case 'required':
        return 'This field is required';
      case 'minLength':
        return `Must be at least ${rule.minLength} characters`;
      case 'maxLength':
        return `Must be no more than ${rule.maxLength} characters`;
      case 'pattern':
        return 'Invalid format';
      case 'email':
        return 'Must be a valid email address';
      case 'url':
        return 'Must be a valid URL';
      case 'number':
        return 'Must be a valid number';
      case 'range':
        return `Must be between ${rule.min} and ${rule.max}`;
      default:
        return 'Invalid value';
    }
  };

  // Debounced validation
  const debouncedValidate = useCallback(
    async (val: unknown) => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }

      debounceTimerRef.current = setTimeout(async () => {
        const result = await validateValue(val);
        setValidationState(prev => ({
          ...prev,
          isValid: result.isValid,
          errors: result.errors,
          warnings: showWarnings ? result.warnings : [],
          isPending: false
        }));
      }, debounceMs);
    },
    [validateValue, debounceMs, showWarnings]
  );

  // Handle value change
  useEffect(() => {
    if (validateOnChange) {
      setValidationState(prev => ({
        ...prev,
        isDirty: true,
        isTouched: true,
        isPending: true,
        value
      }));
      debouncedValidate(value);
    }
  }, [value, validateOnChange, debouncedValidate]);

  // Handle blur
  const handleBlur = useCallback(() => {
    if (validateOnBlur) {
      setValidationState(prev => ({
        ...prev,
        isTouched: true
      }));
      debouncedValidate(value);
    }
  }, [validateOnBlur, debouncedValidate, value]);

  // Clear validation state
  const clearValidation = useCallback(() => {
    setValidationState({
      isValid: true,
      isDirty: false,
      isTouched: false,
      isPending: false,
      errors: [],
      warnings: [],
      value,
      originalValue: value
    });
  }, [value]);

  // Set custom error
  const setError = useCallback((error: ValidationError) => {
    setValidationState(prev => ({
      ...prev,
      isValid: false,
      errors: [error],
      warnings: []
    }));
  }, []);

  // Set custom warning
  const setWarning = useCallback((warning: ValidationWarning) => {
    setValidationState(prev => ({
      ...prev,
      warnings: [...prev.warnings, warning]
    }));
  }, []);

  // Reset to original value
  const resetToOriginal = useCallback(() => {
    setValidationState(prev => ({
      ...prev,
      value: prev.originalValue,
      isValid: true,
      errors: [],
      warnings: []
    }));
  }, []);

  // Cleanup debounce timer on unmount
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  return {
    ...validationState,
    validate: validateValue,
    clear: clearValidation,
    setError,
    setWarning,
    resetToOriginal,
    handleBlur,
    isDebouncing
  };
};
