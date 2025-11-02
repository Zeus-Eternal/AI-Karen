"use client";
import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import {
  Settings,
  Code,
  Zap,
  Info,
  Save,
  RotateCcw,
  ExternalLink
} from 'lucide-react';
interface CopilotKitConfig {
  enabled: boolean;
  apiEndpoint: string;
  features: {
    codeAssistance: boolean;
    contextualHelp: boolean;
    autoComplete: boolean;
    codeReview: boolean;
  };
  ui: {
    theme: string;
    position: string;
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
  apiEndpoint: '/copilot',
  features: {
    codeAssistance: true,
    contextualHelp: true,
    autoComplete: true,
    codeReview: false
  },
  ui: {
    theme: 'auto',
    position: 'bottom-right',
    showShortcuts: true,
    compactMode: false
  },
  performance: {
    debounceMs: 300,
    maxSuggestions: 5,
    cacheEnabled: true
  }
};
export default function CopilotKitSettings() {
  const [config, setConfig] = useState<CopilotKitConfig>(defaultConfig);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const { toast } = useToast();
  const handleConfigChange = (path: string, value: any) => {
    setConfig(prev => {
      const newConfig = { ...prev };
      const keys = path.split('.');
      let current: any = newConfig;
      for (let i = 0; i < keys.length - 1; i++) {
        current = current[keys[i]];
      }
      current[keys[keys.length - 1]] = value;
      return newConfig;
    });
    setHasChanges(true);
  };
  const handleSave = async () => {
    try {
      setSaving(true);
      // Save configuration to localStorage for now
      // In a real implementation, this would save to the backend
      localStorage.setItem('copilotkit_config', JSON.stringify(config));
      setHasChanges(false);
      toast({
        title: "Settings Saved",
        description: "CopilotKit configuration has been saved successfully.",
      });
    } catch (error) {
      toast({
        title: "Save Failed",
        description: "Could not save CopilotKit settings. Please try again.",
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
      title: "Settings Reset",
      description: "CopilotKit configuration has been reset to defaults.",
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
                <Code className="h-5 w-5 sm:w-auto md:w-full" />
                CopilotKit Configuration
              </CardTitle>
              <CardDescription>
                Configure CopilotKit UI framework for AI-powered development assistance
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <button
                variant="outline"
                onClick={handleReset}
                disabled={saving}
               aria-label="Button">
                <RotateCcw className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
                Reset
              </Button>
              <button
                onClick={handleSave}
                disabled={saving || !hasChanges}
               aria-label="Button">
                <Save className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
                {saving ? 'Saving...' : 'Save Changes'}
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>
      {/* General Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-4 w-4 sm:w-auto md:w-full" />
            General Settings
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Enable CopilotKit</Label>
              <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                Enable or disable CopilotKit UI framework
              </p>
            </div>
            <Switch
              checked={config.enabled}
              onCheckedChange={(checked) => handleConfigChange('enabled', checked)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="api-endpoint">API Endpoint</Label>
            <input
              id="api-endpoint"
              value={config.apiEndpoint}
              onChange={(e) = aria-label="Input"> handleConfigChange('apiEndpoint', e.target.value)}
              placeholder="/copilot"
            />
            <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
              Endpoint for CopilotKit API integration
            </p>
          </div>
        </CardContent>
      </Card>
      {/* Features */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-4 w-4 sm:w-auto md:w-full" />
            Features
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Code Assistance</Label>
              <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                Enable AI-powered code suggestions and completions
              </p>
            </div>
            <Switch
              checked={config.features.codeAssistance}
              onCheckedChange={(checked) => handleConfigChange('features.codeAssistance', checked)}
            />
          </div>
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Contextual Help</Label>
              <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                Show contextual help and documentation
              </p>
            </div>
            <Switch
              checked={config.features.contextualHelp}
              onCheckedChange={(checked) => handleConfigChange('features.contextualHelp', checked)}
            />
          </div>
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Auto Complete</Label>
              <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                Enable automatic code completion
              </p>
            </div>
            <Switch
              checked={config.features.autoComplete}
              onCheckedChange={(checked) => handleConfigChange('features.autoComplete', checked)}
            />
          </div>
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Code Review</Label>
              <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                Enable AI-powered code review suggestions
              </p>
            </div>
            <Switch
              checked={config.features.codeReview}
              onCheckedChange={(checked) => handleConfigChange('features.codeReview', checked)}
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
                className="w-full p-2 border rounded-md sm:p-4 md:p-6"
                value={config.ui.theme}
                onChange={(e) = aria-label="Select option"> handleConfigChange('ui.theme', e.target.value)}
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
                className="w-full p-2 border rounded-md sm:p-4 md:p-6"
                value={config.ui.position}
                onChange={(e) = aria-label="Select option"> handleConfigChange('ui.position', e.target.value)}
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
              <Label>Show Shortcuts</Label>
              <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                Display keyboard shortcuts in the UI
              </p>
            </div>
            <Switch
              checked={config.ui.showShortcuts}
              onCheckedChange={(checked) => handleConfigChange('ui.showShortcuts', checked)}
            />
          </div>
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Compact Mode</Label>
              <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                Use compact UI layout to save space
              </p>
            </div>
            <Switch
              checked={config.ui.compactMode}
              onCheckedChange={(checked) => handleConfigChange('ui.compactMode', checked)}
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
            <input
              id="debounce"
              type="number"
              value={config.performance.debounceMs}
              onChange={(e) = aria-label="Input"> handleConfigChange('performance.debounceMs', parseInt(e.target.value))}
              min="100"
              max="2000"
            />
            <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
              Delay before triggering suggestions (100-2000ms)
            </p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="max-suggestions">Max Suggestions</Label>
            <input
              id="max-suggestions"
              type="number"
              value={config.performance.maxSuggestions}
              onChange={(e) = aria-label="Input"> handleConfigChange('performance.maxSuggestions', parseInt(e.target.value))}
              min="1"
              max="20"
            />
            <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
              Maximum number of suggestions to show (1-20)
            </p>
          </div>
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Enable Caching</Label>
              <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                Cache suggestions for better performance
              </p>
            </div>
            <Switch
              checked={config.performance.cacheEnabled}
              onCheckedChange={(checked) => handleConfigChange('performance.cacheEnabled', checked)}
            />
          </div>
        </CardContent>
      </Card>
      {/* Information */}
      <Alert>
        <Info className="h-4 w-4 sm:w-auto md:w-full" />
        <AlertTitle>About CopilotKit</AlertTitle>
        <AlertDescription className="space-y-2">
          <p>
            CopilotKit is a UI framework for building AI-powered interfaces, not an LLM provider.
            It provides components and tools for integrating AI assistance into your development workflow.
          </p>
          <div className="flex gap-2 mt-2">
            <button variant="outline" size="sm" asChild aria-label="Button">
              <a href="https://copilotkit.ai/docs" target="_blank" rel="noopener noreferrer">
                <ExternalLink className="h-3 w-3 mr-1 sm:w-auto md:w-full" />
                Documentation
              </a>
            </Button>
            <button variant="outline" size="sm" asChild aria-label="Button">
              <a href="https://github.com/CopilotKit/CopilotKit" target="_blank" rel="noopener noreferrer">
                <ExternalLink className="h-3 w-3 mr-1 sm:w-auto md:w-full" />
                GitHub
              </a>
            </Button>
          </div>
        </AlertDescription>
      </Alert>
    </div>
  );
}
