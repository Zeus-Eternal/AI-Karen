/**
 * CopilotGateway - Bridge to KAREN's CORTEX engine
 * Implements the frontend-backend contract for the Copilot-First Unified Chat Surface
 */

import { enhancedApiClient } from '@/lib/enhanced-api-client';

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

  constructor(config: CopilotBackendConfig) {
    this.config = config;
    this.correlationId = config.correlationId || this.generateCorrelationId();
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
    const url = `${this.config.baseUrl}/copilot/assist`;
    
    const headers: Record<string, string> = {
      'X-Kari-User-ID': this.config.userId,
      'X-Kari-Session-ID': this.config.sessionId,
      'X-Correlation-ID': this.correlationId,
    };

    if (this.config.apiKey) {
      headers['Authorization'] = `Bearer ${this.config.apiKey}`;
    }

    try {
      const response = await enhancedApiClient.post<CopilotBackendResponse>(url, request, { headers });

      return response.data;
    } catch (error) {
      console.error('Error sending request to Copilot backend:', error);
      throw error;
    }
  }

  /**
   * Execute a plugin action
   */
  public async executePlugin(request: PluginExecutionRequest): Promise<PluginExecutionResponse> {
    const url = `${this.config.baseUrl}/copilot/plugins/execute`;
    
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
      throw error;
    }
  }

  /**
   * Select an LNM (Local Neural Model)
   */
  public async selectLNM(request: LNMSelectionRequest): Promise<LNMSelectionResponse> {
    const url = `${this.config.baseUrl}/copilot/lnm/select`;
    
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
      throw error;
    }
  }

  /**
   * Get available LNMs
   */
  public async getAvailableLNMs(): Promise<LNMInfo[]> {
    const url = `${this.config.baseUrl}/copilot/lnm/list`;
    
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
      throw error;
    }
  }

  /**
   * Get available plugins
   */
  public async getAvailablePlugins(): Promise<PluginManifest[]> {
    const url = `${this.config.baseUrl}/copilot/plugins/list`;
    
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
      throw error;
    }
  }

  /**
   * Get security context
   */
  public async getSecurityContext(): Promise<SecurityContext> {
    const url = `${this.config.baseUrl}/copilot/security/context`;
    
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
      throw error;
    }
  }

  /**
   * Record a telemetry event
   */
  public async recordTelemetryEvent(event: TelemetryEvent): Promise<void> {
    const url = `${this.config.baseUrl}/copilot/telemetry/event`;
    
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
    
    const url = `${this.config.baseUrl}/copilot/telemetry/flush`;
    
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