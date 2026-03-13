/**
 * Test Database Integration for Chat API
 * This file tests the database integration functions
 */

import { executeQuery, testConnection } from '@/lib/database';
import { 
  getConversationHistory,
  getUserMemories,
  getUserFacts,
  saveConversationMessage,
  checkRateLimit
} from './helpers';

// Test function to verify database integration
export async function testDatabaseIntegration() {
  const results = {
    databaseConnection: false,
    conversationHistory: false,
    userMemories: false,
    userFacts: false,
    messageSaving: false,
    rateLimiting: false,
  };

  try {
    // Test database connection
    results.databaseConnection = await testConnection();
    console.log('Database connection test:', results.databaseConnection ? 'PASSED' : 'FAILED');

    // Test conversation history retrieval
    const testConversationId = 'test-conv-123';
    const history = await getConversationHistory(testConversationId, 'test-user');
    results.conversationHistory = Array.isArray(history);
    console.log('Conversation history test:', results.conversationHistory ? 'PASSED' : 'FAILED');

    // Test user memories retrieval
    const memories = await getUserMemories('test-user');
    results.userMemories = Array.isArray(memories);
    console.log('User memories test:', results.userMemories ? 'PASSED' : 'FAILED');

    // Test user facts retrieval
    const facts = await getUserFacts('test-user');
    results.userFacts = Array.isArray(facts);
    console.log('User facts test:', results.userFacts ? 'PASSED' : 'FAILED');

    // Test message saving
    await saveConversationMessage({
      conversationId: testConversationId,
      messageId: 'test-msg-123',
      userId: 'test-user',
      role: 'user',
      content: 'Test message for database integration',
      provider: 'test-provider',
    });
    results.messageSaving = true;
    console.log('Message saving test: PASSED');

    // Test rate limiting
    const rateLimitResult = await checkRateLimit('test-user', 5, 60000);
    results.rateLimiting = rateLimitResult.allowed !== undefined;
    console.log('Rate limiting test:', results.rateLimiting ? 'PASSED' : 'FAILED');

  } catch (error) {
    console.error('Database integration test failed:', error);
  }

  return results;
}

// Test endpoint for manual testing
export async function GET() {
  const results = await testDatabaseIntegration();
  
  return Response.json({
    success: true,
    message: 'Database integration test completed',
    results,
    timestamp: new Date().toISOString(),
  });
}