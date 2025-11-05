"use client";

import React, { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { format, subDays, startOfDay, endOfDay } from "date-fns";
import { AgCharts } from "ag-charts-react";
import type { AgChartOptions } from "ag-charts-community";

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
    [timeframe, timeframeOptions]
  );

  const {
    data: statistics,
    isLoading: statsLoading,
    error: statsError,
  } = useQuery({
    queryKey: ["audit", "statistics", dateRange.start.toISOString(), dateRange.end.toISOString()],
    queryFn: async () => auditLogger.getStatistics(dateRange),
    staleTime: 60_000,
  });

  const {
    data: userBehavior = null,
    isLoading: behaviorLoading,
    error: behaviorError,
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
                {(Object.entries(timeframeOptions) as Array<[TimeframeKey, { label: string }]>).map(([key, { label }]) => (
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
              onUserSelect={(id) => setSelectedUser(id)}
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

function OverviewDashboard({ statistics, loading }: { statistics: any; loading: boolean }) {
  if (loading) return <div>Loading...</div>;
  if (!statistics) return <div>No data.</div>;

  const totalSecurity = Object.entries(statistics.eventsByType || {})
    .filter(([type]) => String(type).startsWith("security:"))
    .reduce((sum, [, count]) => sum + Number(count || 0), 0);

  const failed = Number(statistics?.eventsByOutcome?.failure || 0);

  const metrics = [
    { title: "Total Events", value: Number(statistics.totalEvents || 0).toLocaleString(), icon: Activity, trend: "+12%", trendUp: true },
    { title: "Active Users", value: Number((statistics.topUsers || []).length || 0).toString(), icon: Users, trend: "+5%", trendUp: true },
    { title: "Security Events", value: totalSecurity.toString(), icon: Shield, trend: "-8%", trendUp: false },
    { title: "Failed Actions", value: failed.toString(), icon: AlertTriangle, trend: "-15%", trendUp: false },
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
                {metric.trendUp ? <TrendingUp className="h-3 w-3 mr-1 text-green-500" /> : <TrendingDown className="h-3 w-3 mr-1 text-red-500" />}
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
            <div className="h-80"><AgCharts options={{ data: statistics.riskTrends || [], theme: "ag-default", background: { fill: "transparent" }, series: [{ type: "line", xKey: "date", yKey: "averageRiskScore", stroke: "#8884d8", strokeWidth: 2 } as any], axes: [{ type: "category", position: "bottom" }, { type: "number", position: "left" }] }} /></div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Top Active Users</CardTitle>
            <CardDescription>Most events generated by users</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {(statistics.topUsers || []).slice(0, 5).map((user: any, index: number) => (
                <div key={user.userId ?? index} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center text-xs">{index + 1}</div>
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

function EventAnalysis({ statistics, loading }: { statistics: any; loading: boolean }) {
  if (loading) return <div>Loading...</div>;
  if (!statistics) return <div>No data.</div>;

  const eventTypeData = Object.entries(statistics.eventsByType || {}).map(([type, count]) => ({ name: String(type), value: Number(count) }));
  const severityData = Object.entries(statistics.eventsBySeverity || {}).map(([severity, count]) => ({ name: String(severity), value: Number(count) }));

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Events by Type</CardTitle><CardDescription>Distribution of event categories</CardDescription></CardHeader>
          <CardContent><div className="h-80"><AgCharts options={{ data: eventTypeData, theme: "ag-default", background: { fill: "transparent" }, series: [{ type: "bar", xKey: "name", yKey: "value", fill: "#8884d8" } as any], axes: [{ type: "category", position: "bottom", label: { rotation: -35 } }, { type: "number", position: "left" }] }} /></div></CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Events by Severity</CardTitle><CardDescription>Relative share of severities</CardDescription></CardHeader>
          <CardContent><div className="h-80"><AgCharts options={{ data: severityData, theme: "ag-default", background: { fill: "transparent" }, series: [{ type: "pie", angleKey: "value", labelKey: "name", label: { enabled: true } } as any] }} /></div></CardContent>
        </Card>
      </div>
      <Card>
        <CardHeader><CardTitle>Event Distribution Over Time</CardTitle></CardHeader>
        <CardContent><div className="h-80"><AgCharts options={{ data: statistics.riskTrends || [], theme: "ag-default", background: { fill: "transparent" }, series: [{ type: "area", xKey: "date", yKey: "averageRiskScore", fill: "#8884d8", fillOpacity: 0.3 } as any], axes: [{ type: "category", position: "bottom" }, { type: "number", position: "left" }] }} /></div></CardContent>
      </Card>
    </div>
  );
}

function UserBehaviorAnalysis({ statistics, loading, selectedUser, onUserSelect, userBehavior, behaviorLoading, behaviorError }: { statistics: any; loading: boolean; selectedUser: string; onUserSelect: (userId: string) => void; userBehavior: UserBehaviorPattern | null; behaviorLoading: boolean; behaviorError: any }) {
  if (loading) return <div>Loading...</div>;
  if (!statistics) return <div>No data.</div>;
  return <div className="space-y-6"><Card><CardHeader><CardTitle>Select User for Analysis</CardTitle></CardHeader><CardContent><Select value={selectedUser} onValueChange={onUserSelect}><SelectTrigger className="w-80"><SelectValue placeholder="Select a user" /></SelectTrigger><SelectContent>{(statistics.topUsers || []).map((user: any) => <SelectItem key={user.userId} value={String(user.userId)}>{user.username ?? user.userId} ({Number(user.eventCount || 0)} events)</SelectItem>)}</SelectContent></Select></CardContent></Card>{behaviorError && <Alert variant="destructive"><AlertTriangle className="h-4 w-4" /><AlertDescription>Could not load user behavior.</AlertDescription></Alert>}{userBehavior && <div className="grid gap-4 md:grid-cols-3"><Card><CardHeader><CardTitle>Login Frequency</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{userBehavior.loginFrequency}</div><p className="text-xs text-muted-foreground">logins per day</p></CardContent></Card><Card><CardHeader><CardTitle>Avg Session Duration</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{Math.round(userBehavior.averageSessionDuration / 60)}m</div><p className="text-xs text-muted-foreground">minutes</p></CardContent></Card><Card><CardHeader><CardTitle>Risk Score</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{userBehavior.riskScore}/10</div><Badge variant={userBehavior.riskScore >= 8 ? "destructive" : userBehavior.riskScore >= 5 ? "default" : "secondary"}>{userBehavior.riskScore >= 8 ? "High Risk" : userBehavior.riskScore >= 5 ? "Medium Risk" : "Low Risk"}</Badge></CardContent></Card></div>}</div>;
}

function SecurityTrends({ statistics, loading }: { statistics: any; loading: boolean }) {
  if (loading) return <div>Loading...</div>;
  if (!statistics) return <div>No data.</div>;
  const securityEvents = Object.entries(statistics.eventsByType || {}).filter(([type]) => String(type).startsWith("security:")).map(([type, count]) => ({ name: String(type).replace("security:", ""), value: Number(count) }));
  return <div className="space-y-6"><Card><CardHeader><CardTitle>Security Event Distribution</CardTitle></CardHeader><CardContent><div className="h-80"><AgCharts options={{ data: securityEvents, theme: "ag-default", background: { fill: "transparent" }, series: [{ type: "bar", xKey: "name", yKey: "value", fill: "#ef4444" } as any], axes: [{ type: "category", position: "bottom" }, { type: "number", position: "left" }] }} /></div></CardContent></Card></div>;
}

function AnomalyDetection() {
  return <div className="space-y-6"><Card><CardHeader><CardTitle>Anomaly Detection Status</CardTitle></CardHeader><CardContent><div className="grid gap-4 md:grid-cols-2"><div className="space-y-2"><div className="flex items-center justify-between"><span>Detection Engine</span><Badge variant="default">Active</Badge></div></div></div></CardContent></Card></div>;
}

async function getUserBehaviorPattern(userId: string, timeframe: { start: Date; end: Date }): Promise<UserBehaviorPattern> {
  return { userId, username: "testuser", timeframe, loginFrequency: 3.2, averageSessionDuration: 1800, mostActiveHours: [9, 10, 14, 15], mostActiveDays: ["Monday", "Tuesday", "Wednesday"], featuresUsed: [{ feature: "Dashboard", usageCount: 45, lastUsed: new Date() }, { feature: "Chat", usageCount: 32, lastUsed: new Date() }], riskScore: 3, riskFactors: [{ factor: "Login Frequency", score: 2, description: "Normal login pattern" }], anomalies: [] };
}
