/**
 * Plugin Detail View Component
 * 
 * Detailed view for individual plugins showing configuration, logs, dependencies, and performance data.
 * Based on requirements: 5.1, 5.4
 */

"use client";

import React, { useState, useEffect } from 'react';
import { 
  ArrowLeft, 
  Settings, 
  Power, 
  PowerOff, 
  Trash2, 
  Download,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  RefreshCw,
  ExternalLink,
  Shield,
  Activity,
  FileText,
  Package,
  BarChart3,
  Calendar,
  User,
  Globe,
  HardDrive,
  Cpu,
  Zap,
  Network,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';

import { PluginInfo } from '@/types/plugins';
import { usePluginStore, selectPluginLoading, selectPluginError } from '@/store/plugin-store';

interface PluginDetailViewProps {
  plugin: PluginInfo;
  onClose: () => void;
  onEnable: (id: string) => void;
  onDisable: (id: string) => void;
  onUninstall: (id: string) => void;
  onConfigure: (plugin: PluginInfo) => void;
}

const statusConfig = {
  active: { 
    label: 'Active', 
    variant: 'default' as const, 
    icon: CheckCircle, 
    color: 'text-green-600' 
  },
  inactive: { 
    label: 'Inactive', 
    variant: 'secondary' as const, 
    icon: Clock, 
    color: 'text-gray-500' 
  },
  error: { 
    label: 'Error', 
    variant: 'destructive' as const, 
    icon: XCircle, 
    color: 'text-red-600' 
  },
  installing: { 
    label: 'Installing', 
    variant: 'outline' as const, 
    icon: Download, 
    color: 'text-blue-600' 
  },
  updating: { 
    label: 'Updating', 
    variant: 'outline' as const, 
    icon: RefreshCw, 
    color: 'text-blue-600' 
  },
  uninstalling: { 
    label: 'Uninstalling', 
    variant: 'outline' as const, 
    icon: Trash2, 
    color: 'text-orange-600' 
  },
};

const MetricCard: React.FC<{
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ComponentType<{ className?: string }>;
  trend?: 'up' | 'down' | 'stable';
}> = ({ title, value, subtitle, icon: Icon, trend }) => (
  <Card>
    <CardContent className="p-4 sm:p-4 md:p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-muted-foreground md:text-base lg:text-lg">{title}</p>
          <p className="text-2xl font-bold">{value}</p>
          {subtitle && <p className="text-xs text-muted-foreground sm:text-sm md:text-base">{subtitle}</p>}
        </div>
        <Icon className="w-8 h-8 text-muted-foreground sm:w-auto md:w-full" />
      </div>
    </CardContent>
  </Card>
);

const PermissionBadge: React.FC<{ permission: any }> = ({ permission }) => {
  const levelColors = {
    read: 'bg-blue-100 text-blue-800',
    write: 'bg-yellow-100 text-yellow-800',
    admin: 'bg-red-100 text-red-800',
  };

  return (
    <div className="flex items-center gap-2 p-2 border rounded-lg sm:p-4 md:p-6">
      <Shield className="w-4 h-4 text-muted-foreground sm:w-auto md:w-full" />
      <div className="flex-1">
        <div className="font-medium text-sm md:text-base lg:text-lg">{permission.name}</div>
        <div className="text-xs text-muted-foreground sm:text-sm md:text-base">{permission.description}</div>
      </div>
      <Badge className={`text-xs ${levelColors[permission.level as keyof typeof levelColors]}`}>
        {permission.level}
      </Badge>
    </div>
  );
};

const LogEntry: React.FC<{ entry: any }> = ({ entry }) => {
  const levelColors = {
    debug: 'text-gray-500',
    info: 'text-blue-600',
    warn: 'text-yellow-600',
    error: 'text-red-600',
  };

  return (
    <div className="flex gap-3 p-3 border-b last:border-b-0 sm:p-4 md:p-6">
      <div className="text-xs text-muted-foreground w-20 flex-shrink-0 sm:w-auto md:w-full">
        {entry.timestamp.toLocaleTimeString()}
      </div>
      <div className={`text-xs font-medium w-12 flex-shrink-0 uppercase ${levelColors[entry.level as keyof typeof levelColors] || 'text-gray-500'}`}>
        {entry.level}
      </div>
      <div className="flex-1 text-sm md:text-base lg:text-lg">{entry.message}</div>
    </div>
  );
};

export const PluginDetailView: React.FC<PluginDetailViewProps> = ({
  plugin,
  onClose,
  onEnable,
  onDisable,
  onUninstall,
  onConfigure,
}) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [mockLogs] = useState([
    {
      id: '1',
      timestamp: new Date(Date.now() - 300000),
      level: 'info',
      message: 'Plugin initialized successfully',
    },
    {
      id: '2',
      timestamp: new Date(Date.now() - 600000),
      level: 'debug',
      message: 'Loading configuration from manifest',
    },
    {
      id: '3',
      timestamp: new Date(Date.now() - 900000),
      level: 'warn',
      message: 'API rate limit approaching (80% of quota used)',
    },
    {
      id: '4',
      timestamp: new Date(Date.now() - 1200000),
      level: 'error',
      message: 'Authentication failed: Token expired',
    },
  ]);

  const enableLoading = usePluginStore(selectPluginLoading(`enable-${plugin.id}`));
  const disableLoading = usePluginStore(selectPluginLoading(`disable-${plugin.id}`));
  const uninstallLoading = usePluginStore(selectPluginLoading(`uninstall-${plugin.id}`));
  const configureLoading = usePluginStore(selectPluginLoading(`configure-${plugin.id}`));

  const statusInfo = statusConfig[plugin.status];
  const StatusIcon = statusInfo.icon;

  const handleToggleEnabled = () => {
    if (plugin.enabled) {
      onDisable(plugin.id);
    } else {
      onEnable(plugin.id);
    }
  };

  const isActionDisabled = plugin.status === 'installing' || plugin.status === 'updating' || plugin.status === 'uninstalling';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button variant="ghost" size="sm" onClick={onClose} aria-label="Button">
            <ArrowLeft className="w-4 h-4 mr-2 sm:w-auto md:w-full" />
            Back to Plugins
          </Button>
          <Separator orientation="vertical" className="h-6" />
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
          <button 
            variant="outline" 
            onClick={() = aria-label="Button"> onConfigure(plugin)}
            disabled={isActionDisabled || configureLoading}
          >
            <Settings className="w-4 h-4 mr-2 sm:w-auto md:w-full" />
            Configure
          </Button>
          <button 
            variant={plugin.enabled ? "outline" : "default"}
            onClick={handleToggleEnabled}
            disabled={isActionDisabled || enableLoading || disableLoading}
           aria-label="Button">
            {enableLoading || disableLoading ? (
              <RefreshCw className="w-4 h-4 mr-2 animate-spin sm:w-auto md:w-full" />
            ) : plugin.enabled ? (
              <PowerOff className="w-4 h-4 mr-2 sm:w-auto md:w-full" />
            ) : (
              <Power className="w-4 h-4 mr-2 sm:w-auto md:w-full" />
            )}
            {plugin.enabled ? 'Disable' : 'Enable'}
          </Button>
          <button 
            variant="destructive" 
            onClick={() = aria-label="Button"> onUninstall(plugin.id)}
            disabled={isActionDisabled || uninstallLoading}
          >
            {uninstallLoading ? (
              <RefreshCw className="w-4 h-4 mr-2 animate-spin sm:w-auto md:w-full" />
            ) : (
              <Trash2 className="w-4 h-4 mr-2 sm:w-auto md:w-full" />
            )}
            Uninstall
          </Button>
        </div>
      </div>

      {/* Error Display */}
      {plugin.lastError && (
        <Alert variant="destructive">
          <XCircle className="w-4 h-4 sm:w-auto md:w-full" />
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
        <Alert variant="destructive">
          <AlertTriangle className="w-4 h-4 sm:w-auto md:w-full" />
          <AlertDescription>
            <div className="font-medium">Health Issues:</div>
            <ul className="list-disc list-inside mt-1">
              {plugin.metrics.health.issues.map((issue, index) => (
                <li key={index} className="text-sm md:text-base lg:text-lg">{issue}</li>
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

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2">
            {/* Plugin Information */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Package className="w-5 h-5 sm:w-auto md:w-full" />
                  Plugin Information
                </CardTitle>
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
                    <button variant="outline" size="sm" asChild aria-label="Button">
                      <a href={plugin.manifest.homepage} target="_blank" rel="noopener noreferrer">
                        <ExternalLink className="w-4 h-4 mr-2 sm:w-auto md:w-full" />
                        Visit Homepage
                      </a>
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Runtime Information */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="w-5 h-5 sm:w-auto md:w-full" />
                  Runtime Status
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm md:text-base lg:text-lg">
                  <div>
                    <div className="text-muted-foreground">Auto Start</div>
                    <div className="font-medium">{plugin.autoStart ? 'Yes' : 'No'}</div>
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
                  <div className="text-sm text-muted-foreground mb-2 md:text-base lg:text-lg">Health Status</div>
                  <div className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full ${
                      plugin.metrics.health.status === 'healthy' ? 'bg-green-500' :
                      plugin.metrics.health.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
                    }`} />
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

        {/* Performance Tab */}
        <TabsContent value="performance" className="space-y-6">
          {/* Performance Metrics */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <MetricCard
              title="Total Executions"
              value={plugin.metrics.performance.totalExecutions.toLocaleString()}
              icon={BarChart3}
            />
            <MetricCard
              title="Average Time"
              value={`${plugin.metrics.performance.averageExecutionTime}ms`}
              icon={Clock}
            />
            <MetricCard
              title="Error Rate"
              value={`${(plugin.metrics.performance.errorRate * 100).toFixed(1)}%`}
              icon={AlertTriangle}
            />
            <MetricCard
              title="Last Execution"
              value={plugin.metrics.performance.lastExecution ? 
                plugin.metrics.performance.lastExecution.toLocaleTimeString() : 'Never'
              }
              icon={Calendar}
            />
          </div>

          {/* Resource Usage */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="w-5 h-5 sm:w-auto md:w-full" />
                Resource Usage
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid gap-6 md:grid-cols-2">
                <div className="space-y-4">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Cpu className="w-4 h-4 sm:w-auto md:w-full" />
                        <span className="text-sm font-medium md:text-base lg:text-lg">CPU Usage</span>
                      </div>
                      <span className="text-sm text-muted-foreground md:text-base lg:text-lg">
                        {plugin.metrics.resources.cpuUsage.toFixed(1)}%
                      </span>
                    </div>
                    <Progress value={plugin.metrics.resources.cpuUsage} className="h-2" />
                  </div>
                  
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Zap className="w-4 h-4 sm:w-auto md:w-full" />
                        <span className="text-sm font-medium md:text-base lg:text-lg">Memory Usage</span>
                      </div>
                      <span className="text-sm text-muted-foreground md:text-base lg:text-lg">
                        {plugin.metrics.resources.memoryUsage.toFixed(1)} MB
                      </span>
                    </div>
                    <Progress value={plugin.metrics.resources.memoryUsage} max={100} className="h-2" />
                  </div>
                </div>
                
                <div className="space-y-4">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <HardDrive className="w-4 h-4 sm:w-auto md:w-full" />
                        <span className="text-sm font-medium md:text-base lg:text-lg">Disk Usage</span>
                      </div>
                      <span className="text-sm text-muted-foreground md:text-base lg:text-lg">
                        {plugin.metrics.resources.diskUsage.toFixed(1)} MB
                      </span>
                    </div>
                    <Progress value={plugin.metrics.resources.diskUsage} max={100} className="h-2" />
                  </div>
                  
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Network className="w-4 h-4 sm:w-auto md:w-full" />
                        <span className="text-sm font-medium md:text-base lg:text-lg">Network Usage</span>
                      </div>
                      <span className="text-sm text-muted-foreground md:text-base lg:text-lg">
                        {plugin.metrics.resources.networkUsage.toFixed(1)} KB/s
                      </span>
                    </div>
                    <Progress value={plugin.metrics.resources.networkUsage} max={10} className="h-2" />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Permissions Tab */}
        <TabsContent value="permissions" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5 sm:w-auto md:w-full" />
                Plugin Permissions
              </CardTitle>
              <CardDescription>
                Permissions granted to this plugin for system access
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {plugin.permissions.map((permission) => (
                  <PermissionBadge key={permission.id} permission={permission} />
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Security Policy */}
          <Card>
            <CardHeader>
              <CardTitle>Security Policy</CardTitle>
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
                    <Badge variant={plugin.manifest.securityPolicy.allowNetworkAccess ? "secondary" : "default"}>
                      {plugin.manifest.securityPolicy.allowNetworkAccess ? "Allowed" : "Denied"}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm md:text-base lg:text-lg">File System Access</span>
                    <Badge variant={plugin.manifest.securityPolicy.allowFileSystemAccess ? "secondary" : "default"}>
                      {plugin.manifest.securityPolicy.allowFileSystemAccess ? "Allowed" : "Denied"}
                    </Badge>
                  </div>
                </div>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm md:text-base lg:text-lg">System Calls</span>
                    <Badge variant={plugin.manifest.securityPolicy.allowSystemCalls ? "secondary" : "default"}>
                      {plugin.manifest.securityPolicy.allowSystemCalls ? "Allowed" : "Denied"}
                    </Badge>
                  </div>
                  {plugin.manifest.securityPolicy.trustedDomains && (
                    <div>
                      <div className="text-sm text-muted-foreground mb-2 md:text-base lg:text-lg">Trusted Domains</div>
                      <div className="space-y-1">
                        {plugin.manifest.securityPolicy.trustedDomains.map((domain) => (
                          <Badge key={domain} variant="outline" className="text-xs sm:text-sm md:text-base">
                            {domain}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Dependencies Tab */}
        <TabsContent value="dependencies" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Package className="w-5 h-5 sm:w-auto md:w-full" />
                Dependencies
              </CardTitle>
              <CardDescription>
                External dependencies required by this plugin
              </CardDescription>
            </CardHeader>
            <CardContent>
              {plugin.manifest.dependencies.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Package className="w-12 h-12 mx-auto mb-4 opacity-50 sm:w-auto md:w-full" />
                  <p>This plugin has no external dependencies</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {plugin.manifest.dependencies.map((dep) => (
                    <div key={dep.id} className="flex items-center justify-between p-3 border rounded-lg sm:p-4 md:p-6">
                      <div>
                        <div className="font-medium">{dep.name}</div>
                        <div className="text-sm text-muted-foreground md:text-base lg:text-lg">
                          Version: {dep.version} ({dep.versionConstraint})
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {dep.optional && (
                          <Badge variant="outline" className="text-xs sm:text-sm md:text-base">Optional</Badge>
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

        {/* Logs Tab */}
        <TabsContent value="logs" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="w-5 h-5 sm:w-auto md:w-full" />
                Plugin Logs
              </CardTitle>
              <CardDescription>
                Recent activity and error logs from this plugin
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0 sm:p-4 md:p-6">
              <ScrollArea className="h-96">
                {mockLogs.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <FileText className="w-12 h-12 mx-auto mb-4 opacity-50 sm:w-auto md:w-full" />
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