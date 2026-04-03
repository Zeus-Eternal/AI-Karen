import React, { Suspense, lazy } from 'react';
import { Loader2 } from 'lucide-react';

// Pre-defined mapping of plugin IDs to their component imports.
// This enforces the Plugin GUI Hook Contract where UI components are 
// statically bundled but lazy-loaded on demand.
const pluginUIComponents: Record<string, React.LazyExoticComponent<any>> = {
  'karen-weather-services': lazy(() => import('./WeatherPluginPage').catch(() => ({ default: () => <div className="text-sm p-4 text-center">UI Module Not Found or Failed to Load</div> }))),
  'karen-datetime-services': lazy(() => import('./DateTimePluginPage').catch(() => ({ default: () => <div className="text-sm p-4 text-center">UI Module Not Found</div> }))),
  'karen-gmail-services': lazy(() => import('./GmailPluginPage').catch(() => ({ default: () => <div className="text-sm p-4 text-center">UI Module Not Found</div> }))),
  'karen-data-connector': lazy(() => import('./DataConnectorPluginPage').catch(() => ({ default: () => <div className="text-sm p-4 text-center">UI Module Not Found</div> }))),
};

export interface PluginHostProps {
  pluginId: string;
  fallback?: React.ReactNode;
}

export function PluginHost({ pluginId, fallback }: PluginHostProps) {
  const PluginComponent = pluginUIComponents[pluginId];

  if (!PluginComponent) {
    return (
      <div className="p-4 border rounded bg-muted/50 text-center text-muted-foreground text-sm flex flex-col items-center justify-center">
        This plugin does not provide a UI component or is not supported yet.
      </div>
    );
  }

  return (
    <Suspense 
      fallback={
        fallback || (
          <div className="flex items-center justify-center p-8">
            <Loader2 className="h-6 w-6 animate-spin text-primary" />
          </div>
        )
      }
    >
      <PluginComponent />
    </Suspense>
  );
}
