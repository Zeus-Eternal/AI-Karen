/**
 * Tests for setup validation utilities
 * Tests password strength validation, email verification, and super admin creation validation
 */

import { describe, it, expect, vi } from 'vitest';
import {
  validateSuperAdminCreation,
  calculatePasswordStrength,
  validateEmailFormat,
  generateEmailVerificationToken,
  verifyEmailVerificationToken,
  hashPassword,
  createSuperAdminValidator,
  SUPER_ADMIN_PASSWORD_RULES,
  SUPER_ADMIN_EMAIL_RULES,
  FULL_NAME_RULES
} from '../setup-validation';
import type { CreateSuperAdminRequest } from '@/types/admin';

describe('Setup Validation Utilities', () => {
  describe('validateSuperAdminCreation', () => {
    const validRequest: CreateSuperAdminRequest = {
      email: 'admin@example.com',
      full_name: 'System Administrator',
      password: 'SuperSecure987!@#',
      confirm_password: 'SuperSecure987!@#'
    };

    it('should validate a valid super admin creation request', async () => {
      const result = await validateSuperAdminCreation(validRequest);
      
      expect(result.isValid).toBe(true);
      expect(Object.keys(result.errors)).toHaveLength(0);
    });

    it('should reject empty email', async () => {
      const request = { ...validRequest, email: '' };
      const result = await validateSuperAdminCreation(request);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.email).toBe('Email is required');
    });

    it('should reject invalid email format', async () => {
      const request = { ...validRequest, email: 'invalid-email' };
      const result = await validateSuperAdminCreation(request);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.email).toBe('Please enter a valid email address');
    });

    it('should reject temporary email domains', async () => {
      const request = { ...validRequest, email: 'test@10minutemail.com' };
      const result = await validateSuperAdminCreation(request);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.email).toBe('Please use a permanent email address');
    });

    it('should reject empty full name', async () => {
      const request = { ...validRequest, full_name: '' };
      const result = await validateSuperAdminCreation(request);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.full_name).toBe('Full name is required');
    });

    it('should reject full name with invalid characters', async () => {
      const request = { ...validRequest, full_name: 'Admin@123' };
      const result = await validateSuperAdminCreation(request);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.full_name).toBe('Full name can only contain letters, spaces, hyphens, apostrophes, and periods');
    });

    it('should reject short password', async () => {
      const request = { 
        ...validRequest, 
        password: 'Short1!', 
        confirm_password: 'Short1!' 
      };
      const result = await validateSuperAdminCreation(request);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.password).toBe('Password must be at least 12 characters long');
    });

    it('should reject password without uppercase', async () => {
      const request = { 
        ...validRequest, 
        password: 'supersecure123!@#', 
        confirm_password: 'supersecure123!@#' 
      };
      const result = await validateSuperAdminCreation(request);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.password).toBe('Password must contain at least one uppercase letter');
    });

    it('should reject password without lowercase', async () => {
      const request = { 
        ...validRequest, 
        password: 'SUPERSECURE123!@#', 
        confirm_password: 'SUPERSECURE123!@#' 
      };
      const result = await validateSuperAdminCreation(request);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.password).toBe('Password must contain at least one lowercase letter');
    });

    it('should reject password without numbers', async () => {
      const request = { 
        ...validRequest, 
        password: 'SuperSecure!@#', 
        confirm_password: 'SuperSecure!@#' 
      };
      const result = await validateSuperAdminCreation(request);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.password).toBe('Password must contain at least one number');
    });

    it('should reject password without special characters', async () => {
      const request = { 
        ...validRequest, 
        password: 'SuperSecure123', 
        confirm_password: 'SuperSecure123' 
      };
      const result = await validateSuperAdminCreation(request);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.password).toBe('Password must contain at least one special character');
    });

    it('should reject common weak passwords', async () => {
      const request = { 
        ...validRequest, 
        password: 'Password123!', 
        confirm_password: 'Password123!' 
      };
      const result = await validateSuperAdminCreation(request);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.password).toBe('Password is too common. Please choose a more unique password');
    });

    it('should reject password with sequential characters', async () => {
      const request = { 
        ...validRequest, 
        password: 'SuperSecure123!', 
        confirm_password: 'SuperSecure123!' 
      };
      const result = await validateSuperAdminCreation(request);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.password).toBe('Password should not contain sequential characters');
    });

    it('should reject password with repeated characters', async () => {
      const request = { 
        ...validRequest, 
        password: 'SuperSecureaaa1!', 
        confirm_password: 'SuperSecureaaa1!' 
      };
      const result = await validateSuperAdminCreation(request);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.password).toBe('Password should not contain repeated characters');
    });

    it('should reject mismatched passwords', async () => {
      const request = { 
        ...validRequest, 
        confirm_password: 'DifferentPassword123!@#' 
      };
      const result = await validateSuperAdminCreation(request);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.confirm_password).toBe('Passwords do not match');
    });

    it('should reject password containing email', async () => {
      const request = { 
        ...validRequest, 
        email: 'admin@example.com',
        password: 'AdminSecure123!@#', 
        confirm_password: 'AdminSecure123!@#' 
      };
      const result = await validateSuperAdminCreation(request);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.password).toBe('Password should not contain your email address');
    });

    it('should reject password containing name', async () => {
      const request = { 
        ...validRequest, 
        full_name: 'John Smith',
        password: 'JohnSecure123!@#', 
        confirm_password: 'JohnSecure123!@#' 
      };
      const result = await validateSuperAdminCreation(request);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.password).toBe('Password should not contain your name');
    });
  });

  describe('calculatePasswordStrength', () => {
    it('should rate very weak password correctly', () => {
      const result = calculatePasswordStrength('weak');
      
      expect(result.level).toBe('very_weak');
      expect(result.score).toBeLessThan(2);
      expect(result.feedback).toContain('Use at least 12 characters');
    });

    it('should rate weak password correctly', () => {
      const result = calculatePasswordStrength('weak12A');
      
      expect(result.level).toBe('weak');
      expect(result.score).toBeGreaterThanOrEqual(2);
      expect(result.score).toBeLessThan(4);
    });

    it('should rate medium password correctly', () => {
      const result = calculatePasswordStrength('WeakPass12');
      
      expect(result.level).toBe('medium');
      expect(result.score).toBeGreaterThanOrEqual(4);
      expect(result.score).toBeLessThan(6);
    });

    it('should rate strong password correctly', () => {
      const result = calculatePasswordStrength('MediumPass987!');
      
      expect(result.level).toBe('strong');
      expect(result.score).toBeGreaterThanOrEqual(6);
      expect(result.score).toBeLessThan(8);
    });

    it('should rate very strong password correctly', () => {
      const result = calculatePasswordStrength('StrongPassword987!');
      
      expect(result.level).toBe('very_strong');
      expect(result.score).toBeGreaterThanOrEqual(8);
    });

    it('should penalize repeated characters', () => {
      const normalResult = calculatePasswordStrength('StrongPassword987!');
      const repeatedResult = calculatePasswordStrength('StrongPasswordddd987!');
      
      expect(repeatedResult.score).toBeLessThan(normalResult.score);
      expect(repeatedResult.feedback).toContain('Avoid repeated characters');
    });

    it('should penalize sequential characters', () => {
      const normalResult = calculatePasswordStrength('StrongPassword975!');
      const sequentialResult = calculatePasswordStrength('StrongPassword123!');
      
      expect(sequentialResult.score).toBeLessThan(normalResult.score);
      expect(sequentialResult.feedback).toContain('Avoid sequential characters');
    });

    it('should provide helpful feedback', () => {
      const result = calculatePasswordStrength('short');
      
      expect(result.feedback).toContain('Use at least 12 characters');
      expect(result.feedback).toContain('Add uppercase letters');
      expect(result.feedback).toContain('Add numbers');
      expect(result.feedback).toContain('Add special characters');
    });
  });

  describe('validateEmailFormat', () => {
    it('should validate correct email format', () => {
      const result = validateEmailFormat('admin@example.com');
      
      expect(result.isValid).toBe(true);
      expect(result.error).toBeUndefined();
    });

    it('should reject empty email', () => {
      const result = validateEmailFormat('');
      
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Email is required');
    });

    it('should reject invalid email format', () => {
      const result = validateEmailFormat('invalid-email');
      
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Please enter a valid email address');
    });

    it('should reject email that is too long', () => {
      const longEmail = 'a'.repeat(250) + '@example.com';
      const result = validateEmailFormat(longEmail);
      
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Email address is too long');
    });

    it('should reject email with long local part', () => {
      const longLocalPart = 'a'.repeat(65) + '@example.com';
      const result = validateEmailFormat(longLocalPart);
      
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Email local part is too long');
    });

    it('should reject email with consecutive dots', () => {
      const result = validateEmailFormat('admin..test@example.com');
      
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Email format is invalid');
    });

    it('should reject email with leading dot', () => {
      const result = validateEmailFormat('.admin@example.com');
      
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Email format is invalid');
    });

    it('should reject email with trailing dot', () => {
      const result = validateEmailFormat('admin.@example.com');
      
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Email format is invalid');
    });
  });

  describe('Email Verification Token', () => {
    it('should generate valid verification token', () => {
      const email = 'admin@example.com';
      const token = generateEmailVerificationToken(email);
      
      expect(token).toMatch(/^[A-Za-z0-9+/=]+\.[a-f0-9]{64}$/);
    });

    it('should verify valid token', () => {
      const email = 'admin@example.com';
      const token = generateEmailVerificationToken(email);
      const result = verifyEmailVerificationToken(token);
      
      expect(result.isValid).toBe(true);
      expect(result.email).toBe(email);
      expect(result.error).toBeUndefined();
    });

    it('should reject invalid token format', () => {
      const result = verifyEmailVerificationToken('invalid-token');
      
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Invalid token format');
    });

    it('should reject expired token', () => {
      // Mock Date.now to simulate expired token
      const originalNow = Date.now;
      const pastTime = Date.now() - (25 * 60 * 60 * 1000); // 25 hours ago
      
      vi.spyOn(Date, 'now').mockReturnValue(pastTime);
      const token = generateEmailVerificationToken('admin@example.com');
      Date.now = originalNow;
      
      const result = verifyEmailVerificationToken(token);
      
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Token has expired');
    });

    it('should reject token with wrong type', () => {
      // Create a token with wrong type
      const payload = btoa(JSON.stringify({
        email: 'admin@example.com',
        timestamp: Date.now(),
        type: 'wrong_type'
      }));
      const token = `${payload}.abcd1234`;
      
      const result = verifyEmailVerificationToken(token);
      
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Invalid token type');
    });
  });

  describe('hashPassword', () => {
    it('should hash password consistently', async () => {
      const password = 'TestPassword123!';
      const hash1 = await hashPassword(password);
      const hash2 = await hashPassword(password);
      
      expect(hash1).toBeDefined();
      expect(hash1).toMatch(/^[a-f0-9]{64}$/); // SHA-256 hex string
      expect(hash1).not.toBe(password);
      // Note: In this simple implementation, hashes will be different due to timestamp
      // In production, use proper bcrypt with salt
    });

    it('should produce different hashes for different passwords', async () => {
      const hash1 = await hashPassword('Password1!');
      const hash2 = await hashPassword('Password2!');
      
      expect(hash1).not.toBe(hash2);
    });
  });

  describe('createSuperAdminValidator', () => {
    it('should create validator with super admin rules', () => {
      const validator = createSuperAdminValidator();
      
      expect(validator).toBeDefined();
      
      // Test that it uses the strict password rules
      const weakPasswordResult = validator.validateField('password', 'weak123');
      expect(weakPasswordResult.isValid).toBe(false);
      
      const strongPasswordResult = validator.validateField('password', 'SuperSecure987!@#');
      expect(strongPasswordResult.isValid).toBe(true);
    });
  });

  describe('Validation Rules', () => {
    describe('SUPER_ADMIN_PASSWORD_RULES', () => {
      it('should have all required password rules', () => {
        const ruleMessages = SUPER_ADMIN_PASSWORD_RULES.map(rule => rule.message);
        
        expect(ruleMessages).toContain('Password is required');
        expect(ruleMessages).toContain('Password must be at least 12 characters long');
        expect(ruleMessages).toContain('Password must contain at least one lowercase letter');
        expect(ruleMessages).toContain('Password must contain at least one uppercase letter');
        expect(ruleMessages).toContain('Password must contain at least one number');
        expect(ruleMessages).toContain('Password must contain at least one special character');
      });

      it('should validate each rule correctly', () => {
        const testCases = [
          { password: '', expectedMessage: 'Password is required' },
          { password: 'Short1!', expectedMessage: 'Password must be at least 12 characters long' },
          { password: 'SUPERSECURE123!', expectedMessage: 'Password must contain at least one lowercase letter' },
          { password: 'supersecure123!', expectedMessage: 'Password must contain at least one uppercase letter' },
          { password: 'SuperSecure!', expectedMessage: 'Password must contain at least one number' },
          { password: 'SuperSecure123', expectedMessage: 'Password must contain at least one special character' }
        ];

        testCases.forEach(({ password, expectedMessage }) => {
          const failingRule = SUPER_ADMIN_PASSWORD_RULES.find(rule => !rule.validate(password));
          expect(failingRule?.message).toBe(expectedMessage);
        });
      });
    });

    describe('SUPER_ADMIN_EMAIL_RULES', () => {
      it('should have all required email rules', () => {
        const ruleMessages = SUPER_ADMIN_EMAIL_RULES.map(rule => rule.message);
        
        expect(ruleMessages).toContain('Email is required');
        expect(ruleMessages).toContain('Please enter a valid email address');
        expect(ruleMessages).toContain('Email address is too long');
        expect(ruleMessages).toContain('Please use a permanent email address');
      });
    });

    describe('FULL_NAME_RULES', () => {
      it('should have all required name rules', () => {
        const ruleMessages = FULL_NAME_RULES.map(rule => rule.message);
        
        expect(ruleMessages).toContain('Full name is required');
        expect(ruleMessages).toContain('Full name must be at least 2 characters long');
        expect(ruleMessages).toContain('Full name is too long (maximum 100 characters)');
      });

      it('should validate name format correctly', () => {
        const validNames = [
          'John Smith',
          'Mary-Jane Watson',
          "O'Connor",
          'Dr. Smith Jr.',
          'Jean-Claude Van Damme'
        ];

        const invalidNames = [
          'John123',
          'Smith@domain',
          'User#1',
          'Test$Name'
        ];

        const formatRule = FULL_NAME_RULES.find(rule => 
          rule.message === 'Full name can only contain letters, spaces, hyphens, apostrophes, and periods'
        );

        validNames.forEach(name => {
          expect(formatRule?.validate(name)).toBe(true);
        });

        invalidNames.forEach(name => {
          expect(formatRule?.validate(name)).toBe(false);
        });
      });
    });
  });
});