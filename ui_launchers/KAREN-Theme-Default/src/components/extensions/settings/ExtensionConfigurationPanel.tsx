/**
 * Extension Configuration Panel Component
 * 
 * Provides a comprehensive interface for configuring extension settings,
 * permissions, and advanced options.
 */
"use client";

import { useCallback, useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../ui/tabs';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';

import {
  Settings,
  Shield,
  Eye,
  EyeOff,
  Info,
  Database,
  Globe,
  Key,
  RefreshCw,
  RotateCcw,
  Save,
  AlertTriangle,
  Copy,
  FileText,
  Code,
  Zap
} from 'lucide-react';

type SettingPrimitive = string | number | boolean;
type SettingValue = SettingPrimitive | SettingPrimitive[] | Record<string, unknown> | null;

interface SettingFieldProps {
  setting: ExtensionSetting;
  showSensitive: boolean;
  onChange: (value: SettingValue) => void;
  onToggleSensitive: () => void;
}

interface ExtensionSetting {
  key: string;
  label: string;
  description?: string;
  type: 'string' | 'number' | 'boolean' | 'select' | 'multiselect' | 'password' | 'json' | 'array';
  value: SettingValue;
  defaultValue: SettingValue;
  validation?: {
    required?: boolean;
    min?: number;
    max?: number;
    step?: number;
    pattern?: string;
    options?: { value: SettingPrimitive; label: string }[];
  };
  group?: string;
  sensitive?: boolean;
  readonly?: boolean;
}
interface ExtensionPermission {
  key: string;
  label: string;
  description: string;
  granted: boolean;
  required: boolean;
  category: 'filesystem' | 'network' | 'system' | 'data' | 'api';
}
interface ExtensionConfigurationPanelProps {
  extensionId: string;
  extensionName: string;
  className?: string;
  onSave?: (settings: Record<string, SettingValue>) => Promise<void>;
  onReset?: () => Promise<void>;
  onPermissionChange?: (permission: string, granted: boolean) => Promise<void>;
}

// Helper functions
function valueToString(value: SettingValue): string {
  if (value == null) return '';
  if (Array.isArray(value)) {
    return value.map((item) => valueToString(item)).join(', ');
  }
  if (typeof value === 'object') {
    try {
      return JSON.stringify(value);
    } catch (error) {
      return '';
    }
  }
  return String(value);
}

function isPrimitiveArray(value: SettingValue): value is SettingPrimitive[] {
  return Array.isArray(value) && value.every((item) => ['string', 'number', 'boolean'].includes(typeof item));
}

function SettingField({ setting, showSensitive, onChange, onToggleSensitive }: SettingFieldProps) {
  const textValue = valueToString(setting.value);
  const defaultPlaceholder = typeof setting.defaultValue === 'string' ? setting.defaultValue : undefined;

  const renderInput = () => {
    switch (setting.type) {
      case 'string':
      case 'password':
        return (
          <div className="relative">
            <input
              type={setting.type === 'password' && !showSensitive ? 'password' : 'text'}
              value={textValue}
              onChange={(e) => onChange(e.target.value)}
              disabled={setting.readonly}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
              placeholder={defaultPlaceholder}
            />
            {setting.sensitive && (
              <Button
                type="button"
                onClick={onToggleSensitive}
                variant="ghost"
                size="sm"
                className="absolute right-1 top-1/2 transform -translate-y-1/2 h-8 w-8 p-0"
              >
                {showSensitive ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </Button>
            )}
          </div>
        );
      case 'number':
        return (
          <input
            type="number"
            value={typeof setting.value === 'number' ? setting.value : ''}
            onChange={(e) => onChange(Number(e.target.value))}
            disabled={setting.readonly}
            min={setting.validation?.min}
            max={setting.validation?.max}
            step={setting.validation?.step}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
          />
        );
      case 'boolean': {
        const booleanValue = typeof setting.value === 'boolean' ? setting.value : Boolean(setting.value);
        return (
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={booleanValue}
              onChange={(e) => onChange(e.target.checked)}
              disabled={setting.readonly}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <span className="ml-2 text-sm text-gray-700 md:text-base lg:text-lg">
              {booleanValue ? 'Enabled' : 'Disabled'}
            </span>
          </label>
        );
      }
      case 'select': {
        const options = setting.validation?.options ?? [];
        const selectedValue = (() => {
          if (typeof setting.value === 'string' || typeof setting.value === 'number') {
            return setting.value;
          }
          if (typeof setting.value === 'boolean') {
            return setting.value ? 'true' : 'false';
          }
          return '';
        })();

        const toRawValue = (raw: string): SettingValue => {
          const match = options.find((option) => {
            const optionString = typeof option.value === 'boolean'
              ? (option.value ? 'true' : 'false')
              : option.value.toString();
            return optionString === raw;
          });

          if (!match) {
            return raw;
          }

          if (typeof match.value === 'boolean') {
            return match.value;
          }

          if (typeof match.value === 'number') {
            return match.value;
          }

          return match.value;
        };

        return (
          <select
            value={selectedValue}
            onChange={(e) => onChange(toRawValue(e.target.value))}
            disabled={setting.readonly}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
          >
            {options.map((option) => {
              const optionValue = typeof option.value === 'boolean'
                ? option.value ? 'true' : 'false'
                : option.value.toString();
              return (
                <option key={`${setting.key}-${optionValue}`} value={optionValue}>
                  {option.label}
                </option>
              );
            })}
          </select>
        );
      }
      case 'multiselect': {
        const options = setting.validation?.options ?? [];
        const selectedValues = isPrimitiveArray(setting.value)
          ? setting.value.map((item) => (typeof item === 'boolean' ? (item ? 'true' : 'false') : item.toString()))
          : [];

        const mapRawValues = (rawValues: string[]): SettingPrimitive[] =>
          rawValues.map((raw) => {
            const match = options.find((option) => {
              const optionValue = typeof option.value === 'boolean'
                ? option.value ? 'true' : 'false'
                : option.value.toString();
              return optionValue === raw;
            });

            if (!match) {
              return raw;
            }

            return match.value;
          });

        return (
          <select
            multiple
            value={selectedValues}
            onChange={(e) => {
              const values = Array.from(e.target.selectedOptions, (option) => option.value);
              onChange(mapRawValues(values));
            }}
            disabled={setting.readonly}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
          >
            {options.map((option) => {
              const optionValue = typeof option.value === 'boolean'
                ? option.value ? 'true' : 'false'
                : option.value.toString();
              return (
                <option key={`${setting.key}-${optionValue}`} value={optionValue}>
                  {option.label}
                </option>
              );
            })}
          </select>
        );
      }
      default:
        return null;
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-gray-700 md:text-base lg:text-lg">
          {setting.label}
          {setting.validation?.required && (
            <span className="text-red-500 ml-1">*</span>
          )}
        </label>
        {setting.sensitive && (
          <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
            <Shield className="h-2 w-2 mr-1" />
            Sensitive
          </Badge>
        )}
      </div>
      {setting.description && (
        <p className="text-xs text-gray-500 sm:text-sm md:text-base">{setting.description}</p>
      )}
      {renderInput()}
      {setting.value !== setting.defaultValue && (
        <div className="flex items-center gap-1 text-xs text-blue-600 sm:text-sm md:text-base">
          <Info className="h-3 w-3" />
          <span>Modified from default: {JSON.stringify(setting.defaultValue)}</span>
        </div>
      )}
    </div>
  );
}

interface PermissionFieldProps {
  permission: ExtensionPermission;
  onChange: (granted: boolean) => void;
}

function PermissionField({ permission, onChange }: PermissionFieldProps) {
  return (
    <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg sm:p-4 md:p-6">
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <h4 className="font-medium text-gray-900">{permission.label}</h4>
          {permission.required && (
            <Badge variant="destructive" className="text-xs sm:text-sm md:text-base">Required</Badge>
          )}
        </div>
        <p className="text-sm text-gray-600 mt-1 md:text-base lg:text-lg">{permission.description}</p>
      </div>
      <div className="flex items-center gap-3">
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={permission.granted}
            onChange={(e) => onChange(e.target.checked)}
            disabled={permission.required}
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <span className="ml-2 text-sm text-gray-700 md:text-base lg:text-lg">
            {permission.granted ? 'Granted' : 'Denied'}
          </span>
        </label>
      </div>
    </div>
  );
}

function getCategoryIcon(category: string) {
  switch (category) {
    case 'filesystem':
      return <Database className="h-4 w-4" />;
    case 'network':
      return <Globe className="h-4 w-4" />;
    case 'system':
      return <Settings className="h-4 w-4" />;
    case 'data':
      return <Shield className="h-4 w-4" />;
    case 'api':
      return <Key className="h-4 w-4" />;
    default:
      return <Settings className="h-4 w-4" />;
  }
}

export function ExtensionConfigurationPanel({
  extensionId,
  extensionName,
  className,
  onSave,
  onReset,
  onPermissionChange
}: ExtensionConfigurationPanelProps) {
  const [activeTab, setActiveTab] = useState('settings');
  const [settings, setSettings] = useState<ExtensionSetting[]>([]);
  const [permissions, setPermissions] = useState<ExtensionPermission[]>([]);
  const [hasChanges, setHasChanges] = useState(false);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showSensitive, setShowSensitive] = useState<Set<string>>(new Set());
  // Load extension configuration
  useEffect(() => {
    loadConfiguration();
  }, [extensionId]);
  const loadConfiguration = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Simulate loading configuration from API
      await new Promise(resolve => setTimeout(resolve, 1000));
      // 
      const sampleSettings: ExtensionSetting[] = [
        {
          key: 'api_endpoint',
          label: 'API Endpoint',
          description: 'Base URL for the extension API',
          type: 'string',
          value: 'https://api.example.com/v1',
          defaultValue: 'https://api.example.com/v1',
          group: 'connection',
          validation: {
            required: true,
            pattern: '^https?://.+'
          }
        },
        {
          key: 'api_key',
          label: 'API Key',
          description: 'Authentication key for API access',
          type: 'password',
          value: 'sk-1234567890abcdef',
          defaultValue: '',
          group: 'authentication',
          sensitive: true,
          validation: {
            required: true
          }
        },
        {
          key: 'timeout',
          label: 'Request Timeout',
          description: 'Timeout for API requests in seconds',
          type: 'number',
          value: 30,
          defaultValue: 30,
          group: 'connection',
          validation: {
            min: 1,
            max: 300,
            step: 1
          }
        },
        {
          key: 'enable_caching',
          label: 'Enable Caching',
          description: 'Cache API responses to improve performance',
          type: 'boolean',
          value: true,
          defaultValue: true,
          group: 'performance'
        },
        {
          key: 'log_level',
          label: 'Log Level',
          description: 'Minimum level for logging messages',
          type: 'select',
          value: 'info',
          defaultValue: 'info',
          group: 'debugging',
          validation: {
            options: [
              { value: 'debug', label: 'Debug' },
              { value: 'info', label: 'Info' },
              { value: 'warning', label: 'Warning' },
              { value: 'error', label: 'Error' }
            ]
          }
        },
        {
          key: 'allowed_domains',
          label: 'Allowed Domains',
          description: 'List of domains that can access this extension',
          type: 'array',
          value: ['example.com', 'api.example.com'],
          defaultValue: [],
          group: 'security'
        },
        {
          key: 'webhook_config',
          label: 'Webhook Configuration',
          description: 'JSON configuration for webhook endpoints',
          type: 'json',
          value: {
            url: 'https://webhook.example.com',
            secret: 'webhook-secret',
            events: ['create', 'update', 'delete']
          },
          defaultValue: {},
          group: 'integration'
        }
      ];
      const samplePermissions: ExtensionPermission[] = [
        {
          key: 'filesystem_read',
          label: 'Read Files',
          description: 'Read files from the local filesystem',
          granted: true,
          required: true,
          category: 'filesystem'
        },
        {
          key: 'filesystem_write',
          label: 'Write Files',
          description: 'Write files to the local filesystem',
          granted: false,
          required: false,
          category: 'filesystem'
        },
        {
          key: 'network_outbound',
          label: 'Outbound Network Access',
          description: 'Make HTTP requests to external services',
          granted: true,
          required: true,
          category: 'network'
        },
        {
          key: 'network_inbound',
          label: 'Inbound Network Access',
          description: 'Accept incoming HTTP requests',
          granted: false,
          required: false,
          category: 'network'
        },
        {
          key: 'system_metrics',
          label: 'System Metrics',
          description: 'Access system performance metrics',
          granted: true,
          required: false,
          category: 'system'
        },
        {
          key: 'data_user_profiles',
          label: 'User Profile Data',
          description: 'Access user profile information',
          granted: true,
          required: true,
          category: 'data'
        }
      ];
      setSettings(sampleSettings);
      setPermissions(samplePermissions);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load configuration');
    } finally {
      setLoading(false);
    }
  }, [extensionId]);
  const handleSettingChange = useCallback((key: string, value: SettingValue) => {
    setSettings(prev => prev.map(setting =>
      setting.key === key ? { ...setting, value } : setting
    ));
    setHasChanges(true);
  }, []);
  const handlePermissionChange = useCallback(async (key: string, granted: boolean) => {
    try {
      if (onPermissionChange) {
        await onPermissionChange(key, granted);
      }
      setPermissions(prev => prev.map(permission =>
        permission.key === key ? { ...permission, granted } : permission
      ));
    } catch (error) {
      console.error(`Failed to update permission ${key}`, error);
    }
  }, [onPermissionChange]);
  const handleSave = useCallback(async () => {
    setSaving(true);
    setError(null);
    try {
      const settingsObject = settings.reduce<Record<string, SettingValue>>((acc, setting) => {
        acc[setting.key] = setting.value;
        return acc;
      }, {});
      if (onSave) {
        await onSave(settingsObject);
      }
      setHasChanges(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save configuration');
    } finally {
      setSaving(false);
    }
  }, [settings, onSave]);
  const handleReset = useCallback(async () => {
    try {
      if (onReset) {
        await onReset();
      }
      setSettings(prev => prev.map(setting => ({
        ...setting,
        value: setting.defaultValue
      })));
      setHasChanges(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reset configuration');
    }
  }, [onReset]);
  const toggleSensitiveVisibility = useCallback((key: string) => {
    setShowSensitive(prev => {
      const newSet = new Set(prev);
      if (newSet.has(key)) {
        newSet.delete(key);
      } else {
        newSet.add(key);
      }
      return newSet;
    });
  }, []);
  const groupedSettings = settings.reduce((acc, setting) => {
    const group = setting.group || 'general';
    if (!acc[group]) acc[group] = [];
    acc[group].push(setting);
    return acc;
  }, {} as Record<string, ExtensionSetting[]>);
  const groupedPermissions = permissions.reduce((acc, permission) => {
    if (!acc[permission.category]) acc[permission.category] = [];
    acc[permission.category].push(permission);
    return acc;
  }, {} as Record<string, ExtensionPermission[]>);
  if (loading) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4 " />
          <p className="text-gray-600">Loading configuration...</p>
        </div>
      </div>
    );
  }
  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Extension Configuration</h1>
          <p className="text-gray-600 mt-1">Configure settings and permissions for {extensionName}</p>
        </div>
        <div className="flex gap-2">
          {hasChanges && (
            <Button
              variant="outline"
              onClick={handleReset}
              className="flex items-center gap-2"
            >
              <RotateCcw className="h-4 w-4" />
              Reset Changes
            </Button>
          )}
          <Button
            onClick={handleSave}
            disabled={!hasChanges || saving}
            className="flex items-center gap-2"
          >
            {saving ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              <Save className="h-4 w-4" />
            )}
            {saving ? 'Saving...' : 'Save Changes'}
          </Button>
        </div>
      </div>
      {/* Error Display */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-center">
              <AlertTriangle className="h-5 w-5 text-red-500 mr-3 " />
              <div>
                <h3 className="font-semibold text-red-800">Configuration Error</h3>
                <p className="text-red-700">{error}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
      {/* Configuration Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="settings">Settings</TabsTrigger>
          <TabsTrigger value="permissions">Permissions</TabsTrigger>
          <TabsTrigger value="advanced">Advanced</TabsTrigger>
        </TabsList>
        <TabsContent value="settings" className="space-y-6">
          {Object.entries(groupedSettings).map(([group, groupSettings]) => (
            <Card key={group}>
              <CardHeader>
                <CardTitle className="capitalize">{group.replace('_', ' ')} Settings</CardTitle>
                <CardDescription>
                  Configure {group} related options for this extension
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {groupSettings.map(setting => (
                  <SettingField
                    key={setting.key}
                    setting={setting}
                    showSensitive={showSensitive.has(setting.key)}
                    onChange={(value) => handleSettingChange(setting.key, value)}
                    onToggleSensitive={() => toggleSensitiveVisibility(setting.key)}
                  />
                ))}
              </CardContent>
            </Card>
          ))}
        </TabsContent>
        <TabsContent value="permissions" className="space-y-6">
          {Object.entries(groupedPermissions).map(([category, categoryPermissions]) => (
            <Card key={category}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 capitalize">
                  {getCategoryIcon(category)}
                  {category} Permissions
                </CardTitle>
                <CardDescription>
                  Manage {category} access permissions for this extension
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {categoryPermissions.map(permission => (
                  <PermissionField
                    key={permission.key}
                    permission={permission}
                    onChange={(granted) => handlePermissionChange(permission.key, granted)}
                  />
                ))}
              </CardContent>
            </Card>
          ))}
        </TabsContent>
        <TabsContent value="advanced" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Advanced Configuration</CardTitle>
              <CardDescription>
                Access diagnostics, metadata, and low-level tools for this extension
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium md:text-base lg:text-lg">Extension ID</label>
                  <div className="flex items-center gap-2">
                    <code className="flex-1 px-3 py-2 bg-gray-100 rounded text-sm font-mono md:text-base lg:text-lg">
                      {extensionId}
                    </code>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => navigator.clipboard.writeText(extensionId)}
                    >
                      <Copy className="h-3 w-3 " />
                    </Button>
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium md:text-base lg:text-lg">Configuration Path</label>
                  <div className="flex items-center gap-2">
                    <code className="flex-1 px-3 py-2 bg-gray-100 rounded text-sm font-mono md:text-base lg:text-lg">
                      /extensions/{extensionId}/config
                    </code>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => navigator.clipboard.writeText(`/extensions/${extensionId}/config`)}
                    >
                      <Copy className="h-3 w-3 " />
                    </Button>
                  </div>
                </div>
              </div>
              <div className="pt-4 border-t border-gray-200">
                <h4 className="font-medium mb-3">Debug Actions</h4>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" >
                    <FileText className="h-3 w-3 mr-1 " />
                  </Button>
                  <Button variant="outline" size="sm" >
                    <Code className="h-3 w-3 mr-1 " />
                  </Button>
                  <Button variant="outline" size="sm" >
                    <Zap className="h-3 w-3 mr-1 " />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
