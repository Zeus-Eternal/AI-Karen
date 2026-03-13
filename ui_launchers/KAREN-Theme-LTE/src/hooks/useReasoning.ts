/**
 * useReasoning Hook - React hook for the reasoning system
 */

import React from 'react';
const { useState, useCallback, useEffect } = React;
import {
  reasoningService,
  ReasoningRequest,
  ReasoningResponse,
} from '@/services/reasoningService';
import { safeError, ErrorContext } from '@/lib/errorHandler';

export interface UseReasoningReturn {
  analyze: (input: string, context?: unknown) => Promise<ReasoningResponse>;
  isLoading: boolean;
  error: string | null;
  lastResponse: ReasoningResponse | null;
  systemStatus: { status: string; lastCheck: Date } | null;
  isConnected: boolean;
}

export function useReasoning(): UseReasoningReturn {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastResponse, setLastResponse] = useState<ReasoningResponse | null>(
    null
  );
  const [systemStatus, setSystemStatus] = useState<{ status: string; lastCheck: Date } | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  // Check connection status on mount
  useEffect(() => {
    const checkConnection = async () => {
      try {
        // Simple connection check - try to perform a basic reasoning request
        const testRequest: ReasoningRequest = {
          query: 'connection test',
          context: { test: true }
        };
        await reasoningService.performReasoning(testRequest);
        setIsConnected(true);
        setSystemStatus({
          status: 'connected',
          lastCheck: new Date()
        });
      } catch (err) {
        setIsConnected(false);
        const errorContext: ErrorContext = {
          type: 'error',
          message: err instanceof Error ? err.message : 'Unknown error',
          operation: 'connection_check',
          metadata: { component: 'useReasoning' }
        };
        safeError('Connection check failed:', errorContext);
      }
    };

    checkConnection();

    // Check connection every 30 seconds
    const interval = setInterval(checkConnection, 30000);
    return () => clearInterval(interval);
  }, []);

  const analyze = useCallback(
    async (input: string, context?: unknown): Promise<ReasoningResponse> => {
      setIsLoading(true);
      setError(null);

      try {
        const request: ReasoningRequest = {
          query: input,
          context: {
            user_id: 'anonymous',
            conversation_id: `chat_${Date.now()}`,
            ...(typeof context === 'object' && context !== null ? (context as Record<string, unknown>) : {}),
          },
        };

        const response = await reasoningService.performReasoning(request);
        setLastResponse(response);

        return response;
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Unknown error";
        setError(errorMessage);

        // Return fallback response
        const fallbackResponse: ReasoningResponse = {
          result: `I'm having trouble processing your request right now. You asked: "${input}". I'm running in offline mode but still here to help.`,
          reasoning: 'hook_fallback',
          confidence: 0.5,
          tokensUsed: 0,
          processingTime: 0,
          metadata: {
            fallback_mode: true,
            local_processing: true,
            error: errorMessage,
          },
        };

        setLastResponse(fallbackResponse);
        return fallbackResponse;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

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
