"use client";

import React, { useMemo, useRef, useState } from "react";
import { ErrorBoundary } from "@/components/error-handling/ErrorBoundary";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Select,
  SelectTrigger,
  SelectContent,
  SelectItem,
  SelectValue,
} from "@/components/ui/select";
import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from "@/components/ui/collapsible";

import {
  AlertTriangle,
  Cpu,
  Copy,
  Download,
  Eye,
  EyeOff,
  Globe,
  HardDrive,
  Info,
  Minus,
  Network,
  Plus,
  RefreshCw,
  RotateCcw,
  Save,
  Search,
  Settings,
  Upload,
  Shield,
} from "lucide-react";

import type { PluginInfo, PluginConfig, PluginConfigField } from "@/types/plugins";

/**
 * Plugin Configuration Manager Component
 * Dynamic plugin configuration forms based on plugin manifests.
 * Production-ready: shadcn-correct, typed validation, JSON import/export, collapsible sections.
 */

export interface ValidationError {
  field: string;
  message: string;
}

export interface ConfigurationSection {
  id: string;
  name: string;
  description: string;
  fields: PluginConfigField[];
  collapsed?: boolean;
}

export interface PluginConfigurationManagerProps {
  plugin: PluginInfo;
  onSave: (config: PluginConfig) => Promise<void>;
  onReset: () => Promise<void>;
  onExport?: (config: PluginConfig) => void;
  onImport?: (config: PluginConfig) => void;
  readOnly?: boolean;
}

export const PluginConfigurationManager: React.FC<PluginConfigurationManagerProps> = ({
  plugin,
  onSave,
  onReset,
  onExport,
  onImport,
  readOnly = false,
}) => {
  const [config, setConfig] = useState<PluginConfig>(plugin.config || {});
  const [originalConfig] = useState<PluginConfig>(plugin.config || {});
  const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);
  const [saving, setSaving] = useState(false);
  const [showPasswords, setShowPasswords] = useState<Record<string, boolean>>({});
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(["general"]));
  const [searchQuery, setSearchQuery] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Group configuration fields into sections (by prefix before first '.')
  const sections: ConfigurationSection[] = useMemo(() => {
    const schema = plugin.manifest.configSchema || [];
    const sectionMap = new Map<string, PluginConfigField[]>();

    for (const field of schema) {
      const section = field.key.includes(".") ? field.key.split(".")[0] : "general";
      if (!sectionMap.has(section)) sectionMap.set(section, []);
      sectionMap.get(section)!.push(field);
    }

    return Array.from(sectionMap.entries()).map(([id, fields]) => ({
      id,
      name: id.charAt(0).toUpperCase() + id.slice(1).replace(/([A-Z])/g, " $1"),
      description: `Configure ${id} settings for ${plugin.name}`,
      fields,
    }));
  }, [plugin.manifest.configSchema, plugin.name]);

  // Filter fields based on search query
  const filteredSections = useMemo(() => {
    if (!searchQuery) return sections;
    const q = searchQuery.toLowerCase();
    return sections
      .map((section) => ({
        ...section,
        fields: section.fields.filter(
          (field) =>
            field.label.toLowerCase().includes(q) ||
            field.key.toLowerCase().includes(q) ||
            (field.description && field.description.toLowerCase().includes(q))
        ),
      }))
      .filter((s) => s.fields.length > 0);
  }, [sections, searchQuery]);

  const validateField = (field: PluginConfigField, value: any): string | null => {
    if (field.required && (value === undefined || value === null || value === "")) {
      return `${field.label} is required`;
    }
    if (field.validation) {
      const { min, max, pattern, custom } = field.validation;
      if (field.type === "number" && typeof value === "number") {
        if (min !== undefined && value < min) return `${field.label} must be at least ${min}`;
        if (max !== undefined && value > max) return `${field.label} must be at most ${max}`;
      }
      if (field.type === "string" && typeof value === "string") {
        if (pattern && !new RegExp(pattern).test(value)) return `${field.label} format is invalid`;
      }
      if (custom) {
        const msg = custom(value);
        if (msg) return msg;
      }
    }
    return null;
  };

  const validateConfig = (): ValidationError[] => {
    const errors: ValidationError[] = [];
    for (const field of plugin.manifest.configSchema || []) {
      const value = (config as any)[field.key];
      const error = validateField(field, value);
      if (error) errors.push({ field: field.key, message: error });
    }
    return errors;
  };

  const handleFieldChange = (fieldKey: string, value: any) => {
    setConfig((prev) => ({ ...prev, [fieldKey]: value }));
    // Clear validation error for this field
    setValidationErrors((prev) => prev.filter((e) => e.field !== fieldKey));
  };

  const handleSave = async () => {
    const errors = validateConfig();
    if (errors.length > 0) {
      setValidationErrors(errors);
      return;
    }
    setSaving(true);
    try {
      await onSave(config);
      setValidationErrors([]);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    setConfig(originalConfig);
    setValidationErrors([]);
    await onReset();
  };

  const handleExport = () => {
    onExport?.(config);
  };

  const handleImport = (importedConfig: PluginConfig) => {
    setConfig(importedConfig);
    onImport?.(importedConfig);
  };

  const triggerImport = () => fileInputRef.current?.click();

  const togglePasswordVisibility = (fieldKey: string) => {
    setShowPasswords((prev) => ({ ...prev, [fieldKey]: !prev[fieldKey] }));
  };

  const toggleSection = (sectionId: string) => {
    setExpandedSections((prev) => {
      const next = new Set(prev);
      if (next.has(sectionId)) next.delete(sectionId);
      else next.add(sectionId);
      return next;
    });
  };

  const renderField = (field: PluginConfigField) => {
    const value = (config as any)[field.key] ?? field.default ?? (field.type === "boolean" ? false : "");
    const error = validationErrors.find((e) => e.field === field.key);
    const isPassword = field.type === "password";
    const showPassword = !!showPasswords[field.key];
    const fieldId = `field-${field.key}`;

    return (
      <div key={field.key} className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor={fieldId} className="flex items-center gap-2">
            {field.label}
            {field.required && <span className="text-destructive">*</span>}
            {field.description && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button variant="ghost" size="icon" className="h-6 w-6">
                      <Info className="w-3 h-3 text-muted-foreground" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p className="max-w-xs">{field.description}</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )}
          </Label>

          {isPassword && (
            <Button type="button" variant="ghost" size="sm" onClick={() => togglePasswordVisibility(field.key)}>
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </Button>
          )}
        </div>

        {/* FIELD RENDERERS */}
        {field.type === "string" && (
          <Input
            id={fieldId}
            type={isPassword && !showPassword ? "password" : "text"}
            value={value as string}
            onChange={(e) => handleFieldChange(field.key, e.target.value)}
            placeholder={field.default?.toString()}
            disabled={readOnly}
            className={error ? "border-destructive" : ""}
          />
        )}

        {field.type === "number" && (
          <Input
            id={fieldId}
            type="number"
            value={value as number}
            onChange={(e) => handleFieldChange(field.key, Number(e.target.value))}
            min={field.validation?.min}
            max={field.validation?.max}
            disabled={readOnly}
            className={error ? "border-destructive" : ""}
          />
        )}

        {field.type === "boolean" && (
          <div className="flex items-center space-x-2">
            <Switch
              id={fieldId}
              checked={Boolean(value)}
              onCheckedChange={(checked) => handleFieldChange(field.key, checked)}
              disabled={readOnly}
            />
            <Label
              htmlFor={fieldId}
              className="text-sm text-muted-foreground md:text-base lg:text-lg"
            >
              {value ? "Enabled" : "Disabled"}
            </Label>
          </div>
        )}

        {field.type === "select" && field.options && (
          <Select
            value={(value as string) ?? ""}
            onValueChange={(newValue) => handleFieldChange(field.key, newValue)}
            disabled={readOnly}
          >
            <SelectTrigger className={error ? "border-destructive" : ""}>
              <SelectValue placeholder="Select an option" />
            </SelectTrigger>
            <SelectContent>
              {field.options.map((opt) => (
                <SelectItem key={opt.value.toString()} value={opt.value.toString()}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}

        {field.type === "multiselect" && field.options && (
          <div className="space-y-2">
            {field.options.map((opt) => {
              const arr = Array.isArray(value) ? value : [];
              const checked = arr.includes(opt.value);
              return (
                <div key={opt.value.toString()} className="flex items-center space-x-2">
                  <Checkbox
                    id={`${fieldId}-${opt.value}`}
                    checked={checked}
                    onCheckedChange={(ck) => {
                      const current = Array.isArray(value) ? [...value] : [];
                      if (ck) handleFieldChange(field.key, Array.from(new Set([...current, opt.value])));
                      else handleFieldChange(field.key, current.filter((v: any) => v !== opt.value));
                    }}
                    disabled={readOnly}
                  />
                  <Label htmlFor={`${fieldId}-${opt.value}`} className="text-sm md:text-base lg:text-lg">
                    {opt.label}
                  </Label>
                </div>
              );
            })}
          </div>
        )}

        {field.type === "json" && (
          <Textarea
            id={fieldId}
            value={typeof value === "string" ? value : JSON.stringify(value, null, 2)}
            onChange={(e) => {
              const text = e.target.value;
              try {
                const parsed = JSON.parse(text);
                handleFieldChange(field.key, parsed);
              } catch {
                handleFieldChange(field.key, text);
              }
            }}
            rows={6}
            placeholder="Enter JSON configuration"
            disabled={readOnly}
            className={`font-mono text-sm ${error ? "border-destructive" : ""}`}
          />
        )}

        {error && (
          <Alert variant="destructive" className="py-2">
            <AlertTriangle className="w-4 h-4" />
            <AlertDescription className="text-sm md:text-base lg:text-lg">
              {error.message}
            </AlertDescription>
          </Alert>
        )}
      </div>
    );
  };

  const hasChanges = JSON.stringify(config) !== JSON.stringify(originalConfig);

  return (
    <ErrorBoundary fallback={<div>Something went wrong in PluginConfigurationManager.</div>}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold">Plugin Configuration</h2>
            <p className="text-muted-foreground">Configure settings for {plugin.name}</p>
          </div>

          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search settings..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 w-64"
              />
            </div>
            <Button variant="outline" size="sm" onClick={() => setShowAdvanced((v) => !v)}>
              <Settings className="w-4 h-4 mr-2" />
              {showAdvanced ? "Simple" : "Advanced"}
            </Button>
            {onExport && (
              <Button variant="outline" size="sm" onClick={handleExport}>
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
            )}
          </div>
        </div>

        {/* Status */}
        {hasChanges && (
          <Alert>
            <Info className="w-4 h-4" />
            <AlertDescription>You have unsaved changes. Don’t forget to save.</AlertDescription>
          </Alert>
        )}

        {validationErrors.length > 0 && (
          <Alert variant="destructive">
            <AlertTriangle className="w-4 h-4" />
            <AlertDescription>
              Please fix {validationErrors.length} configuration error
              {validationErrors.length !== 1 ? "s" : ""} before saving.
            </AlertDescription>
          </Alert>
        )}

        <Tabs defaultValue="configuration" className="space-y-4">
          <TabsList>
            <TabsTrigger value="configuration">Configuration</TabsTrigger>
            <TabsTrigger value="security">Security</TabsTrigger>
            <TabsTrigger value="advanced">Advanced</TabsTrigger>
          </TabsList>

          {/* CONFIGURATION */}
          <TabsContent value="configuration" className="space-y-4">
            {filteredSections.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <Settings className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <h3 className="text-lg font-medium mb-2">No Configuration Available</h3>
                  <p className="text-muted-foreground">
                    This plugin doesn’t have any configurable settings.
                  </p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-4">
                {filteredSections.map((section) => (
                  <Card key={section.id}>
                    <Collapsible
                      open={expandedSections.has(section.id)}
                      onOpenChange={() => toggleSection(section.id)}
                    >
                      <CollapsibleTrigger asChild>
                        <CardHeader className="cursor-pointer hover:bg-muted/50">
                          <div className="flex items-center justify-between">
                            <div>
                              <CardTitle className="text-lg">{section.name}</CardTitle>
                              <CardDescription>{section.description}</CardDescription>
                            </div>
                            <div className="flex items-center gap-2">
                              <Badge variant="outline">
                                {section.fields.length} setting
                                {section.fields.length !== 1 ? "s" : ""}
                              </Badge>
                              {expandedSections.has(section.id) ? (
                                <Minus className="w-4 h-4" />
                              ) : (
                                <Plus className="w-4 h-4" />
                              )}
                            </div>
                          </div>
                        </CardHeader>
                      </CollapsibleTrigger>
                      <CollapsibleContent>
                        <CardContent className="space-y-6">
                          {section.fields.map((f) => renderField(f))}
                        </CardContent>
                      </CollapsibleContent>
                    </Collapsible>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* SECURITY */}
          <TabsContent value="security" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="w-5 h-5" />
                  Security
                </CardTitle>
                <CardDescription>Sandboxing and permissions details.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <h4 className="font-medium">Security Policy</h4>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Network className="w-4 h-4" />
                          <span className="text-sm md:text-base lg:text-lg">Network Access</span>
                        </div>
                        <Badge
                          variant={
                            plugin.manifest.securityPolicy.allowNetworkAccess ? "default" : "secondary"
                          }
                        >
                          {plugin.manifest.securityPolicy.allowNetworkAccess ? "Allowed" : "Blocked"}
                        </Badge>
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <HardDrive className="w-4 h-4" />
                          <span className="text-sm md:text-base lg:text-lg">File System Access</span>
                        </div>
                        <Badge
                          variant={
                            plugin.manifest.securityPolicy.allowFileSystemAccess ? "default" : "secondary"
                          }
                        >
                          {plugin.manifest.securityPolicy.allowFileSystemAccess ? "Allowed" : "Blocked"}
                        </Badge>
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Cpu className="w-4 h-4" />
                          <span className="text-sm md:text-base lg:text-lg">System Calls</span>
                        </div>
                        <Badge
                          variant={
                            plugin.manifest.securityPolicy.allowSystemCalls ? "default" : "secondary"
                          }
                        >
                          {plugin.manifest.securityPolicy.allowSystemCalls ? "Allowed" : "Blocked"}
                        </Badge>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h4 className="font-medium">Sandboxing</h4>
                    <div className="flex items-center justify-between">
                      <span className="text-sm md:text-base lg:text-lg">Sandboxed Execution</span>
                      <Badge variant={plugin.manifest.sandboxed ? "default" : "destructive"}>
                        {plugin.manifest.sandboxed ? "Enabled" : "Disabled"}
                      </Badge>
                    </div>

                    {plugin.manifest.securityPolicy?.trustedDomains?.length ? (
                      <div className="space-y-2">
                        <h5 className="text-sm font-medium md:text-base lg:text-lg">Trusted Domains</h5>
                        <div className="space-y-1">
                          {plugin.manifest.securityPolicy.trustedDomains.map((domain, i) => (
                            <div key={domain + i} className="flex items-center gap-2 text-sm">
                              <Globe className="w-3 h-3" />
                              <span className="font-mono">{domain}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : null}
                  </div>
                </div>

                <Separator />

                {plugin.permissions?.length ? (
                  <div className="space-y-4">
                    <h4 className="font-medium">Permissions</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {plugin.permissions.map((permission) => (
                        <div key={permission.id} className="p-3 border rounded-lg sm:p-4 md:p-6">
                          <div className="flex items-center justify-between mb-2">
                            <h5 className="font-medium text-sm md:text-base lg:text-lg">
                              {permission.name}
                            </h5>
                            <Badge
                              variant={
                                permission.level === "admin"
                                  ? "destructive"
                                  : permission.level === "write"
                                  ? "default"
                                  : "secondary"
                              }
                              className="text-xs sm:text-sm md:text-base"
                            >
                              {permission.level}
                            </Badge>
                          </div>
                          <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
                            {permission.description}
                          </p>
                          <div className="flex items-center gap-2 mt-2">
                            <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                              {permission.category}
                            </Badge>
                            {permission.required && (
                              <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                                Required
                              </Badge>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="text-sm text-muted-foreground">No explicit permissions listed.</div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* ADVANCED */}
          <TabsContent value="advanced" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Advanced Configuration</CardTitle>
                <CardDescription>Metadata and configuration utilities.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <h4 className="font-medium">Plugin Information</h4>
                    <div className="space-y-2 text-sm md:text-base lg:text-lg">
                      <div className="flex justify-between">
                        <span>Plugin ID:</span>
                        <span className="font-mono">{plugin.id}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Version:</span>
                        <span>{plugin.version}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>API Version:</span>
                        <span>{plugin.manifest.apiVersion}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Installed:</span>
                        <span>{plugin.installedAt.toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h4 className="font-medium">Runtime Information</h4>
                    <div className="space-y-2 text-sm md:text-base lg:text-lg">
                      <div className="flex justify-between">
                        <span>Auto Start:</span>
                        <Badge variant={plugin.autoStart ? "default" : "secondary"}>
                          {plugin.autoStart ? "Yes" : "No"}
                        </Badge>
                      </div>
                      <div className="flex justify-between">
                        <span>Restart Count:</span>
                        <span>{plugin.restartCount}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Status:</span>
                        <Badge variant={plugin.status === "active" ? "default" : "secondary"}>
                          {plugin.status}
                        </Badge>
                      </div>
                    </div>
                  </div>
                </div>

                <Separator />

                <div className="space-y-4">
                  <h4 className="font-medium">Configuration Management</h4>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={handleExport}>
                      <Download className="w-4 h-4 mr-2" />
                      Export JSON
                    </Button>

                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="application/json"
                      className="hidden"
                      onChange={async (e) => {
                        const file = e.target.files?.[0];
                        if (!file) return;
                        try {
                          const text = await file.text();
                          const parsed = JSON.parse(text);
                          handleImport(parsed);
                        } catch {
                          // swallow parse errors; in prod you might surface a toast
                        }
                      }}
                    />
                    <Button variant="outline" size="sm" onClick={triggerImport}>
                      <Upload className="w-4 h-4 mr-2" />
                      Import JSON
                    </Button>

                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        navigator.clipboard.writeText(JSON.stringify(config, null, 2));
                      }}
                    >
                      <Copy className="w-4 h-4 mr-2" />
                      Copy JSON
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Action Buttons */}
        {!readOnly && (
          <div className="flex items-center justify-between pt-6 border-t">
            <div className="flex items-center gap-2">
              <Button variant="outline" onClick={handleReset} disabled={!hasChanges}>
                <RotateCcw className="w-4 h-4 mr-2" />
                Reset
              </Button>
            </div>
            <div className="flex items-center gap-2">
              <Button
                onClick={handleSave}
                disabled={!hasChanges || saving || validationErrors.length > 0}
              >
                {saving ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    Save Changes
                  </>
                )}
              </Button>
            </div>
          </div>
        )}
      </div>
    </ErrorBoundary>
  );
};

export default PluginConfigurationManager;
