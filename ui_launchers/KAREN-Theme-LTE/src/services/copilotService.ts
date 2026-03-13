/**
 * Copilot Service
 * Provides core Copilot functionality and API integration
 */

export interface CopilotMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant' | 'system';
  timestamp: Date;
  metadata?: {
    modality?: 'text' | 'code' | 'image' | 'audio';
    intent?: string;
    confidence?: number;
    suggestions?: CopilotSuggestion[];
    actions?: CopilotAction[];
    workflows?: CopilotWorkflow[];
    artifacts?: CopilotArtifact[];
  };
}

export interface CopilotSuggestion {
  id: string;
  title: string;
  description: string;
  category?: string;
  priority?: 'low' | 'medium' | 'high';
}

export interface CopilotAction {
  id: string;
  title: string;
  description: string;
  category?: string;
  icon?: string;
  riskLevel?: 'safe' | 'medium' | 'high' | 'critical';
}

export interface CopilotWorkflow {
  id: string;
  title: string;
  description?: string;
  steps?: string[];
  estimatedTime?: number;
  pluginId?: string;
  riskLevel?: 'safe' | 'medium' | 'high' | 'critical';
}

export interface CopilotArtifact {
  id: string;
  title: string;
  type: 'text' | 'code' | 'image' | 'audio' | 'other';
  description?: string;
  content?: string;
  pluginId?: string;
  riskLevel?: 'safe' | 'medium' | 'high' | 'critical';
}

export interface CopilotResponse {
  response: string;
  suggestions?: CopilotSuggestion[];
  actions?: CopilotAction[];
  workflows?: CopilotWorkflow[];
  artifacts?: CopilotArtifact[];
}

export interface KarenSettings {
  theme?: 'light' | 'dark' | 'auto';
  fontSize?: 'small' | 'medium' | 'large';
  enableAnimations?: boolean;
  enableSoundEffects?: boolean;
}

export interface LNMInfo {
  id: string;
  name: string;
  description: string;
  capabilities: string[];
  version?: string;
  size?: number;
  isActive?: boolean;
  isPersonal?: boolean;
}

export interface PluginManifest {
  id: string;
  name: string;
  version: string;
  description: string;
  author?: string;
  enabled: boolean;
  capabilities: string[];
  riskLevel?: 'safe' | 'medium' | 'high' | 'critical';
  config?: {
    parameters?: PluginParameterConfig[];
  };
}

export interface PluginParameterConfig {
  name: string;
  type: string;
  description: string;
  required: boolean;
  defaultValue?: unknown;
}

export interface SecurityContext {
  userRoles: string[];
  securityMode: 'safe' | 'medium' | 'high' | 'critical';
  canAccessSensitive: boolean;
  redactionLevel: 'none' | 'partial' | 'full';
}

class CopilotService {
  private baseUrl: string;
  private apiKey?: string;
  private userId: string;
  private sessionId: string;

  constructor(config: { baseUrl: string; apiKey?: string; userId: string; sessionId: string }) {
    this.baseUrl = config.baseUrl;
    this.apiKey = config.apiKey;
    this.userId = config.userId;
    this.sessionId = config.sessionId;
  }

  async processInput(
    input: string, 
    history: CopilotMessage[], 
    settings: KarenSettings,
    context?: { userId?: string; sessionId?: string }
  ): Promise<CopilotResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/api/copilot/process`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(this.apiKey && { 'Authorization': `Bearer ${this.apiKey}` })
        },
        body: JSON.stringify({
          input,
          history,
          settings,
          context: {
            userId: context?.userId || this.userId,
            sessionId: context?.sessionId || this.sessionId
          }
        })
      });

      if (!response.ok) {
        throw new Error(`Copilot service error: ${response.statusText}`);
      }

      return await response.json() as CopilotResponse;
    } catch (error) {
      throw new Error(`Failed to process input: ${error}`);
    }
  }

  async executeAction(actionId: string): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/api/copilot/action/${actionId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': this.apiKey ? `Bearer ${this.apiKey}` : undefined
        } as HeadersInit
      });

      return response.ok;
    } catch (error) {
      throw new Error(`Failed to execute action: ${error}`);
    }
  }

  async executeWorkflow(workflowId: string): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/api/copilot/workflow/${workflowId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': this.apiKey ? `Bearer ${this.apiKey}` : undefined
        } as HeadersInit
      });

      return response.ok;
    } catch (error) {
      throw new Error(`Failed to execute workflow: ${error}`);
    }
  }

  async generateArtifact(artifactId: string): Promise<string | null> {
    try {
      const response = await fetch(`${this.baseUrl}/api/copilot/artifact/${artifactId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': this.apiKey ? `Bearer ${this.apiKey}` : undefined
        } as HeadersInit
      });

      if (!response.ok) {
        throw new Error(`Failed to generate artifact: ${response.statusText}`);
      }

      const result = await response.json();
      return result.content || null;
    } catch (error) {
      throw new Error(`Failed to generate artifact: ${error}`);
    }
  }

  async getSecurityContext(): Promise<SecurityContext> {
    try {
      const response = await fetch(`${this.baseUrl}/api/copilot/security`, {
        method: 'GET',
        headers: {
          'Authorization': this.apiKey ? `Bearer ${this.apiKey}` : undefined
        } as HeadersInit
      });

      if (!response.ok) {
        throw new Error(`Failed to get security context: ${response.statusText}`);
      }

      return await response.json() as SecurityContext;
    } catch (error) {
      throw new Error(`Failed to get security context: ${error}`);
    }
  }

  async getAvailableLNMs(): Promise<LNMInfo[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/copilot/lnms`, {
        method: 'GET',
        headers: {
          'Authorization': this.apiKey ? `Bearer ${this.apiKey}` : undefined
        } as HeadersInit
      });

      if (!response.ok) {
        throw new Error(`Failed to get available LNMs: ${response.statusText}`);
      }

      return await response.json() as LNMInfo[];
    } catch (error) {
      throw new Error(`Failed to get available LNMs: ${error}`);
    }
  }

  async selectLNM(modelId: string): Promise<{ success: boolean; error?: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/api/copilot/lnm/${modelId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': this.apiKey ? `Bearer ${this.apiKey}` : undefined
        } as HeadersInit
      });

      if (!response.ok) {
        return { success: false, error: response.statusText };
      }

      return { success: true };
    } catch (error) {
      return { success: false, error: String(error) };
    }
  }

  async getAvailablePlugins(): Promise<PluginManifest[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/copilot/plugins`, {
        method: 'GET',
        headers: {
          'Authorization': this.apiKey ? `Bearer ${this.apiKey}` : undefined
        } as HeadersInit
      });

      if (!response.ok) {
        throw new Error(`Failed to get available plugins: ${response.statusText}`);
      }

      return await response.json() as PluginManifest[];
    } catch (error) {
      throw new Error(`Failed to get available plugins: ${error}`);
    }
  }

  async togglePlugin(pluginId: string, enabled: boolean): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/api/copilot/plugin/${pluginId}/toggle`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(this.apiKey && { 'Authorization': `Bearer ${this.apiKey}` })
        } as HeadersInit,
        body: JSON.stringify({ enabled })
      });

      return response.ok;
    } catch (error) {
      throw new Error(`Failed to toggle plugin: ${error}`);
    }
  }
}

let copilotServiceInstance: CopilotService | null = null;

export const getCopilotService = (): CopilotService => {
  if (!copilotServiceInstance) {
    // Default configuration - in production, these would come from environment
    copilotServiceInstance = new CopilotService({
      baseUrl: process.env.NODE_ENV === 'production' 
        ? 'https://api.karen.ai' 
        : 'http://localhost:3001',
      userId: 'default-user',
      sessionId: 'default-session'
    });
  }
  return copilotServiceInstance;
};

export default CopilotService;