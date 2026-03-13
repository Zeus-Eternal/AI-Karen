// ui_launchers/KAREN-Theme-Default/src/components/plugins/PluginSecurityManager.tsx
"use client";

import React, { useMemo, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { cn } from "@/lib/utils";
import type { Permission, PluginInfo } from "@/types/plugins";

export type IsolationLevel = "none" | "basic" | "strict" | "maximum";

export interface SecurityPolicy {
  allowNetworkAccess: boolean;
  allowFileSystemAccess: boolean;
  allowSystemCalls: boolean;
  trustedDomains: string[];
  sandboxed: boolean;
  isolationLevel: IsolationLevel;
  resourceLimits: {
    maxMemory: number;
    maxCpu: number;
    maxDisk: number;
    maxNetworkBandwidth: number;
  };
  timeouts: {
    executionTimeout: number;
    networkTimeout: number;
    fileOperationTimeout: number;
  };
}

export interface PluginSecurityManagerProps {
  plugin: PluginInfo;
  onUpdateSecurity: (policy: SecurityPolicy) => Promise<void>;
  onGrantPermission: (permissionId: string) => Promise<void>;
  onRevokePermission: (permissionId: string) => Promise<void>;
  readOnly?: boolean;
}

const isolationLevelCopy: Record<IsolationLevel, string> = {
  none: "No sandboxing applied. Plugin runs with host privileges.",
  basic: "Limited sandboxing. Core APIs allowed, sensitive resources blocked.",
  strict:
    "Strict sandboxing. Only approved APIs and trusted domains are accessible.",
  maximum:
    "Maximum isolation. Plugin runs in a dedicated environment with tight quotas.",
};

const computeInitialPolicy = (plugin: PluginInfo): SecurityPolicy => {
  const manifestPolicy =
    (plugin.manifest.securityPolicy as Partial<SecurityPolicy> | undefined) ??
    {};

  return {
    allowNetworkAccess: manifestPolicy.allowNetworkAccess ?? false,
    allowFileSystemAccess: manifestPolicy.allowFileSystemAccess ?? false,
    allowSystemCalls: manifestPolicy.allowSystemCalls ?? false,
    trustedDomains: manifestPolicy.trustedDomains ?? [],
    sandboxed: plugin.manifest.sandboxed ?? false,
    isolationLevel: (plugin.manifest.sandboxed ? "strict" : "none") satisfies IsolationLevel,
    resourceLimits: {
      maxMemory: manifestPolicy.resourceLimits?.maxMemory ?? 256,
      maxCpu: manifestPolicy.resourceLimits?.maxCpu ?? 50,
      maxDisk: manifestPolicy.resourceLimits?.maxDisk ?? 512,
      maxNetworkBandwidth:
        manifestPolicy.resourceLimits?.maxNetworkBandwidth ?? 25,
    },
    timeouts: {
      executionTimeout: manifestPolicy.timeouts?.executionTimeout ?? 30,
      networkTimeout: manifestPolicy.timeouts?.networkTimeout ?? 15,
      fileOperationTimeout:
        manifestPolicy.timeouts?.fileOperationTimeout ?? 10,
    },
  };
};

const calculateSecurityScore = (
  policy: SecurityPolicy,
  permissions: Permission[],
  grantedPermissions: Set<string>,
): { score: number; label: string; tone: string } => {
  let score = 100;

  if (policy.allowNetworkAccess) score -= 15;
  if (policy.allowFileSystemAccess) score -= 20;
  if (policy.allowSystemCalls) score -= 25;
  if (!policy.sandboxed) score -= 30;
  if (policy.isolationLevel === "basic") score -= 10;
  if (policy.isolationLevel === "none") score -= 20;

  const elevatedPermissions = permissions.filter(
    (permission) =>
      permission.level === "admin" && grantedPermissions.has(permission.id),
  );
  score -= elevatedPermissions.length * 8;

  const clamped = Math.max(0, Math.min(100, score));
  if (clamped >= 80) return { score: clamped, label: "High", tone: "success" };
  if (clamped >= 60)
    return { score: clamped, label: "Medium", tone: "warning" };
  if (clamped >= 40) return { score: clamped, label: "Low", tone: "warning" };
  return { score: clamped, label: "Critical", tone: "destructive" };
};

export const PluginSecurityManager: React.FC<PluginSecurityManagerProps> = ({
  plugin,
  onUpdateSecurity,
  onGrantPermission,
  onRevokePermission,
  readOnly = false,
}) => {
  const [policy, setPolicy] = useState<SecurityPolicy>(() =>
    computeInitialPolicy(plugin),
  );
  const [grantedPermissions, setGrantedPermissions] = useState<Set<string>>(
    () => new Set(plugin.permissions?.filter((p) => p.required).map((p) => p.id)),
  );
  const [saving, setSaving] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{
    tone: "success" | "destructive";
    text: string;
  } | null>(null);
  const [trustedDomainInput, setTrustedDomainInput] = useState("");

  const score = useMemo(
    () => calculateSecurityScore(policy, plugin.permissions ?? [], grantedPermissions),
    [policy, plugin.permissions, grantedPermissions],
  );

  const handlePolicyToggle = (
    key: keyof Pick<
      SecurityPolicy,
      "allowNetworkAccess" | "allowFileSystemAccess" | "allowSystemCalls" | "sandboxed"
    >,
  ) => (value: boolean) => {
    setStatusMessage(null);
    setPolicy((prev) => ({
      ...prev,
      [key]: value,
      isolationLevel:
        key === "sandboxed" && !value ? "none" : prev.isolationLevel,
    }));
  };

  const handleIsolationLevelChange = (level: IsolationLevel) => {
    if (readOnly) return;
    setStatusMessage(null);
    setPolicy((prev) => ({
      ...prev,
      sandboxed: level !== "none",
      isolationLevel: level,
    }));
  };

  const handleResourceChange = (
    key: keyof SecurityPolicy["resourceLimits"],
    value: number,
  ) => {
    if (Number.isNaN(value)) return;
    setPolicy((prev) => ({
      ...prev,
      resourceLimits: { ...prev.resourceLimits, [key]: value },
    }));
  };

  const handleTimeoutChange = (
    key: keyof SecurityPolicy["timeouts"],
    value: number,
  ) => {
    if (Number.isNaN(value)) return;
    setPolicy((prev) => ({
      ...prev,
      timeouts: { ...prev.timeouts, [key]: value },
    }));
  };

  const handleTrustedDomainAdd = () => {
    const trimmed = trustedDomainInput.trim();
    if (!trimmed || policy.trustedDomains.includes(trimmed)) return;
    setPolicy((prev) => ({
      ...prev,
      trustedDomains: [...prev.trustedDomains, trimmed],
    }));
    setTrustedDomainInput("");
  };

  const handleTrustedDomainRemove = (domain: string) => {
    setPolicy((prev) => ({
      ...prev,
      trustedDomains: prev.trustedDomains.filter((item) => item !== domain),
    }));
  };

  const handlePermissionToggle = async (permission: Permission) => {
    const currentlyGranted = grantedPermissions.has(permission.id);
    const nextGranted = new Set(grantedPermissions);
    try {
      if (currentlyGranted) {
        if (permission.required) return;
        await onRevokePermission(permission.id);
        nextGranted.delete(permission.id);
      } else {
        await onGrantPermission(permission.id);
        nextGranted.add(permission.id);
      }
      setGrantedPermissions(nextGranted);
      setStatusMessage({
        tone: "success",
        text: `${permission.name} ${
          currentlyGranted ? "revoked" : "granted"
        } successfully.`,
      });
    } catch (error) {
      console.error(error);
      setStatusMessage({
        tone: "destructive",
        text: `Unable to ${
          currentlyGranted ? "revoke" : "grant"
        } ${permission.name}.`,
      });
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setStatusMessage(null);
    try {
      await onUpdateSecurity(policy);
      setStatusMessage({
        tone: "success",
        text: "Security policy updated.",
      });
    } catch (error) {
      console.error(error);
      setStatusMessage({
        tone: "destructive",
        text: "Failed to update security policy. Please try again.",
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            Security Overview
            <Badge
              variant={
                score.tone === "success"
                  ? "default"
                  : score.tone === "warning"
                  ? "secondary"
                  : "destructive"
              }
            >
              {score.label} · {score.score} / 100
            </Badge>
          </CardTitle>
          <CardDescription>
            Review and adjust how the plugin interacts with sensitive resources.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <PolicyToggle
              label="Allow network access"
              description="Let the plugin make network requests to external services."
              checked={policy.allowNetworkAccess}
              onCheckedChange={handlePolicyToggle("allowNetworkAccess")}
              disabled={readOnly}
            />
            <PolicyToggle
              label="Allow file system access"
              description="Permit reading or writing files on the host machine."
              checked={policy.allowFileSystemAccess}
              onCheckedChange={handlePolicyToggle("allowFileSystemAccess")}
              disabled={readOnly}
            />
            <PolicyToggle
              label="Allow system calls"
              description="Allow direct system commands, which is high risk."
              checked={policy.allowSystemCalls}
              onCheckedChange={handlePolicyToggle("allowSystemCalls")}
              disabled={readOnly}
            />
            <PolicyToggle
              label="Sandboxed execution"
              description="Run the plugin in a restricted sandbox."
              checked={policy.sandboxed}
              onCheckedChange={handlePolicyToggle("sandboxed")}
              disabled={readOnly}
            />
          </div>

          <div>
            <Label className="mb-2 block text-sm font-medium">
              Isolation level
            </Label>
            <div className="flex flex-wrap gap-2">
              {(["none", "basic", "strict", "maximum"] as IsolationLevel[]).map(
                (level) => (
                  <Button
                    key={level}
                    type="button"
                    size="sm"
                    variant={
                      policy.isolationLevel === level ? "default" : "outline"
                    }
                    onClick={() => handleIsolationLevelChange(level)}
                    disabled={readOnly}
                  >
                    {level.charAt(0).toUpperCase() + level.slice(1)}
                  </Button>
                ),
              )}
            </div>
            <p className="mt-2 text-sm text-muted-foreground">
              {isolationLevelCopy[policy.isolationLevel]}
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Resource limits</CardTitle>
          <CardDescription>
            Enforce conservative limits to prevent runaway resource usage.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <NumberField
            label="Memory (MB)"
            value={policy.resourceLimits.maxMemory}
            onChange={(value) => handleResourceChange("maxMemory", value)}
            disabled={readOnly}
          />
          <NumberField
            label="CPU (%)"
            value={policy.resourceLimits.maxCpu}
            onChange={(value) => handleResourceChange("maxCpu", value)}
            disabled={readOnly}
          />
          <NumberField
            label="Disk (MB)"
            value={policy.resourceLimits.maxDisk}
            onChange={(value) => handleResourceChange("maxDisk", value)}
            disabled={readOnly}
          />
          <NumberField
            label="Network bandwidth (MB/s)"
            value={policy.resourceLimits.maxNetworkBandwidth}
            onChange={(value) =>
              handleResourceChange("maxNetworkBandwidth", value)
            }
            disabled={readOnly}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Timeouts</CardTitle>
          <CardDescription>
            Prevent long-running operations from blocking the host application.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <NumberField
            label="Execution timeout (s)"
            value={policy.timeouts.executionTimeout}
            onChange={(value) => handleTimeoutChange("executionTimeout", value)}
            disabled={readOnly}
          />
          <NumberField
            label="Network timeout (s)"
            value={policy.timeouts.networkTimeout}
            onChange={(value) => handleTimeoutChange("networkTimeout", value)}
            disabled={readOnly}
          />
          <NumberField
            label="File operation timeout (s)"
            value={policy.timeouts.fileOperationTimeout}
            onChange={(value) =>
              handleTimeoutChange("fileOperationTimeout", value)
            }
            disabled={readOnly}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Trusted domains</CardTitle>
          <CardDescription>
            Restrict outbound network traffic to vetted destinations.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col gap-2 sm:flex-row">
            <Input
              value={trustedDomainInput}
              onChange={(event) => setTrustedDomainInput(event.target.value)}
              placeholder="api.example.com"
              disabled={readOnly}
            />
            <Button
              type="button"
              onClick={handleTrustedDomainAdd}
              disabled={readOnly || !trustedDomainInput.trim()}
            >
              Add domain
            </Button>
          </div>
          {policy.trustedDomains.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No trusted domains configured. The plugin will be blocked from
              making outbound requests when sandboxed.
            </p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {policy.trustedDomains.map((domain) => (
                <Badge
                  key={domain}
                  variant="outline"
                  className="flex items-center gap-2"
                >
                  {domain}
                  {!readOnly && (
                    <Button
                      type="button"
                      className="text-xs text-destructive"
                      onClick={() => handleTrustedDomainRemove(domain)}
                    >
                      Remove
                    </Button>
                  )}
                </Badge>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Permission grants</CardTitle>
          <CardDescription>
            Fine-tune which plugin permissions are active in this workspace.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {plugin.permissions?.length ? (
            plugin.permissions.map((permission) => {
              const granted = grantedPermissions.has(permission.id);
              return (
                <div
                  key={permission.id}
                  className={cn(
                    "flex flex-col gap-2 rounded-md border p-4 md:flex-row md:items-center md:justify-between",
                    permission.required && "bg-muted/50",
                  )}
                >
                  <div>
                    <p className="text-sm font-medium">{permission.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {permission.description ??
                        "No additional description was provided."}
                    </p>
                    <div className="mt-2 flex flex-wrap items-center gap-2">
                      <Badge variant="outline">{permission.level}</Badge>
                      {permission.required && (
                        <Badge variant="secondary">Required</Badge>
                      )}
                      {granted && <Badge variant="default">Granted</Badge>}
                    </div>
                  </div>
                  <Switch
                    checked={granted}
                    onCheckedChange={() => handlePermissionToggle(permission)}
                    disabled={readOnly || permission.required}
                  />
                </div>
              );
            })
          ) : (
            <p className="text-sm text-muted-foreground">
              This plugin does not request any additional permissions.
            </p>
          )}
        </CardContent>
      </Card>

      {statusMessage && (
        <div role="alert" className={cn("relative w-full rounded-lg border p-4 [&>svg~*]:pl-7 [&>svg+div]:translate-y-[-3px] [&>svg]:absolute [&>svg]:left-4 [&>svg]:top-4 [&>svg]:text-foreground", statusMessage.tone === 'destructive' ? "text-destructive border-destructive/50 dark:border-destructive [&>svg]:text-destructive" : "")}>
          <div className="text-sm [&_p]:leading-relaxed">{statusMessage.text}</div>
        </div>
      )}

      {!readOnly && (
        <div className="flex justify-end">
          <Button onClick={handleSave} disabled={saving}>
            {saving ? "Saving…" : "Save security policy"}
          </Button>
        </div>
      )}
    </div>
  );
};

export interface PolicyToggleProps {
  label: string;
  description: string;
  checked: boolean;
  disabled?: boolean;
  onCheckedChange: (value: boolean) => void;
}

const PolicyToggle: React.FC<PolicyToggleProps> = ({
  label,
  description,
  checked,
  disabled,
  onCheckedChange,
}) => (
  <div className="flex items-start justify-between gap-4 rounded-md border p-4">
    <div>
      <p className="text-sm font-medium">{label}</p>
      <p className="text-sm text-muted-foreground">{description}</p>
    </div>
    <Switch
      checked={checked}
      onCheckedChange={(state) => onCheckedChange(state === true)}
      disabled={disabled}
      aria-label={label}
    />
  </div>
);

export interface NumberFieldProps {
  label: string;
  value: number;
  disabled?: boolean;
  onChange: (value: number) => void;
}

const NumberField: React.FC<NumberFieldProps> = ({
  label,
  value,
  disabled,
  onChange,
}) => (
  <div className="space-y-2">
    <Label className="text-sm font-medium">{label}</Label>
    <Input
      type="number"
      value={value}
      disabled={disabled}
      onChange={(event) => onChange(Number(event.target.value))}
      min={0}
    />
  </div>
);

export default PluginSecurityManager;
