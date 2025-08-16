import { useCallback } from 'react';

interface InputPreservationHook {
  preserveInput: (value: string) => void;
  restoreInput: () => string | null;
  clearPreservedInput: () => void;
}

export const useInputPreservation = (key: string): InputPreservationHook => {
  const storageKey = `input-preservation-${key}`;

  const preserveInput = useCallback((value: string) => {
    try {
      if (value.trim()) {
        localStorage.setItem(storageKey, value);
      } else {
        localStorage.removeItem(storageKey);
      }
    } catch (error) {
      console.warn('Failed to preserve input:', error);
    }
  }, [storageKey]);

  const restoreInput = useCallback((): string | null => {
    try {
      return localStorage.getItem(storageKey);
    } catch (error) {
      console.warn('Failed to restore input:', error);
      return null;
    }
  }, [storageKey]);

  const clearPreservedInput = useCallback(() => {
    try {
      localStorage.removeItem(storageKey);
    } catch (error) {
      console.warn('Failed to clear preserved input:', error);
    }
  }, [storageKey]);

  return {
    preserveInput,
    restoreInput,
    clearPreservedInput
  };
};