"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertCircle,
  BarChart3,
  Clock3,
  Loader2,
  RefreshCw,
  ShieldAlert,
  Users,
} from "lucide-react";

import { apiClient, ApiError } from "@/lib/api";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

type AnalyticsWindow = {
  interactions?: number | null;
  users?: number | null;
  satisfaction?: number | null;
  average_session_duration?: number | null;
  peak_hours?: number[] | null;
};

type AnalyticsSummary = {
  daily?: AnalyticsWindow | null;
  weekly?: AnalyticsWindow | null;
  monthly?: AnalyticsWindow | null;
  system?: Record<string, unknown>;
  timestamp?: string | null;
};

type AnalyticsSummaryResponse =
  | AnalyticsSummary
  | {
      summary?: AnalyticsSummary | null;
      data?: AnalyticsSummary | null;
      timestamp?: string | null;
    };

type AnalyticsCard = {
  title: string;
  value: string;
  detail: string;
  icon: typeof Activity;
};

const EMPTY_WINDOW: AnalyticsWindow = {
  interactions: null,
  users: null,
  satisfaction: null,
  average_session_duration: null,
  peak_hours: [],
};

const getErrorMessage = (error: unknown, fallback: string) => {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return "This session is not authenticated. Sign in to inspect backend usage analytics.";
    }

    if (error.status === 403) {
      return "This session is not authorized to inspect backend usage analytics.";
    }

    return error.message || fallback;
  }

  if (error instanceof Error && error.message) {
    return error.message;
  }

  return fallback;
};

const normalizeSummaryResponse = (
  response: AnalyticsSummaryResponse,
): AnalyticsSummary | null => {
  if ("summary" in response && response.summary) {
    return response.summary;
  }

  if ("data" in response && response.data) {
    return response.data;
  }

  if ("daily" in response || "weekly" in response || "monthly" in response) {
    return response;
  }

  return null;
};

const isFiniteNumber = (value: unknown): value is number => {
  return typeof value === "number" && Number.isFinite(value);
};

const formatInteger = (value: number | null | undefined) => {
  if (!isFiniteNumber(value)) {
    return "unknown";
  }

  return Math.round(value).toLocaleString();
};

const formatMinutes = (value: number | null | undefined) => {
  if (!isFiniteNumber(value)) {
    return "unknown";
  }

  return `${value.toFixed(1)}m`;
};

const formatSatisfaction = (value: number | null | undefined) => {
  if (!isFiniteNumber(value)) {
    return "unscored";
  }

  return value.toFixed(1);
};

const formatPeakHours = (hours: number[] | null | undefined): string => {
  if (!Array.isArray(hours) || hours.length === 0) {
    return "No peak data";
  }

  return hours
    .filter((hour) => Number.isInteger(hour) && hour >= 0 && hour <= 23)
    .slice(0, 4)
    .map((hour) => `${String(hour).padStart(2, "0")}:00`)
    .join(", ");
};

const formatDateTime = (value: string | null | undefined) => {
  if (!value) {
    return "Not recorded";
  }

  const parsed = new Date(value);

  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleString();
};

const getWindow = (
  summary: AnalyticsSummary | null,
  key: "daily" | "weekly" | "monthly",
): AnalyticsWindow => {
  return summary?.[key] || EMPTY_WINDOW;
};

export default function AdminAnalyticsPanel() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [authRequired, setAuthRequired] = useState(false);
  const [accessDenied, setAccessDenied] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  const loadSummary = useCallback(async () => {
    setIsLoading(true);
    setAuthRequired(false);
    setAccessDenied(false);
    setLoadError(null);

    try {
      const response = await apiClient.get<AnalyticsSummaryResponse>(
        "/api/analytics/summary",
      );

      setSummary(normalizeSummaryResponse(response));
    } catch (error) {
      setSummary(null);

      if (error instanceof ApiError && error.status === 401) {
        setAuthRequired(true);
        return;
      }

      if (error instanceof ApiError && error.status === 403) {
        setAccessDenied(true);
        return;
      }

      setLoadError(
        getErrorMessage(error, "Karen could not load analytics summary."),
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadSummary();
  }, [loadSummary]);

  const daily = getWindow(summary, "daily");
  const weekly = getWindow(summary, "weekly");
  const monthly = getWindow(summary, "monthly");

  const cards = useMemo<AnalyticsCard[]>(() => {
    if (!summary) {
      return [];
    }

    return [
      {
        title: "Daily Interactions",
        value: formatInteger(daily.interactions),
        detail: `${formatInteger(daily.users)} unique users`,
        icon: Activity,
      },
      {
        title: "Weekly Interactions",
        value: formatInteger(weekly.interactions),
        detail: `${formatInteger(weekly.users)} unique users`,
        icon: BarChart3,
      },
      {
        title: "Avg Session",
        value: formatMinutes(daily.average_session_duration),
        detail: `daily satisfaction ${formatSatisfaction(daily.satisfaction)}`,
        icon: Clock3,
      },
      {
        title: "Monthly Users",
        value: formatInteger(monthly.users),
        detail: `${formatInteger(monthly.interactions)} interactions`,
        icon: Users,
      },
    ];
  }, [daily, monthly, summary, weekly]);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-primary" />
              Analytics
            </CardTitle>
            <CardDescription>
              Backend-derived usage analytics from Karen&apos;s analytics service instead of
              placeholder admin metrics.
            </CardDescription>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => void loadSummary()}
            disabled={isLoading}
          >
            {isLoading ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="mr-2 h-4 w-4" />
            )}
            Refresh
          </Button>
        </CardHeader>

        <CardContent className="space-y-4">
          {authRequired && (
            <Alert className="border-primary/20 bg-primary/5">
              <ShieldAlert className="h-4 w-4 !text-primary" />
              <AlertTitle>Sign In Required</AlertTitle>
              <AlertDescription>
                The analytics routes are live, but this session is not authenticated. Sign in
                to inspect backend usage metrics.
              </AlertDescription>
            </Alert>
          )}

          {accessDenied && (
            <Alert className="border-primary/20 bg-primary/5">
              <ShieldAlert className="h-4 w-4 !text-primary" />
              <AlertTitle>Analytics Access Restricted</AlertTitle>
              <AlertDescription>
                The analytics routes are live, but this session is not authorized to inspect
                backend usage metrics.
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
          ) : authRequired ? (
            <div className="rounded-xl border border-dashed border-border/70 p-6 text-sm text-muted-foreground">
              Analytics require an authenticated session.
            </div>
          ) : accessDenied ? (
            <div className="rounded-xl border border-dashed border-border/70 p-6 text-sm text-muted-foreground">
              Analytics are restricted by backend permissions.
            </div>
          ) : loadError ? (
            <div className="rounded-xl border border-dashed border-border/70 p-6 text-sm text-muted-foreground">
              Analytics could not be loaded from the backend.
            </div>
          ) : summary ? (
            <>
              {summary.timestamp && (
                <div className="rounded-xl border border-border/70 bg-muted/30 p-3 text-xs text-muted-foreground">
                  Generated: {formatDateTime(summary.timestamp)}
                </div>
              )}

              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                {cards.map((card) => {
                  const Icon = card.icon;

                  return (
                    <Card key={card.title} className="border-border/70">
                      <CardHeader className="pb-2">
                        <CardTitle className="flex items-center justify-between gap-3 text-sm font-medium">
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
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-muted-foreground">Peak hours</span>
                      <Badge variant="outline">{formatPeakHours(daily.peak_hours)}</Badge>
                    </div>

                    <div className="flex items-center justify-between gap-3">
                      <span className="text-muted-foreground">Satisfaction</span>
                      <span>{formatSatisfaction(daily.satisfaction)}</span>
                    </div>

                    <div className="flex items-center justify-between gap-3">
                      <span className="text-muted-foreground">Avg session</span>
                      <span>{formatMinutes(daily.average_session_duration)}</span>
                    </div>
                  </CardContent>
                </Card>

                <Card className="border-border/70">
                  <CardHeader>
                    <CardTitle className="text-base">Weekly Window</CardTitle>
                    <CardDescription>Short-horizon trend data.</CardDescription>
                  </CardHeader>

                  <CardContent className="space-y-2 text-sm">
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-muted-foreground">Peak hours</span>
                      <Badge variant="outline">{formatPeakHours(weekly.peak_hours)}</Badge>
                    </div>

                    <div className="flex items-center justify-between gap-3">
                      <span className="text-muted-foreground">Avg session</span>
                      <span>{formatMinutes(weekly.average_session_duration)}</span>
                    </div>

                    <div className="flex items-center justify-between gap-3">
                      <span className="text-muted-foreground">Satisfaction</span>
                      <span>{formatSatisfaction(weekly.satisfaction)}</span>
                    </div>
                  </CardContent>
                </Card>

                <Card className="border-border/70">
                  <CardHeader>
                    <CardTitle className="text-base">Monthly Window</CardTitle>
                    <CardDescription>Longer-horizon system view.</CardDescription>
                  </CardHeader>

                  <CardContent className="space-y-2 text-sm">
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-muted-foreground">Peak hours</span>
                      <Badge variant="outline">{formatPeakHours(monthly.peak_hours)}</Badge>
                    </div>

                    <div className="flex items-center justify-between gap-3">
                      <span className="text-muted-foreground">Satisfaction</span>
                      <span>{formatSatisfaction(monthly.satisfaction)}</span>
                    </div>

                    <div className="flex items-center justify-between gap-3">
                      <span className="text-muted-foreground">Avg session</span>
                      <span>{formatMinutes(monthly.average_session_duration)}</span>
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