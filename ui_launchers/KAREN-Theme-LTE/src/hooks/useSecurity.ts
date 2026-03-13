/**
 * useSecurity Hook - Security management hook
 */
import { useState, useCallback } from 'react';

export interface SecurityLevel {
  level: 'low' | 'medium' | 'high' | 'strict';
  score?: number;
}

export interface SecurityEvent {
  type: 'security_violation' | 'permission_change' | 'login' | 'logout';
  severity: 'low' | 'medium' | 'high';
  message: string;
  details?: Record<string, unknown>;
  timestamp: Date;
}

export function useSecurity() {
  const [securityLevel, setSecurityLevel] = useState<SecurityLevel>({
    level: 'medium',
    score: 75
  });

  const [securityEvents, setSecurityEvents] = useState<SecurityEvent[]>([]);

  const logSecurityEvent = useCallback((event: Omit<SecurityEvent, 'timestamp'>) => {
    const eventWithTimestamp: SecurityEvent = {
      ...event,
      timestamp: new Date()
    };
    
    setSecurityEvents(prev => [...prev, eventWithTimestamp]);
  }, []);

  const updateSecurityLevel = useCallback((level: 'low' | 'medium' | 'high' | 'strict') => {
    const scores: Record<string, number> = {
      low: 50,
      medium: 75,
      high: 90,
      strict: 100
    };
    
    setSecurityLevel(prev => ({
      ...prev,
      level,
      score: scores[level]
    }));

    // Log security level change
    logSecurityEvent({
      type: 'permission_change',
      severity: 'low',
      message: `Security level changed to ${level}`,
      details: { level, score: scores[level] }
    });
  }, [logSecurityEvent]);

  const checkChatPermission = useCallback((permission: string): boolean => {
    // Simple permission check - in a real implementation, this would check against user permissions
    const basePermissions = ['chat:read', 'chat:write', 'chat:conversations:read', 'chat:conversations:write'];
    const adminPermissions = ['chat:admin', 'chat:audit:read', 'chat:security:read', 'chat:security:write'];
    
    return basePermissions.includes(permission) || adminPermissions.includes(permission);
  }, []);

  return {
    securityLevel,
    setSecurityLevel,
    updateSecurityLevel,
    securityEvents,
    logSecurityEvent,
    checkChatPermission
  };
}

export default useSecurity;
