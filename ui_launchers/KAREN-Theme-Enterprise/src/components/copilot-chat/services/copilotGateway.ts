/**
 * CopilotGateway - Bridge to KAREN's CORTEX engine
 * Implements the frontend-backend contract for the Copilot-First Unified Chat Surface
 */

import { enhancedApiClient } from '@/lib/base-api-client';

export interface CopilotBackendConfig {
  baseUrl: string;
  apiKey?: string;               // for non-local deployments / org RBAC
  correlationId?: string;
  userId: string;
  sessionId: string;
}

export interface CopilotBackendRequest {
  user_id: string;
  message: string;
  top_k?: number;
  action?: string;
  context?: {
    viewId?: string;
    interfaceMode?: string;
    activePanel?: string;
    client?: string;
    capabilities?: string[];
    intent?: string;
  };
}

export interface CopilotBackendResponse {
  answer: string;
  context: Array<{
    id: string;
    text: string;
    preview?: string;
    score: number;
    tags: string[];
    recency?: string;
    meta: Record<string, unknown>;
    importance: number;
    decay_tier: string;
    created_at: string;
    updated_at?: string;
    user_id: string;
    org_id?: string;
  }>;
  actions: Array<{
    type: string;
    params: Record<string, unknown>;
    confidence: number;
    description?: string;
  }>;
  timings: Record<string, number | boolean>;
  correlation_id: string;
}

export interface PluginManifest {
  id: string;
  name: string;
  description: string;
  version: string;
  author: string;
  enabled: boolean;
  capabilities: string[];
  riskLevel: 'safe' | 'privileged' | 'evil-mode-only';
  config?: {
    parameters: {
      name: string;
      type: string;
      description: string;
      required: boolean;
      defaultValue?: unknown;
    }[];
  };
}

export interface LNMSelectionResponse {
  success: boolean;
  model?: {
    id: string;
    name: string;
    description: string;
    capabilities: string[];
  };
  error?: string;
}

export interface LNMInfo {
  id: string;
  name: string;
  description: string;
  capabilities: string[];
  isPersonal: boolean;
}

export interface SecurityContext {
  userRoles: string[];
  securityMode: 'safe' | 'aggressive' | 'evil';
  canAccessSensitive: boolean;
  redactionLevel: 'none' | 'partial' | 'full';
}

/**
 * CopilotGateway - Bridge to KAREN's CORTEX engine
 * Handles all communication between frontend and backend
 */
export class CopilotGateway {
  private config: CopilotBackendConfig;
  private correlationId: string;
  private baseUrl: string;

  constructor(config: CopilotBackendConfig) {
    this.config = config;
    this.correlationId = config.correlationId || this.generateCorrelationId();
    // Use frontend API routes instead of direct backend URL
    this.baseUrl = this.getFrontendApiUrl();
  }

  private getFrontendApiUrl(): string {
    if (typeof window !== 'undefined') {
      return window.location.origin;
    }
    return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  }

  private getBackendUrl(): string {
    // Use the configured backend URL with fallback to localhost:8000
    return this.config.baseUrl || process.env.NEXT_PUBLIC_KAREN_BACKEND_URL || process.env.KAREN_BACKEND_URL || 'http://localhost:8000';
  }

  /**
   * Generate a correlation ID for request tracking
   */
  private generateCorrelationId(): string {
    return `corr_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get the current correlation ID
   */
  public getCorrelationId(): string {
    return this.correlationId;
  }

  /**
   * Send a chat request to the backend
   */
  public async send(request: CopilotBackendRequest): Promise<CopilotBackendResponse> {
    // Always use frontend API routes in development for better compatibility
    const isDevelopment = process.env.NODE_ENV === 'development' || process.env.NEXT_PUBLIC_ENABLE_DEVELOPMENT_FEATURES === 'true';
    
    // For development, always use frontend API routes to avoid backend connectivity issues
    let url: string;
    if (isDevelopment) {
      url = `${this.getFrontendApiUrl()}/api/copilot/assist`;
    } else {
      // In production, try direct backend first, then fallback to frontend API routes
      url = `${this.getBackendUrl()}/api/copilot/assist`;
    }
    
    const headers: Record<string, string> = {
      'X-Kari-User-ID': this.config.userId,
      'X-Kari-Session-ID': this.config.sessionId,
      'X-Correlation-ID': this.correlationId,
    };

    if (this.config.apiKey) {
      headers['Authorization'] = `Bearer ${this.config.apiKey}`;
    }

    try {
      console.log(`[CopilotGateway] Sending request to: ${url}`);
      console.log(`[CopilotGateway] Request payload:`, request);
      console.log(`[CopilotGateway] Headers:`, headers);
      console.log(`[CopilotGateway] Environment check - isDevelopment: ${isDevelopment}, NODE_ENV: ${process.env.NODE_ENV}, NEXT_PUBLIC_ENABLE_DEVELOPMENT_FEATURES: ${process.env.NEXT_PUBLIC_ENABLE_DEVELOPMENT_FEATURES}`);
      
      const response = await enhancedApiClient.post<CopilotBackendResponse>(url, request, { headers });
      
      console.log(`[CopilotGateway] Response status: ${response.status}`);
      console.log(`[CopilotGateway] Response data:`, response.data);
      
      return response.data;
    } catch (error) {
      const errorObj = error instanceof Error ? error : new Error(String(error));
      console.error('[CopilotGateway] Error sending request to Copilot backend:', errorObj);
      console.error(`[CopilotGateway] Error details:`, {
        name: errorObj.name,
        message: errorObj.message,
        code: (errorObj as any).code,
        status: (errorObj as any).status,
        url: url,
        isDevelopment
      });
      
      // Enhanced error handling with multiple fallback strategies
      const fallbackStrategies = [
        // Strategy 1: Try frontend API routes if not already using them
        () => {
          if (isDevelopment && !url.includes('/api/copilot/assist')) {
            console.log('[CopilotGateway] Strategy 1: Retrying with frontend API routes as fallback');
            const fallbackUrl = `${this.getFrontendApiUrl()}/api/copilot/assist`;
            return enhancedApiClient.post<CopilotBackendResponse>(fallbackUrl, request, { headers });
          }
          return null;
        },
        // Strategy 2: Try direct backend with different port
        () => {
          if (url.includes('8010') || url.includes('8011')) {
            console.log('[CopilotGateway] Strategy 2: Retrying with correct backend port 8000');
            const correctedUrl = url.replace(/:801[01]/, ':8000');
            return enhancedApiClient.post<CopilotBackendResponse>(correctedUrl, request, { headers });
          }
          return null;
        },
        // Strategy 3: Try localhost if current URL is not localhost
        () => {
          if (!url.includes('localhost') && !url.includes('127.0.0.1')) {
            console.log('[CopilotGateway] Strategy 3: Retrying with localhost:8000');
            const localhostUrl = 'http://localhost:8000/api/copilot/assist';
            return enhancedApiClient.post<CopilotBackendResponse>(localhostUrl, request, { headers });
          }
          return null;
        }
      ];

      // Try each fallback strategy
      for (let i = 0; i < fallbackStrategies.length; i++) {
        try {
          const fallbackResult = fallbackStrategies[i]();
          if (fallbackResult) {
            const fallbackResponse = await fallbackResult;
            console.log(`[CopilotGateway] Strategy ${i + 1} succeeded with status: ${fallbackResponse.status}`);
            return fallbackResponse.data;
          }
        } catch (fallbackError) {
          console.warn(`[CopilotGateway] Strategy ${i + 1} failed:`, fallbackError);
          // Continue to next strategy
        }
      }
      
      // If all strategies fail, return a degraded response instead of throwing
      console.error('[CopilotGateway] All fallback strategies failed, returning degraded response');
      return {
        answer: "I'm experiencing connectivity issues. Please check your network connection and ensure the backend service is running on port 8000. You can try refreshing the page or contacting support if the issue persists.",
        context: [],
        actions: [{
          type: "retry_request",
          params: { originalRequest: request },
          confidence: 0.8,
          description: "Retry the request when connectivity is restored"
        }],
        timings: {
          total_ms: 0,
          degraded_mode: true,
          network_error: true
        },
        correlation_id: this.correlationId
      };
    }
  }

  /**
   * Execute a plugin action
   */
  public async executePlugin(request: { pluginId: string; action: string; parameters?: Record<string, unknown>; context: { sessionId: string; userId: string } }): Promise<{ success: boolean; result?: unknown; error?: string }> {
    // Use frontend API routes for development compatibility, direct backend for production
    const isDevelopment = process.env.NODE_ENV === 'development' || process.env.NEXT_PUBLIC_ENABLE_DEVELOPMENT_FEATURES === 'true';
    const url = isDevelopment ? `${this.baseUrl}/api/copilot/plugins/execute` : `${this.getBackendUrl()}/api/copilot/plugins/execute`;
    
    const headers: Record<string, string> = {
      'X-Kari-User-ID': this.config.userId,
      'X-Kari-Session-ID': this.config.sessionId,
      'X-Correlation-ID': this.correlationId,
    };

    if (this.config.apiKey) {
      headers['Authorization'] = `Bearer ${this.config.apiKey}`;
    }

    try {
      const response = await enhancedApiClient.post(url, request, { headers });
      return {
        success: true,
        result: response.data
      };
    } catch (error) {
      const errorObj = error instanceof Error ? error : new Error(String(error));
      console.error('Error executing plugin:', errorObj);
      return {
        success: false,
        error: errorObj.message || 'Unknown error executing plugin'
      };
    }
  }

  /**
   * Select an LNM (Local Neural Model)
   */
  public async selectLNM(request: { modelId: string; context: { conversationId: string; taskType: string } }): Promise<{ success: boolean; model?: { id: string; name: string; description: string; capabilities: string[] }; error?: string }> {
    // Use frontend API routes for development compatibility, direct backend for production
    const isDevelopment = process.env.NODE_ENV === 'development' || process.env.NEXT_PUBLIC_ENABLE_DEVELOPMENT_FEATURES === 'true';
    const url = isDevelopment ? `${this.baseUrl}/api/copilot/lnm/select` : `${this.getBackendUrl()}/api/copilot/lnm/select`;
    
    const headers: Record<string, string> = {
      'X-Kari-User-ID': this.config.userId,
      'X-Kari-Session-ID': this.config.sessionId,
      'X-Correlation-ID': this.correlationId,
    };

    if (this.config.apiKey) {
      headers['Authorization'] = `Bearer ${this.config.apiKey}`;
    }

    try {
      const response = await enhancedApiClient.post(url, request, { headers });
      return {
        success: true,
        model: response.data as { id: string; name: string; description: string; capabilities: string[]; }
      };
    } catch (error) {
      const errorObj = error instanceof Error ? error : new Error(String(error));
      console.error('Error selecting LNM:', errorObj);
      return {
        success: false,
        error: errorObj.message || 'Unknown error selecting LNM'
      };
    }
  }

  /**
   * Get available LNMs
   */
  public async getAvailableLNMs(): Promise<LNMInfo[]> {
    // Use the existing /api/copilot/assist endpoint with action parameter
    return this.send({
      user_id: this.config.userId,
      message: '', // Empty message for action requests
      action: 'getLnmList',
      // Add any other parameters needed for LNM request
      context: {
        viewId: 'lnm'
      }
    }).then(response => {
      // Extract LNM list from the response
      const lnmContext = response.context?.find(item => item.id === 'lnm');
      return lnmContext && typeof lnmContext.text === 'string' ? JSON.parse(lnmContext.text) : [];
    }).catch(error => {
      console.error('Error fetching available LNMs:', error);
      throw error;
    });
  }

  /**
   * Get available plugins
   */
  public async getAvailablePlugins(): Promise<PluginManifest[]> {
    // Use the existing /api/copilot/assist endpoint with action parameter
    return this.send({
      user_id: this.config.userId,
      message: '', // Empty message for action requests
      action: 'getPlugins',
      // Add any other parameters needed for plugins request
      context: {
        viewId: 'plugins'
      }
    }).then(response => {
      // Extract plugins from the response
      const pluginsContext = response.context?.find(item => item.id === 'plugins');
      return pluginsContext && typeof pluginsContext.text === 'string' ? JSON.parse(pluginsContext.text) : [];
    }).catch(error => {
      console.error('Error fetching available plugins:', error);
      throw error;
    });
  }

  /**
   * Get security context
   */
  public async getSecurityContext(): Promise<SecurityContext> {
    // Use the existing /api/copilot/assist endpoint with action parameter
    return this.send({
      user_id: this.config.userId,
      message: '', // Empty message for action requests
      action: 'getSecurityContext',
      // Add any other parameters needed for security context request
      context: {
        viewId: 'security'
      }
    }).then(response => {
      // Extract security context from the response
      const securityContext = response.context?.find(item => item.id === 'security');
      return securityContext && typeof securityContext.text === 'string' ? JSON.parse(securityContext.text) : {
        userRoles: ['user'],
        securityMode: 'safe',
        canAccessSensitive: false,
        redactionLevel: 'partial'
      };
    }).catch(error => {
      console.error('Error fetching security context:', error);
      throw error;
    });
  }

  /**
   * Record a telemetry event
   */
  public async recordTelemetryEvent(event: { eventName: string; properties?: Record<string, unknown>; timestamp?: Date }): Promise<void> {
    // Use backend URL directly for telemetry
    const url = `${this.getBackendUrl()}/copilot/telemetry/event`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'X-Kari-User-ID': this.config.userId,
      'X-Kari-Session-ID': this.config.sessionId,
      'X-Correlation-ID': this.correlationId,
    };

    if (this.config.apiKey) {
      headers['Authorization'] = `Bearer ${this.config.apiKey}`;
    }

    try {
      const payload = {
        eventName: event.eventName,
        properties: event.properties,
        timestamp: event.timestamp || new Date(),
      };

      await enhancedApiClient.post(url, payload, { headers });
    } catch (error) {
      console.error('Error recording telemetry event:', error);
      // Don't throw to avoid disrupting the application flow
    }
  }

  /**
   * Flush all pending telemetry data
   */
  public async flushAll(): Promise<void> {
    // In a real implementation, this would flush any buffered telemetry events
    console.log('Flushing telemetry data');
    
    // Use backend URL directly for telemetry
    const url = `${this.getBackendUrl()}/copilot/telemetry/flush`;
    
    const headers: Record<string, string> = {
      'X-Kari-User-ID': this.config.userId,
      'X-Kari-Session-ID': this.config.sessionId,
      'X-Correlation-ID': this.correlationId,
    };

    if (this.config.apiKey) {
      headers['Authorization'] = `Bearer ${this.config.apiKey}`;
    }

    try {
      await enhancedApiClient.post(url, {}, { headers });
    } catch (error) {
      console.error('Error flushing telemetry data:', error);
      // Don't throw to avoid disrupting the application flow
    }
  }
}