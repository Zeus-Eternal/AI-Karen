import React, { useState, useEffect, useCallback } from 'react';
import { ErrorBoundary } from '@/components/error-handling/ErrorBoundary';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { useToast } from '@/hooks/use-toast';
import { enhancedApiClient } from '@/lib/enhanced-api-client';
import {
  Lock,
  Eye,
  EyeOff,
  Activity,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Plus,
  Trash2,
  RefreshCw,
  Save,
  TestTube
} from 'lucide-react';

// Enhanced Type Definitions
export interface ProviderConfig {
  id: string;
  name: string;
  type: string;
  enabled: boolean;
  configuration: Record<string, unknown>;
  credentials: Record<string, string>;
  metadata: ProviderMetadata;
  createdAt: Date;
  updatedAt: Date;
}

export interface ProviderType {
  id: string;
  name: string;
  category: 'cloud' | 'local' | 'custom' | 'enterprise';
  description: string;
  icon: string;
  configSchema: ProviderConfigSchema;
  supportedModels: string[];
  capabilities: string[];
  pricingTier?: 'free' | 'standard' | 'premium' | 'enterprise';
  rateLimits?: RateLimitConfig;
}

export interface ProviderConfigSchema {
  fields: ProviderConfigField[];
  validation: ValidationRule[];
  advanced?: AdvancedConfigSection[];
}

export interface ProviderConfigField {
  name: string;
  type: 'string' | 'password' | 'number' | 'boolean' | 'select' | 'textarea' | 'url';
  label: string;
  description: string;
  required: boolean;
  sensitive?: boolean;
  default?: unknown;
  validation?: FieldValidation;
  options?: SelectOption[];
  advanced?: boolean;
  dependsOn?: string;
  condition?: (data: ProviderFormData) => boolean;
}

export interface ValidationRule {
  field: string;
  rule: 'required' | 'pattern' | 'custom';
  message: string;
  validator?: (value: unknown, formData: ProviderFormData) => boolean;
}

export interface SelectOption {
  value: string;
  label: string;
  description?: string;
}

export interface FieldValidation {
  min?: number;
  max?: number;
  minLength?: number;
  maxLength?: number;
  pattern?: string;
}

export interface ProviderHealth {
  status: 'healthy' | 'degraded' | 'unhealthy' | 'unknown';
  responseTime: number;
  uptime: number;
  errorRate: number;
  lastCheck: Date;
  metrics: HealthMetrics;
  issues: HealthIssue[];
}

export interface HealthMetrics {
  requestCount: number;
  successRate: number;
  averageLatency: number;
  throughput: number;
  cacheHitRate?: number;
}

export interface HealthIssue {
  id: string;
  message: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  details?: string;
  timestamp: Date;
}

export interface RateLimitConfig {
  requestsPerMinute: number;
  requestsPerHour: number;
  tokensPerMinute: number;
}

export interface ProviderMetadata {
  version: string;
  description: string;
  tags: string[];
  supportUrl: string;
  documentationUrl: string;
  compliance?: ComplianceInfo;
}

export interface ComplianceInfo {
  gdpr: boolean;
  hipaa: boolean;
  soc2: boolean;
  dataRetention: number; // days
}

export interface AdvancedConfigSection {
  name: string;
  title: string;
  description: string;
  fields: string[];
  condition?: (data: ProviderFormData) => boolean;
}

export interface ProviderFormData {
  [key: string]: unknown;
}

export interface ValidationError {
  field: string;
  message: string;
  severity: 'error' | 'warning';
}

export interface ProviderConfigInterfaceProps {
  onProviderSaved?: (provider: ProviderConfig) => void;
  onProviderDeleted?: (providerId: string) => void;
  onProviderTested?: (providerId: string, success: boolean) => void;
  className?: string;
  allowedCategories?: ('cloud' | 'local' | 'custom' | 'enterprise')[];
  enableAdvancedFeatures?: boolean;
  complianceRequirements?: ComplianceInfo;
}

// Enhanced Provider Types with Business Logic
const PROVIDER_TYPES: ProviderType[] = [
  {
    id: 'openai',
    name: 'OpenAI',
    category: 'cloud',
    description: 'OpenAI GPT models and APIs with enterprise-grade security',
    icon: '🤖',
    pricingTier: 'premium',
    rateLimits: {
      requestsPerMinute: 60,
      requestsPerHour: 1000,
      tokensPerMinute: 150000
    },
    configSchema: {
      fields: [
        {
          name: 'apiKey',
          type: 'password',
          label: 'API Key',
          description: 'Your OpenAI API key starting with sk-',
          required: true,
          sensitive: true,
          validation: {
            pattern: '^sk-',
            minLength: 20
          }
        },
        {
          name: 'organization',
          type: 'string',
          label: 'Organization ID',
          description: 'Optional organization ID for billing',
          required: false
        },
        {
          name: 'baseUrl',
          type: 'url',
          label: 'Base URL',
          description: 'Custom API endpoint for enterprise deployments',
          required: false,
          default: 'https://api.openai.com/v1',
          advanced: true
        },
        {
          name: 'timeout',
          type: 'number',
          label: 'Timeout (seconds)',
          description: 'Request timeout in seconds',
          required: false,
          default: 30,
          validation: { min: 1, max: 300 }
        },
        {
          name: 'maxRetries',
          type: 'number',
          label: 'Max Retries',
          description: 'Maximum number of retry attempts',
          required: false,
          default: 3,
          validation: { min: 0, max: 10 },
          advanced: true
        }
      ],
      validation: [
        {
          field: 'apiKey',
          rule: 'required',
          message: 'API key is required for OpenAI integration'
        },
        {
          field: 'apiKey',
          rule: 'pattern',
          message: 'API key must start with sk-'
        }
      ],
      advanced: [
        {
          name: 'security',
          title: 'Security Settings',
          description: 'Advanced security and compliance configurations',
          fields: ['baseUrl', 'maxRetries']
        }
      ]
    },
    supportedModels: ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo', 'text-embedding-ada-002'],
    capabilities: ['text-generation', 'embedding', 'chat', 'vision', 'function-calling']
  },
  {
    id: 'anthropic',
    name: 'Anthropic',
    category: 'cloud',
    description: 'Claude models with advanced reasoning capabilities',
    icon: '🧠',
    pricingTier: 'premium',
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
        },
        {
          name: 'maxTokens',
          type: 'number',
          label: 'Max Tokens',
          description: 'Maximum tokens per response',
          required: false,
          default: 4096,
          validation: { min: 1, max: 100000 }
        }
      ],
      validation: []
    },
    supportedModels: ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku'],
    capabilities: ['text-generation', 'chat', 'analysis', 'reasoning']
  },
  {
    id: 'ollama',
    name: 'Ollama',
    category: 'local',
    description: 'Local Ollama server for private deployments',
    icon: '🦙',
    pricingTier: 'free',
    configSchema: {
      fields: [
        {
          name: 'host',
          type: 'string',
          label: 'Host',
          description: 'Ollama server host address',
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
        },
        {
          name: 'model',
          type: 'string',
          label: 'Default Model',
          description: 'Default model to use',
          required: false,
          default: 'llama2'
        }
      ],
      validation: []
    },
    supportedModels: ['llama2', 'codellama', 'mistral', 'mixtral'],
    capabilities: ['text-generation', 'code', 'chat', 'local-inference']
  },
  {
    id: 'azure-openai',
    name: 'Azure OpenAI',
    category: 'enterprise',
    description: 'Azure-hosted OpenAI services with enterprise compliance',
    icon: '☁️',
    pricingTier: 'enterprise',
    configSchema: {
      fields: [
        {
          name: 'apiKey',
          type: 'password',
          label: 'API Key',
          description: 'Azure OpenAI API key',
          required: true,
          sensitive: true
        },
        {
          name: 'endpoint',
          type: 'url',
          label: 'Endpoint',
          description: 'Azure resource endpoint',
          required: true
        },
        {
          name: 'apiVersion',
          type: 'string',
          label: 'API Version',
          description: 'Azure API version',
          required: true,
          default: '2023-12-01-preview'
        },
        {
          name: 'deploymentName',
          type: 'string',
          label: 'Deployment Name',
          description: 'Model deployment name',
          required: true
        }
      ],
      validation: []
    },
    supportedModels: ['gpt-4', 'gpt-35-turbo'],
    capabilities: ['text-generation', 'chat', 'enterprise-compliance']
  }
];

// Enhanced Provider Configuration Interface
const ProviderConfigInterface: React.FC<ProviderConfigInterfaceProps> = ({
  onProviderSaved,
  onProviderDeleted,
  onProviderTested,
  className,
  allowedCategories = ['cloud', 'local', 'custom', 'enterprise'],
  enableAdvancedFeatures = false,
  complianceRequirements
}) => {
  const { toast } = useToast();
  const [providers, setProviders] = useState<ProviderConfig[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<ProviderConfig | null>(null);
  const [selectedType, setSelectedType] = useState<ProviderType | null>(null);
  const [formData, setFormData] = useState<ProviderFormData>({});
  const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);
  const [showSensitive, setShowSensitive] = useState<Record<string, boolean>>({});
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string; details?: unknown } | null>(null);
  const [providerHealth, setProviderHealth] = useState<Record<string, ProviderHealth>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  type ProviderConfigResponse = Omit<ProviderConfig, 'createdAt' | 'updatedAt'> & {
    createdAt: string | Date;
    updatedAt: string | Date;
  };

  const normalizeProvider = useCallback((provider: ProviderConfigResponse): ProviderConfig => ({
    ...provider,
    createdAt: provider.createdAt instanceof Date
      ? provider.createdAt
      : new Date(provider.createdAt),
    updatedAt: provider.updatedAt instanceof Date
      ? provider.updatedAt
      : new Date(provider.updatedAt),
  }), []);

  // Enhanced data loading with retry logic
  const loadProviders = useCallback(async (retryCount = 0) => {
    setLoading(true);
    try {
      const response = await enhancedApiClient.get<
        ProviderConfigResponse[] | { providers?: ProviderConfigResponse[] }
      >('/api/providers', {
        headers: {
          'Cache-Control': 'no-cache',
          'X-Request-ID': `provider-load-${Date.now()}`
        }
      });

      const payload = response.data;
      const providerList = Array.isArray(payload)
        ? payload
        : payload?.providers ?? [];
      const normalizedProviders = providerList.map(normalizeProvider);
      setProviders(normalizedProviders);

      // Validate provider configurations
      normalizedProviders.forEach((provider) => {
        const providerValidationErrors = validateProviderConfig(provider);
        if (providerValidationErrors.length > 0) {
          console.warn(
            `Provider ${provider.id} has configuration issues:`,
            providerValidationErrors
          );
        }
      });
    } catch (error) {
      console.error('Failed to load providers:', error);

      if (retryCount < 3) {
        setTimeout(() => loadProviders(retryCount + 1), 1000 * Math.pow(2, retryCount));
        return;
      }
      
      toast({
        title: 'Connection Error',
        description: 'Failed to load provider configurations. Please check your connection.',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  }, [normalizeProvider, toast, validateProviderConfig]);

  const loadProviderHealth = useCallback(async () => {
    try {
      const response = await enhancedApiClient.get<
        Record<string, ProviderHealth> | { health?: Record<string, ProviderHealth> }
      >('/api/providers/health');
      const payload = response.data;
      const health = payload && typeof payload === 'object' && 'health' in payload
        ? (payload as { health?: Record<string, ProviderHealth> }).health ?? {}
        : (payload as Record<string, ProviderHealth>) ?? {};
      setProviderHealth(health);
    } catch (error) {
      console.error('Failed to load provider health:', error);
    }
  }, []);

  // Enhanced validation with business rules
  const validateField = useCallback((field: ProviderConfigField, value: unknown): ValidationError[] => {
    const errors: ValidationError[] = [];

    if (field.required && (value === undefined || value === '' || value === null)) {
      errors.push({
        field: field.name,
        message: `${field.label} is required`,
        severity: 'error'
      });
      return errors;
    }

    if (value === undefined || value === '' || value === null) {
      return errors;
    }

    switch (field.type) {
      case 'number': {
        const numValue = Number(value);
        if (Number.isNaN(numValue)) {
          errors.push({
            field: field.name,
            message: `${field.label} must be a valid number`,
            severity: 'error'
          });
        } else if (field.validation) {
          if (field.validation.min !== undefined && numValue < field.validation.min) {
            errors.push({
              field: field.name,
              message: `${field.label} must be at least ${field.validation.min}`,
              severity: 'error'
            });
          }
          if (field.validation.max !== undefined && numValue > field.validation.max) {
            errors.push({
              field: field.name,
              message: `${field.label} must be at most ${field.validation.max}`,
              severity: 'error'
            });
          }
        }
        break;
      }

      case 'url': {
        try {
          new URL(String(value));
        } catch {
          errors.push({
            field: field.name,
            message: `${field.label} must be a valid URL`,
            severity: 'error'
          });
        }
        break;
      }

      case 'string': {
        if (field.validation) {
          const stringValue = String(value);
          if (field.validation.minLength && stringValue.length < field.validation.minLength) {
            errors.push({
              field: field.name,
              message: `${field.label} must be at least ${field.validation.minLength} characters`,
              severity: 'error'
            });
          }
          if (field.validation.maxLength && stringValue.length > field.validation.maxLength) {
            errors.push({
              field: field.name,
              message: `${field.label} must be at most ${field.validation.maxLength} characters`,
              severity: 'error'
            });
          }
          if (field.validation.pattern && !new RegExp(field.validation.pattern).test(stringValue)) {
            errors.push({
              field: field.name,
              message: `${field.label} format is invalid`,
              severity: 'error'
            });
          }
        }
        break;
      }
    }

    return errors;
  }, []);

  const validateCompliance = useCallback((
    type: ProviderType,
    _data: ProviderFormData,
    requirements: ComplianceInfo,
  ): ValidationError[] => {
    const errors: ValidationError[] = [];

    if (requirements.gdpr && type.category === 'cloud') {
      errors.push({
        field: 'compliance',
        message: 'Cloud providers may not be GDPR compliant. Consider using local or enterprise providers.',
        severity: 'warning'
      });
    }

    if (requirements.hipaa && type.category !== 'enterprise') {
      errors.push({
        field: 'compliance',
        message: 'HIPAA compliance requires enterprise-grade providers.',
        severity: 'error'
      });
    }

    return errors;
  }, []);

  const shouldShowField = useCallback((field: ProviderConfigField, currentFormData: ProviderFormData): boolean => {
    if (field.advanced && !enableAdvancedFeatures) return false;
    if (!field.dependsOn) return true;
    if (field.condition) return field.condition(currentFormData);

    return currentFormData[field.dependsOn] === true;
  }, [enableAdvancedFeatures]);

  const validateForm = useCallback((type: ProviderType, data: ProviderFormData): ValidationError[] => {
    const errors: ValidationError[] = [];

    // Field-level validation
    type.configSchema.fields.forEach(field => {
      if (!shouldShowField(field, data)) return;

      const value = data[field.name];
      const fieldErrors = validateField(field, value);
      errors.push(...fieldErrors);
    });

    // Custom validation rules
    type.configSchema.validation.forEach(rule => {
      const value = data[rule.field];
      let isValid = true;

      switch (rule.rule) {
        case 'required':
          isValid = value !== undefined && value !== '' && value !== null;
          break;
        case 'pattern':
          if (rule.field === 'apiKey' && value && !value.startsWith('sk-')) {
            isValid = false;
          }
          break;
        case 'custom':
          isValid = rule.validator ? rule.validator(value, data) : true;
          break;
      }

      if (!isValid) {
        errors.push({
          field: rule.field,
          message: rule.message,
          severity: 'error'
        });
      }
    });

    // Compliance validation
    if (complianceRequirements) {
      const complianceErrors = validateCompliance(type, data, complianceRequirements);
      errors.push(...complianceErrors);
    }

    return errors;
  }, [complianceRequirements, shouldShowField, validateCompliance, validateField]);

  const validateProviderConfig = useCallback((provider: ProviderConfig): ValidationError[] => {
    const type = PROVIDER_TYPES.find(t => t.id === provider.type);
    if (!type) return [];

    return validateForm(type, {
      ...provider.configuration,
      ...provider.credentials,
      name: provider.name,
      enabled: provider.enabled
    });
  }, [validateForm]);

  // Enhanced connection testing with detailed diagnostics
  const handleTestConnection = async () => {
    if (!selectedType) return;
    
    const errors = validateForm(selectedType, formData);
    const criticalErrors = errors.filter(e => e.severity === 'error');
    
    if (criticalErrors.length > 0) {
      setValidationErrors(errors);
      toast({
        title: 'Configuration Errors',
        description: 'Please fix the critical errors before testing',
        variant: 'destructive'
      });
      return;
    }

    setTesting(true);
    setTestResult(null);

    try {
      const testPayload = {
        type: selectedType.id,
        configuration: formData,
        metadata: {
          testId: `test-${Date.now()}`,
          timestamp: new Date().toISOString(),
          userAgent: navigator.userAgent
        }
      };

      const response = await enhancedApiClient.post<{
        success?: boolean;
        message?: string;
        details?: unknown;
      }>(
        '/api/providers/test',
        testPayload,
        {
          headers: {
            'X-Test-ID': testPayload.metadata.testId
          },
          timeout: 30000
        }
      );

      const result = response.data ?? {};
      const success = result.success ?? (typeof response.status === 'number' ? response.status < 400 : true);
      const message = result.message || (success ? 'Connection successful' : 'Connection failed');

      setTestResult({
        success,
        message,
        details: result.details
      });

      onProviderTested?.(selectedProvider?.id || 'new', success);

      if (success) {
        toast({
          title: 'Test Successful',
          description: 'Provider connection is working correctly',
          variant: 'default'
        });
      } else {
        toast({
          title: 'Test Failed',
          description: result.message || 'Failed to connect to provider',
          variant: 'destructive'
        });
      }
    } catch (error) {
      const message = error instanceof Error && error.name === 'TimeoutError'
        ? 'Connection test timed out after 30 seconds'
        : 'Network error occurred during testing';
      const details = error instanceof Error ? error.message : String(error);

      setTestResult({
        success: false,
        message,
        details: { error: details }
      });

      toast({
        title: 'Test Error',
        description: message,
        variant: 'destructive'
      });
    } finally {
      setTesting(false);
    }
  };

  // Enhanced save with versioning and audit trail
  const handleSave = async () => {
    if (!selectedType) return;
    
    const errors = validateForm(selectedType, formData);
    const criticalErrors = errors.filter(e => e.severity === 'error');
    
    if (criticalErrors.length > 0) {
      setValidationErrors(errors);
      toast({
        title: 'Validation Failed',
        description: 'Please fix the errors before saving',
        variant: 'destructive'
      });
      return;
    }

    setSaving(true);

    try {
      const providerData: ProviderConfig = {
        id: selectedProvider?.id || `${selectedType.id}-${Date.now()}`,
        name: formData.name || `${selectedType.name} Provider`,
        type: selectedType.id,
        enabled: formData.enabled !== false,
        configuration: Object.fromEntries(
          Object.entries(formData).filter(([key]) => 
            !selectedType.configSchema.fields.find(f => f.name === key)?.sensitive
          )
        ),
        credentials: Object.fromEntries(
          selectedType.configSchema.fields
            .filter(field => field.sensitive)
            .map(field => [field.name, formData[field.name] || ''])
        ),
        metadata: {
          version: '2.0.0',
          description: selectedType.description,
          tags: [selectedType.category, selectedType.pricingTier || 'standard'],
          supportUrl: '',
          documentationUrl: '',
          compliance: {
            gdpr: selectedType.category === 'enterprise',
            hipaa: selectedType.category === 'enterprise',
            soc2: selectedType.category === 'enterprise',
            dataRetention: 30
          }
        },
        createdAt: selectedProvider?.createdAt || new Date(),
        updatedAt: new Date()
      };

      const endpoint = selectedProvider ? `/api/providers/${selectedProvider.id}` : '/api/providers';
      const response = selectedProvider
        ? await enhancedApiClient.put<ProviderConfigResponse>(endpoint, providerData, {
            headers: { 'X-Provider-Version': '2.0.0' }
          })
        : await enhancedApiClient.post<ProviderConfigResponse>(endpoint, providerData, {
            headers: { 'X-Provider-Version': '2.0.0' }
          });

      const savedProviderResponse = response.data;

      if (!savedProviderResponse) {
        throw new Error('Provider response did not include configuration data');
      }

      const savedProvider = normalizeProvider(savedProviderResponse);

      // Update local state
      if (selectedProvider) {
        setProviders(prev => prev.map(p => p.id === selectedProvider.id ? savedProvider : p));
      } else {
        setProviders(prev => [...prev, savedProvider]);
      }

      onProviderSaved?.(savedProvider);

      toast({
        title: 'Provider Saved',
        description: `${savedProvider.name} has been configured successfully`,
        variant: 'default'
      });

      // Reset form
      resetSelection();

    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to save provider configuration';
      toast({
        title: 'Save Failed',
        description: message,
        variant: 'destructive'
      });
    } finally {
      setSaving(false);
    }
  };

  // Handle field changes
  const handleFieldChange = useCallback((fieldName: string, value: unknown) => {
    setFormData(prev => ({
      ...prev,
      [fieldName]: value
    }));

    // Clear validation error for this field
    setValidationErrors(prev => prev.filter(error => error.field !== fieldName));
  }, [resetSelection]);

  const handleRefresh = useCallback(() => {
    void loadProviders();
    void loadProviderHealth();
  }, [loadProviderHealth, loadProviders]);

  const resetSelection = useCallback(() => {
    setSelectedProvider(null);
    setSelectedType(null);
    setFormData({});
    setValidationErrors([]);
    setShowSensitive({});
    setTestResult(null);
  }, []);

  const handleSelectProvider = useCallback((provider: ProviderConfig) => {
    const type = PROVIDER_TYPES.find(t => t.id === provider.type) || null;
    setSelectedProvider(provider);
    setSelectedType(type);

    const mergedData: ProviderFormData = {
      name: provider.name,
      enabled: provider.enabled,
      ...provider.configuration,
      ...provider.credentials,
    };

    type?.configSchema.fields.forEach(field => {
      if (mergedData[field.name] === undefined && field.default !== undefined) {
        mergedData[field.name] = field.default;
      }
    });

    setFormData(mergedData);
    setValidationErrors([]);
    setShowSensitive({});
    setTestResult(null);
  }, []);

  const handleSelectType = useCallback((type: ProviderType) => {
    setSelectedProvider(null);
    setSelectedType(type);

    const defaults = type.configSchema.fields.reduce<ProviderFormData>((acc, field) => {
      if (field.default !== undefined) {
        acc[field.name] = field.default;
      }
      return acc;
    }, {});

    setFormData({
      name: `${type.name} Provider`,
      enabled: true,
      ...defaults
    });
    setValidationErrors([]);
    setShowSensitive({});
    setTestResult(null);
  }, []);

  const handleDeleteProvider = useCallback(async (providerId: string) => {
    setDeletingId(providerId);
    try {
      await enhancedApiClient.delete(`/api/providers/${providerId}`);
      setProviders(prev => prev.filter(provider => provider.id !== providerId));
      if (selectedProvider?.id === providerId) {
        resetSelection();
      }
      onProviderDeleted?.(providerId);
      toast({
        title: 'Provider Removed',
        description: 'The provider has been deleted successfully.',
        variant: 'default'
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to delete provider';
      toast({
        title: 'Delete Failed',
        description: message,
        variant: 'destructive'
      });
    } finally {
      setDeletingId(null);
    }
  }, [onProviderDeleted, resetSelection, selectedProvider, toast]);

  const toPercent = (value?: number) => {
    if (value === undefined || value === null) {
      return 0;
    }
    const numeric = Number(value);
    if (Number.isNaN(numeric)) {
      return 0;
    }
    return numeric <= 1 ? Math.round(numeric * 100) : Math.round(numeric);
  };

  // Enhanced field rendering with conditional logic
  const renderField = (field: ProviderConfigField) => {
    if (!shouldShowField(field, formData)) return null;

    const rawValue = formData[field.name];
    const value = rawValue ?? field.default ?? (field.type === 'number' ? '' : '');
    const error = validationErrors.find(e => e.field === field.name);
    const isVisible = showSensitive[field.name] || !field.sensitive;

    return (
      <div key={field.name} className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor={field.name} className="flex items-center gap-2">
            {field.label}
            {field.required && <span className="text-red-500">*</span>}
            {field.sensitive && <Lock className="w-3 h-3 text-gray-500" />}
            {field.advanced && <Badge variant="outline" className="text-xs">Advanced</Badge>}
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
              {isVisible ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </Button>
          )}
        </div>

        {field.type === 'select' ? (
          <Select
            value={typeof value === 'string' ? value : ''}
            onValueChange={(val) => handleFieldChange(field.name, val)}
          >
            <SelectTrigger className={error ? 'border-red-500' : ''}>
              <SelectValue placeholder={`Select ${field.label}`} />
            </SelectTrigger>
            <SelectContent>
              {field.options?.map(option => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        ) : field.type === 'boolean' ? (
          <div className="flex items-center space-x-2">
            <Switch
              id={field.name}
              checked={!!value}
              onCheckedChange={(checked) => handleFieldChange(field.name, checked)}
            />
            <Label htmlFor={field.name} className="text-sm">
              {field.description}
            </Label>
          </div>
        ) : field.type === 'textarea' ? (
          <Textarea
            id={field.name}
            value={typeof value === 'string' ? value : ''}
            onChange={(e) => handleFieldChange(field.name, e.target.value)}
            placeholder={field.description}
            className={error ? 'border-red-500' : ''}
            rows={3}
          />
        ) : (
          <Input
            id={field.name}
            type={field.sensitive && !isVisible ? 'password' :
                  field.type === 'number' ? 'number' : 'text'}
            value={value as string | number | readonly string[]}
            onChange={(e) => {
              const nextValue = field.type === 'number'
                ? (e.target.value === '' ? '' : Number(e.target.value))
                : e.target.value;
              handleFieldChange(field.name, nextValue);
            }}
            placeholder={field.description}
            className={error ? 'border-red-500' : ''}
          />
        )}

        {field.description && field.type !== 'boolean' && (
          <p className="text-xs text-gray-600">{field.description}</p>
        )}

        {error && (
          <p className={`text-xs flex items-center gap-1 ${
            error.severity === 'error' ? 'text-red-600' : 'text-yellow-600'
          }`}>
            <AlertTriangle className="w-3 h-3" />
            {error.message}
          </p>
        )}
      </div>
    );
  };

  // Health monitoring with polling
  useEffect(() => {
    loadProviders();
    loadProviderHealth();

    const interval = setInterval(loadProviderHealth, 30000); // Every 30 seconds
    return () => clearInterval(interval);
  }, [loadProviderHealth, loadProviders]);

  // Filter providers by allowed categories
  const filteredProviderTypes = PROVIDER_TYPES.filter(type => 
    allowedCategories.includes(type.category)
  );

  const containerClassName = ['space-y-6', className].filter(Boolean).join(' ');
  const criticalErrors = validationErrors.filter(error => error.severity === 'error');
  const warningErrors = validationErrors.filter(error => error.severity === 'warning');

  return (
    <ErrorBoundary
      fallback={({ error }) => (
        <div className="p-4 text-center">
          <AlertTriangle className="w-8 h-8 mx-auto mb-2 text-red-500" />
          <h3 className="text-lg font-medium">Configuration Error</h3>
          <p className="text-gray-600">Please refresh the page and try again.</p>
          {error && <p className="text-sm text-gray-500 mt-2">{error.message}</p>}
        </div>
      )}
    >
      <div className={containerClassName}>
        <div className="grid gap-6 lg:grid-cols-[1fr,2fr]">
          <Card className="h-full">
            <CardHeader className="flex flex-row items-center justify-between gap-2">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-4 w-4" /> Configured Providers
                </CardTitle>
                <CardDescription>Manage provider connections and monitor health.</CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={handleRefresh}
                  disabled={loading}
                  aria-label="Refresh providers"
                >
                  <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                </Button>
                <Button type="button" onClick={resetSelection} variant="outline" size="sm">
                  <Plus className="mr-2 h-4 w-4" /> New Provider
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {loading ? (
                <p className="text-sm text-gray-600">Loading providers...</p>
              ) : providers.length === 0 ? (
                <p className="text-sm text-gray-600">No providers configured yet. Select a provider type to get started.</p>
              ) : (
                <ul className="space-y-3">
                  {providers.map(provider => {
                    const type = PROVIDER_TYPES.find(t => t.id === provider.type);
                    const health = providerHealth[provider.id];
                    const isSelected = selectedProvider?.id === provider.id;
                    const statusIcon = health?.status === 'healthy'
                      ? <CheckCircle className="h-4 w-4 text-green-500" />
                      : health?.status === 'unhealthy'
                        ? <XCircle className="h-4 w-4 text-red-500" />
                        : <Activity className="h-4 w-4 text-yellow-500" />;

                    return (
                      <li key={provider.id} className="rounded-lg border p-3">
                        <button
                          type="button"
                          className={`w-full rounded-md p-3 text-left transition ${isSelected
                            ? 'border border-primary bg-primary/5'
                            : 'border border-transparent hover:bg-muted/50'}`}
                          onClick={() => handleSelectProvider(provider)}
                        >
                          <div className="flex items-center justify-between gap-2">
                            <div>
                              <p className="font-medium">{provider.name}</p>
                              <p className="text-xs text-gray-500">{type?.name ?? provider.type}</p>
                            </div>
                            <div className="flex items-center gap-2">
                              {statusIcon}
                              <Badge variant="outline">{provider.enabled ? 'Enabled' : 'Disabled'}</Badge>
                            </div>
                          </div>
                          {health ? (
                            <div className="mt-3 space-y-2">
                              <div className="flex items-center justify-between text-xs text-gray-600">
                                <span>Uptime</span>
                                <span>{toPercent(health.uptime)}%</span>
                              </div>
                              <Progress value={Math.max(0, Math.min(100, toPercent(health.uptime)))} />
                              <div className="flex items-center justify-between text-xs text-gray-600">
                                <span>Response</span>
                                <span>{health.responseTime}ms</span>
                              </div>
                            </div>
                          ) : (
                            <p className="mt-3 text-xs text-gray-500">No health data available.</p>
                          )}
                        </button>
                        <div className="mt-2 flex justify-end">
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteProvider(provider.id)}
                            disabled={deletingId === provider.id}
                          >
                            <Trash2 className="mr-2 h-4 w-4" />
                            {deletingId === provider.id ? 'Deleting...' : 'Delete'}
                          </Button>
                        </div>
                      </li>
                    );
                  })}
                </ul>
              )}
            </CardContent>
          </Card>

          <Card className="h-full">
            <CardHeader>
              <CardTitle>
                {selectedType ? `${selectedType.name} Configuration` : 'Select a Provider Type'}
              </CardTitle>
              <CardDescription>
                {selectedType
                  ? 'Configure credentials, endpoints, and advanced settings for this provider.'
                  : 'Choose a provider type to begin configuring a new integration.'}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {selectedType ? (
                <div className="space-y-6">
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="provider-name">Provider Name</Label>
                      <Input
                        id="provider-name"
                        value={typeof formData.name === 'string' ? formData.name : ''}
                        placeholder="Friendly name for this provider"
                        onChange={(event) => handleFieldChange('name', event.target.value)}
                      />
                    </div>
                    <div className="flex items-center justify-between rounded-md border p-3">
                      <div>
                        <Label htmlFor="provider-enabled">Provider Status</Label>
                        <p className="text-xs text-gray-600">Enable to allow routing to this provider.</p>
                      </div>
                      <Switch
                        id="provider-enabled"
                        checked={formData.enabled !== false}
                        onCheckedChange={(checked) => handleFieldChange('enabled', checked)}
                      />
                    </div>
                  </div>

                  <div className="grid gap-4 md:grid-cols-2">
                    {selectedType.configSchema.fields.map(renderField)}
                  </div>

                  {criticalErrors.length > 0 && (
                    <Alert variant="destructive">
                      <AlertTitle>Configuration Issues</AlertTitle>
                      <AlertDescription>
                        Resolve all critical errors before testing or saving this provider.
                      </AlertDescription>
                    </Alert>
                  )}

                  {warningErrors.length > 0 && criticalErrors.length === 0 && (
                    <Alert>
                      <AlertTitle>Warnings Detected</AlertTitle>
                      <AlertDescription>
                        Review the highlighted warnings to ensure the configuration meets your compliance needs.
                      </AlertDescription>
                    </Alert>
                  )}

                  {testResult && (
                    <Alert variant={testResult.success ? 'default' : 'destructive'}>
                      <AlertTitle>{testResult.success ? 'Connection Successful' : 'Connection Failed'}</AlertTitle>
                      <AlertDescription>{testResult.message}</AlertDescription>
                    </Alert>
                  )}

                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={handleTestConnection}
                      disabled={testing || saving}
                    >
                      <TestTube className="mr-2 h-4 w-4" />
                      {testing ? 'Testing...' : 'Test Connection'}
                    </Button>
                    <div className="flex items-center gap-2">
                      {selectedProvider && (
                        <Button type="button" variant="ghost" onClick={resetSelection}>
                          Cancel
                        </Button>
                      )}
                      <Button
                        type="button"
                        onClick={handleSave}
                        disabled={saving || testing}
                      >
                        <Save className="mr-2 h-4 w-4" />
                        {saving ? 'Saving...' : selectedProvider ? 'Update Provider' : 'Save Provider'}
                      </Button>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="grid gap-4 sm:grid-cols-2">
                  {filteredProviderTypes.map(type => (
                    <button
                      key={type.id}
                      type="button"
                      className="rounded-lg border p-4 text-left transition hover:border-primary"
                      onClick={() => handleSelectType(type)}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-2xl" aria-hidden>{type.icon}</span>
                        <Badge variant="outline" className="capitalize">{type.category}</Badge>
                      </div>
                      <p className="mt-3 font-medium">{type.name}</p>
                      <p className="mt-1 text-xs text-gray-600">{type.description}</p>
                    </button>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {providers.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Health Overview</CardTitle>
              <CardDescription>Quick glance at provider reliability across your integrations.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {providers.map(provider => {
                const health = providerHealth[provider.id];
                const type = PROVIDER_TYPES.find(t => t.id === provider.type);
                return (
                  <div key={provider.id} className="rounded-lg border p-4">
                    <div className="flex items-center justify-between">
                      <p className="font-medium">{provider.name}</p>
                      <Badge variant="outline" className="text-xs">{type?.category ?? provider.type}</Badge>
                    </div>
                    {health ? (
                      <div className="mt-3 space-y-2 text-xs text-gray-600">
                        <div className="flex justify-between">
                          <span>Status</span>
                          <span className="capitalize">{health.status}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Success Rate</span>
                          <span>{toPercent(health.metrics.successRate)}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Latency</span>
                          <span>{health.responseTime}ms</span>
                        </div>
                      </div>
                    ) : (
                      <p className="mt-3 text-xs text-gray-500">No recent health checks.</p>
                    )}
                  </div>
                );
              })}
            </CardContent>
          </Card>
        )}
      </div>
    </ErrorBoundary>
  );
};

export default ProviderConfigInterface;
