/**
 * Unit tests for FormValidator class
 * Tests validation rules, error handling, and debounced validation
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import {
  FormValidator,
  createFormValidator,
  DEFAULT_VALIDATION_RULES,
  ENHANCED_VALIDATION_RULES,
  getFieldErrorMessage
} from '../form-validator';
import type { LoginCredentials } from '@/types/auth';
import type { FormFieldType } from '@/types/auth-form';

describe('FormValidator', () => {
  let validator: FormValidator;

  beforeEach(() => {
    validator = createFormValidator();
    vi.useFakeTimers();
  });

  afterEach(() => {
    validator.clearDebounceTimers();
    vi.useRealTimers();
  });

  describe('Email Validation', () => {
    it('should validate required email', () => {
      const result = validator.validateField('email', '');
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Email is required');
    });

    it('should validate email format', () => {
      const invalidEmails = [
        'invalid-email',
        '@domain.com',
        'user@',
        'user@domain',
        'user.domain.com',
        'user@domain.',
        'user @domain.com',
        'user@domain .com'
      ];

      invalidEmails.forEach(email => {
        const result = validator.validateField('email', email);
        expect(result.isValid).toBe(false);
        expect(result.error).toBe('Please enter a valid email address');
      });
    });

    it('should accept valid email addresses', () => {
      const validEmails = [
        'user@domain.com',
        'test.email@example.org',
        'user+tag@domain.co.uk',
        'firstname.lastname@company.com',
        'user123@test-domain.com'
      ];

      validEmails.forEach(email => {
        const result = validator.validateField('email', email);
        expect(result.isValid).toBe(true);
        expect(result.error).toBeNull();
      });
    });

    it('should validate email length', () => {
      const longEmail = 'a'.repeat(250) + '@domain.com';
      const result = validator.validateField('email', longEmail);
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Email address is too long');
    });

    it('should trim whitespace from email', () => {
      const result = validator.validateField('email', '  user@domain.com  ');
      expect(result.isValid).toBe(true);
    });
  });

  describe('Password Validation', () => {
    it('should validate required password', () => {
      const result = validator.validateField('password', '');
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Password is required');
    });

    it('should validate minimum password length', () => {
      const result = validator.validateField('password', '1234567');
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Password must be at least 8 characters long');
    });

    it('should validate maximum password length', () => {
      const longPassword = 'a'.repeat(129);
      const result = validator.validateField('password', longPassword);
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Password is too long');
    });

    it('should accept valid passwords', () => {
      const validPasswords = [
        'password123',
        'mySecurePass1',
        'anotherValidPassword2024',
        '12345678'
      ];

      validPasswords.forEach(password => {
        const result = validator.validateField('password', password);
        expect(result.isValid).toBe(true);
        expect(result.error).toBeNull();
      });
    });
  });

  describe('TOTP Code Validation', () => {
    it('should accept empty TOTP code (optional field)', () => {
      const result = validator.validateField('totp_code', '');
      expect(result.isValid).toBe(true);
      expect(result.error).toBeNull();
    });

    it('should validate TOTP code format', () => {
      const invalidCodes = [
        '12345',     // Too short
        '1234567',   // Too long
        '12345a',    // Contains letters
        '123 456',   // Contains space
        '123-456'    // Contains dash
      ];

      invalidCodes.forEach(code => {
        const result = validator.validateField('totp_code', code);
        expect(result.isValid).toBe(false);
        expect(result.error).toBe('2FA code must be exactly 6 digits');
      });
    });

    it('should accept valid TOTP codes', () => {
      const validCodes = ['123456', '000000', '999999'];

      validCodes.forEach(code => {
        const result = validator.validateField('totp_code', code);
        expect(result.isValid).toBe(true);
        expect(result.error).toBeNull();
      });
    });
  });

  describe('Enhanced Validation Rules', () => {
    beforeEach(() => {
      validator = new FormValidator(ENHANCED_VALIDATION_RULES);
    });

    it('should validate email format more strictly', () => {
      const invalidEmails = [
        'user..name@domain.com',
        '.user@domain.com',
        'user.@domain.com'
      ];

      invalidEmails.forEach(email => {
        const result = validator.validateField('email', email);
        expect(result.isValid).toBe(false);
        expect(result.error).toBe('Email format is invalid');
      });
    });

    it('should require letter and number in password', () => {
      const result = validator.validateField('password', 'onlyletters');
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Password must contain at least one letter and one number');
    });

    it('should reject common weak passwords', () => {
      const weakPasswords = ['password', '12345678', 'qwerty123', 'admin123'];

      weakPasswords.forEach(password => {
        const result = validator.validateField('password', password);
        expect(result.isValid).toBe(false);
        expect(result.error).toBe('Password is too common. Please choose a stronger password');
      });
    });

    it('should accept strong passwords', () => {
      const strongPasswords = ['MySecure123', 'Another1Valid', 'Complex9Pass'];

      strongPasswords.forEach(password => {
        const result = validator.validateField('password', password);
        expect(result.isValid).toBe(true);
        expect(result.error).toBeNull();
      });
    });
  });

  describe('Form Validation', () => {
    it('should validate complete form', () => {
      const credentials: LoginCredentials = {
        email: 'user@domain.com',
        password: 'password123'
      };

      const result = validator.validateForm(credentials);
      expect(result.isValid).toBe(true);
      expect(Object.keys(result.errors)).toHaveLength(0);
    });

    it('should return errors for invalid form', () => {
      const credentials: LoginCredentials = {
        email: 'invalid-email',
        password: '123'
      };

      const result = validator.validateForm(credentials);
      expect(result.isValid).toBe(false);
      expect(result.errors.email).toBe('Please enter a valid email address');
      expect(result.errors.password).toBe('Password must be at least 8 characters long');
      expect(result.firstErrorField).toBe('email');
    });

    it('should validate TOTP when required', () => {
      const credentials: LoginCredentials = {
        email: 'user@domain.com',
        password: 'password123',
        totp_code: '12345'
      };

      const result = validator.validateForm(credentials, true);
      expect(result.isValid).toBe(false);
      expect(result.errors.totp_code).toBe('2FA code must be exactly 6 digits');
    });

    it('should validate TOTP when provided', () => {
      const credentials: LoginCredentials = {
        email: 'user@domain.com',
        password: 'password123',
        totp_code: '12345'
      };

      const result = validator.validateForm(credentials, false);
      expect(result.isValid).toBe(false);
      expect(result.errors.totp_code).toBe('2FA code must be exactly 6 digits');
    });
  });

  describe('Debounced Validation', () => {
    it('should debounce field validation', () => {
      const callback = vi.fn();

      validator.validateFieldDebounced('email', 'user@domain.com', callback, 100);

      expect(callback).not.toHaveBeenCalled();

      vi.advanceTimersByTime(100);

      expect(callback).toHaveBeenCalledWith({
        isValid: true,
        error: null
      });
    });

    it('should cancel previous debounced validation', () => {
      const callback = vi.fn();

      // First validation
      validator.validateFieldDebounced('email', 'invalid', callback, 100);

      // Second validation before first completes
      validator.validateFieldDebounced('email', 'user@domain.com', callback, 100);

      vi.advanceTimersByTime(100);

      // Should only call callback once with the latest validation
      expect(callback).toHaveBeenCalledTimes(1);
      expect(callback).toHaveBeenCalledWith({
        isValid: true,
        error: null
      });
    });

    it('should clear all debounce timers', () => {
      const callback = vi.fn();

      validator.validateFieldDebounced('email', 'test', callback, 100);
      validator.validateFieldDebounced('password', 'test', callback, 100);

      validator.clearDebounceTimers();

      vi.advanceTimersByTime(100);

      expect(callback).not.toHaveBeenCalled();
    });
  });

  describe('Configuration Management', () => {
    it('should update validation configuration', () => {
      const newRule = {
        validate: (value: string) => value.includes('@test.com'),
        message: 'Must be a test email'
      };

      validator.updateConfig({
        email: [newRule]
      });

      const result = validator.validateField('email', 'user@domain.com');
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Must be a test email');
    });

    it('should add custom validation rule', () => {
      const customRule = {
        validate: (value: string) => value.length >= 10,
        message: 'Password must be at least 10 characters'
      };

      validator.addValidationRule('password', customRule);

      const result = validator.validateField('password', 'short123');
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Password must be at least 10 characters');
    });

    it('should remove validation rule', () => {
      // First add a custom rule to test removal
      const customRule = {
        validate: (value: string) => value.length >= 10,
        message: 'Password must be at least 10 characters'
      };
      validator.addValidationRule('password', customRule);

      // Verify the custom rule is working
      let result = validator.validateField('password', 'short123');
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Password must be at least 10 characters');

      // Remove the custom rule
      validator.removeValidationRule('password', 'Password must be at least 10 characters');

      // Now it should pass the original 8-character rule
      result = validator.validateField('password', 'short123');
      expect(result.isValid).toBe(true);
      expect(result.error).toBeNull();
    });
  });

  describe('Validation Timing', () => {
    it('should validate email on change', () => {
      expect(validator.shouldValidateOnChange('email')).toBe(true);
    });

    it('should not validate password on change', () => {
      expect(validator.shouldValidateOnChange('password')).toBe(false);
    });

    it('should validate TOTP on change', () => {
      expect(validator.shouldValidateOnChange('totp_code')).toBe(true);
    });

    it('should validate all fields on blur', () => {
      expect(validator.shouldValidateOnBlur('email')).toBe(true);
      expect(validator.shouldValidateOnBlur('password')).toBe(true);
      expect(validator.shouldValidateOnBlur('totp_code')).toBe(true);
    });

    it('should return appropriate debounce delays', () => {
      expect(validator.getDebounceDelay('email')).toBe(300);
      expect(validator.getDebounceDelay('password')).toBe(500);
      expect(validator.getDebounceDelay('totp_code')).toBe(200);
    });
  });

  describe('Static Utility Methods', () => {
    it('should validate email format', () => {
      expect(FormValidator.isValidEmail('user@domain.com')).toBe(true);
      expect(FormValidator.isValidEmail('invalid-email')).toBe(false);
      expect(FormValidator.isValidEmail('  user@domain.com  ')).toBe(true);
    });

    it('should assess password strength', () => {
      expect(FormValidator.getPasswordStrength('weak')).toBe('weak');
      expect(FormValidator.getPasswordStrength('password123')).toBe('medium');
      expect(FormValidator.getPasswordStrength('StrongPass123!')).toBe('strong');
      expect(FormValidator.getPasswordStrength('VeryLongAndComplexPassword123!')).toBe('strong');
    });

    it('should sanitize input values', () => {
      expect(FormValidator.sanitizeInput('  USER@DOMAIN.COM  ', 'email')).toBe('user@domain.com');
      expect(FormValidator.sanitizeInput('123abc456def', 'totp_code')).toBe('123456');
      expect(FormValidator.sanitizeInput('password123', 'password')).toBe('password123');
    });
  });

  describe('Error Message Utilities', () => {
    it('should return field-specific error messages', () => {
      expect(getFieldErrorMessage('email', 'This field is required')).toBe('Email is required');
      expect(getFieldErrorMessage('password', 'This field is required')).toBe('Password is required');
      expect(getFieldErrorMessage('totp_code', 'This field is required')).toBe('2FA Code is required');
    });

    it('should return original message if field name already included', () => {
      const message = 'Email format is invalid';
      expect(getFieldErrorMessage('email', message)).toBe(message);
    });

    it('should return undefined for undefined error', () => {
      expect(getFieldErrorMessage('email', undefined)).toBeUndefined();
    });
  });

  describe('Factory Functions', () => {
    it('should create validator with default rules', () => {
      const defaultValidator = createFormValidator(false);
      expect(defaultValidator.getConfig()).toEqual(DEFAULT_VALIDATION_RULES);
    });

    it('should create validator with enhanced rules', () => {
      const enhancedValidator = createFormValidator(true);
      expect(enhancedValidator.getConfig()).toEqual(ENHANCED_VALIDATION_RULES);
    });
  });
});