import React from 'react';
import { CopilotBackendRequest, CopilotBackendResponse } from '../services/copilotGateway';
import { EnhancedContext } from '../types/copilot';

interface ContextBridgeState {
  // UI context
  viewId: string;
  interfaceMode: string;
  activePanel: 'chat' | 'memory' | 'workflows' | 'artifacts';
  inputModality: 'text' | 'code' | 'image' | 'audio';
  
  // System context
  client: 'web' | 'desktop' | 'mobile';
  capabilities: string[];
  
  // Intent and plugin hints
  intentHints: string[];
  pluginHints: string[];
  
  // Methods
  createBackendRequest: (input: string, modality?: 'text' | 'code' | 'image' | 'audio') => CopilotBackendRequest;
  processBackendResponse: (response: CopilotBackendResponse) => EnhancedContext;
  updateUIContext: (updates: Partial<ContextBridgeState>) => void;
  addIntentHint: (hint: string) => void;
  addPluginHint: (hint: string) => void;
  clearHints: () => void;
}

const defaultContextBridgeState: ContextBridgeState = {
  viewId: 'copilot-chat',
  interfaceMode: 'chat',
  activePanel: 'chat',
  inputModality: 'text',
  client: 'web',
  capabilities: ['text', 'code', 'image', 'audio'],
  intentHints: [],
  pluginHints: [],
  createBackendRequest: () => ({} as CopilotBackendRequest),
  processBackendResponse: () => ({} as EnhancedContext),
  updateUIContext: () => {},
  addIntentHint: () => {},
  addPluginHint: () => {},
  clearHints: () => {},
};

// Create context
export const ContextBridgeContext = React.createContext<ContextBridgeState>(defaultContextBridgeState);
export type { ContextBridgeState };