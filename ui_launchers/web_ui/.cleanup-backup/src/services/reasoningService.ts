/**
 * Reasoning Service - Connects to the backend reasoning system with fallbacks
 */
import { getConfigManager } from '@/lib/endpoint-config';
import { safeError } from '@/lib/safe-console';

export interface ReasoningRequest {
  input: string;
  context?: {
    user_id?: string;
    conversation_id?: string;
    [key: string]: any;
  };
}

export interface ReasoningResponse {
  success: boolean;
  response: {
    content: string;
    type: string;
    metadata?: {
      fallback_mode?: boolean;
      local_processing?: boolean;
      [key: string]: any;
    };
  };
  reasoning_method: string;
  fallback_used: boolean;
  errors?: {
    ai_error?: string;
    fallback_error?: string;
  };
}

class ReasoningService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = getConfigManager().getBackendUrl();
  }

  async analyze(request: ReasoningRequest): Promise<ReasoningResponse> {
    try {
      // Use the Next.js proxy route instead of direct backend URL
      const response = await fetch('/api/karen/api/reasoning/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      safeError('Reasoning service error:', error);
      
      // Return a fallback response
      return {
        success: true,
        response: {
          content: `I'm having trouble connecting to the reasoning system right now. However, I can see you're asking about: "${request.input}". I'm running in offline mode but still here to help as best I can.`,
          type: 'text',
          metadata: {
            fallback_mode: true,
            local_processing: true,
            connection_error: true,
          },
        },
        reasoning_method: 'client_fallback',
        fallback_used: true,
        errors: {
          ai_error: error instanceof Error ? error.message : 'Unknown error',
        },
      };
    }
  }

  async testConnection(): Promise<boolean> {
    try {
      // Use the Next.js proxy route instead of direct backend URL
      const response = await fetch('/api/health/degraded-mode');
      return response.ok;
    } catch {
      return false;
    }
  }

  async getSystemStatus(): Promise<any> {
    try {
      // Use the Next.js proxy route for degraded-mode health check
      const response = await fetch('/api/health/degraded-mode');
      if (response.ok) {
        const degradedModeData = await response.json();
        
        // Map the degraded mode response to the expected system status format
        return {
          degraded: degradedModeData.is_active,
          components: degradedModeData.infrastructure_issues || [],
          fallback_systems_active: degradedModeData.core_helpers_available?.fallback_responses || false,
          local_models_available: degradedModeData.core_helpers_available?.total_ai_capabilities || false,
          ai_status: degradedModeData.ai_status,
          failed_providers: degradedModeData.failed_providers || [],
          reason: degradedModeData.reason,
        };
      }
    } catch (error) {
      safeError('Failed to get system status:', error);
    }
    
    return {
      degraded: true,
      components: ['connection'],
      fallback_systems_active: true,
      local_models_available: false,
    };
  }
}

export const reasoningService = new ReasoningService();
export default reasoningService;