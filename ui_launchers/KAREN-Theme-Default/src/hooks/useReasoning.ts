/**
 * useReasoning Hook - React hook for the reasoning system
 */

import { useState, useCallback, useEffect } from 'react';
import { reasoningService, ReasoningRequest, ReasoningResponse } from '@/services/reasoningService';
import { safeError } from '@/lib/safe-console';

export interface UseReasoningReturn {
  analyze: (input: string, context?: any) => Promise<ReasoningResponse>;
  isLoading: boolean;
  error: string | null;
  lastResponse: ReasoningResponse | null;
  systemStatus: any;
  isConnected: boolean;
}

export function useReasoning(): UseReasoningReturn {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastResponse, setLastResponse] = useState<ReasoningResponse | null>(null);
  const [systemStatus, setSystemStatus] = useState<any>(null);
  const [isConnected, setIsConnected] = useState(false);

  // Check connection status on mount
  useEffect(() => {
    const checkConnection = async () => {
      try {
        const connected = await reasoningService.testConnection();
        setIsConnected(connected);
        
        if (connected) {
          const status = await reasoningService.getSystemStatus();
          setSystemStatus(status);
        }
      } catch (err) {
        setIsConnected(false);
        safeError('Connection check failed:', err);
      }
    };

    checkConnection();
    
    // Check connection every 30 seconds
    const interval = setInterval(checkConnection, 30000);
    return () => clearInterval(interval);
  }, []);

  const analyze = useCallback(async (input: string, context?: any): Promise<ReasoningResponse> => {
    setIsLoading(true);
    setError(null);

    try {
      const request: ReasoningRequest = {
        input,
        context: {
          user_id: 'anonymous',
          conversation_id: `chat_${Date.now()}`,
          ...context,
        },
      };

      const response = await reasoningService.analyze(request);
      setLastResponse(response);
      
      if (!response.success) {
        setError(response.errors?.ai_error || 'Analysis failed');
      }

      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      
      // Return fallback response
      const fallbackResponse: ReasoningResponse = {
        success: true,
        response: {
          content: `I'm having trouble processing your request right now. You asked: "${input}". I'm running in offline mode but still here to help.`,
          type: 'text',
          metadata: {
            fallback_mode: true,
            local_processing: true,
          },
        },
        reasoning_method: 'hook_fallback',
        fallback_used: true,
        errors: {
          ai_error: errorMessage,
        },
      };
      
      setLastResponse(fallbackResponse);
      return fallbackResponse;
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    analyze,
    isLoading,
    error,
    lastResponse,
    systemStatus,
    isConnected,
  };
}

export default useReasoning;