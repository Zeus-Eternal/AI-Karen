import React, { useState, useEffect } from 'react';
import { ErrorBoundary } from '@/components/error-handling/ErrorBoundary';
import { 
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Progress } from '@/components/ui/progress';
import {
import { PluginInfo, Permission } from '@/types/plugins';
/**
 * Plugin Security Manager Component
 * 
 * Manages plugin sandboxing controls and security policy enforcement.
 * Based on requirements: 5.3, 9.1, 9.2, 9.4
 */
"use client";


  Shield, 
  Lock, 
  Unlock,
  AlertTriangle, 
  CheckCircle, 
  XCircle,
  Eye,
  EyeOff,
  Settings,
  Network,
  HardDrive,
  Cpu,
  Globe,
  Users,
  Database,
  Key,
  FileText,
  Activity,
  Clock,
  Target,
  Zap,
  RefreshCw,
  Save,
  RotateCcw,
  Info,
  ExternalLink,
  Download,
  Upload,
} from 'lucide-react';













  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';

  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';

interface SecurityPolicy {
  allowNetworkAccess: boolean;
  allowFileSystemAccess: boolean;
  allowSystemCalls: boolean;
  trustedDomains: string[];
  sandboxed: boolean;
  isolationLevel: 'none' | 'basic' | 'strict' | 'maximum';
  resourceLimits: {
    maxMemory: number; // MB
    maxCpu: number; // percentage
    maxDisk: number; // MB
    maxNetworkBandwidth: number; // MB/s
  };
  timeouts: {
    executionTimeout: number; // seconds
    networkTimeout: number; // seconds
    fileOperationTimeout: number; // seconds
  };
}
interface SecurityViolation {
  id: string;
  timestamp: Date;
  type: 'permission' | 'resource' | 'network' | 'filesystem' | 'timeout';
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  details: Record<string, any>;
  resolved: boolean;
}
interface PluginSecurityManagerProps {
  plugin: PluginInfo;
  onUpdateSecurity: (policy: SecurityPolicy) => Promise<void>;
  onGrantPermission: (permissionId: string) => Promise<void>;
  onRevokePermission: (permissionId: string) => Promise<void>;
  readOnly?: boolean;
}
export const PluginSecurityManager: React.FC<PluginSecurityManagerProps> = ({
  plugin,
  onUpdateSecurity,
  onGrantPermission,
  onRevokePermission,
  readOnly = false,
}) => {
  const [securityPolicy, setSecurityPolicy] = useState<SecurityPolicy>({
    allowNetworkAccess: plugin.manifest.securityPolicy.allowNetworkAccess,
    allowFileSystemAccess: plugin.manifest.securityPolicy.allowFileSystemAccess,
    allowSystemCalls: plugin.manifest.securityPolicy.allowSystemCalls,
    trustedDomains: plugin.manifest.securityPolicy.trustedDomains || [],
    sandboxed: plugin.manifest.sandboxed,
    isolationLevel: plugin.manifest.sandboxed ? 'strict' : 'none',
    resourceLimits: {
      maxMemory: 256,
      maxCpu: 50,
      maxDisk: 100,
      maxNetworkBandwidth: 10,
    },
    timeouts: {
      executionTimeout: 30,
      networkTimeout: 10,
      fileOperationTimeout: 5,
    },
  });
  const [grantedPermissions, setGrantedPermissions] = useState<Set<string>>(
    new Set(plugin.permissions.map(p => p.id))
  );
  const [violations, setViolations] = useState<SecurityViolation[]>([
    {
      id: 'v1',
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
      type: 'network',
      severity: 'medium',
      description: 'Attempted to access non-trusted domain',
      details: { domain: 'suspicious-site.com', blocked: true },
      resolved: false,
    },
    {
      id: 'v2',
      timestamp: new Date(Date.now() - 30 * 60 * 1000),
      type: 'resource',
      severity: 'low',
      description: 'Memory usage exceeded 80% of limit',
      details: { usage: 205, limit: 256 },
      resolved: true,
    },
  ]);
  const [saving, setSaving] = useState(false);
  const [newTrustedDomain, setNewTrustedDomain] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const handleSavePolicy = async () => {
    setSaving(true);
    try {
      await onUpdateSecurity(securityPolicy);
    } finally {
      setSaving(false);
    }
  };
  const handlePermissionToggle = async (permission: Permission, granted: boolean) => {
    try {
      if (granted) {
        await onGrantPermission(permission.id);
        setGrantedPermissions(prev => new Set([...prev, permission.id]));
      } else {
        await onRevokePermission(permission.id);
        setGrantedPermissions(prev => {
          const newSet = new Set(prev);
          newSet.delete(permission.id);
          return newSet;
        });
      }
    } catch (error) {
    }
  };
  const addTrustedDomain = () => {
    if (newTrustedDomain && !securityPolicy.trustedDomains.includes(newTrustedDomain)) {
      setSecurityPolicy(prev => ({
        ...prev,
        trustedDomains: [...prev.trustedDomains, newTrustedDomain],
      }));
      setNewTrustedDomain('');
    }
  };
  const removeTrustedDomain = (domain: string) => {
    setSecurityPolicy(prev => ({
      ...prev,
      trustedDomains: prev.trustedDomains.filter(d => d !== domain),
    }));
  };
  const getSecurityScore = (): number => {
    let score = 100;
    if (securityPolicy.allowNetworkAccess) score -= 15;
    if (securityPolicy.allowFileSystemAccess) score -= 20;
    if (securityPolicy.allowSystemCalls) score -= 25;
    if (!securityPolicy.sandboxed) score -= 30;
    const highRiskPermissions = plugin.manifest.permissions.filter(p => 
      p.level === 'admin' && grantedPermissions.has(p.id)
    ).length;
    score -= highRiskPermissions * 10;
    return Math.max(0, score);
  };
  const getSecurityLevel = (score: number): { level: string; color: string; description: string } => {
    if (score >= 80) return { level: 'High', color: 'text-green-600', description: 'Well secured' };
    if (score >= 60) return { level: 'Medium', color: 'text-yellow-600', description: 'Moderately secure' };
    if (score >= 40) return { level: 'Low', color: 'text-orange-600', description: 'Security concerns' };
    return { level: 'Critical', color: 'text-red-600', description: 'High security risk' };
  };
  const securityScore = getSecurityScore();
  const securityLevel = getSecurityLevel(securityScore);
  const renderPermissionCard = (permission: Permission) => {
    const isGranted = grantedPermissions.has(permission.id);
    const isRequired = permission.required;
    return (
    <ErrorBoundary fallback={<div>Something went wrong in PluginSecurityManager</div>}>
      <Card key={permission.id} className={`${isRequired ? 'border-orange-200' : ''}`}>
        <CardContent className="p-4 sm:p-4 md:p-6">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <h4 className="font-medium">{permission.name}</h4>
                <Badge 
                  variant={
                    permission.level === 'admin' ? 'destructive' :
                    permission.level === 'write' ? 'default' : 'secondary'
                  }
                  className="text-xs sm:text-sm md:text-base"
                >
                  {permission.level}
                </Badge>
                {isRequired && (
                  <Badge variant="outline" className="text-xs sm:text-sm md:text-base">Required</Badge>
                )}
              </div>
              <p className="text-sm text-muted-foreground mb-3 md:text-base lg:text-lg">{permission.description}</p>
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                  {permission.category}
                </Badge>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Switch
                checked={isGranted}
                onCheckedChange={(checked) => handlePermissionToggle(permission, checked)}
                disabled={readOnly || isRequired}
              />
              <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
                {isGranted ? 'Granted' : 'Denied'}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };
  const renderViolation = (violation: SecurityViolation) => {
    const severityConfig = {
      low: { variant: 'default' as const, icon: Info, color: 'text-blue-600' },
      medium: { variant: 'default' as const, icon: AlertTriangle, color: 'text-yellow-600' },
      high: { variant: 'destructive' as const, icon: AlertTriangle, color: 'text-orange-600' },
      critical: { variant: 'destructive' as const, icon: XCircle, color: 'text-red-600' },
    };
    const config = severityConfig[violation.severity];
    const ViolationIcon = config.icon;
    return (
      <Alert key={violation.id} variant={config.variant} className="mb-3">
        <ViolationIcon className="w-4 h-4 sm:w-auto md:w-full" />
        <div className="flex-1">
          <div className="flex items-center justify-between">
            <AlertDescription className="font-medium">
              {violation.description}
            </AlertDescription>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                {violation.type}
              </Badge>
              {violation.resolved && (
                <CheckCircle className="w-4 h-4 text-green-600 sm:w-auto md:w-full" />
              )}
            </div>
          </div>
          <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground sm:text-sm md:text-base">
            <span className="capitalize">{violation.severity}</span>
            <span>{violation.timestamp.toLocaleString()}</span>
          </div>
        </div>
      </Alert>
    );
  };
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Security Management</h2>
          <p className="text-muted-foreground">
            Manage security policies and permissions for {plugin.name}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            variant="outline"
            size="sm"
            onClick={() = aria-label="Button"> setShowAdvanced(!showAdvanced)}
          >
            <Settings className="w-4 h-4 mr-2 sm:w-auto md:w-full" />
            {showAdvanced ? 'Simple' : 'Advanced'}
          </Button>
          {!readOnly && (
            <button onClick={handleSavePolicy} disabled={saving} aria-label="Button">
              {saving ? (
                <RefreshCw className="w-4 h-4 mr-2 animate-spin sm:w-auto md:w-full" />
              ) : (
                <Save className="w-4 h-4 mr-2 sm:w-auto md:w-full" />
              )}
              {saving ? 'Saving...' : 'Save Policy'}
            </Button>
          )}
        </div>
      </div>
      {/* Security Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5 sm:w-auto md:w-full" />
            Security Overview
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="relative w-24 h-24 mx-auto mb-4 sm:w-auto md:w-full">
                <div className="absolute inset-0 rounded-full bg-muted">
                  <div 
                    className="absolute inset-0 rounded-full bg-gradient-to-r from-red-500 via-yellow-500 to-green-500"
                    style={{
                      clipPath: `polygon(50% 50%, 50% 0%, ${50 + (securityScore / 100) * 50}% 0%, ${50 + (securityScore / 100) * 50}% 100%, 50% 100%)`
                    }}
                  />
                  <div className="absolute inset-2 rounded-full bg-background flex items-center justify-center">
                    <span className="text-2xl font-bold">{securityScore}</span>
                  </div>
                </div>
              </div>
              <h3 className={`font-medium ${securityLevel.color}`}>{securityLevel.level}</h3>
              <p className="text-sm text-muted-foreground md:text-base lg:text-lg">{securityLevel.description}</p>
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm md:text-base lg:text-lg">Sandboxed</span>
                <Badge variant={securityPolicy.sandboxed ? 'default' : 'destructive'}>
                  {securityPolicy.sandboxed ? 'Yes' : 'No'}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm md:text-base lg:text-lg">Network Access</span>
                <Badge variant={securityPolicy.allowNetworkAccess ? 'destructive' : 'default'}>
                  {securityPolicy.allowNetworkAccess ? 'Allowed' : 'Blocked'}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm md:text-base lg:text-lg">File System</span>
                <Badge variant={securityPolicy.allowFileSystemAccess ? 'destructive' : 'default'}>
                  {securityPolicy.allowFileSystemAccess ? 'Allowed' : 'Blocked'}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm md:text-base lg:text-lg">System Calls</span>
                <Badge variant={securityPolicy.allowSystemCalls ? 'destructive' : 'default'}>
                  {securityPolicy.allowSystemCalls ? 'Allowed' : 'Blocked'}
                </Badge>
              </div>
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm md:text-base lg:text-lg">Permissions</span>
                <span className="text-sm font-medium md:text-base lg:text-lg">
                  {grantedPermissions.size} / {plugin.manifest.permissions.length}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm md:text-base lg:text-lg">Violations</span>
                <span className="text-sm font-medium md:text-base lg:text-lg">
                  {violations.filter(v => !v.resolved).length} active
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm md:text-base lg:text-lg">Trusted Domains</span>
                <span className="text-sm font-medium md:text-base lg:text-lg">{securityPolicy.trustedDomains.length}</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
      <Tabs defaultValue="permissions" className="space-y-4">
        <TabsList>
          <TabsTrigger value="permissions">Permissions</TabsTrigger>
          <TabsTrigger value="policy">Security Policy</TabsTrigger>
          <TabsTrigger value="violations">Violations</TabsTrigger>
          {showAdvanced && <TabsTrigger value="advanced">Advanced</TabsTrigger>}
        </TabsList>
        <TabsContent value="permissions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Permission Management</CardTitle>
              <CardDescription>
                Control what actions this plugin can perform
              </CardDescription>
            </CardHeader>
            <CardContent>
              {plugin.manifest.permissions.length === 0 ? (
                <div className="text-center py-8">
                  <Shield className="w-12 h-12 mx-auto mb-4 opacity-50 sm:w-auto md:w-full" />
                  <h3 className="text-lg font-medium mb-2">No Permissions Required</h3>
                  <p className="text-muted-foreground">
                    This plugin doesn't require any special permissions
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {plugin.manifest.permissions.map(renderPermissionCard)}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="policy" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Security Policy</CardTitle>
              <CardDescription>
                Configure security restrictions and access controls
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h4 className="font-medium">Access Controls</h4>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Network className="w-4 h-4 sm:w-auto md:w-full" />
                      <Label>Network Access</Label>
                    </div>
                    <Switch
                      checked={securityPolicy.allowNetworkAccess}
                      onCheckedChange={(checked) => 
                        setSecurityPolicy(prev => ({ ...prev, allowNetworkAccess: checked }))
                      }
                      disabled={readOnly}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <HardDrive className="w-4 h-4 sm:w-auto md:w-full" />
                      <Label>File System Access</Label>
                    </div>
                    <Switch
                      checked={securityPolicy.allowFileSystemAccess}
                      onCheckedChange={(checked) => 
                        setSecurityPolicy(prev => ({ ...prev, allowFileSystemAccess: checked }))
                      }
                      disabled={readOnly}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Cpu className="w-4 h-4 sm:w-auto md:w-full" />
                      <Label>System Calls</Label>
                    </div>
                    <Switch
                      checked={securityPolicy.allowSystemCalls}
                      onCheckedChange={(checked) => 
                        setSecurityPolicy(prev => ({ ...prev, allowSystemCalls: checked }))
                      }
                      disabled={readOnly}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Shield className="w-4 h-4 sm:w-auto md:w-full" />
                      <Label>Sandboxed Execution</Label>
                    </div>
                    <Switch
                      checked={securityPolicy.sandboxed}
                      onCheckedChange={(checked) => 
                        setSecurityPolicy(prev => ({ ...prev, sandboxed: checked }))
                      }
                      disabled={readOnly}
                    />
                  </div>
                </div>
                <div className="space-y-4">
                  <h4 className="font-medium">Isolation Level</h4>
                  <select
                    value={securityPolicy.isolationLevel}
                    onValueChange={(value: any) = aria-label="Select option"> 
                      setSecurityPolicy(prev => ({ ...prev, isolationLevel: value }))
                    }
                    disabled={readOnly}
                  >
                    <selectTrigger aria-label="Select option">
                      <selectValue />
                    </SelectTrigger>
                    <selectContent aria-label="Select option">
                      <selectItem value="none" aria-label="Select option">None - Full system access</SelectItem>
                      <selectItem value="basic" aria-label="Select option">Basic - Limited access</SelectItem>
                      <selectItem value="strict" aria-label="Select option">Strict - Sandboxed execution</SelectItem>
                      <selectItem value="maximum" aria-label="Select option">Maximum - Minimal privileges</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <Separator />
              <div className="space-y-4">
                <h4 className="font-medium">Trusted Domains</h4>
                <div className="flex gap-2">
                  <input
                    placeholder="Enter domain (e.g., api.example.com)"
                    value={newTrustedDomain}
                    onChange={(e) = aria-label="Input"> setNewTrustedDomain(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && addTrustedDomain()}
                    disabled={readOnly}
                  />
                  <button onClick={addTrustedDomain} disabled={readOnly} aria-label="Button">
                    Add
                  </Button>
                </div>
                {securityPolicy.trustedDomains.length > 0 && (
                  <div className="space-y-2">
                    {securityPolicy.trustedDomains.map((domain, index) => (
                      <div key={index} className="flex items-center justify-between p-2 bg-muted rounded sm:p-4 md:p-6">
                        <div className="flex items-center gap-2">
                          <Globe className="w-4 h-4 sm:w-auto md:w-full" />
                          <span className="font-mono text-sm md:text-base lg:text-lg">{domain}</span>
                        </div>
                        {!readOnly && (
                          <button
                            variant="ghost"
                            size="sm"
                            onClick={() = aria-label="Button"> removeTrustedDomain(domain)}
                          >
                            <XCircle className="w-4 h-4 sm:w-auto md:w-full" />
                          </Button>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="violations" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Security Violations</CardTitle>
              <CardDescription>
                Monitor and review security policy violations
              </CardDescription>
            </CardHeader>
            <CardContent>
              {violations.length === 0 ? (
                <div className="text-center py-8">
                  <CheckCircle className="w-12 h-12 mx-auto mb-4 text-green-600 sm:w-auto md:w-full" />
                  <h3 className="text-lg font-medium mb-2">No Violations</h3>
                  <p className="text-muted-foreground">
                    This plugin has not violated any security policies
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {violations.map(renderViolation)}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        {showAdvanced && (
          <TabsContent value="advanced" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Advanced Security Settings</CardTitle>
                <CardDescription>
                  Configure resource limits and timeouts
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <h4 className="font-medium">Resource Limits</h4>
                    <div className="space-y-2">
                      <Label>Max Memory (MB)</Label>
                      <input
                        type="number"
                        value={securityPolicy.resourceLimits.maxMemory}
                        onChange={(e) = aria-label="Input"> setSecurityPolicy(prev => ({
                          ...prev,
                          resourceLimits: { ...prev.resourceLimits, maxMemory: Number(e.target.value) }
                        }))}
                        disabled={readOnly}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Max CPU (%)</Label>
                      <input
                        type="number"
                        value={securityPolicy.resourceLimits.maxCpu}
                        onChange={(e) = aria-label="Input"> setSecurityPolicy(prev => ({
                          ...prev,
                          resourceLimits: { ...prev.resourceLimits, maxCpu: Number(e.target.value) }
                        }))}
                        disabled={readOnly}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Max Disk (MB)</Label>
                      <input
                        type="number"
                        value={securityPolicy.resourceLimits.maxDisk}
                        onChange={(e) = aria-label="Input"> setSecurityPolicy(prev => ({
                          ...prev,
                          resourceLimits: { ...prev.resourceLimits, maxDisk: Number(e.target.value) }
                        }))}
                        disabled={readOnly}
                      />
                    </div>
                  </div>
                  <div className="space-y-4">
                    <h4 className="font-medium">Timeouts</h4>
                    <div className="space-y-2">
                      <Label>Execution Timeout (seconds)</Label>
                      <input
                        type="number"
                        value={securityPolicy.timeouts.executionTimeout}
                        onChange={(e) = aria-label="Input"> setSecurityPolicy(prev => ({
                          ...prev,
                          timeouts: { ...prev.timeouts, executionTimeout: Number(e.target.value) }
                        }))}
                        disabled={readOnly}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Network Timeout (seconds)</Label>
                      <input
                        type="number"
                        value={securityPolicy.timeouts.networkTimeout}
                        onChange={(e) = aria-label="Input"> setSecurityPolicy(prev => ({
                          ...prev,
                          timeouts: { ...prev.timeouts, networkTimeout: Number(e.target.value) }
                        }))}
                        disabled={readOnly}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>File Operation Timeout (seconds)</Label>
                      <input
                        type="number"
                        value={securityPolicy.timeouts.fileOperationTimeout}
                        onChange={(e) = aria-label="Input"> setSecurityPolicy(prev => ({
                          ...prev,
                          timeouts: { ...prev.timeouts, fileOperationTimeout: Number(e.target.value) }
                        }))}
                        disabled={readOnly}
                      />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        )}
      </Tabs>
    </div>
    </ErrorBoundary>
  );
};
