"use client";

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { Separator } from '@/components/ui/separator';
import { Switch } from '@/components/ui/switch';
import {
  Bot,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Settings,
  Info,
  Save,
  Loader2,
  Code,
  Zap,
  Shield,
  Globe,
  ExternalLink
} from 'lucide-react';
import { getKarenBackend } from '@/lib/karen-backend';
import { ErrorHandler } from '@/lib/error-handler';

interface CopilotKitConfig {
  enabled: boolean;
  api_base_url: string;
  timeout: number;
  features: {
    code_suggestions: boolean;
    ui_assistance: boolean;
    development_tools: boolean;
    memory_integration: boolean;
  };
  advanced: {
    max_suggestions: number;
    suggestion_delay: number;
    auto_complete: boolean;
    context_awareness: boolean;
  };
}

interface CopilotKitStatus {
  status: 'healthy' | 'unhealthy' | 'unknown';
  message: string;
  version?: string;
  features_available?: string[];
  last_check?: number;
}

const DEFAULT_CONFIG: CopilotKitConfig = {
  enabled: true,
  api_base_url: 'http://localhost:8000/api/copilot',
  timeout: 30,
  features: {
    code_suggestions: true,
    ui_assistance: true,
    development_tools: true,
    memory_integration: false
  },
  advanced: {
    max_suggestions: 5,
    suggestion_delay: 500,
    auto_complete: true,
    context_awareness: true
  }
};

const LOCAL_STORAGE_KEY = 'copilotkit_settings';

/**
 * @file CopilotKitSettings.tsx
 * @description Dedicated settings component for CopilotKit configuration.
 * Separated from LLM settings as CopilotKit is a UI framework, not an LLM provider.
 */
export default function CopilotKitSettings() {
  const [config, setConfig] = useState<CopilotKitConfig>(DEFAULT_CONFIG);
  const [status, setStatus] = useState<CopilotKitStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  
  const { toast } = useToast();
  const backend = getKarenBackend();

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);

      // Load from localStorage first
      const stored = localStorage.getItem(LOCAL_STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        setConfig({ ...DEFAULT_CONFIG, ...parsed });
      }

      // Try to load from backend and get status
      await Promise.all([
        loadBackendSettings(),
        checkCopilotKitStatus()
      ]);

    } catch (error) {
      console.error('Failed to load CopilotKit settings:', error);
      // Use localStorage settings as fallback
    } finally {
      setLoading(false);
    }
  };

  const loadBackendSettings = async () => {
    try {
      const response = await backend.makeRequestPublic<CopilotKitConfig>('/api/copilot/settings');
      if (response) {
        setConfig(response);
      }
    } catch (error) {
      console.warn('Backend settings unavailable, using local settings:', error);
    }
  };

  const checkCopilotKitStatus = async () => {
    try {
      const response = await backend.makeRequestPublic<CopilotKitStatus>('/api/copilot/status');
      setStatus(response);
    } catch (error) {
      console.warn('CopilotKit status check failed:', error);
      setStatus({
        status: 'unknown',
        message: 'Status check failed - service may be unavailable',
        last_check: Date.now()
      });
    }
  };

  const handleConfigChange = (path: string, value: any) => {
    setConfig(prev => {
      const updated = { ...prev };
      const keys = path.split('.');
      let current = updated as any;
      
      for (let i = 0; i < keys.length - 1; i++) {
        current = current[keys[i]];
      }
      
      current[keys[keys.length - 1]] = value;
      return updated;
    });
  };

  const testConnection = async () => {
    try {
      setTesting(true);
      
      const response = await backend.makeRequestPublic('/api/copilot/test', {
        method: 'POST',
        body: JSON.stringify({
          api_base_url: config.api_base_url,
          timeout: config.timeout
        })
      });

      if (response) {
        toast({
          title: "Connection Test Successful",
          description: "CopilotKit service is responding correctly.",
        });
        
        // Refresh status
        await checkCopilotKitStatus();
      }
    } catch (error) {
      console.error('Connection test failed:', error);
      const info = (error as any)?.errorInfo || ErrorHandler.handleApiError(error as any, 'testConnection');
      toast({
        title: info.title || "Connection Test Failed",
        description: info.message || "Could not connect to CopilotKit service.",
        variant: "destructive",
      });
    } finally {
      setTesting(false);
    }
  };

  const saveSettings = async () => {
    try {
      setSaving(true);

      // Save to localStorage first (always works)
      localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(config));

      // Try to save to backend
      try {
        await backend.makeRequestPublic('/api/copilot/settings', {
          method: 'POST',
          body: JSON.stringify(config)
        });

        toast({
          title: "Settings Saved",
          description: "CopilotKit settings have been saved successfully.",
        });
      } catch (backendError) {
        console.warn('Backend save failed, using local storage:', backendError);
        toast({
          title: "Settings Saved Locally",
          description: "Settings saved to browser storage. Backend sync will retry automatically.",
        });
      }

    } catch (error) {
      console.error('Failed to save settings:', error);
      const info = (error as any)?.errorInfo || ErrorHandler.handleApiError(error as any, 'saveSettings');
      toast({
        title: info.title || "Error Saving Settings",
        description: info.message || "Could not save CopilotKit settings. Please try again.",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'unhealthy':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Info className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'healthy':
        return <Badge variant="default" className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100">Healthy</Badge>;
      case 'unhealthy':
        return <Badge variant="destructive">Unhealthy</Badge>;
      default:
        return <Badge variant="secondary">Unknown</Badge>;
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <div className="text-center space-y-4">
            <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
            <div className="space-y-2">
              <p className="text-lg font-medium">Loading CopilotKit Settings</p>
              <p className="text-sm text-muted-foreground">
                Checking service status and configuration...
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h3 className="text-lg font-medium flex items-center gap-2">
          <Bot className="h-5 w-5" />
          CopilotKit Configuration
        </h3>
        <p className="text-sm text-muted-foreground">
          Configure AI-powered development assistance and UI framework settings.
          CopilotKit is a UI framework, not an LLM provider.
        </p>
      </div>

      {/* Status Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              Service Status
              {status && getStatusIcon(status.status)}
            </span>
            {status && getStatusBadge(status.status)}
          </CardTitle>
          <CardDescription>
            Current CopilotKit service health and availability
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {status ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Status Message:</span>
                <span className="text-sm text-muted-foreground">{status.message}</span>
              </div>
              
              {status.version && (
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Version:</span>
                  <span className="text-sm text-muted-foreground">{status.version}</span>
                </div>
              )}
              
              {status.features_available && (
                <div className="space-y-2">
                  <span className="text-sm font-medium">Available Features:</span>
                  <div className="flex flex-wrap gap-1">
                    {status.features_available.map(feature => (
                      <Badge key={feature} variant="outline" className="text-xs">
                        {feature}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
              
              {status.last_check && (
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Last Check:</span>
                  <span className="text-sm text-muted-foreground">
                    {new Date(status.last_check).toLocaleString()}
                  </span>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-4">
              <Info className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
              <p className="text-sm text-muted-foreground">Status information unavailable</p>
            </div>
          )}
          
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={checkCopilotKitStatus}
              disabled={loading}
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh Status
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={testConnection}
              disabled={testing}
            >
              {testing ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Zap className="h-4 w-4 mr-2" />
              )}
              Test Connection
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Basic Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            Basic Configuration
          </CardTitle>
          <CardDescription>
            Core CopilotKit service settings and connection parameters
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center space-x-2">
            <Switch
              id="enabled"
              checked={config.enabled}
              onCheckedChange={(checked) => handleConfigChange('enabled', checked)}
            />
            <Label htmlFor="enabled" className="text-sm font-medium">
              Enable CopilotKit
            </Label>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="api_base_url">API Base URL</Label>
            <Input
              id="api_base_url"
              value={config.api_base_url}
              onChange={(e) => handleConfigChange('api_base_url', e.target.value)}
              placeholder="http://localhost:8000/api/copilot"
              disabled={!config.enabled}
            />
            <p className="text-xs text-muted-foreground">
              Base URL for CopilotKit API endpoints
            </p>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="timeout">Request Timeout (seconds)</Label>
            <Input
              id="timeout"
              type="number"
              min="1"
              max="300"
              value={config.timeout}
              onChange={(e) => handleConfigChange('timeout', parseInt(e.target.value) || 30)}
              disabled={!config.enabled}
            />
            <p className="text-xs text-muted-foreground">
              Maximum time to wait for API responses
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Feature Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Code className="h-4 w-4" />
            Feature Configuration
          </CardTitle>
          <CardDescription>
            Enable or disable specific CopilotKit features
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center space-x-2">
              <Switch
                id="code_suggestions"
                checked={config.features.code_suggestions}
                onCheckedChange={(checked) => handleConfigChange('features.code_suggestions', checked)}
                disabled={!config.enabled}
              />
              <Label htmlFor="code_suggestions" className="text-sm font-medium">
                Code Suggestions
              </Label>
            </div>
            
            <div className="flex items-center space-x-2">
              <Switch
                id="ui_assistance"
                checked={config.features.ui_assistance}
                onCheckedChange={(checked) => handleConfigChange('features.ui_assistance', checked)}
                disabled={!config.enabled}
              />
              <Label htmlFor="ui_assistance" className="text-sm font-medium">
                UI Assistance
              </Label>
            </div>
            
            <div className="flex items-center space-x-2">
              <Switch
                id="development_tools"
                checked={config.features.development_tools}
                onCheckedChange={(checked) => handleConfigChange('features.development_tools', checked)}
                disabled={!config.enabled}
              />
              <Label htmlFor="development_tools" className="text-sm font-medium">
                Development Tools
              </Label>
            </div>
            
            <div className="flex items-center space-x-2">
              <Switch
                id="memory_integration"
                checked={config.features.memory_integration}
                onCheckedChange={(checked) => handleConfigChange('features.memory_integration', checked)}
                disabled={!config.enabled}
              />
              <Label htmlFor="memory_integration" className="text-sm font-medium">
                Memory Integration
              </Label>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Advanced Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-4 w-4" />
            Advanced Settings
          </CardTitle>
          <CardDescription>
            Fine-tune CopilotKit behavior and performance
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="max_suggestions">Max Suggestions</Label>
              <Input
                id="max_suggestions"
                type="number"
                min="1"
                max="20"
                value={config.advanced.max_suggestions}
                onChange={(e) => handleConfigChange('advanced.max_suggestions', parseInt(e.target.value) || 5)}
                disabled={!config.enabled}
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="suggestion_delay">Suggestion Delay (ms)</Label>
              <Input
                id="suggestion_delay"
                type="number"
                min="0"
                max="5000"
                value={config.advanced.suggestion_delay}
                onChange={(e) => handleConfigChange('advanced.suggestion_delay', parseInt(e.target.value) || 500)}
                disabled={!config.enabled}
              />
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center space-x-2">
              <Switch
                id="auto_complete"
                checked={config.advanced.auto_complete}
                onCheckedChange={(checked) => handleConfigChange('advanced.auto_complete', checked)}
                disabled={!config.enabled}
              />
              <Label htmlFor="auto_complete" className="text-sm font-medium">
                Auto Complete
              </Label>
            </div>
            
            <div className="flex items-center space-x-2">
              <Switch
                id="context_awareness"
                checked={config.advanced.context_awareness}
                onCheckedChange={(checked) => handleConfigChange('advanced.context_awareness', checked)}
                disabled={!config.enabled}
              />
              <Label htmlFor="context_awareness" className="text-sm font-medium">
                Context Awareness
              </Label>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Documentation and Help */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Info className="h-4 w-4" />
            Documentation & Help
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">
              CopilotKit is an AI-powered development assistance framework that provides
              code suggestions, UI assistance, and development tools. It is not an LLM provider
              but rather a UI framework that enhances the development experience.
            </p>
            
            <div className="flex gap-2">
              <Button variant="outline" size="sm" asChild>
                <a href="https://docs.copilotkit.ai" target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="h-4 w-4 mr-2" />
                  Documentation
                </a>
              </Button>
              
              <Button variant="outline" size="sm" asChild>
                <a href="https://github.com/CopilotKit/CopilotKit" target="_blank" rel="noopener noreferrer">
                  <Globe className="h-4 w-4 mr-2" />
                  GitHub
                </a>
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button onClick={saveSettings} disabled={saving}>
          {saving ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <Save className="h-4 w-4 mr-2" />
          )}
          Save Settings
        </Button>
      </div>

      {/* Info Alert */}
      <Alert>
        <Info className="h-4 w-4" />
        <AlertTitle>Important Note</AlertTitle>
        <AlertDescription className="text-sm space-y-2">
          <p>• CopilotKit is a UI framework for AI-powered development assistance, not an LLM provider</p>
          <p>• These settings are separate from LLM provider configurations</p>
          <p>• Changes take effect immediately for new development sessions</p>
          <p>• Settings are saved locally and synced with the backend when available</p>
        </AlertDescription>
      </Alert>
    </div>
  );
}