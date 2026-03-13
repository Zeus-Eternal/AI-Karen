/**
 * Form Validator
 * 
 * Provides validation functionality for authentication forms
 */

import type { FormFieldType, LoginCredentials, FormValidationRule } from '@/types/auth-form';

export interface FieldValidationResult {
  field: FormFieldType;
  isValid: boolean;
  error: string | null;
}

export interface FormValidationResult {
  isValid: boolean;
  errors: Record<FormFieldType, string>;
  fieldResults: Record<FormFieldType, FieldValidationResult>;
}

export interface FormValidator {
  validateField: (field: FormFieldType, value: string) => FieldValidationResult;
  validateFieldDebounced: (field: FormFieldType, value: string, callback: (result: FieldValidationResult) => void, delay?: number) => void;
  validateForm: (credentials: LoginCredentials, requireTwoFactor?: boolean) => FormValidationResult;
  shouldValidateOnChange: (field: FormFieldType) => boolean;
  shouldValidateOnBlur: (field: FormFieldType) => boolean;
  getDebounceDelay: (field: FormFieldType) => number;
  clearDebounceTimers: () => void;
}

export function createFormValidator(enhanced: boolean = false): FormValidator {
  const debounceTimers = new Map<string, NodeJS.Timeout>();

  const validationRules: FormValidationRule[] = [
    {
      field: 'email',
      required: true,
      minLength: 5,
      maxLength: 254,
      pattern: {
        regex: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
        message: 'Please enter a valid email address'
      }
    },
    {
      field: 'password',
      required: true,
      minLength: 8,
      maxLength: 128,
      pattern: {
        regex: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
        message: 'Password must contain at least one lowercase letter, one uppercase letter, and one number'
      }
    },
    {
      field: 'totp_code',
      required: false,
      minLength: 6,
      maxLength: 6,
      pattern: {
        regex: /^\d{6}$/,
        message: 'Two-factor code must be 6 digits'
      }
    }
  ];

  const validateField = (field: FormFieldType, value: string): FieldValidationResult => {
    const rule = validationRules.find(r => r.field === field);
    if (!rule) {
      return {
        field,
        isValid: true,
        error: null
      };
    }

    // Check required
    if (rule.required && (!value || value.trim() === '')) {
      return {
        field,
        isValid: false,
        error: `${field} is required`
      };
    }

    // Skip other validations if field is empty and not required
    if (!value || value.trim() === '') {
      return {
        field,
        isValid: true,
        error: null
      };
    }

    // Check length
    if (rule.minLength && value.length < rule.minLength) {
      return {
        field,
        isValid: false,
        error: `${field} must be at least ${rule.minLength} characters`
      };
    }

    if (rule.maxLength && value.length > rule.maxLength) {
      return {
        field,
        isValid: false,
        error: `${field} must be no more than ${rule.maxLength} characters`
      };
    }

    // Check pattern
    if (rule.pattern && !rule.pattern.regex.test(value)) {
      return {
        field,
        isValid: false,
        error: rule.pattern.message
      };
    }

    // Check custom validator
    if (rule.custom) {
      const customError = rule.custom(value);
      if (customError) {
        return {
          field,
          isValid: false,
          error: customError
        };
      }
    }

    return {
      field,
      isValid: true,
      error: null
    };
  };

  const validateFieldDebounced = (
    field: FormFieldType,
    value: string,
    callback: (result: FieldValidationResult) => void,
    delay: number = 300
  ): void => {
    const timerKey = field;
    
    // Clear existing timer
    const existingTimer = debounceTimers.get(timerKey);
    if (existingTimer) {
      clearTimeout(existingTimer);
    }

    // Set new timer
    const timer = setTimeout(() => {
      const result = validateField(field, value);
      callback(result);
      debounceTimers.delete(timerKey);
    }, delay);

    debounceTimers.set(timerKey, timer);
  };

  const validateForm = (
    credentials: LoginCredentials,
    requireTwoFactor: boolean = false
  ): FormValidationResult => {
    const fieldResults: Record<FormFieldType, FieldValidationResult> = {} as Record<FormFieldType, FieldValidationResult>;
    const errors: Record<FormFieldType, string> = {} as Record<FormFieldType, string>;
    let isValid = true;

    // Validate each field
    const fields: FormFieldType[] = ['email', 'password'];
    if (requireTwoFactor) {
      fields.push('totp_code');
    }

    for (const field of fields) {
      let value = '';
      if (field === 'email') {
        value = credentials.email || '';
      } else if (field === 'password') {
        value = credentials.password || '';
      } else if (field === 'totp_code') {
        value = credentials.totp_code || '';
      }

      const result = validateField(field, value);
      fieldResults[field] = result;

      if (!result.isValid) {
        errors[field] = result.error || 'Invalid value';
        isValid = false;
      }
    }

    return {
      isValid,
      errors,
      fieldResults
    };
  };

  const shouldValidateOnChange = (field: FormFieldType): boolean => {
    // Email and password validate on change for enhanced UX
    if (enhanced) {
      return field === 'email' || field === 'password';
    }
    return false;
  };

  const shouldValidateOnBlur = (): boolean => {
    // All fields validate on blur
    return true;
  };

  const getDebounceDelay = (field: FormFieldType): number => {
    // Different debounce delays for different fields
    switch (field) {
      case 'email':
        return 500; // Longer debounce for email (API validation)
      case 'password':
        return 300; // Medium debounce for password
      case 'totp_code':
        return 200; // Shorter debounce for 2FA code
      default:
        return 300;
    }
  };

  const clearDebounceTimers = (): void => {
    debounceTimers.forEach(timer => clearTimeout(timer));
    debounceTimers.clear();
  };

  return {
    validateField,
    validateFieldDebounced,
    validateForm,
    shouldValidateOnChange,
    shouldValidateOnBlur,
    getDebounceDelay,
    clearDebounceTimers
  };
}

export default createFormValidator;