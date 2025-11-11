"use client";

import React, { useMemo, useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type {
  PluginConfig,
  PluginInfo,
  PluginMarketplaceEntry,
} from "@/types/plugins";
import { EnhancedPluginMarketplace } from "./EnhancedPluginMarketplace";
import { PluginAuditLogger } from "./PluginAuditLogger";
import {
  PluginSecurityManager,
  type SecurityPolicy,
} from "./PluginSecurityManager";
import { DynamicPluginConfigForm } from "./DynamicPluginConfigForm";

export interface ValidationError {
  field: string;
  message: string;
  severity: "error" | "warning";
}

export interface PluginConfigurationSecurityIntegrationProps {
  plugin: PluginInfo;
  onClose: () => void;
  onSaveConfiguration: (config: PluginConfig) => Promise<void>;
  onUpdateSecurity: (policy: SecurityPolicy) => Promise<void>;
  onGrantPermission: (permissionId: string) => Promise<void>;
  onRevokePermission: (permissionId: string) => Promise<void>;
  onInstallFromMarketplace: (
    plugin: PluginMarketplaceEntry,
  ) => Promise<void>;
  onPurchasePlugin?: (plugin: PluginMarketplaceEntry) => Promise<void>;
  onExportAuditLog?: (format: "csv" | "json" | "pdf") => void;
  onGenerateReport?: (type: "compliance" | "security" | "activity") => void;
  readOnly?: boolean;
}

const riskLabel = (riskScore: number) => {
  if (riskScore >= 80) return { label: "High", tone: "destructive" as const };
  if (riskScore >= 50) return { label: "Medium", tone: "secondary" as const };
  return { label: "Low", tone: "default" as const };
};

const PluginConfigurationSecurityIntegration: React.FC<
  PluginConfigurationSecurityIntegrationProps
> = ({
  plugin,
  onClose,
  onSaveConfiguration,
  onUpdateSecurity,
  onGrantPermission,
  onRevokePermission,
  onInstallFromMarketplace,
  onPurchasePlugin,
  onExportAuditLog,
  onGenerateReport,
  readOnly = false,
}) => {
  const [activeTab, setActiveTab] =
    useState<"configuration" | "security" | "audit" | "marketplace">(
      "configuration",
    );
  const [showMarketplace, setShowMarketplace] = useState(false);
  const [configurationDirty, setConfigurationDirty] = useState(false);
  const [securityDirty, setSecurityDirty] = useState(false);
  const [lastSavedAt, setLastSavedAt] = useState<Date | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const validationRules = useMemo(
    () => plugin.manifest.configSchema ?? [],
    [plugin.manifest.configSchema],
  );

  const validateConfiguration = (config: PluginConfig): ValidationError[] => {
    const errors: ValidationError[] = [];
    validationRules.forEach((field) => {
      if (field.required && !config[field.key]) {
        errors.push({
          field: field.key,
          message: `${field.label ?? field.key} is required`,
          severity: "error",
        });
      }
    });
    return errors;
  };

  const handleSaveConfiguration = async (config: PluginConfig) => {
    setStatusMessage(null);
    try {
      await onSaveConfiguration(config);
      setConfigurationDirty(false);
      setLastSavedAt(new Date());
      setStatusMessage("Configuration saved.");
    } catch (error) {
      console.error(error);
      setStatusMessage("Failed to save configuration.");
    }
  };

  const handleSaveSecurity = async (policy: SecurityPolicy) => {
    setStatusMessage(null);
    try {
      await onUpdateSecurity(policy);
      setSecurityDirty(false);
      setLastSavedAt(new Date());
      setStatusMessage("Security policy updated.");
    } catch (error) {
      console.error(error);
      setStatusMessage("Failed to update security policy.");
    }
  };

  const riskScore = useMemo(() => {
    const policy = plugin.manifest.securityPolicy ?? {
      allowNetworkAccess: false,
      allowFileSystemAccess: false,
      allowSystemCalls: false,
    };
    let score = 0;
    if (policy.allowNetworkAccess) score += 30;
    if (policy.allowFileSystemAccess) score += 25;
    if (policy.allowSystemCalls) score += 35;
    score += (plugin.manifest.permissions ?? []).filter(
      (permission) => permission.level === "admin",
    ).length * 10;
    return Math.min(score, 100);
  }, [plugin.manifest.permissions, plugin.manifest.securityPolicy]);

  const { label: riskLabelText, tone: riskTone } = riskLabel(riskScore);

  return (
    <>
      <div className="space-y-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Plugin management</h1>
            <p className="text-sm text-muted-foreground">
              Configure, secure, and audit the {plugin.name} plugin.
            </p>
          </div>
          <div className="flex items-center gap-2">
            {lastSavedAt && (
              <span className="text-sm text-muted-foreground">
                Last saved {lastSavedAt.toLocaleTimeString()}
              </span>
            )}
            <Button variant="outline" size="sm" onClick={() => onClose()}>
              Back
            </Button>
          </div>
        </div>

        <Card>
          <CardHeader className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                {plugin.name}
                <Badge variant={plugin.status === "active" ? "default" : "secondary"}>
                  {plugin.status}
                </Badge>
              </CardTitle>
              <CardDescription>{plugin.manifest.description}</CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant={riskTone}>
                Security risk · {riskLabelText}
              </Badge>
              <Badge variant="outline">v{plugin.version}</Badge>
            </div>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <InfoItem label="Category" value={plugin.manifest.category ?? "Unknown"} />
            <InfoItem label="Author" value={plugin.manifest.author?.name ?? "Unknown"} />
            <InfoItem
              label="Permissions"
              value={String(plugin.manifest.permissions?.length ?? 0)}
            />
            <InfoItem
              label="Sandboxed"
              value={plugin.manifest.sandboxed ? "Yes" : "No"}
            />
          </CardContent>
        </Card>

        {(configurationDirty || securityDirty) && (
          <Alert>
            <AlertDescription>
              You have unsaved {configurationDirty ? "configuration" : "security"} changes.
            </AlertDescription>
          </Alert>
        )}

        {statusMessage && (
          <Alert>
            <AlertDescription>{statusMessage}</AlertDescription>
          </Alert>
        )}

        <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as typeof activeTab)}>
          <TabsList className="grid grid-cols-4">
            <TabsTrigger value="configuration">Configuration</TabsTrigger>
            <TabsTrigger value="security">Security</TabsTrigger>
            <TabsTrigger value="audit">Audit</TabsTrigger>
            <TabsTrigger value="marketplace">Marketplace</TabsTrigger>
          </TabsList>

          <TabsContent value="configuration" className="space-y-4">
            <DynamicPluginConfigForm
              plugin={plugin}
              initialConfig={plugin.config}
              onSave={handleSaveConfiguration}
              onValidate={validateConfiguration}
              onPreview={() => undefined}
              readOnly={readOnly}
            />
            {!readOnly && (
              <Button
                variant="outline"
                onClick={() => setShowMarketplace(true)}
                className="self-start"
              >
                Browse marketplace
              </Button>
            )}
          </TabsContent>

          <TabsContent value="security">
            <PluginSecurityManager
              plugin={plugin}
              onUpdateSecurity={handleSaveSecurity}
              onGrantPermission={onGrantPermission}
              onRevokePermission={onRevokePermission}
              readOnly={readOnly}
            />
          </TabsContent>

          <TabsContent value="audit">
            <PluginAuditLogger
              plugin={plugin}
              onExportAuditLog={onExportAuditLog}
              onGenerateReport={onGenerateReport}
            />
          </TabsContent>

          <TabsContent value="marketplace">
            <Card>
              <CardHeader>
                <CardTitle>Marketplace</CardTitle>
                <CardDescription>
                  Discover additional plugins compatible with your environment.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button onClick={() => setShowMarketplace(true)}>
                  Open marketplace
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>

      <Dialog open={showMarketplace} onOpenChange={setShowMarketplace}>
        <DialogContent className="max-h-[90vh] w-full max-w-4xl overflow-hidden">
          <DialogHeader>
            <DialogTitle>Plugin marketplace</DialogTitle>
          </DialogHeader>
          <EnhancedPluginMarketplace
            onClose={() => setShowMarketplace(false)}
            onInstall={onInstallFromMarketplace}
            onPurchase={onPurchasePlugin}
          />
        </DialogContent>
      </Dialog>
    </>
  );
};

export interface InfoItemProps {
  label: string;
  value: string;
}

const InfoItem: React.FC<InfoItemProps> = ({ label, value }) => (
  <div>
    <p className="text-sm text-muted-foreground">{label}</p>
    <p className="text-base font-medium">{value}</p>
  </div>
);

export { PluginConfigurationSecurityIntegration };
