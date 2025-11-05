/**
 * Services Index - Central export for all service modules
 * Provides easy access to all AI Karen services
 */
// Export service classes and functions
export { ChatService, getChatService, initializeChatService } from './chatService';
export { MemoryService, getMemoryService, initializeMemoryService } from './memoryService';
export { PluginService, getPluginService, initializePluginService } from './pluginService';
export { ExtensionService, getExtensionService, initializeExtensionService } from './extensionService';
export { AuthService, getAuthService, initializeAuthService } from './authService';
export { AuditService } from './auditService';
export { AlertManager, alertManager } from './alertManager';
// Export service types
export type { ConversationSession, ProcessMessageOptions } from './chatService';
export type { MemorySearchOptions, MemoryStats, MemoryContext } from './memoryService';
export type { PluginCategory, PluginExecutionOptions, PluginValidationResult, PluginMetrics } from './pluginService';
export type { ExtensionInfo } from './extensionService';
export type { LoginResult, CurrentUser } from '@/lib/karen-backend';
// Service initialization helper
export async function initializeAllServices() {
  const { initializeChatService } = await import('./chatService');
  const { initializeMemoryService } = await import('./memoryService');
  const { initializePluginService } = await import('./pluginService');
  const { initializeExtensionService } = await import('./extensionService');
  const { getAuthService } = await import('./authService');
  const { alertManager } = await import('./alertManager');
  const chatService = initializeChatService();
  const memoryService = initializeMemoryService();
  const pluginService = initializePluginService();
  const extensionService = initializeExtensionService();
  const authService = getAuthService();
  // Initialize AlertManager
  await alertManager.initialize();
  return {
    chatService,
    memoryService,
    pluginService,
    extensionService,
    authService,
    alertManager,
  };
}
// Service health check helper
export async function checkServicesHealth(): Promise<{
  chat: boolean;
  memory: boolean;
  plugins: boolean;
  extensions: boolean;
  overall: boolean;
}> {
  const results = {
    chat: false,
    memory: false,
    plugins: false,
    extensions: false,
    overall: false,
  };
  try {
    // Test chat service
    const { getChatService } = await import('./chatService');
    const chatService = getChatService();
    results.chat = true;
  } catch (error) {
  }
  try {
    // Test memory service
    const { getMemoryService } = await import('./memoryService');
    const memoryService = getMemoryService();
    results.memory = true;
  } catch (error) {
  }
  try {
    // Test plugin service
    const { getPluginService } = await import('./pluginService');
    const pluginService = getPluginService();
    results.plugins = true;
  } catch (error) {
  }
  try {
    // Test extension service
    const { getExtensionService } = await import('./extensionService');
    const extService = getExtensionService();
    results.extensions = true;
  } catch (error) {
  }
  results.overall = results.chat && results.memory && results.plugins && results.extensions;
  return results;
}
// Clear all service caches
export async function clearAllServiceCaches(): Promise<void> {
  try {
    const { getChatService } = await import('./chatService');
    const { getMemoryService } = await import('./memoryService');
    const { getPluginService } = await import('./pluginService');
    const { getExtensionService } = await import('./extensionService');
    getChatService().clearCache();
    getMemoryService().clearCache();
    getPluginService().clearCache();
  } catch (error) {
  }
}
// Get all service cache statistics
export async function getAllServiceCacheStats(): Promise<{
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
  extensions: { size: number; keys: string[] };
}> {
  const { getChatService } = await import('./chatService');
  const { getMemoryService } = await import('./memoryService');
  const { getPluginService } = await import('./pluginService');
  const { getExtensionService } = await import('./extensionService');
  return {
    chat: getChatService().getCacheStats(),
    memory: getMemoryService().getCacheStats(),
    plugins: getPluginService().getCacheStats(),
    extensions: { size: 0, keys: [] }, // ExtensionService doesn't have cache stats
  };
}
