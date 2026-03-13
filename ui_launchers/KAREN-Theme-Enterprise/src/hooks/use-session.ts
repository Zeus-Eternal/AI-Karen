"use client";

import React from 'react';
const { useContext } = React;
import { SessionContext, type SessionContextType } from '@/contexts/SessionProvider';

export type UseSessionReturn = SessionContextType;

export const useSession = (): UseSessionReturn => {
  const context = useContext(SessionContext);
  if (context === undefined) {
    throw new Error('useSession must be used within a SessionProvider');
  }
  return context;
};