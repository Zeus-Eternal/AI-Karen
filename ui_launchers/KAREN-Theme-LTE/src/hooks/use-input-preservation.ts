import React from 'react';
const { useCallback } = React;
import { safeWarn, errorHandler } from '@/lib/errorHandler';

export interface InputPreservationHook {
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
      safeWarn('Failed to preserve input:', errorHandler.toErrorContext(error));
    }
  }, [storageKey]);

  const restoreInput = useCallback((): string | null => {
    try {
      return localStorage.getItem(storageKey);
    } catch (error) {
      safeWarn('Failed to restore input:', errorHandler.toErrorContext(error));
      return null;
    }
  }, [storageKey]);

  const clearPreservedInput = useCallback(() => {
    try {
      localStorage.removeItem(storageKey);
    } catch (error) {
      safeWarn('Failed to clear preserved input:', errorHandler.toErrorContext(error));
    }
  }, [storageKey]);

  return {
    preserveInput,
    restoreInput,
    clearPreservedInput
  };
};