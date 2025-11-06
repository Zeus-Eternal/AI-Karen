"use client";

import React, { useMemo, useState, useEffect } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRBAC } from "@/providers/rbac-provider";
import { auditLogger } from "@/services/audit-logger";
import type { EvilModeSession } from "@/types/rbac";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Progress } from "@/components/ui/progress";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

import {
  Skull,
  Shield,
  AlertTriangle,
  Timer,
  Lock,
  Unlock,
  Eye,
  FileText,
  CheckCircle,
  XCircle,
} from "lucide-react";

export interface EvilModeToggleProps {
  className?: string;
}

export function EvilModeToggle({ className }: EvilModeToggleProps) {
  const {
    isEvilModeEnabled,
    canEnableEvilMode,
    enableEvilMode,
    disableEvilMode,
    evilModeSession,
    evilModeConfig,
  } = useRBAC();

  const [showEnableDialog, setShowEnableDialog] = useState(false);
  const [showDisableDialog, setShowDisableDialog] = useState(false);
  const [justification, setJustification] = useState("");
  const [additionalAuth, setAdditionalAuth] = useState("");
  const [acknowledged, setAcknowledged] = useState(false);

  const queryClient = useQueryClient();

  const enableMutation = useMutation({
    mutationFn: async () => {
      await enableEvilMode(justification.trim(), additionalAuth || undefined);
      await auditLogger.logAuthz(
        "authz:evil_mode_enabled",
        "system",
        "success",
        {
          justification: justification.trim(),
          additionalAuth: Boolean(additionalAuth),
          timeLimit: evilModeConfig?.timeLimit ?? null,
        }
      );
    },
    onSuccess: () => {
      setShowEnableDialog(false);
      setJustification("");
      setAdditionalAuth("");
      setAcknowledged(false);
      queryClient.invalidateQueries({ queryKey: ["rbac"] });
    },
  });

  const disableMutation = useMutation({
    mutationFn: async () => {
      await disableEvilMode();
      const durationMs = evilModeSession
        ? Date.now() - new Date(evilModeSession.startTime).getTime()
        : 0;
      await auditLogger.logAuthz(
        "authz:evil_mode_disabled",
        "system",
        "success",
        {
          sessionDurationMs: durationMs,
        }
      );
    },
    onSuccess: () => {
      setShowDisableDialog(false);
      queryClient.invalidateQueries({ queryKey: ["rbac"] });
    },
  });

  // Keyboard ESC closes any open dialog (extra a11y on top of shadcn defaults)
  useEffect(() => {
    const onEsc = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setShowEnableDialog(false);
        setShowDisableDialog(false);
      }
    };
    document.addEventListener("keydown", onEsc);
    return () => document.removeEventListener("keydown", onEsc);
  }, []);

  // If the user cannot enable evil mode, show a clear block state
  if (!canEnableEvilMode && !isEvilModeEnabled) {
    return (
      <div className={className}>
        <Alert variant="destructive">
          <Shield className="h-4 w-4" />
          <AlertDescription>
            Your role or environment policy forbids enabling Evil Mode.
            Request a temporary elevation or contact an administrator.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className={className}>
      <div className="flex items-center justify-between p-4 border rounded-lg bg-gradient-to-r from-red-50 to-orange-50 dark:from-red-950/20 dark:to-orange-950/20">
        <div className="flex items-center space-x-3">
          <div className="p-3 rounded-full bg-red-100 dark:bg-red-900/30">
            <Skull className="h-6 w-6 text-red-600 dark:text-red-400" aria-hidden />
          </div>
          <div>
            <h3 className="font-semibold text-red-900 dark:text-red-100">
              Evil Mode
            </h3>
            <p className="text-sm text-red-700 dark:text-red-300">
              {isEvilModeEnabled
                ? "Currently active"
                : "Elevated privileges system"}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {isEvilModeEnabled ? (
            <>
              <EvilModeStatus session={evilModeSession} config={evilModeConfig} />
              <Button
                variant="destructive"
                onClick={() => setShowDisableDialog(true)}
                disabled={disableMutation.isPending}
                aria-label="Disable Evil Mode"
              >
                <Lock className="h-4 w-4 mr-2" />
                {disableMutation.isPending ? "Disabling..." : "Disable"}
              </Button>
            </>
          ) : (
            <Button
              variant="destructive"
              onClick={() => setShowEnableDialog(true)}
              disabled={enableMutation.isPending || !canEnableEvilMode}
              aria-label="Enable Evil Mode"
            >
              <Unlock className="h-4 w-4 mr-2" />
              {enableMutation.isPending ? "Enabling..." : "Enable"}
            </Button>
          )}
        </div>
      </div>

      {/* Enable Evil Mode Dialog */}
      <Dialog open={showEnableDialog} onOpenChange={setShowEnableDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center space-x-2 text-red-600">
              <AlertTriangle className="h-5 w-5" aria-hidden />
              <span>Enable Evil Mode</span>
            </DialogTitle>
            <DialogDescription>
              You are about to enable elevated privileges that can bypass normal
              controls. All actions are fully audited.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6">
            {/* Warning Message */}
            {!!evilModeConfig?.warningMessage && (
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" aria-hidden />
                <AlertDescription>
                  {evilModeConfig.warningMessage}
                </AlertDescription>
              </Alert>
            )}

            {/* Security Warnings */}
            <SecurityWarnings />

            {/* Justification */}
            <div className="space-y-2">
              <Label htmlFor="justification">
                Justification <span className="text-red-500">*</span>
              </Label>
              <Textarea
                id="justification"
                placeholder="Provide a detailed justification for enabling Evil Mode..."
                value={justification}
                onChange={(e) => setJustification(e.target.value)}
                required
              />
              <p className="text-xs text-muted-foreground">
                Be specific. This is stored in the audit trail.
              </p>
            </div>

            {/* Additional Authentication */}
            {evilModeConfig?.additionalAuthRequired && (
              <div className="space-y-2">
                <Label htmlFor="additional-auth">
                  Additional Authentication <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="additional-auth"
                  type="password"
                  placeholder="Enter your password or OTP"
                  value={additionalAuth}
                  onChange={(e) => setAdditionalAuth(e.target.value)}
                  required
                />
              </div>
            )}

            {/* Acknowledgment */}
            <div className="flex items-start space-x-2">
              <Input
                type="checkbox"
                id="acknowledge"
                checked={acknowledged}
                onChange={(e) => setAcknowledged(e.target.checked)}
                className="mt-1 h-4 w-4"
              />
              <Label htmlFor="acknowledge" className="text-sm">
                I acknowledge the risks and will use these privileges
                responsibly, only for the stated justification.
              </Label>
            </div>

            {/* Time Limit Warning */}
            {evilModeConfig?.timeLimit && (
              <Alert>
                <Timer className="h-4 w-4" aria-hidden />
                <AlertDescription>
                  Evil Mode will automatically expire after{" "}
                  {evilModeConfig.timeLimit} minutes.
                </AlertDescription>
              </Alert>
            )}
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowEnableDialog(false)}
              disabled={enableMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => enableMutation.mutate()}
              disabled={
                !justification.trim() ||
                (evilModeConfig?.additionalAuthRequired && !additionalAuth) ||
                !acknowledged ||
                enableMutation.isPending
              }
            >
              {enableMutation.isPending ? "Enabling..." : "Enable Evil Mode"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Disable Evil Mode Dialog */}
      <AlertDialog open={showDisableDialog} onOpenChange={setShowDisableDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Disable Evil Mode?</AlertDialogTitle>
            <AlertDialogDescription>
              This will immediately revoke elevated privileges. Any operations
              requiring elevation will be terminated.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={disableMutation.isPending}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={() => disableMutation.mutate()}
              disabled={disableMutation.isPending}
              className="bg-green-600 hover:bg-green-700"
            >
              {disableMutation.isPending ? "Disabling..." : "Disable Evil Mode"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

export interface EvilModeStatusProps {
  session: EvilModeSession | null;
  config: any;
}

function EvilModeStatus({ session, config }: EvilModeStatusProps) {
  if (!session) return null;

  const startTime = useMemo(() => new Date(session.startTime), [session.startTime]);
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000 * 15); // update every 15s
    return () => clearInterval(id);
  }, []);

  const elapsedMs = now.getTime() - startTime.getTime();
  const elapsedMinutes = Math.max(0, Math.floor(elapsedMs / (1000 * 60)));

  const timeLimit = config?.timeLimit || 60;
  const remainingMinutes = Math.max(0, timeLimit - elapsedMinutes);
  const progress = Math.min(100, Math.max(0, (elapsedMinutes / timeLimit) * 100));

  return (
    <div className="flex items-center space-x-3">
      <Badge variant="destructive" className="animate-pulse">
        Active
      </Badge>
      {config?.timeLimit ? (
        <div className="flex items-center space-x-2 text-sm">
          <Timer className="h-4 w-4" aria-hidden />
          <span>{remainingMinutes}m left</span>
        </div>
      ) : null}
      <div className="w-32">
        <Progress value={progress} aria-label="Evil Mode elapsed time" />
      </div>
    </div>
  );
}

function SecurityWarnings() {
  const warnings = [
    {
      icon: AlertTriangle,
      title: "System Integrity Risk",
      description:
        "Evil Mode can bypass normal security controls and potentially damage system integrity.",
    },
    {
      icon: Eye,
      title: "Enhanced Monitoring",
      description:
        "All actions in Evil Mode are logged with detailed audit trails and real-time monitoring.",
    },
    {
      icon: FileText,
      title: "Compliance Impact",
      description:
        "Evil Mode usage may trigger compliance reviews and require additional documentation.",
    },
    {
      icon: Shield,
      title: "Responsibility",
      description:
        "You are personally responsible for all actions taken while Evil Mode is active.",
    },
  ] as const;

  return (
    <div className="space-y-3">
      <h4 className="font-medium text-red-600">Security Warnings</h4>
      <div className="grid gap-3">
        {warnings.map((w, i) => (
          <div
            key={i}
            className="flex items-start space-x-3 p-3 bg-red-50 dark:bg-red-950/20 rounded-lg"
          >
            <w.icon className="h-5 w-5 text-red-500 mt-0.5 flex-shrink-0" aria-hidden />
            <div>
              <h5 className="font-medium text-red-900 dark:text-red-100">
                {w.title}
              </h5>
              <p className="text-sm text-red-700 dark:text-red-300">{w.description}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export interface EvilModeActivityLogProps {
  session: EvilModeSession | null;
}

export function EvilModeActivityLog({ session }: EvilModeActivityLogProps) {
  if (!session) return null;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">Evil Mode Activity Log</h3>
        <Badge variant="destructive">{session.actions.length} actions</Badge>
      </div>

      <div className="space-y-2">
        {session.actions.map((action, index) => {
          const colorWrap =
            action.impact === "critical"
              ? "bg-red-100 dark:bg-red-900/30"
              : action.impact === "high"
              ? "bg-orange-100 dark:bg-orange-900/30"
              : action.impact === "medium"
              ? "bg-yellow-100 dark:bg-yellow-900/30"
              : "bg-blue-100 dark:bg-blue-900/30";
          return (
            <div
              key={index}
              className="flex items-center justify-between p-3 border rounded-lg"
            >
              <div className="flex items-center space-x-3">
                <div className={`p-1 rounded-full ${colorWrap}`}>
                  {action.reversible ? (
                    <CheckCircle className="h-3 w-3 text-green-600" aria-hidden />
                  ) : (
                    <XCircle className="h-3 w-3 text-red-600" aria-hidden />
                  )}
                </div>
                <div>
                  <p className="font-medium">{action.action}</p>
                  <p className="text-sm text-muted-foreground">
                    {action.resource} •{" "}
                    {new Date(action.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <Badge
                  variant={
                    action.impact === "critical"
                      ? "destructive"
                      : action.impact === "high"
                      ? "default"
                      : "secondary"
                  }
                >
                  {action.impact}
                </Badge>
                {!action.reversible && (
                  <Badge variant="outline" className="text-red-600">
                    irreversible
                  </Badge>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {session.actions.length === 0 && (
        <div className="text-center py-8 text-muted-foreground">
          No activity recorded during this session.
        </div>
      )}
    </div>
  );
}
