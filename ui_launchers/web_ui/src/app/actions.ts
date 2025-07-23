'use server';

// Import new service-based architecture
import { getChatService } from '@/services/chatService';
import { getMemoryService } from '@/services/memoryService';
import { getPluginService } from '@/services/pluginService';
import { getKarenBackend } from '@/lib/karen-backend';

// Minimal tool imports for backward compatibility
import {
  getCurrentDate,
  getCurrentTime,
  getWeather,
  mockQueryBookDatabase,
  mockCheckGmailUnread,
  mockComposeGmail
} from '@/ai/tools/core-tools';

import type {
  AiData,
  KarenSettings,
  HandleUserMessageResult,
  ChatMessage
} from '@/lib/types';

import { DEFAULT_KAREN_SETTINGS } from '@/lib/constants';
import { handleError } from '@/lib/errorHandler';

// --- Chat message handler ---
export async function handleUserMessage(
  prompt: string,
  conversationHistory: string,
  settings: KarenSettings | null,
  totalMessagesSoFar: number
): Promise<HandleUserMessageResult> {
  try {
    const currentSettings = settings || DEFAULT_KAREN_SETTINGS;
    const chatService = getChatService();

    // Parse conversationHistory into ChatMessage array
    const messages: ChatMessage[] = conversationHistory
      .split('\n')
      .filter(line => line.trim())
      .map((line, index, arr) => {
        const isUser = line.startsWith('User:');
        return {
          id: `msg_${index}`,
          role: isUser ? 'user' : 'assistant',
          content: line.replace(/^(User:|Karen:)\s*/, ''),
          timestamp: new Date(Date.now() - (arr.length - index) * 60000),
        } as ChatMessage;
      });

    const result = await chatService.processUserMessage(
      prompt,
      messages,
      currentSettings,
      {
        storeInMemory: true,
        generateSummary:
          currentSettings.notifications.enabled &&
          currentSettings.notifications.alertOnSummaryReady &&
          totalMessagesSoFar > 0 &&
          (totalMessagesSoFar + 1) % 7 === 0,
      }
    );

    return result;

  } catch (error) {
    const errorResponse = handleError(error, {
      operation: 'handleUserMessage',
      component: 'actions',
      additionalData: { prompt: prompt.substring(0, 100) }
    });

    return {
      finalResponse: `Karen: ${errorResponse.userFriendlyMessage}`,
      suggestedNewFacts: undefined,
      proactiveSuggestion: undefined,
      summaryWasGenerated: false,
    };
  }
}

// --- Starter Prompt Fetcher (aligns with FastAPI GET /api/ai/generate-starter) ---
export async function getSuggestedStarter(assistantType: string): Promise<string> {
  try {
    const backend = getKarenBackend();
    // API contract: GET request, returns { prompts: string[], timestamp: ... }
    const url = `${backend['config'].baseUrl}/api/ai/generate-starter`;
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...(backend['config'].apiKey && { 'Authorization': `Bearer ${backend['config'].apiKey}` }),
      },
      // GET requests never send a body!
    });

    if (response.ok) {
      const data = await response.json();
      // Pick a random prompt, or the first if array is empty.
      if (Array.isArray(data.prompts) && data.prompts.length > 0) {
        const idx = Math.floor(Math.random() * data.prompts.length);
        return data.prompts[idx];
      }
      return "Tell me something interesting!";
    }
    throw new Error(`Failed to get starter: ${response.statusText}`);
  } catch (error) {
    console.error('Error getting suggested starter:', error);
    return "I had trouble thinking of a starter prompt right now. How about you start with 'Tell me something interesting'?";
  }
}

// --- Chat handler with advanced options (user/session aware) ---
export async function handleUserMessageWithKarenBackend(
  prompt: string,
  conversationHistory: ChatMessage[],
  settings: KarenSettings | null,
  userId?: string,
  sessionId?: string
): Promise<HandleUserMessageResult> {
  try {
    const currentSettings = settings || DEFAULT_KAREN_SETTINGS;
    const chatService = getChatService();

    const result = await chatService.processUserMessage(
      prompt,
      conversationHistory,
      currentSettings,
      {
        userId,
        sessionId,
        storeInMemory: true,
        generateSummary:
          currentSettings.notifications.enabled &&
          currentSettings.notifications.alertOnSummaryReady &&
          conversationHistory.length > 0 &&
          (conversationHistory.length + 1) % 7 === 0,
      }
    );

    return result;

  } catch (error) {
    const errorResponse = handleError(error, {
      operation: 'handleUserMessageWithKarenBackend',
      component: 'actions',
      userId,
      sessionId,
      additionalData: { prompt: prompt.substring(0, 100) }
    });

    return {
      finalResponse: `Karen: ${errorResponse.userFriendlyMessage}`,
      summaryWasGenerated: false,
    };
  }
}

// --- System Health ---
export async function getKarenSystemHealth(): Promise<{
  status: string;
  services: Record<string, any>;
  metrics: Record<string, any>;
}> {
  try {
    const backend = getKarenBackend();
    const [health, metrics] = await Promise.all([
      backend.healthCheck(),
      backend.getSystemMetrics(),
    ]);

    return {
      status: health.status,
      services: health.services,
      metrics: {
        cpu_usage: metrics.cpu_usage,
        memory_usage: metrics.memory_usage,
        active_sessions: metrics.active_sessions,
        uptime_hours: metrics.uptime_hours,
        response_time_avg: metrics.response_time_avg,
      }
    };
  } catch (error) {
    console.error('Failed to get Karen system health:', error);
    return {
      status: 'error',
      services: {},
      metrics: {}
    };
  }
}

// --- Plugins API ---
export async function getKarenPlugins(): Promise<Array<{
  name: string;
  description: string;
  category: string;
  enabled: boolean;
  version: string;
}>> {
  try {
    const pluginService = getPluginService();
    return await pluginService.getAvailablePlugins();
  } catch (error) {
    console.error('Failed to get Karen plugins:', error);
    return [];
  }
}

export async function executeKarenPluginAction(
  pluginName: string,
  parameters: Record<string, any>,
  userId?: string
): Promise<{
  success: boolean;
  result?: any;
  error?: string;
}> {
  try {
    const pluginService = getPluginService();
    const result = await pluginService.executePlugin(pluginName, parameters, { userId });

    return {
      success: result.success,
      result: result.result,
      error: result.error,
    };
  } catch (error) {
    console.error(`Failed to execute Karen plugin ${pluginName}:`, error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

// --- Memory Search ---
export async function searchKarenMemories(
  query: string,
  userId?: string,
  sessionId?: string,
  options: {
    topK?: number;
    similarityThreshold?: number;
    tags?: string[];
  } = {}
): Promise<Array<{
  content: string;
  similarity_score?: number;
  tags: string[];
  timestamp: number;
}>> {
  try {
    const memoryService = getMemoryService();
    return await memoryService.queryMemories(query, {
      userId,
      sessionId,
      topK: options.topK ?? 10,
      similarityThreshold: options.similarityThreshold ?? 0.6,
      tags: options.tags,
    });
  } catch (error) {
    console.error('Failed to search Karen memories:', error);
    return [];
  }
}

// --- Analytics ---
export async function getKarenAnalyticsData(
  timeRange: string = '24h'
): Promise<{
  total_interactions: number;
  unique_users: number;
  popular_features: Array<{ name: string; usage_count: number }>;
  user_satisfaction: number;
}> {
  try {
    const backend = getKarenBackend();
    return await backend.getUsageAnalytics(timeRange);
  } catch (error) {
    console.error('Failed to get Karen analytics:', error);
    return {
      total_interactions: 0,
      unique_users: 0,
      popular_features: [],
      user_satisfaction: 0,
    };
  }
}
