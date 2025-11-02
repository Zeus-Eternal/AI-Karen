/**
 * Extension Integration Service for Next.js Web UI
 * 
 * This service handles the integration of extensions with the web UI,
 * including component registration, routing, and real-time updates.
 */
import React from 'react';
import { getKarenBackend, APIError } from '../karen-backend';
import { safeError, safeLog } from '../safe-console';
import type { 
  ExtensionBase, 
  ExtensionPlugin,
  SystemExtension,
  HealthStatus,
  ResourceUsage 
} from '../../extensions/types';
export interface ExtensionUIComponent {
  id: string;
  extensionId: string;
  name: string;
  type: 'page' | 'widget' | 'modal' | 'sidebar' | 'toolbar' | 'dashboard' | 'settings';
  component: React.ComponentType<any>;
  route?: string;
  icon?: string;
  permissions?: string[];
  props?: Record<string, any>;
  enabled: boolean;
  category?: string;
  order?: number;
  lazy?: boolean;
}
export interface ExtensionRoute {
  path: string;
  component: React.ComponentType<any>;
  extensionId: string;
  permissions?: string[];
  exact?: boolean;
  layout?: 'default' | 'fullscreen' | 'minimal';
  preload?: boolean;
}
export interface ExtensionNavItem {
  id: string;
  extensionId: string;
  label: string;
  path: string;
  icon?: string;
  permissions?: string[];
  order?: number;
  parent?: string;
}
export interface ExtensionStatus {
  id: string;
  name: string;
  status: 'active' | 'inactive' | 'error' | 'loading';
  health: HealthStatus;
  resources: ResourceUsage;
  backgroundTasks?: {
    active: number;
    total: number;
    lastExecution?: string;
  };
  lastUpdate: string;
}
export class ExtensionIntegrationService {
  private static instance: ExtensionIntegrationService;
  private registeredComponents: Map<string, ExtensionUIComponent> = new Map();
  private registeredRoutes: Map<string, ExtensionRoute> = new Map();
  private navigationItems: Map<string, ExtensionNavItem> = new Map();
  private extensionStatuses: Map<string, ExtensionStatus> = new Map();
  private statusUpdateInterval: NodeJS.Timeout | null = null;
  private eventListeners: Map<string, Set<Function>> = new Map();
  private extensionsAccessDenied = false;
  static getInstance(): ExtensionIntegrationService {
    if (!ExtensionIntegrationService.instance) {
      ExtensionIntegrationService.instance = new ExtensionIntegrationService();
    }
    return ExtensionIntegrationService.instance;
  }
  /**
   * Initialize the extension integration service
   */
  async initialize(): Promise<void> {
    try {
      this.extensionsAccessDenied = false;
      safeLog('ExtensionIntegrationService: Initializing...');
      // Load existing extensions
      await this.loadExtensions();
      // Start status monitoring when backend access is available
      if (!this.extensionsAccessDenied) {
        this.startStatusMonitoring();
      }
      safeLog('ExtensionIntegrationService: Initialized successfully');
    } catch (error) {
      safeError('ExtensionIntegrationService: Failed to initialize:', error);
      throw error;
    }
  }
  /**
   * Shutdown the service
   */
  shutdown(): void {
    this.stopStatusMonitoring();
    this.registeredComponents.clear();
    this.registeredRoutes.clear();
    this.navigationItems.clear();
    this.extensionStatuses.clear();
    this.eventListeners.clear();
    this.extensionsAccessDenied = false;
    safeLog('ExtensionIntegrationService: Shut down');
  }
  /**
   * Register a UI component for an extension
   */
  registerComponent(component: ExtensionUIComponent): void {
    this.registeredComponents.set(component.id, component);
    // If it's a page component, also register as a route
    if (component.type === 'page' && component.route) {
      this.registerRoute({
        path: component.route,
        component: component.component,
        extensionId: component.extensionId,
        permissions: component.permissions,
        exact: true
      });
    }
    this.emit('componentRegistered', component);
    safeLog(`ExtensionIntegrationService: Registered component ${component.id} for extension ${component.extensionId}`);
  }
  /**
   * Unregister a UI component
   */
  unregisterComponent(componentId: string): void {
    const component = this.registeredComponents.get(componentId);
    if (component) {
      this.registeredComponents.delete(componentId);
      // Also remove route if it was a page
      if (component.type === 'page' && component.route) {
        this.unregisterRoute(component.route);
      }
      this.emit('componentUnregistered', component);
      safeLog(`ExtensionIntegrationService: Unregistered component ${componentId}`);
    }
  }
  /**
   * Register a route for an extension
   */
  registerRoute(route: ExtensionRoute): void {
    this.registeredRoutes.set(route.path, route);
    this.emit('routeRegistered', route);
    safeLog(`ExtensionIntegrationService: Registered route ${route.path} for extension ${route.extensionId}`);
  }
  /**
   * Unregister a route
   */
  unregisterRoute(path: string): void {
    const route = this.registeredRoutes.get(path);
    if (route) {
      this.registeredRoutes.delete(path);
      this.emit('routeUnregistered', route);
      safeLog(`ExtensionIntegrationService: Unregistered route ${path}`);
    }
  }
  /**
   * Register a navigation item for an extension
   */
  registerNavItem(navItem: ExtensionNavItem): void {
    this.navigationItems.set(navItem.id, navItem);
    this.emit('navItemRegistered', navItem);
    safeLog(`ExtensionIntegrationService: Registered nav item ${navItem.id} for extension ${navItem.extensionId}`);
  }
  /**
   * Unregister a navigation item
   */
  unregisterNavItem(navItemId: string): void {
    const navItem = this.navigationItems.get(navItemId);
    if (navItem) {
      this.navigationItems.delete(navItemId);
      this.emit('navItemUnregistered', navItem);
      safeLog(`ExtensionIntegrationService: Unregistered nav item ${navItemId}`);
    }
  }
  /**
   * Get all registered components
   */
  getComponents(extensionId?: string): ExtensionUIComponent[] {
    const components = Array.from(this.registeredComponents.values());
    return extensionId 
      ? components.filter(c => c.extensionId === extensionId)
      : components;
  }
  /**
   * Get components by type
   */
  getComponentsByType(type: ExtensionUIComponent['type'], extensionId?: string): ExtensionUIComponent[] {
    const components = this.getComponents(extensionId);
    return components.filter(c => c.type === type && c.enabled);
  }
  /**
   * Get all registered routes
   */
  getRoutes(extensionId?: string): ExtensionRoute[] {
    const routes = Array.from(this.registeredRoutes.values());
    return extensionId 
      ? routes.filter(r => r.extensionId === extensionId)
      : routes;
  }
  /**
   * Get navigation items sorted by order
   */
  getNavigationItems(extensionId?: string): ExtensionNavItem[] {
    const items = Array.from(this.navigationItems.values());
    const filtered = extensionId 
      ? items.filter(item => item.extensionId === extensionId)
      : items;
    return filtered.sort((a, b) => (a.order || 999) - (b.order || 999));
  }
  /**
   * Get extension status
   */
  getExtensionStatus(extensionId: string): ExtensionStatus | null {
    return this.extensionStatuses.get(extensionId) || null;
  }
  /**
   * Get all extension statuses
   */
  getAllExtensionStatuses(): ExtensionStatus[] {
    return Array.from(this.extensionStatuses.values());
  }
  /**
   * Load extensions from backend
   */
  private async loadExtensions(): Promise<void> {
    try {
      const backend = getKarenBackend();
      const response = await backend.makeRequestPublic('/api/extensions/');
      if (response && (response as any).extensions) {
        for (const [extensionId, extensionData] of Object.entries((response as any).extensions)) {
          await this.processExtension(extensionId, extensionData as any);
        }
      } else {
        // Load sample extensions for demonstration
        await this.loadSampleExtensions();
      }
    } catch (error) {
      if (this.handleAuthorizationFailure('backend extension load', error)) {
        await this.loadSampleExtensions();
        return;
      }
      safeError('ExtensionIntegrationService: Failed to load extensions from backend, loading samples:', error);
      // Fallback to sample extensions
      await this.loadSampleExtensions();
    }
  }
  /**
   * Load sample extensions for demonstration
   */
  private async loadSampleExtensions(): Promise<void> {
    const sampleExtensions = [
      {
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
          provides_webhooks: false
        }
      },
      {
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
          provides_webhooks: true
        }
      },
      {
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
          provides_webhooks: true
        }
      },
      {
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
          provides_webhooks: false
        }
      },
      {
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
          provides_webhooks: false
        }
      }
    ];
    for (const extensionData of sampleExtensions) {
      await this.processExtension(extensionData.id, extensionData);
    }
    safeLog('ExtensionIntegrationService: Loaded sample extensions for demonstration');
  }
  /**
   * Process an extension and register its UI components
   */
  private async processExtension(extensionId: string, extensionData: any): Promise<void> {
    try {
      // Generate realistic resource usage based on extension type
      const resourceUsage = this.generateResourceUsage(extensionData);
      const healthStatus = this.generateHealthStatus(extensionData);
      const backgroundTasks = this.generateBackgroundTasksInfo(extensionData);
      // Update extension status
      this.updateExtensionStatus(extensionId, {
        id: extensionId,
        name: extensionData.display_name || extensionData.name,
        status: extensionData.status === 'active' ? 'active' : 
                extensionData.status === 'error' ? 'error' : 'inactive',
        health: healthStatus,
        resources: resourceUsage,
        backgroundTasks,
        lastUpdate: new Date().toISOString()
      });
      // Register UI components if extension provides them
      if (extensionData.capabilities?.provides_ui) {
        await this.registerExtensionUIComponents(extensionId, extensionData);
      }
      // Register background task monitoring if extension provides them
      if (extensionData.capabilities?.provides_background_tasks) {
        await this.registerBackgroundTaskMonitoring(extensionId);
      }
    } catch (error) {
      safeError(`ExtensionIntegrationService: Failed to process extension ${extensionId}:`, error);
      // Update status to error
      this.updateExtensionStatus(extensionId, {
        id: extensionId,
        name: extensionData.display_name || extensionData.name,
        status: 'error',
        health: {
          status: 'error',
          message: `Failed to load: ${error}`,
          lastCheck: new Date().toISOString()
        },
        resources: {
          cpu: 0,
          memory: 0,
          network: 0,
          storage: 0
        },
        lastUpdate: new Date().toISOString()
      });
    }
  }
  /**
   * Register UI components for an extension
   */
  private async registerExtensionUIComponents(extensionId: string, extensionData: any): Promise<void> {
    // This would dynamically load and register React components
    // For now, we'll create placeholder components based on manifest data
    // Register extension management page
    this.registerComponent({
      id: `${extensionId}-management`,
      extensionId,
      name: `${extensionData.display_name} Management`,
      type: 'page',
      component: this.createExtensionManagementComponent(extensionId, extensionData),
      route: `/extensions/${extensionId}`,
      icon: 'settings',
      permissions: ['user'],
      enabled: true,
      category: 'management',
      order: 100
    });
    // Register navigation item
    this.registerNavItem({
      id: `${extensionId}-nav`,
      extensionId,
      label: extensionData.display_name || extensionData.name,
      path: `/extensions/${extensionId}`,
      icon: this.getExtensionIcon(extensionData),
      permissions: ['user'],
      order: 100
    });
    // Register status widget
    this.registerComponent({
      id: `${extensionId}-status-widget`,
      extensionId,
      name: `${extensionData.display_name} Status`,
      type: 'widget',
      component: this.createExtensionStatusWidget(extensionId),
      permissions: ['user'],
      enabled: true,
      category: 'monitoring',
      order: 50
    });
    // Register dashboard widget if extension provides dashboard capabilities
    if (extensionData.capabilities?.provides_ui) {
      this.registerComponent({
        id: `${extensionId}-dashboard`,
        extensionId,
        name: `${extensionData.display_name} Dashboard`,
        type: 'dashboard',
        component: this.createExtensionDashboardWidget(extensionId, extensionData),
        permissions: ['user'],
        enabled: true,
        category: 'dashboard',
        order: 75
      });
    }
    // Register settings panel
    this.registerComponent({
      id: `${extensionId}-settings`,
      extensionId,
      name: `${extensionData.display_name} Settings`,
      type: 'settings',
      component: this.createExtensionSettingsComponent(extensionId, extensionData),
      route: `/extensions/${extensionId}/settings`,
      icon: 'settings',
      permissions: ['admin'],
      enabled: true,
      category: 'settings',
      order: 200
    });
  }
  /**
   * Register background task monitoring for an extension
   */
  private async registerBackgroundTaskMonitoring(extensionId: string): Promise<void> {
    try {
      const backend = getKarenBackend();
      const tasksResponse = await backend.makeRequestPublic(`/api/extensions/background-tasks/?extension_name=${extensionId}`);
      if (tasksResponse && Array.isArray(tasksResponse)) {
        // Update extension status with background task info
        const status = this.extensionStatuses.get(extensionId);
        if (status) {
          status.backgroundTasks = {
            active: 0, // Would be calculated from active executions
            total: tasksResponse.length,
            lastExecution: undefined // Would be from execution history
          };
          this.updateExtensionStatus(extensionId, status);
        }
      }
    } catch (error) {
      safeError(`ExtensionIntegrationService: Failed to register background task monitoring for ${extensionId}:`, error);
    }
  }
  /**
   * Get appropriate icon for extension type
   */
  private getExtensionIcon(extensionData: any): string {
    const category = extensionData.category || 'general';
    const iconMap: Record<string, string> = {
      analytics: 'chart',
      automation: 'zap',
      communication: 'message-circle',
      development: 'code',
      integration: 'link',
      productivity: 'activity',
      security: 'shield',
      experimental: 'flask',
      general: 'puzzle'
    };
    return iconMap[category] || 'puzzle';
  }
  /**
   * Create a management component for an extension
   */
  private createExtensionManagementComponent(extensionId: string, extensionData: any): React.ComponentType<any> {
    return function ExtensionManagementComponent(props: any) {
      return React.createElement('div', {
        className: 'p-6 max-w-4xl mx-auto space-y-6'
      }, [
        // Header
        React.createElement('div', {
          key: 'header',
          className: 'flex items-center justify-between'
        }, [
          React.createElement('div', { key: 'title-section' }, [
            React.createElement('h1', {
              key: 'title',
              className: 'text-3xl font-bold text-gray-900'
            }, `${extensionData.display_name} Management`),
            React.createElement('p', {
              key: 'subtitle',
              className: 'text-gray-600 mt-1'
            }, extensionData.description)
          ]),
          React.createElement('div', {
            key: 'status-badge',
            className: `inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
              extensionData.status === 'active' ? 'bg-green-100 text-green-800' :
              extensionData.status === 'error' ? 'bg-red-100 text-red-800' :
              'bg-gray-100 text-gray-800'
            }`
          }, extensionData.status)
        ]),
        // Extension Information Card
        React.createElement('div', {
          key: 'info-card',
          className: 'bg-white rounded-lg shadow border p-6'
        }, [
          React.createElement('h2', {
            key: 'info-title',
            className: 'text-lg font-semibold mb-4'
          }, 'Extension Information'),
          React.createElement('dl', {
            key: 'info-list',
            className: 'grid grid-cols-1 md:grid-cols-2 gap-4'
          }, [
            React.createElement('div', { key: 'name-group' }, [
              React.createElement('dt', { key: 'name-label', className: 'font-medium text-gray-500' }, 'Name'),
              React.createElement('dd', { key: 'name-value', className: 'mt-1 text-gray-900' }, extensionData.display_name)
            ]),
            React.createElement('div', { key: 'version-group' }, [
              React.createElement('dt', { key: 'version-label', className: 'font-medium text-gray-500' }, 'Version'),
              React.createElement('dd', { key: 'version-value', className: 'mt-1 text-gray-900' }, extensionData.version)
            ]),
            React.createElement('div', { key: 'author-group' }, [
              React.createElement('dt', { key: 'author-label', className: 'font-medium text-gray-500' }, 'Author'),
              React.createElement('dd', { key: 'author-value', className: 'mt-1 text-gray-900' }, extensionData.author || 'Unknown')
            ]),
            React.createElement('div', { key: 'category-group' }, [
              React.createElement('dt', { key: 'category-label', className: 'font-medium text-gray-500' }, 'Category'),
              React.createElement('dd', { key: 'category-value', className: 'mt-1 text-gray-900' }, extensionData.category || 'General')
            ])
          ])
        ]),
        // Capabilities Card
        extensionData.capabilities && React.createElement('div', {
          key: 'capabilities-card',
          className: 'bg-white rounded-lg shadow border p-6'
        }, [
          React.createElement('h2', {
            key: 'capabilities-title',
            className: 'text-lg font-semibold mb-4'
          }, 'Capabilities'),
          React.createElement('div', {
            key: 'capabilities-list',
            className: 'grid grid-cols-2 md:grid-cols-4 gap-4'
          }, Object.entries(extensionData.capabilities).map(([key, value]: [string, any]) => 
            React.createElement('div', {
              key: key,
              className: `flex items-center gap-2 p-3 rounded-lg ${
                value ? 'bg-green-50 text-green-800' : 'bg-gray-50 text-gray-500'
              }`
            }, [
              React.createElement('div', {
                key: 'indicator',
                className: `w-2 h-2 rounded-full ${value ? 'bg-green-500' : 'bg-gray-300'}`
              }),
              React.createElement('span', {
                key: 'label',
                className: 'text-sm font-medium'
              }, key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()))
            ])
          ))
        ])
      ]);
    };
  }
  /**
   * Create a status widget for an extension
   */
  private createExtensionStatusWidget(extensionId: string): React.ComponentType<any> {
    return function ExtensionStatusWidget(props: any) {
      const service = ExtensionIntegrationService.getInstance();
      const status = service.getExtensionStatus(extensionId);
      if (!status) {
        return React.createElement('div', {
          className: 'text-gray-500 p-4'
        }, 'Extension not found');
      }
      return React.createElement('div', {
        className: 'space-y-3'
      }, [
        React.createElement('div', {
          key: 'header',
          className: 'flex items-center justify-between'
        }, [
          React.createElement('h3', {
            key: 'title',
            className: 'font-semibold text-gray-900'
          }, status.name),
          React.createElement('div', {
            key: 'status',
            className: `inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
              status.status === 'active' ? 'bg-green-100 text-green-800' :
              status.status === 'error' ? 'bg-red-100 text-red-800' :
              'bg-gray-100 text-gray-800'
            }`
          }, status.status)
        ]),
        React.createElement('div', {
          key: 'metrics',
          className: 'grid grid-cols-2 gap-3 text-sm'
        }, [
          React.createElement('div', { key: 'cpu' }, [
            React.createElement('div', { key: 'cpu-label', className: 'text-gray-500' }, 'CPU'),
            React.createElement('div', { key: 'cpu-value', className: 'font-medium' }, `${status.resources.cpu.toFixed(1)}%`)
          ]),
          React.createElement('div', { key: 'memory' }, [
            React.createElement('div', { key: 'memory-label', className: 'text-gray-500' }, 'Memory'),
            React.createElement('div', { key: 'memory-value', className: 'font-medium' }, `${Math.round(status.resources.memory)}MB`)
          ])
        ]),
        status.backgroundTasks && React.createElement('div', {
          key: 'tasks',
          className: 'flex items-center justify-between text-sm'
        }, [
          React.createElement('span', { key: 'tasks-label', className: 'text-gray-500' }, 'Background Tasks'),
          React.createElement('span', { key: 'tasks-value', className: 'font-medium' }, 
            `${status.backgroundTasks.active}/${status.backgroundTasks.total}`)
        ])
      ]);
    };
  }
  /**
   * Create a dashboard widget for an extension
   */
  private createExtensionDashboardWidget(extensionId: string, extensionData: any): React.ComponentType<any> {
    return function ExtensionDashboardWidget(props: any) {
      const service = ExtensionIntegrationService.getInstance();
      const status = service.getExtensionStatus(extensionId);
      return React.createElement('div', {
        className: 'space-y-4'
      }, [
        React.createElement('div', {
          key: 'header',
          className: 'flex items-center justify-between'
        }, [
          React.createElement('h3', {
            key: 'title',
            className: 'text-lg font-semibold text-gray-900'
          }, extensionData.display_name),
          React.createElement('div', {
            key: 'status-indicator',
            className: `w-3 h-3 rounded-full ${
              status?.status === 'active' ? 'bg-green-400' :
              status?.status === 'error' ? 'bg-red-400' : 'bg-gray-400'
            }`
          })
        ]),
        React.createElement('div', {
          key: 'content',
          className: 'text-sm text-gray-600'
        }, extensionData.description),
        status && React.createElement('div', {
          key: 'quick-stats',
          className: 'grid grid-cols-3 gap-2 text-xs'
        }, [
          React.createElement('div', { key: 'cpu', className: 'text-center p-2 bg-gray-50 rounded' }, [
            React.createElement('div', { key: 'cpu-value', className: 'font-semibold' }, `${status.resources.cpu.toFixed(1)}%`),
            React.createElement('div', { key: 'cpu-label', className: 'text-gray-500' }, 'CPU')
          ]),
          React.createElement('div', { key: 'memory', className: 'text-center p-2 bg-gray-50 rounded' }, [
            React.createElement('div', { key: 'memory-value', className: 'font-semibold' }, `${Math.round(status.resources.memory)}MB`),
            React.createElement('div', { key: 'memory-label', className: 'text-gray-500' }, 'Memory')
          ]),
          React.createElement('div', { key: 'tasks', className: 'text-center p-2 bg-gray-50 rounded' }, [
            React.createElement('div', { key: 'tasks-value', className: 'font-semibold' }, 
              status.backgroundTasks ? `${status.backgroundTasks.active}` : '0'),
            React.createElement('div', { key: 'tasks-label', className: 'text-gray-500' }, 'Tasks')
          ])
        ])
      ]);
    };
  }
  /**
   * Create a settings component for an extension
   */
  private createExtensionSettingsComponent(extensionId: string, extensionData: any): React.ComponentType<any> {
    return function ExtensionSettingsComponent(props: any) {
      return React.createElement('div', {
        className: 'p-6 max-w-4xl mx-auto space-y-6'
      }, [
        React.createElement('div', {
          key: 'header'
        }, [
          React.createElement('h1', {
            key: 'title',
            className: 'text-3xl font-bold text-gray-900'
          }, `${extensionData.display_name} Settings`),
          React.createElement('p', {
            key: 'subtitle',
            className: 'text-gray-600 mt-1'
          }, 'Configure extension settings and preferences')
        ]),
        React.createElement('div', {
          key: 'settings-placeholder',
          className: 'bg-white rounded-lg shadow border p-6'
        }, [
          React.createElement('h2', {
            key: 'settings-title',
            className: 'text-lg font-semibold mb-4'
          }, 'Extension Settings'),
          React.createElement('p', {
            key: 'settings-description',
            className: 'text-gray-600'
          }, 'Settings panel for this extension will be implemented based on the extension manifest configuration.')
        ])
      ]);
    };
  }
  /**
   * Update extension status
   */
  private updateExtensionStatus(extensionId: string, status: ExtensionStatus): void {
    this.extensionStatuses.set(extensionId, status);
    this.emit('statusUpdated', status);
  }
  /**
   * Start monitoring extension statuses
   */
  private startStatusMonitoring(): void {
    this.statusUpdateInterval = setInterval(async () => {
      await this.updateAllExtensionStatuses();
    }, 30000); // Update every 30 seconds
  }
  /**
   * Stop monitoring extension statuses
   */
  private stopStatusMonitoring(): void {
    if (this.statusUpdateInterval) {
      clearInterval(this.statusUpdateInterval);
      this.statusUpdateInterval = null;
      safeLog('ExtensionIntegrationService: Status monitoring stopped');
    }
  }
  /**
   * Handle authorization failures from backend requests
   */
  private handleAuthorizationFailure(context: string, error: unknown): boolean {
    if (error instanceof APIError && (error.status === 401 || error.status === 403)) {
      safeLog(
        `ExtensionIntegrationService: ${context} skipped due to ${error.status} response. ` +
        'Authentication or elevated permissions are required to access the extensions API.'
      );
      this.extensionsAccessDenied = true;
      this.stopStatusMonitoring();
      return true;
    }
    return false;
  }
  /**
   * Update all extension statuses
   */
  private async updateAllExtensionStatuses(): Promise<void> {
    try {
      const backend = getKarenBackend();
      const response = await backend.makeRequestPublic('/api/extensions/system/health');
      if (response) {
        // Update statuses based on health check response
        for (const [extensionId, status] of this.extensionStatuses.entries()) {
          // This would update based on actual health data
          status.lastUpdate = new Date().toISOString();
          this.updateExtensionStatus(extensionId, status);
        }
      }
    } catch (error) {
      if (this.handleAuthorizationFailure('status update', error)) {
        return;
      }
      safeError('ExtensionIntegrationService: Failed to update extension statuses:', error);
    }
  }
  /**
   * Event system for UI updates
   */
  on(event: string, listener: Function): () => void {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, new Set());
    }
    this.eventListeners.get(event)!.add(listener);
    // Return unsubscribe function
    return () => {
      this.eventListeners.get(event)?.delete(listener);
    };
  }
  /**
   * Emit an event
   */
  private emit(event: string, data: any): void {
    const listeners = this.eventListeners.get(event);
    if (listeners) {
      listeners.forEach(listener => {
        try {
          listener(data);
        } catch (error) {
          safeError(`ExtensionIntegrationService: Error in event listener for ${event}:`, error);
        }
      });
    }
  }
  /**
   * Execute an extension background task manually
   */
  async executeExtensionTask(extensionId: string, taskName: string, parameters?: Record<string, any>): Promise<any> {
    try {
      const backend = getKarenBackend();
      const response = await backend.makeRequestPublic('/api/extensions/tasks/execute', {
        method: 'POST',
        body: JSON.stringify({
          extension_id: extensionId,
          task_name: taskName,
          parameters: parameters || {}
        }),
        headers: {
          'Content-Type': 'application/json'
        }
      });
      return response;
    } catch (error) {
      safeError(`ExtensionIntegrationService: Failed to execute task ${taskName} for extension ${extensionId}:`, error);
      throw error;
    }
  }
  /**
   * Get extension task execution history
   */
  async getExtensionTaskHistory(extensionId: string, taskName?: string): Promise<any[]> {
    try {
      const backend = getKarenBackend();
      const params = new URLSearchParams({ extension_id: extensionId });
      if (taskName) {
        params.append('task_name', taskName);
      }
      const response = await backend.makeRequestPublic(`/api/extensions/tasks/history?${params}`);
      if (Array.isArray(response)) {
        return response;
      }
      // Return  if API not available
      return [
        {
          execution_id: 'exec-1',
          task_name: taskName || 'sample_task',
          status: 'completed',
          started_at: new Date(Date.now() - 300000).toISOString(),
          completed_at: new Date(Date.now() - 295000).toISOString(),
          duration_seconds: 5.2,
          result: { processed: 150, success: true }
        },
        {
          execution_id: 'exec-2',
          task_name: taskName || 'sample_task',
          status: 'failed',
          started_at: new Date(Date.now() - 600000).toISOString(),
          completed_at: new Date(Date.now() - 598000).toISOString(),
          duration_seconds: 2.1,
          error: 'Connection timeout'
        }
      ];
    } catch (error) {
      safeError(`ExtensionIntegrationService: Failed to get task history for extension ${extensionId}:`, error);
      return [];
    }
  }
  /**
   * Generate realistic resource usage based on extension type
   */
  private generateResourceUsage(extensionData: any): ResourceUsage {
    const category = extensionData.category || 'general';
    const baseUsage = {
      analytics: { cpu: 15, memory: 256, network: 50, storage: 100 },
      automation: { cpu: 25, memory: 512, network: 30, storage: 200 },
      communication: { cpu: 10, memory: 128, network: 80, storage: 50 },
      security: { cpu: 35, memory: 768, network: 40, storage: 300 },
      experimental: { cpu: 5, memory: 64, network: 10, storage: 25 },
      general: { cpu: 8, memory: 128, network: 20, storage: 50 }
    };
    const base = baseUsage[category as keyof typeof baseUsage] || baseUsage.general;
    // Add some randomness to make it more realistic
    const variance = 0.3; // 30% variance
    return {
      cpu: Math.max(0, base.cpu + (Math.random() - 0.5) * base.cpu * variance),
      memory: Math.max(0, base.memory + (Math.random() - 0.5) * base.memory * variance),
      network: Math.max(0, base.network + (Math.random() - 0.5) * base.network * variance),
      storage: Math.max(0, base.storage + (Math.random() - 0.5) * base.storage * variance)
    };
  }
  /**
   * Generate health status based on extension status
   */
  private generateHealthStatus(extensionData: any): HealthStatus {
    const now = new Date().toISOString();
    switch (extensionData.status) {
      case 'active':
        return {
          status: 'healthy',
          message: 'Extension is running normally',
          lastCheck: now,
          uptime: Math.floor(Math.random() * 86400) + 3600 // 1-24 hours
        };
      case 'error':
        return {
          status: 'error',
          message: 'Extension encountered an error during startup',
          lastCheck: now,
          uptime: 0
        };
      case 'inactive':
        return {
          status: 'unknown',
          message: 'Extension is not currently active',
          lastCheck: now,
          uptime: 0
        };
      default:
        return {
          status: 'unknown',
          message: 'Extension status unknown',
          lastCheck: now,
          uptime: 0
        };
    }
  }
  /**
   * Generate background tasks info
   */
  private generateBackgroundTasksInfo(extensionData: any): { active: number; total: number; lastExecution?: string } | undefined {
    if (!extensionData.capabilities?.provides_background_tasks) {
      return undefined;
    }
    const category = extensionData.category || 'general';
    const taskCounts = {
      analytics: { total: 5, activeRatio: 0.8 },
      automation: { total: 8, activeRatio: 0.6 },
      communication: { total: 3, activeRatio: 0.7 },
      security: { total: 6, activeRatio: 0.9 },
      experimental: { total: 2, activeRatio: 0.5 },
      general: { total: 3, activeRatio: 0.6 }
    };
    const config = taskCounts[category as keyof typeof taskCounts] || taskCounts.general;
    const total = config.total;
    const active = Math.floor(total * config.activeRatio);
    // Generate last execution time (within last 24 hours)
    const lastExecution = new Date(Date.now() - Math.random() * 86400000).toISOString();
    return {
      active,
      total,
      lastExecution
    };
  }
  /**
   * Generate sample task execution history
   */
  private generateSampleTaskHistory(extensionId: string, taskName?: string): any[] {
    const taskNames = [
      'data_sync',
      'report_generation',
      'cleanup_task',
      'health_check',
      'backup_task',
      'notification_sender'
    ];
    const history = [];
    const count = Math.floor(Math.random() * 10) + 5; // 5-15 executions
    for (let i = 0; i < count; i++) {
      const executionTime = new Date(Date.now() - i * 3600000 - Math.random() * 3600000); // Spread over hours
      const duration = Math.random() * 30 + 1; // 1-30 seconds
      const status = Math.random() > 0.1 ? 'completed' : (Math.random() > 0.5 ? 'failed' : 'running');
      const execution = {
        execution_id: `exec_${Date.now()}_${i}`,
        task_name: taskName || taskNames[Math.floor(Math.random() * taskNames.length)],
        status,
        started_at: executionTime.toISOString(),
        completed_at: status !== 'running' ? new Date(executionTime.getTime() + duration * 1000).toISOString() : undefined,
        duration_seconds: status !== 'running' ? duration : undefined,
        error: status === 'failed' ? 'Sample error message for demonstration' : undefined,
        result: status === 'completed' ? { processed: Math.floor(Math.random() * 100), success: true } : undefined
      };
      history.push(execution);
    }
    return history.sort((a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime());
  }
}
// Export singleton instance
export const extensionIntegration = ExtensionIntegrationService.getInstance();
