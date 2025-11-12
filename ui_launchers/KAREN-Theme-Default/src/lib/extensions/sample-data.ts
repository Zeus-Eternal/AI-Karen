export interface SampleExtensionDefinition {
  id: string;
  display_name: string;
  name: string;
  description: string;
  version: string;
  author: string;
  category: string;
  status: 'active' | 'inactive' | 'error';
  capabilities: {
    provides_ui: boolean;
    provides_api: boolean;
    provides_background_tasks: boolean;
    provides_webhooks: boolean;
  };
}

export type SampleExtensionRegistry = Record<string, SampleExtensionDefinition>;

export const SAMPLE_EXTENSION_REGISTRY: SampleExtensionRegistry = {
  'analytics-dashboard': {
    id: 'analytics-dashboard',
    display_name: 'Analytics Dashboard',
    name: 'analytics-dashboard',
    description: 'Advanced analytics and reporting dashboard with real-time metrics',
    version: '1.2.0',
    author: 'Kari Team',
    category: 'analytics',
    status: 'active',
    capabilities: {
      provides_ui: true,
      provides_api: true,
      provides_background_tasks: true,
      provides_webhooks: false,
    },
  },
  'automation-engine': {
    id: 'automation-engine',
    display_name: 'Automation Engine',
    name: 'automation-engine',
    description: 'Intelligent workflow automation with AI-powered task orchestration',
    version: '2.1.0',
    author: 'Kari Team',
    category: 'automation',
    status: 'active',
    capabilities: {
      provides_ui: true,
      provides_api: true,
      provides_background_tasks: true,
      provides_webhooks: true,
    },
  },
  'communication-hub': {
    id: 'communication-hub',
    display_name: 'Communication Hub',
    name: 'communication-hub',
    description: 'Unified communication platform with multi-channel support',
    version: '1.0.5',
    author: 'Community',
    category: 'communication',
    status: 'active',
    capabilities: {
      provides_ui: true,
      provides_api: true,
      provides_background_tasks: false,
      provides_webhooks: true,
    },
  },
  'security-monitor': {
    id: 'security-monitor',
    display_name: 'Security Monitor',
    name: 'security-monitor',
    description: 'Real-time security monitoring and threat detection system',
    version: '3.0.1',
    author: 'Security Team',
    category: 'security',
    status: 'error',
    capabilities: {
      provides_ui: true,
      provides_api: true,
      provides_background_tasks: true,
      provides_webhooks: false,
    },
  },
  'experimental-ai': {
    id: 'experimental-ai',
    display_name: 'Experimental AI Features',
    name: 'experimental-ai',
    description: 'Cutting-edge AI features and experimental capabilities',
    version: '0.8.0-beta',
    author: 'Research Team',
    category: 'experimental',
    status: 'inactive',
    capabilities: {
      provides_ui: true,
      provides_api: false,
      provides_background_tasks: true,
      provides_webhooks: false,
    },
  },
} as const;

export function getSampleExtensionsResponse() {
  const entries = Object.values(SAMPLE_EXTENSION_REGISTRY);
  return {
    extensions: SAMPLE_EXTENSION_REGISTRY,
    total: entries.length,
    message: 'Sample extension payload returned due to backend unavailability.',
  } as const;
}

export function getSampleExtensionsList() {
  return Object.values(SAMPLE_EXTENSION_REGISTRY);
}
