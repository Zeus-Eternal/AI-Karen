/**
 * Plugin Detail View Component
 *
 * Detailed view for individual plugins showing configuration, logs, dependencies, and performance data.
 * Based on requirements: 5.1, 5.4
 */

"use client";

import React, { useMemo, useRef, useState } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  BarChart3,
  Calendar,
  CheckCircle,
  Clock,
  Cpu,
  Download,
  ExternalLink,
  FileText,
  HardDrive,
  Network,
  Package,
  Power,
  PowerOff,
  RefreshCw,
  Settings,
  Shield,
  Trash2,
  XCircle,
  Zap,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { alertClassName } from "./utils/alertVariants";
import { VerticalSeparator } from "./utils/vertical-separator";

import type { PluginInfo } from "@/types/plugins";
import { usePluginStore, selectPluginLoading } from "@/store/plugin-store";

// --- Status Config -----------------------------------------------------------

const statusConfig = {
  active: {
    label: "Active",
    variant: "default" as const,
    icon: CheckCircle,
    color: "text-green-600",
  },
  inactive: {
    label: "Inactive",
    variant: "secondary" as const,
    icon: Clock,
    color: "text-gray-500",
  },
  error: {
    label: "Error",
    variant: "destructive" as const,
    icon: XCircle,
    color: "text-red-600",
  },
  installing: {
    label: "Installing",
    variant: "outline" as const,
    icon: Download,
    color: "text-blue-600",
  },
  updating: {
    label: "Updating",
    variant: "outline" as const,
    icon: RefreshCw,
    color: "text-blue-600",
  },
  uninstalling: {
    label: "Uninstalling",
    variant: "outline" as const,
    icon: Trash2,
    color: "text-orange-600",
  },
} as const;

// --- Small Components --------------------------------------------------------

const MetricCard: React.FC<{
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ComponentType<{ className?: string }>;
}> = ({ title, value, subtitle, icon: Icon }) => (
  <Card>
    <CardContent className="p-4 sm:p-4 md:p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-muted-foreground md:text-base lg:text-lg">{title}</p>
          <p className="text-2xl font-bold">{value}</p>
          {subtitle && (
            <p className="text-xs text-muted-foreground sm:text-sm md:text-base">{subtitle}</p>
          )}
        </div>
        <Icon className="w-8 h-8 text-muted-foreground" />
      </div>
    </CardContent>
  </Card>
);

export type Permission = {
  id: string;
  name: string;
  description: string;
  level: "read" | "write" | "admin";
  category?: string;
  required?: boolean;
};

const PermissionBadge: React.FC<{ permission: Permission }> = ({ permission }) => {
  const levelColors: Record<Permission["level"], string> = {
    read: "bg-blue-100 text-blue-800",
    write: "bg-yellow-100 text-yellow-800",
    admin: "bg-red-100 text-red-800",
  };
  return (
    <div className="flex items-center gap-2 p-2 border rounded-lg sm:p-4 md:p-6">
      <Shield className="w-4 h-4 text-muted-foreground" />
      <div className="flex-1">
        <div className="font-medium text-sm md:text-base lg:text-lg">{permission.name}</div>
        <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
          {permission.description}
        </div>
      </div>
      <Badge className={`text-xs ${levelColors[permission.level]}`}>{permission.level}</Badge>
    </div>
  );
};

export type LogEntryT = {
  id: string;
  timestamp: Date;
  level: "debug" | "info" | "warn" | "error";
  message: string;
};

const LogEntry: React.FC<{ entry: LogEntryT }> = ({ entry }) => {
  const levelColors = {
    debug: "text-gray-500",
    info: "text-blue-600",
    warn: "text-yellow-600",
    error: "text-red-600",
  } as const;

  return (
    <div className="flex gap-3 p-3 border-b last:border-b-0 sm:p-4 md:p-6">
      <div className="text-xs text-muted-foreground w-24 flex-shrink-0">
        {entry.timestamp.toLocaleTimeString()}
      </div>
      <div
        className={`text-xs font-medium w-14 flex-shrink-0 uppercase ${
          levelColors[entry.level] || "text-gray-500"
        }`}
      >
        {entry.level}
      </div>
      <div className="flex-1 text-sm md:text-base lg:text-lg">{entry.message}</div>
    </div>
  );
};

const INITIAL_MOCK_LOGS: LogEntryT[] = (() => {
  const now = Date.now();
  return [
    {
      id: "1",
      timestamp: new Date(now - 300000),
      level: "info",
      message: "Plugin initialized successfully",
    },
    {
      id: "2",
      timestamp: new Date(now - 600000),
      level: "debug",
      message: "Loading configuration from manifest",
    },
    {
      id: "3",
      timestamp: new Date(now - 900000),
      level: "warn",
      message: "API rate limit approaching (80% of quota used)",
    },
    {
      id: "4",
      timestamp: new Date(now - 1200000),
      level: "error",
      message: "Authentication failed: Token expired",
    },
  ];
})();

// --- Main Component ----------------------------------------------------------

export interface PluginDetailViewProps {
  plugin: PluginInfo;
  onClose: () => void;
  onEnable: (id: string) => void;
  onDisable: (id: string) => void;
  onUninstall: (id: string) => void;
  onConfigure: (plugin: PluginInfo) => void;
}

export const PluginDetailView: React.FC<PluginDetailViewProps> = ({
  plugin,
  onClose,
  onEnable,
  onDisable,
  onUninstall,
  onConfigure,
}) => {
  const [activeTab, setActiveTab] = useState("overview");

  // Mock logs (replace with real source/wire to store later)
  const [mockLogs] = useState<LogEntryT[]>(() => {
    const now = Date.now();
    return [
      {
        id: "1",
        timestamp: new Date(now - 300000),
        level: "info",
        message: "Plugin initialized successfully",
      },
      {
        id: "2",
        timestamp: new Date(now - 600000),
        level: "debug",
        message: "Loading configuration from manifest",
      },
      {
        id: "3",
        timestamp: new Date(now - 900000),
        level: "warn",
        message: "API rate limit approaching (80% of quota used)",
      },
      {
        id: "4",
        timestamp: new Date(now - 1200000),
        level: "error",
        message: "Authentication failed: Token expired",
      },
    ];
  });

  // Store selectors (assumes selector factory pattern per your store)
  const enableLoading = usePluginStore(selectPluginLoading(`enable-${plugin.id}`));
  const disableLoading = usePluginStore(selectPluginLoading(`disable-${plugin.id}`));
  const uninstallLoading = usePluginStore(selectPluginLoading(`uninstall-${plugin.id}`));
  const configureLoading = usePluginStore(selectPluginLoading(`configure-${plugin.id}`));
  const openExternalLink = (url: string) => {
    if (typeof window !== "undefined") {
      window.open(url, "_blank", "noopener,noreferrer");
    }
  };

  const statusInfo = statusConfig[plugin.status] ?? statusConfig.active;
  const StatusIcon = statusInfo.icon;

  const handleToggleEnabled = () => {
    if (plugin.enabled) onDisable(plugin.id);
    else onEnable(plugin.id);
  };

  const isActionDisabled =
    plugin.status === "installing" ||
    plugin.status === "updating" ||
    plugin.status === "uninstalling";

  // Normalize resource metrics into percentages for Progress components
  const cpuPct = Math.max(0, Math.min(100, plugin.metrics.resources.cpuUsage)); // already 0-100
  const memPct = useMemo(() => {
    // If you track absolute MB, compute a pseudo-percent for UI bar (UI-only).
    // Here we cap at 100 for visualization; display exact MB in label.
    return Math.max(0, Math.min(100, plugin.metrics.resources.memoryUsage));
  }, [plugin.metrics.resources.memoryUsage]);

  const diskPct = useMemo(() => {
    return Math.max(0, Math.min(100, plugin.metrics.resources.diskUsage));
  }, [plugin.metrics.resources.diskUsage]);

  const netPct = useMemo(() => {
    // If you track KB/s, you can map to a 0-100 scale; here we clamp directly.
    return Math.max(0, Math.min(100, plugin.metrics.resources.networkUsage));
  }, [plugin.metrics.resources.networkUsage]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={onClose}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            <VerticalSeparator className="h-6" />
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold">{plugin.name}</h1>
              <Badge variant={statusInfo.variant} className="text-sm md:text-base lg:text-lg">
                <StatusIcon className={`w-4 h-4 mr-1 ${statusInfo.color}`} />
                {statusInfo.label}
              </Badge>
            </div>
            <p className="text-muted-foreground">{plugin.manifest.description}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={() => onConfigure(plugin)}
            disabled={isActionDisabled || configureLoading}
          >
            {configureLoading ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                Opening…
              </>
            ) : (
              <>
                <Settings className="w-4 h-4 mr-2" />
                Configure
              </>
            )}
          </Button>

          <Button
            variant={plugin.enabled ? "outline" : "default"}
            onClick={handleToggleEnabled}
            disabled={isActionDisabled || enableLoading || disableLoading}
          >
            {enableLoading || disableLoading ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                {plugin.enabled ? "Disabling…" : "Enabling…"}
              </>
            ) : plugin.enabled ? (
              <>
                <PowerOff className="w-4 h-4 mr-2" />
                Disable
              </>
            ) : (
              <>
                <Power className="w-4 h-4 mr-2" />
                Enable
              </>
            )}
          </Button>

          <Button
            variant="destructive"
            onClick={() => onUninstall(plugin.id)}
            disabled={isActionDisabled || uninstallLoading}
          >
            {uninstallLoading ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                Uninstalling…
              </>
            ) : (
              <>
                <Trash2 className="w-4 h-4 mr-2" />
                Uninstall
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Error Display */}
      {plugin.lastError && (
        <Alert className={alertClassName("destructive")}>
          <XCircle className="w-4 h-4" />
          <AlertDescription>
            <div className="font-medium">Last Error:</div>
            <div>{plugin.lastError.message}</div>
            <div className="text-sm text-muted-foreground mt-1 md:text-base lg:text-lg">
              {plugin.lastError.timestamp.toLocaleString()}
            </div>
          </AlertDescription>
        </Alert>
      )}

      {/* Health Issues */}
      {plugin.metrics.health.issues.length > 0 && (
        <Alert className={alertClassName("destructive")}>
          <AlertTriangle className="w-4 h-4" />
          <AlertDescription>
            <div className="font-medium">Health Issues:</div>
            <ul className="list-disc list-inside mt-1">
              {plugin.metrics.health.issues.map((issue, index) => (
                <li key={index} className="text-sm md:text-base lg:text-lg">
                  {issue}
                </li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="permissions">Permissions</TabsTrigger>
          <TabsTrigger value="dependencies">Dependencies</TabsTrigger>
          <TabsTrigger value="logs">Logs</TabsTrigger>
        </TabsList>

        {/* Overview */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2">
            {/* Plugin Information */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Package className="w-5 h-5" />
                  Plugin Info
                </CardTitle>
                <CardDescription>Basic metadata for this plugin.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm md:text-base lg:text-lg">
                  <div>
                    <div className="text-muted-foreground">Version</div>
                    <div className="font-medium">{plugin.version}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Category</div>
                    <div className="font-medium capitalize">{plugin.manifest.category}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Author</div>
                    <div className="font-medium">{plugin.manifest.author.name}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">License</div>
                    <div className="font-medium">{plugin.manifest.license}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Installed</div>
                    <div className="font-medium">{plugin.installedAt.toLocaleDateString()}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Updated</div>
                    <div className="font-medium">{plugin.updatedAt.toLocaleDateString()}</div>
                  </div>
                </div>

                  {plugin.manifest.homepage && (
                    <div className="pt-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => openExternalLink(plugin.manifest.homepage ?? "")}
                      >
                        <ExternalLink className="w-4 h-4 mr-2" />
                        Homepage
                      </Button>
                    </div>
                  )}
              </CardContent>
            </Card>

            {/* Runtime Information */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="w-5 h-5" />
                  Runtime
                </CardTitle>
                <CardDescription>Operational status and health.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm md:text-base lg:text-lg">
                  <div>
                    <div className="text-muted-foreground">Auto Start</div>
                    <div className="font-medium">{plugin.autoStart ? "Yes" : "No"}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Restart Count</div>
                    <div className="font-medium">{plugin.restartCount}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Uptime</div>
                    <div className="font-medium">{plugin.metrics.health.uptime.toFixed(1)}%</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Last Check</div>
                    <div className="font-medium">
                      {plugin.metrics.health.lastHealthCheck.toLocaleTimeString()}
                    </div>
                  </div>
                </div>

                <div>
                  <div className="text-sm text-muted-foreground mb-2 md:text-base lg:text-lg">
                    Health Status
                  </div>
                  <div className="flex items-center gap-2">
                    <div
                      className={`w-3 h-3 rounded-full ${
                        plugin.metrics.health.status === "healthy"
                          ? "bg-green-500"
                          : plugin.metrics.health.status === "warning"
                          ? "bg-yellow-500"
                          : "bg-red-500"
                      }`}
                    />
                    <span className="capitalize font-medium">{plugin.metrics.health.status}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Keywords */}
          {plugin.manifest.keywords.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Keywords</CardTitle>
                <CardDescription>Tags associated with this plugin.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {plugin.manifest.keywords.map((keyword) => (
                    <Badge key={keyword} variant="secondary">
                      {keyword}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Performance */}
        <TabsContent value="performance" className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <MetricCard
              title="Total Executions"
              value={plugin.metrics.performance.totalExecutions.toLocaleString()}
              icon={BarChart3}
            />
            <MetricCard
              title="Average Time"
              value={`${plugin.metrics.performance.averageExecutionTime} ms`}
              icon={Clock}
            />
            <MetricCard
              title="Error Rate"
              value={`${(plugin.metrics.performance.errorRate * 100).toFixed(1)}%`}
              icon={AlertTriangle}
            />
            <MetricCard
              title="Last Execution"
              value={
                plugin.metrics.performance.lastExecution
                  ? plugin.metrics.performance.lastExecution.toLocaleTimeString()
                  : "Never"
              }
              icon={Calendar}
            />
          </div>

          {/* Resource Usage */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="w-5 h-5" />
                Resource Usage
              </CardTitle>
              <CardDescription>CPU, memory, disk and network activity.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid gap-6 md:grid-cols-2">
                <div className="space-y-4">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Cpu className="w-4 h-4" />
                        <span className="text-sm font-medium md:text-base lg:text-lg">CPU Usage</span>
                      </div>
                      <span className="text-sm text-muted-foreground md:text-base lg:text-lg">
                        {cpuPct.toFixed(1)}%
                      </span>
                    </div>
                    <Progress value={cpuPct} className="h-2" />
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Zap className="w-4 h-4" />
                        <span className="text-sm font-medium md:text-base lg:text-lg">Memory Usage</span>
                      </div>
                      <span className="text-sm text-muted-foreground md:text-base lg:text-lg">
                        {plugin.metrics.resources.memoryUsage.toFixed(1)} MB
                      </span>
                    </div>
                    <Progress value={memPct} className="h-2" />
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <HardDrive className="w-4 h-4" />
                        <span className="text-sm font-medium md:text-base lg:text-lg">Disk Usage</span>
                      </div>
                      <span className="text-sm text-muted-foreground md:text-base lg:text-lg">
                        {plugin.metrics.resources.diskUsage.toFixed(1)} MB
                      </span>
                    </div>
                    <Progress value={diskPct} className="h-2" />
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Network className="w-4 h-4" />
                        <span className="text-sm font-medium md:text-base lg:text-lg">Network Usage</span>
                      </div>
                      <span className="text-sm text-muted-foreground md:text-base lg:text-lg">
                        {plugin.metrics.resources.networkUsage.toFixed(1)} KB/s
                      </span>
                    </div>
                    <Progress value={netPct} className="h-2" />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Permissions */}
        <TabsContent value="permissions" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5" />
                Permissions
              </CardTitle>
              <CardDescription>Declared permission requirements.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {plugin.permissions.map((permission) => (
                  <PermissionBadge key={permission.id} permission={permission as unknown as Permission} />
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Security Policy */}
          <Card>
            <CardHeader>
              <CardTitle>Security Policy</CardTitle>
              <CardDescription>Sandboxing and access controls.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm md:text-base lg:text-lg">Sandboxed</span>
                    <Badge variant={plugin.manifest.sandboxed ? "default" : "destructive"}>
                      {plugin.manifest.sandboxed ? "Yes" : "No"}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm md:text-base lg:text-lg">Network Access</span>
                    <Badge
                      variant={
                        plugin.manifest.securityPolicy.allowNetworkAccess ? "secondary" : "default"
                      }
                    >
                      {plugin.manifest.securityPolicy.allowNetworkAccess ? "Allowed" : "Denied"}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm md:text-base lg:text-lg">File System Access</span>
                    <Badge
                      variant={
                        plugin.manifest.securityPolicy.allowFileSystemAccess ? "secondary" : "default"
                      }
                    >
                      {plugin.manifest.securityPolicy.allowFileSystemAccess ? "Allowed" : "Denied"}
                    </Badge>
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm md:text-base lg:text-lg">System Calls</span>
                    <Badge
                      variant={
                        plugin.manifest.securityPolicy.allowSystemCalls ? "secondary" : "default"
                      }
                    >
                      {plugin.manifest.securityPolicy.allowSystemCalls ? "Allowed" : "Denied"}
                    </Badge>
                  </div>

                  {plugin.manifest.securityPolicy.trustedDomains?.length ? (
                    <div>
                      <div className="text-sm text-muted-foreground mb-2 md:text-base lg:text-lg">
                        Trusted Domains
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {plugin.manifest.securityPolicy.trustedDomains.map((domain) => (
                          <Badge key={domain} variant="outline" className="text-xs sm:text-sm md:text-base">
                            {domain}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  ) : null}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Dependencies */}
        <TabsContent value="dependencies" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Package className="w-5 h-5" />
                Dependencies
              </CardTitle>
              <CardDescription>External libraries and services.</CardDescription>
            </CardHeader>
            <CardContent>
              {plugin.manifest.dependencies.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Package className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>This plugin has no external dependencies.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {plugin.manifest.dependencies.map((dep) => (
                    <div
                      key={dep.id}
                      className="flex items-center justify-between p-3 border rounded-lg sm:p-4 md:p-6"
                    >
                      <div>
                        <div className="font-medium">{dep.name}</div>
                        <div className="text-sm text-muted-foreground md:text-base lg:text-lg">
                          Version: {dep.version} ({dep.versionConstraint})
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {dep.optional && (
                          <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                            Optional
                          </Badge>
                        )}
                        <Badge variant={dep.installed ? "default" : "destructive"}>
                          {dep.installed ? "Installed" : "Missing"}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Logs */}
        <TabsContent value="logs" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="w-5 h-5" />
                Logs
              </CardTitle>
              <CardDescription>Recent runtime messages.</CardDescription>
            </CardHeader>
            <CardContent className="p-0 sm:p-4 md:p-6">
              <ScrollArea className="h-96">
                {mockLogs.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>No logs available</p>
                  </div>
                ) : (
                  <div>
                    {mockLogs.map((entry) => (
                      <LogEntry key={entry.id} entry={entry} />
                    ))}
                  </div>
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};
