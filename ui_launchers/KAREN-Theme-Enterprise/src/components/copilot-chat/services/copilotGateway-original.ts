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

export interface CopilotAction {
  id: string;
  pluginId: string;
  title: string;
  description: string;
  riskLevel: 'safe' | 'privileged' | 'evil-mode-only';
  config?: Record<string, unknown>;
}

export interface CopilotWorkflowSummary {
  id: string;
  name: string;
  pluginId: string;
  description: string;
  steps: string[];
  estimatedTime: number;
  riskLevel: 'safe' | 'privileged' | 'evil-mode-only';
}

export interface CopilotArtifactSummary {
  id: string;
  title: string;
  pluginId: string;
  type: 'code' | 'documentation' | 'analysis' | 'test';
  description: string;
  riskLevel: 'safe' | 'privileged' | 'evil-mode-only';
}

export interface PluginExecutionRequest {
  pluginId: string;
  action: string;
  parameters?: Record<string, unknown>;
  context: {
    sessionId: string;
    userId: string;
  };
}

export interface PluginExecutionResponse {
  success: boolean;
  result?: unknown;
  error?: string;
}

export interface LNMSelectionRequest {
  modelId: string;
  context: {
    conversationId: string;
    taskType: string;
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

export interface PluginManifest {
  id: string;
  name: string;
  description: string;
  version: string;
  author: string;
  enabled: boolean;
  capabilities: string[];
  riskLevel: 'safe' | 'privileged' | 'evil-mode-only';
  config?: Record<string, unknown>;
}

export interface SecurityContext {
  userRoles: string[];
  securityMode: 'safe' | 'aggressive' | 'evil';
  canAccessSensitive: boolean;
  redactionLevel: 'none' | 'partial' | 'full';
}

export interface TelemetryEvent {
  eventName: string;
  properties?: Record<string, unknown>;
  timestamp?: Date;
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
    return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
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
    // Use frontend API routes for development compatibility, direct backend for production
    const isDevelopment = process.env.NODE_ENV === 'development' || process.env.NEXT_PUBLIC_ENABLE_DEVELOPMENT_FEATURES === 'true';
    const url = isDevelopment ? `${this.baseUrl}/api/copilot/assist` : `${this.getBackendUrl()}/api/copilot/assist`;
    
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
      console.error('[CopilotGateway] Error sending request to Copilot backend:', error);
      const errorObj = error instanceof Error ? error : new Error(String(error));
      console.error(`[CopilotGateway] Error details:`, {
        name: errorObj.name,
        message: errorObj.message,
        code: (errorObj as any).code,
        status: (errorObj as any).status,
        url: url,
        isDevelopment
      });
      throw errorObj;
    }
  }

  /**
   * Execute a plugin action
   */
  public async executePlugin(request: PluginExecutionRequest): Promise<PluginExecutionResponse> {
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
      const response = await enhancedApiClient.post<PluginExecutionResponse>(url, request, { headers });

      return response.data;
    } catch (error) {
      console.error('Error executing plugin:', error);
      const errorObj = error instanceof Error ? error : new Error(String(error));
      throw errorObj;
    }
  }

  /**
   * Select an LNM (Local Neural Model)
   */
  public async selectLNM(request: LNMSelectionRequest): Promise<LNMSelectionResponse> {
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
      const response = await enhancedApiClient.post<LNMSelectionResponse>(url, request, { headers });

      return response.data;
    } catch (error) {
      console.error('Error selecting LNM:', error);
      const errorObj = error instanceof Error ? error : new Error(String(error));
      throw errorObj;
    }
  }

  /**
   * Get available LNMs
   */
  public async getAvailableLNMs(): Promise<LNMInfo[]> {
    // Use frontend API routes for development compatibility, direct backend for production
    const isDevelopment = process.env.NODE_ENV === 'development' || process.env.NEXT_PUBLIC_ENABLE_DEVELOPMENT_FEATURES === 'true';
    const url = isDevelopment ? `${this.baseUrl}/api/copilot/lnm/list` : `${this.getBackendUrl()}/api/copilot/lnm/list`;
    
    const headers: Record<string, string> = {
      'X-Kari-User-ID': this.config.userId,
      'X-Kari-Session-ID': this.config.sessionId,
      'X-Correlation-ID': this.correlationId,
    };

    if (this.config.apiKey) {
      headers['Authorization'] = `Bearer ${this.config.apiKey}`;
    }

    try {
      const response = await enhancedApiClient.get<LNMInfo[]>(url, { headers });

      return response.data;
    } catch (error) {
      console.error('Error fetching available LNMs:', error);
      const errorObj = error instanceof Error ? error : new Error(String(error));
      throw errorObj;
    }
  }

  /**
   * Get available plugins
   */
  public async getAvailablePlugins(): Promise<PluginManifest[]> {
    // Use frontend API routes for development compatibility, direct backend for production
    const isDevelopment = process.env.NODE_ENV === 'development' || process.env.NEXT_PUBLIC_ENABLE_DEVELOPMENT_FEATURES === 'true';
    const url = isDevelopment ? `${this.baseUrl}/api/copilot/plugins/list` : `${this.getBackendUrl()}/api/copilot/plugins/list`;
    
    const headers: Record<string, string> = {
      'X-Kari-User-ID': this.config.userId,
      'X-Kari-Session-ID': this.config.sessionId,
      'X-Correlation-ID': this.correlationId,
    };

    if (this.config.apiKey) {
      headers['Authorization'] = `Bearer ${this.config.apiKey}`;
    }

    try {
      const response = await enhancedApiClient.get<PluginManifest[]>(url, { headers });

      return response.data;
    } catch (error) {
      console.error('Error fetching available plugins:', error);
      const errorObj = error instanceof Error ? error : new Error(String(error));
      throw errorObj;
    }
  }

  /**
   * Get security context
   */
  public async getSecurityContext(): Promise<SecurityContext> {
    // Use frontend API routes for development compatibility, direct backend for production
    const isDevelopment = process.env.NODE_ENV === 'development' || process.env.NEXT_PUBLIC_ENABLE_DEVELOPMENT_FEATURES === 'true';
    const url = isDevelopment ? `${this.baseUrl}/api/copilot/security/context` : `${this.getBackendUrl()}/api/copilot/security/context`;
    
    const headers: Record<string, string> = {
      'X-Kari-User-ID': this.config.userId,
      'X-Kari-Session-ID': this.config.sessionId,
      'X-Correlation-ID': this.correlationId,
    };

    if (this.config.apiKey) {
      headers['Authorization'] = `Bearer ${this.config.apiKey}`;
    }

    try {
      const response = await enhancedApiClient.get<SecurityContext>(url, { headers });

      return response.data;
    } catch (error) {
      console.error('Error fetching security context:', error);
      const errorObj = error instanceof Error ? error : new Error(String(error));
      throw errorObj;
    }
  }

  /**
   * Record a telemetry event
   */
  public async recordTelemetryEvent(event: TelemetryEvent): Promise<void> {
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