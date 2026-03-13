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

export interface CopilotConfig {
  enabled: boolean;
  backendUrl: string;
  expertiseLevel: "beginner" | "intermediate" | "advanced" | "expert";
  features: {
    intelligentAssistant: boolean;
    memoryManagement: boolean;
    workflowAutomation: boolean;
    artifactSystem: boolean;
    pluginDiscovery: boolean;
    multiModalInput: boolean;
  };
  ui: {
    theme: "auto" | "light" | "dark";
    fontSize: "small" | "medium" | "large";
    showTimestamps: boolean;
    showMemoryOps: boolean;
    showDebugInfo: boolean;
    maxMessageHistory: number;
    enableAnimations: boolean;
    enableSoundEffects: boolean;
    enableKeyboardShortcuts: boolean;
    autoScroll: boolean;
    markdownSupport: boolean;
    codeHighlighting: boolean;
    imagePreview: boolean;
  };
  performance: {
    debounceMs: number;
    maxSuggestions: number;
    cacheEnabled: boolean;
  };
}

const defaultConfig: CopilotConfig = {
  enabled: true,
  backendUrl: "/api",
  expertiseLevel: "intermediate",
  features: {
    intelligentAssistant: true,
    memoryManagement: true,
    workflowAutomation: true,
    artifactSystem: true,
    pluginDiscovery: true,
    multiModalInput: true,
  },
  ui: {
    theme: "auto",
    fontSize: "medium",
    showTimestamps: true,
    showMemoryOps: true,
    showDebugInfo: false,
    maxMessageHistory: 50,
    enableAnimations: true,
    enableSoundEffects: false,
    enableKeyboardShortcuts: true,
    autoScroll: true,
    markdownSupport: true,
    codeHighlighting: true,
    imagePreview: true,
  },
  performance: {
    debounceMs: 300,
    maxSuggestions: 5,
    cacheEnabled: true,
  },
};

const STORAGE_KEY = "copilot_config";

function clampInt(value: unknown, min: number, max: number, fallback: number) {
  const n = typeof value === "number" ? value : Number(value);
  if (Number.isNaN(n)) return fallback;
  return Math.min(max, Math.max(min, Math.trunc(n)));
}

export default function CopilotSettings() {
  const { toast } = useToast();
  const [config, setConfig] = useState<CopilotConfig>(defaultConfig);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  // Load persisted config on mount (fault-tolerant)
  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as Partial<CopilotConfig>;
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
      let cursor = next as unknown as Record<string, unknown>;

      for (let i = 0; i < keys.length - 1; i++) {
        const key = keys[i];
        if (
          typeof cursor[key] !== "object" ||
          cursor[key] === null
        ) {
          cursor[key] = {};
        }
        cursor = cursor[key] as Record<string, unknown>;
      }

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
        description: "KARI Copilot configuration has been stored locally.",
      });
    } catch {
      toast({
        title: "Save failed",
        description: "Could not persist KARI Copilot settings. Try again.",
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
                KARI Copilot Settings
              </CardTitle>
              <CardDescription>
                Configure the KARI Copilot system that serves as the UI gateway to KAREN&rsquo;s entire engine.
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
              <Label htmlFor="enable-copilot">Enable KARI Copilot</Label>
              <p className="text-sm text-muted-foreground">
                Toggle the KARI Copilot system on/off.
              </p>
            </div>
            <Switch
              id="enable-copilot"
              checked={config.enabled}
              onCheckedChange={(checked) => handleConfigChange("enabled", checked)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="backend-url">Backend URL</Label>
            <Input
              id="backend-url"
              value={config.backendUrl}
              onChange={(e) => handleConfigChange("backendUrl", e.target.value)}
              placeholder="/api"
              spellCheck={false}
              autoComplete="off"
            />
            <p className="text-sm text-muted-foreground">
              Relative or absolute URL for the KAREN backend.
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="expertise-level">Expertise Level</Label>
            <select
              id="expertise-level"
              className="w-full rounded-md border bg-transparent p-2"
              value={config.expertiseLevel}
              onChange={(e) =>
                handleConfigChange("expertiseLevel", e.target.value as CopilotConfig["expertiseLevel"])
              }
            >
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
              <option value="expert">Expert</option>
            </select>
            <p className="text-sm text-muted-foreground">
              Select your expertise level to customize the interface.
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
              <Label htmlFor="feat-intelligent">Intelligent Assistant</Label>
              <p className="text-sm text-muted-foreground">
                Context-aware suggestions and actions.
              </p>
            </div>
            <Switch
              id="feat-intelligent"
              checked={config.features.intelligentAssistant}
              onCheckedChange={(checked) =>
                handleConfigChange("features.intelligentAssistant", checked)
              }
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="feat-memory">Memory Management</Label>
              <p className="text-sm text-muted-foreground">
                Manage short-term, long-term, and persistent memory.
              </p>
            </div>
            <Switch
              id="feat-memory"
              checked={config.features.memoryManagement}
              onCheckedChange={(checked) =>
                handleConfigChange("features.memoryManagement", checked)
              }
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="feat-workflow">Workflow Automation</Label>
              <p className="text-sm text-muted-foreground">
                Execute backend-provided workflows.
              </p>
            </div>
            <Switch
              id="feat-workflow"
              checked={config.features.workflowAutomation}
              onCheckedChange={(checked) =>
                handleConfigChange("features.workflowAutomation", checked)
              }
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="feat-artifact">Artifact System</Label>
              <p className="text-sm text-muted-foreground">
                Manage and preview generated artifacts.
              </p>
            </div>
            <Switch
              id="feat-artifact"
              checked={config.features.artifactSystem}
              onCheckedChange={(checked) =>
                handleConfigChange("features.artifactSystem", checked)
              }
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="feat-plugin">Plugin Discovery</Label>
              <p className="text-sm text-muted-foreground">
                Discover and manage plugins.
              </p>
            </div>
            <Switch
              id="feat-plugin"
              checked={config.features.pluginDiscovery}
              onCheckedChange={(checked) =>
                handleConfigChange("features.pluginDiscovery", checked)
              }
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="feat-multimodal">Multi-Modal Input</Label>
              <p className="text-sm text-muted-foreground">
                Support for text, code, image, and audio input.
              </p>
            </div>
            <Switch
              id="feat-multimodal"
              checked={config.features.multiModalInput}
              onCheckedChange={(checked) =>
                handleConfigChange("features.multiModalInput", checked)
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
                  handleConfigChange("ui.theme", e.target.value as CopilotConfig["ui"]["theme"])
                }
              >
                <option value="auto">Auto</option>
                <option value="light">Light</option>
                <option value="dark">Dark</option>
              </select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="font-size">Font Size</Label>
              <select
                id="font-size"
                className="w-full rounded-md border bg-transparent p-2"
                value={config.ui.fontSize}
                onChange={(e) =>
                  handleConfigChange(
                    "ui.fontSize",
                    e.target.value as CopilotConfig["ui"]["fontSize"]
                  )
                }
              >
                <option value="small">Small</option>
                <option value="medium">Medium</option>
                <option value="large">Large</option>
              </select>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="ui-timestamps">Show Timestamps</Label>
              <p className="text-sm text-muted-foreground">
                Display message timestamps.
              </p>
            </div>
            <Switch
              id="ui-timestamps"
              checked={config.ui.showTimestamps}
              onCheckedChange={(checked) =>
                handleConfigChange("ui.showTimestamps", checked)
              }
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="ui-memory">Show Memory Operations</Label>
              <p className="text-sm text-muted-foreground">
                Display memory management options.
              </p>
            </div>
            <Switch
              id="ui-memory"
              checked={config.ui.showMemoryOps}
              onCheckedChange={(checked) =>
                handleConfigChange("ui.showMemoryOps", checked)
              }
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="ui-debug">Show Debug Info</Label>
              <p className="text-sm text-muted-foreground">
                Display debug information.
              </p>
            </div>
            <Switch
              id="ui-debug"
              checked={config.ui.showDebugInfo}
              onCheckedChange={(checked) =>
                handleConfigChange("ui.showDebugInfo", checked)
              }
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="ui-max-history">Max Message History</Label>
            <Input
              id="ui-max-history"
              type="number"
              inputMode="numeric"
              value={config.ui.maxMessageHistory}
              onChange={(e) =>
                handleConfigChange(
                  "ui.maxMessageHistory",
                  clampInt(e.target.value, 10, 1000, config.ui.maxMessageHistory)
                )
              }
              min={10}
              max={1000}
            />
            <p className="text-sm text-muted-foreground">
              Maximum number of messages to keep (10–1000).
            </p>
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="ui-animations">Enable Animations</Label>
              <p className="text-sm text-muted-foreground">
                Enable UI animations.
              </p>
            </div>
            <Switch
              id="ui-animations"
              checked={config.ui.enableAnimations}
              onCheckedChange={(checked) =>
                handleConfigChange("ui.enableAnimations", checked)
              }
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="ui-sound">Enable Sound Effects</Label>
              <p className="text-sm text-muted-foreground">
                Enable sound effects.
              </p>
            </div>
            <Switch
              id="ui-sound"
              checked={config.ui.enableSoundEffects}
              onCheckedChange={(checked) =>
                handleConfigChange("ui.enableSoundEffects", checked)
              }
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="ui-shortcuts">Enable Keyboard Shortcuts</Label>
              <p className="text-sm text-muted-foreground">
                Enable keyboard shortcuts.
              </p>
            </div>
            <Switch
              id="ui-shortcuts"
              checked={config.ui.enableKeyboardShortcuts}
              onCheckedChange={(checked) =>
                handleConfigChange("ui.enableKeyboardShortcuts", checked)
              }
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="ui-autoscroll">Enable Auto Scroll</Label>
              <p className="text-sm text-muted-foreground">
                Auto-scroll to new messages.
              </p>
            </div>
            <Switch
              id="ui-autoscroll"
              checked={config.ui.autoScroll}
              onCheckedChange={(checked) =>
                handleConfigChange("ui.autoScroll", checked)
              }
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="ui-markdown">Enable Markdown</Label>
              <p className="text-sm text-muted-foreground">
                Enable markdown rendering.
              </p>
            </div>
            <Switch
              id="ui-markdown"
              checked={config.ui.markdownSupport}
              onCheckedChange={(checked) =>
                handleConfigChange("ui.markdownSupport", checked)
              }
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="ui-code">Enable Code Highlighting</Label>
              <p className="text-sm text-muted-foreground">
                Enable code syntax highlighting.
              </p>
            </div>
            <Switch
              id="ui-code"
              checked={config.ui.codeHighlighting}
              onCheckedChange={(checked) =>
                handleConfigChange("ui.codeHighlighting", checked)
              }
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="ui-image">Enable Image Preview</Label>
              <p className="text-sm text-muted-foreground">
                Enable image preview.
              </p>
            </div>
            <Switch
              id="ui-image"
              checked={config.ui.imagePreview}
              onCheckedChange={(checked) =>
                handleConfigChange("ui.imagePreview", checked)
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
        <AlertTitle>About KARI Copilot</AlertTitle>
        <AlertDescription className="space-y-2">
          <p>
            KARI Copilot is an advanced chat interface that serves as the UI gateway to KAREN&rsquo;s entire engine.
            It integrates CORTEX (intent + routing + reasoning), MemoryManager/NeuroVault, and the Prompt-First Plugin Engine.
          </p>
          <div className="flex gap-2 mt-2">
            <Button variant="outline" size="sm" asChild>
              <a
                href="/docs/copilot"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="Open KARI Copilot documentation"
              >
                <ExternalLink className="h-3 w-3 mr-1" />
                Docs
              </a>
            </Button>
            <Button variant="outline" size="sm" asChild>
              <a
                href="https://github.com/KIRO-AI/KAREN"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="Open KAREN GitHub repository"
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
