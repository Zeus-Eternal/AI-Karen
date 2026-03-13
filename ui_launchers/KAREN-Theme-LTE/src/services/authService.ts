import { AuthResponse, LoginCredentials, User } from '@/types/auth';

// Note: AuthResponse already has token property, no need to extend
import { verifyToken } from '@/lib/jwt';

// Types for chat authentication service
export interface ChatAuthService {
  // Basic authentication
  login: (credentials: LoginCredentials) => Promise<AuthResponse>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<AuthResponse>;
  checkAuth: () => Promise<boolean>;
  
  // Chat-specific authentication
  loginWithChatSession: (credentials: LoginCredentials, conversationId?: string) => Promise<AuthResponse>;
  logoutWithChatSession: (conversationId?: string) => Promise<void>;
  validateChatSession: (conversationId: string) => Promise<boolean>;
  
  // Security
  validateSecurityToken: (token: string) => Promise<boolean>;
  generateSecurityToken: () => string;
  encryptSensitiveData: (data: unknown) => string;
  decryptSensitiveData: (encryptedData: string) => unknown;
  
  // Session management
  createChatSession: (userId: string, conversationId: string) => Promise<ChatSession>;
  getChatSession: (sessionId: string) => Promise<ChatSession | null>;
  updateChatSession: (sessionId: string, updates: Partial<ChatSession>) => Promise<ChatSession>;
  deleteChatSession: (sessionId: string) => Promise<void>;
  
  // Rate limiting
  checkRateLimit: (action: string, userId?: string) => Promise<boolean>;
  incrementRateLimit: (action: string, userId?: string) => Promise<void>;
  getRateLimitStatus: (userId?: string) => Promise<RateLimitStatus>;
  
  // Permissions
  hasChatPermission: (permission: string, user?: User) => boolean;
  hasAnyChatPermission: (permissions: string[], user?: User) => boolean;
  hasAllChatPermissions: (permissions: string[], user?: User) => boolean;
  getChatPermissions: (user?: User) => Promise<string[]>;
}

export interface ChatSession {
  id: string;
  userId: string;
  conversationId: string;
  startTime: Date;
  lastActivity: Date;
  isActive: boolean;
  securityLevel: 'low' | 'medium' | 'high' | 'strict';
  ipAddress: string;
  userAgent: string;
  metadata?: Record<string, unknown>;
}

export interface RateLimit {
  action: string;
  count: number;
  maxRequests: number;
  resetTime: number;
}

export interface RateLimitStatus {
  action: string;
  limit: number;
  remaining: number;
  resetTime: Date;
  isBlocked: boolean;
}

// Enhanced authentication service implementation
class ChatAuthServiceImpl implements ChatAuthService {
  private baseUrl: string;
  private tokenStorageKey = 'auth_token';
  private chatSessionStorageKey = 'chat_sessions';
  private rateLimitStorageKey = 'rate_limits';

  constructor(baseUrl: string = '/api') {
    this.baseUrl = baseUrl;
  }

  // Basic authentication methods
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      });

      if (!response.ok) {
        throw new Error('Login failed');
      }

      const data: AuthResponse = await response.json();
      
      if (data.success && data.token) {
        this.setToken(data.token);
      }

      return data;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }

  async logout(): Promise<void> {
    try {
      await fetch(`${this.baseUrl}/auth/logout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.getToken()}`,
        },
      });

      this.clearToken();
      this.clearChatSessions();
    } catch (error) {
      console.error('Logout error:', error);
      throw error;
    }
  }

  async refreshToken(): Promise<AuthResponse> {
    try {
      const currentToken = this.getToken();
      if (!currentToken) {
        throw new Error('No token to refresh');
      }

      const response = await fetch(`${this.baseUrl}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${currentToken}`,
        },
      });

      if (!response.ok) {
        throw new Error('Token refresh failed');
      }

      const data: AuthResponse = await response.json();
      
      if (data.success && data.token) {
        this.setToken(data.token);
      }

      return data;
    } catch (error) {
      console.error('Token refresh error:', error);
      throw error;
    }
  }

  async checkAuth(): Promise<boolean> {
    try {
      const token = this.getToken();
      if (!token) {
        return false;
      }

      const response = await fetch(`${this.baseUrl}/auth/check`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        this.clearToken();
        return false;
      }

      const data = await response.json();
      return data.valid || false;
    } catch (error) {
      console.error('Auth check error:', error);
      return false;
    }
  }

  // Chat-specific authentication methods
  async loginWithChatSession(credentials: LoginCredentials, conversationId?: string): Promise<AuthResponse> {
    try {
      const response = await this.login(credentials);
      
      if (response.success && conversationId) {
        await this.createChatSession(response.user?.userId || 'unknown', conversationId);
      }

      return response;
    } catch (error) {
      console.error('Chat login error:', error);
      throw error;
    }
  }

  async logoutWithChatSession(conversationId?: string): Promise<void> {
    try {
      if (conversationId) {
        const sessions = this.getChatSessions();
        const sessionToDelete = sessions.find(s => s.conversationId === conversationId);
        
        if (sessionToDelete) {
          await this.deleteChatSession(sessionToDelete.id);
        }
      }

      await this.logout();
    } catch (error) {
      console.error('Chat logout error:', error);
      throw error;
    }
  }

  async validateChatSession(conversationId: string): Promise<boolean> {
    try {
      const sessions = this.getChatSessions();
      const session = sessions.find(s => s.conversationId === conversationId);
      
      if (!session) {
        return false;
      }

      // Check if session is still valid (not expired)
      const now = new Date();
      const sessionAge = now.getTime() - session.lastActivity.getTime();
      const maxAge = 30 * 60 * 1000; // 30 minutes
      
      return session.isActive && sessionAge < maxAge;
    } catch (error) {
      console.error('Session validation error:', error);
      return false;
    }
  }

  // Security methods
  async validateSecurityToken(token: string): Promise<boolean> {
    try {
      const payload = verifyToken(token);
      return payload !== null;
    } catch (error) {
      console.error('Token validation error:', error);
      return false;
    }
  }

  generateSecurityToken(): string {
    // Generate a cryptographically secure random token
    const array = new Uint8Array(32);
    crypto.getRandomValues(array);
    
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
  }

  encryptSensitiveData(data: unknown): string {
    try {
      // In a real implementation, use a proper encryption library
      // For demonstration, we'll use a simple obfuscation
      const jsonString = JSON.stringify(data);
      return btoa(jsonString);
    } catch (error) {
      console.error('Encryption error:', error);
      return '';
    }
  }

  decryptSensitiveData(encryptedData: string): unknown {
    try {
      // In a real implementation, use a proper decryption library
      const jsonString = atob(encryptedData);
      return JSON.parse(jsonString);
    } catch (error) {
      console.error('Decryption error:', error);
      return null;
    }
  }

  // Session management methods
  async createChatSession(userId: string, conversationId: string): Promise<ChatSession> {
    try {
      const session: ChatSession = {
        id: this.generateSessionId(),
        userId,
        conversationId,
        startTime: new Date(),
        lastActivity: new Date(),
        isActive: true,
        securityLevel: 'medium',
        ipAddress: await this.getClientIP(),
        userAgent: navigator.userAgent,
        metadata: {
          createdAt: new Date().toISOString(),
        }
      };

      const sessions = this.getChatSessions();
      sessions.push(session);
      this.setChatSessions(sessions);

      return session;
    } catch (error) {
      console.error('Create session error:', error);
      throw error;
    }
  }

  async getChatSession(sessionId: string): Promise<ChatSession | null> {
    try {
      const sessions = this.getChatSessions();
      return sessions.find(s => s.id === sessionId) || null;
    } catch (error) {
      console.error('Get session error:', error);
      return null;
    }
  }

  async updateChatSession(sessionId: string, updates: Partial<ChatSession>): Promise<ChatSession> {
    try {
      const sessions = this.getChatSessions();
      const sessionIndex = sessions.findIndex(s => s.id === sessionId);
      
      if (sessionIndex === -1) {
        throw new Error('Session not found');
      }

      const existingSession = sessions[sessionIndex];
      const updatedSession: ChatSession = {
        ...existingSession,
        ...updates,
        lastActivity: new Date(),
        startTime: existingSession?.startTime || new Date(),
        isActive: existingSession?.isActive ?? updates.isActive ?? true,
        securityLevel: existingSession?.securityLevel || updates.securityLevel || 'medium',
        ipAddress: existingSession?.ipAddress || updates.ipAddress || '',
        userAgent: existingSession?.userAgent || updates.userAgent || '',
        metadata: existingSession?.metadata || updates.metadata || {},
        id: existingSession?.id || updates.id || `session_${Date.now()}`,
        userId: existingSession?.userId || updates.userId || '',
        conversationId: existingSession?.conversationId || updates.conversationId || '',
      };
      
      sessions[sessionIndex] = updatedSession;

      this.setChatSessions(sessions);
      return sessions[sessionIndex]!;
    } catch (error) {
      console.error('Update session error:', error);
      throw error;
    }
  }

  async deleteChatSession(sessionId: string): Promise<void> {
    try {
      const sessions = this.getChatSessions();
      const filteredSessions = sessions.filter(s => s.id !== sessionId);
      this.setChatSessions(filteredSessions);
    } catch (error) {
      console.error('Delete session error:', error);
      throw error;
    }
  }

  // Rate limiting methods
  async checkRateLimit(action: string, userId?: string): Promise<boolean> {
    try {
      const rateLimits = this.getRateLimits();
      const key = userId ? `${userId}:${action}` : action;
      const limit = rateLimits[key];
      
      if (!limit) {
        return true;
      }

      const now = Date.now();
      const timeSinceReset = now - limit.resetTime;
      const resetInterval = 60 * 1000; // 1 minute
      
      if (timeSinceReset >= resetInterval) {
        return true; // Reset the limit
      }

      return limit.count < limit.maxRequests;
    } catch (error) {
      console.error('Rate limit check error:', error);
      return false;
    }
  }

  async incrementRateLimit(action: string, userId?: string): Promise<void> {
    try {
      const rateLimits = this.getRateLimits();
      const key = userId ? `${userId}:${action}` : action;
      const now = Date.now();
      const resetInterval = 60 * 1000; // 1 minute
      
      if (!rateLimits[key] || now - (rateLimits[key]?.resetTime || 0) >= resetInterval) {
        rateLimits[key] = {
          action,
          count: 1,
          maxRequests: this.getMaxRequests(action),
          resetTime: now,
        };
      } else {
        rateLimits[key].count++;
      }

      this.setRateLimits(rateLimits);
    } catch (error) {
      console.error('Rate limit increment error:', error);
    }
  }

  async getRateLimitStatus(userId?: string): Promise<RateLimitStatus> {
    try {
      const rateLimits = this.getRateLimits();
      const userLimits = userId 
        ? Object.entries(rateLimits).filter(([key]) => key.startsWith(`${userId}:`))
        : [];

      if (userLimits.length === 0) {
        return {
          action: 'none',
          limit: 0,
          remaining: 0,
          resetTime: new Date(),
          isBlocked: false,
        };
      }

      // Aggregate user's rate limits
      const totalRequests = userLimits.reduce((sum, [, limit]) => sum + limit.count, 0);
      const maxRequests = userLimits.reduce((max, [, limit]) => Math.max(max, limit.maxRequests), 0);
      const earliestReset = userLimits.reduce((earliest, [, limit]) => 
        earliest < limit.resetTime ? earliest : limit.resetTime, new Date().getTime()
      );

      return {
        action: 'aggregated',
        limit: maxRequests,
        remaining: Math.max(0, maxRequests - totalRequests),
        resetTime: new Date(earliestReset),
        isBlocked: totalRequests >= maxRequests,
      };
    } catch (error) {
      console.error('Get rate limit status error:', error);
      return {
        action: 'error',
        limit: 0,
        remaining: 0,
        resetTime: new Date(),
        isBlocked: false,
      };
    }
  }

  // Permission methods
  hasChatPermission(permission: string, user?: User): boolean {
    if (!user) {
      return false;
    }

    return user.permissions?.includes(permission) || false;
  }

  hasAnyChatPermission(permissions: string[], user?: User): boolean {
    if (!user) {
      return false;
    }

    return permissions.some(permission => user.permissions?.includes(permission) || false);
  }

  hasAllChatPermissions(permissions: string[], user?: User): boolean {
    if (!user) {
      return false;
    }

    return permissions.every(permission => user.permissions?.includes(permission) || false);
  }

  async getChatPermissions(user?: User): Promise<string[]> {
    try {
      if (!user) {
        return [];
      }

      const response = await fetch(`${this.baseUrl}/auth/permissions/${user.userId}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${this.getToken()}`,
        },
      });

      if (!response.ok) {
        return user.permissions || [];
      }

      const data = await response.json();
      return data.permissions || [];
    } catch (error) {
      console.error('Get permissions error:', error);
      return user?.permissions || [];
    }
  }

  // Utility methods
  private getToken(): string {
    if (typeof window === 'undefined') {
      return '';
    }

    return localStorage.getItem(this.tokenStorageKey) || '';
  }

  private setToken(token: string): void {
    if (typeof window === 'undefined') {
      return;
    }

    localStorage.setItem(this.tokenStorageKey, token);
  }

  private clearToken(): void {
    if (typeof window === 'undefined') {
      return;
    }

    localStorage.removeItem(this.tokenStorageKey);
  }

  private getChatSessions(): ChatSession[] {
    if (typeof window === 'undefined') {
      return [];
    }

    const sessions = localStorage.getItem(this.chatSessionStorageKey);
    return sessions ? JSON.parse(sessions) : [];
  }

  private setChatSessions(sessions: ChatSession[]): void {
    if (typeof window === 'undefined') {
      return;
    }

    localStorage.setItem(this.chatSessionStorageKey, JSON.stringify(sessions));
  }

  private clearChatSessions(): void {
    if (typeof window === 'undefined') {
      return;
    }

    localStorage.removeItem(this.chatSessionStorageKey);
  }

  private getRateLimits(): Record<string, RateLimit> {
    if (typeof window === 'undefined') {
      return {};
    }

    const limits = localStorage.getItem(this.rateLimitStorageKey);
    return limits ? JSON.parse(limits) : {};
  }

  private setRateLimits(limits: Record<string, RateLimit>): void {
    if (typeof window === 'undefined') {
      return;
    }

    localStorage.setItem(this.rateLimitStorageKey, JSON.stringify(limits));
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private getMaxRequests(action: string): number {
    const limits: Record<string, number> = {
      'login': 5,
      'message': 100,
      'conversation': 50,
      'file_upload': 10,
      'search': 30,
      'admin': 20,
    };

    return limits[action] || 10;
  }

  private async getClientIP(): Promise<string> {
    try {
      const response = await fetch('https://api.ipify.org?format=json');
      const data = await response.json();
      return data.ip || 'unknown';
    } catch (error) {
      console.error('Failed to get client IP:', error);
      return 'unknown';
    }
  }
}

// Create and export the service instance
export const chatAuthService = new ChatAuthServiceImpl();

// Default export
export default chatAuthService;
