/**
 * Plugin Manager Component
 * 
 * Main interface for managing plugins with status, version, and metrics display.
 * Based on requirements: 5.1, 5.4
 */

"use client";

import React, { useEffect, useState } from 'react';
import { 
  Search, 
  Filter, 
  Grid, 
  List, 
  Plus, 
  Settings, 
  Power, 
  PowerOff, 
  Trash2, 
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  Download,
  MoreVertical,
  Eye,
  RefreshCw,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuSeparator, 
  DropdownMenuTrigger 
} from '@/components/ui/dropdown-menu';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { Separator } from '@/components/ui/separator';

import { usePluginStore, selectFilteredPlugins, selectPluginLoading, selectPluginError } from '@/store/plugin-store';
import { PluginInfo, PluginStatus } from '@/types/plugins';
import { PluginDetailView } from './PluginDetailView';
import { PluginInstallationWizard } from './PluginInstallationWizard';
import { PluginMarketplace } from './PluginMarketplace';

// Status badge configuration
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

interface PluginCardProps {
  plugin: PluginInfo;
  onSelect: (plugin: PluginInfo) => void;
  onEnable: (id: string) => void;
  onDisable: (id: string) => void;
  onUninstall: (id: string) => void;
  onConfigure: (plugin: PluginInfo) => void;
  loading: boolean;
}

const PluginCard: React.FC<PluginCardProps> = ({
  plugin,
  onSelect,
  onEnable,
  onDisable,
  onUninstall,
  onConfigure,
  loading,
}) => {
  const statusInfo = statusConfig[plugin.status];
  const StatusIcon = statusInfo.icon;
  
  const handleToggleEnabled = () => {
    if (plugin.enabled) {
      onDisable(plugin.id);
    } else {
      onEnable(plugin.id);
    }
  };

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <CardTitle className="text-lg">{plugin.name}</CardTitle>
              <Badge variant={statusInfo.variant} className="text-xs">
                <StatusIcon className={`w-3 h-3 mr-1 ${statusInfo.color}`} />
                {statusInfo.label}
              </Badge>
            </div>
            <CardDescription className="text-sm">
              {plugin.manifest.description}
            </CardDescription>
            <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
              <span>v{plugin.version}</span>
              <span>by {plugin.manifest.author.name}</span>
              <span className="capitalize">{plugin.manifest.category}</span>
            </div>
          </div>
          
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" disabled={loading}>
                <MoreVertical className="w-4 h-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onSelect(plugin)}>
                <Eye className="w-4 h-4 mr-2" />
                View Details
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onConfigure(plugin)}>
                <Settings className="w-4 h-4 mr-2" />
                Configure
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem 
                onClick={handleToggleEnabled}
                disabled={plugin.status === 'installing' || plugin.status === 'updating'}
              >
                {plugin.enabled ? (
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
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem 
                onClick={() => onUninstall(plugin.id)}
                className="text-destructive"
                disabled={plugin.status === 'installing' || plugin.status === 'updating'}
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Uninstall
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>
      
      <CardContent className="pt-0">
        {/* Performance Metrics */}
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div>
            <div className="text-muted-foreground">Executions</div>
            <div className="font-medium">{plugin.metrics.performance.totalExecutions.toLocaleString()}</div>
          </div>
          <div>
            <div className="text-muted-foreground">Avg Time</div>
            <div className="font-medium">{plugin.metrics.performance.averageExecutionTime}ms</div>
          </div>
          <div>
            <div className="text-muted-foreground">Error Rate</div>
            <div className="font-medium">{(plugin.metrics.performance.errorRate * 100).toFixed(1)}%</div>
          </div>
        </div>
        
        {/* Health Status */}
        <div className="mt-4">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Health</span>
            <div className="flex items-center gap-1">
              <div className={`w-2 h-2 rounded-full ${
                plugin.metrics.health.status === 'healthy' ? 'bg-green-500' :
                plugin.metrics.health.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
              }`} />
              <span className="capitalize">{plugin.metrics.health.status}</span>
            </div>
          </div>
          
          {plugin.metrics.health.issues.length > 0 && (
            <div className="mt-2">
              <Alert variant="destructive" className="py-2">
                <AlertTriangle className="w-4 h-4" />
                <AlertDescription className="text-xs">
                  {plugin.metrics.health.issues[0]}
                  {plugin.metrics.health.issues.length > 1 && 
                    ` (+${plugin.metrics.health.issues.length - 1} more)`
                  }
                </AlertDescription>
              </Alert>
            </div>
          )}
        </div>
        
        {/* Last Error */}
        {plugin.lastError && (
          <div className="mt-3">
            <Alert variant="destructive" className="py-2">
              <XCircle className="w-4 h-4" />
              <AlertDescription className="text-xs">
                <div className="font-medium">Last Error:</div>
                <div>{plugin.lastError.message}</div>
                <div className="text-muted-foreground mt-1">
                  {plugin.lastError.timestamp.toLocaleString()}
                </div>
              </AlertDescription>
            </Alert>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

const PluginListSkeleton: React.FC = () => (
  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
    {Array.from({ length: 6 }).map((_, i) => (
      <Card key={i}>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <Skeleton className="h-6 w-32 mb-2" />
              <Skeleton className="h-4 w-full mb-2" />
              <div className="flex gap-4">
                <Skeleton className="h-3 w-16" />
                <Skeleton className="h-3 w-20" />
                <Skeleton className="h-3 w-16" />
              </div>
            </div>
            <Skeleton className="h-8 w-8" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div>
              <Skeleton className="h-3 w-16 mb-1" />
              <Skeleton className="h-4 w-12" />
            </div>
            <div>
              <Skeleton className="h-3 w-16 mb-1" />
              <Skeleton className="h-4 w-12" />
            </div>
            <div>
              <Skeleton className="h-3 w-16 mb-1" />
              <Skeleton className="h-4 w-12" />
            </div>
          </div>
          <Skeleton className="h-4 w-full" />
        </CardContent>
      </Card>
    ))}
  </div>
);

export const PluginManager: React.FC = () => {
  const {
    plugins,
    selectedPlugin,
    searchQuery,
    filters,
    sortBy,
    sortOrder,
    view,
    showInstallationWizard,
    showMarketplace,
    loadPlugins,
    selectPlugin,
    enablePlugin,
    disablePlugin,
    uninstallPlugin,
    setSearchQuery,
    setFilters,
    setSorting,
    setView,
    setShowInstallationWizard,
    setShowMarketplace,
    clearErrors,
  } = usePluginStore();
  
  const filteredPlugins = usePluginStore(selectFilteredPlugins);
  const loading = usePluginStore(selectPluginLoading('plugins'));
  const error = usePluginStore(selectPluginError('plugins'));
  
  const [configurePlugin, setConfigurePlugin] = useState<PluginInfo | null>(null);

  useEffect(() => {
    loadPlugins();
  }, [loadPlugins]);

  const handleRefresh = () => {
    clearErrors();
    loadPlugins();
  };

  const handleInstallPlugin = () => {
    setShowInstallationWizard(true);
  };

  const handleBrowseMarketplace = () => {
    setShowMarketplace(true);
  };

  const handleConfigurePlugin = (plugin: PluginInfo) => {
    setConfigurePlugin(plugin);
  };

  if (showInstallationWizard) {
    return (
      <PluginInstallationWizard 
        onClose={() => setShowInstallationWizard(false)}
        onComplete={() => {
          setShowInstallationWizard(false);
          loadPlugins();
        }}
      />
    );
  }

  if (showMarketplace) {
    return (
      <PluginMarketplace 
        onClose={() => setShowMarketplace(false)}
        onInstall={(plugin) => {
          setShowMarketplace(false);
          setShowInstallationWizard(true);
        }}
      />
    );
  }

  if (selectedPlugin) {
    return (
      <PluginDetailView 
        plugin={selectedPlugin}
        onClose={() => selectPlugin(null)}
        onEnable={enablePlugin}
        onDisable={disablePlugin}
        onUninstall={uninstallPlugin}
        onConfigure={handleConfigurePlugin}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Plugin Manager</h1>
          <p className="text-muted-foreground">
            Manage and monitor your installed plugins and extensions
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={handleRefresh} disabled={loading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button variant="outline" onClick={handleBrowseMarketplace}>
            <Search className="w-4 h-4 mr-2" />
            Browse Marketplace
          </Button>
          <Button onClick={handleInstallPlugin}>
            <Plus className="w-4 h-4 mr-2" />
            Install Plugin
          </Button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="w-4 h-4" />
          <AlertDescription>{typeof error === 'string' ? error : 'An error occurred'}</AlertDescription>
        </Alert>
      )}

      {/* Filters and Search */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div className="flex-1 max-w-md">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  placeholder="Search plugins..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <Select
                value={filters.status?.[0] || 'all'}
                onValueChange={(value) => 
                  setFilters({ status: value === 'all' ? undefined : [value as PluginStatus] })
                }
              >
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="inactive">Inactive</SelectItem>
                  <SelectItem value="error">Error</SelectItem>
                </SelectContent>
              </Select>
              
              <Select
                value={`${sortBy}-${sortOrder}`}
                onValueChange={(value) => {
                  const [field, order] = value.split('-');
                  setSorting(field, order as 'asc' | 'desc');
                }}
              >
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Sort by" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="name-asc">Name A-Z</SelectItem>
                  <SelectItem value="name-desc">Name Z-A</SelectItem>
                  <SelectItem value="status-asc">Status</SelectItem>
                  <SelectItem value="installedAt-desc">Recently Installed</SelectItem>
                  <SelectItem value="performance-asc">Performance</SelectItem>
                </SelectContent>
              </Select>
              
              <Separator orientation="vertical" className="h-6" />
              
              <div className="flex items-center border rounded-md">
                <Button
                  variant={view === 'list' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setView('list')}
                  className="rounded-r-none"
                >
                  <List className="w-4 h-4" />
                </Button>
                <Button
                  variant={view === 'grid' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setView('grid')}
                  className="rounded-l-none"
                >
                  <Grid className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Plugin List */}
      <div>
        {loading ? (
          <PluginListSkeleton />
        ) : filteredPlugins.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <div className="text-muted-foreground">
                {searchQuery || Object.keys(filters).length > 0 ? (
                  <>
                    <Search className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <h3 className="text-lg font-medium mb-2">No plugins found</h3>
                    <p>Try adjusting your search or filters</p>
                  </>
                ) : (
                  <>
                    <Plus className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <h3 className="text-lg font-medium mb-2">No plugins installed</h3>
                    <p className="mb-4">Get started by installing your first plugin</p>
                    <div className="flex justify-center gap-2">
                      <Button onClick={handleBrowseMarketplace}>
                        Browse Marketplace
                      </Button>
                      <Button variant="outline" onClick={handleInstallPlugin}>
                        Install Plugin
                      </Button>
                    </div>
                  </>
                )}
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className={view === 'grid' ? 'grid gap-4 md:grid-cols-2 lg:grid-cols-3' : 'space-y-4'}>
            {filteredPlugins.map((plugin) => (
              <PluginCard
                key={plugin.id}
                plugin={plugin}
                onSelect={selectPlugin}
                onEnable={enablePlugin}
                onDisable={disablePlugin}
                onUninstall={uninstallPlugin}
                onConfigure={handleConfigurePlugin}
                loading={loading}
              />
            ))}
          </div>
        )}
      </div>

      {/* Plugin Configuration Modal */}
      {configurePlugin && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-background rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <h2 className="text-xl font-semibold mb-4">Configure {configurePlugin.name}</h2>
            <p className="text-muted-foreground mb-6">
              Adjust settings for this plugin. Changes will be applied immediately.
            </p>
            
            {/* Configuration form would go here */}
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Plugin configuration interface will be implemented based on the plugin's manifest schema.
              </p>
            </div>
            
            <div className="flex justify-end gap-2 mt-6">
              <Button variant="outline" onClick={() => setConfigurePlugin(null)}>
                Cancel
              </Button>
              <Button onClick={() => setConfigurePlugin(null)}>
                Save Changes
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};