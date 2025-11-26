/**
 * Copilot Service - Standardized service for Copilot functionality
 * Integrates with ChatService and CopilotGateway to provide a unified interface
 */

import { enhancedApiClient } from '@/lib/enhanced-api-client';
import { getServiceErrorHandler } from './errorHandler';
import { generateUUID } from '@/lib/uuid';
import { CopilotGateway, CopilotBackendRequest, CopilotBackendResponse } from '@/components/copilot-chat/services/copilotGateway';
import { ChatService } from './chatService';
import type { ChatMessage, KarenSettings } from '@/lib/types';
import type {
  CopilotSuggestion,
  CopilotAction,
  CopilotWorkflow,
  CopilotArtifact
} from '@/components/copilot-chat/types/copilot';

export interface ProcessCopilotInputOptions {
  userId?: string;
  sessionId?: string;
  preferredLLMProvider?: string;
  preferredModel?: string;
}

export interface CopilotResponse {
  response: string;
  suggestions: CopilotSuggestion[];
  actions: CopilotAction[];
  workflows: CopilotWorkflow[];
  artifacts: CopilotArtifact[];
}

export class CopilotService {
  private apiClient = enhancedApiClient;
  private errorHandler = getServiceErrorHandler();
  private chatService: ChatService;
  private copilotGateway: CopilotGateway;

  constructor() {
    this.chatService = new ChatService();
    this.copilotGateway = new CopilotGateway({
      baseUrl: 'http://localhost:8000',
      userId: 'default-user',
      sessionId: 'default-session'
    });
  }

  /**
   * Process user input with Copilot intelligence
   */
  async processInput(
    input: string,
    conversationHistory: ChatMessage[],
    settings: KarenSettings,
    options: ProcessCopilotInputOptions = {}
  ): Promise<CopilotResponse> {
    return this.errorHandler.withRetryAndFallback(
      async () => {
        const sessionId = options.sessionId || generateUUID();
        
        // First, process the message through ChatService
        await this.chatService.processUserMessage(
          input,
          conversationHistory,
          settings,
          {
            sessionId,
            userId: options.userId || 'default-user',
            preferredLLMProvider: options.preferredLLMProvider,
            preferredModel: options.preferredModel
          }
        );
        
        // Create backend request for CopilotGateway
        const backendRequest: CopilotBackendRequest = {
          user_id: options.userId || 'default-user',
          message: input,
          top_k: 6,
          context: {
            viewId: 'copilot-chat',
            interfaceMode: 'chat',
            activePanel: 'chat',
            client: 'web',
            capabilities: ['text', 'code', 'image', 'audio'],
            intent: 'chat'
          }
        };
        
        // Send request to Copilot backend
        const backendResponse: CopilotBackendResponse = await this.copilotGateway.send(backendRequest);
        
        // Transform backend response to CopilotResponse format
        return {
          response: backendResponse.answer,
          suggestions: this.transformBackendSuggestions(backendResponse),
          actions: this.transformBackendActions(backendResponse.actions),
          workflows: this.transformBackendWorkflows(backendResponse),
          artifacts: this.transformBackendArtifacts(backendResponse)
        };
      },
      {
        response: "I'm experiencing some technical difficulties right now. Please try again in a moment.",
        suggestions: [],
        actions: [],
        workflows: [],
        artifacts: []
      },
      {
        service: 'CopilotService',
        method: 'processInput',
        endpoint: '/copilot/assist'
      }
    );
  }

  /**
   * Execute an action
   */
  async executeAction(actionId: string): Promise<boolean> {
    try {
      // Execute action through CopilotGateway
      const result = await this.copilotGateway.executePlugin({
        pluginId: 'system',
        action: actionId,
        context: {
          sessionId: 'default-session',
          userId: 'default-user'
        }
      });
      
      return result.success;
    } catch (error) {
      console.error('Error executing action:', error);
      return false;
    }
  }

  /**
   * Execute a workflow
   */
  async executeWorkflow(workflowId: string): Promise<boolean> {
    try {
      // Execute workflow through CopilotGateway
      const result = await this.copilotGateway.executePlugin({
        pluginId: 'system',
        action: workflowId,
        context: {
          sessionId: 'default-session',
          userId: 'default-user'
        }
      });
      
      return result.success;
    } catch (error) {
      console.error('Error executing workflow:', error);
      return false;
    }
  }

  /**
   * Generate an artifact
   */
  async generateArtifact(artifactId: string): Promise<CopilotArtifact | null> {
    try {
      // Generate artifact through CopilotGateway
      const result = await this.copilotGateway.executePlugin({
        pluginId: 'system',
        action: `generate_${artifactId}`,
        context: {
          sessionId: 'default-session',
          userId: 'default-user'
        }
      });
      
      if (result.success && result.result) {
        return result.result as CopilotArtifact;
      }
      
      return null;
    } catch (error) {
      console.error('Error generating artifact:', error);
      return null;
    }
  }

  /**
   * Get available LNMs
   */
  async getAvailableLNMs() {
    try {
      return await this.copilotGateway.getAvailableLNMs();
    } catch (error) {
      console.error('Error getting available LNMs:', error);
      return [];
    }
  }

  /**
   * Select an LNM
   */
  async selectLNM(modelId: string) {
    try {
      return await this.copilotGateway.selectLNM({
        modelId,
        context: {
          conversationId: 'default-conversation',
          taskType: 'chat'
        }
      });
    } catch (error) {
      console.error('Error selecting LNM:', error);
      return { success: false, error: String(error) };
    }
  }

  /**
   * Get available plugins
   */
  async getAvailablePlugins() {
    try {
      return await this.copilotGateway.getAvailablePlugins();
    } catch (error) {
      console.error('Error getting available plugins:', error);
      return [];
    }
  }

  /**
   * Get security context
   */
  async getSecurityContext() {
    try {
      return await this.copilotGateway.getSecurityContext();
    } catch (error) {
      console.error('Error getting security context:', error);
      return {
        userRoles: [],
        securityMode: 'safe' as const,
        canAccessSensitive: false,
        redactionLevel: 'none' as const
      };
    }
  }

  /**
    * Toggle a plugin
    */
  async togglePlugin(pluginId: string, enabled: boolean): Promise<boolean> {
    try {
      // Toggle plugin through CopilotGateway
      const result = await this.copilotGateway.executePlugin({
        pluginId,
        action: enabled ? 'enable' : 'disable',
        context: {
          sessionId: 'default-session',
          userId: 'default-user'
        }
      });
      
      return result.success;
    } catch (error) {
      console.error('Error toggling plugin:', error);
      return false;
    }
  }

  /**
    * Record a telemetry event
    */
  async recordTelemetryEvent(eventName: string, properties?: Record<string, unknown>) {
    try {
      await this.copilotGateway.recordTelemetryEvent({
        eventName,
        properties,
        timestamp: new Date()
      });
    } catch (error) {
      console.error('Error recording telemetry event:', error);
    }
  }

  /**
   * Flush all telemetry data
   */
  async flushTelemetry() {
    try {
      await this.copilotGateway.flushAll();
    } catch (error) {
      console.error('Error flushing telemetry data:', error);
    }
  }

  /**
   * Transform backend actions to frontend actions format
   */
  private transformBackendActions(backendActions: Array<{
    type: string;
    params: Record<string, unknown>;
    confidence: number;
    description?: string;
  }>): CopilotAction[] {
    const actions: CopilotAction[] = [];
    
    if (backendActions) {
      backendActions.forEach((action, index) => {
        actions.push({
          id: `action_${index}`,
          pluginId: 'system',
          title: action.description || action.type,
          description: action.description || 'Execute this action',
          riskLevel: 'safe',
          requiresConfirmation: false,
          config: action.params || {}
        });
      });
    }
    
    // Add a general action if none from backend
    if (actions.length === 0) {
      actions.push({
        id: 'action_general',
        pluginId: 'system',
        title: 'Learn More',
        description: 'Explore related topics and best practices',
        riskLevel: 'safe',
        requiresConfirmation: false,
        config: {}
      });
    }
    
    return actions;
  }

  /**
   * Transform backend suggestions to frontend format
   */
  private transformBackendSuggestions(backendResponse: CopilotBackendResponse): CopilotSuggestion[] {
    const suggestions: CopilotSuggestion[] = [];
    
    if (backendResponse.actions) {
      backendResponse.actions.forEach((action, index) => {
        suggestions.push({
          id: `suggestion_${index}`,
          type: 'action',
          title: action.description || 'Action',
          description: action.description || 'Execute this action',
          confidence: 0.8,
          priority: 'medium',
          data: {
            id: `action_${index}`,
            action: `action_${index}`
          }
        });
      });
    }
    
    // Add a general suggestion if none from backend
    if (suggestions.length === 0) {
      suggestions.push({
        id: 'suggestion_general',
        type: 'response',
        title: 'Learn More',
        description: 'Explore related topics and best practices',
        confidence: 0.6,
        priority: 'low',
        data: {
          topic: 'general'
        }
      });
    }
    
    return suggestions;
  }

  /**
   * Transform backend workflows to frontend format
   */
  private transformBackendWorkflows(_backendResponse: CopilotBackendResponse): CopilotWorkflow[] {
    // Backend doesn't return workflows in the current format
    return [];
  }

  /**
   * Transform backend artifacts to frontend format
   */
  private transformBackendArtifacts(_backendResponse: CopilotBackendResponse): CopilotArtifact[] {
    // Backend doesn't return artifacts in the current format
    return [];
  }
}

let copilotService: CopilotService | null = null;
export function getCopilotService(): CopilotService {
  if (!copilotService) {
    copilotService = new CopilotService();
  }
  return copilotService;
}
export function initializeCopilotService(): CopilotService {
  copilotService = new CopilotService();
  return copilotService;
}
