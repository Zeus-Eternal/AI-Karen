/**
 * Plugin UI Component Registry - Production-ready component registration system.
 *
 * Handles dynamic registration and deregistration of plugin UI components
 * with proper lifecycle management, error boundaries, and lazy loading.
 */

import React, { Suspense, ComponentType, ReactNode, ErrorInfo } from 'react';

// Types
export interface PluginComponentDefinition {
  pluginId: string;
  componentId: string;
  component: ComponentType<any>;
  zone: string;
  order?: number;
  label?: string;
  capabilities?: string[];
  requiresAuth?: boolean;
}

export interface PluginZone {
  zoneId: string;
  components: PluginComponentDefinition[];
  maxComponents?: number;
}

export interface ComponentRegistrationResult {
  success: boolean;
  componentId: string;
  error?: string;
}

export interface ComponentDeregistrationResult {
  success: boolean;
  componentId: string;
  removed: boolean;
}

// Error boundary for plugin components
class PluginErrorBoundary extends React.Component<
  { children?: ReactNode; pluginId: string; componentId: string },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children?: ReactNode; pluginId: string; componentId: string }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error(`Plugin component error in ${this.props.pluginId}:${this.props.componentId}:`, error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return React.createElement('div', {
        className: 'p-4 border border-destructive/20 rounded-lg bg-destructive/5'
      }, [
        React.createElement('div', {
          key: 'header',
          className: 'flex items-center gap-2 text-destructive'
        }, React.createElement('span', {
          className: 'text-sm font-medium'
        }, 'Plugin Error')),
        React.createElement('p', {
          key: 'message',
          className: 'text-xs text-muted-foreground mt-1'
        }, `Component ${this.props.pluginId}:${this.props.componentId} failed to load`),
        React.createElement('details', {
          key: 'details',
          className: 'mt-2'
        }, [
          React.createElement('summary', {
            key: 'summary',
            className: 'text-xs cursor-pointer'
          }, 'Error details'),
          React.createElement('pre', {
            key: 'error',
            className: 'text-xs mt-1 p-2 bg-muted rounded overflow-auto'
          }, this.state.error?.message || 'Unknown error')
        ])
      ]);
    }

    return this.props.children;
  }
}

// Loading component for lazy-loaded plugin components
const PluginComponentLoader: React.FC<{ pluginId: string; componentId: string }> = ({
  pluginId,
  componentId
}) =>
  React.createElement('div', {
    className: 'p-4 border border-muted rounded-lg bg-muted/20 animate-pulse'
  }, React.createElement('div', {
    className: 'flex items-center gap-2'
  }, [
    React.createElement('div', {
      key: 'spinner',
      className: 'w-4 h-4 bg-muted rounded'
    }),
    React.createElement('span', {
      key: 'text',
      className: 'text-sm text-muted-foreground'
    }, `Loading ${pluginId}:${componentId}...`)
  ]));

// Plugin Component Registry
class PluginComponentRegistry {
  private static instance: PluginComponentRegistry;
  private zones: Map<string, PluginZone> = new Map();
  private components: Map<string, PluginComponentDefinition> = new Map();
  private lazyComponents: Map<string, ComponentType<any>> = new Map();

  private constructor() {
    // Initialize default zones
    this.initializeDefaultZones();
  }

  public static getInstance(): PluginComponentRegistry {
    if (!PluginComponentRegistry.instance) {
      PluginComponentRegistry.instance = new PluginComponentRegistry();
    }
    return PluginComponentRegistry.instance;
  }

  private initializeDefaultZones() {
    // Define standard UI zones where plugins can register components
    const defaultZones = [
      { zoneId: 'sidebar.plugins', maxComponents: 10 },
      { zoneId: 'header.actions', maxComponents: 5 },
      { zoneId: 'dashboard.widgets', maxComponents: 20 },
      { zoneId: 'settings.tabs', maxComponents: 10 },
      { zoneId: 'footer.links', maxComponents: 5 },
      { zoneId: 'modal.overlays', maxComponents: 3 },
      { zoneId: 'context.menus', maxComponents: 15 },
    ];

    for (const zone of defaultZones) {
      this.zones.set(zone.zoneId, {
        zoneId: zone.zoneId,
        components: [],
        maxComponents: zone.maxComponents,
      });
    }
  }

  /**
   * Register a plugin component
   */
  public registerComponent(definition: PluginComponentDefinition): ComponentRegistrationResult {
    try {
      const componentKey = `${definition.pluginId}:${definition.componentId}`;

      // Check if component already exists
      if (this.components.has(componentKey)) {
        return {
          success: false,
          componentId: componentKey,
          error: 'Component already registered',
        };
      }

      // Validate zone exists
      if (!this.zones.has(definition.zone)) {
        return {
          success: false,
          componentId: componentKey,
          error: `Zone '${definition.zone}' does not exist`,
        };
      }

      const zone = this.zones.get(definition.zone)!;

      // Check zone capacity
      if (zone.maxComponents && zone.components.length >= zone.maxComponents) {
        return {
          success: false,
          componentId: componentKey,
          error: `Zone '${definition.zone}' is at maximum capacity (${zone.maxComponents})`,
        };
      }

      // Register component
      this.components.set(componentKey, definition);

      // Add to zone (sorted by order)
      zone.components.push(definition);
      zone.components.sort((a, b) => (a.order || 999) - (b.order || 999));

      console.log(`Plugin component registered: ${componentKey} in zone ${definition.zone}`);

      return {
        success: true,
        componentId: componentKey,
      };
    } catch (error) {
      const componentKey = `${definition.pluginId}:${definition.componentId}`;
      return {
        success: false,
        componentId: componentKey,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Deregister a plugin component
   */
  public deregisterComponent(pluginId: string, componentId: string): ComponentDeregistrationResult {
    try {
      const componentKey = `${pluginId}:${componentId}`;

      // Check if component exists
      const definition = this.components.get(componentKey);
      if (!definition) {
        return {
          success: true, // Not an error if component doesn't exist
          componentId: componentKey,
          removed: false,
        };
      }

      // Remove from components map
      this.components.delete(componentKey);

      // Remove from zone
      const zone = this.zones.get(definition.zone);
      if (zone) {
        zone.components = zone.components.filter(
          comp => !(comp.pluginId === pluginId && comp.componentId === componentId)
        );
      }

      // Clean up lazy component if it exists
      this.lazyComponents.delete(componentKey);

      console.log(`Plugin component deregistered: ${componentKey}`);

      return {
        success: true,
        componentId: componentKey,
        removed: true,
      };
    } catch (error) {
      const componentKey = `${pluginId}:${componentId}`;
      console.error(`Failed to deregister component ${componentKey}:`, error);
      return {
        success: false,
        componentId: componentKey,
        removed: false,
      };
    }
  }

  /**
   * Deregister all components for a plugin
   */
  public deregisterPluginComponents(pluginId: string): ComponentDeregistrationResult[] {
    const results: ComponentDeregistrationResult[] = [];
    const componentsToRemove = Array.from(this.components.entries())
      .filter(([_, def]) => def.pluginId === pluginId);

    for (const [componentKey, _] of componentsToRemove) {
      const [pid, cid] = componentKey.split(':');
      results.push(this.deregisterComponent(pid, cid));
    }

    return results;
  }

  /**
   * Get components for a specific zone
   */
  public getZoneComponents(zoneId: string): PluginComponentDefinition[] {
    const zone = this.zones.get(zoneId);
    return zone ? [...zone.components] : [];
  }

  /**
   * Get all registered zones
   */
  public getZones(): string[] {
    return Array.from(this.zones.keys());
  }

  /**
   * Get component definition
   */
  public getComponent(pluginId: string, componentId: string): PluginComponentDefinition | null {
    const componentKey = `${pluginId}:${componentId}`;
    return this.components.get(componentKey) || null;
  }

  /**
   * Check if component is registered
   */
  public isComponentRegistered(pluginId: string, componentId: string): boolean {
    const componentKey = `${pluginId}:${componentId}`;
    return this.components.has(componentKey);
  }

  /**
   * Render a component with error boundary and lazy loading
   */
  public renderComponent(
    pluginId: string,
    componentId: string,
    props: Record<string, any> = {}
  ): ReactNode {
    const definition = this.getComponent(pluginId, componentId);

    if (!definition) {
      return React.createElement('div', {
        className: 'p-4 border border-destructive/20 rounded-lg bg-destructive/5'
      }, React.createElement('p', {
        className: 'text-sm text-destructive'
      }, `Component ${pluginId}:${componentId} not registered`));
    }

    const Component = definition.component;

    return React.createElement(PluginErrorBoundary, {
      pluginId,
      componentId
    }, React.createElement(Suspense, {
      fallback: React.createElement(PluginComponentLoader, { pluginId, componentId })
    }, React.createElement(Component, props)));
  }

  /**
   * Render all components for a zone
   */
  public renderZoneComponents(
    zoneId: string,
    props: Record<string, any> = {}
  ): ReactNode[] {
    const components = this.getZoneComponents(zoneId);

    return components.map(definition =>
      this.renderComponent(definition.pluginId, definition.componentId, props)
    );
  }

  /**
   * Get registry statistics
   */
  public getStats(): {
    totalComponents: number;
    totalZones: number;
    zoneStats: Record<string, number>;
  } {
    const zoneStats: Record<string, number> = {};
    Array.from(this.zones.entries()).forEach(([zoneId, zone]) => {
      zoneStats[zoneId] = zone.components.length;
    });

    return {
      totalComponents: this.components.size,
      totalZones: this.zones.size,
      zoneStats,
    };
  }

  /**
   * Clear all registered components (for testing/cleanup)
   */
  public clear(): void {
    this.components.clear();
    this.lazyComponents.clear();
    for (const zone of this.zones.values()) {
      zone.components = [];
    }
  }
}

// Export singleton instance
export const pluginComponentRegistry = PluginComponentRegistry.getInstance();

// Convenience functions
export const registerPluginComponent = (definition: PluginComponentDefinition) =>
  pluginComponentRegistry.registerComponent(definition);

export const deregisterPluginComponent = (pluginId: string, componentId: string) =>
  pluginComponentRegistry.deregisterComponent(pluginId, componentId);

export const deregisterPluginComponents = (pluginId: string) =>
  pluginComponentRegistry.deregisterPluginComponents(pluginId);

export const renderPluginComponent = (
  pluginId: string,
  componentId: string,
  props?: Record<string, any>
) => pluginComponentRegistry.renderComponent(pluginId, componentId, props);

export const renderZoneComponents = (
  zoneId: string,
  props?: Record<string, any>
) => pluginComponentRegistry.renderZoneComponents(zoneId, props);

export const getPluginComponentStats = () => pluginComponentRegistry.getStats();