/**
 * Chat API Helper Functions
 * Helper functions for the chat API route
 */

import type { ChatMessage } from '@/lib/types';
import { executeQuery, executeTransaction } from '@/lib/database';

export async function authenticateRequest(request: Request): Promise<{ success: boolean; error?: string; userId?: string }> {
  const authHeader = request.headers.get('authorization');
  
  if (!authHeader) {
    return { success: false, error: 'Missing authorization header' };
  }
  
  // Verify API key (simplified for demo)
  const expectedApiKey = process.env.KAREN_API_KEY;
  if (!expectedApiKey) {
    // In development, allow requests without API key
    if (process.env.NODE_ENV === 'development') {
      return { success: true, userId: 'dev-user' };
    }
    return { success: false, error: 'API key not configured' };
  }
  
  if (authHeader !== `Bearer ${expectedApiKey}`) {
    return { success: false, error: 'Invalid API key' };
  }
  
  return { success: true, userId: 'authenticated-user' };
}

export async function getConversationHistory(conversationId?: string, userId?: string): Promise<ChatMessage[]> {
  if (!conversationId) {
    return [];
  }
  
  try {
    // Query messages from the messages table
    const result = await executeQuery(
      `SELECT id, role, content, metadata, created_at as timestamp
       FROM messages 
       WHERE conversation_id = $1
       ORDER BY created_at ASC
     LIMIT 50`,
      [conversationId]
    );
    
    return result.rows.map((row: unknown) => {
      const r = row as {
        id: string;
        role: 'user' | 'assistant' | 'system';
        content: string;
        timestamp: string;
        metadata?: Record<string, unknown>;
      };
      return {
        id: r.id,
        role: r.role,
        content: r.content,
        timestamp: new Date(r.timestamp),
        metadata: r.metadata || {}
      };
    });
  } catch (error) {
    console.error('Failed to get conversation history:', error);
    return [];
  }
}

export async function getUserMemories(userId?: string): Promise<any[]> {
  if (!userId) {
    return [];
  }
  
  try {
    // Query memories from the unified memories table
    const result = await executeQuery(
      `SELECT id, text, importance, decay_tier, tags, meta, created_at
       FROM memories 
       WHERE user_id = $1 AND deleted_at IS NULL
       ORDER BY importance DESC, created_at DESC
       LIMIT 20`,
      [userId]
    );
    
    return result.rows.map((row: unknown) => {
      const r = row as {
        id: string;
        text: string;
        importance: number;
        decay_tier: number;
        tags: string[];
        meta: Record<string, unknown>;
        created_at: string;
      };
      return {
        id: r.id,
        text: r.text,
        importance: r.importance,
        decayTier: r.decay_tier,
        tags: r.tags,
        metadata: r.meta,
        createdAt: r.created_at
      };
    });
  } catch (error) {
    console.error('Failed to get user memories:', error);
    return [];
  }
}

export async function getUserFacts(userId?: string): Promise<string[]> {
  if (!userId) {
    return [];
  }
  
  try {
    // Query user facts from memories table with memory_type 'fact'
    const result = await executeQuery(
      `SELECT text
       FROM memories 
       WHERE user_id = $1 AND memory_type = 'fact' AND deleted_at IS NULL
       ORDER BY importance DESC, created_at DESC
       LIMIT 10`,
      [userId]
    );
    
    return result.rows.map((row: unknown) => {
      const r = row as { text: string };
      return r.text;
    });
  } catch (error) {
    console.error('Failed to get user facts:', error);
    return [];
  }
}

export async function getUserPersonaInstructions(userId?: string): Promise<string> {
  if (!userId) {
    return '';
  }
  
  try {
    // Query user persona instructions from memories table
    const result = await executeQuery(
      `SELECT text
       FROM memories 
       WHERE user_id = $1 AND memory_type = 'preference' AND meta->>'type' = 'persona'
       ORDER BY created_at DESC
       LIMIT 1`,
      [userId]
    );
    
    return result.rows.length > 0 
      ? (result.rows[0] as { text: string }).text 
      : '';
  } catch (error) {
    console.error('Failed to get user persona instructions:', error);
    return '';
  }
}

export async function saveUserFacts(userId: string, facts: string[]): Promise<void> {
  if (!userId || !facts.length) {
    return;
  }
  
  try {
    // Insert new facts into memories table
    const insertQueries = facts.map(fact => ({
      text: `INSERT INTO memories (user_id, text, memory_type, importance, decay_tier, meta) 
               VALUES ($1, $2, 'fact', 7, 'long', '{"type": "fact", "source": "chat"}')`,
      params: [userId, fact]
    }));
    
    await executeTransaction(insertQueries);
    console.log(`Saved ${facts.length} user facts for user ${userId}`);
  } catch (error) {
    console.error('Failed to save user facts:', error);
    throw error;
  }
}

export async function saveConversationMessage(message: {
  conversationId: string;
  messageId: string;
  userId?: string;
  role: 'user' | 'assistant';
  content: string;
  metadata?: any;
  provider?: string;
}): Promise<void> {
  if (!message.conversationId || !message.messageId) {
    throw new Error('Missing required conversation or message ID');
  }
  
  try {
    // Check if conversation exists, create if not
    const conversationResult = await executeQuery(
      'SELECT id FROM conversations WHERE id = $1',
      [message.conversationId]
    );
    
    if (conversationResult.rowCount === 0) {
      // Create new conversation
      await executeQuery(
        `INSERT INTO conversations (id, user_id, title, is_active, created_at, updated_at)
         VALUES ($1, $2, $3, true, NOW(), NOW())`,
        [message.conversationId, message.userId || 'anonymous', `Chat ${new Date().toISOString()}`]
      );
    } else {
      // Update conversation timestamp
      await executeQuery(
        'UPDATE conversations SET updated_at = NOW() WHERE id = $1',
        [message.conversationId]
      );
    }
    
    // Insert message into messages table
    await executeQuery(
      `INSERT INTO messages (id, conversation_id, role, content, metadata, created_at)
       VALUES ($1, $2, $3, $4, $5, NOW())`,
      [
        message.messageId,
        message.conversationId,
        message.role,
        message.content,
        JSON.stringify({
          provider: message.provider,
          ...message.metadata
        })
      ]
    );
    
    console.log(`Saved message ${message.messageId} for conversation ${message.conversationId}`);
  } catch (error) {
    console.error('Failed to save conversation message:', error);
    throw error;
  }
}

export async function saveConversation(conversation: {
  id: string;
  userId?: string;
  title?: string;
  messages: ChatMessage[];
  metadata?: any;
}): Promise<void> {
  if (!conversation.id) {
    throw new Error('Conversation ID is required');
  }
  
  try {
    // Use transaction to save conversation and messages
    const queries = [];
    
    // Insert or update conversation
    if (conversation.messages.length > 0) {
      queries.push({
        text: `INSERT INTO conversations (id, user_id, title, is_active, created_at, updated_at, conversation_metadata)
         VALUES ($1, $2, $3, true, NOW(), NOW(), $4)
         ON CONFLICT (id) DO UPDATE SET 
           title = EXCLUDED.title,
           updated_at = NOW(),
           conversation_metadata = EXCLUDED.conversation_metadata`,
        params: [
          conversation.id,
          conversation.userId || 'anonymous',
          conversation.title || `Chat ${new Date().toISOString()}`,
          JSON.stringify(conversation.metadata || {})
        ]
      });
    }
    
    // Insert messages
    for (const msg of conversation.messages) {
      queries.push({
        text: `INSERT INTO messages (id, conversation_id, role, content, metadata, created_at)
         VALUES ($1, $2, $3, $4, $5, $6)
         ON CONFLICT (id) DO NOTHING`,
        params: [
          msg.id,
          conversation.id,
          msg.role,
          msg.content,
          JSON.stringify(msg.metadata || {}),
          msg.timestamp || new Date()
        ]
      });
    }
    
    await executeTransaction(queries);
    console.log(`Saved conversation ${conversation.id} with ${conversation.messages.length} messages`);
  } catch (error) {
    console.error('Failed to save conversation:', error);
    throw error;
  }
}

export function generateMessageId(): string {
  return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

export function generateConversationId(): string {
  return `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Rate limiting helper
 */
export async function checkRateLimit(userId: string, limit: number = 10, windowMs: number = 60000): Promise<{ allowed: boolean; remaining?: number; resetTime?: Date }> {
  if (!userId) {
    return { allowed: true };
  }
  
  try {
    // Simple in-memory rate limiting (in production, use Redis)
    const result = await executeQuery(
      `SELECT COUNT(*) as count
       FROM rate_limits
       WHERE user_id = $1 AND created_at > NOW() - INTERVAL '${windowMs} milliseconds'`,
      [userId]
    );
    
    const count = parseInt((result.rows[0] as { count: unknown }).count as string);
    
    if (count >= limit) {
      return { 
        allowed: false, 
        remaining: 0,
        resetTime: new Date(Date.now() + windowMs)
      };
    }
    
    // Log this request
    await executeQuery(
      'INSERT INTO rate_limits (user_id) VALUES ($1)',
      [userId]
    );
    
    return { 
      allowed: true, 
      remaining: limit - count 
    };
  } catch (error) {
    console.error('Rate limit check failed:', error);
    // Fail open - allow the request
    return { allowed: true };
  }
}
