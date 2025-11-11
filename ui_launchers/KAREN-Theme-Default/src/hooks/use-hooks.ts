"use client";

import { useContext } from 'react';
import { HookContext } from '@/contexts/HookContext';

export const useHooks = () => {
  const context = useContext(HookContext);
  if (context === undefined) {
    throw new Error('useHooks must be used within a HookProvider');
  }
  return context;
};