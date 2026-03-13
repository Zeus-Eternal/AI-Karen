/**
 * AI Chat API Route
 * Handles chat requests with authentication, rate limiting, and multi-provider support
 */

import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { decideAction } from '@/ai/flows/decide-action-flow';
import { executeTool } from '@/ai/tools/core-tools';
import { aiClientManager } from '@/ai/providers/ai-client-manager';
import { auditLogger } from '@/lib/audit-logger';
import type { ChatMessage } from '@/lib/types';
import {
  authenticateRequest,
  getConversationHistory,
  getUserMemories,
  getUserFacts,
  getUserPersonaInstructions,
  saveUserFacts,
  saveConversationMessage,
  checkRateLimit,
  generateMessageId,
  generateConversationId,
} from './helpers';

// Request schema with validation
const ChatRequestSchema = z.object({
  message: z.string().min(1).max(4000),
  conversationId: z.string().optional(),
  sessionId: z.string().optional(),
  userId: z.string().optional(),
  preferences: z.object({
    personalityTone: z.enum(['neutral', 'friendly', 'formal', 'humorous']).optional(),
    personalityVerbosity: z.enum(['concise', 'balanced', 'detailed']).optional(),
    memoryDepth: z.enum(['short', 'medium', 'long']).optional(),
    preferredProvider: z.string().optional(),
    enableStreaming: z.boolean().default(true),
    maxTokens: z.number().min(1).max(8000).optional(),
    temperature: z.number().min(0).max(2).optional(),
  }).optional(),
});

export type ChatRequest = z.infer<typeof ChatRequestSchema>;

// Response schema
const ChatResponseSchema = z.object({
  success: z.boolean(),
  message: z.string(),
  messageId: z.string(),
  conversationId: z.string(),
  toolCall: z.object({
    tool: z.string(),
    parameters: z.record(z.any()),
  }).optional(),
  provider: z.string(),
  cached: z.boolean(),
  usage: z.object({
    promptTokens: z.number(),
    completionTokens: z.number(),
    totalTokens: z.number(),
  }).optional(),
  metadata: z.record(z.any()).optional(),
});

export type ChatResponse = z.infer<typeof ChatResponseSchema>;

// GET /api/ai/chat/history - Get conversation history
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const conversationId = searchParams.get('conversationId');
    const userId = searchParams.get('userId');

    if (!conversationId) {
      return NextResponse.json({
        success: false,
        error: 'Conversation ID is required',
      }, { status: 400 });
    }

    // Get conversation history
    const messages = await getConversationHistory(conversationId, userId || undefined);

    return NextResponse.json({
      success: true,
      conversationId,
      messages,
    });
  } catch (error) {
    console.error('Chat history API error:', error);
    
    await auditLogger.log('ERROR', 'CHAT_HISTORY_ERROR', {
      error: error instanceof Error ? error.message : 'Unknown error',
      userAgent: request.headers.get('user-agent'),
    });
    
    return NextResponse.json({
      success: false,
      error: 'Internal server error',
    }, { status: 500 });
  }
}

// POST /api/ai/chat
export async function POST(request: NextRequest) {
  const startTime = Date.now();
  let body: any = null;
  
  try {
    // Authenticate request
    const authResult = await authenticateRequest(request);
    if (!authResult.success) {
      await auditLogger.log('WARN', 'AUTHENTICATION_FAILED', {
        error: authResult.error,
        userAgent: request.headers.get('user-agent'),
        ip: request.headers.get('x-forwarded-for') || 'unknown',
      });
      
      return NextResponse.json({
        success: false,
        error: authResult.error,
        code: 'AUTHENTICATION_ERROR',
      }, { status: 401 });
    }
    
    // Parse and validate request
    body = await request.json();
    const validationResult = ChatRequestSchema.safeParse(body);
    
    if (!validationResult.success) {
      await auditLogger.log('ERROR', 'INVALID_REQUEST', {
        error: validationResult.error.message,
        userAgent: request.headers.get('user-agent'),
        ip: request.headers.get('x-forwarded-for') || 'unknown',
      });
      
      return NextResponse.json({
        success: false,
        error: 'Invalid request format',
        details: validationResult.error.issues,
      }, { status: 400 });
    }
    
    const { message, conversationId, sessionId, userId, preferences } = validationResult.data;
    
    // Apply rate limiting
    const rateLimitResult = await checkRateLimit(
      authResult.userId || 'anonymous',
      10, // 10 requests per minute
      60000 // 1 minute window
    );
    
    if (!rateLimitResult.allowed) {
      await auditLogger.log('WARN', 'RATE_LIMIT_EXCEEDED', {
        userId: authResult.userId || 'anonymous',
        userAgent: request.headers.get('user-agent'),
        ip: request.headers.get('x-forwarded-for') || 'unknown',
      });
      
      return NextResponse.json({
        success: false,
        error: 'Rate limit exceeded',
        details: {
          limit: 10,
          window: '1 minute',
          resetTime: rateLimitResult.resetTime,
        },
      }, { 
        status: 429,
        headers: {
          'X-RateLimit-Limit': '10',
          'X-RateLimit-Remaining': rateLimitResult.remaining?.toString() || '0',
          'X-RateLimit-Reset': rateLimitResult.resetTime?.toUTCString() || '',
        } as HeadersInit,
      });
    }
    
    // Get conversation history for context
    const conversationHistory = await getConversationHistory(conversationId || undefined, userId);
    
    // Get user memories for context
    const userMemories = await getUserMemories(userId);
    
    // Get user facts for context
    const userFacts = await getUserFacts(userId);
    
    // Get user persona instructions
    const personaInstructions = await getUserPersonaInstructions(userId);
    
    // Decide action using AI flow
    const decision = await decideAction({
      prompt: message,
      shortTermMemory: JSON.stringify(conversationHistory.slice(-10)), // Last 10 messages
      longTermMemory: JSON.stringify(userMemories),
      personalFacts: userFacts,
      customPersonaInstructions: personaInstructions,
      enableStreaming: preferences?.enableStreaming ?? true,
      personalityTone: preferences?.personalityTone,
      personalityVerbosity: preferences?.personalityVerbosity,
      memoryDepth: preferences?.memoryDepth,
      preferredProvider: preferences?.preferredProvider,
      maxTokens: preferences?.maxTokens,
      temperature: preferences?.temperature,
      userId,
      sessionId,
    });
    
    let response: ChatResponse;
    
    // Execute tool if needed
    if (decision.toolToCall && decision.toolToCall !== 'none') {
      try {
        const toolResult = await executeTool(decision.toolToCall, decision.toolInput || {});
        
        if (toolResult.success) {
          response = {
            success: true,
            message: decision.intermediateResponse,
            messageId: generateMessageId(),
            conversationId: conversationId || generateConversationId(),
            toolCall: {
              tool: decision.toolToCall,
              parameters: decision.toolInput || {},
            },
            provider: decision.providerUsed || 'default',
            cached: decision.fallbackUsed || false,
            usage: {
              promptTokens: 0,
              completionTokens: 0,
              totalTokens: 0,
            },
            metadata: {
              toolExecution: {
                tool: decision.toolToCall,
                executionTime: toolResult.executionTime,
                provider: toolResult.provider,
              },
            },
          };
        } else {
          response = {
            success: false,
            message: `Tool execution failed: ${toolResult.error}`,
            messageId: generateMessageId(),
            conversationId: conversationId || generateConversationId(),
            provider: decision.providerUsed || 'default',
            cached: false,
          };
        }
      } catch (toolError) {
        console.error('Tool execution error:', toolError);
        response = {
          success: false,
          message: `Tool execution error: ${toolError instanceof Error ? toolError.message : 'Unknown tool error'}`,
          messageId: generateMessageId(),
          conversationId: conversationId || generateConversationId(),
          provider: decision.providerUsed || 'default',
          cached: false,
        };
      }
    } else {
      // Direct AI response
      response = {
        success: true,
        message: decision.intermediateResponse,
        messageId: generateMessageId(),
        conversationId: conversationId || generateConversationId(),
        provider: decision.providerUsed || 'default',
        cached: decision.fallbackUsed || false,
        usage: {
          promptTokens: 0,
          completionTokens: 0,
          totalTokens: 0,
        },
        metadata: {
          confidence: decision.confidence,
          reasoning: decision.reasoning,
          fallbackUsed: decision.fallbackUsed,
          suggestedNewFacts: decision.suggestedNewFacts,
          proactiveSuggestion: decision.proactiveSuggestion,
        },
      };
    }
    
    // Save new facts if suggested
    if (decision.suggestedNewFacts && decision.suggestedNewFacts.length > 0 && userId) {
      try {
        await saveUserFacts(userId, [
          ...userFacts,
          ...decision.suggestedNewFacts,
        ]);
      } catch (factError) {
        console.error('Failed to save user facts:', factError);
        // Don't fail the whole request for this
      }
    }
    
    // Update conversation history
    try {
      await saveConversationMessage({
        conversationId: response.conversationId,
        messageId: response.messageId,
        userId,
        role: 'assistant',
        content: response.message,
        metadata: response.metadata,
        provider: response.provider,
      });
    } catch (saveError) {
      console.error('Failed to save conversation message:', saveError);
      // Don't fail the whole request for this, but log it
    }
    
    // Log successful request
    await auditLogger.log('INFO', 'CHAT_SUCCESS', {
      conversationId: response.conversationId,
      messageId: response.messageId,
      userId,
      provider: response.provider,
      toolUsed: decision.toolToCall,
      responseTime: Date.now() - startTime,
      cached: response.cached,
      tokensUsed: response.usage?.totalTokens,
      userAgent: request.headers.get('user-agent'),
      ip: request.headers.get('x-forwarded-for') || 'unknown',
    });
    
    return NextResponse.json(response, {
      headers: {
        'X-Response-Time': `${Date.now() - startTime}ms`,
        'X-Provider-Used': response.provider,
        'X-Cached': response.cached.toString(),
        'X-RateLimit-Limit': '10',
        'X-RateLimit-Remaining': rateLimitResult.remaining?.toString() || '9',
        'X-RateLimit-Reset': rateLimitResult.resetTime?.toUTCString() || '',
      },
    });
    
  } catch (error) {
    console.error('Chat API error:', error);
    
    await auditLogger.log('ERROR', 'CHAT_ERROR', {
      error: error instanceof Error ? error.message : 'Unknown error',
      userId: body?.userId || 'anonymous',
      responseTime: Date.now() - startTime,
      userAgent: request.headers.get('user-agent'),
      ip: request.headers.get('x-forwarded-for') || 'unknown',
    });
    
    return NextResponse.json({
      success: false,
      error: 'Internal server error',
      code: 'INTERNAL_ERROR',
    }, { status: 500 });
  }
}
