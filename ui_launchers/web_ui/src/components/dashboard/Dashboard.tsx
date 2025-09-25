"use client";
import { useAuth } from '@/contexts/AuthContext';
import { HealthDashboard } from '../monitoring/health-dashboard';
import UsageAnalyticsCharts from '../analytics/UsageAnalyticsCharts';
import AuditLogTable from '../analytics/AuditLogTable';
import { LayoutGrid, LayoutHeader, LayoutSection } from '../layout/ModernLayout';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

export default function Dashboard() {
  const { user } = useAuth();
  if (!user) return null;
  const isAdmin = user.roles?.includes('admin') || user.roles?.includes('super_admin');
  
  return (
    <div className="space-y-fluid">
      <LayoutHeader
        title={isAdmin ? 'Admin Dashboard' : 'My Dashboard'}
        description={!isAdmin ? `Welcome, ${user.email ?? 'User'}` : undefined}
      />
      
      <LayoutGrid columns="auto-fit" gap="lg" responsive>
        {isAdmin && (
          <Card>
            <CardHeader>
              <CardTitle>System Health</CardTitle>
            </CardHeader>
            <CardContent>
              <HealthDashboard />
            </CardContent>
          </Card>
        )}
        
        <Card>
          <CardHeader>
            <CardTitle>Usage Analytics</CardTitle>
          </CardHeader>
          <CardContent>
            <UsageAnalyticsCharts />
          </CardContent>
        </Card>
        
        {isAdmin && (
          <Card className="col-span-full">
            <CardHeader>
              <CardTitle>Audit Logs</CardTitle>
            </CardHeader>
            <CardContent>
              <AuditLogTable />
            </CardContent>
          </Card>
        )}
      </LayoutGrid>
    </div>
  );
}
