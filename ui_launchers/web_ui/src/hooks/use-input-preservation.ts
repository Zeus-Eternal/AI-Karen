'use client';

import { useState, useEffect, useCallback, useRef } from 'react';

interface InputPreservationOptions {
  key: string;
  debounceMs?: number;
  maxLength?: number;
  clearOnSubmit?: boolean;
}

interface InputPreservationState {
  value: string;
  lastSaved: number;
  isDirty: boolean;
  isRestored: boolean;
}

export function useInputPreservation(options: InputPreservationOptions) {
  const {
    key,
    debounceMs = 1000,
    maxLength = 10000,
    clearOnSubmit = true,
  } = options;

  const [state, setState] = useState<InputPreservationState>({
    value: '',
    lastSaved: 0,
    isDirty: false,
    isRestored: false,
  });

  const debounceRef = useRef<NodeJS.Timeout>();
  const storageKey = `karen_input_${key}`;

  // Load preserved input on mount
  useEffect(() => {
    try {
      const preserved = localStorage.getItem(storageKey);
      if (preserved) {
        const data = JSON.parse(preserved);
        if (data.value && data.timestamp > Date.now() - 24 * 60 * 60 * 1000) { // 24 hours
          setState(prev => ({
            ...prev,
            value: data.value,
            lastSaved: data.timestamp,
            isRestored: true,
          }));
        } else {
          // Clear expired data
          localStorage.removeItem(storageKey);
        }
      }
    } catch (error) {
      console.warn('Failed to restore input:', error);
    }
  }, [storageKey]);

  // Save input with debouncing
  const saveInput = useCallback((value: string) => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    debounceRef.current = setTimeout(() => {
      try {
        if (value.trim() && value.length <= maxLength) {
          const data = {
            value: value.trim(),
            timestamp: Date.now(),
          };
          localStorage.setItem(storageKey, JSON.stringify(data));
          setState(prev => ({
            ...prev,
            lastSaved: Date.now(),
            isDirty: false,
          }));
        } else if (!value.trim()) {
          // Clear storage if input is empty
          localStorage.removeItem(storageKey);
        }
      } catch (error) {
        console.warn('Failed to save input:', error);
      }
    }, debounceMs);
  }, [storageKey, debounceMs, maxLength]);

  // Update input value
  const setValue = useCallback((newValue: string) => {
    setState(prev => ({
      ...prev,
      value: newValue,
      isDirty: true,
      isRestored: false,
    }));
    saveInput(newValue);
  }, [saveInput]);

  // Clear preserved input
  const clearInput = useCallback(() => {
    try {
      localStorage.removeItem(storageKey);
      setState({
        value: '',
        lastSaved: 0,
        isDirty: false,
        isRestored: false,
      });
    } catch (error) {
      console.warn('Failed to clear input:', error);
    }
  }, [storageKey]);

  // Mark as submitted (optionally clear)
  const markSubmitted = useCallback(() => {
    if (clearOnSubmit) {
      clearInput();
    } else {
      setState(prev => ({
        ...prev,
        isDirty: false,
      }));
    }
  }, [clearOnSubmit, clearInput]);

  // Get preservation status
  const getStatus = useCallback(() => {
    return {
      hasPreservedData: state.isRestored,
      lastSaved: state.lastSaved,
      isDirty: state.isDirty,
      canRestore: !!localStorage.getItem(storageKey),
    };
  }, [state, storageKey]);

  // Restore from storage manually
  const restoreInput = useCallback(() => {
    try {
      const preserved = localStorage.getItem(storageKey);
      if (preserved) {
        const data = JSON.parse(preserved);
        setState(prev => ({
          ...prev,
          value: data.value || '',
          lastSaved: data.timestamp || 0,
          isRestored: true,
          isDirty: false,
        }));
        return data.value || '';
      }
    } catch (error) {
      console.warn('Failed to restore input:', error);
    }
    return '';
  }, [storageKey]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, []);

  return {
    value: state.value,
    setValue,
    clearInput,
    markSubmitted,
    getStatus,
    restoreInput,
    isRestored: state.isRestored,
    isDirty: state.isDirty,
  };
}