import { useContext } from 'react';
import { HookContext } from '@/contexts/HookContext';

export const useHookContext = () => {
  const context = useContext(HookContext);
  if (context === undefined) {
    throw new Error('useHookContext must be used within a HookProvider');
  }
  return context;
};