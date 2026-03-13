"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';

// Types for chat authentication
export interface ChatAuthState {
  isAuthenticated: boolean;
  hasChatAccess: boolean;
  chatPermissions: string[];
  currentConversationId: string | null;
  sessionActive: boolean;
  securityLevel: 'low' | 'medium' | 'high' | 'strict';
  lastActivity: Date | null;
  error: string | null;
  isLoading: boolean;
}

export interface ChatAuthCredentials {
  username: string;
  password: string;
  [key: string]: unknown;
}

export interface ChatAuthContextType {
  // Authentication methods
  login: (credentials: ChatAuthCredentials) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<boolean>;
  refreshSession: () => Promise<boolean>;
  clearError: () => void;
  isAuthenticated: boolean;
  
  // Chat-specific methods
  checkChatPermission: (permission: string) => boolean;
  hasChatAccess: boolean;
  startChatSession: (conversationId: string) => Promise<void>;
  endChatSession: (conversationId?: string) => Promise<void>;
  updateChatActivity: () => void;
  setSecurityLevel: (level: 'low' | 'medium' | 'high' | 'strict') => void;
  
  // Utility methods
  validateMessageContent: (content: string) => { isValid: boolean; threats: string[]; sanitized: string };
  encryptSensitiveData: (data: unknown) => string;
  decryptSensitiveData: (encryptedData: string) => unknown;
  
  // State
  chatAuthState: ChatAuthState;
}

// Create context
const ChatAuthContext = createContext<ChatAuthContextType | undefined>(undefined);

// Provider component
export function ChatAuthProvider({ children }: { children: React.ReactNode }) {
  const auth = useAuth();
  const { isAuthenticated, user, isAdmin, login, logout, checkAuth, refreshSession, clearError } = auth;
  const [chatAuthState, setChatAuthState] = useState<ChatAuthState>({
    isAuthenticated,
    hasChatAccess: false,
    chatPermissions: [],
    currentConversationId: null,
    sessionActive: false,
    securityLevel: 'medium',
    lastActivity: null,
    error: null,
    isLoading: false,
  });

  // Check chat permissions on auth state change
  useEffect(() => {
    if (isAuthenticated && user) {
      // Base chat permissions for authenticated users
      const basePermissions = [
        'chat:read',
        'chat:write',
        'chat:conversations:read',
        'chat:conversations:write',
        'chat:messages:read',
        'chat:messages:write',
        'chat:providers:read',
        'chat:providers:write',
      ];
      
      // Add admin permissions if user is admin
      const adminPermissions = isAdmin() ? [
        'chat:admin',
        'chat:audit:read',
        'chat:security:read',
        'chat:security:write',
      ] : [];
      
      const allPermissions = [...basePermissions, ...adminPermissions];
      
      setChatAuthState(prev => ({
        ...prev,
        isAuthenticated: true,
        hasChatAccess: true,
        chatPermissions: allPermissions,
        lastActivity: new Date(),
      }));
    } else {
      setChatAuthState(prev => ({
        ...prev,
        isAuthenticated: false,
        hasChatAccess: false,
        chatPermissions: [],
        lastActivity: new Date(),
      }));
    }
  }, [isAuthenticated, user, isAdmin]);

  // Helper function to get auth token
  const getAuthToken = useCallback((): string => {
    if (typeof window === 'undefined') return '';
    
    const cookies = document.cookie.split(';').reduce((acc, cookie) => {
      const [key, value] = cookie.trim().split('=');
      if (key && value) {
        acc[key] = value;
      }
      return acc;
    }, {} as Record<string, string>);
    
    return cookies.token || '';
  }, []);

  // Chat session management
  const startChatSession = useCallback(async (conversationId: string) => {
    if (!isAuthenticated) {
      setChatAuthState(prev => ({ ...prev, error: 'Authentication required for chat access' }));
      return;
    }

    try {
      setChatAuthState(prev => ({ ...prev, isLoading: true }));
      
      const token = getAuthToken();
      
      const response = await fetch('/api/chat/sessions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          conversationId,
          action: 'start',
        }),
      });
      
      if (response.ok) {
        await response.json();
        setChatAuthState(prev => ({
          ...prev,
          currentConversationId: conversationId,
          sessionActive: true,
          isLoading: false,
          lastActivity: new Date(),
        }));
      } else {
        throw new Error('Failed to start chat session');
      }
    } catch (error) {
      setChatAuthState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to start chat session',
        isLoading: false,
      }));
    }
  }, [getAuthToken, isAuthenticated]);

  const endChatSession = useCallback(async (conversationId?: string) => {
    if (!isAuthenticated) {
      setChatAuthState(prev => ({ ...prev, error: 'Authentication required for chat access' }));
      return;
    }

    try {
      setChatAuthState(prev => ({ ...prev, isLoading: true }));
      
      const currentSessionId = conversationId || chatAuthState.currentConversationId;
      
      if (currentSessionId) {
        const token = getAuthToken();
        
        const response = await fetch(`/api/chat/sessions/${currentSessionId}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({
            action: 'end',
          }),
        });
        
        if (response.ok) {
          setChatAuthState(prev => ({
            ...prev,
            currentConversationId: null,
            sessionActive: false,
            isLoading: false,
            lastActivity: new Date(),
          }));
        } else {
          throw new Error('Failed to end chat session');
        }
      } else {
        setChatAuthState(prev => ({
          ...prev,
          sessionActive: false,
          isLoading: false,
          lastActivity: new Date(),
        }));
      }
    } catch (error) {
      setChatAuthState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to end chat session',
        isLoading: false,
      }));
    }
  }, [chatAuthState.currentConversationId, getAuthToken, isAuthenticated]);

  // Permission checking
  const checkChatPermission = useCallback((permission: string): boolean => {
    return chatAuthState.chatPermissions.includes(permission) || 
           chatAuthState.chatPermissions.includes('chat:admin');
  }, [chatAuthState.chatPermissions]);

  // Security level management
  const setSecurityLevel = useCallback((level: 'low' | 'medium' | 'high' | 'strict') => {
    setChatAuthState(prev => ({
      ...prev,
      securityLevel: level,
    }));
  }, []);

  // Update activity
  const updateChatActivity = useCallback(() => {
    setChatAuthState(prev => ({
      ...prev,
      lastActivity: new Date(),
    }));
  }, []);

  // Content validation
  const validateMessageContent = useCallback((content: string) => {
    // Basic validation for common threats
    const xssPatterns = [
      /<script[^>]*>.*?<\/script>/gi,
      /javascript:/gi,
      /on\w+\s*=/gi,
      /<iframe[^>]*>/gi,
      /<object[^>]*>/gi,
      /<embed[^>]*>/gi,
    ];
    
    const sqlInjectionPatterns = [
      /(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)/gi,
      /(--|#|\/\*|\*\/)/gi,
      /(\bOR\b\s+\w+\s*=\s*\w+)/gi,
    ];
    
    const commandInjectionPatterns = [
      /[;&|`$()]/gi,
      /\b(curl|wget|nc|netcat|telnet|ssh|ftp|scp|rm|mv|cp|cat|ls|ps|kill|chmod|chown)\b/gi,
    ];
    
    const pathTraversalPatterns = [
      /\.\.[\/\\]/gi,
      /%2e%2e[\/\\]/gi,
      /\.\.%5c[\/\\]/gi,
      /\/etc\/(passwd|shadow|hosts)/gi,
      /\/proc\/[sys]/gi,
      /\/sys\/[class]/gi,
    ];
    
    const sensitiveDataPatterns = [
      /\b\d{4}[-\s]?\d{4}[-\s]?\d{4}\b/gi,  // Credit card numbers
      /\b\d{3}-\d{2}-\d{4}\b/gi,  // SSN
      /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/gi,  // Email addresses
      /\b(?:\d{1,3}\.){1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b/gi,  // IP addresses
    ];
    
    const threats: string[] = [];
    
    // Check for each threat type
    xssPatterns.forEach(pattern => {
      if (pattern.test(content)) {
        threats.push('XSS: Cross-site scripting');
      }
    });
    
    sqlInjectionPatterns.forEach(pattern => {
      if (pattern.test(content)) {
        threats.push('SQL Injection');
      }
    });
    
    commandInjectionPatterns.forEach(pattern => {
      if (pattern.test(content)) {
        threats.push('Command Injection');
      }
    });
    
    pathTraversalPatterns.forEach(pattern => {
      if (pattern.test(content)) {
        threats.push('Path Traversal');
      }
    });
    
    sensitiveDataPatterns.forEach(pattern => {
      if (pattern.test(content)) {
        threats.push('Sensitive Data Exposure');
      }
    });
    
    // Sanitize content
    let sanitizedContent = content;
    
    // Basic XSS protection
    sanitizedContent = sanitizedContent
      .replace(/<script[^>]*>.*?<\/script>/gi, '')
      .replace(/javascript:/gi, '')
      .replace(/on\w+\s*=/gi, '')
      .replace(/<iframe[^>]*>/gi, '')
      .replace(/<object[^>]*>/gi, '')
      .replace(/<embed[^>]*>/gi, '');
    
    // Remove dangerous attributes
    sanitizedContent = sanitizedContent
      .replace(/on\w+\s*=/gi, '')
      .replace(/style\s*=/gi, '')
      .replace(/href\s*=/gi, '');
    
    // Length check
    if (sanitizedContent.length > 10000) {
      sanitizedContent = sanitizedContent.substring(0, 10000);
      threats.push('Content too long');
    }
    
    return {
      isValid: threats.length === 0,
      threats,
      sanitized: sanitizedContent,
    };
  }, []);

  // Encryption utilities (client-side)
  const encryptSensitiveData = useCallback((data: unknown): string => {
    // In a real implementation, this would use a proper encryption library
    // For now, we'll use a simple obfuscation for demonstration
    try {
      const jsonString = JSON.stringify(data);
      return btoa(jsonString);
    } catch (error) {
      console.error('Encryption failed:', error);
      return '';
    }
  }, []);

  const decryptSensitiveData = useCallback((encryptedData: string): unknown => {
    try {
      const jsonString = atob(encryptedData);
      return JSON.parse(jsonString);
    } catch (error) {
      console.error('Decryption failed:', error);
      return null;
    }
  }, []);

  // Session timeout handling
  useEffect(() => {
    const checkSessionTimeout = () => {
      if (chatAuthState.lastActivity) {
        const timeSinceLastActivity = new Date().getTime() - chatAuthState.lastActivity.getTime();
        const sessionTimeout = 30 * 60 * 1000; // 30 minutes in milliseconds
        
        if (timeSinceLastActivity > sessionTimeout) {
          setChatAuthState(prev => ({
            ...prev,
            sessionActive: false,
            currentConversationId: null,
            error: 'Session expired due to inactivity',
          }));
          
          // Clear auth state
          logout();
        }
      }
    };

    const interval = setInterval(checkSessionTimeout, 60000); // Check every minute

    return () => clearInterval(interval);
  }, [chatAuthState.lastActivity, logout]);

  const contextValue: ChatAuthContextType = {
    // Authentication methods - wrap auth.login to convert credentials
    login: async (credentials: ChatAuthCredentials) => {
      // Convert ChatAuthCredentials to LoginCredentials
      const loginCredentials = {
        email: credentials.username,
        password: credentials.password,
        totp_code: credentials.totp_code as string | undefined,
      };
      return login(loginCredentials);
    },
    logout,
    checkAuth,
    refreshSession,
    clearError,
    isAuthenticated: chatAuthState.isAuthenticated,
    
    // Chat-specific methods
    checkChatPermission,
    hasChatAccess: chatAuthState.hasChatAccess,
    startChatSession,
    endChatSession,
    updateChatActivity,
    setSecurityLevel,
    
    // Utility methods
    validateMessageContent,
    encryptSensitiveData,
    decryptSensitiveData,
    
    // State
    chatAuthState,
  };

  return (
    <ChatAuthContext.Provider value={contextValue}>
      {children}
    </ChatAuthContext.Provider>
  );
}

// Custom hook for chat authentication
export function useChatAuth() {
  const context = useContext(ChatAuthContext);
  
  if (!context) {
    throw new Error('useChatAuth must be used within a ChatAuthProvider');
  }
  
  return context;
}

// Higher-order component for authentication guards
export interface ChatAuthGuardProps {
  children: React.ReactNode;
  requiredPermission?: string;
  fallback?: React.ReactNode;
  securityLevel?: 'low' | 'medium' | 'high' | 'strict';
}

export function ChatAuthGuard({ 
  children, 
  requiredPermission, 
  fallback = <div>You need to log in to access this feature.</div>,
  securityLevel = 'medium' 
}: ChatAuthGuardProps) {
  const { checkChatPermission, chatAuthState } = useChatAuth();
  
  const hasRequiredPermission = requiredPermission 
    ? checkChatPermission(requiredPermission)
    : true;
  
  const hasRequiredSecurityLevel = securityLevel 
    ? chatAuthState.securityLevel === securityLevel || 
      (securityLevel === 'medium' && chatAuthState.securityLevel !== 'low')
    : true;
  
  const isAuthorized = chatAuthState.isAuthenticated && 
                        hasRequiredPermission && 
                        hasRequiredSecurityLevel;
  
  if (isAuthorized) {
    return <>{children}</>;
  } else {
    return <>{fallback}</>;
  }
}

export default ChatAuthContext;
