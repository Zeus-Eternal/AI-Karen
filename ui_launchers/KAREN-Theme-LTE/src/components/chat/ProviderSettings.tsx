/**
 * Provider Settings Component
 * Configuration interface for LLM providers with secure API key management
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Loader2, CheckCircle, XCircle, AlertTriangle, Eye, EyeOff } from 'lucide-react';
import { LLMProvider, ProviderConfigSchema, ConfigProperty } from '@/types/chat';
import { useProviderConfig } from '@/hooks/useProviderConfig';
import { useProviderStatus } from '@/hooks/useProviderStatus';

interface ProviderSettingsProps {
  provider?: LLMProvider;
  onProviderChange?: (provider: LLMProvider) => void;
  onConfigSave?: (providerId: string, config: Record<string, any>) => void;
  className?: string;
}

interface ProviderConfigState {
  [key: string]: any;
}

interface ConnectionState {
  testing: boolean;
  lastTest: Date | null;
  success: boolean | null;
  error?: string;
}

export const ProviderSettings: React.FC<ProviderSettingsProps> = ({
  provider,
  onProviderChange,
  onConfigSave,
  className
}) => {
  const { saveProviderConfig, validateProviderConfig } = useProviderConfig();
  const { testProviderConnection } = useProviderStatus();
  
  const [activeTab, setActiveTab] = useState('configuration');
  const [configState, setConfigState] = useState<ProviderConfigState>({});
  const [connectionState, setConnectionState] = useState<Record<string, ConnectionState>>({});
  const [showApiKeys, setShowApiKeys] = useState<Record<string, boolean>>({});
  const [validationErrors, setValidationErrors] = useState<Record<string, string[]>>({});

  // Initialize config state when provider changes
  useEffect(() => {
    if (provider) {
      const initialConfig: ProviderConfigState = {};
      
      // Set default values from provider schema
      Object.entries(provider.configSchema.properties).forEach(([key, property]) => {
        initialConfig[key] = property.default || '';
      });
      
      // Override with any existing config
      if (provider.config) {
        Object.assign(initialConfig, provider.config);
      }
      
      setConfigState(initialConfig);
    }
  }, [provider]);

  const handleConfigChange = (key: string, value: any) => {
    setConfigState(prev => ({
      ...prev,
      [key]: value
    }));
    
    // Clear validation errors for this field
    if (validationErrors[key]) {
      setValidationErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[key];
        return newErrors;
      });
    }
  };

  const handleSaveConfig = async () => {
    if (!provider) return;

    try {
      // Validate configuration
      const validation = await validateProviderConfig(provider.id, configState);
      
      if (!validation.isValid) {
        setValidationErrors(
          validation.errors.reduce((acc, error) => {
            const parts = error.split(':');
            const field = parts[0]?.trim();
            const message = parts[1]?.trim();
            if (field && message) {
              return {
                ...acc,
                [field]: [...(acc[field] || []), message]
              };
            }
            return acc;
          }, {} as Record<string, string[]>)
        );
        return;
      }

      // Save configuration
      await saveProviderConfig(provider.id, configState);
      onConfigSave?.(provider.id, configState);
      
      setActiveTab('status');
    } catch (error) {
      console.error('Failed to save provider config:', error);
    }
  };

  const handleTestConnection = async (providerId: string) => {
    setConnectionState(prev => ({
      ...prev,
      [providerId]: {
        testing: true,
        lastTest: new Date(),
        success: null,
        error: undefined
      }
    }));

    try {
      const result = await testProviderConnection(providerId, configState);

      setConnectionState(prev => ({
        ...prev,
        [providerId]: {
          testing: false,
          lastTest: prev[providerId]?.lastTest ?? null,
          success: result.success,
          error: result.error
        }
      }));
    } catch (error) {
      setConnectionState(prev => ({
        ...prev,
        [providerId]: {
          testing: false,
          lastTest: prev[providerId]?.lastTest ?? null,
          success: false,
          error: error instanceof Error ? error.message : 'Connection test failed'
        }
      }));
    }
  };

  const renderConfigField = (key: string, property: ConfigProperty) => {
    const value = configState[key];
    const error = validationErrors[key];
    const isSecret = property.secret;
    const showKey = showApiKeys[key];

    switch (property.type) {
      case 'boolean':
        return (
          <div className="flex items-center space-x-2">
            <Switch
              id={key}
              checked={value || false}
              onCheckedChange={(checked) => handleConfigChange(key, checked)}
            />
            <Label htmlFor={key}>{property.title}</Label>
          </div>
        );

      case 'number':
        return (
          <div className="space-y-2">
            <Label htmlFor={key}>{property.title}</Label>
            <Input
              id={key}
              type="number"
              value={value || ''}
              onChange={(e) => handleConfigChange(key, parseFloat(e.target.value))}
              min={property.minimum}
              max={property.maximum}
              step={property.step}
              className={error ? 'border-red-500' : ''}
            />
            {property.description && (
              <p className="text-sm text-muted-foreground">{property.description}</p>
            )}
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error.join(', ')}</AlertDescription>
              </Alert>
            )}
          </div>
        );

      case 'select':
        return (
          <div className="space-y-2">
            <Label htmlFor={key}>{property.title}</Label>
            <Select
              value={value || ''}
              onValueChange={(newValue) => handleConfigChange(key, newValue)}
            >
              <SelectTrigger className={error ? 'border-red-500' : ''}>
                <SelectValue placeholder={`Select ${property.title}`} />
              </SelectTrigger>
              <SelectContent>
                {property.enum?.map((option) => (
                  <SelectItem key={option} value={option}>
                    {option}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {property.description && (
              <p className="text-sm text-muted-foreground">{property.description}</p>
            )}
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error.join(', ')}</AlertDescription>
              </Alert>
            )}
          </div>
        );

      default:
        return (
          <div className="space-y-2">
            <Label htmlFor={key}>{property.title}</Label>
            <div className="relative">
              <Input
                id={key}
                type={isSecret && !showKey ? 'password' : 'text'}
                value={value || ''}
                onChange={(e) => handleConfigChange(key, e.target.value)}
                placeholder={property.description}
                className={error ? 'border-red-500 pr-10' : 'pr-10'}
              />
              {isSecret && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                  onClick={() => setShowApiKeys(prev => ({ ...prev, [key]: !prev[key] }))}
                >
                  {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
              )}
            </div>
            {property.description && (
              <p className="text-sm text-muted-foreground">{property.description}</p>
            )}
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error.join(', ')}</AlertDescription>
              </Alert>
            )}
          </div>
        );
    }
  };

  if (!provider) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <p className="text-center text-muted-foreground">Select a provider to configure</p>
        </CardContent>
      </Card>
    );
  }

  const connection = connectionState[provider.id];
  const isRequiredFieldsFilled = provider.configSchema.required.every(
    field => configState[field] && configState[field].toString().trim() !== ''
  );

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              {provider.displayName}
              <Badge variant={provider.status === 'active' ? 'default' : 'secondary'}>
                {provider.status}
              </Badge>
            </CardTitle>
            <CardDescription>{provider.description}</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            {connection?.testing && (
              <Loader2 className="h-4 w-4 animate-spin" />
            )}
            {connection?.lastTest && (
              <div className="flex items-center gap-1">
                {connection.success === true && (
                  <CheckCircle className="h-4 w-4 text-green-500" />
                )}
                {connection.success === false && (
                  <XCircle className="h-4 w-4 text-red-500" />
                )}
                <span className="text-sm text-muted-foreground">
                  Tested {connection.lastTest.toLocaleTimeString()}
                </span>
              </div>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="configuration">Configuration</TabsTrigger>
            <TabsTrigger value="models">Models</TabsTrigger>
            <TabsTrigger value="status">Status</TabsTrigger>
          </TabsList>

          <TabsContent value="configuration" className="space-y-4 mt-4">
            <div className="space-y-4">
              {Object.entries(provider.configSchema.properties).map(([key, property]) => (
                <div key={key}>
                  {renderConfigField(key, property)}
                </div>
              ))}
            </div>

            <div className="flex gap-2 pt-4">
              <Button
                onClick={handleSaveConfig}
                disabled={!isRequiredFieldsFilled || Object.keys(validationErrors).length > 0}
              >
                Save Configuration
              </Button>
              <Button
                variant="outline"
                onClick={() => handleTestConnection(provider.id)}
                disabled={!isRequiredFieldsFilled}
              >
                {connection?.testing ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Testing...
                  </>
                ) : (
                  'Test Connection'
                )}
              </Button>
            </div>

            {connection?.error && (
              <Alert variant="destructive" className="mt-4">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>{connection.error}</AlertDescription>
              </Alert>
            )}
          </TabsContent>

          <TabsContent value="models" className="space-y-4 mt-4">
            <div className="grid gap-4">
              {provider.models.map((model) => (
                <Card key={model.id}>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-semibold">{model.displayName}</h4>
                        <p className="text-sm text-muted-foreground">{model.description}</p>
                        <div className="flex items-center gap-2 mt-2">
                          <Badge variant="outline">
                            Context: {model.contextWindow.toLocaleString()}
                          </Badge>
                          <Badge variant="outline">
                            Max: {model.maxTokens.toLocaleString()}
                          </Badge>
                          {model.isBeta && (
                            <Badge variant="secondary">Beta</Badge>
                          )}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-medium">
                          ${model.inputTokenPrice}/1K input
                        </div>
                        <div className="text-sm font-medium">
                          ${model.outputTokenPrice}/1K output
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="status" className="space-y-4 mt-4">
            {provider.healthCheck && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Status</Label>
                    <Badge 
                      variant={
                        provider.healthCheck.status === 'healthy' ? 'default' :
                        provider.healthCheck.status === 'degraded' ? 'secondary' : 'destructive'
                      }
                    >
                      {provider.healthCheck.status}
                    </Badge>
                  </div>
                  <div>
                    <Label>Response Time</Label>
                    <p className="text-sm font-medium">
                      {provider.healthCheck.responseTime}ms
                    </p>
                  </div>
                  <div>
                    <Label>Error Rate</Label>
                    <p className="text-sm font-medium">
                      {(provider.healthCheck.errorRate * 100).toFixed(2)}%
                    </p>
                  </div>
                  <div>
                    <Label>Uptime</Label>
                    <p className="text-sm font-medium">
                      {(provider.healthCheck.uptime * 100).toFixed(2)}%
                    </p>
                  </div>
                </div>

                {provider.healthCheck.issues && provider.healthCheck.issues.length > 0 && (
                  <Alert>
                    <AlertTriangle className="h-4 w-4" />
                    <AlertDescription>
                      <div className="space-y-1">
                        <p className="font-medium">Known Issues:</p>
                        <ul className="list-disc list-inside text-sm">
                          {provider.healthCheck.issues.map((issue, index) => (
                            <li key={index}>{issue}</li>
                          ))}
                        </ul>
                      </div>
                    </AlertDescription>
                  </Alert>
                )}

                <div>
                  <Label>Last Checked</Label>
                  <p className="text-sm text-muted-foreground">
                    {provider.healthCheck.lastChecked.toLocaleString()}
                  </p>
                </div>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};