"use client";
import { useAuth } from '@/contexts/AuthContext';
import { HealthDashboard } from '../monitoring/health-dashboard';
import UsageAnalyticsCharts from '../analytics/UsageAnalyticsCharts';
import AuditLogTable from '../analytics/AuditLogTable';
import { GridContainer } from '@/components/ui/layout/grid-container';
import { FlexContainer } from '@/components/ui/layout/flex-container';
import { Card } from '@/components/ui/compound/card';
import { TextSelectionDemo } from '@/components/ui/text-selection-demo';

export default function Dashboard() {
  const { user } = useAuth();
  if (!user) return null;
  const isAdmin = user.roles?.includes('admin') || user.roles?.includes('super_admin');
  
  return (
    <FlexContainer direction="column" className="space-y-fluid">
      <div className="modern-card-header">
        <h2 className="text-2xl font-semibold tracking-tight">
          {isAdmin ? 'Admin Dashboard' : 'My Dashboard'}
        </h2>
        {!isAdmin && (
          <p className="text-sm text-muted-foreground mt-2">
            Welcome, {user.email ?? 'User'}
          </p>
        )}
      </div>
      
      <GridContainer 
        columns="repeat(auto-fit, minmax(300px, 1fr))" 
        gap="var(--space-lg)"
        className="dashboard-grid"
      >
        {isAdmin && (
          <Card.Root className="modern-card">
            <Card.Header>
              <Card.Title>System Health</Card.Title>
            </Card.Header>
            <Card.Content>
              <HealthDashboard />
            </Card.Content>
          </Card.Root>
        )}
        
        <Card.Root className="modern-card">
          <Card.Header>
            <Card.Title>Usage Analytics</Card.Title>
          </Card.Header>
          <Card.Content>
            <UsageAnalyticsCharts />
          </Card.Content>
        </Card.Root>
        
        {isAdmin && (
          <Card.Root className="modern-card col-span-full">
            <Card.Header>
              <Card.Title>Audit Logs</Card.Title>
            </Card.Header>
            <Card.Content>
              <AuditLogTable />
            </Card.Content>
          </Card.Root>
        )}
        
        <Card.Root className="modern-card col-span-full">
          <Card.Header>
            <Card.Title>Text Selection Test</Card.Title>
          </Card.Header>
          <Card.Content>
            <TextSelectionDemo />
          </Card.Content>
        </Card.Root>
      </GridContainer>
    </FlexContainer>
  );
}
