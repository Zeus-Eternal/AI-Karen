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
      console.error('Failed to save CopilotKit settings:', error);
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
                <Code className="h-5 w-5" />
                CopilotKit Configuration
              </CardTitle>
              <CardDescription>
                Configure CopilotKit UI framework for AI-powered development assistance
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={handleReset}
                disabled={saving}
              >
                <RotateCcw className="h-4 w-4 mr-2" />
                Reset
              </Button>
              <Button
                onClick={handleSave}
                disabled={saving || !hasChanges}
              >
                <Save className="h-4 w-4 mr-2" />
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
            <Settings className="h-4 w-4" />
            General Settings
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Enable CopilotKit</Label>
              <p className="text-sm text-muted-foreground">
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
            <Input
              id="api-endpoint"
              value={config.apiEndpoint}
              onChange={(e) => handleConfigChange('apiEndpoint', e.target.value)}
              placeholder="/copilot"
            />
            <p className="text-sm text-muted-foreground">
              Endpoint for CopilotKit API integration
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
              <Label>Code Assistance</Label>
              <p className="text-sm text-muted-foreground">
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
              <p className="text-sm text-muted-foreground">
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
              <p className="text-sm text-muted-foreground">
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
              <p className="text-sm text-muted-foreground">
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
                className="w-full p-2 border rounded-md"
                value={config.ui.theme}
                onChange={(e) => handleConfigChange('ui.theme', e.target.value)}
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
                className="w-full p-2 border rounded-md"
                value={config.ui.position}
                onChange={(e) => handleConfigChange('ui.position', e.target.value)}
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
              <p className="text-sm text-muted-foreground">
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
              <p className="text-sm text-muted-foreground">
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
            <Input
              id="debounce"
              type="number"
              value={config.performance.debounceMs}
              onChange={(e) => handleConfigChange('performance.debounceMs', parseInt(e.target.value))}
              min="100"
              max="2000"
            />
            <p className="text-sm text-muted-foreground">
              Delay before triggering suggestions (100-2000ms)
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="max-suggestions">Max Suggestions</Label>
            <Input
              id="max-suggestions"
              type="number"
              value={config.performance.maxSuggestions}
              onChange={(e) => handleConfigChange('performance.maxSuggestions', parseInt(e.target.value))}
              min="1"
              max="20"
            />
            <p className="text-sm text-muted-foreground">
              Maximum number of suggestions to show (1-20)
            </p>
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Enable Caching</Label>
              <p className="text-sm text-muted-foreground">
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
        <Info className="h-4 w-4" />
        <AlertTitle>About CopilotKit</AlertTitle>
        <AlertDescription className="space-y-2">
          <p>
            CopilotKit is a UI framework for building AI-powered interfaces, not an LLM provider.
            It provides components and tools for integrating AI assistance into your development workflow.
          </p>
          <div className="flex gap-2 mt-2">
            <Button variant="outline" size="sm" asChild>
              <a href="https://copilotkit.ai/docs" target="_blank" rel="noopener noreferrer">
                <ExternalLink className="h-3 w-3 mr-1" />
                Documentation
              </a>
            </Button>
            <Button variant="outline" size="sm" asChild>
              <a href="https://github.com/CopilotKit/CopilotKit" target="_blank" rel="noopener noreferrer">
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