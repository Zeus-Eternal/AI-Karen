'use client';

/**
 * Super Admin Dashboard Component
 * 
 * This component provides the main interface for super admin users,
 * including navigation and layout for all administrative functions.
 */

import React, { useState } from 'react';
import { useRole } from '@/hooks/useRole';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { LayoutContainer, LayoutHeader, LayoutSection } from '@/components/layout/ModernLayout';
import AdminManagementInterface from './AdminManagementInterface';
import SystemConfigurationPanel from './SystemConfigurationPanel';
import SecuritySettingsPanel from './SecuritySettingsPanel';
import AuditLogViewer from './audit/AuditLogViewer';
import { 
  Users, 
  Settings, 
  Shield, 
  FileText, 
  UserCheck, 
  AlertTriangle,
  Activity,
  Database
} from 'lucide-react';

interface DashboardStats {
  totalUsers: number;
  totalAdmins: number;
  activeUsers: number;
  securityAlerts: number;
  systemHealth: 'healthy' | 'warning' | 'critical';
}

export default function SuperAdminDashboard() {
  const { user } = useAuth();
  const { hasRole } = useRole();
  const [activeTab, setActiveTab] = useState('overview');
  const [stats, setStats] = useState<DashboardStats>({
    totalUsers: 0,
    totalAdmins: 0,
    activeUsers: 0,
    securityAlerts: 0,
    systemHealth: 'healthy'
  });

  // Load dashboard stats
  React.useEffect(() => {
    const loadStats = async () => {
      try {
        const response = await fetch('/api/admin/dashboard/stats');
        if (response.ok) {
          const data = await response.json();
          setStats(data);
        }
      } catch (error) {
        console.error('Failed to load dashboard stats:', error);
      }
    };

    loadStats();
  }, []);

  if (!hasRole('super_admin')) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="text-center text-red-600">Access Denied</CardTitle>
            <CardDescription className="text-center">
              You don't have permission to access the super admin dashboard.
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  const getHealthBadgeVariant = (health: string) => {
    switch (health) {
      case 'healthy': return 'default';
      case 'warning': return 'secondary';
      case 'critical': return 'destructive';
      default: return 'default';
    }
  };

  return (
    <LayoutContainer size="full" className="py-6">
      <LayoutHeader
        title="Super Admin Dashboard"
        description="Manage administrators, system configuration, and security settings"
        actions={
          <div className="flex items-center gap-2">
            <Badge variant={getHealthBadgeVariant(stats.systemHealth)}>
              System {stats.systemHealth}
            </Badge>
            <span className="text-sm text-muted-foreground">
              Welcome, {user?.email}
            </span>
          </div>
        }
      />

      <LayoutSection className="mt-6">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="overview" className="flex items-center gap-2">
              <Activity className="h-4 w-4" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="admins" className="flex items-center gap-2">
              <UserCheck className="h-4 w-4" />
              Admin Management
            </TabsTrigger>
            <TabsTrigger value="system" className="flex items-center gap-2">
              <Settings className="h-4 w-4" />
              System Config
            </TabsTrigger>
            <TabsTrigger value="security" className="flex items-center gap-2">
              <Shield className="h-4 w-4" />
              Security
            </TabsTrigger>
            <TabsTrigger value="audit" className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Audit Logs
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="mt-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Users</CardTitle>
                  <Users className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats.totalUsers}</div>
                  <p className="text-xs text-muted-foreground">
                    Registered users in the system
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Administrators</CardTitle>
                  <UserCheck className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats.totalAdmins}</div>
                  <p className="text-xs text-muted-foreground">
                    Active admin accounts
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Active Sessions</CardTitle>
                  <Activity className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats.activeUsers}</div>
                  <p className="text-xs text-muted-foreground">
                    Currently logged in users
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Security Alerts</CardTitle>
                  <AlertTriangle className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-red-600">{stats.securityAlerts}</div>
                  <p className="text-xs text-muted-foreground">
                    Requires attention
                  </p>
                </CardContent>
              </Card>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Quick Actions</CardTitle>
                  <CardDescription>
                    Common administrative tasks
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Button 
                    variant="outline" 
                    className="w-full justify-start"
                    onClick={() => setActiveTab('admins')}
                  >
                    <UserCheck className="mr-2 h-4 w-4" />
                    Create New Administrator
                  </Button>
                  <Button 
                    variant="outline" 
                    className="w-full justify-start"
                    onClick={() => setActiveTab('system')}
                  >
                    <Settings className="mr-2 h-4 w-4" />
                    Update System Configuration
                  </Button>
                  <Button 
                    variant="outline" 
                    className="w-full justify-start"
                    onClick={() => setActiveTab('security')}
                  >
                    <Shield className="mr-2 h-4 w-4" />
                    Review Security Settings
                  </Button>
                  <Button 
                    variant="outline" 
                    className="w-full justify-start"
                    onClick={() => setActiveTab('audit')}
                  >
                    <FileText className="mr-2 h-4 w-4" />
                    View Recent Activity
                  </Button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>System Status</CardTitle>
                  <CardDescription>
                    Current system health and performance
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Database</span>
                    <Badge variant="default">
                      <Database className="mr-1 h-3 w-3" />
                      Connected
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Authentication</span>
                    <Badge variant="default">
                      <Shield className="mr-1 h-3 w-3" />
                      Active
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Audit Logging</span>
                    <Badge variant="default">
                      <FileText className="mr-1 h-3 w-3" />
                      Recording
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Security Monitoring</span>
                    <Badge variant={stats.securityAlerts > 0 ? "destructive" : "default"}>
                      <AlertTriangle className="mr-1 h-3 w-3" />
                      {stats.securityAlerts > 0 ? `${stats.securityAlerts} Alerts` : 'Normal'}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="admins" className="mt-6">
            <AdminManagementInterface />
          </TabsContent>

          <TabsContent value="system" className="mt-6">
            <SystemConfigurationPanel />
          </TabsContent>

          <TabsContent value="security" className="mt-6">
            <SecuritySettingsPanel />
          </TabsContent>

          <TabsContent value="audit" className="mt-6">
            <AuditLogViewer 
              showExportButton={true}
              showFilters={true}
              className="border-0 shadow-none"
            />
          </TabsContent>
        </Tabs>
      </LayoutSection>
    </LayoutContainer>
  );
}