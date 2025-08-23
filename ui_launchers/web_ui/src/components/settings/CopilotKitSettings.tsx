"use client";

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { Switch } from '@/components/ui/switch';
import {
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Settings,
  ExternalLink,
  Info,
  Loader2,
  Zap,
  Code,
  MessageSquare,
  Brain
} from 'lucide-react';
import { getKarenBackend } from '@/lib/karen-backend';

interface CopilotKitConfig {
  enabled: boolean;
  runtime_url: string;
  api_key?: string;
  features: {
    code_assistance: boolean;
    contextual_help: boolean;
    auto_suggestions: boolean;
    chat_integration: boolean;
  };
  ui_settings: {
    theme: 'light' | 'dark' | 'auto';
    position: 'right' | 'left' | 'bottom';
    auto_open: boolean;
    show_suggestions: boolean;
  };
  performance: {
    debounce_ms: number;
    max_context_length: number;
    cache_responses: boolean;
  };
}

interface CopilotKitStatus {
  status: 'healthy' | 'unhealthy' | 'unknown';
  version?: string;
  last_check?: number;
  error_message?: string;
  features_available: string[];
}

const LOCAL_STORAGE_KEY = 'copilotkit_config';

/**
 * CopilotKit Settings Component
 * 
 * Dedicated settings interface for CopilotKit UI framework configuration.
 * Separated from LLM provider settings as CopilotKit is a UI framework, not an LLM provider.
 */
export default function CopilotKitSettings() {
  const [config, setConfig] = useState<CopilotKitConfig>({
    enabled: true,
    runtime_url: '/api/copilot',
    features: {
      code_assistance: true,
      contextual_help: true,
      auto_suggestions: true,
      chat_integration: true,
    },
    ui_settings: {
      theme: 'auto',
      position: 'right',
      auto_open: false,
      show_suggestions: true,
    },
    performance: {
      debounce_ms: 300,
      max_context_length: 4000,
      cache_responses: true,
    }
  });

  const [status, setStatus] = useState<CopilotKitStatus>({
    status: 'unknown',
    features_available: []
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);

  const { toast } = useToast();
  const backend = getKarenBackend();

  useEffect(() => {
    loadConfig();
    checkStatus();
  }, []);

  const loadConfig = () => {
    try {
      const savedConfig = localStorage.getItem(LOCAL_STORAGE_KEY);
      if (savedConfig) {
        const parsed = JSON.parse(savedConfig);
        setConfig(prev => ({ ...prev, ...parsed }));
      }
    } catch (error) {
      console.warn('Failed to load CopilotKit config:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveConfig = async () => {
    try {
      setSaving(true);
      
      // Save to localStorage
      localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(config));
      
      // Optionally save to backend
      try {
        await backend.makeRequestPublic('/api/copilot/config', {
          method: 'POST',
          body: JSON.stringify(config)
        });
      } catch (backendError) {
        console.warn('Failed to save config to backend:', backendError);
        // Continue with local save only
      }
      
      toast({
        title: "Configuration Saved",
        description: "CopilotKit settings have been updated successfully.",
      });
      
    } catch (error) {
      console.error('Failed to save config:', error);
      toast({
        title: "Save Failed",
        description: "Could not save CopilotKit configuration.",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  const checkStatus = async () => {
    try {
      const response = await backend.makeRequestPublic<CopilotKitStatus>('/api/copilot/status');
      setStatus(response || {
        status: 'unknown',
        features_available: []
      });
    } catch (error) {
      console.warn('Failed to check CopilotKit status:', error);
      setStatus({
        status: 'unknown',
        error_message: 'Status check failed',
        features_available: []
      });
    }
  };

  const testConnection = async () => {
    try {
      setTesting(true);
      
      const response = await backend.makeRequestPublic('/api/copilot/test', {
        method: 'POST',
        body: JSON.stringify({ runtime_url: config.runtime_url })
      });
      
      if (response.success) {
        toast({
          title: "Connection Test Successful",
          description: "CopilotKit runtime is responding correctly.",
        });
        await checkStatus();
      } else {
        toast({
          title: "Connection Test Failed",
          description: response.message || "Could not connect to CopilotKit runtime.",
          variant: "destructive",
        });
      }
      
    } catch (error) {
      console.error('Connection test failed:', error);
      toast({
        title: "Connection Test Failed",
        description: "Could not test CopilotKit connection.",
        variant: "destructive",
      });
    } finally {
      setTesting(false);
    }
  };

  const updateConfig = (updates: Partial<CopilotKitConfig>) => {
    setConfig(prev => ({ ...prev, ...updates }));
  };

  const updateFeatures = (feature: keyof CopilotKitConfig['features'], enabled: boolean) => {
    setConfig(prev => ({
      ...prev,
      features: { ...prev.features, [feature]: enabled }
    }));
  };

  const updateUISettings = (setting: keyof CopilotKitConfig['ui_settings'], value: any) => {
    setConfig(prev => ({
      ...prev,
      ui_settings: { ...prev.ui_settings, [setting]: value }
    }));
  };

  const updatePerformance = (setting: keyof CopilotKitConfig['performance'], value: any) => {
    setConfig(prev => ({
      ...prev,
      performance: { ...prev.performance, [setting]: value }
    }));
  };

  const getStatusIcon = () => {
    switch (status.status) {
      case 'healthy':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'unhealthy':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Info className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusBadge = () => {
    switch (status.status) {
      case 'healthy':
        return <Badge variant="default" className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100">Active</Badge>;
      case 'unhealthy':
        return <Badge variant="destructive">Error</Badge>;
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
            <p className="text-lg font-medium">Loading CopilotKit Settings</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <Brain className="h-6 w-6" />
            CopilotKit Settings
          </h2>
          <p className="text-muted-foreground">
            Configure CopilotKit UI framework for AI-powered interfaces
          </p>
        </div>
        <div className="flex items-center gap-2">
          {getStatusBadge()}
          <Button
            variant="outline"
            size="sm"
            onClick={checkStatus}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Check Status
          </Button>
        </div>
      </div>

      {/* Status Alert */}
      <Alert>
        <Info className="h-4 w-4" />
        <AlertTitle>About CopilotKit</AlertTitle>
        <AlertDescription>
          CopilotKit is a UI framework for building AI-powered interfaces, not an LLM provider. 
          It provides components and hooks for integrating AI assistance into your application's user interface.
        </AlertDescription>
      </Alert>

      {/* Main Configuration */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                General Configuration
              </CardTitle>
              <CardDescription>
                Basic CopilotKit runtime and connection settings
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              {getStatusIcon()}
              <span className="text-sm text-muted-foreground">
                {status.status === 'healthy' ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>
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
              onCheckedChange={(enabled) => updateConfig({ enabled })}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="runtime-url">Runtime URL</Label>
            <div className="flex gap-2">
              <Input
                id="runtime-url"
                value={config.runtime_url}
                onChange={(e) => updateConfig({ runtime_url: e.target.value })}
                placeholder="/api/copilot"
              />
              <Button
                variant="outline"
                onClick={testConnection}
                disabled={testing}
              >
                {testing ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Zap className="h-4 w-4" />
                )}
              </Button>
            </div>
            <p className="text-sm text-muted-foreground">
              URL endpoint for CopilotKit runtime API
            </p>
          </div>

          {status.error_message && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{status.error_message}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Feature Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Code className="h-5 w-5" />
            Features
          </CardTitle>
          <CardDescription>
            Enable or disable specific CopilotKit features
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Code Assistance</Label>
                <p className="text-sm text-muted-foreground">AI-powered code suggestions</p>
              </div>
              <Switch
                checked={config.features.code_assistance}
                onCheckedChange={(enabled) => updateFeatures('code_assistance', enabled)}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Contextual Help</Label>
                <p className="text-sm text-muted-foreground">Context-aware assistance</p>
              </div>
              <Switch
                checked={config.features.contextual_help}
                onCheckedChange={(enabled) => updateFeatures('contextual_help', enabled)}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Auto Suggestions</Label>
                <p className="text-sm text-muted-foreground">Automatic AI suggestions</p>
              </div>
              <Switch
                checked={config.features.auto_suggestions}
                onCheckedChange={(enabled) => updateFeatures('auto_suggestions', enabled)}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Chat Integration</Label>
                <p className="text-sm text-muted-foreground">Integrated chat interface</p>
              </div>
              <Switch
                checked={config.features.chat_integration}
                onCheckedChange={(enabled) => updateFeatures('chat_integration', enabled)}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* UI Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            UI Settings
          </CardTitle>
          <CardDescription>
            Customize CopilotKit interface appearance and behavior
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Theme</Label>
              <select
                className="w-full p-2 border rounded-md"
                value={config.ui_settings.theme}
                onChange={(e) => updateUISettings('theme', e.target.value)}
              >
                <option value="auto">Auto</option>
                <option value="light">Light</option>
                <option value="dark">Dark</option>
              </select>
            </div>

            <div className="space-y-2">
              <Label>Position</Label>
              <select
                className="w-full p-2 border rounded-md"
                value={config.ui_settings.position}
                onChange={(e) => updateUISettings('position', e.target.value)}
              >
                <option value="right">Right</option>
                <option value="left">Left</option>
                <option value="bottom">Bottom</option>
              </select>
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Auto Open</Label>
                <p className="text-sm text-muted-foreground">Open interface automatically</p>
              </div>
              <Switch
                checked={config.ui_settings.auto_open}
                onCheckedChange={(enabled) => updateUISettings('auto_open', enabled)}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Show Suggestions</Label>
                <p className="text-sm text-muted-foreground">Display suggestion tooltips</p>
              </div>
              <Switch
                checked={config.ui_settings.show_suggestions}
                onCheckedChange={(enabled) => updateUISettings('show_suggestions', enabled)}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Performance Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Performance Settings</CardTitle>
          <CardDescription>
            Optimize CopilotKit performance and resource usage
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="debounce">Debounce (ms)</Label>
              <Input
                id="debounce"
                type="number"
                value={config.performance.debounce_ms}
                onChange={(e) => updatePerformance('debounce_ms', parseInt(e.target.value))}
                min="100"
                max="2000"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="context-length">Max Context Length</Label>
              <Input
                id="context-length"
                type="number"
                value={config.performance.max_context_length}
                onChange={(e) => updatePerformance('max_context_length', parseInt(e.target.value))}
                min="1000"
                max="10000"
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Cache Responses</Label>
                <p className="text-sm text-muted-foreground">Cache AI responses</p>
              </div>
              <Switch
                checked={config.performance.cache_responses}
                onCheckedChange={(enabled) => updatePerformance('cache_responses', enabled)}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Button variant="outline" asChild>
            <a href="https://docs.copilotkit.ai" target="_blank" rel="noopener noreferrer">
              <ExternalLink className="h-4 w-4 mr-2" />
              Documentation
            </a>
          </Button>
        </div>
        
        <Button onClick={saveConfig} disabled={saving}>
          {saving ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <Settings className="h-4 w-4 mr-2" />
          )}
          Save Configuration
        </Button>
      </div>
    </div>
  );
}