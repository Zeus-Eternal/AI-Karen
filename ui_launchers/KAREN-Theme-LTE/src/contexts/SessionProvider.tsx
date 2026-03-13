import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';

export interface SessionUser {
  id: string;
  name: string;
  email: string;
  role: 'user' | 'admin' | 'moderator';
  permissions: string[];
  lastLogin: Date;
}

export interface Session {
  id: string;
  user: SessionUser;
  token: string;
  createdAt: Date;
  expiresAt: Date;
  isActive: boolean;
  metadata?: Record<string, unknown>;
}

export interface SessionContextType {
  session: Session | null;
  login: (email: string, password: string) => Promise<Session>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<Session>;
  updateSession: (updates: Partial<Session>) => void;
  isLoading: boolean;
  error: string | null;
}

type SessionAction =
  | { type: 'LOGIN_START' }
  | { type: 'LOGIN_SUCCESS'; payload: Session }
  | { type: 'LOGIN_FAILURE'; payload: string }
  | { type: 'LOGOUT_START' }
  | { type: 'LOGOUT_SUCCESS' }
  | { type: 'LOGOUT_FAILURE'; payload: string }
  | { type: 'REFRESH_TOKEN_START' }
  | { type: 'REFRESH_TOKEN_SUCCESS'; payload: Session }
  | { type: 'REFRESH_TOKEN_FAILURE'; payload: string }
  | { type: 'UPDATE_SESSION'; payload: Partial<Session> }
  | { type: 'CLEAR_ERROR' };

interface SessionState {
  session: Session | null;
  isLoading: boolean;
  error: string | null;
}

const initialState: SessionState = {
  session: null,
  isLoading: false,
  error: null
};

function sessionReducer(state: SessionState, action: SessionAction): SessionState {
  switch (action.type) {
    case 'LOGIN_START':
      return {
        ...state,
        isLoading: true,
        error: null
      };

    case 'LOGIN_SUCCESS':
      return {
        ...state,
        session: action.payload,
        isLoading: false,
        error: null
      };

    case 'LOGIN_FAILURE':
      return {
        ...state,
        isLoading: false,
        error: action.payload
      };

    case 'LOGOUT_START':
      return {
        ...state,
        isLoading: true,
        error: null
      };

    case 'LOGOUT_SUCCESS':
      return {
        ...state,
        session: null,
        isLoading: false,
        error: null
      };

    case 'LOGOUT_FAILURE':
      return {
        ...state,
        isLoading: false,
        error: action.payload
      };

    case 'REFRESH_TOKEN_START':
      return {
        ...state,
        isLoading: true,
        error: null
      };

    case 'REFRESH_TOKEN_SUCCESS':
      return {
        ...state,
        session: action.payload,
        isLoading: false,
        error: null
      };

    case 'REFRESH_TOKEN_FAILURE':
      return {
        ...state,
        isLoading: false,
        error: action.payload
      };

    case 'UPDATE_SESSION':
      return {
        ...state,
        session: state.session ? { ...state.session, ...action.payload } : null
      };

    case 'CLEAR_ERROR':
      return {
        ...state,
        error: null
      };

    default:
      return state;
  }
}

const SessionContext = createContext<SessionContextType | undefined>(undefined);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(sessionReducer, initialState);

  const login = async (email: string, password: string): Promise<Session> => {
    dispatch({ type: 'LOGIN_START' });
    
    try {
      // Mock API call - replace with actual authentication
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
      });

      if (!response.ok) {
        throw new Error('Login failed');
      }

      const session: Session = await response.json();
      dispatch({ type: 'LOGIN_SUCCESS', payload: session });
      
      // Store session token
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem('auth_token', session.token);
      }
      
      return session;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Login failed';
      dispatch({ type: 'LOGIN_FAILURE', payload: errorMessage });
      throw error;
    }
  };

  const logout = async (): Promise<void> => {
    dispatch({ type: 'LOGOUT_START' });
    
    try {
      // Mock API call - replace with actual logout
      await fetch('/api/auth/logout', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${state.session?.token}`
        }
      });

      dispatch({ type: 'LOGOUT_SUCCESS' });
      
      // Clear stored token
      if (typeof localStorage !== 'undefined') {
        localStorage.removeItem('auth_token');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Logout failed';
      dispatch({ type: 'LOGOUT_FAILURE', payload: errorMessage });
      throw error;
    }
  };

  const refreshToken = async (): Promise<Session> => {
    dispatch({ type: 'REFRESH_TOKEN_START' });
    
    try {
      // Mock API call - replace with actual token refresh
      const response = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${state.session?.token}`
        }
      });

      if (!response.ok) {
        throw new Error('Token refresh failed');
      }

      const session: Session = await response.json();
      dispatch({ type: 'REFRESH_TOKEN_SUCCESS', payload: session });
      
      // Update stored token
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem('auth_token', session.token);
      }
      
      return session;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Token refresh failed';
      dispatch({ type: 'REFRESH_TOKEN_FAILURE', payload: errorMessage });
      throw error;
    }
  };

  const updateSession = (updates: Partial<Session>): void => {
    dispatch({ type: 'UPDATE_SESSION', payload: updates });
  };

  // Check for existing session on mount
  useEffect(() => {
    const checkExistingSession = async () => {
      if (typeof localStorage !== 'undefined') {
        const token = localStorage.getItem('auth_token');
        if (token) {
          try {
            // Validate token with server
            const response = await fetch('/api/auth/validate', {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${token}`
              }
            });

            if (response.ok) {
              const session: Session = await response.json();
              dispatch({ type: 'LOGIN_SUCCESS', payload: session });
            }
          } catch (error) {
            // Clear invalid token
            localStorage.removeItem('auth_token');
          }
        }
      }
    };

    checkExistingSession();
  }, []);

  const contextValue: SessionContextType = {
    ...state,
    login,
    logout,
    refreshToken,
    updateSession
  };

  return (
    <SessionContext.Provider value={contextValue}>
      {children}
    </SessionContext.Provider>
  );
}

export function useSession(): SessionContextType {
  const context = useContext(SessionContext);
  if (context === undefined) {
    throw new Error('useSession must be used within a SessionProvider');
  }
  return context;
}

export { SessionContext };
export default SessionProvider;
