"use client";

import React, { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import {
  Code,
  RotateCcw,
  Save,
  Settings,
  Zap,
  Info,
  ExternalLink,
} from "lucide-react";

export interface CopilotKitConfig {
  enabled: boolean;
  apiEndpoint: string;
  features: {
    codeAssistance: boolean;
    contextualHelp: boolean;
    autoComplete: boolean;
    codeReview: boolean;
  };
  ui: {
    theme: "auto" | "light" | "dark";
    position: "bottom-right" | "bottom-left" | "top-right" | "top-left";
    showShortcuts: boolean;
    compactMode: boolean;
  };
  performance: {
    debounceMs: number;
    maxSuggestions: number;
    cacheEnabled: boolean;
  };
}

const defaultConfig: CopilotKitConfig = {
  enabled: true,
  apiEndpoint: "/copilot",
  features: {
    codeAssistance: true,
    contextualHelp: true,
    autoComplete: true,
    codeReview: false,
  },
  ui: {
    theme: "auto",
    position: "bottom-right",
    showShortcuts: true,
    compactMode: false,
  },
  performance: {
    debounceMs: 300,
    maxSuggestions: 5,
    cacheEnabled: true,
  },
};

const STORAGE_KEY = "copilotkit_config";

function clampInt(value: unknown, min: number, max: number, fallback: number) {
  const n = typeof value === "number" ? value : Number(value);
  if (Number.isNaN(n)) return fallback;
  return Math.min(max, Math.max(min, Math.trunc(n)));
}

export default function CopilotKitSettings() {
  const { toast } = useToast();
  const [config, setConfig] = useState<CopilotKitConfig>(defaultConfig);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  // Load persisted config on mount (fault-tolerant)
  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as Partial<CopilotKitConfig>;
        // Minimal defensive merge to survive older shapes
        setConfig((prev) => ({
          ...prev,
          ...parsed,
          features: { ...prev.features, ...(parsed.features ?? {}) },
          ui: { ...prev.ui, ...(parsed.ui ?? {}) },
          performance: { ...prev.performance, ...(parsed.performance ?? {}) },
        }));
      }
    } catch {
      // Ignore corrupted storage; stick with defaults
    }
  }, []);

  const handleConfigChange = (path: string, value: unknown) => {
    setConfig((prev) => {
      const next = structuredClone(prev);
      const keys = path.split(".");
      let cursor: unknown = next;
      for (let i = 0; i < keys.length - 1; i++) cursor = cursor[keys[i]];
      cursor[keys[keys.length - 1]] = value;
      return next;
    });
    setHasChanges(true);
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
      setHasChanges(false);
      toast({
        title: "Settings saved",
        description: "CopilotKit configuration has been stored locally.",
      });
    } catch {
      toast({
        title: "Save failed",
        description: "Could not persist CopilotKit settings. Try again.",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    setConfig(defaultConfig);
    setHasChanges(true);
    toast({
      title: "Settings reset",
      description: "Reverted to factory defaults (not yet saved).",
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Code className="h-5 w-5" />
                CopilotKit Settings
              </CardTitle>
              <CardDescription>
                Configure the UI framework that powers your AI development assistant.
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={handleReset}
                disabled={saving}
                aria-label="Reset to defaults"
              >
                <RotateCcw className="h-4 w-4 mr-2" />
                Reset
              </Button>
              <Button
                onClick={handleSave}
                disabled={saving || !hasChanges}
                aria-label="Save changes"
                aria-busy={saving}
              >
                <Save className="h-4 w-4 mr-2" />
                {saving ? "Saving..." : "Save Changes"}
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* General Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            General
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="enable-copilot">Enable CopilotKit</Label>
              <p className="text-sm text-muted-foreground">
                Toggle the entire assistant on/off.
              </p>
            </div>
            <Switch
              id="enable-copilot"
              checked={config.enabled}
              onCheckedChange={(checked) => handleConfigChange("enabled", checked)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="api-endpoint">API Endpoint</Label>
            <Input
              id="api-endpoint"
              value={config.apiEndpoint}
              onChange={(e) => handleConfigChange("apiEndpoint", e.target.value)}
              placeholder="/copilot"
              spellCheck={false}
              autoComplete="off"
            />
            <p className="text-sm text-muted-foreground">
              Relative or absolute URL for your CopilotKit backend.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Features */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-4 w-4" />
            Features
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="feat-code">Code Assistance</Label>
              <p className="text-sm text-muted-foreground">
                AI suggestions and inline completions.
              </p>
            </div>
            <Switch
              id="feat-code"
              checked={config.features.codeAssistance}
              onCheckedChange={(checked) =>
                handleConfigChange("features.codeAssistance", checked)
              }
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="feat-context">Contextual Help</Label>
              <p className="text-sm text-muted-foreground">
                Tips & references based on current file/context.
              </p>
            </div>
            <Switch
              id="feat-context"
              checked={config.features.contextualHelp}
              onCheckedChange={(checked) =>
                handleConfigChange("features.contextualHelp", checked)
              }
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="feat-autocomplete">Auto Complete</Label>
              <p className="text-sm text-muted-foreground">
                Predictive token completion as you type.
              </p>
            </div>
            <Switch
              id="feat-autocomplete"
              checked={config.features.autoComplete}
              onCheckedChange={(checked) =>
                handleConfigChange("features.autoComplete", checked)
              }
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="feat-review">Code Review</Label>
              <p className="text-sm text-muted-foreground">
                Automated review suggestions & nits.
              </p>
            </div>
            <Switch
              id="feat-review"
              checked={config.features.codeReview}
              onCheckedChange={(checked) =>
                handleConfigChange("features.codeReview", checked)
              }
            />
          </div>
        </CardContent>
      </Card>

      {/* UI Settings */}
      <Card>
        <CardHeader>
          <CardTitle>UI Settings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="theme">Theme</Label>
              <select
                id="theme"
                className="w-full rounded-md border bg-transparent p-2"
                value={config.ui.theme}
                onChange={(e) =>
                  handleConfigChange("ui.theme", e.target.value as CopilotKitConfig["ui"]["theme"])
                }
              >
                <option value="auto">Auto</option>
                <option value="light">Light</option>
                <option value="dark">Dark</option>
              </select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="position">Position</Label>
              <select
                id="position"
                className="w-full rounded-md border bg-transparent p-2"
                value={config.ui.position}
                onChange={(e) =>
                  handleConfigChange(
                    "ui.position",
                    e.target.value as CopilotKitConfig["ui"]["position"]
                  )
                }
              >
                <option value="bottom-right">Bottom Right</option>
                <option value="bottom-left">Bottom Left</option>
                <option value="top-right">Top Right</option>
                <option value="top-left">Top Left</option>
              </select>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="ui-shortcuts">Show Shortcuts</Label>
              <p className="text-sm text-muted-foreground">
                Display quick keys in the UI.
              </p>
            </div>
            <Switch
              id="ui-shortcuts"
              checked={config.ui.showShortcuts}
              onCheckedChange={(checked) =>
                handleConfigChange("ui.showShortcuts", checked)
              }
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="ui-compact">Compact Mode</Label>
              <p className="text-sm text-muted-foreground">
                Reduce padding and density for small screens.
              </p>
            </div>
            <Switch
              id="ui-compact"
              checked={config.ui.compactMode}
              onCheckedChange={(checked) =>
                handleConfigChange("ui.compactMode", checked)
              }
            />
          </div>
        </CardContent>
      </Card>

      {/* Performance Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Performance Settings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="debounce">Debounce (ms)</Label>
            <Input
              id="debounce"
              type="number"
              inputMode="numeric"
              value={config.performance.debounceMs}
              onChange={(e) =>
                handleConfigChange(
                  "performance.debounceMs",
                  clampInt(e.target.value, 100, 2000, config.performance.debounceMs)
                )
              }
              min={100}
              max={2000}
            />
            <p className="text-sm text-muted-foreground">
              Delay before triggering suggestions (100–2000 ms).
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="max-suggestions">Max Suggestions</Label>
            <Input
              id="max-suggestions"
              type="number"
              inputMode="numeric"
              value={config.performance.maxSuggestions}
              onChange={(e) =>
                handleConfigChange(
                  "performance.maxSuggestions",
                  clampInt(e.target.value, 1, 20, config.performance.maxSuggestions)
                )
              }
              min={1}
              max={20}
            />
            <p className="text-sm text-muted-foreground">
              Maximum number of suggestions to display (1–20).
            </p>
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="perf-cache">Enable Caching</Label>
              <p className="text-sm text-muted-foreground">
                Cache recent prompts & responses for faster UX.
              </p>
            </div>
            <Switch
              id="perf-cache"
              checked={config.performance.cacheEnabled}
              onCheckedChange={(checked) =>
                handleConfigChange("performance.cacheEnabled", checked)
              }
            />
          </div>
        </CardContent>
      </Card>

      {/* Information */}
      <Alert>
        <Info className="h-4 w-4" />
        <AlertTitle>About CopilotKit</AlertTitle>
        <AlertDescription className="space-y-2">
          <p>
            CopilotKit is a UI framework for building AI-powered interfaces — it’s not an LLM provider.
            Use it to wire models and features into a cohesive developer experience.
          </p>
          <div className="flex gap-2 mt-2">
            <Button variant="outline" size="sm" asChild>
              <a
                href="https://copilotkit.ai/docs"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="Open CopilotKit documentation"
              >
                <ExternalLink className="h-3 w-3 mr-1" />
                Docs
              </a>
            </Button>
            <Button variant="outline" size="sm" asChild>
              <a
                href="https://github.com/CopilotKit/CopilotKit"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="Open CopilotKit GitHub repository"
              >
                <ExternalLink className="h-3 w-3 mr-1" />
                GitHub
              </a>
            </Button>
          </div>
        </AlertDescription>
      </Alert>
    </div>
  );
}
