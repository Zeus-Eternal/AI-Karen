'use client';

import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { format, subDays, startOfDay, endOfDay } from 'date-fns';
import { UserBehaviorPattern, AuditEventType, AuditSeverity } from '@/types/audit';
import { auditLogger } from '@/services/audit-logger';
import { PermissionGate } from '@/components/rbac';

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

import { 
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Area,
  AreaChart
} from 'recharts';

import { 
  TrendingUp, 
  TrendingDown,
  Users, 
  Shield, 
  AlertTriangle,
  Activity,
  Clock,
  Target,
  Eye,
  BarChart3
} from 'lucide-react';

interface AuditAnalyticsProps {
  className?: string;
}

export function AuditAnalytics({ className }: AuditAnalyticsProps) {
  const [timeframe, setTimeframe] = useState<'7d' | '30d' | '90d'>('30d');
  const [selectedUser, setSelectedUser] = useState<string>('');

  const timeframeOptions = {
    '7d': { days: 7, label: 'Last 7 days' },
    '30d': { days: 30, label: 'Last 30 days' },
    '90d': { days: 90, label: 'Last 90 days' }
  };

  const dateRange = useMemo(() => ({
    start: startOfDay(subDays(new Date(), timeframeOptions[timeframe].days)),
    end: endOfDay(new Date())
  }), [timeframe]);

  const { data: statistics } = useQuery({
    queryKey: ['audit', 'statistics', dateRange],
    queryFn: () => auditLogger.getStatistics(dateRange),
  });

  const { data: userBehavior } = useQuery({
    queryKey: ['audit', 'user-behavior', selectedUser, dateRange],
    queryFn: () => selectedUser ? getUserBehaviorPattern(selectedUser, dateRange) : null,
    enabled: !!selectedUser
  });

  return (
    <PermissionGate permission="security:audit">
      <div className={className}>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold">Audit Analytics</h2>
            <p className="text-muted-foreground">
              Analyze user behavior patterns and security trends
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <Select value={timeframe} onValueChange={(value: '7d' | '30d' | '90d') => setTimeframe(value)}>
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(timeframeOptions).map(([key, { label }]) => (
                  <SelectItem key={key} value={key}>{label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <Tabs defaultValue="overview" className="space-y-4">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="events">Event Analysis</TabsTrigger>
            <TabsTrigger value="users">User Behavior</TabsTrigger>
            <TabsTrigger value="security">Security Trends</TabsTrigger>
            <TabsTrigger value="anomalies">Anomaly Detection</TabsTrigger>
          </TabsList>

          <TabsContent value="overview">
            <OverviewDashboard statistics={statistics} />
          </TabsContent>

          <TabsContent value="events">
            <EventAnalysis statistics={statistics} />
          </TabsContent>

          <TabsContent value="users">
            <UserBehaviorAnalysis 
              statistics={statistics}
              selectedUser={selectedUser}
              onUserSelect={setSelectedUser}
              userBehavior={userBehavior}
            />
          </TabsContent>

          <TabsContent value="security">
            <SecurityTrends statistics={statistics} />
          </TabsContent>

          <TabsContent value="anomalies">
            <AnomalyDetection />
          </TabsContent>
        </Tabs>
      </div>
    </PermissionGate>
  );
}

interface OverviewDashboardProps {
  statistics: any;
}

function OverviewDashboard({ statistics }: OverviewDashboardProps) {
  if (!statistics) {
    return <div>Loading...</div>;
  }

  const metrics = [
    {
      title: 'Total Events',
      value: statistics.totalEvents.toLocaleString(),
      icon: Activity,
      trend: '+12%',
      trendUp: true
    },
    {
      title: 'Active Users',
      value: statistics.topUsers.length.toString(),
      icon: Users,
      trend: '+5%',
      trendUp: true
    },
    {
      title: 'Security Events',
      value: Object.entries(statistics.eventsByType)
        .filter(([type]) => type.startsWith('security:'))
        .reduce((sum, [, count]) => sum + (count as number), 0)
        .toString(),
      icon: Shield,
      trend: '-8%',
      trendUp: false
    },
    {
      title: 'Failed Actions',
      value: (statistics.eventsByOutcome.failure || 0).toString(),
      icon: AlertTriangle,
      trend: '-15%',
      trendUp: false
    }
  ];

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {metrics.map((metric) => (
          <Card key={metric.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{metric.title}</CardTitle>
              <metric.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metric.value}</div>
              <div className="flex items-center text-xs text-muted-foreground">
                {metric.trendUp ? (
                  <TrendingUp className="h-3 w-3 mr-1 text-green-500" />
                ) : (
                  <TrendingDown className="h-3 w-3 mr-1 text-red-500" />
                )}
                {metric.trend} from last period
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Risk Score Trends</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={statistics.riskTrends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Line 
                  type="monotone" 
                  dataKey="averageRiskScore" 
                  stroke="#8884d8" 
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Top Active Users</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {statistics.topUsers.slice(0, 5).map((user: any, index: number) => (
                <div key={user.userId} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center text-xs">
                      {index + 1}
                    </div>
                    <span className="font-medium">{user.username}</span>
                  </div>
                  <Badge variant="secondary">{user.eventCount} events</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

interface EventAnalysisProps {
  statistics: any;
}

function EventAnalysis({ statistics }: EventAnalysisProps) {
  if (!statistics) return <div>Loading...</div>;

  const eventTypeData = Object.entries(statistics.eventsByType).map(([type, count]) => ({
    name: type,
    value: count as number
  }));

  const severityData = Object.entries(statistics.eventsBySeverity).map(([severity, count]) => ({
    name: severity,
    value: count as number
  }));

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Events by Type</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={eventTypeData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Events by Severity</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={severityData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {severityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Event Distribution Over Time</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={statistics.riskTrends}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Area 
                type="monotone" 
                dataKey="averageRiskScore" 
                stroke="#8884d8" 
                fill="#8884d8" 
                fillOpacity={0.3}
              />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}

interface UserBehaviorAnalysisProps {
  statistics: any;
  selectedUser: string;
  onUserSelect: (userId: string) => void;
  userBehavior: UserBehaviorPattern | null;
}

function UserBehaviorAnalysis({ 
  statistics, 
  selectedUser, 
  onUserSelect, 
  userBehavior 
}: UserBehaviorAnalysisProps) {
  if (!statistics) return <div>Loading...</div>;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Select User for Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <Select value={selectedUser} onValueChange={onUserSelect}>
            <SelectTrigger>
              <SelectValue placeholder="Select a user to analyze" />
            </SelectTrigger>
            <SelectContent>
              {statistics.topUsers.map((user: any) => (
                <SelectItem key={user.userId} value={user.userId}>
                  {user.username} ({user.eventCount} events)
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {userBehavior && (
        <>
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Login Frequency</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{userBehavior.loginFrequency}</div>
                <p className="text-xs text-muted-foreground">logins per day</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Avg Session Duration</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {Math.round(userBehavior.averageSessionDuration / 60)}m
                </div>
                <p className="text-xs text-muted-foreground">minutes</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Risk Score</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{userBehavior.riskScore}/10</div>
                <Badge 
                  variant={
                    userBehavior.riskScore >= 8 ? 'destructive' :
                    userBehavior.riskScore >= 5 ? 'default' : 'secondary'
                  }
                >
                  {userBehavior.riskScore >= 8 ? 'High Risk' :
                   userBehavior.riskScore >= 5 ? 'Medium Risk' : 'Low Risk'}
                </Badge>
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Feature Usage</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {userBehavior.featuresUsed.slice(0, 5).map((feature) => (
                    <div key={feature.feature} className="flex items-center justify-between">
                      <span className="text-sm">{feature.feature}</span>
                      <Badge variant="outline">{feature.usageCount} uses</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Risk Factors</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {userBehavior.riskFactors.map((factor, index) => (
                    <div key={index} className="space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">{factor.factor}</span>
                        <Badge variant={factor.score >= 7 ? 'destructive' : 'default'}>
                          {factor.score}/10
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground">{factor.description}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {userBehavior.anomalies.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Detected Anomalies</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {userBehavior.anomalies.map((anomaly, index) => (
                    <Alert key={index} variant={anomaly.severity === 'high' ? 'destructive' : 'default'}>
                      <AlertTriangle className="h-4 w-4" />
                      <AlertDescription>
                        <div className="flex items-center justify-between">
                          <div>
                            <strong>{anomaly.type}</strong>
                            <p className="text-sm">{anomaly.description}</p>
                            <p className="text-xs text-muted-foreground">
                              Detected: {format(new Date(anomaly.detectedAt), 'PPp')}
                            </p>
                          </div>
                          <Badge variant={anomaly.resolved ? 'secondary' : 'destructive'}>
                            {anomaly.resolved ? 'Resolved' : 'Active'}
                          </Badge>
                        </div>
                      </AlertDescription>
                    </Alert>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}

function SecurityTrends({ statistics }: { statistics: any }) {
  if (!statistics) return <div>Loading...</div>;

  const securityEvents = Object.entries(statistics.eventsByType)
    .filter(([type]) => type.startsWith('security:'))
    .map(([type, count]) => ({
      name: type.replace('security:', ''),
      value: count as number
    }));

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Security Event Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={securityEvents}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#ef4444" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Threat Level Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span>Critical</span>
                <Badge variant="destructive">5 events</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span>High</span>
                <Badge variant="default">12 events</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span>Medium</span>
                <Badge variant="secondary">28 events</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span>Low</span>
                <Badge variant="outline">45 events</Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Security Alerts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  Multiple failed login attempts detected for user admin
                </AlertDescription>
              </Alert>
              <Alert>
                <Shield className="h-4 w-4" />
                <AlertDescription>
                  Unusual access pattern detected for sensitive data
                </AlertDescription>
              </Alert>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function AnomalyDetection() {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Anomaly Detection Status</CardTitle>
          <CardDescription>
            Real-time monitoring for unusual patterns and behaviors
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span>Detection Engine</span>
                <Badge variant="default">Active</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span>Sensitivity Level</span>
                <Badge variant="secondary">Medium</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span>Last Scan</span>
                <span className="text-sm text-muted-foreground">2 minutes ago</span>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span>Active Alerts</span>
                <Badge variant="destructive">3</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span>Resolved Today</span>
                <Badge variant="secondary">7</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span>False Positives</span>
                <Badge variant="outline">2</Badge>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Active Anomalies</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                <div className="flex items-center justify-between">
                  <div>
                    <strong>Unusual Login Pattern</strong>
                    <p className="text-sm">User logging in from multiple locations simultaneously</p>
                  </div>
                  <Badge variant="destructive">High</Badge>
                </div>
              </AlertDescription>
            </Alert>

            <Alert>
              <Eye className="h-4 w-4" />
              <AlertDescription>
                <div className="flex items-center justify-between">
                  <div>
                    <strong>Elevated Data Access</strong>
                    <p className="text-sm">User accessing 300% more data than usual</p>
                  </div>
                  <Badge variant="default">Medium</Badge>
                </div>
              </AlertDescription>
            </Alert>

            <Alert>
              <Clock className="h-4 w-4" />
              <AlertDescription>
                <div className="flex items-center justify-between">
                  <div>
                    <strong>Off-Hours Activity</strong>
                    <p className="text-sm">System activity detected outside normal business hours</p>
                  </div>
                  <Badge variant="secondary">Low</Badge>
                </div>
              </AlertDescription>
            </Alert>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Mock function for user behavior pattern - would be replaced with actual API call
async function getUserBehaviorPattern(userId: string, timeframe: { start: Date; end: Date }): Promise<UserBehaviorPattern> {
  // This would be an actual API call
  return {
    userId,
    username: 'testuser',
    timeframe,
    loginFrequency: 3.2,
    averageSessionDuration: 1800, // 30 minutes
    mostActiveHours: [9, 10, 14, 15],
    mostActiveDays: ['Monday', 'Tuesday', 'Wednesday'],
    featuresUsed: [
      { feature: 'Dashboard', usageCount: 45, lastUsed: new Date() },
      { feature: 'Chat', usageCount: 32, lastUsed: new Date() },
      { feature: 'Memory', usageCount: 18, lastUsed: new Date() }
    ],
    riskScore: 3,
    riskFactors: [
      { factor: 'Login Frequency', score: 2, description: 'Normal login pattern' },
      { factor: 'Data Access', score: 4, description: 'Slightly elevated data access' }
    ],
    anomalies: []
  };
}