'use client';

import { useCallback } from 'react';
import { useHapticContext } from './haptic-provider';
import { HapticPattern } from './types';

export function useHaptic() {
  const { enabled, supported, setEnabled, trigger } = useHapticContext();

  const triggerHaptic = useCallback((pattern: HapticPattern) => {
    trigger(pattern);
  }, [trigger]);

  const triggerSuccess = useCallback(() => {
    trigger('success');
  }, [trigger]);

  const triggerError = useCallback(() => {
    trigger('error');
  }, [trigger]);

  const triggerWarning = useCallback(() => {
    trigger('warning');
  }, [trigger]);

  const triggerSelection = useCallback(() => {
    trigger('selection');
  }, [trigger]);

  const triggerNotification = useCallback(() => {
    trigger('notification');
  }, [trigger]);

  const triggerImpact = useCallback(() => {
    trigger('impact');
  }, [trigger]);

  return {
    // State
    enabled,
    supported,
    
    // Actions
    setEnabled,
    triggerHaptic,
    
    // Convenience methods
    triggerSuccess,
    triggerError,
    triggerWarning,
    triggerSelection,
    triggerNotification,
    triggerImpact
  };
}