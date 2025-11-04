"use client";
import type {
  LoginCredentials,
  ValidationErrors,
  AuthenticationState,
  FeedbackMessage,
  ValidationRule,
  ValidationConfig,
} from "./auth";

/**
 * Authentication Form Types, Defaults, Reducers & Utilities (production‑grade)
 * - Complete, compile‑safe module with zero placeholder code
 * - Split reducers for form fields and submission lifecycle
 * - Helpers for validation, accessibility, and focus management
 */

// ---------------------------------------------------------------------------
// Field & Form Types
// ---------------------------------------------------------------------------
export type FormFieldType = "email" | "password" | "totp_code";

export interface FormFieldState {
  value: string;
  error: string | null;
  touched: boolean;
  focused: boolean;
  validating: boolean;
}

export interface AuthFormState {
  fields: Record<FormFieldType, FormFieldState>;
  isSubmitting: boolean;
  isValid: boolean;
  submitAttempted: boolean;
  lastSubmitTime?: Date;
}

export interface FormFieldProps {
  name: FormFieldType;
  type: "email" | "password" | "text";
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

export interface FormValidationContext {
  config: ValidationConfig;
  validateOnChange: boolean;
  validateOnBlur: boolean;
  debounceDelay: number;
}

export interface FormSubmissionState {
  isSubmitting: boolean;
  canSubmit: boolean;
  submitCount: number;
  lastSubmitTime?: Date;
  cooldownPeriod?: number; // ms
}

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

// ---------------------------------------------------------------------------
// Actions
// ---------------------------------------------------------------------------
export type FormAction =
  | { type: "SET_FIELD_VALUE"; field: FormFieldType; value: string }
  | { type: "SET_FIELD_ERROR"; field: FormFieldType; error: string | null }
  | { type: "SET_FIELD_TOUCHED"; field: FormFieldType; touched: boolean }
  | { type: "SET_FIELD_FOCUSED"; field: FormFieldType; focused: boolean }
  | { type: "SET_FIELD_VALIDATING"; field: FormFieldType; validating: boolean }
  | { type: "SET_SUBMITTING"; submitting: boolean }
  | { type: "SET_VALIDATION_ERRORS"; errors: ValidationErrors }
  | { type: "CLEAR_ERRORS" }
  | { type: "RESET_FORM" }
  | { type: "SET_SUBMIT_ATTEMPTED"; attempted: boolean };

export type SubmissionAction =
  | { type: "SET_SUBMITTING"; submitting: boolean }
  | { type: "INCREMENT_SUBMIT_COUNT" }
  | { type: "SET_LAST_SUBMIT_TIME"; when: Date }
  | { type: "SET_CAN_SUBMIT"; canSubmit: boolean }
  | { type: "SET_COOLDOWN"; cooldownMs: number };

// ---------------------------------------------------------------------------
// Validation & Config
// ---------------------------------------------------------------------------
export interface FormFieldConfig {
  type: "email" | "password" | "text";
  label: string;
  placeholder?: string;
  required: boolean;
  autoComplete?: string;
  validationRules: ValidationRule[];
  validateOnChange?: boolean;
  validateOnBlur?: boolean;
  debounceDelay?: number; // ms
}

export interface AuthFormConfig {
  fields: Record<FormFieldType, FormFieldConfig>;
  submitCooldown: number; // ms
  maxSubmitAttempts: number;
  enableRememberEmail: boolean;
  enableRealTimeValidation: boolean;
}

export const DEFAULT_FORM_FIELDS: Record<FormFieldType, FormFieldConfig> = {
  email: {
    type: "email",
    label: "Email Address",
    placeholder: "Enter your email",
    required: true,
    autoComplete: "email",
    validationRules: [
      { validate: (v) => v.trim().length > 0, message: "Email is required" },
      { validate: (v) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v), message: "Invalid email format" },
    ],
    validateOnChange: true,
    validateOnBlur: true,
    debounceDelay: 300,
  },
  password: {
    type: "password",
    label: "Password",
    placeholder: "Enter your password",
    required: true,
    autoComplete: "current-password",
    validationRules: [
      { validate: (v) => v.length > 0, message: "Password is required" },
      { validate: (v) => v.length >= 8, message: "Password must be at least 8 characters" },
    ],
    validateOnChange: false,
    validateOnBlur: true,
    debounceDelay: 500,
  },
  totp_code: {
    type: "text",
    label: "2FA Code",
    placeholder: "Enter 6-digit code",
    required: false,
    autoComplete: "one-time-code",
    validationRules: [
      { validate: (v) => v.trim() === "" || /^\d{6}$/.test(v.trim()), message: "2FA code must be 6 digits" },
    ],
    validateOnChange: true,
    validateOnBlur: true,
    debounceDelay: 200,
  },
};

export const DEFAULT_AUTH_FORM_CONFIG: AuthFormConfig = {
  fields: DEFAULT_FORM_FIELDS,
  submitCooldown: 1_000,
  maxSubmitAttempts: 5,
  enableRememberEmail: true,
  enableRealTimeValidation: true,
};

// ---------------------------------------------------------------------------
// Initial State Factories
// ---------------------------------------------------------------------------
export const createInitialFieldState = (): FormFieldState => ({
  value: "",
  error: null,
  touched: false,
  focused: false,
  validating: false,
});

export const createInitialFormState = (): AuthFormState => ({
  fields: {
    email: createInitialFieldState(),
    password: createInitialFieldState(),
    totp_code: createInitialFieldState(),
  },
  isSubmitting: false,
  isValid: false,
  submitAttempted: false,
});

export const createInitialSubmissionState = (
  cooldownMs: number = DEFAULT_AUTH_FORM_CONFIG.submitCooldown
): FormSubmissionState => ({
  isSubmitting: false,
  canSubmit: true,
  submitCount: 0,
  cooldownPeriod: cooldownMs,
});

// ---------------------------------------------------------------------------
// Reducers
// ---------------------------------------------------------------------------
export function formReducer(state: AuthFormState, action: FormAction): AuthFormState {
  switch (action.type) {
    case "SET_FIELD_VALUE": {
      const next = {
        ...state,
        fields: {
          ...state.fields,
          [action.field]: { ...state.fields[action.field], value: action.value, error: null },
        },
      };
      // optimistic validity: valid if no field has error and required fields non-empty
      const anyError = Object.values(next.fields).some((f) => !!f.error);
      const requiredFilled = next.fields.email.value.trim() !== "" && next.fields.password.value !== "";
      return { ...next, isValid: !anyError && requiredFilled };
    }
    case "SET_FIELD_ERROR": {
      const fields = {
        ...state.fields,
        [action.field]: { ...state.fields[action.field], error: action.error },
      };
      const anyError = Object.values(fields).some((f) => !!f.error);
      return { ...state, fields, isValid: !anyError };
    }
    case "SET_FIELD_TOUCHED":
      return {
        ...state,
        fields: { ...state.fields, [action.field]: { ...state.fields[action.field], touched: action.touched } },
      };
    case "SET_FIELD_FOCUSED":
      return {
        ...state,
        fields: { ...state.fields, [action.field]: { ...state.fields[action.field], focused: action.focused } },
      };
    case "SET_FIELD_VALIDATING":
      return {
        ...state,
        fields: { ...state.fields, [action.field]: { ...state.fields[action.field], validating: action.validating } },
      };
    case "SET_SUBMITTING":
      return { ...state, isSubmitting: action.submitting, lastSubmitTime: action.submitting ? new Date() : state.lastSubmitTime };
    case "SET_VALIDATION_ERRORS": {
      const updated: AuthFormState["fields"] = { ...state.fields };
      // clear all errors first
      (Object.keys(updated) as FormFieldType[]).forEach((f) => {
        updated[f] = { ...updated[f], error: null };
      });
      // set new errors
      (Object.entries(action.errors) as Array<[FormFieldType, string | undefined]>).forEach(([field, err]) => {
        if (updated[field]) updated[field] = { ...updated[field], error: err ?? null };
      });
      const isValid = Object.keys(action.errors).length === 0;
      return { ...state, fields: updated, isValid };
    }
    case "CLEAR_ERRORS": {
      const cleared: AuthFormState["fields"] = { ...state.fields };
      (Object.keys(cleared) as FormFieldType[]).forEach((f) => {
        cleared[f] = { ...cleared[f], error: null };
      });
      return { ...state, fields: cleared, isValid: true };
    }
    case "RESET_FORM":
      return createInitialFormState();
    case "SET_SUBMIT_ATTEMPTED":
      return { ...state, submitAttempted: action.attempted };
    default:
      return state;
  }
}

export function submissionReducer(
  state: FormSubmissionState,
  action: SubmissionAction
): FormSubmissionState {
  switch (action.type) {
    case "SET_SUBMITTING":
      return { ...state, isSubmitting: action.submitting };
    case "INCREMENT_SUBMIT_COUNT":
      return { ...state, submitCount: state.submitCount + 1 };
    case "SET_LAST_SUBMIT_TIME":
      return { ...state, lastSubmitTime: action.when };
    case "SET_CAN_SUBMIT":
      return { ...state, canSubmit: action.canSubmit };
    case "SET_COOLDOWN":
      return { ...state, cooldownPeriod: action.cooldownMs };
    default:
      return state;
  }
}

// ---------------------------------------------------------------------------
// Validation Utilities
// ---------------------------------------------------------------------------
export interface FormValidationResult {
  isValid: boolean;
  errors: ValidationErrors;
  firstErrorField?: FormFieldType;
}

export class FormValidator {
  constructor(private readonly config: AuthFormConfig = DEFAULT_AUTH_FORM_CONFIG) {}

  validateField(field: FormFieldType, value: string): string | null {
    const fieldCfg = this.config.fields[field];
    for (const rule of fieldCfg.validationRules) {
      if (!rule.validate(value)) return rule.message;
    }
    return null;
  }

  validateForm(credentials: LoginCredentials, requireTwoFactor = false): FormValidationResult {
    const errors: ValidationErrors = {};

    const emailError = this.validateField("email", credentials.email);
    if (emailError) errors.email = emailError;

    const passwordError = this.validateField("password", credentials.password);
    if (passwordError) errors.password = passwordError;

    if (requireTwoFactor || credentials.totp_code) {
      const totpError = this.validateField("totp_code", credentials.totp_code || "");
      if (totpError) errors.totp_code = totpError;
    }

    const isValid = Object.keys(errors).length === 0;
    const firstErrorField = (Object.keys(errors)[0] as FormFieldType | undefined) || undefined;

    return { isValid, errors, firstErrorField };
  }

  canSubmit(submissionState: FormSubmissionState): boolean {
    if (submissionState.isSubmitting) return false;
    if (!submissionState.canSubmit) return false;

    if (submissionState.lastSubmitTime && submissionState.cooldownPeriod) {
      const since = Date.now() - submissionState.lastSubmitTime.getTime();
      if (since < submissionState.cooldownPeriod) return false;
    }
    return true;
  }
}

// ---------------------------------------------------------------------------
// Focus Management (DOM integration kept abstract for SSR safety)
// ---------------------------------------------------------------------------
export interface FormFocusManager {
  focusField: (field: FormFieldType) => void;
  focusFirstError: (errors: ValidationErrors) => void;
  focusNextField: (currentField: FormFieldType) => void;
  focusPreviousField: (currentField: FormFieldType) => void;
}

export function createFormFocusManager(prefix = "auth"): FormFocusManager {
  const ids: Record<FormFieldType, string> = {
    email: `${prefix}-email`,
    password: `${prefix}-password`,
    totp_code: `${prefix}-totp`,
  };
  const order: FormFieldType[] = ["email", "password", "totp_code"];

  const focusById = (id: string) => {
    if (typeof document === "undefined") return;
    const el = document.getElementById(id) as (HTMLInputElement | null);
    el?.focus?.();
  };

  return {
    focusField(field) {
      focusById(ids[field]);
    },
    focusFirstError(errors) {
      const key = (Object.keys(errors)[0] as FormFieldType | undefined);
      if (key) focusById(ids[key]);
    },
    focusNextField(current) {
      const idx = order.indexOf(current);
      const next = order[Math.min(order.length - 1, idx + 1)];
      focusById(ids[next]);
    },
    focusPreviousField(current) {
      const idx = order.indexOf(current);
      const prev = order[Math.max(0, idx - 1)];
      focusById(ids[prev]);
    },
  };
}

// ---------------------------------------------------------------------------
// Accessibility Helpers
// ---------------------------------------------------------------------------
export interface FormAccessibilityHelpers {
  getFieldAriaLabel: (field: FormFieldType) => string;
  getFieldAriaDescribedBy: (field: FormFieldType, hasError: boolean) => string;
  getFieldAriaInvalid: (hasError: boolean) => boolean;
  announceError: (error: string) => void;
  announceSuccess: (message: string) => void;
}

export function createFormAccessibilityHelpers(prefix = "auth"): FormAccessibilityHelpers {
  const ids: Record<FormFieldType, { input: string; error: string; hint: string }> = {
    email: { input: `${prefix}-email`, error: `${prefix}-email-error`, hint: `${prefix}-email-hint` },
    password: { input: `${prefix}-password`, error: `${prefix}-password-error`, hint: `${prefix}-password-hint` },
    totp_code: { input: `${prefix}-totp`, error: `${prefix}-totp-error`, hint: `${prefix}-totp-hint` },
  };

  const liveRegionId = `${prefix}-live`;

  const speak = (text: string) => {
    if (typeof document === "undefined") return;
    let region = document.getElementById(liveRegionId);
    if (!region) {
      region = document.createElement("div");
      region.id = liveRegionId;
      region.setAttribute("role", "status");
      region.setAttribute("aria-live", "polite");
      region.style.position = "absolute";
      region.style.left = "-9999px";
      document.body.appendChild(region);
    }
    region.textContent = text;
  };

  return {
    getFieldAriaLabel(field) {
      switch (field) {
        case "email":
          return "Email address";
        case "password":
          return "Password";
        case "totp_code":
          return "Two-factor authentication code";
      }
    },
    getFieldAriaDescribedBy(field, hasError) {
      const base = ids[field];
      return [hasError ? base.error : "", base.hint].filter(Boolean).join(" ");
    },
    getFieldAriaInvalid(hasError) {
      return !!hasError;
    },
    announceError(error) {
      speak(error);
    },
    announceSuccess(message) {
      speak(message);
    },
  };
}
