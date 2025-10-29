/**
 * Extension Integration Test Page
 * 
 * Test page to verify extension integration is working
 */

'use client';

import React, { useState } from 'react';
import { 
  useExtensionStatuses, 
  useExtensionRoutes, 
  useExtensionNavigation,
  useExtensionHealth,
  useExtensionPerformance,
  useExtensionTaskMonitoring
} from '@/lib/extensions/hooks';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  ExtensionMarketplace,
  ExtensionManager,
  ExtensionConfigurationPanel,
  ExtensionDebugger,
  ExtensionPerformanceMonitor
} from '@/components/extensions';

export default function ExtensionTestPage() {
  const [activeTab, setActiveTab] = useState('statuses');
  const { statuses, loading: statusesLoading, error: statusesError } = useExtensionStatuses();
  const routes = useExtensionRoutes();
  const navItems = useExtensionNavigation();
  const healthData = useExtensionHealth();
  const performanceData = useExtensionPerformance();
  const taskData = useExtensionTaskMonitoring();

  return (
    <div className="container mx-auto px-4 py-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Extension Integration Test</h1>
        <p className="text-gray-600 mt-1">Testing extension integration functionality</p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="statuses">Statuses</TabsTrigger>
          <TabsTrigger value="marketplace">Marketplace</TabsTrigger>
          <TabsTrigger value="manager">Manager</TabsTrigger>
          <TabsTrigger value="config">Configuration</TabsTrigger>
          <TabsTrigger value="debug">Debugging</TabsTrigger>
          <TabsTrigger value="monitor">Monitoring</TabsTrigger>
        </TabsList>

        <TabsContent value="statuses" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Extension Statuses</CardTitle>
              <CardDescription>Current status of all extensions</CardDescription>
            </CardHeader>
            <CardContent>
              {statusesLoading && <p>Loading...</p>}
              {statusesError && <p className="text-red-600">Error: {statusesError}</p>}
              {statuses.length === 0 && !statusesLoading && <p>No extensions found</p>}
              
              <div className="space-y-3">
                {statuses.map((status) => (
                  <div key={status.id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div>
                      <h3 className="font-semibold">{status.name}</h3>
                      <p className="text-sm text-gray-500">ID: {status.id}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={
                        status.status === 'active' ? 'default' :
                        status.status === 'error' ? 'destructive' : 'secondary'
                      }>
                        {status.status}
                      </Badge>
                      <div className="text-sm text-gray-500">
                        CPU: {status.resources.cpu.toFixed(1)}%
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="marketplace">
          <ExtensionMarketplace
            onInstall={async (id) => console.log('Install:', id)}
            onUninstall={async (id) => console.log('Uninstall:', id)}
          />
        </TabsContent>

        <TabsContent value="manager">
          <ExtensionManager
            onInstallFromFile={async (file) => console.log('Install from file:', file.name)}
            onUninstall={async (id) => console.log('Uninstall:', id)}
            onEnable={async (id) => console.log('Enable:', id)}
            onDisable={async (id) => console.log('Disable:', id)}
            onConfigure={(id) => console.log('Configure:', id)}
            onViewLogs={(id) => console.log('View logs:', id)}
            onViewMetrics={(id) => console.log('View metrics:', id)}
          />
        </TabsContent>

        <TabsContent value="config">
          <ExtensionConfigurationPanel
            extensionId="test-extension"
            extensionName="Test Extension"
            onSave={async (settings) => console.log('Save settings:', settings)}
            onReset={async () => console.log('Reset settings')}
            onPermissionChange={async (perm, granted) => console.log('Permission change:', perm, granted)}
          />
        </TabsContent>

        <TabsContent value="debug">
          <ExtensionDebugger
            extensionId="test-extension"
            extensionName="Test Extension"
          />
        </TabsContent>

        <TabsContent value="monitor">
          <ExtensionPerformanceMonitor />
        </TabsContent>
      </Tabs>
    </div>
  );
}