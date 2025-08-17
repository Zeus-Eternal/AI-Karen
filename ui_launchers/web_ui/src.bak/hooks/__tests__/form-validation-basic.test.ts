/**
 * Basic tests for form validation system
 * Tests the core functionality that's required for the task
 */

import { describe, it, expect } from 'vitest';
import { FormValidator, createFormValidator } from '@/lib/form-validator';
import type { LoginCredentials } from '@/types/auth';

describe('Form Validation System', () => {
  describe('FormValidator Class', () => {
    it('should create validator with email and password validation rules', () => {
      const validator = createFormValidator();
      expect(validator).toBeInstanceOf(FormValidator);
      
      const config = validator.getConfig();
      expect(config.email).toBeDefined();
      expect(config.password).toBeDefined();
      expect(config.email.length).toBeGreaterThan(0);
      expect(config.password.length).toBeGreaterThan(0);
    });

    it('should validate email field with real-time feedback', () => {
      const validator = createFormValidator();
      
      // Test invalid email
      const invalidResult = validator.validateField('email', 'invalid-email');
      expect(invalidResult.isValid).toBe(false);
      expect(invalidResult.error).toBe('Please enter a valid email address');
      
      // Test valid email
      const validResult = validator.validateField('email', 'user@example.com');
      expect(validResult.isValid).toBe(true);
      expect(validResult.error).toBeNull();
    });

    it('should validate password field with real-time feedback', () => {
      const validator = createFormValidator();
      
      // Test short password
      const shortResult = validator.validateField('password', 'short');
      expect(shortResult.isValid).toBe(false);
      expect(shortResult.error).toBe('Password must be at least 8 characters long');
      
      // Test valid password
      const validResult = validator.validateField('password', 'validpassword123');
      expect(validResult.isValid).toBe(true);
      expect(validResult.error).toBeNull();
    });

    it('should provide field-specific error display and clearing logic', () => {
      const validator = createFormValidator();
      
      // Test field-specific errors
      const emailError = validator.validateField('email', '');
      expect(emailError.error).toBe('Email is required');
      
      const passwordError = validator.validateField('password', '');
      expect(passwordError.error).toBe('Password is required');
      
      // Test clearing errors by providing valid input
      const validEmail = validator.validateField('email', 'user@example.com');
      expect(validEmail.error).toBeNull();
      
      const validPassword = validator.validateField('password', 'validpassword123');
      expect(validPassword.error).toBeNull();
    });

    it('should validate complete form', () => {
      const validator = createFormValidator();
      
      const invalidCredentials: LoginCredentials = {
        email: 'invalid',
        password: 'short'
      };
      
      const invalidResult = validator.validateForm(invalidCredentials);
      expect(invalidResult.isValid).toBe(false);
      expect(invalidResult.errors.email).toBeDefined();
      expect(invalidResult.errors.password).toBeDefined();
      
      const validCredentials: LoginCredentials = {
        email: 'user@example.com',
        password: 'validpassword123'
      };
      
      const validResult = validator.validateForm(validCredentials);
      expect(validResult.isValid).toBe(true);
      expect(Object.keys(validResult.errors)).toHaveLength(0);
    });

    it('should support debounced validation', () => {
      const validator = createFormValidator();
      
      // Test that debounce delays are configured
      expect(validator.getDebounceDelay('email')).toBe(300);
      expect(validator.getDebounceDelay('password')).toBe(500);
      expect(validator.getDebounceDelay('totp_code')).toBe(200);
    });

    it('should support enhanced validation rules', () => {
      const enhancedValidator = createFormValidator(true);
      
      // Test enhanced password validation
      const weakPasswordResult = enhancedValidator.validateField('password', 'password');
      expect(weakPasswordResult.isValid).toBe(false);
      expect(weakPasswordResult.error).toBe('Password is too common. Please choose a stronger password');
      
      // Test password with letter and number requirement
      const noNumberResult = enhancedValidator.validateField('password', 'onlyletters');
      expect(noNumberResult.isValid).toBe(false);
      expect(noNumberResult.error).toBe('Password must contain at least one letter and one number');
    });

    it('should handle validation timing preferences', () => {
      const validator = createFormValidator();
      
      // Email should validate on change
      expect(validator.shouldValidateOnChange('email')).toBe(true);
      
      // Password should not validate on change (to avoid interrupting typing)
      expect(validator.shouldValidateOnChange('password')).toBe(false);
      
      // All fields should validate on blur
      expect(validator.shouldValidateOnBlur('email')).toBe(true);
      expect(validator.shouldValidateOnBlur('password')).toBe(true);
      expect(validator.shouldValidateOnBlur('totp_code')).toBe(true);
    });
  });

  describe('Validation Rules', () => {
    it('should have comprehensive email validation rules', () => {
      const validator = createFormValidator();
      
      // Required
      expect(validator.validateField('email', '').isValid).toBe(false);
      
      // Format validation
      expect(validator.validateField('email', 'invalid').isValid).toBe(false);
      expect(validator.validateField('email', 'invalid@').isValid).toBe(false);
      expect(validator.validateField('email', '@invalid.com').isValid).toBe(false);
      
      // Valid emails
      expect(validator.validateField('email', 'user@example.com').isValid).toBe(true);
      expect(validator.validateField('email', 'test.email+tag@domain.co.uk').isValid).toBe(true);
    });

    it('should have comprehensive password validation rules', () => {
      const validator = createFormValidator();
      
      // Required
      expect(validator.validateField('password', '').isValid).toBe(false);
      
      // Length validation
      expect(validator.validateField('password', 'short').isValid).toBe(false);
      expect(validator.validateField('password', 'a'.repeat(129)).isValid).toBe(false);
      
      // Valid passwords
      expect(validator.validateField('password', 'validpassword').isValid).toBe(true);
      expect(validator.validateField('password', 'validpassword123').isValid).toBe(true);
    });

    it('should have optional TOTP validation rules', () => {
      const validator = createFormValidator();
      
      // Optional field - empty should be valid
      expect(validator.validateField('totp_code', '').isValid).toBe(true);
      
      // Format validation when provided
      expect(validator.validateField('totp_code', '123').isValid).toBe(false);
      expect(validator.validateField('totp_code', '1234567').isValid).toBe(false);
      expect(validator.validateField('totp_code', 'abcdef').isValid).toBe(false);
      
      // Valid TOTP codes
      expect(validator.validateField('totp_code', '123456').isValid).toBe(true);
      expect(validator.validateField('totp_code', '000000').isValid).toBe(true);
    });
  });

  describe('Error Handling', () => {
    it('should provide user-friendly error messages', () => {
      const validator = createFormValidator();
      
      const emailError = validator.validateField('email', '');
      expect(emailError.error).toBe('Email is required');
      
      const formatError = validator.validateField('email', 'invalid');
      expect(formatError.error).toBe('Please enter a valid email address');
      
      const passwordError = validator.validateField('password', '');
      expect(passwordError.error).toBe('Password is required');
      
      const lengthError = validator.validateField('password', 'short');
      expect(lengthError.error).toBe('Password must be at least 8 characters long');
    });

    it('should handle form validation with multiple errors', () => {
      const validator = createFormValidator();
      
      const result = validator.validateForm({
        email: '',
        password: ''
      });
      
      expect(result.isValid).toBe(false);
      expect(result.errors.email).toBe('Email is required');
      expect(result.errors.password).toBe('Password is required');
      expect(result.firstErrorField).toBe('email');
    });
  });
});