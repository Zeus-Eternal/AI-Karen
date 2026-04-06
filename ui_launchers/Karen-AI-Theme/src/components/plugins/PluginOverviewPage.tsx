"use client";

/**
 * @file PluginOverviewPage.tsx
 * @description Displays an overview of Karen AI's integrated plugins with
 * enhanced lifecycle controls and detailed status information.
 *
 * Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 10.1, 10.2, 10.3, 10.4
 */

import React, { useState } from "react";
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle
} from "@/components/ui/card";
import { 
  Button
} from "@/components/ui/button";
import { 
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem
} from "@/components/ui/dropdown-menu";
import { 
  Tooltip,
  TooltipTrigger,
  TooltipContent
} from "@/components/ui/tooltip";
import { 
  Alert, 
  AlertDescription, 
  AlertTitle 
} from "@/components/ui/alert";
import { usePluginRegistry, usePluginHealth, type PluginHealthRecord, type FrontendMountState } from "@/plugin_host/registry";
import { PluginHost } from "./PluginHost";
import { UIInstallerService } from "@/plugin_host/ui-installer";
import { 
  PlugZap, 
  MessageSquare, 
  Info, 
  Settings2, 
  Puzzle, 
  Loader2, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  EyeOff, 
  Clock,
  Save,
  RefreshCw,
  Trash2,
  Play,
  Pause,
  RotateCcw,
  Zap,
  Settings,
  Github,
  HelpCircle
} from "lucide-react";

// ─── Enhanced badge helpers ───────────────────────────────────────────────

type UIInstallStatus = 'not_installed' | 'installed' | 'removing' | 'restoring' | 'error' | 'installing';

interface EnhancedPluginHealthRecord extends PluginHealthRecord {
  // Extended fields for richer status
  uiInstallStatus?: UIInstallStatus;
  uiRegistrationStatus?: 'not_registered' | 'registered' | 'mountable' | 'mount_error';
  backendStatusDetail?: 'not_discovered' | 'discovered' | 'validated' | 'installed' | 'enabled' | 'disabled' | 'broken' | 'uninstalled' | 'restorable';
}

function BackendStateBadge({ state, detail }: { state: string; detail?: string }) {
  const getBadgeConfig = (state: string): { 
    icon: React.ComponentType<any>; 
    color: string; 
    label: string 
  } => {
    switch (state) {
      case 'active': return { icon: CheckCircle2, color: 'text-green-600 dark:text-green-400', label: 'active' };
      case 'error': return { icon: XCircle, color: 'text-destructive', label: 'error' };
      case 'disabled': return { icon: Pause, color: 'text-amber-600 dark:text-amber-400', label: 'disabled' };
      case 'broken': return { icon: Zap, color: 'text-orange-600 dark:text-orange-400', label: 'broken' };
      case 'uninstalled': return { icon: Trash2, color: 'text-muted-foreground', label: 'uninstalled' };
      case 'restorable': return { icon: RotateCcw, color: 'text-purple-600 dark:text-purple-400', label: 'restorable' };
      case 'validated': return { icon: CheckCircle2, color: 'text-blue-600 dark:text-blue-400', label: 'validated' };
      case 'discovered': return { icon: Github, color: 'text-gray-600 dark:text-gray-400', label: 'discovered' };
      case 'not_discovered': return { icon: HelpCircle, color: 'text-muted-foreground', label: 'not discovered' };
      default: return { icon: AlertTriangle, color: 'text-muted-foreground', label: state };
    }
  };

  const config = getBadgeConfig(state);
  return (
    <span className="inline-flex items-center gap-1 text-xs">
      <config.icon className={`h-3 w-3 ${config.color}`} />
      {detail ? `${config.label} (${detail})` : config.label}
    </span>
  );
}

function FrontendStateBadge({ state }: { state: FrontendMountState }) {
  switch (state) {
    case 'mounted':
      return (
        <span className="inline-flex items-center gap-1 text-xs text-green-600 dark:text-green-400">
          <CheckCircle2 className="h-3 w-3" /> mounted
        </span>
      );
    case 'error':
      return (
        <span className="inline-flex items-center gap-1 text-xs text-destructive">
          <XCircle className="h-3 w-3" /> render error
        </span>
      );
    case 'not_registered':
      return (
        <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
          <AlertTriangle className="h-3 w-3" /> not registered
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
          <Clock className="h-3 w-3" /> loading
        </span>
      );
  }
}

function UIInstallStatusBadge({ status }: { status: UIInstallStatus }) {
  switch (status) {
    case 'installed':
      return (
        <span className="inline-flex items-center gap-1 text-xs text-green-600 dark:text-green-400">
          <CheckCircle2 className="h-3 w-3" /> installed
        </span>
      );
    case 'not_installed':
      return (
        <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
          <AlertTriangle className="h-3 w-3" /> not installed
        </span>
      );
    case 'removing':
      return (
        <span className="inline-flex items-center gap-1 text-xs text-amber-600 dark:text-amber-400 animate-pulse">
          <Trash2 className="h-3 w-3" /> removing
        </span>
      );
    case 'restoring':
      return (
        <span className="inline-flex items-center gap-1 text-xs text-blue-600 dark:text-blue-400 animate-pulse">
          <RotateCcw className="h-3 w-3" /> restoring
        </span>
      );
    case 'error':
      return (
        <span className="inline-flex items-center gap-1 text-xs text-destructive">
          <XCircle className="h-3 w-3" /> error
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
          <HelpCircle className="h-3 w-3" /> unknown
        </span>
      );
  }
}

function UIRegistrationStatusBadge({ status }: { status: 'not_registered' | 'registered' | 'mountable' | 'mount_error' }) {
  switch (status) {
    case 'registered':
      return (
        <span className="inline-flex items-center gap-1 text-xs text-green-600 dark:text-green-400">
          <CheckCircle2 className="h-3 w-3" /> registered
        </span>
      );
    case 'mountable':
      return (
        <span className="inline-flex items-center gap-1 text-xs text-amber-600 dark:text-amber-400">
          <AlertTriangle className="h-3 w-3" /> mountable
        </span>
      );
    case 'mount_error':
      return (
        <span className="inline-flex items-center gap-1 text-xs text-destructive">
          <XCircle className="h-3 w-3" /> mount error
        </span>
      );
    case 'not_registered':
    default:
      return (
        <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
          <AlertTriangle className="h-3 w-3" /> not registered
        </span>
      );
  }
}

// ─── Per-plugin health card ───────────────────────────────────────────────────

function PluginHealthCard({ pluginId, displayName, description, version }: {
  pluginId: string;
  displayName: string;
  description: string;
  version: string;
}) {
  const health: PluginHealthRecord = usePluginHealth(pluginId);
  const [uiInstallStatus, setUiInstallStatus] = useState<UIInstallStatus>('not_installed');
  const [uiRegistrationStatus, setUiRegistrationStatus] = useState<'not_registered' | 'registered' | 'mountable' | 'mount_error'>('not_registered');
  
  const isUIBusy = (status: UIInstallStatus): boolean => {
    return status === 'installed' || status === 'removing' || status === 'restoring' || status === 'installing';
  };
  
  const isInstalling = (status: UIInstallStatus): boolean => {
    return status === 'installing';
  };
  
  const isRemoving = (status: UIInstallStatus): boolean => {
    return status === 'removing';
  };
  
  const isRestoring = (status: UIInstallStatus): boolean => {
    return status === 'restoring';
  };
  const [backendStatusDetail, setBackendStatusDetail] = useState<'not_discovered' | 'discovered' | 'validated' | 'installed' | 'enabled' | 'disabled' | 'broken' | 'uninstalled' | 'restorable'>('discovered');

  // Initialize extended status from basic health data
  React.useEffect(() => {
    // Map basic backend state to detailed status
    switch (health.backendState) {
      case 'active': setBackendStatusDetail('enabled'); break;
      case 'error': setBackendStatusDetail('broken'); break;
      default: setBackendStatusDetail('discovered'); // Default for discovered/not loaded
    }
  }, [health.backendState]);

  // Determine if plugin has UI capabilities based on menu contributions
  const hasUiCapabilities = health.pluginId && 
    // In a real implementation, we'd check the registry for UI capabilities
    // For now, we'll assume plugins with menu contributions have UI
    true; // Simplified - in reality would check registry data

  const hasDiscrepancy =
    health.backendState === 'active' && health.frontendMountState === 'error';

  const handleInstallUI = async () => {
    setUiInstallStatus('installing');
    try {
      const installer = UIInstallerService.getInstance();
      const result = await installer.installUI(pluginId);
      if (result.success) {
        setUiInstallStatus('installed');
        setUiRegistrationStatus('registered'); // Assume registration happens after install
      } else {
        setUiInstallStatus('error');
        console.error(`Failed to install UI for ${pluginId}:`, result.message);
      }
    } catch (error) {
      setUiInstallStatus('error');
      console.error(`Error installing UI for ${pluginId}:`, error);
    }
  };

  const handleRemoveUI = async () => {
    setUiInstallStatus('removing');
    try {
      const installer = UIInstallerService.getInstance();
      const result = await installer.removeUI(pluginId);
      if (result.success) {
        setUiInstallStatus('not_installed');
        setUiRegistrationStatus('not_registered');
      } else {
        setUiInstallStatus('error');
        console.error(`Failed to remove UI for ${pluginId}:`, result.message);
      }
    } catch (error) {
      setUiInstallStatus('error');
      console.error(`Error removing UI for ${pluginId}:`, error);
    }
  };

  const handleRestoreUI = async () => {
    setUiInstallStatus('restoring');
    try {
      const installer = UIInstallerService.getInstance();
      const result = await installer.restoreUI(pluginId);
      if (result.success) {
        setUiInstallStatus('installed');
        setUiRegistrationStatus('registered');
      } else {
        setUiInstallStatus('error');
        console.error(`Failed to restore UI for ${pluginId}:`, result.message);
      }
    } catch (error) {
      setUiInstallStatus('error');
      console.error(`Error restoring UI for ${pluginId}:`, error);
    }
  };

  const handleRetryRegistration = async () => {
    // In a real implementation, this would trigger re-registration
    // For now, we'll simulate by toggling registration status
    setUiRegistrationStatus('registered');
  };

  return (
    <div className="p-4 border rounded-lg bg-muted/30 space-y-3">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h4 className="font-semibold text-sm">
            {displayName}
            <span className="text-xs font-normal opacity-50 ml-2">v{version}</span>
          </h4>
          <p className="text-xs text-muted-foreground">{description || "No description provided."}</p>
        </div>
        {!health.permissionVisible && (
          <span className="inline-flex items-center gap-1 text-xs text-muted-foreground shrink-0">
            <EyeOff className="h-3 w-3" /> hidden
          </span>
        )}
      </div>

      {/* Enhanced health status row */}
      <div className="grid gap-3 text-xs">
        <div className="flex items-center gap-2">
          <span className="text-muted-foreground">Backend:</span>
          <BackendStateBadge 
            state={health.backendState} 
            detail={backendStatusDetail} 
          />
        </div>
        <div className="flex items-center gap-2">
          <span className="text-muted-foreground">Frontend:</span>
          <FrontendStateBadge state={health.frontendMountState} />
        </div>
        {hasUiCapabilities && (
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground">UI Install:</span>
            <UIInstallStatusBadge status={uiInstallStatus} />
          </div>
        )}
        {hasUiCapabilities && (
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground">UI Reg:</span>
            <UIRegistrationStatusBadge status={uiRegistrationStatus} />
          </div>
        )}
      </div>

      {/* Enhanced discrepancy warnings */}
      {health.backendState === 'active' && health.frontendMountState === 'error' && (
        <Alert variant="destructive" className="py-2 px-3">
          <AlertTriangle className="h-3 w-3" />
          <AlertDescription className="text-xs">
            Backend reports active but the UI component failed to render.
            {health.errorMessage && <> Error: {health.errorMessage}</>}
          </AlertDescription>
        </Alert>
      )}
      
      {/* UI-specific discrepancy */}
      {hasUiCapabilities && uiInstallStatus === 'installed' && health.frontendMountState === 'not_registered' && (
        <Alert variant="warning" className="py-2 px-3">
          <AlertTriangle className="h-3 w-3" />
          <AlertDescription className="text-xs">
            UI installed but not registered. Retry registration to fix.
          </AlertDescription>
        </Alert>
      )}

      {/* Plugin controls */}
      <div className="flex flex-wrap gap-2 mt-3">
        {/* Plugin UI preview */}
        {health.permissionVisible && (
          <div className="mt-2 bg-background/50 border border-border p-2 rounded">
            <PluginHost pluginId={pluginId} />
          </div>
        )}
        
        {/* Action buttons */}
        <div className="flex flex-wrap gap-2">
          {hasUiCapabilities && (
            <>
              {uiInstallStatus === 'not_installed' && (
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={handleInstallUI}
                  disabled={isUIBusy(uiInstallStatus)}
                >
                  {isInstalling(uiInstallStatus) ? 'Installing...' : 'Install UI'}
                </Button>
              )}
              
              {uiInstallStatus === 'installed' && (
                <>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={handleRemoveUI}
                    disabled={isRemoving(uiInstallStatus)}
                  >
                    {isRemoving(uiInstallStatus) ? 'Removing...' : 'Remove UI'}
                  </Button>
                  
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    onClick={handleRestoreUI}
                    disabled={isRestoring(uiInstallStatus)}
                  >
                    {isRestoring(uiInstallStatus) ? 'Restoring...' : 'Restore UI'}
                  </Button>
                </>
              )}
              
              {(uiInstallStatus === 'installed' || uiInstallStatus === 'error') && (
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={handleRetryRegistration}
                  disabled={uiRegistrationStatus === 'registered'}
                >
                  {uiRegistrationStatus === 'registered' ? 'Registered' : 'Retry Registration'}
                </Button>
              )}
            </>
          )}
          
          {/* Enable/Disable controls */}
          {health.backendState !== 'error' && (
            <>
              {health.backendState === 'active' && (
                <Button 
                  variant="outline" 
                  size="sm" 
                  // In a real implementation, this would call backend disable API
                  onClick={() => {/* TODO: Implement disable */}}
                  disabled={false}
                >
                  Disable
                </Button>
              )}
              
              {health.backendState !== 'active' && (
                <Button 
                  variant="outline" 
                  size="sm" 
                  // In a real implementation, this would call backend enable API
                  onClick={() => {/* TODO: Implement enable */}}
                  disabled={false}
                >
                  Enable
                </Button>
              )}
            </>
          )}
          
          {/* Uninstall control */}
          {health.backendState !== 'uninstalled' && (
            <Button 
              variant="destructive" 
              size="sm" 
              // In a real implementation, this would call backend uninstall API
              onClick={() => {/* TODO: Implement uninstall */}}
              disabled={false}
            >
              Uninstall
            </Button>
          )}
          
          {/* Restore control for uninstalled plugins */}
          {health.backendState === 'uninstalled' && (
            <Button 
              variant="outline" 
              size="sm" 
              // In a real implementation, this would call backend restore API
              onClick={() => {/* TODO: Implement restore */}}
              disabled={false}
            >
              Restore
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function PluginOverviewPage() {
  const { plugins, loading, error } = usePluginRegistry();

  return (
    <div className="space-y-8">
      <div className="flex items-center space-x-3">
        <PlugZap className="h-8 w-8 text-primary" />
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">Karen AI - Plugins & Tools Overview</h2>
          <p className="text-sm text-muted-foreground">
            Understanding Karen AI's capabilities and how she integrates new features.
          </p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Current Plugin & Tool Integration</CardTitle>
          <CardDescription>
            Karen AI uses a "prompt-first" framework. Her core AI is instructed on how to use
            available tools and capabilities based on your conversational requests.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm">
            When you interact with Karen, her central AI decision-making flow determines if a
            specialized tool is needed. If so, it invokes the tool and crafts a response based
            on the tool's output.
          </p>
          <Alert>
            <MessageSquare className="h-4 w-4" />
            <AlertTitle>Interaction Method</AlertTitle>
            <AlertDescription>
              Most of these tools are used by Karen when you ask relevant questions or make
              requests directly in the chat interface.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Registered Plugin Components</CardTitle>
          <CardDescription>
            Each card shows the combined backend + frontend health state for the plugin.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center p-8">
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
            </div>
          ) : error ? (
            <Alert variant="destructive">
              <XCircle className="h-4 w-4" />
              <AlertTitle>Failed to load plugin catalog</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : plugins.length === 0 ? (
            <div className="text-sm text-muted-foreground">
              No dynamic extensions registered yet. Ensure the Python manager discovered them.
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              {plugins.map((plugin) => (
                <PluginHealthCard
                  key={plugin.id}
                  pluginId={plugin.id}
                  displayName={plugin.displayName}
                  description={plugin.description}
                  version={plugin.version}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center">
            <Settings2 className="mr-2 h-5 w-5 text-primary/80" />
            Vision for Advanced Plugin Architecture
          </CardTitle>
          <CardDescription>
            The long-term goal for Karen AI is to support a more dynamic plugin system.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-muted-foreground">
            Imagine a system where new capabilities could be added and Karen AI could understand
            how to use them based on their defined schemas without requiring manual updates to
            her core logic. This would involve:
          </p>
          <ul className="list-disc list-inside pl-5 text-xs text-muted-foreground space-y-1">
            <li>Standardized plugin schemas describing inputs, outputs, and purpose.</li>
            <li>An AI meta-learning capability for Karen to dynamically understand new tools.</li>
            <li>A secure way to manage and register these plugins.</li>
          </ul>
          <Alert variant="default" className="bg-background">
            <Info className="h-4 w-4" />
            <AlertTitle className="text-sm font-semibold">Developer Note</AlertTitle>
            <AlertDescription className="text-xs">
              Achieving true "drag-and-drop" dynamic plugin integration with autonomous learning
              is a complex AI research and engineering challenge. The current system relies on
              developers explicitly defining tools and guiding Karen's use of them through
              prompt engineering.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>

      <Alert className="mt-6">
        <Puzzle className="h-4 w-4" />
        <AlertTitle>Connecting to the Automation Hub</AlertTitle>
        <AlertDescription>
          The tools provided by these plugins are the building blocks for creating agent skills
          in the Automation Hub. You can assign these tools to agents, enabling them to perform
          complex automated tasks.
        </AlertDescription>
      </Alert>
    </div>
  );
}
