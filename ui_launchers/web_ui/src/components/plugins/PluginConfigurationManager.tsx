import React, { useState, useEffect } from 'react';
import { ErrorBoundary } from '@/components/error-handling/ErrorBoundary';
import { 
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Checkbox } from '@/components/ui/checkbox';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Progress } from '@/components/ui/progress';
import {
import { PluginInfo, PluginConfig, PluginConfigField } from '@/types/plugins';
/**
 * Plugin Configuration Manager Component
 * 
 * Dynamic plugin configuration forms based on plugin manifests.
 * Based on requirements: 5.3, 5.5, 9.1, 9.2, 9.4
 */
"use client";


  Settings, 
  Save, 
  RotateCcw, 
  Eye, 
  EyeOff, 
  Shield, 
  Lock, 
  Unlock,
  AlertTriangle, 
  CheckCircle, 
  Info, 
  Copy,
  Download,
  Upload,
  FileText,
  Key,
  Database,
  Network,
  HardDrive,
  Cpu,
  Globe,
  Users,
  Calendar,
  Clock,
  Zap,
  Target,
  Filter,
  Search,
  RefreshCw,
  ExternalLink,
  Edit,
  Trash2,
  Plus,
  Minus,
} from 'lucide-react';









  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';







  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';

  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';

interface ValidationError {
  field: string;
  message: string;
}
interface ConfigurationSection {
  id: string;
  name: string;
  description: string;
  fields: PluginConfigField[];
  collapsed?: boolean;
}
interface PluginConfigurationManagerProps {
  plugin: PluginInfo;
  onSave: (config: PluginConfig) => Promise<void>;
  onReset: () => Promise<void>;
  onExport?: (config: PluginConfig) => void;
  onImport?: (config: PluginConfig) => void;
  readOnly?: boolean;
}
export const PluginConfigurationManager: React.FC<PluginConfigurationManagerProps> = ({
  plugin,
  onSave,
  onReset,
  onExport,
  onImport,
  readOnly = false,
}) => {
  const [config, setConfig] = useState<PluginConfig>(plugin.config || {});
  const [originalConfig] = useState<PluginConfig>(plugin.config || {});
  const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);
  const [saving, setSaving] = useState(false);
  const [showPasswords, setShowPasswords] = useState<Record<string, boolean>>({});
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['general']));
  const [searchQuery, setSearchQuery] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);
  // Group configuration fields into sections
  const sections: ConfigurationSection[] = React.useMemo(() => {
    if (!plugin.manifest.configSchema) return [];
    const sectionMap = new Map<string, PluginConfigField[]>();
    plugin.manifest.configSchema.forEach(field => {
      const section = field.key.includes('.') ? field.key.split('.')[0] : 'general';
      if (!sectionMap.has(section)) {
        sectionMap.set(section, []);
      }
      sectionMap.get(section)!.push(field);
    });
    return Array.from(sectionMap.entries()).map(([id, fields]) => ({
      id,
      name: id.charAt(0).toUpperCase() + id.slice(1).replace(/([A-Z])/g, ' $1'),
      description: `Configure ${id} settings for ${plugin.name}`,
      fields,
    }));
  }, [plugin.manifest.configSchema, plugin.name]);
  // Filter fields based on search query
  const filteredSections = React.useMemo(() => {
    if (!searchQuery) return sections;
    return sections.map(section => ({
      ...section,
      fields: section.fields.filter(field =>
        field.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
        field.key.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (field.description && field.description.toLowerCase().includes(searchQuery.toLowerCase()))
      ),
    })).filter(section => section.fields.length > 0);
  }, [sections, searchQuery]);
  const validateField = (field: PluginConfigField, value: any): string | null => {
    if (field.required && (value === undefined || value === null || value === '')) {
      return `${field.label} is required`;
    }
    if (field.validation) {
      const { min, max, pattern, custom } = field.validation;
      if (field.type === 'number' && typeof value === 'number') {
        if (min !== undefined && value < min) {
          return `${field.label} must be at least ${min}`;
        }
        if (max !== undefined && value > max) {
          return `${field.label} must be at most ${max}`;
        }
      }
      if (field.type === 'string' && typeof value === 'string') {
        if (pattern && !new RegExp(pattern).test(value)) {
          return `${field.label} format is invalid`;
        }
      }
      if (custom) {
        const customError = custom(value);
        if (customError) return customError;
      }
    }
    return null;
  };
  const validateConfig = (): ValidationError[] => {
    const errors: ValidationError[] = [];
    plugin.manifest.configSchema?.forEach(field => {
      const value = config[field.key];
      const error = validateField(field, value);
      if (error) {
        errors.push({ field: field.key, message: error });
      }
    });
    return errors;
  };
  const handleFieldChange = (fieldKey: string, value: any) => {
    setConfig(prev => ({ ...prev, [fieldKey]: value }));
    // Clear validation error for this field
    setValidationErrors(prev => prev.filter(error => error.field !== fieldKey));
  };
  const handleSave = async () => {
    const errors = validateConfig();
    if (errors.length > 0) {
      setValidationErrors(errors);
      return;
    }
    setSaving(true);
    try {
      await onSave(config);
      setValidationErrors([]);
    } catch (error) {
    } finally {
      setSaving(false);
    }
  };
  const handleReset = async () => {
    setConfig(originalConfig);
    setValidationErrors([]);
    await onReset();
  };
  const handleExport = () => {
    onExport?.(config);
  };
  const handleImport = (importedConfig: PluginConfig) => {
    setConfig(importedConfig);
    onImport?.(importedConfig);
  };
  const togglePasswordVisibility = (fieldKey: string) => {
    setShowPasswords(prev => ({ ...prev, [fieldKey]: !prev[fieldKey] }));
  };
  const toggleSection = (sectionId: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev);
      if (newSet.has(sectionId)) {
        newSet.delete(sectionId);
      } else {
        newSet.add(sectionId);
      }
      return newSet;
    });
  };
  const renderField = (field: PluginConfigField) => {
    const value = config[field.key] ?? field.default ?? '';
    const error = validationErrors.find(e => e.field === field.key);
    const isPassword = field.type === 'password';
    const showPassword = showPasswords[field.key];
    const fieldId = `field-${field.key}`;
    return (
    <ErrorBoundary fallback={<div>Something went wrong in PluginConfigurationManager</div>}>
      <div key={field.key} className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor={fieldId} className="flex items-center gap-2">
            {field.label}
            {field.required && <span className="text-destructive">*</span>}
            {field.description && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger>
                    <Info className="w-3 h-3 text-muted-foreground sm:w-auto md:w-full" />
                  </TooltipTrigger>
                  <TooltipContent>
                    <p className="max-w-xs">{field.description}</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )}
          </Label>
          {isPassword && (
            <button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() = aria-label="Button"> togglePasswordVisibility(field.key)}
            >
              {showPassword ? <EyeOff className="w-3 h-3 sm:w-auto md:w-full" /> : <Eye className="w-3 h-3 sm:w-auto md:w-full" />}
            </Button>
          )}
        </div>
        {field.type === 'string' && (
          <input
            id={fieldId}
            type={isPassword && !showPassword ? 'password' : 'text'}
            value={value}
            onChange={(e) = aria-label="Input"> handleFieldChange(field.key, e.target.value)}
            placeholder={field.default?.toString()}
            disabled={readOnly}
            className={error ? 'border-destructive' : ''}
          />
        )}
        {field.type === 'number' && (
          <input
            id={fieldId}
            type="number"
            value={value}
            onChange={(e) = aria-label="Input"> handleFieldChange(field.key, Number(e.target.value))}
            min={field.validation?.min}
            max={field.validation?.max}
            disabled={readOnly}
            className={error ? 'border-destructive' : ''}
          />
        )}
        {field.type === 'boolean' && (
          <div className="flex items-center space-x-2">
            <Switch
              id={fieldId}
              checked={Boolean(value)}
              onCheckedChange={(checked) => handleFieldChange(field.key, checked)}
              disabled={readOnly}
            />
            <Label htmlFor={fieldId} className="text-sm text-muted-foreground md:text-base lg:text-lg">
              {value ? 'Enabled' : 'Disabled'}
            </Label>
          </div>
        )}
        {field.type === 'select' && field.options && (
          <select
            value={value?.toString() || ''}
            onValueChange={(newValue) = aria-label="Select option"> handleFieldChange(field.key, newValue)}
            disabled={readOnly}
          >
            <selectTrigger className={error ? 'border-destructive' : ''} aria-label="Select option">
              <selectValue placeholder="Select an option" />
            </SelectTrigger>
            <selectContent aria-label="Select option">
              {field.options.map((option) => (
                <selectItem key={option.value} value={option.value.toString()} aria-label="Select option">
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
        {field.type === 'multiselect' && field.options && (
          <div className="space-y-2">
            {field.options.map((option) => (
              <div key={option.value} className="flex items-center space-x-2">
                <Checkbox
                  id={`${fieldId}-${option.value}`}
                  checked={Array.isArray(value) && value.includes(option.value)}
                  onCheckedChange={(checked) => {
                    const currentValues = Array.isArray(value) ? value : [];
                    if (checked) {
                      handleFieldChange(field.key, [...currentValues, option.value]);
                    } else {
                      handleFieldChange(field.key, currentValues.filter(v => v !== option.value));
                    }
                  }}
                  disabled={readOnly}
                />
                <Label htmlFor={`${fieldId}-${option.value}`} className="text-sm md:text-base lg:text-lg">
                  {option.label}
                </Label>
              </div>
            ))}
          </div>
        )}
        {field.type === 'json' && (
          <textarea
            id={fieldId}
            value={typeof value === 'string' ? value : JSON.stringify(value, null, 2)}
            onChange={(e) = aria-label="Textarea"> {
              try {
                const parsed = JSON.parse(e.target.value);
                handleFieldChange(field.key, parsed);
              } catch {
                handleFieldChange(field.key, e.target.value);
              }
            }}
            rows={6}
            placeholder="Enter JSON configuration"
            disabled={readOnly}
            className={`font-mono text-sm ${error ? 'border-destructive' : ''}`}
          />
        )}
        {error && (
          <Alert variant="destructive" className="py-2">
            <AlertTriangle className="w-4 h-4 sm:w-auto md:w-full" />
            <AlertDescription className="text-sm md:text-base lg:text-lg">{error.message}</AlertDescription>
          </Alert>
        )}
      </div>
    );
  };
  const hasChanges = JSON.stringify(config) !== JSON.stringify(originalConfig);
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Plugin Configuration</h2>
          <p className="text-muted-foreground">
            Configure settings for {plugin.name}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground sm:w-auto md:w-full" />
            <input
              placeholder="Search settings..."
              value={searchQuery}
              onChange={(e) = aria-label="Input"> setSearchQuery(e.target.value)}
              className="pl-10 w-64 sm:w-auto md:w-full"
            />
          </div>
          <button
            variant="outline"
            size="sm"
            onClick={() = aria-label="Button"> setShowAdvanced(!showAdvanced)}
          >
            <Settings className="w-4 h-4 mr-2 sm:w-auto md:w-full" />
            {showAdvanced ? 'Simple' : 'Advanced'}
          </Button>
          {onExport && (
            <button variant="outline" size="sm" onClick={handleExport} aria-label="Button">
              <Download className="w-4 h-4 mr-2 sm:w-auto md:w-full" />
              Export
            </Button>
          )}
        </div>
      </div>
      {/* Configuration Status */}
      {hasChanges && (
        <Alert>
          <Info className="w-4 h-4 sm:w-auto md:w-full" />
          <AlertDescription>
            You have unsaved changes. Don't forget to save your configuration.
          </AlertDescription>
        </Alert>
      )}
      {/* Validation Errors Summary */}
      {validationErrors.length > 0 && (
        <Alert variant="destructive">
          <AlertTriangle className="w-4 h-4 sm:w-auto md:w-full" />
          <AlertDescription>
            Please fix {validationErrors.length} configuration error{validationErrors.length !== 1 ? 's' : ''} before saving.
          </AlertDescription>
        </Alert>
      )}
      <Tabs defaultValue="configuration" className="space-y-4">
        <TabsList>
          <TabsTrigger value="configuration">Configuration</TabsTrigger>
          <TabsTrigger value="security">Security</TabsTrigger>
          <TabsTrigger value="advanced">Advanced</TabsTrigger>
        </TabsList>
        <TabsContent value="configuration" className="space-y-4">
          {filteredSections.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Settings className="w-12 h-12 mx-auto mb-4 opacity-50 sm:w-auto md:w-full" />
                <h3 className="text-lg font-medium mb-2">No Configuration Available</h3>
                <p className="text-muted-foreground">
                  This plugin doesn't have any configurable settings.
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {filteredSections.map((section) => (
                <Card key={section.id}>
                  <Collapsible
                    open={expandedSections.has(section.id)}
                    onOpenChange={() => toggleSection(section.id)}
                  >
                    <CollapsibleTrigger asChild>
                      <CardHeader className="cursor-pointer hover:bg-muted/50">
                        <div className="flex items-center justify-between">
                          <div>
                            <CardTitle className="text-lg">{section.name}</CardTitle>
                            <CardDescription>{section.description}</CardDescription>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge variant="outline">
                              {section.fields.length} setting{section.fields.length !== 1 ? 's' : ''}
                            </Badge>
                            {expandedSections.has(section.id) ? (
                              <Minus className="w-4 h-4 sm:w-auto md:w-full" />
                            ) : (
                              <Plus className="w-4 h-4 sm:w-auto md:w-full" />
                            )}
                          </div>
                        </div>
                      </CardHeader>
                    </CollapsibleTrigger>
                    <CollapsibleContent>
                      <CardContent className="space-y-6">
                        {section.fields.map(renderField)}
                      </CardContent>
                    </CollapsibleContent>
                  </Collapsible>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
        <TabsContent value="security" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5 sm:w-auto md:w-full" />
                Security Settings
              </CardTitle>
              <CardDescription>
                Manage security policies and permissions for this plugin
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h4 className="font-medium">Security Policy</h4>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Network className="w-4 h-4 sm:w-auto md:w-full" />
                        <span className="text-sm md:text-base lg:text-lg">Network Access</span>
                      </div>
                      <Badge variant={plugin.manifest.securityPolicy.allowNetworkAccess ? 'default' : 'secondary'}>
                        {plugin.manifest.securityPolicy.allowNetworkAccess ? 'Allowed' : 'Blocked'}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <HardDrive className="w-4 h-4 sm:w-auto md:w-full" />
                        <span className="text-sm md:text-base lg:text-lg">File System Access</span>
                      </div>
                      <Badge variant={plugin.manifest.securityPolicy.allowFileSystemAccess ? 'default' : 'secondary'}>
                        {plugin.manifest.securityPolicy.allowFileSystemAccess ? 'Allowed' : 'Blocked'}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Cpu className="w-4 h-4 sm:w-auto md:w-full" />
                        <span className="text-sm md:text-base lg:text-lg">System Calls</span>
                      </div>
                      <Badge variant={plugin.manifest.securityPolicy.allowSystemCalls ? 'default' : 'secondary'}>
                        {plugin.manifest.securityPolicy.allowSystemCalls ? 'Allowed' : 'Blocked'}
                      </Badge>
                    </div>
                  </div>
                </div>
                <div className="space-y-4">
                  <h4 className="font-medium">Sandboxing</h4>
                  <div className="flex items-center justify-between">
                    <span className="text-sm md:text-base lg:text-lg">Sandboxed Execution</span>
                    <Badge variant={plugin.manifest.sandboxed ? 'default' : 'destructive'}>
                      {plugin.manifest.sandboxed ? 'Enabled' : 'Disabled'}
                    </Badge>
                  </div>
                  {plugin.manifest.securityPolicy.trustedDomains && (
                    <div className="space-y-2">
                      <h5 className="text-sm font-medium md:text-base lg:text-lg">Trusted Domains</h5>
                      <div className="space-y-1">
                        {plugin.manifest.securityPolicy.trustedDomains.map((domain, index) => (
                          <div key={index} className="flex items-center gap-2 text-sm md:text-base lg:text-lg">
                            <Globe className="w-3 h-3 sm:w-auto md:w-full" />
                            <span className="font-mono">{domain}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
              <Separator />
              <div className="space-y-4">
                <h4 className="font-medium">Permissions</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {plugin.permissions.map((permission) => (
                    <div key={permission.id} className="p-3 border rounded-lg sm:p-4 md:p-6">
                      <div className="flex items-center justify-between mb-2">
                        <h5 className="font-medium text-sm md:text-base lg:text-lg">{permission.name}</h5>
                        <Badge 
                          variant={
                            permission.level === 'admin' ? 'destructive' :
                            permission.level === 'write' ? 'default' : 'secondary'
                          }
                          className="text-xs sm:text-sm md:text-base"
                        >
                          {permission.level}
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground sm:text-sm md:text-base">{permission.description}</p>
                      <div className="flex items-center gap-2 mt-2">
                        <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                          {permission.category}
                        </Badge>
                        {permission.required && (
                          <Badge variant="outline" className="text-xs sm:text-sm md:text-base">Required</Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="advanced" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Advanced Configuration</CardTitle>
              <CardDescription>
                Advanced settings and debugging options
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h4 className="font-medium">Plugin Information</h4>
                  <div className="space-y-2 text-sm md:text-base lg:text-lg">
                    <div className="flex justify-between">
                      <span>Plugin ID:</span>
                      <span className="font-mono">{plugin.id}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Version:</span>
                      <span>{plugin.version}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>API Version:</span>
                      <span>{plugin.manifest.apiVersion}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Installed:</span>
                      <span>{plugin.installedAt.toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>
                <div className="space-y-4">
                  <h4 className="font-medium">Runtime Information</h4>
                  <div className="space-y-2 text-sm md:text-base lg:text-lg">
                    <div className="flex justify-between">
                      <span>Auto Start:</span>
                      <Badge variant={plugin.autoStart ? 'default' : 'secondary'}>
                        {plugin.autoStart ? 'Yes' : 'No'}
                      </Badge>
                    </div>
                    <div className="flex justify-between">
                      <span>Restart Count:</span>
                      <span>{plugin.restartCount}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Status:</span>
                      <Badge variant={plugin.status === 'active' ? 'default' : 'secondary'}>
                        {plugin.status}
                      </Badge>
                    </div>
                  </div>
                </div>
              </div>
              <Separator />
              <div className="space-y-4">
                <h4 className="font-medium">Configuration Management</h4>
                <div className="flex gap-2">
                  <button variant="outline" size="sm" onClick={handleExport} aria-label="Button">
                    <Download className="w-4 h-4 mr-2 sm:w-auto md:w-full" />
                    Export Config
                  </Button>
                  <button variant="outline" size="sm" aria-label="Button">
                    <Upload className="w-4 h-4 mr-2 sm:w-auto md:w-full" />
                    Import Config
                  </Button>
                  <button variant="outline" size="sm" aria-label="Button">
                    <Copy className="w-4 h-4 mr-2 sm:w-auto md:w-full" />
                    Copy as JSON
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
      {/* Action Buttons */}
      {!readOnly && (
        <div className="flex items-center justify-between pt-6 border-t">
          <div className="flex items-center gap-2">
            <button variant="outline" onClick={handleReset} disabled={!hasChanges} aria-label="Button">
              <RotateCcw className="w-4 h-4 mr-2 sm:w-auto md:w-full" />
              Reset
            </Button>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleSave}
              disabled={!hasChanges || saving || validationErrors.length  aria-label="Button"> 0}
            >
              {saving ? (
                <RefreshCw className="w-4 h-4 mr-2 animate-spin sm:w-auto md:w-full" />
              ) : (
                <Save className="w-4 h-4 mr-2 sm:w-auto md:w-full" />
              )}
              {saving ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        </div>
      )}
    </div>
    </ErrorBoundary>
  );
};
