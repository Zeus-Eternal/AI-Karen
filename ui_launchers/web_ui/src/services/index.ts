/**
 * Services Index - Central export for all service modules
 * Provides easy access to all AI Karen services
 */

// Export service classes and functions
export { ChatService, getChatService, initializeChatService } from './chatService';
export { MemoryService, getMemoryService, initializeMemoryService } from './memoryService';
export { PluginService, getPluginService, initializePluginService } from './pluginService';

// Export service types
export type { ConversationSession, ProcessMessageOptions } from './chatService';
export type { 
  MemorySearchOptions, 
  MemoryStats, 
  MemoryContext 
} from './memoryService';
export type { 
  PluginCategory, 
  PluginExecutionOptions, 
  PluginValidationResult, 
  PluginMetrics 
} from './pluginService';

// Service initialization helper
export function initializeAllServices() {
  const chatService = initializeChatService();
  const memoryService = initializeMemoryService();
  const pluginService = initializePluginService();
  
  return {
    chatService,
    memoryService,
    pluginService,
  };
}

// Service health check helper
export async function checkServicesHealth(): Promise<{
  chat: boolean;
  memory: boolean;
  plugins: boolean;
  overall: boolean;
}> {
  const results = {
    chat: false,
    memory: false,
    plugins: false,
    overall: false,
  };

  try {
    // Test chat service
    const chatService = getChatService();
    results.chat = true;
  } catch (error) {
    console.error('Chat service health check failed:', error);
  }

  try {
    // Test memory service
    const memoryService = getMemoryService();
    results.memory = true;
  } catch (error) {
    console.error('Memory service health check failed:', error);
  }

  try {
    // Test plugin service
    const pluginService = getPluginService();
    results.plugins = true;
  } catch (error) {
    console.error('Plugin service health check failed:', error);
  }

  results.overall = results.chat && results.memory && results.plugins;
  return results;
}

// Clear all service caches
export function clearAllServiceCaches(): void {
  try {
    getChatService().clearCache();
    getMemoryService().clearCache();
    getPluginService().clearCache();
  } catch (error) {
    console.error('Failed to clear service caches:', error);
  }
}

// Get all service cache statistics
export function getAllServiceCacheStats(): {
  chat: { size: number; keys: string[] };
  memory: {
    queryCache: { size: number; keys: string[] };
    contextCache: { size: number; keys: string[] };
  };
  plugins: {
    pluginCache: { size: number; keys: string[] };
    executionHistory: { size: number; keys: string[] };
    metricsCache: { size: number; keys: string[] };
  };
} {
  return {
    chat: getChatService().getCacheStats(),
    memory: getMemoryService().getCacheStats(),
    plugins: getPluginService().getCacheStats(),
  };
}