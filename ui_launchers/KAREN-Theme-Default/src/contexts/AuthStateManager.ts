import { type SessionUser } from '@/contexts/SessionProvider';

export interface AuthSnapshot {
  isAuthenticated: boolean;
  user: SessionUser | null;
}

type Listener = (state: AuthSnapshot) => void;

class AuthStateManager {
  private state: AuthSnapshot = { isAuthenticated: false, user: null };
  private listeners = new Set<Listener>();

  constructor() {
    if (typeof window !== 'undefined') {
      const stored = window.sessionStorage.getItem('auth_state');
      if (stored) {
        try {
          this.state = JSON.parse(stored);
        } catch {
          /* ignore */
        }
      }
    }
  }

  getState(): AuthSnapshot {
    return this.state;
  }

  updateState(state: AuthSnapshot): void {
    this.state = state;
    if (typeof window !== 'undefined') {
      window.sessionStorage.setItem('auth_state', JSON.stringify(state));
    }
    this.listeners.forEach(l => l(this.state));
  }

  subscribe(listener: Listener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }
}

export const authStateManager = new AuthStateManager();
