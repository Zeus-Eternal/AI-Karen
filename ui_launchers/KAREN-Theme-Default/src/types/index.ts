/**
 * Central export file for all type definitions
 * 
 * Serves as the single entry point for all TypeScript type exports across the system.
 * Ensures modular organization while preventing circular imports.
 */

// --- Core domains with unique type names ---
export * from './karen-alerts';
export * from './auth';
export * from './chat';
export * from './copilot';
export * from './models';
export * from './files';
export * from './dashboard';
export * from './memory';
export * from './audit';
export * from './chat-ui';
export * from './custom-modes';

// --- Modules that share type names are exposed via namespaces to avoid conflicts ---
export * as EnhancedChatTypes from './enhanced-chat';
export * as AdminTypes from './admin';
export * as PluginTypes from './plugins';
export * as ProviderTypes from './providers';
export * as WorkflowTypes from './workflows';
