"use client";
import React, { useState, useCallback, useMemo } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../ui/tabs";
import { Badge } from "../../ui/badge";
import { Button } from "../../ui/button";
import { Checkbox } from "../../ui/checkbox";

/**
 * Extension Manager Component
 *
 * Comprehensive extension management interface for installing, configuring,
 * enabling/disabling, and monitoring installed extensions.
 */

import {
  useExtensionStatuses,
  useExtensionHealth,
  useExtensionPerformance,
} from "../../../lib/extensions/hooks";

import {
  Package,
  Settings,
  Play,
  Pause,
  Trash2,
  Upload,
  BarChart3,
  FileText,
  RefreshCw,
  AlertTriangle,
  Power,
  PowerOff,
  Activity,
  CheckCircle,
  Zap,
  Clock,
  Info,
  Database,
  Globe,
  Shield,
} from "lucide-react";
export interface ExtensionManagerProps {
  className?: string;
  onInstallFromFile?: (file: File) => Promise<void>;
  onUninstall?: (extensionId: string) => Promise<void>;
  onEnable?: (extensionId: string) => Promise<void>;
  onDisable?: (extensionId: string) => Promise<void>;
  onConfigure?: (extensionId: string) => void;
  onViewLogs?: (extensionId: string) => void;
  onViewMetrics?: (extensionId: string) => void;
}
export function ExtensionManager({
  className,
  onInstallFromFile,
  onUninstall,
  onEnable,
  onDisable,
  onConfigure,
  onViewLogs,
  onViewMetrics,
}: ExtensionManagerProps) {
  const [activeTab, setActiveTab] = useState("installed");
  const [selectedExtensions, setSelectedExtensions] = useState<Set<string>>(
    new Set()
  );
  const [actionInProgress, setActionInProgress] = useState<Set<string>>(
    new Set()
  );
  const [showBulkActions, setShowBulkActions] = useState(false);
  const { statuses, loading, error } = useExtensionStatuses();
  const healthData = useExtensionHealth();
  const performanceData = useExtensionPerformance();
  const extensionsByStatus = useMemo(() => {
    return {
      active: statuses.filter((s) => s.status === "active"),
      inactive: statuses.filter((s) => s.status === "inactive"),
      error: statuses.filter((s) => s.status === "error"),
      all: statuses,
    };
  }, [statuses]);
  const handleAction = useCallback(
    async (
      extensionId: string,
      action: "enable" | "disable" | "uninstall",
      callback?: (id: string) => Promise<void>
    ) => {
      if (actionInProgress.has(extensionId)) return;
      setActionInProgress((prev) => new Set(prev).add(extensionId));
      try {
        if (callback) {
          await callback(extensionId);
        }
        // Simulate action delay
        await new Promise((resolve) => setTimeout(resolve, 1000));
      } catch (error) {
        console.error("Action failed:", error);
      } finally {
        setActionInProgress((prev) => {
          const newSet = new Set(prev);
          newSet.delete(extensionId);
          return newSet;
        });
      }
    },
    [actionInProgress]
  );
  const handleBulkAction = useCallback(
    async (action: "enable" | "disable" | "uninstall") => {
      const promises = Array.from(selectedExtensions).map((id) => {
        switch (action) {
          case "enable":
            return handleAction(id, "enable", onEnable);
          case "disable":
            return handleAction(id, "disable", onDisable);
          case "uninstall":
            return handleAction(id, "uninstall", onUninstall);
          default:
            return Promise.resolve();
        }
      });

      await Promise.all(promises);
      setSelectedExtensions(new Set());
      setShowBulkActions(false);
    },
    [selectedExtensions, handleAction, onEnable, onDisable, onUninstall]
  );
  const handleFileUpload = useCallback(
    async (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (file && onInstallFromFile) {
        try {
          await onInstallFromFile(file);
        } catch (error) {
          console.error("File upload failed:", error);
        }
      }
      // Reset file input
      event.target.value = "";
    },
    [onInstallFromFile]
  );
  const toggleExtensionSelection = useCallback((extensionId: string) => {
    setSelectedExtensions((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(extensionId)) {
        newSet.delete(extensionId);
      } else {
        newSet.add(extensionId);
      }
      return newSet;
    });
  }, []);
  if (loading) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4 " />
          <p className="text-gray-600">Loading extension manager...</p>
        </div>
      </div>
    );
  }
  if (error) {
    return (
      <div
        className={`bg-red-50 border border-red-200 rounded-lg p-6 ${className}`}
      >
        <div className="flex items-center">
          <AlertTriangle className="h-5 w-5 text-red-500 mr-3 " />
          <div>
            <h3 className="text-lg font-semibold text-red-800">
              Manager Error
            </h3>
            <p className="text-red-700">{error}</p>
          </div>
        </div>
      </div>
    );
  }
  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            Extension Manager
          </h1>
          <p className="text-gray-600 mt-1">
            Manage your installed extensions and their configurations
          </p>
        </div>
        <div className="flex gap-2">
          {selectedExtensions.size > 0 && (
            <Button
              variant="outline"
              onClick={() => setShowBulkActions(!showBulkActions)}
              className="flex items-center gap-2"
            >
              <Settings className="h-4 w-4 " />
              Bulk Actions ({selectedExtensions.size})
            </Button>
          )}
          <div className="relative">
            <input
              type="file"
              accept=".zip,.tar.gz,.kari-ext"
              onChange={handleFileUpload}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              id="extension-upload"
            />
            <Button variant="outline" className="flex items-center gap-2">
              <Upload className="h-4 w-4 " />
            </Button>
          </div>
        </div>
      </div>
      {/* Bulk Actions Panel */}
      {showBulkActions && selectedExtensions.size > 0 && (
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-blue-900">
                  {selectedExtensions.size} extension
                  {selectedExtensions.size !== 1 ? "s" : ""} selected
                </h3>
                <p className="text-sm text-blue-700 md:text-base lg:text-lg">
                  Choose an action to apply to all selected extensions
                </p>
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleBulkAction("enable")}
                  className="flex items-center gap-1"
                >
                  <Power className="h-3 w-3 " />
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleBulkAction("disable")}
                  className="flex items-center gap-1"
                >
                  <PowerOff className="h-3 w-3 " />
                </Button>
                <Button
                  size="sm"
                  variant="destructive"
                  onClick={() => handleBulkAction("uninstall")}
                  className="flex items-center gap-1"
                >
                  <Trash2 className="h-3 w-3 " />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium md:text-base lg:text-lg">
              Total Extensions
            </CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground " />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {extensionsByStatus.all.length}
            </div>
            <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
              {extensionsByStatus.active.length} active
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium md:text-base lg:text-lg">
              Health Score
            </CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground " />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {healthData.healthPercentage}%
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
              <div
                className={`h-2 rounded-full ${
                  healthData.healthPercentage >= 80
                    ? "bg-green-500"
                    : healthData.healthPercentage >= 60
                    ? "bg-yellow-500"
                    : "bg-red-500"
                }`}
                style={{ width: `${healthData.healthPercentage}%` }}
              />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium md:text-base lg:text-lg">
              Resource Usage
            </CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground " />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {performanceData.avgCpu.toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
              {Math.round(performanceData.totalMemory)}MB memory
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium md:text-base lg:text-lg">
              Issues
            </CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground " />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {extensionsByStatus.error.length}
            </div>
            <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
              {extensionsByStatus.inactive.length} inactive
            </p>
          </CardContent>
        </Card>
      </div>
      {/* Extension Management Tabs */}
      <Tabs
        value={activeTab}
        onValueChange={setActiveTab}
        className="space-y-4"
      >
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="installed">
            All Extensions ({extensionsByStatus.all.length})
          </TabsTrigger>
          <TabsTrigger value="active">
            Active ({extensionsByStatus.active.length})
          </TabsTrigger>
          <TabsTrigger value="inactive">
            Inactive ({extensionsByStatus.inactive.length})
          </TabsTrigger>
          <TabsTrigger value="errors">
            Issues ({extensionsByStatus.error.length})
          </TabsTrigger>
        </TabsList>
        <TabsContent value="installed" className="space-y-4">
          <ExtensionList
            extensions={extensionsByStatus.all}
            selectedExtensions={selectedExtensions}
            actionInProgress={actionInProgress}
            onToggleSelection={toggleExtensionSelection}
            onAction={handleAction}
            onEnable={onEnable}
            onDisable={onDisable}
            onUninstall={onUninstall}
            onConfigure={onConfigure}
            onViewLogs={onViewLogs}
            onViewMetrics={onViewMetrics}
          />
        </TabsContent>
        <TabsContent value="active" className="space-y-4">
          <ExtensionList
            extensions={extensionsByStatus.active}
            selectedExtensions={selectedExtensions}
            actionInProgress={actionInProgress}
            onToggleSelection={toggleExtensionSelection}
            onAction={handleAction}
            onEnable={onEnable}
            onDisable={onDisable}
            onUninstall={onUninstall}
            onConfigure={onConfigure}
            onViewLogs={onViewLogs}
            onViewMetrics={onViewMetrics}
          />
        </TabsContent>
        <TabsContent value="inactive" className="space-y-4">
          <ExtensionList
            extensions={extensionsByStatus.inactive}
            selectedExtensions={selectedExtensions}
            actionInProgress={actionInProgress}
            onToggleSelection={toggleExtensionSelection}
            onAction={handleAction}
            onEnable={onEnable}
            onDisable={onDisable}
            onUninstall={onUninstall}
            onConfigure={onConfigure}
            onViewLogs={onViewLogs}
            onViewMetrics={onViewMetrics}
          />
        </TabsContent>
        <TabsContent value="errors" className="space-y-4">
          <ExtensionList
            extensions={extensionsByStatus.error}
            selectedExtensions={selectedExtensions}
            actionInProgress={actionInProgress}
            onToggleSelection={toggleExtensionSelection}
            onAction={handleAction}
            onEnable={onEnable}
            onDisable={onDisable}
            onUninstall={onUninstall}
            onConfigure={onConfigure}
            onViewLogs={onViewLogs}
            onViewMetrics={onViewMetrics}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}
export interface ExtensionListProps {
  extensions: any[];
  selectedExtensions: Set<string>;
  actionInProgress: Set<string>;
  onToggleSelection: (id: string) => void;
  onAction: (
    id: string,
    action: "enable" | "disable" | "uninstall",
    callback?: any
  ) => Promise<void>;
  onEnable?: (id: string) => Promise<void>;
  onDisable?: (id: string) => Promise<void>;
  onUninstall?: (id: string) => Promise<void>;
  onConfigure?: (id: string) => void;
  onViewLogs?: (id: string) => void;
  onViewMetrics?: (id: string) => void;
}

function ExtensionList({
  extensions,
  selectedExtensions,
  actionInProgress,
  onToggleSelection,
  onAction,
  onEnable,
  onDisable,
  onUninstall,
  onConfigure,
  onViewLogs,
  onViewMetrics,
}: ExtensionListProps) {
  if (extensions.length === 0) {
    return (
      <div className="text-center py-12">
        <Activity className="mx-auto h-12 w-12 text-gray-400 mb-4 " />
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          No extensions found
        </h3>
        <p className="text-gray-600">No extensions match the current filter</p>
      </div>
    );
  }
  return (
    <div className="space-y-4">
      {extensions.map((extension) => (
        <ExtensionCard
          key={extension.id}
          extension={extension}
          selected={selectedExtensions.has(extension.id)}
          actionInProgress={actionInProgress.has(extension.id)}
          onToggleSelection={() => onToggleSelection(extension.id)}
          onEnable={() => onAction(extension.id, "enable", onEnable)}
          onDisable={() => onAction(extension.id, "disable", onDisable)}
          onUninstall={() => onAction(extension.id, "uninstall", onUninstall)}
          onConfigure={() => onConfigure?.(extension.id)}
          onViewLogs={() => onViewLogs?.(extension.id)}
          onViewMetrics={() => onViewMetrics?.(extension.id)}
        />
      ))}
    </div>
  );
}
export interface ExtensionCardProps {
  extension: any;
  selected: boolean;
  actionInProgress: boolean;
  onToggleSelection: () => void;
  onEnable: () => void;
  onDisable: () => void;
  onUninstall: () => void;
  onConfigure: () => void;
  onViewLogs: () => void;
  onViewMetrics: () => void;
}

function ExtensionCard({
  extension,
  selected,
  actionInProgress,
  onToggleSelection,
  onEnable,
  onDisable,
  onUninstall,
  onConfigure,
  onViewLogs,
  onViewMetrics,
}: ExtensionCardProps) {
  const [showDetails, setShowDetails] = useState(false);
  const getStatusIcon = (status: string) => {
    switch (status) {
      case "active":
        return <CheckCircle className="h-5 w-5 text-green-500 " />;
      case "error":
        return <AlertTriangle className="h-5 w-5 text-red-500 " />;
      case "inactive":
        return <Clock className="h-5 w-5 text-gray-400 " />;
      default:
        return <Activity className="h-5 w-5 text-gray-400 " />;
    }
  };
  const getStatusColor = (status: string) => {
    switch (status) {
      case "active":
        return "bg-green-100 text-green-800";
      case "error":
        return "bg-red-100 text-red-800";
      case "inactive":
        return "bg-gray-100 text-gray-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };
  return (
    <Card
      className={`transition-all ${
        selected ? "ring-2 ring-blue-500 bg-blue-50" : ""
      }`}
    >
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Checkbox
              checked={selected}
              onCheckedChange={onToggleSelection}
            />
            <div className="flex items-center space-x-3">
              {getStatusIcon(extension.status)}
              <div>
                <CardTitle className="text-lg">{extension.name}</CardTitle>
                <div className="flex items-center gap-2 mt-1">
                  <Badge className={getStatusColor(extension.status)}>
                    {extension.status}
                  </Badge>
                  <span className="text-sm text-gray-500 md:text-base lg:text-lg">
                    ID: {extension.id}
                  </span>
                </div>
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {/* Quick Actions */}
            <Button
              size="sm"
              variant="outline"
              onClick={onConfigure}
              className="flex items-center gap-1"
            >
              <Settings className="h-3 w-3 " />
            </Button>
            {extension.status === "active" ? (
              <Button
                size="sm"
                variant="outline"
                onClick={onDisable}
                disabled={actionInProgress}
                className="flex items-center gap-1"
              >
                <PowerOff className="h-3 w-3 " />
              </Button>
            ) : (
              <Button
                size="sm"
                variant="outline"
                onClick={onEnable}
                disabled={actionInProgress}
                className="flex items-center gap-1"
              >
                <Power className="h-3 w-3 " />
              </Button>
            )}
            <Button
              size="sm"
              variant="outline"
              onClick={() => setShowDetails(!showDetails)}
            >
              <Info className="h-4 w-4 " />
            </Button>
          </div>
        </div>
      </CardHeader>
      {showDetails && (
        <CardContent className="pt-0">
          <div className="space-y-4">
            {/* Resource Usage */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-gray-50 rounded-lg p-3 sm:p-4 md:p-6">
                <div className="flex items-center gap-2 mb-1">
                  <Zap className="h-4 w-4 text-gray-500 " />
                  <span className="text-sm font-medium text-gray-700 md:text-base lg:text-lg">
                    CPU
                  </span>
                </div>
                <p className="text-lg font-semibold">
                  {extension.resources.cpu.toFixed(1)}%
                </p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3 sm:p-4 md:p-6">
                <div className="flex items-center gap-2 mb-1">
                  <Database className="h-4 w-4 text-gray-500 " />
                  <span className="text-sm font-medium text-gray-700 md:text-base lg:text-lg">
                    Memory
                  </span>
                </div>
                <p className="text-lg font-semibold">
                  {Math.round(extension.resources.memory)}MB
                </p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3 sm:p-4 md:p-6">
                <div className="flex items-center gap-2 mb-1">
                  <Globe className="h-4 w-4 text-gray-500 " />
                  <span className="text-sm font-medium text-gray-700 md:text-base lg:text-lg">
                    Network
                  </span>
                </div>
                <p className="text-lg font-semibold">
                  {extension.resources.network.toFixed(1)} KB/s
                </p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3 sm:p-4 md:p-6">
                <div className="flex items-center gap-2 mb-1">
                  <Shield className="h-4 w-4 text-gray-500 " />
                  <span className="text-sm font-medium text-gray-700 md:text-base lg:text-lg">
                    Storage
                  </span>
                </div>
                <p className="text-lg font-semibold">
                  {Math.round(extension.resources.storage)}MB
                </p>
              </div>
            </div>
            {/* Background Tasks */}
            {extension.backgroundTasks && (
              <div className="bg-gray-50 rounded-lg p-4 sm:p-4 md:p-6">
                <h4 className="font-medium text-gray-900 mb-2">
                  Background Tasks
                </h4>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 md:text-base lg:text-lg">
                      {extension.backgroundTasks.active} active /{" "}
                      {extension.backgroundTasks.total} total
                    </p>
                    {extension.backgroundTasks.lastExecution && (
                      <p className="text-xs text-gray-500 sm:text-sm md:text-base">
                        Last execution:{" "}
                        {new Date(
                          extension.backgroundTasks.lastExecution
                        ).toLocaleString()}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            )}
            {/* Health Status */}
            <div className="bg-gray-50 rounded-lg p-4 sm:p-4 md:p-6">
              <h4 className="font-medium text-gray-900 mb-2">Health Status</h4>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 md:text-base lg:text-lg">
                    {extension.health.message}
                  </p>
                  <p className="text-xs text-gray-500 sm:text-sm md:text-base">
                    Last check:{" "}
                    {new Date(extension.health.lastCheck).toLocaleString()}
                  </p>
                </div>
                <Badge className={getStatusColor(extension.health.status)}>
                  {extension.health.status}
                </Badge>
              </div>
            </div>
            {/* Action Buttons */}
            <div className="flex gap-2 pt-2 border-t border-gray-200">
              <Button
                size="sm"
                variant="outline"
                onClick={onViewLogs}
                className="flex items-center gap-1"
              >
                <FileText className="h-3 w-3 " />
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={onViewMetrics}
                className="flex items-center gap-1"
              >
                <BarChart3 className="h-3 w-3 " />
              </Button>
              <Button
                size="sm"
                variant="destructive"
                onClick={onUninstall}
                disabled={actionInProgress}
                className="flex items-center gap-1 ml-auto"
              >
                <Trash2 className="h-3 w-3 " />
              </Button>
            </div>
          </div>
        </CardContent>
      )}
    </Card>
  );
}
