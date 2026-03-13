/**
 * Unified API Module
 * Consolidates all API client implementations into a single, consistent interface
 * Provides backward compatibility while eliminating duplicate implementations
 */

// Export the unified API client as the primary implementation
export {
  UnifiedApiClient,
  getUnifiedApiClient,
  initializeUnifiedApiClient,
  resetUnifiedApiClient
} from './unified-api-client';

// Export legacy clients for backward compatibility (deprecated)
export {
  EnhancedApiClient,
  ApiClient,
  axiosApiClient,
  enhancedApiClient,
  apiClient as legacyApiClient,
  getApiClient
} from '../base-api-client';

// Export convenience API object
export { api } from './unified-api-client';

// Export types
export type {
  ApiResponse,
  ApiErrorInterface as ApiError,
  EnhancedRequestConfig,
  RequestInterceptor,
  ResponseInterceptor,
  ErrorInterceptor,
  RequestLog
} from '../base-api-client';

// Export specialized API types
export type {
  CopilotAssistRequest,
  CopilotAssistResponse,
  MemorySearchRequest,
  MemorySearchResponse,
  MemoryCommitRequest,
  MemoryCommitResponse,
  ChatRequest,
  ChatResponse,
  Plugin,
  SystemHealth
} from '../base-api-client';

// Default export is the unified API client
export { getUnifiedApiClient as default } from './unified-api-client';

/**
 * Migration guide for legacy API usage:
 * 
 * OLD: import { apiClient } from '../base-api-client';
 * NEW: import { getUnifiedApiClient } from './index';
 * 
 * OLD: const client = new ApiClient();
 * NEW: const client = getUnifiedApiClient();
 * 
 * OLD: apiClient.get('/endpoint');
 * NEW: apiClient.get('/endpoint');
 * 
 * The unified client provides the same interface with enhanced error handling,
 * performance monitoring, and consistent response format.
 */