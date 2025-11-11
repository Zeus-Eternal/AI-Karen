"use client";

import React, { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { format, subDays, startOfDay, endOfDay } from "date-fns";

import { PermissionGate } from "@/components/rbac";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Select,
  SelectTrigger,
  SelectContent,
  SelectItem,
  SelectValue,
} from "@/components/ui/select";

import {
  ResponsiveContainer,
  LineChart,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
} from "recharts";

import {
  Activity,
  Users,
  Shield,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Eye,
  Clock,
} from "lucide-react";

import type { UserBehaviorPattern } from "@/types/audit";
import { auditLogger } from "@/services/audit-logger";

interface AuditAnalyticsProps {
  className?: string;
}

type TimeframeKey = "7d" | "30d" | "90d";

export function AuditAnalytics({ className }: AuditAnalyticsProps) {
  const [timeframe, setTimeframe] = useState<TimeframeKey>("30d");
  const [selectedUser, setSelectedUser] = useState<string>("");

  const timeframeOptions: Record<TimeframeKey, { days: number; label: string }> = {
    "7d": { days: 7, label: "Last 7 days" },
    "30d": { days: 30, label: "Last 30 days" },
    "90d": { days: 90, label: "Last 90 days" },
  };

  const dateRange = useMemo(
    () => ({
      start: startOfDay(subDays(new Date(), timeframeOptions[timeframe].days)),
      end: endOfDay(new Date()),
    }),
    [timeframe]
  );

  const {
    data: statistics,
    isLoading: statsLoading,
    error: statsError,
    refetch: refetchStats,
  } = useQuery({
    queryKey: ["audit", "statistics", dateRange.start.toISOString(), dateRange.end.toISOString()],
    queryFn: async () => auditLogger.getStatistics(dateRange),
    staleTime: 60_000,
  });

  const {
    data: userBehavior = null,
    isLoading: behaviorLoading,
    error: behaviorError,
    refetch: refetchBehavior,
  } = useQuery<UserBehaviorPattern | null>({
    queryKey: ["audit", "user-behavior", selectedUser, dateRange.start.toISOString(), dateRange.end.toISOString()],
    queryFn: async () => (selectedUser ? getUserBehaviorPattern(selectedUser, dateRange) : null),
    enabled: !!selectedUser,
    staleTime: 60_000,
  });

  return (
    <PermissionGate permission="security:audit">
      <div className={className}>
        <div className="flex items-center justify-between mb-6 gap-3 flex-wrap">
          <div>
            <h2 className="text-2xl font-bold">Audit Analytics</h2>
            <p className="text-muted-foreground">
              Explore system events, security signals, and behavior patterns over time.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Select value={timeframe} onValueChange={(v: TimeframeKey) => setTimeframe(v)}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Timeframe" />
              </SelectTrigger>
              <SelectContent>
                {(Object.entries(timeframeOptions) as Array<[TimeframeKey, { label: string }]>) //
                  .map(([key, { label }]) => (
                    <SelectItem key={key} value={key}>
                      {label}
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {statsError && (
          <Alert variant="destructive" className="mb-4">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>Failed to load audit statistics. Please try again.</AlertDescription>
          </Alert>
        )}

        <Tabs defaultValue="overview" className="space-y-4">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="events">Event Analysis</TabsTrigger>
            <TabsTrigger value="users">User Behavior</TabsTrigger>
            <TabsTrigger value="security">Security Trends</TabsTrigger>
            <TabsTrigger value="anomalies">Anomaly Detection</TabsTrigger>
          </TabsList>

          <TabsContent value="overview">
            <OverviewDashboard statistics={statistics} loading={statsLoading} />
          </TabsContent>

          <TabsContent value="events">
            <EventAnalysis statistics={statistics} loading={statsLoading} />
          </TabsContent>

          <TabsContent value="users">
            <UserBehaviorAnalysis
              statistics={statistics}
              loading={statsLoading}
              selectedUser={selectedUser}
              onUserSelect={(id) => {
                setSelectedUser(id);
                // optionally: refetchBehavior(); react-query will handle on key change
              }}
              userBehavior={userBehavior}
              behaviorLoading={behaviorLoading}
              behaviorError={behaviorError}
            />
          </TabsContent>

          <TabsContent value="security">
            <SecurityTrends statistics={statistics} loading={statsLoading} />
          </TabsContent>

          <TabsContent value="anomalies">
            <AnomalyDetection />
          </TabsContent>
        </Tabs>
      </div>
    </PermissionGate>
  );
}

/* -------------------------------- OVERVIEW -------------------------------- */

function OverviewDashboard({ statistics, loading }: { statistics: unknown; loading: boolean }) {
  if (loading) return <div>Loading...</div>;
  if (!statistics) return <div>No data.</div>;

  const totalSecurity = Object.entries(statistics.eventsByType || {})
    .filter(([type]) => String(type).startsWith("security:"))
    .reduce((sum, [, count]) => sum + Number(count || 0), 0);

  const failed = Number(statistics?.eventsByOutcome?.failure || 0);

  const metrics = [
    {
      title: "Total Events",
      value: Number(statistics.totalEvents || 0).toLocaleString(),
      icon: Activity,
      trend: "+12%",
      trendUp: true,
    },
    {
      title: "Active Users",
      value: Number((statistics.topUsers || []).length || 0).toString(),
      icon: Users,
      trend: "+5%",
      trendUp: true,
    },
    {
      title: "Security Events",
      value: totalSecurity.toString(),
      icon: Shield,
      trend: "-8%",
      trendUp: false,
    },
    {
      title: "Failed Actions",
      value: failed.toString(),
      icon: AlertTriangle,
      trend: "-15%",
      trendUp: false,
    },
  ];

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {metrics.map((metric) => (
          <Card key={metric.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium md:text-base lg:text-lg">{metric.title}</CardTitle>
              <metric.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metric.value}</div>
              <div className="flex items-center text-xs text-muted-foreground sm:text-sm md:text-base">
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
            <CardDescription>Average risk score over time</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={statistics.riskTrends || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="averageRiskScore" stroke="#8884d8" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Top Active Users</CardTitle>
            <CardDescription>Most events generated by users</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {(statistics.topUsers || []).slice(0, 5).map((user: unknown, index: number) => (
                <div key={user.userId ?? index} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center text-xs">
                      {index + 1}
                    </div>
                    <span className="font-medium">{user.username ?? user.userId}</span>
                  </div>
                  <Badge variant="secondary">{Number(user.eventCount || 0)} events</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

/* ------------------------------ EVENT ANALYSIS ----------------------------- */

function EventAnalysis({ statistics, loading }: { statistics: unknown; loading: boolean }) {
  if (loading) return <div>Loading...</div>;
  if (!statistics) return <div>No data.</div>;

  const eventTypeData = Object.entries(statistics.eventsByType || {}).map(([type, count]) => ({
    name: String(type),
    value: Number(count),
  }));

  const severityData = Object.entries(statistics.eventsBySeverity || {}).map(([severity, count]) => ({
    name: String(severity),
    value: Number(count),
  }));

  const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884D8", "#ef4444", "#10b981"];

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Events by Type</CardTitle>
            <CardDescription>Distribution of event categories</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={eventTypeData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" angle={-35} textAnchor="end" height={80} interval={0} />
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
            <CardDescription>Relative share of severities</CardDescription>
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
                  outerRadius={90}
                  dataKey="value"
                >
                  {severityData.map((_, index) => (
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
          <CardDescription>Area of average risk score</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={statistics.riskTrends || []}>
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

/* ----------------------------- USER BEHAVIOR ------------------------------ */

function UserBehaviorAnalysis({
  statistics,
  loading,
  selectedUser,
  onUserSelect,
  userBehavior,
  behaviorLoading,
  behaviorError,
}: {
  statistics: unknown;
  loading: boolean;
  selectedUser: string;
  onUserSelect: (userId: string) => void;
  userBehavior: UserBehaviorPattern | null;
  behaviorLoading: boolean;
  behaviorError: unknown;
}) {
  if (loading) return <div>Loading...</div>;
  if (!statistics) return <div>No data.</div>;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Select User for Analysis</CardTitle>
          <CardDescription>Drill down into a specific user’s behavior</CardDescription>
        </CardHeader>
        <CardContent>
          <Select value={selectedUser} onValueChange={onUserSelect}>
            <SelectTrigger className="w-80">
              <SelectValue placeholder="Select a user to analyze" />
            </SelectTrigger>
            <SelectContent>
              {(statistics.topUsers || []).map((user: unknown) => (
                <SelectItem key={user.userId} value={String(user.userId)}>
                  {user.username ?? user.userId} ({Number(user.eventCount || 0)} events)
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {behaviorError && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>Could not load user behavior.</AlertDescription>
        </Alert>
      )}

      {behaviorLoading && <div>Loading user behavior…</div>}

      {userBehavior && !behaviorLoading && (
        <>
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm md:text-base lg:text-lg">Login Frequency</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{userBehavior.loginFrequency}</div>
                <p className="text-xs text-muted-foreground sm:text-sm md:text-base">logins per day</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm md:text-base lg:text-lg">Avg Session Duration</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{Math.round(userBehavior.averageSessionDuration / 60)}m</div>
                <p className="text-xs text-muted-foreground sm:text-sm md:text-base">minutes</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm md:text-base lg:text-lg">Risk Score</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{userBehavior.riskScore}/10</div>
                <Badge
                  variant={
                    userBehavior.riskScore >= 8 ? "destructive" : userBehavior.riskScore >= 5 ? "default" : "secondary"
                  }
                >
                  {userBehavior.riskScore >= 8 ? "High Risk" : userBehavior.riskScore >= 5 ? "Medium Risk" : "Low Risk"}
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
                  {(userBehavior.featuresUsed || []).slice(0, 5).map((feature) => (
                    <div key={feature.feature} className="flex items-center justify-between">
                      <span className="text-sm md:text-base lg:text-lg">{feature.feature}</span>
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
                  {(userBehavior.riskFactors || []).map((factor, index) => (
                    <div key={index} className="space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium md:text-base lg:text-lg">{factor.factor}</span>
                        <Badge variant={factor.score >= 7 ? "destructive" : "default"}>{factor.score}/10</Badge>
                      </div>
                      <p className="text-xs text-muted-foreground sm:text-sm md:text-base">{factor.description}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {(userBehavior.anomalies || []).length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Detected Anomalies</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {userBehavior.anomalies.map((anomaly, index) => (
                    <Alert key={index} variant={anomaly.severity === "high" ? "destructive" : "default"}>
                      <AlertTriangle className="h-4 w-4" />
                      <AlertDescription>
                        <div className="flex items-center justify-between">
                          <div>
                            <strong>{anomaly.type}</strong>
                            <p className="text-sm md:text-base lg:text-lg">{anomaly.description}</p>
                            <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
                              Detected: {format(new Date(anomaly.detectedAt), "PPp")}
                            </p>
                          </div>
                          <Badge variant={anomaly.resolved ? "secondary" : "destructive"}>
                            {anomaly.resolved ? "Resolved" : "Active"}
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

/* ------------------------------ SECURITY TRENDS ---------------------------- */

function SecurityTrends({ statistics, loading }: { statistics: unknown; loading: boolean }) {
  if (loading) return <div>Loading...</div>;
  if (!statistics) return <div>No data.</div>;

  const securityEvents = Object.entries(statistics.eventsByType || {})
    .filter(([type]) => String(type).startsWith("security:"))
    .map(([type, count]) => ({
      name: String(type).replace("security:", ""),
      value: Number(count),
    }));

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Security Event Distribution</CardTitle>
          <CardDescription>Count per security event type</CardDescription>
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
            <CardDescription>Example badges; wire to your stats if available</CardDescription>
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
            <CardDescription>Sample alert tiles; connect to /api/security/alerts</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>Multiple failed logins from unusual IP range</AlertDescription>
              </Alert>
              <Alert>
                <Shield className="h-4 w-4" />
                <AlertDescription>New admin role assignment approved</AlertDescription>
              </Alert>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

/* ------------------------------ ANOMALY VIEW ------------------------------- */

function AnomalyDetection() {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Anomaly Detection Status</CardTitle>
          <CardDescription>Real-time monitoring for unusual patterns and behaviors</CardDescription>
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
                <span className="text-sm text-muted-foreground md:text-base lg:text-lg">2 minutes ago</span>
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
                    <p className="text-sm md:text-base lg:text-lg">
                      User logging in from multiple locations simultaneously
                    </p>
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
                    <p className="text-sm md:text-base lg:text-lg">User accessing 300% more data than usual</p>
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
                    <p className="text-sm md:text-base lg:text-lg">System activity detected outside normal hours</p>
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

/* ------------------------------- MOCK (API) -------------------------------- */

async function getUserBehaviorPattern(
  userId: string,
  timeframe: { start: Date; end: Date }
): Promise<UserBehaviorPattern> {
  // Replace with real API when ready
  return {
    userId,
    username: "testuser",
    timeframe,
    loginFrequency: 3.2,
    averageSessionDuration: 1800, // 30 minutes
    mostActiveHours: [9, 10, 14, 15],
    mostActiveDays: ["Monday", "Tuesday", "Wednesday"],
    featuresUsed: [
      { feature: "Dashboard", usageCount: 45, lastUsed: new Date() },
      { feature: "Chat", usageCount: 32, lastUsed: new Date() },
      { feature: "Memory", usageCount: 18, lastUsed: new Date() },
    ],
    riskScore: 3,
    riskFactors: [
      { factor: "Login Frequency", score: 2, description: "Normal login pattern" },
      { factor: "Data Access", score: 4, description: "Slightly elevated data access" },
    ],
    anomalies: [],
  };
}
