'use client';
import { AppProviders } from '@/contexts/AppProviders';
export function Providers({ children }: { children: React.ReactNode }) {
  return <AppProviders>{children}</AppProviders>;
}
