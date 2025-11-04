import React, { useState, useEffect } from 'react';
import { ErrorBoundary } from '@/components/error-handling/ErrorBoundary';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/hooks/use-toast';
/**
 * Comprehensive Provider Configuration Interface
 * Supporting local, cloud, and custom provider types with secure credential management
 */













import { } from 'lucide-react';

import { } from '@/types/providers';

interface ProviderConfigInterfaceProps {
  onProviderSaved?: (provider: ProviderConfig) => void;
  onProviderDeleted?: (providerId: string) => void;
  className?: string;
}
interface FormData {
  [key: string]: any;
}
interface ValidationError {
  field: string;
  message: string;
}
const PROVIDER_TYPES: ProviderType[] = [
  {
    id: 'openai',
    name: 'OpenAI',
    category: 'cloud',
    description: 'OpenAI GPT models and APIs',
    icon: '🤖',
    configSchema: {
      fields: [
        {
          name: 'apiKey',
          type: 'password',
          label: 'API Key',
          description: 'Your OpenAI API key',
          required: true,
          sensitive: true
        },
        {
          name: 'organization',
          type: 'string',
          label: 'Organization ID',
          description: 'Optional organization ID',
          required: false
        },
        {
          name: 'baseUrl',
          type: 'url',
          label: 'Base URL',
          description: 'Custom API endpoint (optional)',
          required: false,
          default: 'https://api.openai.com/v1'
        },
        {
          name: 'timeout',
          type: 'number',
          label: 'Timeout (seconds)',
          description: 'Request timeout in seconds',
          required: false,
          default: 30,
          validation: { min: 1, max: 300 }
        }
      ],
      validation: [
        {
          field: 'apiKey',
          rule: 'required',
          message: 'API key is required'
        },
        {
          field: 'apiKey',
          rule: 'pattern',
          message: 'API key must start with sk-'
        }
      ]
    },
    supportedModels: ['gpt-4', 'gpt-3.5-turbo', 'text-embedding-ada-002'],
    capabilities: ['text-generation', 'embedding', 'chat']
  },
  {
    id: 'anthropic',
    name: 'Anthropic',
    category: 'cloud',
    description: 'Claude models from Anthropic',
    icon: '🧠',
    configSchema: {
      fields: [
        {
          name: 'apiKey',
          type: 'password',
          label: 'API Key',
          description: 'Your Anthropic API key',
          required: true,
          sensitive: true
        },
        {
          name: 'version',
          type: 'select',
          label: 'API Version',
          description: 'API version to use',
          required: true,
          default: '2023-06-01',
          options: [
            { value: '2023-06-01', label: '2023-06-01' },
            { value: '2023-01-01', label: '2023-01-01' }
          ]
        }
      ],
      validation: []
    },
    supportedModels: ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku'],
    capabilities: ['text-generation', 'chat', 'analysis']
  },
  {
    id: 'ollama',
    name: 'Ollama',
    category: 'local',
    description: 'Local Ollama server',
    icon: '🦙',
    configSchema: {
      fields: [
        {
          name: 'host',
          type: 'string',
          label: 'Host',
          description: 'Ollama server host',
          required: true,
          default: 'localhost'
        },
        {
          name: 'port',
          type: 'number',
          label: 'Port',
          description: 'Ollama server port',
          required: true,
          default: 11434,
          validation: { min: 1, max: 65535 }
        },
        {
          name: 'ssl',
          type: 'boolean',
          label: 'Use SSL',
          description: 'Enable SSL/TLS connection',
          required: false,
          default: false
        }
      ],
      validation: []
    },
    supportedModels: ['llama2', 'codellama', 'mistral'],
    capabilities: ['text-generation', 'code', 'chat']
  }
];
const ProviderConfigInterface: React.FC<ProviderConfigInterfaceProps> = ({
  onProviderSaved,
  onProviderDeleted,
  className
}) => {
  const { toast } = useToast();
  const [providers, setProviders] = useState<ProviderConfig[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<ProviderConfig | null>(null);
  const [selectedType, setSelectedType] = useState<ProviderType | null>(null);
  const [formData, setFormData] = useState<FormData>({});
  const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);
  const [showSensitive, setShowSensitive] = useState<Record<string, boolean>>({});
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [providerHealth, setProviderHealth] = useState<Record<string, ProviderHealth>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  useEffect(() => {
    loadProviders();
    loadProviderHealth();
  }, []);
  const loadProviders = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/providers');
      if (!response.ok) throw new Error('Failed to load providers');
      const data = await response.json();
      setProviders(data.providers || []);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load provider configurations',
        variant: 'destructive'

    } finally {
      setLoading(false);
    }
  };
  const loadProviderHealth = async () => {
    try {
      const response = await fetch('/api/providers/health');
      if (!response.ok) throw new Error('Failed to load provider health');
      const data = await response.json();
      setProviderHealth(data.health || {});
    } catch (error) {
    }
  };
  const validateForm = (type: ProviderType, data: FormData): ValidationError[] => {
    const errors: ValidationError[] = [];
    // Field-level validation
    type.configSchema.fields.forEach(field => {
      const value = data[field.name];
      // Required field validation
      if (field.required && (!value || value === '')) {
        errors.push({
          field: field.name,
          message: `${field.label} is required`

        return;
      }
      // Type-specific validation
      if (value !== undefined && value !== '') {
        switch (field.type) {
          case 'number':
            if (isNaN(Number(value))) {
              errors.push({
                field: field.name,
                message: `${field.label} must be a number`

            } else if (field.validation) {
              const num = Number(value);
              if (field.validation.min !== undefined && num < field.validation.min) {
                errors.push({
                  field: field.name,
                  message: `${field.label} must be at least ${field.validation.min}`

              }
              if (field.validation.max !== undefined && num > field.validation.max) {
                errors.push({
                  field: field.name,
                  message: `${field.label} must be at most ${field.validation.max}`

              }
            }
            break;
          case 'url':
            try {
              new URL(value);
            } catch {
              errors.push({
                field: field.name,
                message: `${field.label} must be a valid URL`

            }
            break;
          case 'string':
            if (field.validation) {
              if (field.validation.minLength && value.length < field.validation.minLength) {
                errors.push({
                  field: field.name,
                  message: `${field.label} must be at least ${field.validation.minLength} characters`

              }
              if (field.validation.maxLength && value.length > field.validation.maxLength) {
                errors.push({
                  field: field.name,
                  message: `${field.label} must be at most ${field.validation.maxLength} characters`

              }
              if (field.validation.pattern && !new RegExp(field.validation.pattern).test(value)) {
                errors.push({
                  field: field.name,
                  message: `${field.label} format is invalid`

              }
            }
            break;
        }
      }

    // Custom validation rules
    type.configSchema.validation.forEach(rule => {
      const value = data[rule.field];
      switch (rule.rule) {
        case 'required':
          if (!value || value === '') {
            errors.push({
              field: rule.field,
              message: rule.message

          }
          break;
        case 'pattern':
          if (value && rule.field === 'apiKey' && !value.startsWith('sk-')) {
            errors.push({
              field: rule.field,
              message: rule.message

          }
          break;
      }

    return errors;
  };
  const handleFieldChange = (fieldName: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [fieldName]: value
    }));
    // Clear validation error for this field
    setValidationErrors(prev => prev.filter(error => error.field !== fieldName));
  };
  const handleTestConnection = async () => {
    if (!selectedType) return;
    const errors = validateForm(selectedType, formData);
    if (errors.length > 0) {
      setValidationErrors(errors);
      toast({
        title: 'Validation Error',
        description: 'Please fix the form errors before testing',
        variant: 'destructive'

      return;
    }
    setTesting(true);
    setTestResult(null);
    try {
      const response = await fetch('/api/providers/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: selectedType.id,
          configuration: formData
        })

      const result = await response.json();
      setTestResult({
        success: response.ok,
        message: result.message || (response.ok ? 'Connection successful' : 'Connection failed')

      if (response.ok) {
        toast({
          title: 'Test Successful',
          description: 'Provider connection is working correctly'

      } else {
        toast({
          title: 'Test Failed',
          description: result.message || 'Failed to connect to provider',
          variant: 'destructive'

      }
    } catch (error) {
      setTestResult({
        success: false,
        message: 'Network error occurred during testing'

      toast({
        title: 'Test Error',
        description: 'Failed to test provider connection',
        variant: 'destructive'

    } finally {
      setTesting(false);
    }
  };
  const handleSave = async () => {
    if (!selectedType) return;
    const errors = validateForm(selectedType, formData);
    if (errors.length > 0) {
      setValidationErrors(errors);
      toast({
        title: 'Validation Error',
        description: 'Please fix the form errors before saving',
        variant: 'destructive'

      return;
    }
    setSaving(true);
    try {
      const providerData = {
        id: selectedProvider?.id || `${selectedType.id}-${Date.now()}`,
        name: formData.name || `${selectedType.name} Provider`,
        type: selectedType.id,
        enabled: formData.enabled !== false,
        configuration: formData,
        credentials: Object.fromEntries(
          selectedType.configSchema.fields
            .filter(field => field.sensitive)
            .map(field => [field.name, formData[field.name]])
        ),
        metadata: {
          version: '1.0.0',
          description: selectedType.description,
          tags: [selectedType.category],
          supportUrl: '',
          documentationUrl: ''
        },
        createdAt: selectedProvider?.createdAt || new Date(),
        updatedAt: new Date()
      };
      const response = await fetch(`/api/providers${selectedProvider ? `/${selectedProvider.id}` : ''}`, {
        method: selectedProvider ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(providerData)

      if (!response.ok) throw new Error('Failed to save provider');
      const savedProvider = await response.json();
      if (selectedProvider) {
        setProviders(prev => prev.map(p => p.id === selectedProvider.id ? savedProvider : p));
      } else {
        setProviders(prev => [...prev, savedProvider]);
      }
      onProviderSaved?.(savedProvider);
      toast({
        title: 'Provider Saved',
        description: `${savedProvider.name} has been saved successfully`

      // Reset form
      setSelectedProvider(null);
      setSelectedType(null);
      setFormData({});
      setValidationErrors([]);
      setTestResult(null);
    } catch (error) {
      toast({
        title: 'Save Error',
        description: 'Failed to save provider configuration',
        variant: 'destructive'

    } finally {
      setSaving(false);
    }
  };
  const handleDelete = async (provider: ProviderConfig) => {
    if (!confirm(`Are you sure you want to delete ${provider.name}?`)) return;
    try {
      const response = await fetch(`/api/providers/${provider.id}`, {
        method: 'DELETE'

      if (!response.ok) throw new Error('Failed to delete provider');
      setProviders(prev => prev.filter(p => p.id !== provider.id));
      onProviderDeleted?.(provider.id);
      if (selectedProvider?.id === provider.id) {
        setSelectedProvider(null);
        setSelectedType(null);
        setFormData({});
      }
      toast({
        title: 'Provider Deleted',
        description: `${provider.name} has been deleted`

    } catch (error) {
      toast({
        title: 'Delete Error',
        description: 'Failed to delete provider',
        variant: 'destructive'

    }
  };
  const handleEdit = (provider: ProviderConfig) => {
    const type = PROVIDER_TYPES.find(t => t.id === provider.type);
    if (!type) return;
    setSelectedProvider(provider);
    setSelectedType(type);
    setFormData({
      ...provider.configuration,
      ...provider.credentials,
      name: provider.name,
      enabled: provider.enabled

    setValidationErrors([]);
    setTestResult(null);
  };
  const handleNewProvider = (type: ProviderType) => {
    setSelectedProvider(null);
    setSelectedType(type);
    // Initialize form with default values
    const defaultData: FormData = {
      name: `${type.name} Provider`,
      enabled: true
    };
    type.configSchema.fields.forEach(field => {
      if (field.default !== undefined) {
        defaultData[field.name] = field.default;
      }

    setFormData(defaultData);
    setValidationErrors([]);
    setTestResult(null);
  };
  const renderField = (field: ProviderConfigField) => {
    const value = formData[field.name] || '';
    const error = validationErrors.find(e => e.field === field.name);
    const isVisible = showSensitive[field.name] || !field.sensitive;
    return (
    <ErrorBoundary fallback={<div>Something went wrong in ProviderConfigInterface</div>}>
      <div key={field.name} className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor={field.name} className="flex items-center gap-2">
            {field.label}
            {field.required && <span className="text-red-500">*</span>}
            {field.sensitive && <Lock className="w-3 h-3 " />}
          </Label>
          {field.sensitive && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setShowSensitive(prev => ({
                ...prev,
                [field.name]: !prev[field.name]
              }))}
            >
              {isVisible ? <EyeOff className="w-4 h-4 " /> : <Eye className="w-4 h-4 " />}
            </Button>
          )}
        </div>
        {field.type === 'select' ? (
          <select value={value} onValueChange={(val) = aria-label="Select option"> handleFieldChange(field.name, val)}>
            <selectTrigger aria-label="Select option">
              <selectValue placeholder={`Select ${field.label}`} />
            </SelectTrigger>
            <selectContent aria-label="Select option">
              {field.options?.map(option => (
                <selectItem key={option.value} value={option.value} aria-label="Select option">
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        ) : field.type === 'boolean' ? (
          <div className="flex items-center space-x-2">
            <Switch
              id={field.name}
              checked={value}
              onCheckedChange={(checked) => handleFieldChange(field.name, checked)}
            />
            <Label htmlFor={field.name} className="text-sm text-gray-600 md:text-base lg:text-lg">
              {field.description}
            </Label>
          </div>
        ) : field.type === 'textarea' ? (
          <textarea
            id={field.name}
            value={value}
            onChange={(e) => handleFieldChange(field.name, e.target.value)}
            placeholder={field.description}
            className={error ? 'border-red-500' : ''}
          />
        ) : (
          <input
            id={field.name}
            type={field.sensitive && !isVisible ? 'password' : field.type === 'number' ? 'number' : 'text'}
            value={value}
            onChange={(e) => handleFieldChange(field.name, e.target.value)}
            placeholder={field.description}
            className={error ? 'border-red-500' : ''}
          />
        )}
        {field.description && field.type !== 'boolean' && (
          <p className="text-xs text-gray-600 sm:text-sm md:text-base">{field.description}</p>
        )}
        {error && (
          <p className="text-xs text-red-600 flex items-center gap-1 sm:text-sm md:text-base">
            <AlertTriangle className="w-3 h-3 " />
            {error.message}
          </p>
        )}
      </div>
    );
  };
  const getHealthIcon = (health?: ProviderHealth) => {
    if (!health) return <Activity className="w-4 h-4 text-gray-400 " />;
    switch (health.status) {
      case 'healthy':
        return <CheckCircle className="w-4 h-4 text-green-600 " />;
      case 'degraded':
        return <AlertTriangle className="w-4 h-4 text-yellow-600 " />;
      case 'unhealthy':
        return <XCircle className="w-4 h-4 text-red-600 " />;
      default:
        return <Activity className="w-4 h-4 text-gray-400 " />;
    }
  };
  const getHealthBadge = (health?: ProviderHealth) => {
    if (!health) return <Badge variant="secondary">Unknown</Badge>;
    const colors = {
      healthy: 'bg-green-100 text-green-800',
      degraded: 'bg-yellow-100 text-yellow-800',
      unhealthy: 'bg-red-100 text-red-800',
      unknown: 'bg-gray-100 text-gray-800'
    };
    return (
      <Badge className={colors[health.status]}>
        {health.status.charAt(0).toUpperCase() + health.status.slice(1)}
      </Badge>
    );
  };
  if (loading) {
    return (
      <Card className={className}>
        <CardContent className="flex items-center justify-center p-8 sm:p-4 md:p-6">
          <div className="text-center space-y-2">
            <Settings className="w-8 h-8 animate-spin mx-auto text-blue-500 " />
            <div>Loading provider configurations...</div>
          </div>
        </CardContent>
      </Card>
    );
  }
  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="w-5 h-5 " />
          </CardTitle>
          <CardDescription>
          </CardDescription>
        </CardHeader>
      </Card>
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Provider List */}
        <div className="lg:col-span-1 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Configured Providers</CardTitle>
              <CardDescription>
                {providers.length} provider{providers.length !== 1 ? 's' : ''} configured
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {providers.map(provider => {
                const health = providerHealth[provider.id];
                const type = PROVIDER_TYPES.find(t => t.id === provider.type);
                return (
                  <div
                    key={provider.id}
                    className={`p-3 border rounded-lg cursor-pointer transition-colors hover:bg-gray-50 ${
                      selectedProvider?.id === provider.id ? 'border-blue-500 bg-blue-50' : ''
                    }`}
                    onClick={() => handleEdit(provider)}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-lg">{type?.icon}</span>
                        <span className="font-medium">{provider.name}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        {getHealthIcon(health)}
                        <Switch checked={provider.enabled} disabled />
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {type?.category === 'cloud' && <Cloud className="w-3 h-3 " />}
                        {type?.category === 'local' && <Server className="w-3 h-3 " />}
                        {type?.category === 'custom' && <Cpu className="w-3 h-3 " />}
                        <span className="text-xs text-gray-600 sm:text-sm md:text-base">{type?.name}</span>
                      </div>
                      {getHealthBadge(health)}
                    </div>
                    {health && (
                      <div className="mt-2 text-xs text-gray-600 sm:text-sm md:text-base">
                        <div className="flex justify-between">
                          <span>Response Time</span>
                          <span>{health.responseTime.toFixed(0)}ms</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Success Rate</span>
                          <span>{((1 - health.errorRate) * 100).toFixed(1)}%</span>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
              {providers.length === 0 && (
                <div className="text-center py-6 text-gray-500">
                  <Settings className="w-8 h-8 mx-auto mb-2 opacity-50 " />
                  <div>No providers configured</div>
                  <div className="text-xs sm:text-sm md:text-base">Add a provider to get started</div>
                </div>
              )}
            </CardContent>
          </Card>
          {/* Add New Provider */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Plus className="w-4 h-4 " />
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {PROVIDER_TYPES.map(type => (
                <Button
                  key={type.id}
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => handleNewProvider(type)}
                >
                  <span className="mr-2 text-lg">{type.icon}</span>
                  <div className="text-left">
                    <div className="font-medium">{type.name}</div>
                    <div className="text-xs text-gray-600 sm:text-sm md:text-base">{type.description}</div>
                  </div>
                  <Badge variant="outline" className="ml-auto">
                    {type.category}
                  </Badge>
                </Button>
              ))}
            </CardContent>
          </Card>
        </div>
        {/* Configuration Form */}
        <div className="lg:col-span-2">
          {selectedType ? (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <span className="text-lg">{selectedType.icon}</span>
                      {selectedProvider ? 'Edit' : 'Add'} {selectedType.name} Provider
                    </CardTitle>
                    <CardDescription>{selectedType.description}</CardDescription>
                  </div>
                  {selectedProvider && (
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => handleDelete(selectedProvider)}
                    >
                      <Trash2 className="w-4 h-4 mr-2 " />
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="configuration">
                  <TabsList className="grid w-full grid-cols-3">
                    <TabsTrigger value="configuration">Configuration</TabsTrigger>
                    <TabsTrigger value="health">Health & Metrics</TabsTrigger>
                    <TabsTrigger value="models">Supported Models</TabsTrigger>
                  </TabsList>
                  <TabsContent value="configuration" className="space-y-6">
                    {/* Basic Settings */}
                    <div className="space-y-4">
                      <div className="space-y-2">
                        <Label htmlFor="name">Provider Name *</Label>
                        <input
                          id="name"
                          value={formData.name || ''}
                          onChange={(e) => handleFieldChange('name', e.target.value)}
                          placeholder="Enter a name for this provider"
                        />
                      </div>
                      <div className="flex items-center space-x-2">
                        <Switch
                          id="enabled"
                          checked={formData.enabled !== false}
                          onCheckedChange={(checked) => handleFieldChange('enabled', checked)}
                        />
                        <Label htmlFor="enabled">Enable this provider</Label>
                      </div>
                    </div>
                    {/* Provider-specific Configuration */}
                    <div className="space-y-4">
                      <h4 className="font-medium">Provider Settings</h4>
                      {selectedType.configSchema.fields.map(renderField)}
                    </div>
                    {/* Test Connection */}
                    <div className="space-y-4">
                      <div className="flex items-center gap-2">
                        <Button
                          onClick={handleTestConnection}
                          disabled={testing}
                          variant="outline"
                         >
                          {testing ? (
                            <RefreshCw className="w-4 h-4 mr-2 animate-spin " />
                          ) : (
                            <TestTube className="w-4 h-4 mr-2 " />
                          )}
                        </Button>
                      </div>
                      {testResult && (
                        <Alert className={testResult.success ? 'border-green-500' : 'border-red-500'}>
                          <div className="flex items-center gap-2">
                            {testResult.success ? (
                              <CheckCircle className="w-4 h-4 text-green-600 " />
                            ) : (
                              <XCircle className="w-4 h-4 text-red-600 " />
                            )}
                            <AlertDescription>{testResult.message}</AlertDescription>
                          </div>
                        </Alert>
                      )}
                    </div>
                    {/* Save Button */}
                    <div className="flex justify-end gap-2">
                      <Button
                        variant="outline"
                        onClick={() => {
                          setSelectedProvider(null);
                          setSelectedType(null);
                          setFormData({});
                        }}
                      >
                      </Button>
                      <Button onClick={handleSave} disabled={saving} aria-label="Button">
                        {saving ? (
                          <RefreshCw className="w-4 h-4 mr-2 animate-spin " />
                        ) : (
                          <Save className="w-4 h-4 mr-2 " />
                        )}
                        {selectedProvider ? 'Update' : 'Save'} Provider
                      </Button>
                    </div>
                  </TabsContent>
                  <TabsContent value="health" className="space-y-4">
                    {selectedProvider && providerHealth[selectedProvider.id] ? (
                      <ProviderHealthDisplay health={providerHealth[selectedProvider.id]} />
                    ) : (
                      <div className="text-center py-8 text-gray-500">
                        <Activity className="w-8 h-8 mx-auto mb-2 opacity-50 " />
                        <div>No health data available</div>
                        <div className="text-xs sm:text-sm md:text-base">Save the provider to see health metrics</div>
                      </div>
                    )}
                  </TabsContent>
                  <TabsContent value="models" className="space-y-4">
                    <div>
                      <h4 className="font-medium mb-3">Supported Models</h4>
                      <div className="grid gap-2 sm:grid-cols-2">
                        {selectedType.supportedModels.map(model => (
                          <div key={model} className="p-2 border rounded flex items-center gap-2 sm:p-4 md:p-6">
                            <CheckCircle className="w-4 h-4 text-green-600 " />
                            <span className="font-mono text-sm md:text-base lg:text-lg">{model}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div>
                      <h4 className="font-medium mb-3">Capabilities</h4>
                      <div className="flex flex-wrap gap-2">
                        {selectedType.capabilities.map(capability => (
                          <Badge key={capability} variant="outline">
                            {capability}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="text-center py-12">
                <Settings className="w-12 h-12 mx-auto mb-4 text-gray-400 " />
                <h3 className="text-lg font-medium mb-2">Select a Provider</h3>
                <p className="text-gray-600 mb-4">
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};
const ProviderHealthDisplay: React.FC<{ health: ProviderHealth }> = ({ health }) => {
  return (
    <div className="space-y-4">
      {/* Status Overview */}
      <div className="grid grid-cols-2 gap-4">
        <div className="p-3 bg-gray-50 rounded-lg sm:p-4 md:p-6">
          <div className="text-sm font-medium text-gray-600 md:text-base lg:text-lg">Status</div>
          <div className="text-xl font-bold capitalize">{health.status}</div>
        </div>
        <div className="p-3 bg-gray-50 rounded-lg sm:p-4 md:p-6">
          <div className="text-sm font-medium text-gray-600 md:text-base lg:text-lg">Response Time</div>
          <div className="text-xl font-bold">{health.responseTime.toFixed(0)}ms</div>
        </div>
        <div className="p-3 bg-gray-50 rounded-lg sm:p-4 md:p-6">
          <div className="text-sm font-medium text-gray-600 md:text-base lg:text-lg">Uptime</div>
          <div className="text-xl font-bold">{(health.uptime * 100).toFixed(2)}%</div>
        </div>
        <div className="p-3 bg-gray-50 rounded-lg sm:p-4 md:p-6">
          <div className="text-sm font-medium text-gray-600 md:text-base lg:text-lg">Error Rate</div>
          <div className="text-xl font-bold">{(health.errorRate * 100).toFixed(2)}%</div>
        </div>
      </div>
      {/* Metrics */}
      <div className="space-y-3">
        <h4 className="font-medium">Performance Metrics</h4>
        <div className="space-y-2">
          <div className="flex justify-between text-sm md:text-base lg:text-lg">
            <span>Request Count</span>
            <span className="font-medium">{health.metrics.requestCount}</span>
          </div>
          <div className="flex justify-between text-sm md:text-base lg:text-lg">
            <span>Success Rate</span>
            <span className="font-medium">{(health.metrics.successRate * 100).toFixed(1)}%</span>
          </div>
          <div className="flex justify-between text-sm md:text-base lg:text-lg">
            <span>Average Latency</span>
            <span className="font-medium">{health.metrics.averageLatency.toFixed(0)}ms</span>
          </div>
          <div className="flex justify-between text-sm md:text-base lg:text-lg">
            <span>Throughput</span>
            <span className="font-medium">{health.metrics.throughput.toFixed(1)} req/s</span>
          </div>
        </div>
      </div>
      {/* Issues */}
      {health.issues.length > 0 && (
        <div className="space-y-3">
          <h4 className="font-medium">Health Issues</h4>
          <div className="space-y-2">
            {health.issues.map(issue => (
              <Alert key={issue.id} className="border-red-200">
                <AlertTriangle className="w-4 h-4 " />
                <AlertDescription>
                  <div className="flex items-center justify-between">
                    <span>{issue.message}</span>
                    <Badge variant={issue.severity === 'critical' ? 'destructive' : 'secondary'}>
                      {issue.severity}
                    </Badge>
                  </div>
                  {issue.details && (
                    <div className="text-xs text-gray-600 mt-1 sm:text-sm md:text-base">{issue.details}</div>
                  )}
                </AlertDescription>
              </Alert>
            ))}
          </div>
        </div>
      )}
      {/* Last Check */}
      <div className="text-xs text-gray-600 sm:text-sm md:text-base">
        Last checked: {new Date(health.lastCheck).toLocaleString()}
      </div>
    </div>
    </ErrorBoundary>
  );
};
export default ProviderConfigInterface;
