/**
 * Copilot Gateway Service
 * Gateway service for Copilot functionality
 */

export interface LNMSelectionResponse {
  success: boolean;
  error?: string;
  lnm?: LNMInfo;
}

export interface LNMInfo {
  id: string;
  name: string;
  description: string;
  capabilities: string[];
}

export interface PluginManifest {
  id: string;
  name: string;
  version: string;
  description: string;
  author?: string;
  enabled: boolean;
  capabilities: string[];
  riskLevel?: 'safe' | 'medium' | 'high' | 'critical';
  config?: {
    parameters?: PluginParameter[];
  };
}

export interface PluginParameter {
  name: string;
  type: string;
  description: string;
  required: boolean;
  defaultValue?: unknown;
}