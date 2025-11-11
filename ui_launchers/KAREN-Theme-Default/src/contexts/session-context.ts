import { createContext } from 'react';

import type { SessionData } from '@/lib/auth/session';

export interface SessionUser {
  userId: string;
  email: string;
  roles: string[];
  tenantId: string;
}

export interface SessionContextType {
  isAuthenticated: boolean;
  user: SessionUser | null;
  isLoading: boolean;
  isInitialized: boolean;
  login: (email: string, password: string, totpCode?: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshSession: () => void;
  hasRole: (role: string) => boolean;
  sessionData: SessionData | null;
}

export const SessionContext = createContext<SessionContextType | undefined>(undefined);

