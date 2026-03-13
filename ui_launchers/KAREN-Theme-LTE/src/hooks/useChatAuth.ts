import { useState, useEffect, useCallback } from 'react';
import { useChatAuth } from '@/contexts/ChatAuthContext';

// Types for chat authentication hook
export interface ChatAuthHookState {
  isAuthenticated: boolean;
  hasChatAccess: boolean;
  isLoading: boolean;
  error: string | null;
  sessionActive: boolean;
  currentConversationId: string | null;
  securityLevel: 'low' | 'medium' | 'high' | 'strict';
  lastActivity: Date | null;
  chatPermissions: string[];
}

export interface ChatAuthCredentials {
  username: string;
  password: string;
  [key: string]: unknown; // Add index signature to match context type
}

export interface ChatAuthHookActions {
  // Authentication actions
  login: (credentials: ChatAuthCredentials) => Promise<void>;
  logout: () => void;
  refreshSession: () => Promise<boolean>;
  clearError: () => void;
  
  // Chat session actions
  startChatSession: (conversationId: string) => Promise<void>;
  endChatSession: (conversationId?: string) => Promise<void>;
  updateChatActivity: () => void;
  
  // Security actions
  setSecurityLevel: (level: 'low' | 'medium' | 'high' | 'strict') => void;
  validateMessageContent: (content: string) => { isValid: boolean; threats: string[]; sanitized: string };
  
  // Permission actions
  checkChatPermission: (permission: string) => boolean;
  hasPermission: (permission: string) => boolean;
  hasAnyPermission: (permissions: string[]) => boolean;
  hasAllPermissions: (permissions: string[]) => boolean;
  
  // Utility actions
  encryptSensitiveData: (data: unknown) => string;
  decryptSensitiveData: (encryptedData: string) => unknown;
  isSessionExpired: () => boolean;
  getTimeUntilSessionExpiry: () => number;
}

export interface UseChatAuthReturn extends ChatAuthHookState, ChatAuthHookActions {}

// Custom hook for chat authentication with additional functionality
export function useChatAuthHook(): UseChatAuthReturn {
  const chatAuth = useChatAuth();
  
  // Local state for additional functionality
  const [localState, setLocalState] = useState({
    lastPermissionCheck: new Date(),
    permissionCache: new Map<string, boolean>(),
  });

  // Enhanced permission checking with caching
  const checkChatPermission = useCallback((permission: string): boolean => {
    // Check cache first
    const cacheKey = `${permission}_${chatAuth.chatAuthState.chatPermissions.join(',')}`;
    
    if (localState.permissionCache.has(cacheKey)) {
      return localState.permissionCache.get(cacheKey)!;
    }
    
    // Check permission and cache result
    const hasPermission = chatAuth.checkChatPermission(permission);
    
    setLocalState(prev => ({
      ...prev,
      permissionCache: new Map(prev.permissionCache).set(cacheKey, hasPermission),
      lastPermissionCheck: new Date(),
    }));
    
    return hasPermission;
  }, [chatAuth, localState.permissionCache]);

  // Convenience permission methods
  const hasPermission = useCallback((permission: string): boolean => {
    return checkChatPermission(permission);
  }, [checkChatPermission]);

  const hasAnyPermission = useCallback((permissions: string[]): boolean => {
    return permissions.some(permission => checkChatPermission(permission));
  }, [checkChatPermission]);

  const hasAllPermissions = useCallback((permissions: string[]): boolean => {
    return permissions.every(permission => checkChatPermission(permission));
  }, [checkChatPermission]);

  // Session management utilities
  const isSessionExpired = useCallback((): boolean => {
    if (!chatAuth.chatAuthState.lastActivity) return true;
    
    const timeSinceLastActivity = new Date().getTime() - chatAuth.chatAuthState.lastActivity.getTime();
    const sessionTimeout = 30 * 60 * 1000; // 30 minutes
    
    return timeSinceLastActivity > sessionTimeout;
  }, [chatAuth.chatAuthState.lastActivity]);

  const getTimeUntilSessionExpiry = useCallback((): number => {
    if (!chatAuth.chatAuthState.lastActivity) return 0;
    
    const timeSinceLastActivity = new Date().getTime() - chatAuth.chatAuthState.lastActivity.getTime();
    const sessionTimeout = 30 * 60 * 1000; // 30 minutes
    
    return Math.max(0, sessionTimeout - timeSinceLastActivity);
  }, [chatAuth.chatAuthState.lastActivity]);

  // Enhanced session management with auto-refresh
  const startChatSession = useCallback(async (conversationId: string) => {
    await chatAuth.startChatSession(conversationId);
  }, [chatAuth]);

  const endChatSession = useCallback(async (conversationId?: string) => {
    await chatAuth.endChatSession(conversationId);
  }, [chatAuth]);

  // Enhanced security level management with validation
  const setSecurityLevel = useCallback((level: 'low' | 'medium' | 'high' | 'strict') => {
    // Validate user has permission to change security level
    if (checkChatPermission('chat:security:write')) {
      chatAuth.setSecurityLevel(level);
    } else {
      console.warn('User does not have permission to change security level');
    }
  }, [chatAuth, checkChatPermission]);

  // Enhanced content validation with additional checks
  const validateMessageContent = useCallback((content: string) => {
    const baseValidation = chatAuth.validateMessageContent(content);
    
    // Add additional validation based on security level
    const enhancedValidation = { ...baseValidation };
    
    switch (chatAuth.chatAuthState.securityLevel) {
      case 'strict':
        // Additional strict validation
        if (content.includes('<') || content.includes('>')) {
          enhancedValidation.threats.push('HTML tags not allowed in strict mode');
          enhancedValidation.isValid = false;
        }
        if (content.length > 500) {
          enhancedValidation.threats.push('Message too long for strict mode');
          enhancedValidation.isValid = false;
        }
        break;
      case 'high':
        // Additional high security validation
        if (content.includes('http://') || content.includes('https://')) {
          enhancedValidation.threats.push('Links not allowed in high security mode');
          enhancedValidation.isValid = false;
        }
        if (content.length > 1000) {
          enhancedValidation.threats.push('Message too long for high security mode');
          enhancedValidation.isValid = false;
        }
        break;
      case 'medium':
        // Medium security validation
        if (content.length > 5000) {
          enhancedValidation.threats.push('Message too long for medium security mode');
          enhancedValidation.isValid = false;
        }
        break;
      case 'low':
        // Low security validation (only basic checks)
        if (content.length > 10000) {
          enhancedValidation.threats.push('Message too long');
          enhancedValidation.isValid = false;
        }
        break;
    }
    
    return enhancedValidation;
  }, [chatAuth]);

  // Auto-refresh session before expiry
  useEffect(() => {
    const checkAndRefreshSession = async () => {
      const timeUntilExpiry = getTimeUntilSessionExpiry();
      
      // Refresh session 5 minutes before expiry
      if (timeUntilExpiry > 0 && timeUntilExpiry < 5 * 60 * 1000) {
        try {
          await chatAuth.refreshSession();
        } catch (error) {
          console.error('Failed to refresh session:', error);
        }
      }
    };

    const interval = setInterval(checkAndRefreshSession, 60000); // Check every minute

    return () => clearInterval(interval);
  }, [getTimeUntilSessionExpiry, chatAuth]);

  // Clear permission cache when permissions change
  useEffect(() => {
    setLocalState(prev => ({
      ...prev,
      permissionCache: new Map(),
      lastPermissionCheck: new Date(),
    }));
  }, [chatAuth.chatAuthState.chatPermissions]);

  // Combine all state and actions
  const hookReturn: UseChatAuthReturn = {
    // State
    isAuthenticated: chatAuth.chatAuthState.isAuthenticated,
    hasChatAccess: chatAuth.chatAuthState.hasChatAccess,
    isLoading: chatAuth.chatAuthState.isLoading,
    error: chatAuth.chatAuthState.error,
    sessionActive: chatAuth.chatAuthState.sessionActive,
    currentConversationId: chatAuth.chatAuthState.currentConversationId,
    securityLevel: chatAuth.chatAuthState.securityLevel,
    lastActivity: chatAuth.chatAuthState.lastActivity,
    chatPermissions: chatAuth.chatAuthState.chatPermissions,
    
    // Authentication actions
    login: (credentials) => chatAuth.login(credentials),
    logout: chatAuth.logout,
    refreshSession: chatAuth.refreshSession,
    clearError: chatAuth.clearError,
    
    // Chat session actions
    startChatSession,
    endChatSession,
    updateChatActivity: chatAuth.updateChatActivity,
    
    // Security actions
    setSecurityLevel,
    validateMessageContent,
    
    // Permission actions
    checkChatPermission,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    
    // Utility actions
    encryptSensitiveData: chatAuth.encryptSensitiveData,
    decryptSensitiveData: chatAuth.decryptSensitiveData,
    isSessionExpired,
    getTimeUntilSessionExpiry,
  };

  return hookReturn;
}

// Convenience hook for specific chat permissions
export function useChatPermission(permission: string): boolean {
  const { hasPermission } = useChatAuthHook();
  return hasPermission(permission);
}

// Convenience hook for multiple chat permissions
export function useChatPermissions(permissions: string[]): {
  hasAny: boolean;
  hasAll: boolean;
  individual: Record<string, boolean>;
} {
  const { hasAnyPermission, hasAllPermissions, checkChatPermission } = useChatAuthHook();
  
  const individual = permissions.reduce((acc, perm) => {
    acc[perm] = checkChatPermission(perm);
    return acc;
  }, {} as Record<string, boolean>);
  
  return {
    hasAny: hasAnyPermission(permissions),
    hasAll: hasAllPermissions(permissions),
    individual,
  };
}

// Convenience hook for chat session management
export function useChatSession() {
  const { 
    sessionActive, 
    currentConversationId, 
    startChatSession, 
    endChatSession, 
    isSessionExpired,
    getTimeUntilSessionExpiry 
  } = useChatAuthHook();
  
  return {
    isActive: sessionActive,
    conversationId: currentConversationId,
    isExpired: isSessionExpired(),
    timeUntilExpiry: getTimeUntilSessionExpiry(),
    start: startChatSession,
    end: endChatSession,
  };
}

// Convenience hook for chat security
export function useChatSecurity() {
  const { 
    securityLevel, 
    setSecurityLevel, 
    validateMessageContent,
    encryptSensitiveData,
    decryptSensitiveData,
    checkChatPermission 
  } = useChatAuthHook();
  
  const canChangeSecurityLevel = checkChatPermission('chat:security:write');
  
  return {
    currentLevel: securityLevel,
    setLevel: canChangeSecurityLevel ? setSecurityLevel : () => {},
    validateContent: validateMessageContent,
    encrypt: encryptSensitiveData,
    decrypt: decryptSensitiveData,
    canChangeLevel: canChangeSecurityLevel,
  };
}

export default useChatAuthHook;
