"use client";

import { useContext } from 'react';
import { HookContext } from '@/contexts/HookContext';
import type { HookContextType } from '@/contexts/hook-types';

export const useHooks = (): HookContextType => {
  console.log('useHooks: Attempting to access HookContext');
  const context = useContext(HookContext);
  console.log('useHooks: HookContext value:', context);
  if (context === undefined) {
    console.error('useHooks: HookContext is undefined - throwing error');
    throw new Error('useHooks must be used within a HookProvider');
  }
  return context;
};