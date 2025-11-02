/**
 * React hook for form validation with real-time feedback
 * Provides debounced validation and error state management
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import type { ValidationErrors, LoginCredentials } from '@/types/auth';
import type { FormFieldType } from '@/types/auth-form';
import { FormValidator, createFormValidator, type FieldValidationResult, type FormValidationResult } from '@/lib/form-validator';

/**
 * Field validation state
 */
interface FieldValidationState {
  error: string | null;
  isValidating: boolean;
  touched: boolean;
  focused: boolean;
}

/**
 * Form validation state
 */
interface FormValidationState {
  fields: Record<FormFieldType, FieldValidationState>;
  isValid: boolean;
  hasErrors: boolean;
  isValidating: boolean;
}

/**
 * Form validation configuration
 */
interface UseFormValidationConfig {
  validateOnChange?: boolean;
  validateOnBlur?: boolean;
  debounceDelay?: number;
  enhanced?: boolean;
}

/**
 * Form validation hook return type
 */
interface UseFormValidationReturn {
  // State
  validationState: FormValidationState;
  errors: ValidationErrors;
  
  // Field operations
  validateField: (field: FormFieldType, value: string) => Promise<FieldValidationResult>;
  validateFieldSync: (field: FormFieldType, value: string) => FieldValidationResult;
  clearFieldError: (field: FormFieldType) => void;
  setFieldTouched: (field: FormFieldType, touched: boolean) => void;
  setFieldFocused: (field: FormFieldType, focused: boolean) => void;
  
  // Form operations
  validateForm: (credentials: LoginCredentials, requireTwoFactor?: boolean) => FormValidationResult;
  clearAllErrors: () => void;
  resetValidation: () => void;
  
  // Real-time validation handlers
  handleFieldChange: (field: FormFieldType, value: string) => void;
  handleFieldBlur: (field: FormFieldType, value: string) => void;
  handleFieldFocus: (field: FormFieldType) => void;
  
  // Utility
  getFieldError: (field: FormFieldType) => string | null;
  isFieldValid: (field: FormFieldType) => boolean;
  isFieldTouched: (field: FormFieldType) => boolean;
  shouldShowError: (field: FormFieldType) => boolean;
}

/**
 * Initial field validation state
 */
const createInitialFieldState = (): FieldValidationState => ({
  error: null,
  isValidating: false,
  touched: false,
  focused: false

/**
 * Initial form validation state
 */
const createInitialValidationState = (): FormValidationState => ({
  fields: {
    email: createInitialFieldState(),
    password: createInitialFieldState(),
    totp_code: createInitialFieldState()
  },
  isValid: false,
  hasErrors: false,
  isValidating: false

/**
 * Form validation hook with real-time feedback
 */
export function useFormValidation(config: UseFormValidationConfig = {}): UseFormValidationReturn {
  const {
    validateOnChange = true,
    validateOnBlur = true,
    debounceDelay = 300,
    enhanced = false
  } = config;

  // Create validator instance
  const validatorRef = useRef<FormValidator>(createFormValidator(enhanced));
  const validator = validatorRef.current;

  // Validation state
  const [validationState, setValidationState] = useState<FormValidationState>(
    createInitialValidationState()
  );

  // Cleanup debounce timers on unmount
  useEffect(() => {
    return () => {
      validator.clearDebounceTimers();
    };
  }, [validator]);

  // Update validation state helper
  const updateFieldState = useCallback((
    field: FormFieldType,
    updates: Partial<FieldValidationState>
  ) => {
    setValidationState(prev => {
      const newFields = {
        ...prev.fields,
        [field]: { ...prev.fields[field], ...updates }
      };

      const hasErrors = Object.values(newFields).some(fieldState => fieldState.error !== null);
      const isValidating = Object.values(newFields).some(fieldState => fieldState.isValidating);
      const isValid = !hasErrors && !isValidating;

      return {
        fields: newFields,
        hasErrors,
        isValidating,
        isValid
      };

  }, []);

  // Validate field synchronously
  const validateFieldSync = useCallback((field: FormFieldType, value: string): FieldValidationResult => {
    return validator.validateField(field, value);
  }, [validator]);

  // Validate field asynchronously with debouncing
  const validateField = useCallback((field: FormFieldType, value: string): Promise<FieldValidationResult> => {
    return new Promise((resolve) => {
      updateFieldState(field, { isValidating: true });

      const delay = validator.getDebounceDelay(field);
      
      validator.validateFieldDebounced(field, value, (result) => {
        updateFieldState(field, {
          error: result.error || null,
          isValidating: false

        resolve(result);
      }, delay);

  }, [validator, updateFieldState]);

  // Clear field error
  const clearFieldError = useCallback((field: FormFieldType) => {
    updateFieldState(field, { error: null });
  }, [updateFieldState]);

  // Set field touched state
  const setFieldTouched = useCallback((field: FormFieldType, touched: boolean) => {
    updateFieldState(field, { touched });
  }, [updateFieldState]);

  // Set field focused state
  const setFieldFocused = useCallback((field: FormFieldType, focused: boolean) => {
    updateFieldState(field, { focused });
  }, [updateFieldState]);

  // Validate entire form
  const validateForm = useCallback((
    credentials: LoginCredentials,
    requireTwoFactor: boolean = false
  ): FormValidationResult => {
    const result = validator.validateForm(credentials, requireTwoFactor);

    // Update all field states with validation results
    Object.entries(result.errors).forEach(([field, error]) => {
      updateFieldState(field as FormFieldType, { error, touched: true });

    // Clear errors for fields that are now valid
    const fieldTypes: FormFieldType[] = ['email', 'password', 'totp_code'];
    fieldTypes.forEach(field => {
      if (!result.errors[field] && validationState.fields[field].error) {
        updateFieldState(field, { error: null });
      }

    return result;
  }, [validator, updateFieldState, validationState.fields]);

  // Clear all errors
  const clearAllErrors = useCallback(() => {
    setValidationState(prev => ({
      ...prev,
      fields: Object.fromEntries(
        Object.entries(prev.fields).map(([field, state]) => [
          field,
          { ...state, error: null }
        ])
      ) as Record<FormFieldType, FieldValidationState>,
      hasErrors: false,
      isValid: true
    }));
  }, []);

  // Reset validation state
  const resetValidation = useCallback(() => {
    validator.clearDebounceTimers();
    setValidationState(createInitialValidationState());
  }, [validator]);

  // Handle field change with real-time validation
  const handleFieldChange = useCallback((field: FormFieldType, value: string) => {
    // Clear existing error immediately when user starts typing
    if (validationState.fields[field].error) {
      clearFieldError(field);
    }

    // Validate on change if enabled and field supports it
    if (validateOnChange && validator.shouldValidateOnChange(field)) {
      validateField(field, value);
    }
  }, [validateOnChange, validator, validationState.fields, clearFieldError, validateField]);

  // Handle field blur with validation
  const handleFieldBlur = useCallback((field: FormFieldType, value: string) => {
    setFieldTouched(field, true);
    setFieldFocused(field, false);

    // Validate on blur if enabled
    if (validateOnBlur && validator.shouldValidateOnBlur(field)) {
      validateField(field, value);
    }
  }, [validateOnBlur, validator, setFieldTouched, setFieldFocused, validateField]);

  // Handle field focus
  const handleFieldFocus = useCallback((field: FormFieldType) => {
    setFieldFocused(field, true);
  }, [setFieldFocused]);

  // Get field error
  const getFieldError = useCallback((field: FormFieldType): string | null => {
    return validationState.fields[field].error;
  }, [validationState.fields]);

  // Check if field is valid
  const isFieldValid = useCallback((field: FormFieldType): boolean => {
    return validationState.fields[field].error === null;
  }, [validationState.fields]);

  // Check if field is touched
  const isFieldTouched = useCallback((field: FormFieldType): boolean => {
    return validationState.fields[field].touched;
  }, [validationState.fields]);

  // Determine if error should be shown
  const shouldShowError = useCallback((field: FormFieldType): boolean => {
    const fieldState = validationState.fields[field];
    return fieldState.touched && fieldState.error !== null;
  }, [validationState.fields]);

  // Create errors object for compatibility
  const errors: ValidationErrors = {
    email: validationState.fields.email.error || undefined,
    password: validationState.fields.password.error || undefined,
    totp_code: validationState.fields.totp_code.error || undefined
  };

  return {
    // State
    validationState,
    errors,
    
    // Field operations
    validateField,
    validateFieldSync,
    clearFieldError,
    setFieldTouched,
    setFieldFocused,
    
    // Form operations
    validateForm,
    clearAllErrors,
    resetValidation,
    
    // Real-time validation handlers
    handleFieldChange,
    handleFieldBlur,
    handleFieldFocus,
    
    // Utility
    getFieldError,
    isFieldValid,
    isFieldTouched,
    shouldShowError
  };
}

/**
 * Hook for simple field validation without full form state
 */
export function useFieldValidation(field: FormFieldType, enhanced: boolean = false) {
  const validator = useRef(createFormValidator(enhanced)).current;
  const [state, setState] = useState<FieldValidationState>(createInitialFieldState());

  const validate = useCallback((value: string) => {
    const result = validator.validateField(field, value);
    setState(prev => ({
      ...prev,
      error: result.error || null,
      isValidating: false
    }));
    return result;
  }, [validator, field]);

  const validateDebounced = useCallback((value: string, callback?: (result: FieldValidationResult) => void) => {
    setState(prev => ({ ...prev, isValidating: true }));
    
    validator.validateFieldDebounced(field, value, (result) => {
      setState(prev => ({
        ...prev,
        error: result.error || null,
        isValidating: false
      }));
      callback?.(result);
    }, validator.getDebounceDelay(field));
  }, [validator, field]);

  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  const setTouched = useCallback((touched: boolean) => {
    setState(prev => ({ ...prev, touched }));
  }, []);

  useEffect(() => {
    return () => validator.clearDebounceTimers();
  }, [validator]);

  return {
    state,
    validate,
    validateDebounced,
    clearError,
    setTouched,
    isValid: state.error === null,
    shouldShowError: state.touched && state.error !== null
  };
}