export interface SampleExtensionDefinition {
  id: string;
  name: string;
  display_name: string;
  description: string;
  version: string;
  author: string;
  category: string;
  status: string;
  capabilities: {
    provides_ui: boolean;
    provides_api: boolean;
    provides_background_tasks: boolean;
    provides_webhooks: boolean;
  };
}

const BASE_SAMPLE_EXTENSIONS: SampleExtensionDefinition[] = [
  {
    id: "analytics-dashboard",
    display_name: "Analytics Dashboard",
    name: "analytics-dashboard",
    description:
      "Advanced analytics and reporting dashboard with real-time metrics",
    version: "1.2.0",
    author: "Kari Team",
    category: "analytics",
    status: "active",
    capabilities: {
      provides_ui: true,
      provides_api: true,
      provides_background_tasks: true,
      provides_webhooks: false,
    },
  },
  {
    id: "automation-engine",
    display_name: "Automation Engine",
    name: "automation-engine",
    description:
      "Intelligent workflow automation with AI-powered task orchestration",
    version: "2.1.0",
    author: "Kari Team",
    category: "automation",
    status: "active",
    capabilities: {
      provides_ui: true,
      provides_api: true,
      provides_background_tasks: true,
      provides_webhooks: true,
    },
  },
  {
    id: "communication-hub",
    display_name: "Communication Hub",
    name: "communication-hub",
    description:
      "Unified communication platform with multi-channel support",
    version: "1.0.5",
    author: "Community",
    category: "communication",
    status: "active",
    capabilities: {
      provides_ui: true,
      provides_api: true,
      provides_background_tasks: false,
      provides_webhooks: true,
    },
  },
  {
    id: "security-monitor",
    display_name: "Security Monitor",
    name: "security-monitor",
    description:
      "Real-time security monitoring and threat detection system",
    version: "3.0.1",
    author: "Security Team",
    category: "security",
    status: "error",
    capabilities: {
      provides_ui: true,
      provides_api: true,
      provides_background_tasks: true,
      provides_webhooks: false,
    },
  },
  {
    id: "experimental-ai",
    display_name: "Experimental AI Features",
    name: "experimental-ai",
    description:
      "Cutting-edge AI features and experimental capabilities",
    version: "0.8.0-beta",
    author: "Research Team",
    category: "experimental",
    status: "inactive",
    capabilities: {
      provides_ui: true,
      provides_api: false,
      provides_background_tasks: true,
      provides_webhooks: false,
    },
  },
];

function cloneExtension(
  extension: SampleExtensionDefinition
): SampleExtensionDefinition {
  return {
    ...extension,
    capabilities: { ...extension.capabilities },
  };
}

export function getSampleExtensions(): SampleExtensionDefinition[] {
  return BASE_SAMPLE_EXTENSIONS.map(cloneExtension);
}

export function getSampleExtensionsRecord(): Record<string, SampleExtensionDefinition> {
  const record: Record<string, SampleExtensionDefinition> = {};
  for (const extension of BASE_SAMPLE_EXTENSIONS) {
    record[extension.id] = cloneExtension(extension);
  }
  return record;
}
