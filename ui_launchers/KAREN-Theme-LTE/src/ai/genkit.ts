/**
 * Genkit AI Configuration
 * Core AI framework setup for KAREN theme
 */

import { genkit } from 'genkit';
import { googleAI } from '@genkit-ai/googleai';
import { z } from 'zod';

// Initialize Genkit with Google AI
export const genkitAI = genkit({
  plugins: [googleAI()],
});

// AI Model configuration
export const AI_MODEL = 'gemini-1.5-flash';

// Response schema for structured outputs
export const ChatResponseSchema = z.object({
  response: z.string(),
  confidence: z.number().min(0).max(1),
  intent: z.string().optional(),
  suggestions: z.array(z.string()).optional(),
  metadata: z.record(z.any()).optional(),
});

// Input schema for chat requests
export const ChatInputSchema = z.object({
  message: z.string(),
  context: z.string().optional(),
  conversationHistory: z.array(z.object({
    role: z.enum(['user', 'assistant', 'system']),
    content: z.string(),
  })).optional(),
  userId: z.string().optional(),
  sessionId: z.string().optional(),
});

// Tool definitions
export const aiTools = {
  // Web search tool
  webSearch: {
    name: 'webSearch',
    description: 'Search the web for current information',
    inputSchema: z.object({
      query: z.string(),
      maxResults: z.number().default(5),
    }),
    outputSchema: z.object({
      results: z.array(z.object({
        title: z.string(),
        url: z.string(),
        snippet: z.string(),
      })),
    }),
  },
  
  // Memory retrieval tool
  memoryRetrieval: {
    name: 'memoryRetrieval',
    description: 'Retrieve relevant memories from the knowledge base',
    inputSchema: z.object({
      query: z.string(),
      limit: z.number().default(10),
      userId: z.string(),
    }),
    outputSchema: z.object({
      memories: z.array(z.object({
        id: z.string(),
        content: z.string(),
        relevance: z.number(),
        timestamp: z.string(),
      })),
    }),
  },
  
  // File analysis tool
  fileAnalysis: {
    name: 'fileAnalysis',
    description: 'Analyze uploaded files for content extraction',
    inputSchema: z.object({
      fileId: z.string(),
      analysisType: z.enum(['summary', 'extract', 'analyze']).default('summary'),
    }),
    outputSchema: z.object({
      content: z.string(),
      metadata: z.record(z.any()),
      confidence: z.number(),
    }),
  },
};
