/**
 * Token Status Component
 * Shows current token/session expiry and (when supported) allows creating long-lived tokens.
 *
 * In simplified/cookie-only auth mode, long-lived tokens are disabled and a clear notice is shown.
 *
 * Safe defaults:
 * - Works even if /api/auth/status is not implemented (falls back to cookie mode).
 * - Never exposes secrets. Only displays metadata (expiry, issuedAt).
 */

"use client";

import React, { useEffect, useMemo, useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Clock, Shield, RefreshCw, CheckCircle, AlertTriangle } from "lucide-react";
import { isAuthenticated } from "@/lib/auth/session";

export type SessionMode = "cookie" | "token" | "hybrid";
export interface SessionInfo {
  mode: SessionMode;
  issuedAt?: string;     // ISO
  expiresAt?: string;    // ISO
  isLongLived?: boolean;
  username?: string;
  userId?: string;
}

export const TokenStatus: React.FC = () => {
  const [sessionInfo, setSessionInfo] = useState<SessionInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Silent exit if user isn’t logged in
  if (!isAuthenticated()) {
    return null;
  }

  const fetchStatus = useCallback(async () => {
    setLoading(true);
    setMessage(null);
    try {
      // Optional backend endpoint. If missing or fails, we default to cookie mode.
      const res = await fetch("/api/auth/status", { method: "GET", credentials: "include" });
      if (!res.ok) throw new Error("STATUS_UNAVAILABLE");
      const data = (await res.json()) as { success?: boolean; data?: SessionInfo };
      if (!data?.data) throw new Error("INVALID_STATUS");
      setSessionInfo(data.data);
    } catch {
      // Fallback to simplified cookie mode if API not available
      setSessionInfo((prev) => prev ?? { mode: "cookie" });
      setMessage({
        type: "error",
        text: "Token management is unavailable in simplified authentication mode. Using cookie-based session.",
      });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchStatus();
  }, [fetchStatus]);

  const now = Date.now();
  const expiresIn = useMemo(() => {
    if (!sessionInfo?.expiresAt) return null;
    const diff = new Date(sessionInfo.expiresAt).getTime() - now;
    return diff > 0 ? diff : 0;
  }, [sessionInfo?.expiresAt, now]);

  const issuedAtFmt = useMemo(() => {
    if (!sessionInfo?.issuedAt) return null;
    try {
      return new Date(sessionInfo.issuedAt).toLocaleString();
    } catch {
      return sessionInfo.issuedAt;
    }
  }, [sessionInfo?.issuedAt]);

  const expiresAtFmt = useMemo(() => {
    if (!sessionInfo?.expiresAt) return null;
    try {
      return new Date(sessionInfo.expiresAt).toLocaleString();
    } catch {
      return sessionInfo.expiresAt;
    }
  }, [sessionInfo?.expiresAt]);

  const countdown = useMemo(() => {
    if (expiresIn == null) return "Session-managed";
    const secs = Math.floor(expiresIn / 1000);
    const h = Math.floor(secs / 3600);
    const m = Math.floor((secs % 3600) / 60);
    const s = secs % 60;
    return `${h}h ${m}m ${s}s`;
  }, [expiresIn]);

  const modeBadge = useMemo(() => {
    const mode = sessionInfo?.mode ?? "cookie";
    if (mode === "cookie") return <Badge variant="default">Cookie-based</Badge>;
    if (mode === "token") return <Badge variant="secondary">Token-based</Badge>;
    return <Badge variant="outline">Hybrid</Badge>;
  }, [sessionInfo?.mode]);

  const canCreateLongLived = sessionInfo?.mode === "token" || sessionInfo?.mode === "hybrid";

  const handleCreateLongLived = async () => {
    if (!canCreateLongLived) {
      setMessage({
        type: "error",
        text: "Long-lived tokens are disabled in simplified cookie authentication mode.",
      });
      return;
    }
    setMessage(null);
    try {
      const res = await fetch("/api/auth/tokens/long-lived", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
      });
      if (!res.ok) throw new Error("CREATE_FAILED");
      const data = await res.json();
      // SECURITY: do not display the raw token here; backend should show once in a secure modal/download
      setMessage({
        type: "success",
        text: "Long-lived token created. Please store it securely.",
      });
      // Re-read session status in case flags changed
      void fetchStatus();
    } catch {
      setMessage({
        type: "error",
        text: "Failed to create a long-lived token.",
      });
    }
  };

  const handleRefreshSession = async () => {
    setRefreshing(true);
    setMessage(null);
    try {
      const res = await fetch("/api/auth/refresh", {
        method: "POST",
        credentials: "include",
      });
      if (!res.ok) throw new Error("REFRESH_FAILED");
      setMessage({ type: "success", text: "Session refreshed." });
      await fetchStatus();
    } catch {
      setMessage({ type: "error", text: "Session refresh failed." });
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <Card className="w-full max-w-md">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Shield className="h-5 w-5" />
          Session & Token Status
        </CardTitle>
        <CardDescription>
          View your current session details. Long-lived tokens are only available in token/hybrid modes.
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium">Session Mode:</span>
          </div>
          {modeBadge}
        </div>

        <div className="grid gap-2 text-sm">
          {sessionInfo?.username && (
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">User</span>
              <span className="font-medium">{sessionInfo.username}</span>
            </div>
          )}

          {issuedAtFmt && (
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Issued</span>
              <span className="font-medium">{issuedAtFmt}</span>
            </div>
          )}

          {expiresAtFmt && (
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Expires</span>
              <span className="font-medium">{expiresAtFmt}</span>
            </div>
          )}

          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Time Remaining</span>
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <span className="font-medium">{loading ? "…" : countdown}</span>
            </div>
          </div>

          {sessionInfo?.isLongLived != null && (
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Long-Lived</span>
              {sessionInfo.isLongLived ? (
                <Badge variant="secondary" className="inline-flex items-center gap-1">
                  <CheckCircle className="h-3 w-3" />
                  Enabled
                </Badge>
              ) : (
                <Badge variant="outline">Disabled</Badge>
              )}
            </div>
          )}
        </div>

        {message && (
          <Alert variant={message.type === "error" ? "destructive" : "default"}>
            <AlertDescription className="flex items-start gap-2">
              {message.type === "error" ? (
                <AlertTriangle className="h-4 w-4 mt-0.5" />
              ) : (
                <CheckCircle className="h-4 w-4 mt-0.5" />
              )}
              <span>{message.text}</span>
            </AlertDescription>
          </Alert>
        )}

        <div className="flex items-center justify-between gap-2 pt-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefreshSession}
            disabled={loading || refreshing}
            className="inline-flex items-center gap-2"
            aria-label="Refresh session"
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
            Refresh Session
          </Button>

          <Button
            size="sm"
            onClick={handleCreateLongLived}
            disabled={!canCreateLongLived || loading}
            className="inline-flex items-center gap-2"
            aria-label="Create long-lived token"
          >
            <Shield className="h-4 w-4" />
            {canCreateLongLived ? "Create Long-Lived Token" : "Unavailable in Cookie Mode"}
          </Button>
        </div>

        <div className="text-xs text-muted-foreground space-y-1">
          <p>• Authentication uses secure HTTP-only cookies when in cookie mode.</p>
          <p>• Sessions are server-managed; token CRUD is not required in this mode.</p>
          <p>• Long-lived tokens are only available when the backend exposes token mode.</p>
        </div>
      </CardContent>
    </Card>
  );
};
