'use client';

import { createContext, useContext, useMemo, useState, useEffect } from 'react';
import type { DependencyList, ReactNode } from 'react';
import { authService, AuthUser } from '@/lib/auth';

// Theme context
type Theme = 'light' | 'dark';
type ThemeContextType = {
    theme: Theme;
    setTheme: (theme: Theme) => void;
};
const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const useTheme = () => {
    const context = useContext(ThemeContext);
    if (!context) {
        throw new Error('useTheme must be used within a ThemeProvider');
    }
    return context;
};

// Internal state for user authentication - using JWT-based auth
interface UserAuthState {
  user: AuthUser | null;
  isUserLoading: boolean;
  userError: Error | null;
}

// Combined state for the Firebase context (now simplified without Firebase services)
export interface FirebaseContextState {
  // User authentication state - now using JWT-based auth
  user: AuthUser | null;
  isUserLoading: boolean; // True during initial auth check
  userError: Error | null; // Error from auth operations
}

// Return type for useFirebase()
export interface FirebaseServicesAndUser {
  user: AuthUser | null;
  isUserLoading: boolean;
  userError: Error | null;
}

// Return type for useUser() - specific to user auth state
export interface UserHookResult {
  user: AuthUser | null;
  isUserLoading: boolean;
  userError: Error | null;
}

interface FirebaseProviderProps {
  children: ReactNode;
}

// React Context
export const FirebaseContext = createContext<FirebaseContextState | undefined>(undefined);

/**
 * FirebaseProvider manages and provides Firebase services.
 * Now using JWT-based authentication instead of Firebase.
 * The name is kept for compatibility but only provides auth/user state.
 */
export function FirebaseProvider({
  children,
}: FirebaseProviderProps) {
  const [userAuthState, setUserAuthState] = useState<UserAuthState>({
    user: null,
    isUserLoading: true,
    userError: null,
  });

  // Initialize authentication state and handle token refresh
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        setUserAuthState((prev: UserAuthState) => ({ ...prev, isUserLoading: true }));
        
        // Check if user is authenticated by looking for stored tokens
        if (authService.isAuthenticated()) {
          const user = authService.getCurrentUser();
          setUserAuthState({
            user,
            isUserLoading: false,
            userError: null,
          });
        } else {
          setUserAuthState({
            user: null,
            isUserLoading: false,
            userError: null,
          });
        }
      } catch (error) {
        setUserAuthState({
          user: null,
          isUserLoading: false,
          userError: error instanceof Error ? error : new Error('Authentication initialization failed'),
        });
      }
    };

    initializeAuth();

    // Set up periodic token refresh
    const refreshInterval = setInterval(async () => {
      if (authService.isAuthenticated()) {
        try {
          await authService.ensureValidToken();
        } catch (error) {
          console.warn('Token refresh failed, logging out user');
          setUserAuthState({
            user: null,
            isUserLoading: false,
            userError: error instanceof Error ? error : new Error('Token refresh failed'),
          });
        }
      }
    }, 5 * 60 * 1000); // Refresh every 5 minutes

    return () => clearInterval(refreshInterval);
  }, []);

  // Memoize the context value
  const contextValue = useMemo((): FirebaseContextState => {
    return {
      user: userAuthState.user,
      isUserLoading: userAuthState.isUserLoading,
      userError: userAuthState.userError,
    };
  }, [userAuthState]);

  // Theme logic
  const [theme, setTheme] = useState<Theme>('dark');
  useEffect(() => {
    const root = window.document.documentElement;
    const currentUserTheme = authService.getCurrentUser()?.preferences?.theme;
    const storedTheme = localStorage.getItem('theme') as Theme | null;
    const initialTheme =
      currentUserTheme === 'light' || currentUserTheme === 'dark'
        ? currentUserTheme
        : storedTheme || 'dark';
    
    setTheme(initialTheme);

    root.classList.remove('light', 'dark');
    root.classList.add(initialTheme);
  }, []);

  const handleSetTheme = (newTheme: Theme) => {
    const root = window.document.documentElement;
    root.classList.remove('light', 'dark');
    root.classList.add(newTheme);
    localStorage.setItem('theme', newTheme);
    setTheme(newTheme);
  };

  const themeContextValue = { theme, setTheme: handleSetTheme };

  return (
    <FirebaseContext.Provider value={contextValue}>
      <ThemeContext.Provider value={themeContextValue}>
        {children}
      </ThemeContext.Provider>
    </FirebaseContext.Provider>
  );
}

/**
 * Hook to access core Firebase services and user authentication state.
 * Now simplified to only provide auth/user state since Firebase services are removed.
 */
export const useFirebase = (): FirebaseServicesAndUser => {
  const context = useContext(FirebaseContext);

  if (context === undefined) {
    throw new Error('useFirebase must be used within a FirebaseProvider.');
  }

  return {
    user: context.user,
    isUserLoading: context.isUserLoading,
    userError: context.userError,
  };
};

/** Hook to access Firebase Auth instance. */
export const useAuth = (): any => {
  // Returning any type since we're not actually providing Firebase Auth anymore
  // Components using this should migrate to useAuthWithJWT or the lib/auth directly
  return null;
};

/** Hook to access Firestore instance. */
export const useFirestore = (): any => {
  // Returning any type since we're not actually providing Firestore anymore
  // Components using this should migrate to proper backend services
  return null;
};

/** Hook to access Firebase App instance. */
export const useFirebaseApp = (): any => {
  // Returning any type since we're not actually providing Firebase App anymore
  // Components using this should migrate to proper backend services
  return null;
};

type MemoFirebase <T> = T & {__memo?: boolean};

export function useMemoFirebase<T>(factory: () => T, deps: DependencyList): T | (MemoFirebase<T>) {
  const memoized = useMemo(factory, deps);
  
  if(typeof memoized !== 'object' || memoized === null) return memoized;
  (memoized as MemoFirebase<T>).__memo = true;
  
  return memoized;
}

/**
 * Hook specifically for accessing the authenticated user's state.
 * This provides the User object, loading status, and any auth errors.
 * @returns {UserHookResult} Object with user, isUserLoading, userError.
 */
export const useUser = (): UserHookResult => {
  const { user, isUserLoading, userError } = useFirebase(); // Leverages the main hook
  return { user, isUserLoading, userError };
};

/** Enhanced auth hook with JWT support */
export const useAuthWithJWT = () => {
  const { user, isUserLoading, userError } = useFirebase();
  
  const logout = async () => {
    try {
      await authService.logout();
      // The Firebase provider will automatically update the state
    } catch (error) {
      console.error('Logout failed:', error);
      // Still clear local state even if API call fails
      authService.clearAuthData();
    }
  };

  return {
    user,
    isUserLoading,
    userError,
    logout
  };
};