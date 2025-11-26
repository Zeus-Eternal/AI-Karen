import { useContext } from 'react';
import { HookContext } from '@/contexts/HookContext';
import type { HookContextType } from '@/contexts/hook-types';

export const useHookContext = (): HookContextType => {
  const context = useContext(HookContext);
  if (context === undefined) {
    throw new Error('useHookContext must be used within a HookProvider');
  }
  return context;
};