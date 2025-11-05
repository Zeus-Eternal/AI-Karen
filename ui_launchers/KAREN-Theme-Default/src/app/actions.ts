'use server';

/**
 * Server Actions: Prompt-First Chat Orchestration + System Health + Plugins + Memory + Analytics
 * - Parses conversation history reliably
 * - Injects the KRO (Kari Reasoning Orchestrator) system prompt
 * - Uses strict typing, safe fetch with timeouts, and uniform error handling
 * - No placeholders; graceful fallbacks on failures
 */

import { getChatService } from '@/services/chatService';
import { getMemoryService } from '@/services/memoryService';
import { getPluginService } from '@/services/pluginService';
import { getKarenBackend } from '@/lib/karen-backend';

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

/* -------------------------------------------------------------------------------------------------
 * KRO (Kari Reasoning Orchestrator) — Prompt-First System Prompt
 * Injected as a system message when handling user messages to enforce plan→route→execute→synthesize.
 * ------------------------------------------------------------------------------------------------- */
function getKROSystemPrompt(): string {
  return `
You are Kari Reasoning Orchestrator (KRO), the prompt-first controller that plans, routes, and synthesizes answers for the front-end UI. Your job is to:
1) understand the user request, 2) plan the minimal path to a correct answer, 3) call the right tools, 4) synthesize a reliable response, and 5) return a UI-ready message.

Operating principles:
- Be precise and production-grade. No placeholders. If confidence is low, say so and propose the next action.
- Keep internal chain-of-thought private. Expose only short reasoning summaries if asked.
- Prefer local resources and cached memory before remote calls. Escalate only when needed.
- Every turn updates memory and telemetry.

Classify intent using the intent map (Basic_Internet_Search | Advanced_Internet_Search | Data_Scraping | Media | Predictive | Automation | ModelMgmt | System | General).
Follow: parse → classify → plan → execute tools (only those available) → validate → synthesize → store helpful memory.
End-user message must lead with the answer, followed by concise details that affect the decision.
  `.trim();
}

/* -------------------------------------------------------------------------------------------------
 * Utilities
 * ------------------------------------------------------------------------------------------------- */

/**
 * Robustly parses a newline-delimited conversation history like:
 *   "User: ...\nKaren: ...\nUser: ..."
 * Falls back safely on malformed lines.
 */
function parseConversationHistory(raw: string): ChatMessage[] {
  if (!raw || typeof raw !== 'string') return [];
  const lines = raw.split('\n').filter(l => l.trim().length > 0);

  const baseTs = Date.now();
  const total = lines.length;

  return lines.map((line, index) => {
    const isUser = line.startsWith('User:');
    const isAssistant = line.startsWith('Karen:') || line.startsWith('Assistant:');

    const content = line.replace(/^(User:|Karen:|Assistant:)\s*/, '').trim();
    const role: 'user' | 'assistant' =
      isUser ? 'user' : isAssistant ? 'assistant' : (index % 2 === 0 ? 'user' : 'assistant');

    return {
      id: `msg_${index}`,
      role,
      content: content || '',
      timestamp: new Date(baseTs - (total - index) * 60_000)
    } as ChatMessage;
  });
}

/**
 * Adds a system message with the KRO system prompt to the top of an existing message list.
 * If the first message is already a system prompt, we respect it and prepend ours.
 */
function withSystemPrompt(messages: ChatMessage[]): ChatMessage[] {
  const sys: ChatMessage = {
    id: 'sys_kro',
    role: 'system' as any, // keep compatibility with your ChatMessage typing if role union is limited
    content: getKROSystemPrompt(),
    timestamp: new Date()
  };
  return [sys, ...messages];
}

/**
 * Decide whether to generate a periodic summary (every 7 messages when alerts enabled).
 */
function shouldGenerateSummary(notifications: KarenSettings['notifications'] | undefined, count: number): boolean {
  if (!notifications?.enabled || !notifications.alertOnSummaryReady) return false;
  if (count <= 0) return false;
  return (count + 1) % 7 === 0;
}

/**
 * Safe fetch helper with consistent timeout and error text extraction.
 */
async function safeJsonFetch<T = unknown>(url: string, init?: RequestInit & { timeoutMs?: number }): Promise<T> {
  const timeoutMs = init?.timeoutMs ?? 12_000;
  const controller = new AbortController();
  const to = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const resp = await fetch(url, {
      ...init,
      signal: init?.signal ?? controller.signal
    });
    if (!resp.ok) {
      const text = await resp.text().catch(() => '');
      throw new Error(`HTTP ${resp.status} ${resp.statusText} — ${text || 'no body'}`);
    }
    return (await resp.json()) as T;
  } finally {
    clearTimeout(to);
  }
}

/* -------------------------------------------------------------------------------------------------
 * Chat message handler — string-based history (UI legacy compatibility)
 * ------------------------------------------------------------------------------------------------- */
export async function handleUserMessage(
  prompt: string,
  conversationHistory: string,
  settings: KarenSettings | null,
  totalMessagesSoFar: number
): Promise<HandleUserMessageResult> {
  try {
    const currentSettings = settings || DEFAULT_KAREN_SETTINGS;
    const chatService = getChatService();

    const parsed = parseConversationHistory(conversationHistory);
    const messagesWithSys = withSystemPrompt(parsed);

    const result = await chatService.processUserMessage(
      prompt,
      messagesWithSys,
      currentSettings,
      {
        storeInMemory: true,
        generateSummary: shouldGenerateSummary(currentSettings.notifications, totalMessagesSoFar),
        // Expose minimal core tools for backward compatibility if your chat service inspects this array.
        tools: {
          getCurrentDate,
          getCurrentTime,
          getWeather,
          mockQueryBookDatabase,
          mockCheckGmailUnread,
          mockComposeGmail
        }
      }
    );

    return result;
  } catch (err) {
    const errorResponse = handleError(err, {
      operation: 'handleUserMessage',
      component: 'server-actions',
      additionalData: { prompt: String(prompt ?? '').slice(0, 200) }
    });

    return {
      finalResponse: `Karen: ${errorResponse.userFriendlyMessage}`,
      suggestedNewFacts: undefined,
      proactiveSuggestion: undefined,
      summaryWasGenerated: false
    };
  }
}

/* -------------------------------------------------------------------------------------------------
 * Starter Prompt (aligns with FastAPI POST /api/ai/generate-starter)
 * ------------------------------------------------------------------------------------------------- */
export async function getSuggestedStarter(assistantType: string): Promise<string> {
  try {
    const backend = getKarenBackend();
    const url = `${backend['config'].baseUrl}/api/ai/generate-starter`;

    type StarterResp = { prompts?: string[]; timestamp?: string };
    const data = await safeJsonFetch<StarterResp>(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(backend['config'].apiKey && { Authorization: `Bearer ${backend['config'].apiKey}` })
      },
      body: JSON.stringify({ assistantType }),
      timeoutMs: 10_000
    });

    const list = Array.isArray(data.prompts) ? data.prompts : [];
    if (list.length > 0) {
      const idx = Math.floor(Math.random() * list.length);
      return list[idx];
    }
    return 'Tell me something interesting!';
  } catch {
    return "I had trouble thinking of a starter prompt right now. How about you start with 'Tell me something interesting'?";
  }
}

/* -------------------------------------------------------------------------------------------------
 * Chat handler — object-based history (user/session aware, preferred)
 * ------------------------------------------------------------------------------------------------- */
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

    // Ensure our KRO system prompt is present
    const messagesWithSys = withSystemPrompt(conversationHistory || []);

    const result = await chatService.processUserMessage(
      prompt,
      messagesWithSys,
      currentSettings,
      {
        userId,
        sessionId,
        storeInMemory: true,
        generateSummary: shouldGenerateSummary(currentSettings.notifications, conversationHistory?.length ?? 0),
        tools: {
          getCurrentDate,
          getCurrentTime,
          getWeather,
          mockQueryBookDatabase,
          mockCheckGmailUnread,
          mockComposeGmail
        }
      }
    );
    return result;
  } catch (err) {
    const errorResponse = handleError(err, {
      operation: 'handleUserMessageWithKarenBackend',
      component: 'server-actions',
      userId,
      sessionId,
      additionalData: { prompt: String(prompt ?? '').slice(0, 200) }
    });

    return {
      finalResponse: `Karen: ${errorResponse.userFriendlyMessage}`,
      summaryWasGenerated: false
    };
  }
}

/* -------------------------------------------------------------------------------------------------
 * System Health
 * ------------------------------------------------------------------------------------------------- */
export async function getKarenSystemHealth(): Promise<{
  status: string;
  services: Record<string, any>;
  metrics: Record<string, any>;
}> {
  try {
    const backend = getKarenBackend();
    const [health, metrics] = await Promise.all([
      backend.healthCheck(),
      backend.getSystemMetrics()
    ]);

    return {
      status: health?.status ?? 'unknown',
      services: health?.services ?? {},
      metrics: {
        cpu_usage: metrics?.cpu_usage ?? 0,
        memory_usage: metrics?.memory_usage ?? 0,
        active_sessions: metrics?.active_sessions ?? 0,
        uptime_hours: metrics?.uptime_hours ?? 0,
        response_time_avg: metrics?.response_time_avg ?? 0
      }
    };
  } catch {
    return { status: 'error', services: {}, metrics: {} };
  }
}

/* -------------------------------------------------------------------------------------------------
 * Plugins API
 * ------------------------------------------------------------------------------------------------- */
export async function getKarenPlugins(): Promise<
  Array<{
    name: string;
    description: string;
    category: string;
    enabled: boolean;
    version: string;
  }>
> {
  try {
    const pluginService = getPluginService();
    return await pluginService.getAvailablePlugins();
  } catch {
    return [];
  }
}

export async function executeKarenPluginAction(
  pluginName: string,
  parameters: Record<string, any>,
  userId?: string
): Promise<{ success: boolean; result?: any; error?: string }> {
  try {
    const pluginService = getPluginService();
    const result = await pluginService.executePlugin(pluginName, parameters, { userId });
    return {
      success: !!result?.success,
      result: result?.result,
      error: result?.error
    };
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error';
    return { success: false, error: message };
  }
}

/* -------------------------------------------------------------------------------------------------
 * Memory Search
 * ------------------------------------------------------------------------------------------------- */
export async function searchKarenMemories(
  query: string,
  userId?: string,
  sessionId?: string,
  options: { topK?: number; similarityThreshold?: number; tags?: string[] } = {}
): Promise<
  Array<{
    content: string;
    similarity_score?: number;
    tags: string[];
    timestamp: number;
  }>
> {
  try {
    const memoryService = getMemoryService();
    const res = await memoryService.queryMemories(query, {
      userId,
      sessionId,
      topK: options.topK ?? 10,
      similarityThreshold: options.similarityThreshold ?? 0.6,
      tags: options.tags ?? []
    });
    return Array.isArray(res) ? res : [];
  } catch {
    return [];
  }
}

/* -------------------------------------------------------------------------------------------------
 * Analytics
 * ------------------------------------------------------------------------------------------------- */
export async function getKarenAnalyticsData(
  timeRange: string = '24h'
): Promise<{
  total_interactions: number;
  unique_users: number;
  popular_features: Array<{ name: string; usage_count: number }>;
  user_satisfaction: number;
  peak_hours?: number[];
}> {
  try {
    const backend = getKarenBackend();
    const data = await backend.getUsageAnalytics(timeRange);
    return {
      total_interactions: data?.total_interactions ?? 0,
      unique_users: data?.unique_users ?? 0,
      popular_features: data?.popular_features ?? [],
      user_satisfaction: data?.user_satisfaction ?? 0,
      peak_hours: data?.peak_hours ?? []
    };
  } catch {
    return {
      total_interactions: 0,
      unique_users: 0,
      popular_features: [],
      user_satisfaction: 0,
      peak_hours: []
    };
  }
}
