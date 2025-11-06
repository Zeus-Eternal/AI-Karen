"use client";

/**
 * Extension Permissions Manager
 *
 * View and manage extension permissions, security policies, and access controls
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Shield,
  Lock,
  Unlock,
  AlertTriangle,
  CheckCircle,
  XCircle,
  RefreshCw,
  Settings,
  FileText,
  Database,
  Globe,
  HardDrive,
  Eye,
  Key,
  UserCheck
} from 'lucide-react';

export interface Permission {
  id: string;
  name: string;
  description: string;
  category: 'file-system' | 'network' | 'database' | 'user-data' | 'system';
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  granted: boolean;
  required: boolean;
}

export interface ExtensionPermissionInfo {
  extensionId: string;
  extensionName: string;
  version: string;
  permissions: Permission[];
  securityScore: number;
  lastAudit: string;
  violations: number;
}

export interface PermissionAuditLog {
  id: string;
  extensionId: string;
  extensionName: string;
  permission: string;
  action: 'granted' | 'revoked' | 'used' | 'denied';
  timestamp: string;
  reason?: string;
}

export interface ExtensionPermissionsProps {
  extensionId?: string;
  refreshInterval?: number;
}

export default function ExtensionPermissions({
  extensionId,
  refreshInterval = 10000
}: ExtensionPermissionsProps) {
  const [extensions, setExtensions] = useState<ExtensionPermissionInfo[]>([]);
  const [auditLogs, setAuditLogs] = useState<PermissionAuditLog[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('permissions');
  const [selectedExtension, setSelectedExtension] = useState<string | null>(extensionId || null);

  const loadPermissionsData = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/extensions/permissions');
      if (response.ok) {
        const data = await response.json();
        setExtensions(data.extensions);
        setAuditLogs(data.auditLogs);
      } else {
        // Fallback mock data
        const mockExtensions: ExtensionPermissionInfo[] = [
          {
            extensionId: 'ext-1',
            extensionName: 'Database Connector',
            version: '2.1.0',
            securityScore: 85,
            lastAudit: new Date(Date.now() - 3600000).toISOString(),
            violations: 0,
            permissions: [
              {
                id: 'perm-1',
                name: 'Read Database',
                description: 'Access to read data from application databases',
                category: 'database',
                riskLevel: 'medium',
                granted: true,
                required: true
              },
              {
                id: 'perm-2',
                name: 'Write Database',
                description: 'Access to modify data in application databases',
                category: 'database',
                riskLevel: 'high',
                granted: true,
                required: true
              },
              {
                id: 'perm-3',
                name: 'Network Access',
                description: 'Make outbound network requests',
                category: 'network',
                riskLevel: 'medium',
                granted: true,
                required: false
              }
            ]
          },
          {
            extensionId: 'ext-2',
            extensionName: 'File Backup Agent',
            version: '1.5.2',
            securityScore: 72,
            lastAudit: new Date(Date.now() - 7200000).toISOString(),
            violations: 2,
            permissions: [
              {
                id: 'perm-4',
                name: 'Read File System',
                description: 'Read files from local file system',
                category: 'file-system',
                riskLevel: 'high',
                granted: true,
                required: true
              },
              {
                id: 'perm-5',
                name: 'Write File System',
                description: 'Create and modify files on local file system',
                category: 'file-system',
                riskLevel: 'critical',
                granted: true,
                required: true
              },
              {
                id: 'perm-6',
                name: 'Delete Files',
                description: 'Delete files from local file system',
                category: 'file-system',
                riskLevel: 'critical',
                granted: false,
                required: false
              },
              {
                id: 'perm-7',
                name: 'Cloud Upload',
                description: 'Upload data to cloud services',
                category: 'network',
                riskLevel: 'high',
                granted: true,
                required: true
              }
            ]
          },
          {
            extensionId: 'ext-3',
            extensionName: 'Analytics Dashboard',
            version: '3.0.1',
            securityScore: 95,
            lastAudit: new Date(Date.now() - 1800000).toISOString(),
            violations: 0,
            permissions: [
              {
                id: 'perm-8',
                name: 'Read User Data',
                description: 'Access user profile and usage data',
                category: 'user-data',
                riskLevel: 'medium',
                granted: true,
                required: true
              },
              {
                id: 'perm-9',
                name: 'View Analytics',
                description: 'Access application analytics and metrics',
                category: 'system',
                riskLevel: 'low',
                granted: true,
                required: true
              }
            ]
          }
        ];

        const mockAuditLogs: PermissionAuditLog[] = [
          {
            id: 'log-1',
            extensionId: 'ext-1',
            extensionName: 'Database Connector',
            permission: 'Read Database',
            action: 'used',
            timestamp: new Date(Date.now() - 600000).toISOString()
          },
          {
            id: 'log-2',
            extensionId: 'ext-2',
            extensionName: 'File Backup Agent',
            permission: 'Delete Files',
            action: 'denied',
            timestamp: new Date(Date.now() - 1200000).toISOString(),
            reason: 'Permission not granted'
          },
          {
            id: 'log-3',
            extensionId: 'ext-2',
            extensionName: 'File Backup Agent',
            permission: 'Cloud Upload',
            action: 'used',
            timestamp: new Date(Date.now() - 1800000).toISOString()
          },
          {
            id: 'log-4',
            extensionId: 'ext-3',
            extensionName: 'Analytics Dashboard',
            permission: 'Read User Data',
            action: 'granted',
            timestamp: new Date(Date.now() - 3600000).toISOString()
          }
        ];

        setExtensions(mockExtensions);
        setAuditLogs(mockAuditLogs);
        if (!selectedExtension && mockExtensions.length > 0) {
          setSelectedExtension(mockExtensions[0].extensionId);
        }
      }
    } catch (error) {
      console.error('Failed to load permissions data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadPermissionsData();
    const interval = setInterval(loadPermissionsData, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const togglePermission = (extensionId: string, permissionId: string, granted: boolean) => {
    setExtensions(prev =>
      prev.map(ext =>
        ext.extensionId === extensionId
          ? {
              ...ext,
              permissions: ext.permissions.map(perm =>
                perm.id === permissionId ? { ...perm, granted } : perm
              )
            }
          : ext
      )
    );

    const log: PermissionAuditLog = {
      id: `log-${Date.now()}`,
      extensionId,
      extensionName: extensions.find(e => e.extensionId === extensionId)?.extensionName || '',
      permission: extensions
        .find(e => e.extensionId === extensionId)
        ?.permissions.find(p => p.id === permissionId)?.name || '',
      action: granted ? 'granted' : 'revoked',
      timestamp: new Date().toISOString()
    };
    setAuditLogs(prev => [log, ...prev]);
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'low':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'file-system':
        return <HardDrive className="h-4 w-4" />;
      case 'network':
        return <Globe className="h-4 w-4" />;
      case 'database':
        return <Database className="h-4 w-4" />;
      case 'user-data':
        return <UserCheck className="h-4 w-4" />;
      case 'system':
        return <Settings className="h-4 w-4" />;
      default:
        return <Key className="h-4 w-4" />;
    }
  };

  const getActionIcon = (action: string) => {
    switch (action) {
      case 'granted':
        return <Unlock className="h-4 w-4 text-green-600" />;
      case 'revoked':
        return <Lock className="h-4 w-4 text-red-600" />;
      case 'used':
        return <Eye className="h-4 w-4 text-blue-600" />;
      case 'denied':
        return <XCircle className="h-4 w-4 text-orange-600" />;
      default:
        return <Shield className="h-4 w-4" />;
    }
  };

  const currentExtension = extensions.find(e => e.extensionId === selectedExtension);
  const filteredLogs = selectedExtension
    ? auditLogs.filter(log => log.extensionId === selectedExtension)
    : auditLogs;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Extension Permissions
            </div>
            <Button onClick={loadPermissionsData} disabled={isLoading} size="sm">
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </CardTitle>
          <CardDescription>
            Manage extension permissions and security policies
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Extension Selector */}
          <div className="mb-6">
            <label className="text-sm font-medium mb-2 block">Select Extension</label>
            <div className="grid md:grid-cols-3 gap-3">
              {extensions.map((ext) => (
                <Card
                  key={ext.extensionId}
                  className={`cursor-pointer transition-all ${
                    selectedExtension === ext.extensionId
                      ? 'ring-2 ring-blue-500 bg-blue-50'
                      : 'hover:bg-gray-50'
                  }`}
                  onClick={() => setSelectedExtension(ext.extensionId)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium text-sm">{ext.extensionName}</h4>
                        <p className="text-xs text-muted-foreground">v{ext.version}</p>
                      </div>
                      {ext.violations > 0 && (
                        <AlertTriangle className="h-4 w-4 text-orange-600" />
                      )}
                    </div>
                    <div className="mt-3 flex items-center justify-between">
                      <div className="flex items-center gap-1">
                        <Shield className="h-3 w-3" />
                        <span className="text-xs font-medium">{ext.securityScore}%</span>
                      </div>
                      <Badge variant="outline" className="text-xs">
                        {ext.permissions.filter(p => p.granted).length}/{ext.permissions.length}
                      </Badge>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          {currentExtension && (
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="permissions">
                  <Key className="h-4 w-4 mr-2" />
                  Permissions
                </TabsTrigger>
                <TabsTrigger value="audit">
                  <FileText className="h-4 w-4 mr-2" />
                  Audit Log
                </TabsTrigger>
              </TabsList>

              {/* Permissions Tab */}
              <TabsContent value="permissions" className="space-y-4">
                <div className="grid md:grid-cols-3 gap-4 mb-4">
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm text-muted-foreground">Security Score</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{currentExtension.securityScore}%</div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm text-muted-foreground">Active Permissions</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">
                        {currentExtension.permissions.filter(p => p.granted).length}/
                        {currentExtension.permissions.length}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm text-muted-foreground">Violations</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold text-orange-600">
                        {currentExtension.violations}
                      </div>
                    </CardContent>
                  </Card>
                </div>

                <ScrollArea className="h-[500px]">
                  <div className="space-y-3 pr-4">
                    {currentExtension.permissions.map((permission) => (
                      <Card key={permission.id}>
                        <CardContent className="p-4">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-2">
                                {getCategoryIcon(permission.category)}
                                <h4 className="font-medium">{permission.name}</h4>
                                {permission.required && (
                                  <Badge variant="outline" className="text-xs">Required</Badge>
                                )}
                              </div>
                              <p className="text-sm text-muted-foreground mb-3">
                                {permission.description}
                              </p>
                              <div className="flex items-center gap-2">
                                <Badge className={getRiskColor(permission.riskLevel)}>
                                  {permission.riskLevel} risk
                                </Badge>
                                <Badge variant="outline" className="capitalize">
                                  {permission.category.replace('-', ' ')}
                                </Badge>
                              </div>
                            </div>
                            <Switch
                              checked={permission.granted}
                              onCheckedChange={(granted) =>
                                togglePermission(currentExtension.extensionId, permission.id, granted)
                              }
                              disabled={permission.required}
                            />
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </ScrollArea>
              </TabsContent>

              {/* Audit Log Tab */}
              <TabsContent value="audit" className="space-y-4">
                <ScrollArea className="h-[600px]">
                  <div className="space-y-3 pr-4">
                    {filteredLogs.map((log) => (
                      <Card key={log.id}>
                        <CardContent className="p-4">
                          <div className="flex items-start justify-between">
                            <div className="flex items-start gap-3 flex-1">
                              {getActionIcon(log.action)}
                              <div>
                                <div className="flex items-center gap-2 mb-1">
                                  <span className="font-medium text-sm">{log.permission}</span>
                                  <Badge variant="outline" className="text-xs capitalize">
                                    {log.action}
                                  </Badge>
                                </div>
                                <p className="text-sm text-muted-foreground">
                                  {log.extensionName}
                                </p>
                                {log.reason && (
                                  <p className="text-xs text-orange-600 mt-1">{log.reason}</p>
                                )}
                              </div>
                            </div>
                            <span className="text-xs text-muted-foreground">
                              {new Date(log.timestamp).toLocaleString()}
                            </span>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </ScrollArea>
              </TabsContent>
            </Tabs>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export { ExtensionPermissions };
export type { ExtensionPermissionsProps, Permission, ExtensionPermissionInfo, PermissionAuditLog };
