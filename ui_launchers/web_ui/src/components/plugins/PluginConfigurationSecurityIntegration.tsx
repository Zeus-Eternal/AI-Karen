import React, { useState, useEffect } from 'react';
import { 
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { PluginInfo, PluginConfig, PluginMarketplaceEntry } from '@/types/plugins';
import { DynamicPluginConfigForm } from './DynamicPluginConfigForm';
import { PluginSecurityManager } from './PluginSecurityManager';
import { PluginAuditLogger } from './PluginAuditLogger';
import { EnhancedPluginMarketplace } from './EnhancedPluginMarketplace';
/**
 * Plugin Configuration and Security Integration Component
 * 
 * Integrates dynamic plugin configuration forms, security management, audit logging,
 * and marketplace functionality into a unified interface.
 * Based on requirements: 5.3, 5.5, 9.1, 9.2, 9.4
 */
"use client";


  Settings, 
  Shield, 
  FileText, 
  Store, 
  ArrowLeft,
  Save,
  AlertTriangle,
  CheckCircle,
  Info,
  RefreshCw,
  Download,
  Eye,
  Lock,
  Unlock,
} from 'lucide-react';







  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';





interface SecurityPolicy {
  allowNetworkAccess: boolean;
  allowFileSystemAccess: boolean;
  allowSystemCalls: boolean;
  trustedDomains: string[];
  sandboxed: boolean;
  isolationLevel: 'none' | 'basic' | 'strict' | 'maximum';
  resourceLimits: {
    maxMemory: number;
    maxCpu: number;
    maxDisk: number;
    maxNetworkBandwidth: number;
  };
  timeouts: {
    executionTimeout: number;
    networkTimeout: number;
    fileOperationTimeout: number;
  };
}
interface PluginConfigurationSecurityIntegrationProps {
  plugin: PluginInfo;
  onClose: () => void;
  onSaveConfiguration: (config: PluginConfig) => Promise<void>;
  onUpdateSecurity: (policy: SecurityPolicy) => Promise<void>;
  onGrantPermission: (permissionId: string) => Promise<void>;
  onRevokePermission: (permissionId: string) => Promise<void>;
  onInstallFromMarketplace: (plugin: PluginMarketplaceEntry) => Promise<void>;
  onPurchasePlugin?: (plugin: PluginMarketplaceEntry) => Promise<void>;
  onExportAuditLog?: (format: 'csv' | 'json' | 'pdf') => void;
  onGenerateReport?: (type: 'compliance' | 'security' | 'activity') => void;
  readOnly?: boolean;
}
export const PluginConfigurationSecurityIntegration: React.FC<PluginConfigurationSecurityIntegrationProps> = ({
  plugin,
  onClose,
  onSaveConfiguration,
  onUpdateSecurity,
  onGrantPermission,
  onRevokePermission,
  onInstallFromMarketplace,
  onPurchasePlugin,
  onExportAuditLog,
  onGenerateReport,
  readOnly = false,
}) => {
  const [activeTab, setActiveTab] = useState<'configuration' | 'security' | 'audit' | 'marketplace'>('configuration');
  const [showMarketplace, setShowMarketplace] = useState(false);
  const [configurationChanged, setConfigurationChanged] = useState(false);
  const [securityChanged, setSecurityChanged] = useState(false);
  const [saving, setSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  // Track configuration changes
  const handleConfigurationChange = () => {
    setConfigurationChanged(true);
  };
  // Track security policy changes
  const handleSecurityChange = () => {
    setSecurityChanged(true);
  };
  // Save configuration
  const handleSaveConfiguration = async (config: PluginConfig) => {
    setSaving(true);
    try {
      await onSaveConfiguration(config);
      setConfigurationChanged(false);
      setLastSaved(new Date());
    } finally {
      setSaving(false);
    }
  };
  // Save security policy
  const handleSaveSecurityPolicy = async (policy: SecurityPolicy) => {
    setSaving(true);
    try {
      await onUpdateSecurity(policy);
      setSecurityChanged(false);
      setLastSaved(new Date());
    } finally {
      setSaving(false);
    }
  };
  // Validate configuration before saving
  const validateConfiguration = (config: PluginConfig) => {
    const errors = [];
    // Check required fields
    if (plugin.manifest.configSchema) {
      for (const field of plugin.manifest.configSchema) {
        if (field.required && (!config[field.key] || config[field.key] === '')) {
          errors.push({
            field: field.key,
            message: `${field.label} is required`,
            severity: 'error' as const,
          });
        }
      }
    }
    return errors;
  };
  // Get security risk level
  const getSecurityRiskLevel = (): { level: string; color: string; description: string } => {
    let riskScore = 0;
    if (plugin.manifest.securityPolicy.allowNetworkAccess) riskScore += 2;
    if (plugin.manifest.securityPolicy.allowFileSystemAccess) riskScore += 3;
    if (plugin.manifest.securityPolicy.allowSystemCalls) riskScore += 4;
    if (!plugin.manifest.sandboxed) riskScore += 3;
    const adminPermissions = plugin.manifest.permissions.filter(p => p.level === 'admin').length;
    riskScore += adminPermissions;
    if (riskScore <= 2) return { level: 'Low', color: 'text-green-600', description: 'Minimal security risk' };
    if (riskScore <= 5) return { level: 'Medium', color: 'text-yellow-600', description: 'Moderate security risk' };
    if (riskScore <= 8) return { level: 'High', color: 'text-orange-600', description: 'Elevated security risk' };
    return { level: 'Critical', color: 'text-red-600', description: 'High security risk' };
  };
  const securityRisk = getSecurityRiskLevel();
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button variant="ghost" size="sm" onClick={onClose} aria-label="Button">
            <ArrowLeft className="w-4 h-4 mr-2 sm:w-auto md:w-full" />
            Back to Plugins
          </Button>
          <div>
            <h1 className="text-2xl font-bold">Plugin Management</h1>
            <p className="text-muted-foreground">
              Configure settings, security, and monitor activity for {plugin.name}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {lastSaved && (
            <div className="text-sm text-muted-foreground md:text-base lg:text-lg">
              Last saved: {lastSaved.toLocaleTimeString()}
            </div>
          )}
          <button
            variant="outline"
            size="sm"
            onClick={() = aria-label="Button"> setShowMarketplace(true)}
          >
            <Store className="w-4 h-4 mr-2 sm:w-auto md:w-full" />
            Marketplace
          </Button>
        </div>
      </div>
      {/* Plugin Overview Card */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                {plugin.name}
                <Badge variant={plugin.status === 'active' ? 'default' : 'secondary'}>
                  {plugin.status}
                </Badge>
                {plugin.manifest.sandboxed && (
                  <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                    <Shield className="w-3 h-3 mr-1 sm:w-auto md:w-full" />
                    Sandboxed
                  </Badge>
                )}
              </CardTitle>
              <CardDescription>
                {plugin.manifest.description}
              </CardDescription>
            </div>
            <div className="text-right">
              <div className="text-sm font-medium md:text-base lg:text-lg">Security Risk</div>
              <div className={`text-sm ${securityRisk.color}`}>
                {securityRisk.level}
              </div>
              <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
                {securityRisk.description}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-6 text-sm text-muted-foreground md:text-base lg:text-lg">
            <span>Version {plugin.version}</span>
            <span>by {plugin.manifest.author.name}</span>
            <span className="capitalize">{plugin.manifest.category}</span>
            <span>{plugin.manifest.permissions.length} permissions</span>
          </div>
        </CardHeader>
      </Card>
      {/* Status Alerts */}
      {(configurationChanged || securityChanged) && (
        <Alert>
          <Info className="w-4 h-4 sm:w-auto md:w-full" />
          <AlertDescription>
            You have unsaved changes. Don't forget to save your {configurationChanged ? 'configuration' : 'security policy'}.
          </AlertDescription>
        </Alert>
      )}
      {plugin.status === 'error' && plugin.lastError && (
        <Alert variant="destructive">
          <AlertTriangle className="w-4 h-4 sm:w-auto md:w-full" />
          <AlertDescription>
            Plugin error: {plugin.lastError.message}
          </AlertDescription>
        </Alert>
      )}
      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={(value: any) => setActiveTab(value)} className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="configuration" className="flex items-center gap-2">
            <Settings className="w-4 h-4 sm:w-auto md:w-full" />
            Configuration
          </TabsTrigger>
          <TabsTrigger value="security" className="flex items-center gap-2">
            <Shield className="w-4 h-4 sm:w-auto md:w-full" />
            Security
          </TabsTrigger>
          <TabsTrigger value="audit" className="flex items-center gap-2">
            <FileText className="w-4 h-4 sm:w-auto md:w-full" />
            Audit & Logs
          </TabsTrigger>
          <TabsTrigger value="marketplace" className="flex items-center gap-2">
            <Store className="w-4 h-4 sm:w-auto md:w-full" />
            Marketplace
          </TabsTrigger>
        </TabsList>
        <TabsContent value="configuration" className="space-y-4">
          <DynamicPluginConfigForm
            plugin={plugin}
            initialConfig={plugin.config}
            onSave={handleSaveConfiguration}
            onValidate={validateConfiguration}
            onPreview={(config) => {
            }}
            readOnly={readOnly}
            showAdvanced={true}
          />
        </TabsContent>
        <TabsContent value="security" className="space-y-4">
          <PluginSecurityManager
            plugin={plugin}
            onUpdateSecurity={handleSaveSecurityPolicy}
            onGrantPermission={onGrantPermission}
            onRevokePermission={onRevokePermission}
            readOnly={readOnly}
          />
        </TabsContent>
        <TabsContent value="audit" className="space-y-4">
          <PluginAuditLogger
            plugin={plugin}
            onExportAuditLog={onExportAuditLog}
            onGenerateReport={onGenerateReport}
          />
        </TabsContent>
        <TabsContent value="marketplace" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Plugin Marketplace</CardTitle>
              <CardDescription>
                Discover and install additional plugins to extend functionality
              </CardDescription>
            </CardHeader>
            <CardContent>
              <button onClick={() = aria-label="Button"> setShowMarketplace(true)}>
                <Store className="w-4 h-4 mr-2 sm:w-auto md:w-full" />
                Open Marketplace
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
      {/* Marketplace Dialog */}
      <Dialog open={showMarketplace} onOpenChange={setShowMarketplace}>
        <DialogContent className="max-w-6xl max-h-[90vh] overflow-hidden sm:w-auto md:w-full">
          <DialogHeader>
            <DialogTitle>Plugin Marketplace</DialogTitle>
            <DialogDescription>
              Discover and install plugins to extend Kari AI functionality
            </DialogDescription>
          </DialogHeader>
          <div className="flex-1 overflow-hidden">
            <EnhancedPluginMarketplace
              onClose={() => setShowMarketplace(false)}
              onInstall={onInstallFromMarketplace}
              onPurchase={onPurchasePlugin}
            />
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};
