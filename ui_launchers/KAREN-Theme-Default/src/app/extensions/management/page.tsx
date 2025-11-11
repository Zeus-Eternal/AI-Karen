"use client";
import React, { useState, useCallback } from "react";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../../../components/ui/tabs";
import { Button } from "../../../components/ui/button";

import Link from "next/link";
/**
 * Extension Management Page
 *
 * Comprehensive extension management interface that integrates all
 * extension management components including marketplace, configuration,
 * debugging, and performance monitoring.
 */

import { ExtensionMarketplace } from "../../../components/extensions/marketplace/ExtensionMarketplace";
import { ExtensionManager } from "../../../components/extensions/management/ExtensionManager";
import { ExtensionConfigurationPanel } from "../../../components/extensions/settings/ExtensionConfigurationPanel";
import { ExtensionDebugger } from "../../../components/extensions/debugging/ExtensionDebugger";
import { ExtensionPerformanceMonitor } from "../../../components/extensions/monitoring/ExtensionPerformanceMonitor";

import { ArrowLeft, Store, Cog, Settings, Bug, Activity } from "lucide-react";

export default function ExtensionManagementPage() {
  const [activeTab, setActiveTab] = useState("marketplace");
  const [selectedExtension, setSelectedExtension] = useState<string | null>(
    null
  );
  const [selectedExtensionName, setSelectedExtensionName] =
    useState<string>("");
  // Extension management handlers
  const handleInstallExtension = useCallback(async (extensionId: string) => {
    // Simulate installation
    console.log("Installing extension:", extensionId);
    await new Promise((resolve) => setTimeout(resolve, 2000));
  }, []);
  const handleUninstallExtension = useCallback(async (extensionId: string) => {
    // Simulate uninstallation
    console.log("Uninstalling extension:", extensionId);
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }, []);
  const handleEnableExtension = useCallback(async (extensionId: string) => {
    // Simulate enabling
    console.log("Enabling extension:", extensionId);
    await new Promise((resolve) => setTimeout(resolve, 500));
  }, []);
  const handleDisableExtension = useCallback(async (extensionId: string) => {
    // Simulate disabling
    console.log("Disabling extension:", extensionId);
    await new Promise((resolve) => setTimeout(resolve, 500));
  }, []);
  const handleConfigureExtension = useCallback((extensionId: string) => {
    setSelectedExtension(extensionId);
    setSelectedExtensionName(extensionId); // In real app, would fetch extension name
    setActiveTab("configuration");
  }, []);
  const handleViewLogs = useCallback((extensionId: string) => {
    setSelectedExtension(extensionId);
    setSelectedExtensionName(extensionId); // In real app, would fetch extension name
    setActiveTab("debugging");
  }, []);
  const handleViewMetrics = useCallback((extensionId: string) => {
    setSelectedExtension(extensionId);
    setSelectedExtensionName(extensionId); // In real app, would fetch extension name
    setActiveTab("monitoring");
  }, []);
  const handleInstallFromFile = useCallback(async (file: File) => {
    // Simulate file installation
    console.log("Installing extension from file:", file.name);
    await new Promise((resolve) => setTimeout(resolve, 3000));
  }, []);
  const handleSaveConfiguration = useCallback(
    async (settings: Record<string, unknown>) => {
      // Simulate saving configuration
      console.log("Saving configuration:", settings);
      await new Promise((resolve) => setTimeout(resolve, 1000));
    },
    []
  );
  const handleResetConfiguration = useCallback(async () => {
    // Simulate resetting configuration
    await new Promise((resolve) => setTimeout(resolve, 500));
  }, []);
  const handlePermissionChange = useCallback(
    async (permission: string, granted: boolean) => {
      // Simulate permission change
      console.log("Permission change:", permission, granted);
      await new Promise((resolve) => setTimeout(resolve, 300));
    },
    []
  );
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-4 mb-4">
            <Link href="/extensions">
              <Button
                variant="outline"
                size="sm"
                className="flex items-center gap-2"
              >
                <ArrowLeft className="h-4 w-4" />
              </Button>
            </Link>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Extension Management
              </h1>
              <p className="text-gray-600 mt-1">
                Manage, configure, and monitor your extensions
              </p>
            </div>
          </div>
        </div>
        {/* Management Interface */}
        <Tabs
          value={activeTab}
          onValueChange={setActiveTab}
          className="space-y-6"
        >
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger
              value="marketplace"
              className="flex items-center gap-2"
            >
              <Store className="h-4 w-4" />
              Marketplace
            </TabsTrigger>
            <TabsTrigger value="manager" className="flex items-center gap-2">
              <Cog className="h-4 w-4" />
              Manager
            </TabsTrigger>
            <TabsTrigger
              value="configuration"
              className="flex items-center gap-2"
            >
              <Settings className="h-4 w-4" />
              Configuration
            </TabsTrigger>
            <TabsTrigger value="debugging" className="flex items-center gap-2">
              <Bug className="h-4 w-4" />
              Debugging
            </TabsTrigger>
            <TabsTrigger value="monitoring" className="flex items-center gap-2">
              <Activity className="h-4 w-4" />
              Monitoring
            </TabsTrigger>
          </TabsList>
          <TabsContent value="marketplace" className="space-y-6">
            <ExtensionMarketplace
              onInstall={handleInstallExtension}
              onUninstall={handleUninstallExtension}
            />
          </TabsContent>
          <TabsContent value="manager" className="space-y-6">
            <ExtensionManager
              onInstallFromFile={handleInstallFromFile}
              onUninstall={handleUninstallExtension}
              onEnable={handleEnableExtension}
              onDisable={handleDisableExtension}
              onConfigure={handleConfigureExtension}
              onViewLogs={handleViewLogs}
              onViewMetrics={handleViewMetrics}
            />
          </TabsContent>
          <TabsContent value="configuration" className="space-y-6">
            {selectedExtension ? (
              <ExtensionConfigurationPanel
                extensionId={selectedExtension}
                extensionName={selectedExtensionName}
                onSave={handleSaveConfiguration}
                onReset={handleResetConfiguration}
                onPermissionChange={handlePermissionChange}
              />
            ) : (
              <div className="text-center py-12">
                <Settings className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  No Extension Selected
                </h3>
                <p className="text-gray-600 mb-4">
                  Select an extension from the manager to configure its
                  settings.
                </p>
                <Button onClick={() => setActiveTab("manager")}>
                  Go to Manager
                </Button>
              </div>
            )}
          </TabsContent>
          <TabsContent value="debugging" className="space-y-6">
            {selectedExtension ? (
              <ExtensionDebugger
                extensionId={selectedExtension}
                extensionName={selectedExtensionName}
              />
            ) : (
              <div className="text-center py-12">
                <Bug className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  No Extension Selected
                </h3>
                <p className="text-gray-600 mb-4">
                  Select an extension from the manager to view its debug
                  information and logs.
                </p>
                <Button onClick={() => setActiveTab("manager")}>
                  Go to Manager
                </Button>
              </div>
            )}
          </TabsContent>
          <TabsContent value="monitoring" className="space-y-6">
            <ExtensionPerformanceMonitor
              extensionId={selectedExtension || undefined}
            />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
