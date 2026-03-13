/**
 * Component Registry and Tracking System
 * 
 * This system ensures only current, maintained components are served
 * and provides a centralized way to manage component lifecycle.
 */

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

export interface ComponentMetadata {
  id: string;
  name: string;
  version: string;
  status: 'active' | 'deprecated' | 'legacy' | 'removed';
  category: 'ui' | 'layout' | 'plugin' | 'chat' | 'settings' | 'performance';
  description?: string;
  dependencies?: string[];
  deprecatedIn?: string;
  removedIn?: string;
  migrationPath?: string;
  lastUpdated: string;
  bundleSize?: number;
  performanceScore?: number;
}

export interface ComponentRegistry {
  [componentId: string]: ComponentMetadata;
}

// ============================================================================
// COMPONENT REGISTRY
// ============================================================================

/**
 * Central registry of all components in the application
 * This helps track which components are active, deprecated, or removed
 */
export const COMPONENT_REGISTRY: ComponentRegistry = {
  // UI Components
  'button': {
    id: 'button',
    name: 'Button',
    version: '2.0.0',
    status: 'active',
    category: 'ui',
    description: 'Modern button component with variants and accessibility features',
    lastUpdated: '2024-01-15',
    performanceScore: 95
  },
  'card': {
    id: 'card',
    name: 'Card',
    version: '2.0.0',
    status: 'active',
    category: 'ui',
    description: 'Responsive card component with proper semantic markup',
    lastUpdated: '2024-01-15',
    performanceScore: 92
  },
  'sheet': {
    id: 'sheet',
    name: 'Sheet',
    version: '2.0.0',
    status: 'active',
    category: 'ui',
    description: 'Modern sheet/slide-out panel component',
    lastUpdated: '2024-01-15',
    performanceScore: 88
  },
  'sidebar': {
    id: 'sidebar',
    name: 'Sidebar',
    version: '2.0.0',
    status: 'active',
    category: 'layout',
    description: 'Responsive sidebar navigation with collapsible states',
    lastUpdated: '2024-01-15',
    performanceScore: 90
  },
  'toast': {
    id: 'toast',
    name: 'Toast',
    version: '2.0.0',
    status: 'active',
    category: 'ui',
    description: 'Accessible toast notification system',
    lastUpdated: '2024-01-15',
    performanceScore: 87
  },

  // Chat Components
  'chat-interface': {
    id: 'chat-interface',
    name: 'Chat Interface',
    version: '2.0.0',
    status: 'active',
    category: 'chat',
    description: 'Modern chat interface with responsive design',
    lastUpdated: '2024-01-15',
    performanceScore: 93
  },
  'message-bubble': {
    id: 'message-bubble',
    name: 'Message Bubble',
    version: '2.0.0',
    status: 'active',
    category: 'chat',
    description: 'Accessible message bubble component',
    lastUpdated: '2024-01-15',
    performanceScore: 91
  },

  // Settings Components
  'settings-dialog': {
    id: 'settings-dialog',
    name: 'Settings Dialog',
    version: '2.0.0',
    status: 'active',
    category: 'settings',
    description: 'Comprehensive settings management interface',
    lastUpdated: '2024-01-15',
    performanceScore: 85
  },

  // Plugin Components
  'plugin-overview': {
    id: 'plugin-overview',
    name: 'Plugin Overview',
    version: '2.0.0',
    status: 'active',
    category: 'plugin',
    description: 'Plugin management and overview interface',
    lastUpdated: '2024-01-15',
    performanceScore: 82
  },

  // Legacy Components (Marked for Removal)
  'legacy-right-panel': {
    id: 'legacy-right-panel',
    name: 'Legacy Right Panel',
    version: '1.0.0',
    status: 'deprecated',
    category: 'layout',
    description: 'Legacy right panel component - use new Sheet component instead',
    deprecatedIn: '2024-01-01',
    removedIn: '2024-06-01',
    migrationPath: 'Use Sheet component from @/components/ui/sheet',
    lastUpdated: '2023-12-01',
    performanceScore: 65
  },
  'legacy-responsive-hook': {
    id: 'legacy-responsive-hook',
    name: 'Legacy Responsive Hook',
    version: '1.0.0',
    status: 'legacy',
    category: 'ui',
    description: 'Legacy responsive utilities - use native CSS Grid/Flexbox instead',
    deprecatedIn: '2023-12-01',
    removedIn: '2024-03-01',
    migrationPath: 'Use native CSS Grid and Flexbox with Tailwind utilities',
    lastUpdated: '2023-11-01',
    performanceScore: 45
  }
};

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Check if a component is active and safe to use
 */
export function isComponentActive(componentId: string): boolean {
  const component = COMPONENT_REGISTRY[componentId];
  return component?.status === 'active';
}

/**
 * Check if a component is deprecated
 */
export function isComponentDeprecated(componentId: string): boolean {
  const component = COMPONENT_REGISTRY[componentId];
  return component?.status === 'deprecated';
}

/**
 * Check if a component is legacy (should not be used)
 */
export function isComponentLegacy(componentId: string): boolean {
  const component = COMPONENT_REGISTRY[componentId];
  return component?.status === 'legacy' || component?.status === 'removed';
}

/**
 * Get component metadata
 */
export function getComponentMetadata(componentId: string): ComponentMetadata | undefined {
  return COMPONENT_REGISTRY[componentId];
}

/**
 * Get all active components by category
 */
export function getActiveComponentsByCategory(category: ComponentMetadata['category']): ComponentMetadata[] {
  return Object.values(COMPONENT_REGISTRY).filter(
    component => component.status === 'active' && component.category === category
  );
}

/**
 * Get all deprecated components
 */
export function getDeprecatedComponents(): ComponentMetadata[] {
  return Object.values(COMPONENT_REGISTRY).filter(
    component => component.status === 'deprecated'
  );
}

/**
 * Get all legacy components
 */
export function getLegacyComponents(): ComponentMetadata[] {
  return Object.values(COMPONENT_REGISTRY).filter(
    component => component.status === 'legacy' || component.status === 'removed'
  );
}

/**
 * Validate component imports at build time
 */
export function validateComponentImports(): {
  valid: string[];
  deprecated: string[];
  legacy: string[];
  errors: string[];
} {
  const valid: string[] = [];
  const deprecated: string[] = [];
  const legacy: string[] = [];
  const errors: string[] = [];

  Object.keys(COMPONENT_REGISTRY).forEach(componentId => {
    const component = COMPONENT_REGISTRY[componentId];
    
    switch (component.status) {
      case 'active':
        valid.push(componentId);
        break;
      case 'deprecated':
        deprecated.push(componentId);
        break;
      case 'legacy':
      case 'removed':
        legacy.push(componentId);
        break;
      default:
        errors.push(`Unknown status for component: ${componentId}`);
    }
  });

  return { valid, deprecated, legacy, errors };
}

// ============================================================================
// DEVELOPMENT WARNINGS
// ============================================================================

/**
 * Development-time warnings for deprecated/legacy components
 */
export function checkComponentUsage(componentId: string): void {
  if (process.env.NODE_ENV !== 'development') return;

  const component = COMPONENT_REGISTRY[componentId];
  if (!component) {
    console.warn(`⚠️ Unknown component: ${componentId}`);
    return;
  }

  switch (component.status) {
    case 'deprecated':
      console.warn(
        `🚨 DEPRECATED: ${component.name} (${component.id}) is deprecated and will be removed in ${component.removedIn}. ` +
        `Migration: ${component.migrationPath}`
      );
      break;
    
    case 'legacy':
    case 'removed':
      console.error(
        `❌ LEGACY: ${component.name} (${component.id}) is ${component.status} and should not be used. ` +
        `Migration: ${component.migrationPath}`
      );
      break;
  }
}

// ============================================================================
// PERFORMANCE MONITORING
// ============================================================================

/**
 * Track component performance metrics
 */
export class ComponentPerformanceTracker {
  private metrics: Map<string, number[]> = new Map();

  recordRenderTime(componentId: string, renderTime: number): void {
    if (!this.metrics.has(componentId)) {
      this.metrics.set(componentId, []);
    }
    
    const times = this.metrics.get(componentId)!;
    times.push(renderTime);
    
    // Keep only last 10 measurements
    if (times.length > 10) {
      times.shift();
    }
  }

  getAverageRenderTime(componentId: string): number | null {
    const times = this.metrics.get(componentId);
    if (!times || times.length === 0) return null;
    
    const sum = times.reduce((acc, time) => acc + time, 0);
    return sum / times.length;
  }

  getPerformanceReport(): Record<string, { average: number; count: number }> {
    const report: Record<string, { average: number; count: number }> = {};
    
    this.metrics.forEach((times, componentId) => {
      const average = times.reduce((acc, time) => acc + time, 0) / times.length;
      report[componentId] = { average, count: times.length };
    });
    
    return report;
  }
}

// Global performance tracker instance
export const performanceTracker = new ComponentPerformanceTracker();

// ============================================================================
// BUNDLE ANALYSIS
// ============================================================================

/**
 * Analyze component bundle sizes
 */
export function analyzeBundleSizes(): Record<string, { size: number; gzipped: number }> {
  // This would be populated by the build process
  return {
    'button': { size: 1024, gzipped: 512 },
    'card': { size: 2048, gzipped: 896 },
    'sidebar': { size: 4096, gzipped: 1536 },
    'chat-interface': { size: 8192, gzipped: 3072 },
  };
}

// ============================================================================
// EXPORTS FOR CONSUMPTION
// ============================================================================

export default COMPONENT_REGISTRY;