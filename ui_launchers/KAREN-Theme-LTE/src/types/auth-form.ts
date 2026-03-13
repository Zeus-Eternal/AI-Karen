/**
 * Authentication Form Types
 * 
 * Type definitions for authentication forms and validation
 */

export type FormFieldType = 'email' | 'password' | 'totp_code' | 'username' | 'remember' | 'consent';

export interface LoginCredentials {
  email: string;
  password: string;
  totp_code?: string;
  remember?: boolean;
}

export interface RegisterCredentials {
  email: string;
  password: string;
  confirmPassword: string;
  username?: string;
  acceptTerms: boolean;
  acceptPrivacy: boolean;
}

export interface ResetPasswordCredentials {
  email: string;
  newPassword: string;
  confirmPassword: string;
  token: string;
}

export interface ChangePasswordCredentials {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

export interface TwoFactorSetupCredentials {
  secret: string;
  code: string;
}

export interface FormFieldConfig {
  type: FormFieldType;
  label: string;
  placeholder?: string;
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  pattern?: RegExp;
  customValidator?: (value: string) => string | null;
  autoComplete?: string;
  autoFocus?: boolean;
}

export interface FormValidationRule {
  field: FormFieldType;
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  pattern?: {
    regex: RegExp;
    message: string;
  };
  custom?: (value: string, allValues?: Record<string, string>) => string | null;
}

export interface FormConfig {
  fields: Record<FormFieldType, FormFieldConfig>;
  validationRules: FormValidationRule[];
  submitButtonText?: string;
  showPasswordToggle?: boolean;
  showRememberMe?: boolean;
  showTwoFactor?: boolean;
  requireTwoFactor?: boolean;
}