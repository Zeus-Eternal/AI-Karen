"use client";

import { useEffect, useState } from "react";
import { apiClient, ApiError } from "@/lib/api";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, AlertCircle, BarChart3, Clock3, Loader2, ShieldAlert, Users } from "lucide-react";

type AnalyticsSummary = {
  daily: {
    interactions: number;
    users: number;
    satisfaction: number;
    average_session_duration: number;
    peak_hours: number[];
  };
  weekly: {
    interactions: number;
    users: number;
    satisfaction: number;
    average_session_duration: number;
    peak_hours: number[];
  };
  monthly: {
    interactions: number;
    users: number;
    satisfaction: number;
    average_session_duration: number;
    peak_hours: number[];
  };
  system: Record<string, unknown>;
  timestamp: string;
};

function formatPeakHours(hours: number[] | undefined): string {
  if (!hours || hours.length === 0) {
    return "No peak data";
  }
  return hours.slice(0, 4).map((hour) => `${hour}:00`).join(", ");
}

export default function AdminAnalyticsPanel() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [authRequired, setAuthRequired] = useState(false);
  const [accessDenied, setAccessDenied] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    const loadSummary = async () => {
      setIsLoading(true);
      setAuthRequired(false);
      setAccessDenied(false);
      try {
        const response = await apiClient.get<AnalyticsSummary>("/api/analytics/summary");
        if (!mounted) {
          return;
        }
        setSummary(response);
        setLoadError(null);
      } catch (error) {
        if (!mounted) {
          return;
        }
        if (error instanceof ApiError && error.status === 401) {
          setAuthRequired(true);
          setSummary(null);
          setLoadError(null);
        } else if (error instanceof ApiError && error.status === 403) {
          setAccessDenied(true);
          setSummary(null);
          setLoadError(null);
        } else {
          setSummary(null);
          setLoadError(error instanceof Error ? error.message : "Karen could not load analytics summary.");
        }
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    };

    void loadSummary();
    return () => {
      mounted = false;
    };
  }, []);

  const cards = summary
    ? [
        {
          title: "Daily Interactions",
          value: summary.daily.interactions,
          detail: `${summary.daily.users} unique users`,
          icon: Activity,
        },
        {
          title: "Weekly Interactions",
          value: summary.weekly.interactions,
          detail: `${summary.weekly.users} unique users`,
          icon: BarChart3,
        },
        {
          title: "Avg Session",
          value: `${summary.daily.average_session_duration.toFixed(1)}m`,
          detail: `daily satisfaction ${summary.daily.satisfaction.toFixed(1)}`,
          icon: Clock3,
        },
        {
          title: "Monthly Users",
          value: summary.monthly.users,
          detail: `${summary.monthly.interactions} interactions`,
          icon: Users,
        },
      ]
    : [];

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-primary" />
            Analytics
          </CardTitle>
          <CardDescription>
            Backend-derived usage analytics from Karen&apos;s analytics service instead of placeholder admin metrics.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {authRequired && (
            <Alert className="border-primary/20 bg-primary/5">
              <ShieldAlert className="h-4 w-4 !text-primary" />
              <AlertTitle>Sign In Required</AlertTitle>
              <AlertDescription>
                The analytics routes are live, but this session is not authenticated. Sign in to inspect backend usage metrics.
              </AlertDescription>
            </Alert>
          )}
          {accessDenied && (
            <Alert className="border-primary/20 bg-primary/5">
              <ShieldAlert className="h-4 w-4 !text-primary" />
              <AlertTitle>Analytics Access Restricted</AlertTitle>
              <AlertDescription>
                The analytics routes are live, but this session is not authorized to inspect backend usage metrics.
              </AlertDescription>
            </Alert>
          )}
          {loadError && (
            <Alert className="border-yellow-500/30 bg-yellow-500/5">
              <AlertCircle className="h-4 w-4 !text-yellow-600" />
              <AlertTitle>Analytics Unavailable</AlertTitle>
              <AlertDescription>{loadError}</AlertDescription>
            </Alert>
          )}
          {isLoading ? (
            <div className="flex items-center gap-2 rounded-xl border border-border/70 p-4 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading analytics summary.
            </div>
          ) : summary ? (
            <>
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                {cards.map((card) => {
                  const Icon = card.icon;
                  return (
                    <Card key={card.title} className="border-border/70">
                      <CardHeader className="pb-2">
                        <CardTitle className="flex items-center justify-between text-sm font-medium">
                          <span>{card.title}</span>
                          <Icon className="h-4 w-4 text-primary" />
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-semibold">{card.value}</div>
                        <p className="text-xs text-muted-foreground">{card.detail}</p>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>

              <div className="grid gap-4 xl:grid-cols-3">
                <Card className="border-border/70">
                  <CardHeader>
                    <CardTitle className="text-base">Daily Window</CardTitle>
                    <CardDescription>Current operational usage snapshot.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-2 text-sm">
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Peak hours</span>
                      <Badge variant="outline">{formatPeakHours(summary.daily.peak_hours)}</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Satisfaction</span>
                      <span>{summary.daily.satisfaction.toFixed(1)}</span>
                    </div>
                  </CardContent>
                </Card>
                <Card className="border-border/70">
                  <CardHeader>
                    <CardTitle className="text-base">Weekly Window</CardTitle>
                    <CardDescription>Short-horizon trend data.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-2 text-sm">
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Peak hours</span>
                      <Badge variant="outline">{formatPeakHours(summary.weekly.peak_hours)}</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Avg session</span>
                      <span>{summary.weekly.average_session_duration.toFixed(1)}m</span>
                    </div>
                  </CardContent>
                </Card>
                <Card className="border-border/70">
                  <CardHeader>
                    <CardTitle className="text-base">Monthly Window</CardTitle>
                    <CardDescription>Longer-horizon system view.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-2 text-sm">
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Peak hours</span>
                      <Badge variant="outline">{formatPeakHours(summary.monthly.peak_hours)}</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Satisfaction</span>
                      <span>{summary.monthly.satisfaction.toFixed(1)}</span>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </>
          ) : (
            <div className="rounded-xl border border-dashed border-border/70 p-6 text-sm text-muted-foreground">
              No analytics summary is currently available.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
