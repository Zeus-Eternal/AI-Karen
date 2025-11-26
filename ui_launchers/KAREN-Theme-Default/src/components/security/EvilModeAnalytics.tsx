"use client";

import React, { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { format, subDays, startOfDay, endOfDay } from "date-fns";
// import { enhancedApiClient } from "@/lib/enhanced-api-client"; // not used currently
import { PermissionGate } from "@/components/rbac";

// Define EvilModeSession type locally
interface EvilModeSession {
  id: string;
  sessionId: string;
  userId: string;
  startTime: Date;
  endTime?: Date;
  reason: string;
  justification?: string;
  approvedBy: string;
  isActive: boolean;
  actions: EvilModeAction[];
}

interface EvilModeAction {
  action: string;
  timestamp: Date;
  resource: string;
  impact: string;
  reversible: boolean;
  details: Record<string, unknown>;
}

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

import {
  ResponsiveContainer,
  BarChart,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Bar,
  PieChart,
  Pie,
  Cell,
} from "recharts";

import {
  Skull,
  Activity,
  Users,
  Target,
  Clock,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Eye,
  FileText,
  CheckCircle,
  XCircle,
  Shield,
} from "lucide-react";

export interface EvilModeAnalyticsProps {
  className?: string;
}

const destructiveAlertClassName =
  "border-destructive/50 text-destructive dark:border-destructive [&>svg]:text-destructive";

const TIMEFRAME_OPTIONS = {
  "7d": { days: 7, label: "Last 7 days" },
  "30d": { days: 30, label: "Last 30 days" },
  "90d": { days: 90, label: "Last 90 days" },
} as const;

type TimeframeKey = keyof typeof TIMEFRAME_OPTIONS;

export interface EvilModeStats {
  totalSessions: number;
  activeSessions: number;
  totalActions: number;
  averageSessionDuration: number; // seconds
  topUsers: Array<{
    userId: string;
    username: string;
    sessionCount: number;
    totalActions: number;
    averageDuration: number;
  }>;
  actionsByImpact: Record<string, number>;
  sessionsByTimeOfDay: Array<{
    hour: number;
    count: number;
  }>;
  complianceMetrics: {
    justificationProvided: number; // %
    additionalAuthUsed: number; // %
    timeoutCompliance: number; // %
    auditTrailComplete: number; // %
  };
  riskAssessment: {
    highRiskActions: number;
    irreversibleActions: number;
    complianceViolations: number;
    securityIncidents: number;
  };
}

export function EvilModeAnalytics({ className }: EvilModeAnalyticsProps) {
  const [timeframe, setTimeframe] = useState<TimeframeKey>("30d");

  const dateRange = useMemo(
    () => ({
      start: startOfDay(subDays(new Date(), TIMEFRAME_OPTIONS[timeframe].days)),
      end: endOfDay(new Date()),
    }),
    [timeframe],
  );

  const { data: stats, isLoading: isLoadingStats } = useQuery<EvilModeStats>({
    queryKey: ["evil-mode", "analytics", dateRange],
    queryFn: () => getEvilModeStats(dateRange),
  });

  const { data: sessions, isLoading: isLoadingSessions } = useQuery<EvilModeSession[]>({
    queryKey: ["evil-mode", "sessions", dateRange],
    queryFn: () => getEvilModeSessions(dateRange),
  });

  return (
    <PermissionGate permissions={["security:admin"]}>
      <div className={className}>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold flex items-center space-x-2">
              <Skull className="h-6 w-6 text-red-600" />
              <span>Evil Mode Analytics</span>
            </h2>
            <p className="text-muted-foreground">
              Audit trails, risk posture, and compliance health for elevated sessions.
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <Select
              value={timeframe}
              onValueChange={(value) => setTimeframe(value as "7d" | "30d" | "90d")}
            >
              <SelectTrigger className="w-44" aria-label="Select timeframe">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(TIMEFRAME_OPTIONS).map(([key, { label }]) => (
                  <SelectItem key={key} value={key}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {isLoadingStats || isLoadingSessions ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
          </div>
        ) : (
          <Tabs defaultValue="overview" className="space-y-4">
            <TabsList>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="sessions">Sessions</TabsTrigger>
              <TabsTrigger value="actions">Actions</TabsTrigger>
              <TabsTrigger value="compliance">Compliance</TabsTrigger>
              <TabsTrigger value="risk">Risk Assessment</TabsTrigger>
            </TabsList>

            <TabsContent value="overview">
              <OverviewDashboard stats={stats} />
            </TabsContent>

            <TabsContent value="sessions">
              <SessionAnalysis stats={stats} sessions={sessions} />
            </TabsContent>

            <TabsContent value="actions">
              <ActionAnalysis stats={stats} sessions={sessions} />
            </TabsContent>

            <TabsContent value="compliance">
              <ComplianceAnalysis stats={stats} />
            </TabsContent>

            <TabsContent value="risk">
              <RiskAssessment stats={stats} />
            </TabsContent>
          </Tabs>
        )}
      </div>
    </PermissionGate>
  );
}

export interface OverviewDashboardProps {
  stats: EvilModeStats | undefined;
}

function OverviewDashboard({ stats }: OverviewDashboardProps) {
  if (!stats) return <div>Loading...</div>;

  const metrics = [
    {
      title: "Total Sessions",
      value: stats.totalSessions.toString(),
      icon: Activity,
      trend: "+5%",
      trendUp: true,
      color: "text-blue-600",
    },
    {
      title: "Active Sessions",
      value: stats.activeSessions.toString(),
      icon: Users,
      trend: stats.activeSessions > 0 ? "Active" : "None",
      trendUp: stats.activeSessions === 0,
      color: stats.activeSessions > 0 ? "text-red-600" : "text-green-600",
    },
    {
      title: "Total Actions",
      value: stats.totalActions.toString(),
      icon: Target,
      trend: "+12%",
      trendUp: true,
      color: "text-orange-600",
    },
    {
      title: "Avg Duration",
      value: `${Math.round(stats.averageSessionDuration / 60)}m`,
      icon: Clock,
      trend: "-8%",
      trendUp: false,
      color: "text-purple-600",
    },
  ] as const;

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {metrics.map((metric) => (
          <Card key={metric.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{metric.title}</CardTitle>
              <metric.icon className={`h-4 w-4 ${metric.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metric.value}</div>
              <div className="flex items-center text-xs text-muted-foreground">
                {metric.trendUp ? (
                  <TrendingUp className="h-3 w-3 mr-1 text-green-500" />
                ) : (
                  <TrendingDown className="h-3 w-3 mr-1 text-red-500" />
                )}
                <span>{metric.trend}</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Usage by Time of Day</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={stats.sessionsByTimeOfDay}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="hour" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#ef4444" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Top Users</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {stats.topUsers.slice(0, 5).map((user, index) => (
                <div key={user.userId} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-6 h-6 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center text-xs">
                      {index + 1}
                    </div>
                    <span className="font-medium">{user.username}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge variant="destructive">{user.sessionCount} sessions</Badge>
                    <Badge variant="outline">{user.totalActions} actions</Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <Alert className={destructiveAlertClassName}>
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          Evil Mode usage is continuously monitored for security and compliance. All activities are
          subject to audit and review.
        </AlertDescription>
      </Alert>
    </div>
  );
}

export interface SessionAnalysisProps {
  stats: EvilModeStats | undefined;
  sessions: EvilModeSession[] | undefined;
}

function SessionAnalysis({ stats, sessions }: SessionAnalysisProps) {
  if (!stats || !sessions) return <div>Loading...</div>;

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm md:text-base">Session Duration Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {[
                ["< 15 min", "45%"],
                ["15-30 min", "30%"],
                ["30-60 min", "20%"],
                ["> 60 min", "5%"],
              ].map(([label, val]) => (
                <div key={label} className="flex justify-between text-sm">
                  <span>{label}</span>
                  <span>{val}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm md:text-base">Session Outcomes</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Normal Termination</span>
                <Badge variant="secondary">85%</Badge>
              </div>
              <div className="flex justify-between text-sm">
                <span>Timeout</span>
                <Badge variant="default">12%</Badge>
              </div>
              <div className="flex justify-between text-sm">
                <span>Force Terminated</span>
                <Badge variant="destructive">3%</Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm md:text-base">Justification Quality</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Detailed</span>
                <Badge variant="default">60%</Badge>
              </div>
              <div className="flex justify-between text-sm">
                <span>Adequate</span>
                <Badge variant="secondary">30%</Badge>
              </div>
              <div className="flex justify-between text-sm">
                <span>Insufficient</span>
                <Badge variant="destructive">10%</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Sessions</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>User</TableHead>
                <TableHead>Start Time</TableHead>
                <TableHead>Duration</TableHead>
                <TableHead>Actions</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Risk Level</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sessions.slice(0, 10).map((session) => {
                const start = new Date(session.startTime);
                const end = session.endTime ? new Date(session.endTime) : new Date();
                const durationMinutes = Math.max(
                  0,
                  Math.floor((end.getTime() - start.getTime()) / (1000 * 60)),
                );

                const highRiskActions = session.actions.filter(
                  (a) => a.impact === "high" || a.impact === "critical",
                ).length;

                const riskLevel =
                  highRiskActions > 5 ? "High" : highRiskActions > 2 ? "Medium" : "Low";

                return (
                  <TableRow key={session.sessionId}>
                    <TableCell className="font-medium">{session.userId}</TableCell>
                    <TableCell>{format(start, "MMM dd, HH:mm")}</TableCell>
                    <TableCell>{durationMinutes}m</TableCell>
                    <TableCell>{session.actions.length}</TableCell>
                    <TableCell>
                      <Badge variant={session.endTime ? "secondary" : "destructive"}>
                        {session.endTime ? "Ended" : "Active"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          riskLevel === "High"
                            ? "destructive"
                            : riskLevel === "Medium"
                            ? "default"
                            : "secondary"
                        }
                      >
                        {riskLevel}
                      </Badge>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

export interface ActionAnalysisProps {
  stats: EvilModeStats | undefined;
  sessions: EvilModeSession[] | undefined;
}

function ActionAnalysis({ stats, sessions }: ActionAnalysisProps) {
  if (!stats || !sessions) return <div>Loading...</div>;

  const actionData = Object.entries(stats.actionsByImpact).map(([impact, count]) => ({
    name: impact,
    value: count,
  }));

  const COLORS = ["#ef4444", "#f97316", "#eab308", "#22c55e"];

  const highRiskItems = sessions
    .flatMap((session) =>
      session.actions
        .filter((action) => action.impact === "critical" || action.impact === "high")
        .map((action) => ({ ...action, sessionId: session.sessionId, userId: session.userId })),
    )
    .slice(0, 10);

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Actions by Impact Level</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={actionData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {actionData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Action Categories</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span>System Configuration</span>
                <Badge variant="destructive">45%</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span>User Management</span>
                <Badge variant="default">25%</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span>Data Access</span>
                <Badge variant="secondary">20%</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span>Security Override</span>
                <Badge variant="destructive">10%</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>High-Risk Actions</CardTitle>
          <CardDescription>Recent elevated operations requiring review</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {highRiskItems.map((action, index) => (
              <div
                key={`${action.sessionId}-${index}`}
                className="flex items-center justify-between p-3 border rounded-lg"
              >
                <div className="flex items-center space-x-3">
                  <div
                    className={`p-1 rounded-full ${
                      action.impact === "critical"
                        ? "bg-red-100 dark:bg-red-900/30"
                        : "bg-orange-100 dark:bg-orange-900/30"
                    }`}
                  >
                    {action.reversible ? (
                      <CheckCircle className="h-3 w-3 text-green-600" />
                    ) : (
                      <XCircle className="h-3 w-3 text-red-600" />
                    )}
                  </div>
                  <div>
                    <p className="font-medium">{action.action}</p>
                    <p className="text-sm text-muted-foreground">
                      {action.resource} • {action.userId} •{" "}
                      {format(new Date(action.timestamp), "MMM dd, HH:mm")}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge variant={action.impact === "critical" ? "destructive" : "default"}>
                    {action.impact}
                  </Badge>
                  {!action.reversible && (
                    <Badge variant="outline" className="text-red-600">
                      irreversible
                    </Badge>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export interface ComplianceAnalysisProps {
  stats: EvilModeStats | undefined;
}

function ComplianceAnalysis({ stats }: ComplianceAnalysisProps) {
  if (!stats) return <div>Loading...</div>;

  const complianceScore = Math.round(
    (stats.complianceMetrics.justificationProvided +
      stats.complianceMetrics.additionalAuthUsed +
      stats.complianceMetrics.timeoutCompliance +
      stats.complianceMetrics.auditTrailComplete) /
      4,
  );

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Compliance Score</CardTitle>
          <CardDescription>Aggregate of key compliance controls</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-4">
            <div className="text-4xl font-bold text-green-600">{complianceScore}%</div>
            <div className="flex-1">
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-green-600 h-2 rounded-full"
                  style={{ width: `${complianceScore}%` }}
                />
              </div>
              <p className="text-sm text-muted-foreground mt-1">
                {complianceScore >= 90
                  ? "Excellent"
                  : complianceScore >= 80
                  ? "Good"
                  : complianceScore >= 70
                  ? "Fair"
                  : "Needs Improvement"}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Compliance Metrics</CardTitle>
          </CardHeader>
        <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span>Justification Provided</span>
                <div className="flex items-center space-x-2">
                  <Badge variant="default">{stats.complianceMetrics.justificationProvided}%</Badge>
                  <CheckCircle className="h-4 w-4 text-green-500" />
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span>Additional Auth Used</span>
                <div className="flex items-center space-x-2">
                  <Badge variant="default">{stats.complianceMetrics.additionalAuthUsed}%</Badge>
                  <CheckCircle className="h-4 w-4 text-green-500" />
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span>Timeout Compliance</span>
                <div className="flex items-center space-x-2">
                  <Badge variant="default">{stats.complianceMetrics.timeoutCompliance}%</Badge>
                  <CheckCircle className="h-4 w-4 text-green-500" />
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span>Audit Trail Complete</span>
                <div className="flex items-center space-x-2">
                  <Badge variant="default">{stats.complianceMetrics.auditTrailComplete}%</Badge>
                  <CheckCircle className="h-4 w-4 text-green-500" />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Compliance Violations</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <Alert className={destructiveAlertClassName}>
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>2 sessions without proper justification</AlertDescription>
              </Alert>
              <Alert>
                <Eye className="h-4 w-4" />
                <AlertDescription>1 session exceeded time limit</AlertDescription>
              </Alert>
              <Alert>
                <FileText className="h-4 w-4" />
                <AlertDescription>3 actions missing audit details</AlertDescription>
              </Alert>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export interface RiskAssessmentProps {
  stats: EvilModeStats | undefined;
}

function RiskAssessment({ stats }: RiskAssessmentProps) {
  if (!stats) return <div>Loading...</div>;

  const riskLevel =
    stats.riskAssessment.highRiskActions > 10
      ? "High"
      : stats.riskAssessment.highRiskActions > 5
      ? "Medium"
      : "Low";

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Overall Risk Level</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-4">
            <Badge
              variant={
                riskLevel === "High" ? "destructive" : riskLevel === "Medium" ? "default" : "secondary"
              }
              className="text-lg px-4 py-2"
            >
              {riskLevel} Risk
            </Badge>
            <div className="text-sm text-muted-foreground">
              Based on recent high/critical actions and incident counts.
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">High Risk Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {stats.riskAssessment.highRiskActions}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Irreversible Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">
              {stats.riskAssessment.irreversibleActions}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Compliance Violations</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">
              {stats.riskAssessment.complianceViolations}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Security Incidents</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {stats.riskAssessment.securityIncidents}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Risk Mitigation Recommendations</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <Alert>
              <Shield className="h-4 w-4" />
              <AlertDescription>
                Require second-factor for all critical actions executed under elevation.
              </AlertDescription>
            </Alert>
            <Alert>
              <Clock className="h-4 w-4" />
              <AlertDescription>
                Reduce maximum session timebox for non-admins to 30 minutes.
              </AlertDescription>
            </Alert>
            <Alert>
              <Eye className="h-4 w-4" />
              <AlertDescription>
                Enable real-time monitoring alerts for high-risk actions.
              </AlertDescription>
            </Alert>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

/* ============================
   Mock API — replace with real calls
   ============================ */

async function getEvilModeStats(_dateRange: { start: Date; end: Date }): Promise<EvilModeStats> {
  return {
    totalSessions: 45,
    activeSessions: 2,
    totalActions: 234,
    averageSessionDuration: 1800, // 30 minutes
    topUsers: [
      { userId: "user-1", username: "admin", sessionCount: 12, totalActions: 89, averageDuration: 1500 },
      { userId: "user-2", username: "security", sessionCount: 8, totalActions: 45, averageDuration: 2100 },
    ],
    actionsByImpact: {
      low: 120,
      medium: 80,
      high: 25,
      critical: 9,
    },
    sessionsByTimeOfDay: Array.from({ length: 24 }, (_, i) => ({
      hour: i,
      count: Math.floor(Math.random() * 10),
    })),
    complianceMetrics: {
      justificationProvided: 95,
      additionalAuthUsed: 88,
      timeoutCompliance: 92,
      auditTrailComplete: 98,
    },
    riskAssessment: {
      highRiskActions: 34,
      irreversibleActions: 12,
      complianceViolations: 6,
      securityIncidents: 2,
    },
  };
}

async function getEvilModeSessions(_dateRange: { start: Date; end: Date }): Promise<EvilModeSession[]> {
  return [
    {
      id: "session-1",
      sessionId: "session-1",
      userId: "user-1",
      startTime: new Date(Date.now() - 3_600_000),
      endTime: new Date(Date.now() - 1_800_000),
      reason: "Emergency system maintenance",
      justification: "Emergency system maintenance",
      approvedBy: "admin-user",
      isActive: false,
      actions: [
        {
          action: "Modified system configuration",
          timestamp: new Date(Date.now() - 3_000_000),
          resource: "system.config",
          impact: "high",
          reversible: true,
          details: {},
        },
      ],
    },
    {
      id: "session-2",
      sessionId: "session-2",
      userId: "user-2",
      startTime: new Date(Date.now() - 5_400_000),
      endTime: undefined, // active
      reason: "Incident response",
      justification: "Incident response",
      approvedBy: "admin-user",
      isActive: true,
      actions: [
        {
          action: "Accessed protected data",
          timestamp: new Date(Date.now() - 1_200_000),
          resource: "vault.records",
          impact: "critical",
          reversible: false,
          details: {},
        },
        {
          action: "Adjusted user role",
          timestamp: new Date(Date.now() - 900_000),
          resource: "rbac.roles",
          impact: "high",
          reversible: true,
          details: {},
        },
      ],
    },
  ];
}
