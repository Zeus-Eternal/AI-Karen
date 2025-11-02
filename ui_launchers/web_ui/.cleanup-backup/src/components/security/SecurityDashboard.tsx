'use client';

import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { format, subDays, startOfDay, endOfDay } from 'date-fns';
import { enhancedApiClient } from '@/lib/enhanced-api-client';
import { PermissionGate } from '@/components/rbac';
import { EvilModeToggle } from './EvilModeToggle';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { 
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

import { 
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  Area,
  AreaChart,
  PieChart,
  Pie,
  Cell
} from 'recharts';

import { 
  Shield, 
  AlertTriangle, 
  TrendingUp, 
  TrendingDown,
  Activity,
  Eye,
  Lock,
  Unlock,
  Target,
  Zap,
  Clock,
  Users,
  Server,
  Database,
  Network,
  FileText,
  CheckCircle,
  XCircle,
  RefreshCw
} from 'lucide-react';

interface SecurityDashboardProps {
  className?: string;
}

interface SecurityMetrics {
  overallSecurityScore: number;
  threatLevel: 'low' | 'medium' | 'high' | 'critical';
  activeThreats: number;
  resolvedThreats: number;
  vulnerabilities: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  complianceScore: number;
  incidentResponse: {
    averageResponseTime: number;
    resolvedIncidents: number;
    openIncidents: number;
  };
  systemHealth: {
    authentication: 'healthy' | 'warning' | 'critical';
    authorization: 'healthy' | 'warning' | 'critical';
    dataProtection: 'healthy' | 'warning' | 'critical';
    networkSecurity: 'healthy' | 'warning' | 'critical';
  };
}

interface SecurityAlert {
  id: string;
  type: 'threat' | 'vulnerability' | 'policy_violation' | 'anomaly';
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  timestamp: Date;
  status: 'open' | 'investigating' | 'resolved' | 'false_positive';
  affectedSystems: string[];
  recommendedActions: string[];
  assignedTo?: string;
}

interface ThreatIntelligence {
  id: string;
  source: string;
  threatType: string;
  confidence: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  indicators: string[];
  description: string;
  mitigation: string[];
  lastUpdated: Date;
}

export function SecurityDashboard({ className }: SecurityDashboardProps) {
  const [timeframe, setTimeframe] = useState<'24h' | '7d' | '30d'>('24h');
  const [selectedAlert, setSelectedAlert] = useState<SecurityAlert | null>(null);

  const timeframeOptions = {
    '24h': { hours: 24, label: 'Last 24 hours' },
    '7d': { days: 7, label: 'Last 7 days' },
    '30d': { days: 30, label: 'Last 30 days' }
  };

  const { data: metrics, isLoading: metricsLoading } = useQuery({
    queryKey: ['security', 'metrics', timeframe],
    queryFn: () => getSecurityMetrics(timeframe),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const { data: alerts } = useQuery({
    queryKey: ['security', 'alerts'],
    queryFn: () => getSecurityAlerts(),
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  const { data: threats } = useQuery({
    queryKey: ['security', 'threat-intelligence'],
    queryFn: () => getThreatIntelligence(),
    refetchInterval: 60000, // Refresh every minute
  });

  return (
    <PermissionGate permission="security:view">
      <div className={className}>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold flex items-center space-x-2">
              <Shield className="h-6 w-6 text-blue-600" />
              <span>Security Dashboard</span>
            </h2>
            <p className="text-muted-foreground">
              Monitor security metrics, threats, and compliance status
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <Select value={timeframe} onValueChange={(value: '24h' | '7d' | '30d') => setTimeframe(value)}>
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(timeframeOptions).map(([key, { label }]) => (
                  <SelectItem key={key} value={key}>{label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button variant="outline" size="sm">
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {metricsLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        ) : (
          <Tabs defaultValue="overview" className="space-y-4">
            <TabsList>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="threats">Threats</TabsTrigger>
              <TabsTrigger value="vulnerabilities">Vulnerabilities</TabsTrigger>
              <TabsTrigger value="compliance">Compliance</TabsTrigger>
              <TabsTrigger value="incidents">Incidents</TabsTrigger>
              <TabsTrigger value="evil-mode">Evil Mode</TabsTrigger>
            </TabsList>

            <TabsContent value="overview">
              <SecurityOverview metrics={metrics} alerts={alerts} />
            </TabsContent>

            <TabsContent value="threats">
              <ThreatMonitoring alerts={alerts} threats={threats} />
            </TabsContent>

            <TabsContent value="vulnerabilities">
              <VulnerabilityManagement metrics={metrics} />
            </TabsContent>

            <TabsContent value="compliance">
              <ComplianceMonitoring metrics={metrics} />
            </TabsContent>

            <TabsContent value="incidents">
              <IncidentResponse metrics={metrics} alerts={alerts} />
            </TabsContent>

            <TabsContent value="evil-mode">
              <EvilModeManagement />
            </TabsContent>
          </Tabs>
        )}
      </div>
    </PermissionGate>
  );
}

interface SecurityOverviewProps {
  metrics: SecurityMetrics | undefined;
  alerts: SecurityAlert[] | undefined;
}

function SecurityOverview({ metrics, alerts }: SecurityOverviewProps) {
  if (!metrics) return <div>Loading...</div>;

  const getThreatLevelColor = (level: string) => {
    switch (level) {
      case 'critical': return 'text-red-600';
      case 'high': return 'text-orange-600';
      case 'medium': return 'text-yellow-600';
      default: return 'text-green-600';
    }
  };

  const getHealthIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'warning': return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'critical': return <XCircle className="h-4 w-4 text-red-500" />;
      default: return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  const recentAlerts = alerts?.slice(0, 5) || [];

  return (
    <div className="space-y-6">
      {/* Security Score and Threat Level */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Security Score</CardTitle>
            <Shield className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.overallSecurityScore}%</div>
            <Progress value={metrics.overallSecurityScore} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-1">
              {metrics.overallSecurityScore >= 90 ? 'Excellent' :
               metrics.overallSecurityScore >= 80 ? 'Good' :
               metrics.overallSecurityScore >= 70 ? 'Fair' : 'Needs Attention'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Threat Level</CardTitle>
            <AlertTriangle className={`h-4 w-4 ${getThreatLevelColor(metrics.threatLevel)}`} />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold capitalize ${getThreatLevelColor(metrics.threatLevel)}`}>
              {metrics.threatLevel}
            </div>
            <div className="flex items-center text-xs text-muted-foreground mt-1">
              <TrendingDown className="h-3 w-3 mr-1 text-green-500" />
              Decreased from yesterday
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Threats</CardTitle>
            <Target className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{metrics.activeThreats}</div>
            <div className="flex items-center text-xs text-muted-foreground mt-1">
              <span>{metrics.resolvedThreats} resolved today</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Compliance</CardTitle>
            <FileText className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.complianceScore}%</div>
            <Progress value={metrics.complianceScore} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-1">
              Meeting regulatory requirements
            </p>
          </CardContent>
        </Card>
      </div>

      {/* System Health */}
      <Card>
        <CardHeader>
          <CardTitle>System Health</CardTitle>
          <CardDescription>
            Real-time status of critical security components
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div className="flex items-center justify-between p-3 border rounded-lg">
              <div className="flex items-center space-x-2">
                <Lock className="h-4 w-4" />
                <span className="font-medium">Authentication</span>
              </div>
              <div className="flex items-center space-x-2">
                {getHealthIcon(metrics.systemHealth.authentication)}
                <Badge variant={
                  metrics.systemHealth.authentication === 'healthy' ? 'default' :
                  metrics.systemHealth.authentication === 'warning' ? 'secondary' : 'destructive'
                }>
                  {metrics.systemHealth.authentication}
                </Badge>
              </div>
            </div>

            <div className="flex items-center justify-between p-3 border rounded-lg">
              <div className="flex items-center space-x-2">
                <Shield className="h-4 w-4" />
                <span className="font-medium">Authorization</span>
              </div>
              <div className="flex items-center space-x-2">
                {getHealthIcon(metrics.systemHealth.authorization)}
                <Badge variant={
                  metrics.systemHealth.authorization === 'healthy' ? 'default' :
                  metrics.systemHealth.authorization === 'warning' ? 'secondary' : 'destructive'
                }>
                  {metrics.systemHealth.authorization}
                </Badge>
              </div>
            </div>

            <div className="flex items-center justify-between p-3 border rounded-lg">
              <div className="flex items-center space-x-2">
                <Database className="h-4 w-4" />
                <span className="font-medium">Data Protection</span>
              </div>
              <div className="flex items-center space-x-2">
                {getHealthIcon(metrics.systemHealth.dataProtection)}
                <Badge variant={
                  metrics.systemHealth.dataProtection === 'healthy' ? 'default' :
                  metrics.systemHealth.dataProtection === 'warning' ? 'secondary' : 'destructive'
                }>
                  {metrics.systemHealth.dataProtection}
                </Badge>
              </div>
            </div>

            <div className="flex items-center justify-between p-3 border rounded-lg">
              <div className="flex items-center space-x-2">
                <Network className="h-4 w-4" />
                <span className="font-medium">Network Security</span>
              </div>
              <div className="flex items-center space-x-2">
                {getHealthIcon(metrics.systemHealth.networkSecurity)}
                <Badge variant={
                  metrics.systemHealth.networkSecurity === 'healthy' ? 'default' :
                  metrics.systemHealth.networkSecurity === 'warning' ? 'secondary' : 'destructive'
                }>
                  {metrics.systemHealth.networkSecurity}
                </Badge>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Recent Alerts */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Security Alerts</CardTitle>
          <CardDescription>
            Latest security events requiring attention
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {recentAlerts.map((alert) => (
              <div key={alert.id} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className={`p-1 rounded-full ${
                    alert.severity === 'critical' ? 'bg-red-100 dark:bg-red-900/30' :
                    alert.severity === 'high' ? 'bg-orange-100 dark:bg-orange-900/30' :
                    alert.severity === 'medium' ? 'bg-yellow-100 dark:bg-yellow-900/30' :
                    'bg-blue-100 dark:bg-blue-900/30'
                  }`}>
                    <AlertTriangle className={`h-3 w-3 ${
                      alert.severity === 'critical' ? 'text-red-600' :
                      alert.severity === 'high' ? 'text-orange-600' :
                      alert.severity === 'medium' ? 'text-yellow-600' :
                      'text-blue-600'
                    }`} />
                  </div>
                  <div>
                    <p className="font-medium">{alert.title}</p>
                    <p className="text-sm text-muted-foreground">
                      {format(new Date(alert.timestamp), 'MMM dd, HH:mm')} • {alert.affectedSystems.join(', ')}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge variant={
                    alert.severity === 'critical' ? 'destructive' :
                    alert.severity === 'high' ? 'default' : 'secondary'
                  }>
                    {alert.severity}
                  </Badge>
                  <Badge variant={
                    alert.status === 'resolved' ? 'default' :
                    alert.status === 'investigating' ? 'secondary' : 'outline'
                  }>
                    {alert.status}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

interface ThreatMonitoringProps {
  alerts: SecurityAlert[] | undefined;
  threats: ThreatIntelligence[] | undefined;
}

function ThreatMonitoring({ alerts, threats }: ThreatMonitoringProps) {
  const threatAlerts = alerts?.filter(alert => alert.type === 'threat') || [];
  const activeThreatIntel = threats?.filter(threat => threat.confidence > 70) || [];

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Active Threats</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{threatAlerts.length}</div>
            <p className="text-xs text-muted-foreground">Requiring immediate attention</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Threat Intelligence</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeThreatIntel.length}</div>
            <p className="text-xs text-muted-foreground">High confidence indicators</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Response Time</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">12m</div>
            <p className="text-xs text-muted-foreground">Average detection to response</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Active Threat Alerts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {threatAlerts.slice(0, 5).map((alert) => (
                <Alert key={alert.id} variant={alert.severity === 'critical' ? 'destructive' : 'default'}>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    <div className="flex items-center justify-between">
                      <div>
                        <strong>{alert.title}</strong>
                        <p className="text-sm">{alert.description}</p>
                        <p className="text-xs text-muted-foreground">
                          {format(new Date(alert.timestamp), 'MMM dd, HH:mm')}
                        </p>
                      </div>
                      <Badge variant={alert.severity === 'critical' ? 'destructive' : 'default'}>
                        {alert.severity}
                      </Badge>
                    </div>
                  </AlertDescription>
                </Alert>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Threat Intelligence Feed</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {activeThreatIntel.slice(0, 5).map((threat) => (
                <div key={threat.id} className="p-3 border rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium">{threat.threatType}</span>
                    <div className="flex items-center space-x-2">
                      <Badge variant="outline">{threat.confidence}% confidence</Badge>
                      <Badge variant={threat.severity === 'critical' ? 'destructive' : 'default'}>
                        {threat.severity}
                      </Badge>
                    </div>
                  </div>
                  <p className="text-sm text-muted-foreground mb-2">{threat.description}</p>
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>Source: {threat.source}</span>
                    <span>{format(new Date(threat.lastUpdated), 'MMM dd, HH:mm')}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

interface VulnerabilityManagementProps {
  metrics: SecurityMetrics | undefined;
}

function VulnerabilityManagement({ metrics }: VulnerabilityManagementProps) {
  if (!metrics) return <div>Loading...</div>;

  const vulnerabilityData = [
    { name: 'Critical', value: metrics.vulnerabilities.critical, color: '#ef4444' },
    { name: 'High', value: metrics.vulnerabilities.high, color: '#f97316' },
    { name: 'Medium', value: metrics.vulnerabilities.medium, color: '#eab308' },
    { name: 'Low', value: metrics.vulnerabilities.low, color: '#22c55e' }
  ];

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Vulnerability Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={vulnerabilityData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: ${value}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {vulnerabilityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Vulnerability Trends</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={[
                { date: '2024-01-01', critical: 5, high: 12, medium: 25, low: 45 },
                { date: '2024-01-02', critical: 3, high: 10, medium: 22, low: 40 },
                { date: '2024-01-03', critical: 2, high: 8, medium: 20, low: 38 },
                { date: '2024-01-04', critical: 1, high: 6, medium: 18, low: 35 },
                { date: '2024-01-05', critical: 1, high: 5, medium: 15, low: 32 }
              ]}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="critical" stroke="#ef4444" strokeWidth={2} />
                <Line type="monotone" dataKey="high" stroke="#f97316" strokeWidth={2} />
                <Line type="monotone" dataKey="medium" stroke="#eab308" strokeWidth={2} />
                <Line type="monotone" dataKey="low" stroke="#22c55e" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Critical Vulnerabilities</CardTitle>
          <CardDescription>
            High-priority vulnerabilities requiring immediate attention
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>CVE ID</TableHead>
                <TableHead>Severity</TableHead>
                <TableHead>Affected System</TableHead>
                <TableHead>CVSS Score</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Due Date</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow>
                <TableCell className="font-mono">CVE-2024-0001</TableCell>
                <TableCell>
                  <Badge variant="destructive">Critical</Badge>
                </TableCell>
                <TableCell>Web Server</TableCell>
                <TableCell>9.8</TableCell>
                <TableCell>
                  <Badge variant="secondary">Patching</Badge>
                </TableCell>
                <TableCell>Jan 15, 2024</TableCell>
              </TableRow>
              <TableRow>
                <TableCell className="font-mono">CVE-2024-0002</TableCell>
                <TableCell>
                  <Badge variant="default">High</Badge>
                </TableCell>
                <TableCell>Database</TableCell>
                <TableCell>8.5</TableCell>
                <TableCell>
                  <Badge variant="outline">Open</Badge>
                </TableCell>
                <TableCell>Jan 20, 2024</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

interface ComplianceMonitoringProps {
  metrics: SecurityMetrics | undefined;
}

function ComplianceMonitoring({ metrics }: ComplianceMonitoringProps) {
  if (!metrics) return <div>Loading...</div>;

  const complianceFrameworks = [
    { name: 'SOC 2', score: 95, status: 'compliant' },
    { name: 'GDPR', score: 88, status: 'compliant' },
    { name: 'HIPAA', score: 92, status: 'compliant' },
    { name: 'PCI DSS', score: 85, status: 'partial' },
    { name: 'ISO 27001', score: 90, status: 'compliant' }
  ];

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Overall Compliance Score</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-4">
            <div className="text-4xl font-bold text-green-600">{metrics.complianceScore}%</div>
            <div className="flex-1">
              <Progress value={metrics.complianceScore} className="h-3" />
              <p className="text-sm text-muted-foreground mt-1">
                Meeting regulatory requirements across all frameworks
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {complianceFrameworks.map((framework) => (
          <Card key={framework.name}>
            <CardHeader>
              <CardTitle className="text-sm">{framework.name}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-2xl font-bold">{framework.score}%</span>
                  <Badge variant={
                    framework.status === 'compliant' ? 'default' :
                    framework.status === 'partial' ? 'secondary' : 'destructive'
                  }>
                    {framework.status}
                  </Badge>
                </div>
                <Progress value={framework.score} className="h-2" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Compliance Issues</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <Alert>
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                PCI DSS: Credit card data encryption needs to be updated to latest standards
              </AlertDescription>
            </Alert>
            <Alert>
              <Eye className="h-4 w-4" />
              <AlertDescription>
                GDPR: Data retention policy review required for user analytics data
              </AlertDescription>
            </Alert>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

interface IncidentResponseProps {
  metrics: SecurityMetrics | undefined;
  alerts: SecurityAlert[] | undefined;
}

function IncidentResponse({ metrics, alerts }: IncidentResponseProps) {
  if (!metrics) return <div>Loading...</div>;

  const openIncidents = alerts?.filter(alert => alert.status === 'open' || alert.status === 'investigating') || [];

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Open Incidents</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{metrics.incidentResponse.openIncidents}</div>
            <p className="text-xs text-muted-foreground">Requiring attention</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Resolved Today</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{metrics.incidentResponse.resolvedIncidents}</div>
            <p className="text-xs text-muted-foreground">Successfully closed</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Avg Response Time</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.incidentResponse.averageResponseTime}m</div>
            <p className="text-xs text-muted-foreground">Detection to response</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Active Incidents</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Incident ID</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Severity</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Assigned To</TableHead>
                <TableHead>Created</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {openIncidents.slice(0, 10).map((incident) => (
                <TableRow key={incident.id}>
                  <TableCell className="font-mono">{incident.id}</TableCell>
                  <TableCell className="capitalize">{incident.type.replace('_', ' ')}</TableCell>
                  <TableCell>
                    <Badge variant={incident.severity === 'critical' ? 'destructive' : 'default'}>
                      {incident.severity}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={incident.status === 'investigating' ? 'secondary' : 'outline'}>
                      {incident.status}
                    </Badge>
                  </TableCell>
                  <TableCell>{incident.assignedTo || 'Unassigned'}</TableCell>
                  <TableCell>{format(new Date(incident.timestamp), 'MMM dd, HH:mm')}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

function EvilModeManagement() {
  return (
    <div className="space-y-6">
      <EvilModeToggle />
      
      <Card>
        <CardHeader>
          <CardTitle>Evil Mode Security Controls</CardTitle>
          <CardDescription>
            Enhanced security measures and monitoring for elevated privilege access
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-3">
              <h4 className="font-medium">Security Measures</h4>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span>Multi-factor Authentication</span>
                  <CheckCircle className="h-4 w-4 text-green-500" />
                </div>
                <div className="flex items-center justify-between">
                  <span>Session Time Limits</span>
                  <CheckCircle className="h-4 w-4 text-green-500" />
                </div>
                <div className="flex items-center justify-between">
                  <span>Real-time Monitoring</span>
                  <CheckCircle className="h-4 w-4 text-green-500" />
                </div>
                <div className="flex items-center justify-between">
                  <span>Audit Logging</span>
                  <CheckCircle className="h-4 w-4 text-green-500" />
                </div>
              </div>
            </div>
            
            <div className="space-y-3">
              <h4 className="font-medium">Monitoring Status</h4>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span>Active Sessions</span>
                  <Badge variant="secondary">0</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span>Today's Usage</span>
                  <Badge variant="outline">2 sessions</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span>Security Violations</span>
                  <Badge variant="destructive">0</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span>Compliance Score</span>
                  <Badge variant="default">98%</Badge>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Mock functions - would be replaced with actual API calls
async function getSecurityMetrics(timeframe: string): Promise<SecurityMetrics> {
  return {
    overallSecurityScore: 87,
    threatLevel: 'medium',
    activeThreats: 3,
    resolvedThreats: 12,
    vulnerabilities: {
      critical: 1,
      high: 5,
      medium: 15,
      low: 32
    },
    complianceScore: 92,
    incidentResponse: {
      averageResponseTime: 12,
      resolvedIncidents: 8,
      openIncidents: 3
    },
    systemHealth: {
      authentication: 'healthy',
      authorization: 'healthy',
      dataProtection: 'warning',
      networkSecurity: 'healthy'
    }
  };
}

async function getSecurityAlerts(): Promise<SecurityAlert[]> {
  return [
    {
      id: 'alert-1',
      type: 'threat',
      severity: 'high',
      title: 'Suspicious login attempts detected',
      description: 'Multiple failed login attempts from unusual IP addresses',
      timestamp: new Date(Date.now() - 1800000),
      status: 'investigating',
      affectedSystems: ['Authentication Service'],
      recommendedActions: ['Block suspicious IPs', 'Enable additional MFA'],
      assignedTo: 'security-team'
    },
    {
      id: 'alert-2',
      type: 'vulnerability',
      severity: 'critical',
      title: 'Critical vulnerability in web server',
      description: 'CVE-2024-0001 affects the main web server component',
      timestamp: new Date(Date.now() - 3600000),
      status: 'open',
      affectedSystems: ['Web Server'],
      recommendedActions: ['Apply security patch immediately'],
      assignedTo: 'devops-team'
    }
  ];
}

async function getThreatIntelligence(): Promise<ThreatIntelligence[]> {
  return [
    {
      id: 'threat-1',
      source: 'MISP',
      threatType: 'Malware Campaign',
      confidence: 85,
      severity: 'high',
      indicators: ['192.168.1.100', 'malicious-domain.com'],
      description: 'New malware campaign targeting financial institutions',
      mitigation: ['Block IP addresses', 'Update antivirus signatures'],
      lastUpdated: new Date(Date.now() - 900000)
    }
  ];
}