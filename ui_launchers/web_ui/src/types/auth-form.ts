import type { LoginCredentials, ValidationErrors, AuthenticationState, FeedbackMessage, ValidationRule, ValidationConfig } from './auth';

/**
 * Types and interfaces for authentication form management
 */

/**
 * Form field types
 */
export type FormFieldType = 'email' | 'password' | 'totp_code';

/**
 * Form field state
 */
export interface FormFieldState {
    value: string;
    error: string | null;
    touched: boolean;
    focused: boolean;
    validating: boolean;
}

/**
 * Complete form state
 */
export interface AuthFormState {
    fields: Record<FormFieldType, FormFieldState>;
    isSubmitting: boolean;
    isValid: boolean;
    submitAttempted: boolean;
    lastSubmitTime?: Date;
}

/**
 * Form field props for input components
 */
export interface FormFieldProps {
    name: FormFieldType;
    type: 'email' | 'password' | 'text';
    label: string;
    placeholder?: string;
    value: string;
    error?: string;
    touched?: boolean;
    disabled?: boolean;
    required?: boolean;
    autoComplete?: string;
    onChange: (value: string) => void;
    onBlur?: () => void;
    onFocus?: () => void;
    className?: string;
}

/**
 * Form validation context
 */
export interface FormValidationContext {
    config: ValidationConfig;
    validateOnChange: boolean;
    validateOnBlur: boolean;
    debounceDelay: number;
}

/**
 * Form submission state
 */
export interface FormSubmissionState {
    isSubmitting: boolean;
    canSubmit: boolean;
    submitCount: number;
    lastSubmitTime?: Date;
    cooldownPeriod?: number;
}

/**
 * Enhanced login form state with comprehensive tracking
 */
export interface EnhancedLoginFormState {
    credentials: LoginCredentials;
    formState: AuthFormState;
    validationErrors: ValidationErrors;
    authenticationState: AuthenticationState;
    feedbackMessage: FeedbackMessage | null;
    submissionState: FormSubmissionState;
    showTwoFactor: boolean;
    rememberEmail: boolean;
}

/**
 * Form actions for state management
 */
export type FormAction =
    | { type: 'SET_FIELD_VALUE'; field: FormFieldType; value: string }
    | { type: 'SET_FIELD_ERROR'; field: FormFieldType; error: string | null }
    | { type: 'SET_FIELD_TOUCHED'; field: FormFieldType; touched: boolean }
    | { type: 'SET_FIELD_FOCUSED'; field: FormFieldType; focused: boolean }
    | { type: 'SET_FIELD_VALIDATING'; field: FormFieldType; validating: boolean }
    | { type: 'SET_SUBMITTING'; submitting: boolean }
    | { type: 'SET_VALIDATION_ERRORS'; errors: ValidationErrors }
    | { type: 'CLEAR_ERRORS' }
    | { type: 'RESET_FORM' }
    | { type: 'SET_SUBMIT_ATTEMPTED'; attempted: boolean }
    | { type: 'INCREMENT_SUBMIT_COUNT' }
    | { type: 'SET_SHOW_TWO_FACTOR'; show: boolean }
    | { type: 'SET_REMEMBER_EMAIL'; remember: boolean };

/**
 * Form validation result
 */
export interface FormValidationResult {
    isValid: boolean;
    errors: ValidationErrors;
    firstErrorField?: FormFieldType;
}

/**
 * Form field configuration
 */
export interface FormFieldConfig {
    type: 'email' | 'password' | 'text';
    label: string;
    placeholder?: string;
    required: boolean;
    autoComplete?: string;
    validationRules: ValidationRule[];
    validateOnChange?: boolean;
    validateOnBlur?: boolean;
    debounceDelay?: number;
}

/**
 * Complete form configuration
 */
export interface AuthFormConfig {
    fields: Record<FormFieldType, FormFieldConfig>;
    submitCooldown: number;
    maxSubmitAttempts: number;
    enableRememberEmail: boolean;
    enableRealTimeValidation: boolean;
}

/**
 * Default form field configurations
 */
export const DEFAULT_FORM_FIELDS: Record<FormFieldType, FormFieldConfig> = {
    email: {
        type: 'email',
        label: 'Email Address',
        placeholder: 'Enter your email',
        required: true,
        autoComplete: 'email',
        validationRules: [
            { validate: (v) => v.trim().length > 0, message: 'Email is required' },
            { validate: (v) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v), message: 'Invalid email format' }
        ],
        validateOnChange: true,
        validateOnBlur: true,
        debounceDelay: 300
    },
    password: {
        type: 'password',
        label: 'Password',
        placeholder: 'Enter your password',
        required: true,
        autoComplete: 'current-password',
        validationRules: [
            { validate: (v) => v.length > 0, message: 'Password is required' },
            { validate: (v) => v.length >= 8, message: 'Password must be at least 8 characters' }
        ],
        validateOnChange: false,
        validateOnBlur: true,
        debounceDelay: 500
    },
    totp_code: {
        type: 'text',
        label: '2FA Code',
        placeholder: 'Enter 6-digit code',
        required: false,
        autoComplete: 'one-time-code',
        validationRules: [
            { validate: (v) => /^\d{6}$/.test(v.trim()), message: '2FA code must be 6 digits' }
        ],
        validateOnChange: true,
        validateOnBlur: true,
        debounceDelay: 200
    }
};

/**
 * Default form configuration
 */
export const DEFAULT_AUTH_FORM_CONFIG: AuthFormConfig = {
    fields: DEFAULT_FORM_FIELDS,
    submitCooldown: 1000, // 1 second between submissions
    maxSubmitAttempts: 5,
    enableRememberEmail: true,
    enableRealTimeValidation: true
};

/**
 * Initial form field state
 */
export const createInitialFieldState = (): FormFieldState => ({
    value: '',
    error: null,
    touched: false,
    focused: false,
    validating: false

/**
 * Initial form state
 */
export const createInitialFormState = (): AuthFormState => ({
    fields: {
        email: createInitialFieldState(),
        password: createInitialFieldState(),
        totp_code: createInitialFieldState()
    },
    isSubmitting: false,
    isValid: false,
    submitAttempted: false

/**
 * Initial submission state
 */
export const createInitialSubmissionState = (): FormSubmissionState => ({
    isSubmitting: false,
    canSubmit: true,
    submitCount: 0,
    cooldownPeriod: 1000

/**
 * Form reducer for state management
 */
export function formReducer(state: AuthFormState, action: FormAction): AuthFormState {
    switch (action.type) {
        case 'SET_FIELD_VALUE':
            return {
                ...state,
                fields: {
                    ...state.fields,
                    [action.field]: {
                        ...state.fields[action.field],
                        value: action.value,
                        error: null // Clear error when user types
                    }
                }
            };

        case 'SET_FIELD_ERROR':
            return {
                ...state,
                fields: {
                    ...state.fields,
                    [action.field]: {
                        ...state.fields[action.field],
                        error: action.error
                    }
                }
            };

        case 'SET_FIELD_TOUCHED':
            return {
                ...state,
                fields: {
                    ...state.fields,
                    [action.field]: {
                        ...state.fields[action.field],
                        touched: action.touched
                    }
                }
            };

        case 'SET_FIELD_FOCUSED':
            return {
                ...state,
                fields: {
                    ...state.fields,
                    [action.field]: {
                        ...state.fields[action.field],
                        focused: action.focused
                    }
                }
            };

        case 'SET_FIELD_VALIDATING':
            return {
                ...state,
                fields: {
                    ...state.fields,
                    [action.field]: {
                        ...state.fields[action.field],
                        validating: action.validating
                    }
                }
            };

        case 'SET_SUBMITTING':
            return {
                ...state,
                isSubmitting: action.submitting
            };

        case 'SET_VALIDATION_ERRORS':
            const updatedFields = { ...state.fields };

            // Clear all errors first
            Object.keys(updatedFields).forEach(field => {
                updatedFields[field as FormFieldType].error = null;

            // Set new errors
            Object.entries(action.errors).forEach(([field, error]) => {
                if (updatedFields[field as FormFieldType]) {
                    updatedFields[field as FormFieldType].error = error || null;
                }

            return {
                ...state,
                fields: updatedFields,
                isValid: Object.keys(action.errors).length === 0
            };

        case 'CLEAR_ERRORS':
            const clearedFields = { ...state.fields };
            Object.keys(clearedFields).forEach(field => {
                clearedFields[field as FormFieldType].error = null;

            return {
                ...state,
                fields: clearedFields,
                isValid: true
            };

        case 'RESET_FORM':
            return createInitialFormState();

        case 'SET_SUBMIT_ATTEMPTED':
            return {
                ...state,
                submitAttempted: action.attempted
            };

        default:
            return state;
    }
}

/**
 * Form validation utilities
 */
export class FormValidator {
    private config: AuthFormConfig;

    constructor(config: AuthFormConfig = DEFAULT_AUTH_FORM_CONFIG) {
        this.config = config;
    }

    validateField(field: FormFieldType, value: string): string | null {
        const fieldConfig = this.config.fields[field];

        for (const rule of fieldConfig.validationRules) {
            if (!rule.validate(value)) {
                return rule.message;
            }
        }

        return null;
    }

    validateForm(credentials: LoginCredentials, requireTwoFactor: boolean = false): FormValidationResult {
        const errors: ValidationErrors = {};

        // Validate email
        const emailError = this.validateField('email', credentials.email);
        if (emailError) errors.email = emailError;

        // Validate password
        const passwordError = this.validateField('password', credentials.password);
        if (passwordError) errors.password = passwordError;

        // Validate TOTP if required or provided
        if (requireTwoFactor || credentials.totp_code) {
            const totpError = this.validateField('totp_code', credentials.totp_code || '');
            if (totpError) errors.totp_code = totpError;
        }

        const isValid = Object.keys(errors).length === 0;
        const firstErrorField = Object.keys(errors)[0] as FormFieldType | undefined;

        return {
            isValid,
            errors,
            firstErrorField
        };
    }

    canSubmit(submissionState: FormSubmissionState): boolean {
        if (submissionState.isSubmitting) return false;
        if (!submissionState.canSubmit) return false;

        // Check cooldown period
        if (submissionState.lastSubmitTime && submissionState.cooldownPeriod) {
            const timeSinceLastSubmit = Date.now() - submissionState.lastSubmitTime.getTime();
            if (timeSinceLastSubmit < submissionState.cooldownPeriod) return false;
        }

        return true;
    }
}

/**
 * Form field focus management
 */
export interface FormFocusManager {
    focusField: (field: FormFieldType) => void;
    focusFirstError: (errors: ValidationErrors) => void;
    focusNextField: (currentField: FormFieldType) => void;
    focusPreviousField: (currentField: FormFieldType) => void;
}

/**
 * Form accessibility helpers
 */
export interface FormAccessibilityHelpers {
    getFieldAriaLabel: (field: FormFieldType) => string;
    getFieldAriaDescribedBy: (field: FormFieldType, hasError: boolean) => string;
    getFieldAriaInvalid: (hasError: boolean) => boolean;
    announceError: (error: string) => void;
    announceSuccess: (message: string) => void;
}