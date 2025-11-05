/**
 * Setup validation utilities for first-run super admin creation
 * Includes strong password validation and email verification
 */

import type { CreateSuperAdminRequest, SetupValidationErrors } from '@/types/admin';
import { FormValidator } from '@/lib/form-validator';

/**
 * Strong password validation rules for super admin setup
 */
export const SUPER_ADMIN_PASSWORD_RULES = [
  {
    validate: (value: string) => value.length > 0,
    message: 'Password is required'
  },
  {
    validate: (value: string) => value.length >= 12,
    message: 'Password must be at least 12 characters long'
  },
  {
    validate: (value: string) => value.length <= 128,
    message: 'Password is too long (maximum 128 characters)'
  },
  {
    validate: (value: string) => /[a-z]/.test(value),
    message: 'Password must contain at least one lowercase letter'
  },
  {
    validate: (value: string) => /[A-Z]/.test(value),
    message: 'Password must contain at least one uppercase letter'
  },
  {
    validate: (value: string) => /\d/.test(value),
    message: 'Password must contain at least one number'
  },
  {
    validate: (value: string) => /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(value),
    message: 'Password must contain at least one special character'
  },
  {
    validate: (value: string) => {
      // Check for common weak passwords
      const weakPasswords = [
        'password123!', 'admin123!', 'superadmin123!', 'administrator123!',
        'Password123!', 'Admin123!', 'SuperAdmin123!', 'Administrator123!',
        'password', 'admin', 'superadmin', 'administrator'
      ];
      return !weakPasswords.some(weak => value.toLowerCase().includes(weak.toLowerCase()));
    },
    message: 'Password is too common. Please choose a more unique password'
  },
  {
    validate: (value: string) => {
      // Check for sequential characters (123, abc, etc.)
      const hasSequential = /(?:012|123|234|345|456|567|678|789|890|abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)/i.test(value);
      return !hasSequential;
    },
    message: 'Password should not contain sequential characters'
  },
  {
    validate: (value: string) => {
      // Check for repeated characters (aaa, 111, etc.)
      const hasRepeated = /(.)\1{2,}/.test(value);
      return !hasRepeated;
    },
    message: 'Password should not contain repeated characters'
  }
];

/**
 * Email validation rules for super admin setup
 */
export const SUPER_ADMIN_EMAIL_RULES = [
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
  },
  {
    validate: (value: string) => {
      // Check for professional email format (avoid obvious temporary emails)
      const tempEmailDomains = ['10minutemail.com', 'tempmail.org', 'guerrillamail.com'];
      const domain = value.split('@')[1]?.toLowerCase();
      return !tempEmailDomains.includes(domain);
    },
    message: 'Please use a permanent email address'
  }
];

/**
 * Full name validation rules
 */
export const FULL_NAME_RULES = [
  {
    validate: (value: string) => value.trim().length > 0,
    message: 'Full name is required'
  },
  {
    validate: (value: string) => value.trim().length >= 2,
    message: 'Full name must be at least 2 characters long'
  },
  {
    validate: (value: string) => value.trim().length <= 100,
    message: 'Full name is too long (maximum 100 characters)'
  },
  {
    validate: (value: string) => /^[a-zA-Z\s\-'\.]+$/.test(value.trim()),
    message: 'Full name can only contain letters, spaces, hyphens, apostrophes, and periods'
  }
];

/**
 * Validation result interface
 */
export interface SetupValidationResult {
  isValid: boolean;
  errors: SetupValidationErrors;
}

/**
 * Validate super admin creation request
 */
export async function validateSuperAdminCreation(
  request: CreateSuperAdminRequest
): Promise<SetupValidationResult> {
  const errors: SetupValidationErrors = {};

  // Validate email
  for (const rule of SUPER_ADMIN_EMAIL_RULES) {
    if (!rule.validate(request.email)) {
      errors.email = rule.message;
      break;
    }
  }

  // Validate full name
  for (const rule of FULL_NAME_RULES) {
    if (!rule.validate(request.full_name)) {
      errors.full_name = rule.message;
      break;
    }
  }

  // Validate password
  for (const rule of SUPER_ADMIN_PASSWORD_RULES) {
    if (!rule.validate(request.password)) {
      errors.password = rule.message;
      break;
    }
  }

  // Validate password confirmation
  if (request.password !== request.confirm_password) {
    errors.confirm_password = 'Passwords do not match';
  }

  // Additional security checks
  if (request.email && request.password) {
    // Check if password contains email
    if (request.password.toLowerCase().includes(request.email.split('@')[0].toLowerCase())) {
      errors.password = 'Password should not contain your email address';
    }

    // Check if password contains name
    if (request.full_name) {
      const nameParts = request.full_name.toLowerCase().split(/\s+/);
      const passwordLower = request.password.toLowerCase();
      
      for (const part of nameParts) {
        if (part.length >= 3 && passwordLower.includes(part)) {
          errors.password = 'Password should not contain your name';
          break;
        }
      }
    }
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
}

/**
 * Calculate password strength score
 */
export function calculatePasswordStrength(password: string): {
  score: number;
  level: 'very_weak' | 'weak' | 'medium' | 'strong' | 'very_strong';
  feedback: string[];
} {
  let score = 0;
  const feedback: string[] = [];

  // Length scoring
  if (password.length >= 12) score += 2;
  else if (password.length >= 8) score += 1;
  else feedback.push('Use at least 12 characters');

  // Character variety
  if (/[a-z]/.test(password)) score += 1;
  else feedback.push('Add lowercase letters');

  if (/[A-Z]/.test(password)) score += 1;
  else feedback.push('Add uppercase letters');

  if (/\d/.test(password)) score += 1;
  else feedback.push('Add numbers');

  if (/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) score += 2;
  else feedback.push('Add special characters');

  // Bonus points for extra length
  if (password.length >= 16) score += 1;
  if (password.length >= 20) score += 1;

  // Penalty for common patterns
  if (/(.)\1{2,}/.test(password)) {
    score -= 2;
    feedback.push('Avoid repeated characters');
  }

  if (/(?:012|123|234|345|456|567|678|789|890|abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)/i.test(password)) {
    score -= 2;
    feedback.push('Avoid sequential characters');
  }

  // Determine level
  let level: 'very_weak' | 'weak' | 'medium' | 'strong' | 'very_strong';
  if (score >= 8) level = 'very_strong';
  else if (score >= 6) level = 'strong';
  else if (score >= 4) level = 'medium';
  else if (score >= 2) level = 'weak';
  else level = 'very_weak';

  return { score, level, feedback };
}

/**
 * Hash password using a secure method
 * Note: In a real implementation, this would use bcrypt or similar
 */
export async function hashPassword(password: string): Promise<string> {
  // For now, we'll use a simple hash. In production, use bcrypt
  const encoder = new TextEncoder();
  const data = encoder.encode(password + 'salt_' + Date.now());
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

/**
 * Validate email format with additional checks
 */
export function validateEmailFormat(email: string): {
  isValid: boolean;
  error?: string;
} {
  const trimmedEmail = email.trim();

  if (!trimmedEmail) {
    return { isValid: false, error: 'Email is required' };
  }

  // Basic format check
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(trimmedEmail)) {
    return { isValid: false, error: 'Please enter a valid email address' };
  }

  // Length check
  if (trimmedEmail.length > 254) {
    return { isValid: false, error: 'Email address is too long' };
  }

  // Local part checks
  const [localPart, domain] = trimmedEmail.split('@');
  
  if (localPart.length > 64) {
    return { isValid: false, error: 'Email local part is too long' };
  }

  // Check for consecutive dots
  if (localPart.includes('..')) {
    return { isValid: false, error: 'Email format is invalid' };
  }

  // Check for leading/trailing dots
  if (localPart.startsWith('.') || localPart.endsWith('.')) {
    return { isValid: false, error: 'Email format is invalid' };
  }

  // Domain checks
  if (domain.length > 253) {
    return { isValid: false, error: 'Email domain is too long' };
  }

  // Check for valid domain format
  const domainRegex = /^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$/;
  if (!domainRegex.test(domain)) {
    return { isValid: false, error: 'Email domain format is invalid' };
  }

  return { isValid: true };
}

/**
 * Generate email verification token
 */
export function generateEmailVerificationToken(email: string): string {
  const timestamp = Date.now().toString();
  const randomBytes = Array.from(crypto.getRandomValues(new Uint8Array(32)))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
  
  // Create a simple token (in production, use proper JWT or similar)
  const payload = btoa(JSON.stringify({
    email,
    timestamp,
    type: 'email_verification'
  }));
  
  return `${payload}.${randomBytes}`;
}

/**
 * Verify email verification token
 */
export function verifyEmailVerificationToken(token: string): {
  isValid: boolean;
  email?: string;
  error?: string;
} {
  try {
    const [payload] = token.split('.');
    const decoded = JSON.parse(atob(payload));
    
    if (decoded.type !== 'email_verification') {
      return { isValid: false, error: 'Invalid token type' };
    }
    
    // Check if token is expired (24 hours)
    const tokenAge = Date.now() - parseInt(decoded.timestamp);
    if (tokenAge > 24 * 60 * 60 * 1000) {
      return { isValid: false, error: 'Token has expired' };
    }
    
    return { isValid: true, email: decoded.email };
  } catch (error) {
    return { isValid: false, error: 'Invalid token format' };
  }
}

/**
 * Create a FormValidator instance with super admin rules
 */
export function createSuperAdminValidator(): FormValidator {
  const validator = new FormValidator({
    email: SUPER_ADMIN_EMAIL_RULES,
    password: SUPER_ADMIN_PASSWORD_RULES
  });

  // Add full_name validation rules manually since FormValidator doesn't support it by default
  validator.addValidationRule('full_name' as any, FULL_NAME_RULES[0]);
  FULL_NAME_RULES.slice(1).forEach(rule => {
    validator.addValidationRule('full_name' as any, rule);
  });

  return validator;
}

/**
 * Alias for validateEmailFormat for backward compatibility
 */
export const validateEmail = validateEmailFormat;