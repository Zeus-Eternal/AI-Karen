"use client";

/**
 * System Configuration Panel Component (Production-Ready)
 *
 * - Strong runtime validation with Zod
 * - Defensive parsing for numeric inputs (no NaN writes)
 * - Optimistic save with rollback on failure
 * - A11y: labels, aria-live, disabled states, keyboard friendly
 * - Observability hooks (console + window event stubs for Prometheus wiring)
 * - Beforeunload guard on dirty state
 * - Consistent shadcn/ui inputs (no raw <input>/<textarea>)
 * - Minimal re-render churn with useCallback/useMemo
 */

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { z } from "zod";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { useToast } from "@/hooks/use-toast";
import {
  RotateCcw,
  Save,
  AlertTriangle,
  Key,
  Clock,
  Shield,
  Mail,
  Info,
} from "lucide-react";

/** ----- Schema & Types ----- */

const SystemConfigSchema = z.object({
  // Password Policy
  passwordMinLength: z.number().int().min(8).max(128),
  passwordRequireUppercase: z.boolean(),
  passwordRequireLowercase: z.boolean(),
  passwordRequireNumbers: z.boolean(),
  passwordRequireSpecialChars: z.boolean(),
  passwordExpirationDays: z.number().int().min(0).max(365),
  passwordHistoryCount: z.number().int().min(0).max(24),

  // Session Settings
  sessionTimeoutMinutes: z.number().int().min(5).max(1440),
  adminSessionTimeoutMinutes: z.number().int().min(5).max(480),
  maxConcurrentSessions: z.number().int().min(1).max(10),
  sessionExtendOnActivity: z.boolean(),

  // Security Settings
  maxLoginAttempts: z.number().int().min(3).max(10),
  lockoutDurationMinutes: z.number().int().min(1).max(1440),
  requireMfaForAdmins: z.boolean(),
  requireMfaForUsers: z.boolean(),
  allowedIpRanges: z.string(), // newline-delimited CIDRs, validated server-side

  // Email Settings
  emailFromAddress: z.string().email().or(z.literal("")),
  emailFromName: z.string(),
  emailSignature: z.string(),
  enableEmailNotifications: z.boolean(),

  // General Settings
  systemName: z.string(),
  systemDescription: z.string(),
  maintenanceMode: z.boolean(),
  maintenanceMessage: z.string(),
  enableRegistration: z.boolean(),
  enablePasswordReset: z.boolean(),
});

type SystemConfig = z.infer<typeof SystemConfigSchema>;

/** ----- Defaults ----- */

const defaultConfig: SystemConfig = {
  passwordMinLength: 12,
  passwordRequireUppercase: true,
  passwordRequireLowercase: true,
  passwordRequireNumbers: true,
  passwordRequireSpecialChars: true,
  passwordExpirationDays: 90,
  passwordHistoryCount: 5,

  sessionTimeoutMinutes: 60,
  adminSessionTimeoutMinutes: 30,
  maxConcurrentSessions: 3,
  sessionExtendOnActivity: true,

  maxLoginAttempts: 5,
  lockoutDurationMinutes: 15,
  requireMfaForAdmins: true,
  requireMfaForUsers: false,
  allowedIpRanges: "",

  emailFromAddress: "",
  emailFromName: "System Administrator",
  emailSignature: "",
  enableEmailNotifications: true,

  systemName: "Admin Management System",
  systemDescription: "Secure administrative interface",
  maintenanceMode: false,
  maintenanceMessage: "System is currently under maintenance. Please try again later.",
  enableRegistration: true,
  enablePasswordReset: true,
};

/** ----- Helpers ----- */

function safeInt(next: string, fallback: number, min?: number, max?: number) {
  const val = Number.parseInt(next, 10);
  if (Number.isNaN(val)) return fallback;
  if (typeof min === "number" && val < min) return min;
  if (typeof max === "number" && val > max) return max;
  return val;
}

async function fetchJSON<T>(url: string, init?: RequestInit, signal?: AbortSignal): Promise<T> {
  const res = await fetch(url, { ...init, signal });
  if (!res.ok) {
    let detail = "";
    try {
      const j = await res.json();
      detail = j?.message || j?.error || res.statusText;
    } catch {
      detail = res.statusText;
    }
    throw new Error(detail || `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

/** ----- Component ----- */

export default function SystemConfigurationPanel() {
  const { toast } = useToast();

  const [config, setConfig] = useState<SystemConfig>(defaultConfig);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  // Keep a snapshot for optimistic rollback
  const lastSavedRef = useRef<SystemConfig>(defaultConfig);

  // Abort controller for load
  const loadAbortRef = useRef<AbortController | null>(null);

  /** Observability hook stubs (wire to Prometheus later) */
  const recordMetric = useCallback((name: string, payload?: unknown) => {
    // Replace with real observability client
    // eslint-disable-next-line no-console
    console.debug("[OBS] metric:", name, payload ?? {});
    // Example: window.dispatchEvent(new CustomEvent('obs_metric', { detail: { name, payload } }))
  }, []);

  const recordAudit = useCallback((action: string, outcome: "success" | "failure", detail?: unknown) => {
    // eslint-disable-next-line no-console
    console.info("[AUDIT] action:", action, "outcome:", outcome, "detail:", detail ?? {});
    // Example: window.dispatchEvent(new CustomEvent('audit_event', { detail: { action, outcome, detail } }))
  }, []);

  const markDirty = useCallback(() => setHasChanges(true), []);

  /** Load configuration on mount */
  const loadConfiguration = useCallback(async () => {
    setLoading(true);
    loadAbortRef.current?.abort();
    const controller = new AbortController();
    loadAbortRef.current = controller;
    try {
      const data = await fetchJSON<Partial<SystemConfig>>("/api/admin/system/config", undefined, controller.signal);
      // Merge with defaults, then validate at runtime
      const merged = { ...defaultConfig, ...data };
      const parsed = SystemConfigSchema.safeParse(merged);
      if (!parsed.success) {
        recordMetric("config_load_validation_error", parsed.error.flatten());
        throw new Error("Invalid configuration received from server.");
      }
      setConfig(parsed.data);
      lastSavedRef.current = parsed.data;
      setHasChanges(false);
      recordMetric("config_loaded");
    } catch (error) {
      recordMetric("config_load_failed", { error: (error as Error).message });
      recordAudit("config.load", "failure", { error: (error as Error).message });
      toast({
        title: "Error",
        description: "Failed to load system configuration.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }, [recordMetric, recordAudit, toast]);

  useEffect(() => {
    loadConfiguration();
    return () => {
      loadAbortRef.current?.abort();
    };
  }, [loadConfiguration]);

  /** Before unload guard */
  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (hasChanges) {
        e.preventDefault();
        e.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [hasChanges]);

  /** Handlers */
  const handleConfigChange = useCallback(
    <K extends keyof SystemConfig>(key: K, value: SystemConfig[K]) => {
      setConfig((prev) => {
        const next = { ...prev, [key]: value };
        return next;
      });
      markDirty();
    },
    [markDirty]
  );

  const handleResetToDefaults = useCallback(() => {
    if (confirm("Reset all settings to their default values? This cannot be undone.")) {
      setConfig(defaultConfig);
      markDirty();
      recordAudit("config.reset_to_defaults", "success");
    }
  }, [markDirty, recordAudit]);

  const handleSaveConfiguration = useCallback(async () => {
    setSaving(true);
    recordAudit("config.save_attempt", "success", { hasChanges });

    // Validate before send
    const parsed = SystemConfigSchema.safeParse(config);
    if (!parsed.success) {
      setSaving(false);
      recordMetric("config_save_validation_error", parsed.error.flatten());
      toast({
        title: "Validation Error",
        description: "Please review highlighted fields and constraints.",
        variant: "destructive",
      });
      return;
    }

    // Optimistic snapshot
    const snapshot = lastSavedRef.current;
    lastSavedRef.current = parsed.data;

    try {
      await fetchJSON("/api/admin/system/config", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(parsed.data),
      });
      setHasChanges(false);
      toast({
        title: "Success",
        description: "System configuration saved successfully.",
      });
      recordMetric("config_saved");
      recordAudit("config.save", "success");
    } catch (error) {
      // Rollback
      lastSavedRef.current = snapshot;
      setConfig(snapshot);
      setHasChanges(false); // rolled back to last-saved, no pending diff
      recordMetric("config_save_failed", { error: (error as Error).message });
      recordAudit("config.save", "failure", { error: (error as Error).message });
      toast({
        title: "Error",
        description:
          error instanceof Error ? error.message : "Failed to save configuration.",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  }, [config, hasChanges, recordAudit, recordMetric, toast]);

  /** Memoized hints */
  const passwordPolicyHint = useMemo(
    () =>
      `Min ${config.passwordMinLength} chars, ` +
      `${config.passwordRequireUppercase ? "uppercase," : ""} ` +
      `${config.passwordRequireLowercase ? "lowercase," : ""} ` +
      `${config.passwordRequireNumbers ? "number," : ""} ` +
      `${config.passwordRequireSpecialChars ? "special char" : ""}`.replace(/,\s*$/, ""),
    [
      config.passwordMinLength,
      config.passwordRequireUppercase,
      config.passwordRequireLowercase,
      config.passwordRequireNumbers,
      config.passwordRequireSpecialChars,
    ]
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8" aria-live="polite">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
        <span className="ml-2">Loading configuration…</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Actions */}
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold">System Configuration</h3>
          <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
            Manage system-wide settings and policies
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={handleResetToDefaults}
            disabled={saving}
            aria-label="Reset to defaults"
          >
            <RotateCcw className="mr-2 h-4 w-4" />
            Reset
          </Button>
          <Button
            type="button"
            onClick={handleSaveConfiguration}
            disabled={!hasChanges || saving}
            aria-label="Save changes"
          >
            <Save className="mr-2 h-4 w-4" />
            {saving ? "Saving…" : "Save Changes"}
          </Button>
        </div>
      </div>

      {hasChanges && (
        <div
          className="flex items-center gap-2 p-4 bg-yellow-50 border border-yellow-200 rounded-lg sm:p-4 md:p-6"
          role="status"
          aria-live="polite"
        >
          <AlertTriangle className="h-4 w-4 text-yellow-600" />
          <span className="text-sm text-yellow-800 md:text-base lg:text-lg">
            You have unsaved changes. Don&apos;t forget to save your configuration.
          </span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Password Policy */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Key className="h-5 w-5" />
              Password Policy
            </CardTitle>
            <CardDescription>{passwordPolicyHint}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="passwordMinLength">Minimum Password Length</Label>
              <Input
                id="passwordMinLength"
                inputMode="numeric"
                type="number"
                min={8}
                max={128}
                value={config.passwordMinLength}
                onChange={(e) =>
                  handleConfigChange(
                    "passwordMinLength",
                    safeInt(e.target.value, config.passwordMinLength, 8, 128)
                  )
                }
              />
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label htmlFor="requireUppercase">Require Uppercase Letters</Label>
                <Switch
                  id="requireUppercase"
                  checked={config.passwordRequireUppercase}
                  onCheckedChange={(checked) =>
                    handleConfigChange("passwordRequireUppercase", checked)
                  }
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="requireLowercase">Require Lowercase Letters</Label>
                <Switch
                  id="requireLowercase"
                  checked={config.passwordRequireLowercase}
                  onCheckedChange={(checked) =>
                    handleConfigChange("passwordRequireLowercase", checked)
                  }
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="requireNumbers">Require Numbers</Label>
                <Switch
                  id="requireNumbers"
                  checked={config.passwordRequireNumbers}
                  onCheckedChange={(checked) =>
                    handleConfigChange("passwordRequireNumbers", checked)
                  }
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="requireSpecialChars">Require Special Characters</Label>
                <Switch
                  id="requireSpecialChars"
                  checked={config.passwordRequireSpecialChars}
                  onCheckedChange={(checked) =>
                    handleConfigChange("passwordRequireSpecialChars", checked)
                  }
                />
              </div>
            </div>

            <Separator />

            <div>
              <Label htmlFor="passwordExpirationDays">Password Expiration (Days)</Label>
              <Input
                id="passwordExpirationDays"
                type="number"
                inputMode="numeric"
                min={0}
                max={365}
                value={config.passwordExpirationDays}
                onChange={(e) =>
                  handleConfigChange(
                    "passwordExpirationDays",
                    safeInt(e.target.value, config.passwordExpirationDays, 0, 365)
                  )
                }
              />
              <p className="text-xs text-muted-foreground mt-1 sm:text-sm md:text-base">
                0 disables expiration.
              </p>
            </div>

            <div>
              <Label htmlFor="passwordHistoryCount">Password History Count</Label>
              <Input
                id="passwordHistoryCount"
                type="number"
                inputMode="numeric"
                min={0}
                max={24}
                value={config.passwordHistoryCount}
                onChange={(e) =>
                  handleConfigChange(
                    "passwordHistoryCount",
                    safeInt(e.target.value, config.passwordHistoryCount, 0, 24)
                  )
                }
              />
              <p className="text-xs text-muted-foreground mt-1 sm:text-sm md:text-base">
                Prevents reuse of the last N passwords.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Session Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Session Settings
            </CardTitle>
            <CardDescription>User and admin session controls</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="sessionTimeout">User Session Timeout (Minutes)</Label>
              <Input
                id="sessionTimeout"
                type="number"
                inputMode="numeric"
                min={5}
                max={1440}
                value={config.sessionTimeoutMinutes}
                onChange={(e) =>
                  handleConfigChange(
                    "sessionTimeoutMinutes",
                    safeInt(e.target.value, config.sessionTimeoutMinutes, 5, 1440)
                  )
                }
              />
            </div>

            <div>
              <Label htmlFor="adminSessionTimeout">Admin Session Timeout (Minutes)</Label>
              <Input
                id="adminSessionTimeout"
                type="number"
                inputMode="numeric"
                min={5}
                max={480}
                value={config.adminSessionTimeoutMinutes}
                onChange={(e) =>
                  handleConfigChange(
                    "adminSessionTimeoutMinutes",
                    safeInt(e.target.value, config.adminSessionTimeoutMinutes, 5, 480)
                  )
                }
              />
            </div>

            <div>
              <Label htmlFor="maxConcurrentSessions">Max Concurrent Sessions</Label>
              <Input
                id="maxConcurrentSessions"
                type="number"
                inputMode="numeric"
                min={1}
                max={10}
                value={config.maxConcurrentSessions}
                onChange={(e) =>
                  handleConfigChange(
                    "maxConcurrentSessions",
                    safeInt(e.target.value, config.maxConcurrentSessions, 1, 10)
                  )
                }
              />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="sessionExtendOnActivity">Extend Session on Activity</Label>
              <Switch
                id="sessionExtendOnActivity"
                checked={config.sessionExtendOnActivity}
                onCheckedChange={(checked) =>
                  handleConfigChange("sessionExtendOnActivity", checked)
                }
              />
            </div>
          </CardContent>
        </Card>

        {/* Security Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Security Settings
            </CardTitle>
            <CardDescription>Login, lockout, MFA, and IP controls</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="maxLoginAttempts">Max Login Attempts</Label>
              <Input
                id="maxLoginAttempts"
                type="number"
                inputMode="numeric"
                min={3}
                max={10}
                value={config.maxLoginAttempts}
                onChange={(e) =>
                  handleConfigChange(
                    "maxLoginAttempts",
                    safeInt(e.target.value, config.maxLoginAttempts, 3, 10)
                  )
                }
              />
            </div>

            <div>
              <Label htmlFor="lockoutDuration">Lockout Duration (Minutes)</Label>
              <Input
                id="lockoutDuration"
                type="number"
                inputMode="numeric"
                min={1}
                max={1440}
                value={config.lockoutDurationMinutes}
                onChange={(e) =>
                  handleConfigChange(
                    "lockoutDurationMinutes",
                    safeInt(e.target.value, config.lockoutDurationMinutes, 1, 1440)
                  )
                }
              />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="requireMfaForAdmins">Require MFA for Admins</Label>
              <Switch
                id="requireMfaForAdmins"
                checked={config.requireMfaForAdmins}
                onCheckedChange={(checked) =>
                  handleConfigChange("requireMfaForAdmins", checked)
                }
              />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="requireMfaForUsers">Require MFA for Users</Label>
              <Switch
                id="requireMfaForUsers"
                checked={config.requireMfaForUsers}
                onCheckedChange={(checked) =>
                  handleConfigChange("requireMfaForUsers", checked)
                }
              />
            </div>

            <div>
              <Label htmlFor="allowedIpRanges">Allowed IP Ranges (Optional)</Label>
              <Textarea
                id="allowedIpRanges"
                placeholder={"192.168.1.0/24\n10.0.0.0/8"}
                value={config.allowedIpRanges}
                onChange={(e) => handleConfigChange("allowedIpRanges", e.target.value)}
                rows={3}
              />
              <p className="text-xs text-muted-foreground mt-1 sm:text-sm md:text-base">
                One CIDR per line. Leave empty to allow all IPs. (Server validates syntax)
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Email Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Mail className="h-5 w-5" />
              Email Settings
            </CardTitle>
            <CardDescription>Notification sender identity & signature</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <Label htmlFor="enableEmailNotifications">Enable Email Notifications</Label>
              <Switch
                id="enableEmailNotifications"
                checked={config.enableEmailNotifications}
                onCheckedChange={(checked) =>
                  handleConfigChange("enableEmailNotifications", checked)
                }
              />
            </div>

            <div>
              <Label htmlFor="emailFromAddress">From Email Address</Label>
              <Input
                id="emailFromAddress"
                type="email"
                placeholder="noreply@example.com"
                value={config.emailFromAddress}
                onChange={(e) => handleConfigChange("emailFromAddress", e.target.value)}
              />
            </div>

            <div>
              <Label htmlFor="emailFromName">From Name</Label>
              <Input
                id="emailFromName"
                placeholder="System Administrator"
                value={config.emailFromName}
                onChange={(e) => handleConfigChange("emailFromName", e.target.value)}
              />
            </div>

            <div>
              <Label htmlFor="emailSignature">Email Signature</Label>
              <Textarea
                id="emailSignature"
                placeholder={"Best regards,\nThe Admin Team"}
                value={config.emailSignature}
                onChange={(e) => handleConfigChange("emailSignature", e.target.value)}
                rows={3}
              />
            </div>
          </CardContent>
        </Card>

        {/* General Settings */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Info className="h-5 w-5" />
              General Settings
            </CardTitle>
            <CardDescription>Branding, registration, and maintenance</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="systemName">System Name</Label>
                <Input
                  id="systemName"
                  placeholder="Admin Management System"
                  value={config.systemName}
                  onChange={(e) => handleConfigChange("systemName", e.target.value)}
                />
              </div>

              <div>
                <Label htmlFor="systemDescription">System Description</Label>
                <Input
                  id="systemDescription"
                  placeholder="Secure administrative interface"
                  value={config.systemDescription}
                  onChange={(e) => handleConfigChange("systemDescription", e.target.value)}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex items-center justify-between">
                <Label htmlFor="enableRegistration">Enable User Registration</Label>
                <Switch
                  id="enableRegistration"
                  checked={config.enableRegistration}
                  onCheckedChange={(checked) =>
                    handleConfigChange("enableRegistration", checked)
                  }
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="enablePasswordReset">Enable Password Reset</Label>
                <Switch
                  id="enablePasswordReset"
                  checked={config.enablePasswordReset}
                  onCheckedChange={(checked) =>
                    handleConfigChange("enablePasswordReset", checked)
                  }
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="maintenanceMode">Maintenance Mode</Label>
                <Switch
                  id="maintenanceMode"
                  checked={config.maintenanceMode}
                  onCheckedChange={(checked) =>
                    handleConfigChange("maintenanceMode", checked)
                  }
                />
              </div>
            </div>

            {config.maintenanceMode && (
              <div>
                <Label htmlFor="maintenanceMessage">Maintenance Message</Label>
                <Textarea
                  id="maintenanceMessage"
                  placeholder="System is currently under maintenance…"
                  value={config.maintenanceMessage}
                  onChange={(e) => handleConfigChange("maintenanceMessage", e.target.value)}
                  rows={2}
                />
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
