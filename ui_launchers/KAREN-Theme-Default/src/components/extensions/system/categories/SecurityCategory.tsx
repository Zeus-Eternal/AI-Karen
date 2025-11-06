"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Shield, Lock, Key, AlertTriangle, CheckCircle, Settings } from "lucide-react";

export interface SecurityExtension {
  id: string;
  name: string;
  displayName?: string;
  description: string;
  status: 'active' | 'inactive' | 'error';
  enabled: boolean;
  securityLevel: 'critical' | 'high' | 'medium' | 'low';
  permissions: string[];
  lastAudit?: Date;
  vulnerabilities?: number;
}

export interface SecurityCategoryProps {
  refreshInterval?: number;
  onConfigure?: (id: string) => void;
}

const mockSecurityExtensions: SecurityExtension[] = [
  {
    id: 'auth-jwt',
    name: 'jwt-auth',
    displayName: 'JWT Authentication',
    description: 'JSON Web Token authentication provider for secure API access',
    status: 'active',
    enabled: true,
    securityLevel: 'critical',
    permissions: ['auth.read', 'auth.write', 'tokens.create'],
    lastAudit: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000),
    vulnerabilities: 0,
  },
  {
    id: 'oauth2',
    name: 'oauth2-provider',
    displayName: 'OAuth2 Provider',
    description: 'OAuth2 authorization server for third-party integrations',
    status: 'active',
    enabled: true,
    securityLevel: 'critical',
    permissions: ['auth.read', 'auth.write', 'oauth.manage'],
    lastAudit: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000),
    vulnerabilities: 0,
  },
  {
    id: 'rate-limiter',
    name: 'rate-limiter',
    displayName: 'Rate Limiter',
    description: 'API rate limiting and throttling for DDoS protection',
    status: 'active',
    enabled: true,
    securityLevel: 'high',
    permissions: ['network.control', 'security.monitor'],
    lastAudit: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
    vulnerabilities: 0,
  },
  {
    id: 'encryption',
    name: 'data-encryption',
    displayName: 'Data Encryption',
    description: 'End-to-end encryption for sensitive data storage and transmission',
    status: 'active',
    enabled: true,
    securityLevel: 'critical',
    permissions: ['data.read', 'data.write', 'crypto.use'],
    lastAudit: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000),
    vulnerabilities: 0,
  },
  {
    id: 'audit-logger',
    name: 'audit-logger',
    displayName: 'Audit Logger',
    description: 'Comprehensive audit logging for security compliance',
    status: 'active',
    enabled: true,
    securityLevel: 'high',
    permissions: ['logs.read', 'logs.write', 'audit.access'],
    lastAudit: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000),
    vulnerabilities: 0,
  },
  {
    id: 'firewall',
    name: 'web-firewall',
    displayName: 'Web Application Firewall',
    description: 'WAF protection against common web vulnerabilities',
    status: 'inactive',
    enabled: false,
    securityLevel: 'high',
    permissions: ['network.control', 'security.manage'],
    lastAudit: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000),
    vulnerabilities: 1,
  },
];

const securityLevelConfig = {
  critical: {
    label: 'Critical',
    icon: AlertTriangle,
    color: 'text-red-500',
    bgColor: 'bg-red-500',
  },
  high: {
    label: 'High',
    icon: Shield,
    color: 'text-orange-500',
    bgColor: 'bg-orange-500',
  },
  medium: {
    label: 'Medium',
    icon: Lock,
    color: 'text-yellow-500',
    bgColor: 'bg-yellow-500',
  },
  low: {
    label: 'Low',
    icon: Key,
    color: 'text-blue-500',
    bgColor: 'bg-blue-500',
  },
};

export default function SecurityCategory({
  refreshInterval = 15000,
  onConfigure,
}: SecurityCategoryProps) {
  const [extensions, setExtensions] = useState<SecurityExtension[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const loadExtensions = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/extensions/category/security');
      if (response.ok) {
        const data = await response.json();
        setExtensions(data);
      } else {
        // Fallback to mock data
        setExtensions(mockSecurityExtensions);
      }
    } catch (error) {
      console.error('Failed to load security extensions:', error);
      setExtensions(mockSecurityExtensions);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadExtensions();
    const interval = setInterval(loadExtensions, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const stats = {
    total: extensions.length,
    active: extensions.filter((ext) => ext.status === 'active').length,
    critical: extensions.filter((ext) => ext.securityLevel === 'critical').length,
    vulnerabilities: extensions.reduce((sum, ext) => sum + (ext.vulnerabilities || 0), 0),
  };

  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Extensions</p>
                <p className="text-2xl font-bold">{stats.total}</p>
              </div>
              <Shield className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Active</p>
                <p className="text-2xl font-bold text-green-500">{stats.active}</p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Critical</p>
                <p className="text-2xl font-bold text-red-500">{stats.critical}</p>
              </div>
              <AlertTriangle className="h-8 w-8 text-red-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Vulnerabilities</p>
                <p className="text-2xl font-bold text-orange-500">{stats.vulnerabilities}</p>
              </div>
              <AlertTriangle className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Extensions List */}
      <Card>
        <CardHeader>
          <CardTitle>Security Extensions</CardTitle>
          <CardDescription>
            Manage authentication, authorization, and security-related extensions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[500px]">
            <div className="space-y-4">
              {extensions.map((extension) => {
                const levelConfig = securityLevelConfig[extension.securityLevel];
                const LevelIcon = levelConfig.icon;

                return (
                  <Card key={extension.id}>
                    <CardContent className="pt-6">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <h3 className="font-semibold">
                              {extension.displayName || extension.name}
                            </h3>
                            <Badge
                              variant={extension.status === 'active' ? 'default' : 'secondary'}
                            >
                              {extension.status}
                            </Badge>
                            <div className={`flex items-center gap-1 ${levelConfig.color}`}>
                              <LevelIcon className="h-4 w-4" />
                              <span className="text-xs font-medium">{levelConfig.label}</span>
                            </div>
                          </div>

                          <p className="text-sm text-muted-foreground mb-3">
                            {extension.description}
                          </p>

                          <div className="flex flex-wrap gap-2 text-xs">
                            <div className="flex items-center gap-1">
                              <Key className="h-3 w-3" />
                              <span>{extension.permissions.length} permissions</span>
                            </div>
                            {extension.lastAudit && (
                              <div>
                                Last audit:{' '}
                                {Math.floor(
                                  (Date.now() - extension.lastAudit.getTime()) /
                                    (1000 * 60 * 60 * 24)
                                )}{' '}
                                days ago
                              </div>
                            )}
                            {extension.vulnerabilities !== undefined &&
                              extension.vulnerabilities > 0 && (
                                <Badge variant="destructive" className="text-xs">
                                  {extension.vulnerabilities} vulnerabilities
                                </Badge>
                              )}
                          </div>
                        </div>

                        {onConfigure && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => onConfigure(extension.id)}
                          >
                            <Settings className="h-4 w-4 mr-1" />
                            Configure
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}

export { SecurityCategory };
export type { SecurityCategoryProps, SecurityExtension };
