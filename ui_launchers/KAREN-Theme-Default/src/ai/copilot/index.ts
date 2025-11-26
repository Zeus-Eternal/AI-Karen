// Main exports for the Copilot system
export * from './types/backend';
export * from './types/copilot';
export * from './services/copilotGateway';
export * from './services/copilotEngine';
export * from './hooks/useCopilot';
export * from './components/CopilotChatInterface';
export * from './components/IntelligentAssistant';
export * from './components/MemoryManagement';
export * from './components/WorkflowAutomation';
export * from './components/ArtifactSystem';
export * from './components/PluginDiscovery';
export * from './components/AdaptiveInterface';
export * from './components/MultiModalInput';

// Explicitly export CopilotProvider from useCopilot
export { CopilotProvider } from './hooks/useCopilot';

// Default export for the main CopilotChatInterface component
export { CopilotChatInterface as default } from './components/CopilotChatInterface';