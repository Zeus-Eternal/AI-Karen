/**
 * Unit tests for useFormValidation hook
 * Tests real-time validation, debouncing, and state management
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useFormValidation, useFieldValidation } from '../use-form-validation';
import type { LoginCredentials } from '@/types/auth';

describe('useFormValidation', () => {
  beforeEach(() => {
    vi.useFakeTimers();

  afterEach(() => {
    vi.useRealTimers();

  describe('Initial State', () => {
    it('should initialize with empty validation state', () => {
      const { result } = renderHook(() => useFormValidation());

      expect(result.current.validationState.isValid).toBe(false);
      expect(result.current.validationState.hasErrors).toBe(false);
      expect(result.current.validationState.isValidating).toBe(false);
      
      expect(result.current.errors.email).toBeUndefined();
      expect(result.current.errors.password).toBeUndefined();
      expect(result.current.errors.totp_code).toBeUndefined();

    it('should initialize all fields as untouched and unfocused', () => {
      const { result } = renderHook(() => useFormValidation());

      expect(result.current.isFieldTouched('email')).toBe(false);
      expect(result.current.isFieldTouched('password')).toBe(false);
      expect(result.current.isFieldTouched('totp_code')).toBe(false);

      expect(result.current.validationState.fields.email.focused).toBe(false);
      expect(result.current.validationState.fields.password.focused).toBe(false);
      expect(result.current.validationState.fields.totp_code.focused).toBe(false);


  describe('Field Validation', () => {
    it('should validate field synchronously', () => {
      const { result } = renderHook(() => useFormValidation());

      const emailResult = result.current.validateFieldSync('email', 'invalid-email');
      expect(emailResult.isValid).toBe(false);
      expect(emailResult.error).toBe('Please enter a valid email address');

      const validEmailResult = result.current.validateFieldSync('email', 'user@domain.com');
      expect(validEmailResult.isValid).toBe(true);
      expect(validEmailResult.error).toBeNull();

    it('should validate field asynchronously with debouncing', async () => {
      const { result } = renderHook(() => useFormValidation());

      let validationResult: any;
      
      act(() => {
        result.current.validateField('email', 'user@domain.com').then(res => {
          validationResult = res;


      // Should be validating initially
      expect(result.current.validationState.fields.email.isValidating).toBe(true);

      // Advance timers to complete debounced validation
      act(() => {
        vi.advanceTimersByTime(300);

      // Wait for promise to resolve
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0));

      expect(validationResult.isValid).toBe(true);
      expect(result.current.validationState.fields.email.isValidating).toBe(false);
      expect(result.current.getFieldError('email')).toBeNull();

    it('should clear field error', () => {
      const { result } = renderHook(() => useFormValidation());

      // First set an error
      act(() => {
        result.current.validateFieldSync('email', 'invalid');
        result.current.validationState.fields.email.error = 'Invalid email';

      // Then clear it
      act(() => {
        result.current.clearFieldError('email');

      expect(result.current.getFieldError('email')).toBeNull();

    it('should set field touched state', () => {
      const { result } = renderHook(() => useFormValidation());

      act(() => {
        result.current.setFieldTouched('email', true);

      expect(result.current.isFieldTouched('email')).toBe(true);

    it('should set field focused state', () => {
      const { result } = renderHook(() => useFormValidation());

      act(() => {
        result.current.setFieldFocused('email', true);

      expect(result.current.validationState.fields.email.focused).toBe(true);


  describe('Form Validation', () => {
    it('should validate entire form', () => {
      const { result } = renderHook(() => useFormValidation());

      const credentials: LoginCredentials = {
        email: 'user@domain.com',
        password: 'password123'
      };

      let formResult: any;
      act(() => {
        formResult = result.current.validateForm(credentials);

      expect(formResult.isValid).toBe(true);
      expect(Object.keys(formResult.errors)).toHaveLength(0);

    it('should return errors for invalid form', () => {
      const { result } = renderHook(() => useFormValidation());

      const credentials: LoginCredentials = {
        email: 'invalid-email',
        password: '123'
      };

      let formResult: any;
      act(() => {
        formResult = result.current.validateForm(credentials);

      expect(formResult.isValid).toBe(false);
      expect(formResult.errors.email).toBe('Please enter a valid email address');
      expect(formResult.errors.password).toBe('Password must be at least 8 characters long');
      expect(formResult.firstErrorField).toBe('email');

    it('should validate with 2FA requirement', () => {
      const { result } = renderHook(() => useFormValidation());

      const credentials: LoginCredentials = {
        email: 'user@domain.com',
        password: 'password123',
        totp_code: '12345'
      };

      let formResult: any;
      act(() => {
        formResult = result.current.validateForm(credentials, true);

      expect(formResult.isValid).toBe(false);
      expect(formResult.errors.totp_code).toBe('2FA code must be exactly 6 digits');

    it('should clear all errors', () => {
      const { result } = renderHook(() => useFormValidation());

      // First create some errors
      const credentials: LoginCredentials = {
        email: 'invalid',
        password: '123'
      };

      act(() => {
        result.current.validateForm(credentials);

      expect(result.current.validationState.hasErrors).toBe(true);

      // Then clear them
      act(() => {
        result.current.clearAllErrors();

      expect(result.current.validationState.hasErrors).toBe(false);
      expect(result.current.getFieldError('email')).toBeNull();
      expect(result.current.getFieldError('password')).toBeNull();

    it('should reset validation state', () => {
      const { result } = renderHook(() => useFormValidation());

      // Set some state
      act(() => {
        result.current.setFieldTouched('email', true);
        result.current.setFieldFocused('email', true);

      // Reset
      act(() => {
        result.current.resetValidation();

      expect(result.current.isFieldTouched('email')).toBe(false);
      expect(result.current.validationState.fields.email.focused).toBe(false);
      expect(result.current.validationState.hasErrors).toBe(false);


  describe('Real-time Validation Handlers', () => {
    it('should handle field change with validation', () => {
      const { result } = renderHook(() => useFormValidation({
        validateOnChange: true
      }));

      act(() => {
        result.current.handleFieldChange('email', 'user@domain.com');

      // Should trigger validation for email (validates on change)
      act(() => {
        vi.advanceTimersByTime(300);

      expect(result.current.getFieldError('email')).toBeNull();

    it('should clear error when user starts typing', () => {
      const { result } = renderHook(() => useFormValidation());

      // First set an error
      act(() => {
        result.current.validateForm({
          email: 'invalid',
          password: 'password123'


      expect(result.current.getFieldError('email')).toBeTruthy();

      // Then simulate user typing
      act(() => {
        result.current.handleFieldChange('email', 'user@domain.com');

      expect(result.current.getFieldError('email')).toBeNull();

    it('should handle field blur with validation', () => {
      const { result } = renderHook(() => useFormValidation({
        validateOnBlur: true
      }));

      act(() => {
        result.current.handleFieldBlur('password', 'short');

      expect(result.current.isFieldTouched('password')).toBe(true);
      expect(result.current.validationState.fields.password.focused).toBe(false);

      // Advance timer for validation
      act(() => {
        vi.advanceTimersByTime(500);

      expect(result.current.getFieldError('password')).toBe('Password must be at least 8 characters long');

    it('should handle field focus', () => {
      const { result } = renderHook(() => useFormValidation());

      act(() => {
        result.current.handleFieldFocus('email');

      expect(result.current.validationState.fields.email.focused).toBe(true);


  describe('Utility Methods', () => {
    it('should check if field is valid', () => {
      const { result } = renderHook(() => useFormValidation());

      expect(result.current.isFieldValid('email')).toBe(true);

      act(() => {
        result.current.validateForm({
          email: 'invalid',
          password: 'password123'


      expect(result.current.isFieldValid('email')).toBe(false);

    it('should determine when to show error', () => {
      const { result } = renderHook(() => useFormValidation());

      // Error should not show if field is not touched
      act(() => {
        result.current.validateForm({
          email: 'invalid',
          password: 'password123'


      expect(result.current.shouldShowError('email')).toBe(true); // validateForm sets touched

      // Reset and test untouched state
      act(() => {
        result.current.resetValidation();

      expect(result.current.shouldShowError('email')).toBe(false);


  describe('Configuration Options', () => {
    it('should respect validateOnChange setting', () => {
      const { result } = renderHook(() => useFormValidation({
        validateOnChange: false
      }));

      act(() => {
        result.current.handleFieldChange('email', 'invalid');

      // Should not validate on change when disabled
      act(() => {
        vi.advanceTimersByTime(300);

      expect(result.current.getFieldError('email')).toBeNull();

    it('should respect validateOnBlur setting', () => {
      const { result } = renderHook(() => useFormValidation({
        validateOnBlur: false
      }));

      act(() => {
        result.current.handleFieldBlur('email', 'invalid');

      // Should not validate on blur when disabled
      act(() => {
        vi.advanceTimersByTime(300);

      expect(result.current.getFieldError('email')).toBeNull();

    it('should use enhanced validation when enabled', () => {
      const { result } = renderHook(() => useFormValidation({
        enhanced: true
      }));

      const weakPasswordResult = result.current.validateFieldSync('password', 'password');
      expect(weakPasswordResult.isValid).toBe(false);
      expect(weakPasswordResult.error).toBe('Password is too common. Please choose a stronger password');



describe('useFieldValidation', () => {
  beforeEach(() => {
    vi.useFakeTimers();

  afterEach(() => {
    vi.useRealTimers();

  it('should validate single field', () => {
    const { result } = renderHook(() => useFieldValidation('email'));

    let validationResult: any;
    act(() => {
      validationResult = result.current.validate('user@domain.com');

    expect(validationResult.isValid).toBe(true);
    expect(result.current.isValid).toBe(true);

  it('should validate field with debouncing', () => {
    const { result } = renderHook(() => useFieldValidation('email'));

    const callback = vi.fn();
    
    act(() => {
      result.current.validateDebounced('user@domain.com', callback);

    expect(result.current.state.isValidating).toBe(true);

    act(() => {
      vi.advanceTimersByTime(300);

    expect(callback).toHaveBeenCalledWith({
      isValid: true,
      error: null

    expect(result.current.state.isValidating).toBe(false);

  it('should clear field error', () => {
    const { result } = renderHook(() => useFieldValidation('email'));

    // Set error first
    act(() => {
      result.current.validate('invalid');

    expect(result.current.isValid).toBe(false);

    // Clear error
    act(() => {
      result.current.clearError();

    expect(result.current.isValid).toBe(true);

  it('should set touched state', () => {
    const { result } = renderHook(() => useFieldValidation('email'));

    act(() => {
      result.current.setTouched(true);

    expect(result.current.state.touched).toBe(true);

  it('should determine when to show error', () => {
    const { result } = renderHook(() => useFieldValidation('email'));

    // Error should not show if not touched
    act(() => {
      result.current.validate('invalid');

    expect(result.current.shouldShowError).toBe(false);

    // Error should show when touched
    act(() => {
      result.current.setTouched(true);

    expect(result.current.shouldShowError).toBe(true);

  it('should use enhanced validation when enabled', () => {
    const { result } = renderHook(() => useFieldValidation('password', true));

    let validationResult: any;
    act(() => {
      validationResult = result.current.validate('password');

    expect(validationResult.isValid).toBe(false);
    expect(validationResult.error).toBe('Password is too common. Please choose a stronger password');

