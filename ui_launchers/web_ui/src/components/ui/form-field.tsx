/**
 * Enhanced form field component with validation feedback
 * Integrates with the form validation system for real-time feedback
 */

import React, { forwardRef, useId } from 'react';
import { cn } from '@/lib/utils';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';
import type { FormFieldType } from '@/types/auth-form';

/**
 * Form field props extending standard input props
 */
export interface FormFieldProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'onChange' | 'onBlur' | 'onFocus'> {
  name: FormFieldType;
  label: string;
  error?: string | null;
  touched?: boolean;
  isValidating?: boolean;
  showValidIcon?: boolean;
  helperText?: string;
  required?: boolean;
  
  // Event handlers with field-specific signatures
  onChange?: (value: string) => void;
  onBlur?: () => void;
  onFocus?: () => void;
  
  // Styling
  className?: string;
  inputClassName?: string;
  labelClassName?: string;
  errorClassName?: string;
  helperClassName?: string;
}

/**
 * Enhanced form field component with validation feedback
 */
export const FormField = forwardRef<HTMLInputElement, FormFieldProps>(({
  name,
  label,
  error,
  touched = false,
  isValidating = false,
  showValidIcon = true,
  helperText,
  required = false,
  onChange,
  onBlur,
  onFocus,
  className,
  inputClassName,
  labelClassName,
  errorClassName,
  helperClassName,
  disabled,
  ...props
}, ref) => {
  const fieldId = useId();
  const errorId = `${fieldId}-error`;
  const helperId = `${fieldId}-helper`;
  
  // Determine field state
  const hasError = touched && error;
  const isValid = touched && !error && !isValidating;
  const showError = hasError;
  const showHelper = helperText && !showError;
  
  // Handle input change
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange?.(e.target.value);
  };
  
  // Handle input blur
  const handleBlur = () => {
    onBlur?.();
  };
  
  // Handle input focus
  const handleFocus = () => {
    onFocus?.();
  };
  
  // Get appropriate input type
  const getInputType = (): string => {
    switch (name) {
      case 'email':
        return 'email';
      case 'password':
        return 'password';
      case 'totp_code':
        return 'text';
      default:
        return props.type || 'text';
    }
  };
  
  // Get appropriate autocomplete value
  const getAutoComplete = (): string => {
    switch (name) {
      case 'email':
        return 'email';
      case 'password':
        return 'current-password';
      case 'totp_code':
        return 'one-time-code';
      default:
        return props.autoComplete || 'off';
    }
  };
  
  // Get appropriate input mode for mobile keyboards
  const getInputMode = (): React.HTMLAttributes<HTMLInputElement>['inputMode'] => {
    switch (name) {
      case 'email':
        return 'email';
      case 'totp_code':
        return 'numeric';
      default:
        return undefined;
    }
  };
  
  // Get appropriate pattern for validation
  const getPattern = (): string | undefined => {
    switch (name) {
      case 'totp_code':
        return '[0-9]{6}';
      default:
        return props.pattern;
    }
  };
  
  // Get appropriate maxLength
  const getMaxLength = (): number | undefined => {
    switch (name) {
      case 'totp_code':
        return 6;
      case 'email':
        return 254;
      case 'password':
        return 128;
      default:
        return props.maxLength;
    }
  };
  
  return (
    <div className={cn('space-y-2', className)}>
      {/* Label */}
      <Label
        htmlFor={fieldId}
        className={cn(
          'text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70',
          hasError && 'text-destructive',
          labelClassName
        )}
      >
        {label}
        {required && <span className="text-destructive ml-1" aria-label="required">*</span>}
      </Label>
      
      {/* Input with validation state */}
      <div className="relative">
        <Input
          ref={ref}
          id={fieldId}
          type={getInputType()}
          autoComplete={getAutoComplete()}
          inputMode={getInputMode()}
          pattern={getPattern()}
          maxLength={getMaxLength()}
          required={required}
          disabled={disabled || isValidating}
          onChange={handleChange}
          onBlur={handleBlur}
          onFocus={handleFocus}
          className={cn(
            'pr-10', // Space for validation icon
            hasError && 'border-destructive focus-visible:ring-destructive',
            isValid && 'border-green-500 focus-visible:ring-green-500',
            inputClassName
          )}
          aria-invalid={hasError ? true : false}
          aria-describedby={cn(
            showError && errorId,
            showHelper && helperId
          )}
          {...props}
        />
        
        {/* Validation icon */}
        <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
          {isValidating && (
            <Loader2 
              className="h-4 w-4 animate-spin text-muted-foreground" 
              aria-label="Validating"
            />
          )}
          {hasError && (
            <AlertCircle 
              className="h-4 w-4 text-destructive" 
              aria-label="Error"
            />
          )}
          {isValid && showValidIcon && (
            <CheckCircle2 
              className="h-4 w-4 text-green-500" 
              aria-label="Valid"
            />
          )}
        </div>
      </div>
      
      {/* Error message */}
      {showError && (
        <p
          id={errorId}
          className={cn(
            'text-sm text-destructive flex items-center gap-1',
            errorClassName
          )}
          role="alert"
          aria-live="polite"
        >
          <AlertCircle className="h-3 w-3 flex-shrink-0" />
          {error}
        </p>
      )}
      
      {/* Helper text */}
      {showHelper && (
        <p
          id={helperId}
          className={cn(
            'text-sm text-muted-foreground',
            helperClassName
          )}
        >
          {helperText}
        </p>
      )}
    </div>
  );
});

FormField.displayName = 'FormField';

/**
 * Form field with validation hook integration
 */
export interface ValidatedFormFieldProps extends Omit<FormFieldProps, 'error' | 'touched' | 'isValidating' | 'onChange' | 'onBlur' | 'onFocus'> {
  value: string;
  onValueChange: (value: string) => void;
  onValidationChange?: (field: FormFieldType, value: string) => void;
  onBlurValidation?: (field: FormFieldType, value: string) => void;
  onFocusChange?: (field: FormFieldType) => void;
  
  // Validation state from hook
  error?: string | null | undefined;
  touched?: boolean;
  isValidating?: boolean;
}

/**
 * Form field component that integrates with validation hooks
 */
export const ValidatedFormField = forwardRef<HTMLInputElement, ValidatedFormFieldProps>(({
  name,
  value,
  onValueChange,
  onValidationChange,
  onBlurValidation,
  onFocusChange,
  error,
  touched,
  isValidating,
  ...props
}, ref) => {
  const handleChange = (newValue: string) => {
    onValueChange(newValue);
    onValidationChange?.(name, newValue);
  };
  
  const handleBlur = () => {
    onBlurValidation?.(name, value);
  };
  
  const handleFocus = () => {
    onFocusChange?.(name);
  };
  
  return (
    <FormField
      ref={ref}
      name={name}
      value={value}
      error={error}
      touched={touched}
      isValidating={isValidating}
      onChange={handleChange}
      onBlur={handleBlur}
      onFocus={handleFocus}
      {...props}
    />
  );
});

ValidatedFormField.displayName = 'ValidatedFormField';

/**
 * Password strength indicator component
 */
interface PasswordStrengthProps {
  password: string;
  show?: boolean;
  className?: string;
}

export const PasswordStrength: React.FC<PasswordStrengthProps> = ({
  password,
  show = true,
  className
}) => {
  if (!show || !password) return null;
  
  // Calculate password strength
  const getStrength = (pwd: string): { level: number; label: string; color: string } => {
    if (pwd.length < 8) return { level: 0, label: 'Too short', color: 'text-destructive' };
    
    let score = 0;
    if (pwd.length >= 12) score += 2;
    else if (pwd.length >= 10) score += 1;
    
    if (/[a-z]/.test(pwd)) score += 1;
    if (/[A-Z]/.test(pwd)) score += 1;
    if (/\d/.test(pwd)) score += 1;
    if (/[^a-zA-Z\d]/.test(pwd)) score += 2;
    
    if (score >= 6) return { level: 3, label: 'Strong', color: 'text-green-600' };
    if (score >= 4) return { level: 2, label: 'Medium', color: 'text-yellow-600' };
    if (score >= 2) return { level: 1, label: 'Weak', color: 'text-orange-600' };
    return { level: 0, label: 'Very weak', color: 'text-destructive' };
  };
  
  const strength = getStrength(password);
  
  return (
    <div className={cn('space-y-1', className)}>
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground">Password strength</span>
        <span className={cn('text-xs font-medium', strength.color)}>
          {strength.label}
        </span>
      </div>
      <div className="flex space-x-1">
        {[0, 1, 2, 3].map((level) => (
          <div
            key={level}
            className={cn(
              'h-1 flex-1 rounded-full',
              level <= strength.level
                ? strength.level === 0
                  ? 'bg-destructive'
                  : strength.level === 1
                  ? 'bg-orange-500'
                  : strength.level === 2
                  ? 'bg-yellow-500'
                  : 'bg-green-500'
                : 'bg-muted'
            )}
          />
        ))}
      </div>
    </div>
  );
};

export default FormField;