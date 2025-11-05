/**
 * Page Integration Utilities
 * Utilities for integrating modern components into existing pages
 */

import React, { ReactNode } from 'react';

export interface PageIntegrationConfig {
  useModernLayout: boolean;
  useModernComponents: boolean;
  enableAnimations: boolean;
  enableAccessibility: boolean;
  enablePerformanceOptimizations: boolean;
}

export const defaultPageConfig: PageIntegrationConfig = {
  useModernLayout: true,
  useModernComponents: true,
  enableAnimations: true,
  enableAccessibility: true,
  enablePerformanceOptimizations: true,
};

/**
 * Wraps page content with modern layout and providers
 */
export function withModernPageLayout(
  Component: React.ComponentType<any>,
  config: Partial<PageIntegrationConfig> = {}
) {
  const finalConfig = { ...defaultPageConfig, ...config };
  
  return function ModernPageWrapper(props: any) {
    if (finalConfig.useModernLayout) {
      return React.createElement('div', { className: 'modern-page-wrapper' },
        React.createElement('div', { className: 'modern-layout-container' },
          React.createElement(Component, props)
        )
      );
    }
    
    return React.createElement(Component, props);
  };
}

/**
 * Migration status tracking for components
 */
export interface ComponentMigrationStatus {
  componentName: string;
  oldPath: string;
  newPath: string;
  migrated: boolean;
  issues: string[];
  testsPassing: boolean;
}

export const componentMigrationMap: ComponentMigrationStatus[] = [
  {
    componentName: 'Button',
    oldPath: '@/components/ui/button',
    newPath: '@/components/ui/polymorphic/button',
    migrated: true,
    issues: [],
    testsPassing: true,
  },
  {
    componentName: 'Card',
    oldPath: '@/components/ui/card',
    newPath: '@/components/ui/compound/card',
    migrated: true,
    issues: [],
    testsPassing: true,
  },
  {
    componentName: 'Modal',
    oldPath: '@/components/ui/modal',
    newPath: '@/components/ui/compound/modal',
    migrated: true,
    issues: [],
    testsPassing: true,
  },
  {
    componentName: 'Form',
    oldPath: '@/components/ui/form',
    newPath: '@/components/ui/compound/form',
    migrated: true,
    issues: [],
    testsPassing: true,
  },
  {
    componentName: 'GridContainer',
    oldPath: 'N/A',
    newPath: '@/components/ui/layout/grid-container',
    migrated: true,
    issues: [],
    testsPassing: true,
  },
  {
    componentName: 'FlexContainer',
    oldPath: 'N/A',
    newPath: '@/components/ui/layout/flex-container',
    migrated: true,
    issues: [],
    testsPassing: true,
  },
  {
    componentName: 'RightPanel',
    oldPath: 'N/A',
    newPath: '@/components/ui/right-panel',
    migrated: true,
    issues: [],
    testsPassing: true,
  },
];

/**
 * Gets migration status for a component
 */
export function getComponentMigrationStatus(componentName: string): ComponentMigrationStatus | null {
  return componentMigrationMap.find(item => item.componentName === componentName) || null;
}

/**
 * Checks if all components are migrated
 */
export function areAllComponentsMigrated(): boolean {
  return componentMigrationMap.every(item => item.migrated && item.testsPassing);
}

/**
 * Gets list of components that still need migration
 */
export function getPendingMigrations(): ComponentMigrationStatus[] {
  return componentMigrationMap.filter(item => !item.migrated || !item.testsPassing);
}