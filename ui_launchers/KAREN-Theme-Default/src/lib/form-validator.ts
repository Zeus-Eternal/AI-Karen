/**
 * Form validation system with real-time feedback
 * Implements comprehensive validation rules for authentication forms
 */

import type { ValidationRule, ValidationErrors, LoginCredentials } from '@/types/auth';
import type { FormFieldType } from '@/types/auth-form';

/**
 * Validation result for individual fields
 */
export interface FieldValidationResult {
  isValid: boolean;
  error: string | null;
}

/**
 * Complete form validation result
 */
export interface FormValidationResult {
  isValid: boolean;
  errors: ValidationErrors;
  firstErrorField?: FormFieldType;
}

/**
 * Validation configuration for form fields
 */
export interface ValidationConfig {
  email: ValidationRule[];
  password: ValidationRule[];
  totp_code?: ValidationRule[];
}

/**
 * Default validation rules for authentication forms
 */
export const DEFAULT_VALIDATION_RULES: ValidationConfig = {
  email: [
    {
      validate: (value: string) => value.trim().length > 0,
      message: 'Email is required'
    },
    {
      validate: (value: string) => {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(value.trim());
      },
      message: 'Please enter a valid email address'
    },
    {
      validate: (value: string) => value.trim().length <= 254,
      message: 'Email address is too long'
    }
  ],
  password: [
    {
      validate: (value: string) => value.length > 0,
      message: 'Password is required'
    },
    {
      validate: (value: string) => value.length >= 8,
      message: 'Password must be at least 8 characters long'
    },
    {
      validate: (value: string) => value.length <= 128,
      message: 'Password is too long'
    }
  ],
  totp_code: [
    {
      validate: (value: string) => {
        if (!value) return true; // Optional field
        return /^\d{6}$/.test(value.trim());
      },
      message: '2FA code must be exactly 6 digits'
    }
  ]
};

/**
 * Enhanced validation rules with additional security checks
 */
export const ENHANCED_VALIDATION_RULES: ValidationConfig = {
  email: [
    ...DEFAULT_VALIDATION_RULES.email,
    {
      validate: (value: string) => {
        // Check for common email format issues
        const trimmed = value.trim();
        if (!trimmed) return true; // Let required rule handle empty values
        
        // Check for consecutive dots, leading/trailing dots in local part
        const [localPart] = trimmed.split('@');
        if (!localPart) return true; // Let basic email validation handle this
        
        return !localPart.includes('..') && !localPart.startsWith('.') && !localPart.endsWith('.');
      },
      message: 'Email format is invalid'
    }
  ],
  password: [
    {
      validate: (value: string) => value.length > 0,
      message: 'Password is required'
    },
    {
      validate: (value: string) => value.length >= 8,
      message: 'Password must be at least 8 characters long'
    },
    {
      validate: (value: string) => value.length <= 128,
      message: 'Password is too long'
    },
    {
      validate: (value: string) => {
        // Check for common weak passwords first
        const weakPasswords = ['password', '12345678', 'qwerty123', 'admin123'];
        return !weakPasswords.includes(value.toLowerCase());
      },
      message: 'Password is too common. Please choose a stronger password'
    },
    {
      validate: (value: string) => {
        // Check for at least one letter and one number
        return /(?=.*[a-zA-Z])(?=.*\d)/.test(value);
      },
      message: 'Password must contain at least one letter and one number'
    }
  ],
  totp_code: DEFAULT_VALIDATION_RULES.totp_code
};

/**
 * FormValidator class for comprehensive form validation
 */
export class FormValidator {
  private config: ValidationConfig;
  private debounceTimers: Map<string, NodeJS.Timeout> = new Map();

  constructor(config: ValidationConfig = DEFAULT_VALIDATION_RULES) {
    this.config = config;
  }

  /**
   * Validate a single field with its rules
   */
  validateField(field: FormFieldType, value: string): FieldValidationResult {
    const rules = this.config[field];
    if (!rules) {
      return { isValid: true, error: null };
    }

    for (const rule of rules) {
      if (!rule.validate(value)) {
        return {
          isValid: false,
          error: rule.message
        };
      }
    }

    return { isValid: true, error: null };
  }

  /**
   * Validate entire form and return comprehensive results
   */
  validateForm(credentials: LoginCredentials, requireTwoFactor: boolean = false): FormValidationResult {
    const errors: ValidationErrors = {};

    // Validate email
    const emailResult = this.validateField('email', credentials.email);
    if (!emailResult.isValid) {
      errors.email = emailResult.error || undefined;
    }

    // Validate password
    const passwordResult = this.validateField('password', credentials.password);
    if (!passwordResult.isValid) {
      errors.password = passwordResult.error || undefined;
    }

    // Validate TOTP code if required or provided
    if (requireTwoFactor || credentials.totp_code) {
      const totpResult = this.validateField('totp_code', credentials.totp_code || '');
      if (!totpResult.isValid) {
        errors.totp_code = totpResult.error || undefined;
      }
    }

    const isValid = Object.keys(errors).length === 0;
    const firstErrorField = Object.keys(errors)[0] as FormFieldType | undefined;

    return {
      isValid,
      errors,
      firstErrorField
    };
  }

  /**
   * Validate field with debounced execution for real-time validation
   */
  validateFieldDebounced(
    field: FormFieldType,
    value: string,
    callback: (result: FieldValidationResult) => void,
    delay: number = 300
  ): void {
    // Clear existing timer for this field
    const existingTimer = this.debounceTimers.get(field);
    if (existingTimer) {
      clearTimeout(existingTimer);
    }

    // Set new timer
    const timer = setTimeout(() => {
      const result = this.validateField(field, value);
      callback(result);
      this.debounceTimers.delete(field);
    }, delay);

    this.debounceTimers.set(field, timer);
  }

  /**
   * Clear all debounce timers
   */
  clearDebounceTimers(): void {
    this.debounceTimers.forEach(timer => clearTimeout(timer));
    this.debounceTimers.clear();
  }

  /**
   * Check if a field should be validated on change
   */
  shouldValidateOnChange(field: FormFieldType): boolean {
    // Email validation on change for immediate feedback
    if (field === 'email') return true;
    // TOTP validation on change for immediate feedback
    if (field === 'totp_code') return true;
    // Password validation only on blur to avoid interrupting typing
    if (field === 'password') return false;
    
    return true;
  }

  /**
   * Check if a field should be validated on blur
   */
  shouldValidateOnBlur(field: FormFieldType): boolean {
    // All fields should be validated on blur
    return true;
  }

  /**
   * Get appropriate debounce delay for field
   */
  getDebounceDelay(field: FormFieldType): number {
    switch (field) {
      case 'email':
        return 300; // Quick feedback for email format
      case 'password':
        return 500; // Longer delay to avoid interrupting typing
      case 'totp_code':
        return 200; // Quick feedback for 2FA codes
      default:
        return 300;
    }
  }

  /**
   * Update validation configuration
   */
  updateConfig(newConfig: Partial<ValidationConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }

  /**
   * Get current validation configuration
   */
  getConfig(): ValidationConfig {
    return { ...this.config };
  }

  /**
   * Add custom validation rule to a field
   */
  addValidationRule(field: FormFieldType, rule: ValidationRule): void {
    if (!this.config[field]) {
      this.config[field] = [];
    }
    this.config[field]!.push(rule);
  }

  /**
   * Remove validation rule from a field by message
   */
  removeValidationRule(field: FormFieldType, message: string): void {
    if (this.config[field]) {
      this.config[field] = this.config[field]!.filter(rule => rule.message !== message);
    }
  }

  /**
   * Validate email format specifically
   */
  static isValidEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email.trim());
  }

  /**
   * Check password strength
   */
  static getPasswordStrength(password: string): 'weak' | 'medium' | 'strong' {
    if (password.length < 8) return 'weak';
    
    let score = 0;
    
    // Length bonus
    if (password.length >= 12) score += 2;
    else if (password.length >= 10) score += 1;
    
    // Character variety
    if (/[a-z]/.test(password)) score += 1;
    if (/[A-Z]/.test(password)) score += 1;
    if (/\d/.test(password)) score += 1;
    if (/[^a-zA-Z\d]/.test(password)) score += 2;
    
    if (score >= 6) return 'strong';
    if (score >= 3) return 'medium';
    return 'weak';
  }

  /**
   * Sanitize input value
   */
  static sanitizeInput(value: string, field: FormFieldType): string {
    switch (field) {
      case 'email':
        return value.trim().toLowerCase();
      case 'totp_code':
        return value.replace(/\D/g, '').slice(0, 6); // Only digits, max 6
      case 'password':
        return value; // Don't modify password
      default:
        return value.trim();
    }
  }
}

/**
 * Create a FormValidator instance with default configuration
 */
export function createFormValidator(enhanced: boolean = false): FormValidator {
  const config = enhanced ? ENHANCED_VALIDATION_RULES : DEFAULT_VALIDATION_RULES;
  return new FormValidator(config);
}

/**
 * Utility function to get field-specific error messages
 */
export function getFieldErrorMessage(field: FormFieldType, error: string | undefined): string | undefined {
  if (!error) return undefined;
  
  // Add field context to generic error messages
  const fieldNames = {
    email: 'Email',
    password: 'Password',
    totp_code: '2FA Code'
  };
  
  const fieldName = fieldNames[field];
  
  // If error already contains field name, return as is
  if (error.toLowerCase().includes(fieldName.toLowerCase())) {
    return error;
  }
  
  // Add field context for generic messages
  if (error === 'This field is required') {
    return `${fieldName} is required`;
  }
  
  return error;
}

/**
 * Export default validator instance
 */
export const defaultFormValidator = createFormValidator();