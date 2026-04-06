'use client';

import React, { useMemo, type ReactNode } from 'react';
import { FirebaseProvider } from '@/firebase/provider';

interface FirebaseClientProviderProps {
  children: ReactNode;
}

export function FirebaseClientProvider({ children }: FirebaseClientProviderProps) {
  // FirebaseProvider now only manages auth state without Firebase services
  return (
    <FirebaseProvider>
      {children}
    </FirebaseProvider>
  );
}