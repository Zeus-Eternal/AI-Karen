/**
 * Dynamic Plugin Configuration Form Component
 * 
 * Generates dynamic configuration forms based on plugin manifests with validation.
 * Based on requirements: 5.3, 5.5, 9.1, 9.2
 */

"use client";

import React, { useState, useEffect } from 'react';
import { 
  Settings, 
  Save, 
  RotateCcw, 
  Eye, 
  EyeOff, 
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
  Code,
  Type,
  Hash,
  ToggleLeft,
  List,
  CheckSquare,
  FileJson,
  Lock,
} from 'lucide-react';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Checkbox } from '@/components/ui/checkbox';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Progress } from '@/components/ui/progress';
import { 
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';

import { PluginInfo, PluginConfig, PluginConfigField } from '@/types/plugins';

interface ValidationError {
  field: string;
  message: string;
  severity: 'error' | 'warning' | 'info';
}

interface FieldGroup {
  id: string;
  name: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  fields: PluginConfigField[];
  collapsed?: boolean;
  required?: boolean;
}

interface DynamicPluginConfigFormProps {
  plugin: PluginInfo;
  initialConfig?: PluginConfig;
  onSave: (config: PluginConfig) => Promise<void>;
  onValidate?: (config: PluginConfig) => ValidationError[];
  onPreview?: (config: PluginConfig) => void;
  readOnly?: boolean;
  showAdvanced?: boolean;
}

export const DynamicPluginConfigForm: React.FC<DynamicPluginConfigFormProps> = ({
  plugin,
  initialConfig = {},
  onSave,
  onValidate,
  onPreview,
  readOnly = false,
  showAdvanced = false,
}) => {
  const [config, setConfig] = useState<PluginConfig>(initialConfig);
  const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);
  const [saving, setSaving] = useState(false);
  const [showPasswords, setShowPasswords] = useState<Record<string, boolean>>({});
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set(['general']));
  const [searchQuery, setSearchQuery] = useState('');
  const [isDirty, setIsDirty] = useState(false);

  // Group configuration fields by category or prefix
  const fieldGroups: FieldGroup[] = React.useMemo(() => {
    if (!plugin.manifest.configSchema) return [];
    
    const groupMap = new Map<string, PluginConfigField[]>();
    
    plugin.manifest.configSchema.forEach(field => {
      let groupId = 'general';
      let groupName = 'General Settings';
      let groupIcon = Settings;
      
      // Determine group based on field key prefix or type
      if (field.key.startsWith('auth') || field.key.includes('token') || field.key.includes('key')) {
        groupId = 'authentication';
        groupName = 'Authentication';
        groupIcon = Key;
      } else if (field.key.startsWith('db') || field.key.includes('database')) {
        groupId = 'database';
        groupName = 'Database';
        groupIcon = Database;
      } else if (field.key.startsWith('network') || field.key.includes('url') || field.key.includes('endpoint')) {
        groupId = 'network';
        groupName = 'Network & API';
        groupIcon = Network;
      } else if (field.key.startsWith('ui') || field.key.includes('theme') || field.key.includes('display')) {
        groupId = 'interface';
        groupName = 'User Interface';
        groupIcon = Eye;
      } else if (field.key.startsWith('perf') || field.key.includes('cache') || field.key.includes('timeout')) {
        groupId = 'performance';
        groupName = 'Performance';
        groupIcon = Zap;
      } else if (field.key.startsWith('security') || field.key.includes('encrypt') || field.key.includes('secure')) {
        groupId = 'security';
        groupName = 'Security';
        groupIcon = Lock;
      }
      
      if (!groupMap.has(groupId)) {
        groupMap.set(groupId, []);
      }
      groupMap.get(groupId)!.push(field);
    });
    
    return Array.from(groupMap.entries()).map(([id, fields]) => {
      const icons = {
        general: Settings,
        authentication: Key,
        database: Database,
        network: Network,
        interface: Eye,
        performance: Zap,
        security: Lock,
      };
      
      const names = {
        general: 'General Settings',
        authentication: 'Authentication',
        database: 'Database',
        network: 'Network & API',
        interface: 'User Interface',
        performance: 'Performance',
        security: 'Security',
      };
      
      return {
        id,
        name: names[id as keyof typeof names] || id.charAt(0).toUpperCase() + id.slice(1),
        description: `Configure ${names[id as keyof typeof names]?.toLowerCase() || id} settings`,
        icon: icons[id as keyof typeof icons] || Settings,
        fields,
        required: fields.some(f => f.required),
      };
    });
  }, [plugin.manifest.configSchema]);

  // Filter fields based on search query
  const filteredGroups = React.useMemo(() => {
    if (!searchQuery) return fieldGroups;
    
    return fieldGroups.map(group => ({
      ...group,
      fields: group.fields.filter(field =>
        field.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
        field.key.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (field.description && field.description.toLowerCase().includes(searchQuery.toLowerCase()))
      ),
    })).filter(group => group.fields.length > 0);
  }, [fieldGroups, searchQuery]);

  // Validate a single field
  const validateField = (field: PluginConfigField, value: any): ValidationError | null => {
    if (field.required && (value === undefined || value === null || value === '')) {
      return {
        field: field.key,
        message: `${field.label} is required`,
        severity: 'error',
      };
    }
    
    if (field.validation) {
      const { min, max, pattern, custom } = field.validation;
      
      if (field.type === 'number' && typeof value === 'number') {
        if (min !== undefined && value < min) {
          return {
            field: field.key,
            message: `${field.label} must be at least ${min}`,
            severity: 'error',
          };
        }
        if (max !== undefined && value > max) {
          return {
            field: field.key,
            message: `${field.label} must be at most ${max}`,
            severity: 'error',
          };
        }
      }
      
      if (field.type === 'string' && typeof value === 'string') {
        if (pattern && !new RegExp(pattern).test(value)) {
          return {
            field: field.key,
            message: `${field.label} format is invalid`,
            severity: 'error',
          };
        }
      }
      
      if (custom) {
        const customError = custom(value);
        if (customError) {
          return {
            field: field.key,
            message: customError,
            severity: 'error',
          };
        }
      }
    }
    
    return null;
  };

  // Validate entire configuration
  const validateConfig = (): ValidationError[] => {
    const errors: ValidationError[] = [];
    
    plugin.manifest.configSchema?.forEach(field => {
      const value = config[field.key];
      const error = validateField(field, value);
      if (error) {
        errors.push(error);
      }
    });
    
    // Add custom validation if provided
    if (onValidate) {
      errors.push(...onValidate(config));
    }
    
    return errors;
  };

  // Handle field value changes
  const handleFieldChange = (fieldKey: string, value: any) => {
    setConfig(prev => ({ ...prev, [fieldKey]: value }));
    setIsDirty(true);
    
    // Clear validation error for this field
    setValidationErrors(prev => prev.filter(error => error.field !== fieldKey));
  };

  // Handle form submission
  const handleSave = async () => {
    const errors = validateConfig();
    if (errors.filter(e => e.severity === 'error').length > 0) {
      setValidationErrors(errors);
      return;
    }
    
    setSaving(true);
    try {
      await onSave(config);
      setValidationErrors([]);
      setIsDirty(false);
    } catch (error) {
      console.error('Failed to save configuration:', error);
      setValidationErrors([{
        field: '_global',
        message: 'Failed to save configuration. Please try again.',
        severity: 'error',
      }]);
    } finally {
      setSaving(false);
    }
  };

  // Handle form reset
  const handleReset = () => {
    setConfig(initialConfig);
    setValidationErrors([]);
    setIsDirty(false);
  };

  // Handle preview
  const handlePreview = () => {
    onPreview?.(config);
  };

  // Toggle password visibility
  const togglePasswordVisibility = (fieldKey: string) => {
    setShowPasswords(prev => ({ ...prev, [fieldKey]: !prev[fieldKey] }));
  };

  // Toggle group expansion
  const toggleGroup = (groupId: string) => {
    setExpandedGroups(prev => {
      const newSet = new Set(prev);
      if (newSet.has(groupId)) {
        newSet.delete(groupId);
      } else {
        newSet.add(groupId);
      }
      return newSet;
    });
  };

  // Get field icon based on type
  const getFieldIcon = (field: PluginConfigField) => {
    const icons = {
      string: Type,
      number: Hash,
      boolean: ToggleLeft,
      select: List,
      multiselect: CheckSquare,
      json: FileJson,
      password: Lock,
    };
    return icons[field.type] || Type;
  };

  // Render individual field
  const renderField = (field: PluginConfigField) => {
    const value = config[field.key] ?? field.default ?? '';
    const error = validationErrors.find(e => e.field === field.key);
    const isPassword = field.type === 'password';
    const showPassword = showPasswords[field.key];
    const FieldIcon = getFieldIcon(field);

    const fieldId = `field-${field.key}`;

    return (
      <div key={field.key} className="space-y-3">
        <div className="flex items-center justify-between">
          <Label htmlFor={fieldId} className="flex items-center gap-2 text-sm font-medium">
            <FieldIcon className="w-4 h-4 text-muted-foreground" />
            {field.label}
            {field.required && <span className="text-destructive">*</span>}
            {field.description && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger>
                    <Info className="w-3 h-3 text-muted-foreground" />
                  </TooltipTrigger>
                  <TooltipContent side="top" className="max-w-xs">
                    <p>{field.description}</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )}
          </Label>
          
          {isPassword && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => togglePasswordVisibility(field.key)}
            >
              {showPassword ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
            </Button>
          )}
        </div>

        {field.type === 'string' && (
          <Input
            id={fieldId}
            type={isPassword && !showPassword ? 'password' : 'text'}
            value={value}
            onChange={(e) => handleFieldChange(field.key, e.target.value)}
            placeholder={field.default?.toString()}
            disabled={readOnly}
            className={error ? 'border-destructive' : ''}
          />
        )}

        {field.type === 'number' && (
          <Input
            id={fieldId}
            type="number"
            value={value}
            onChange={(e) => handleFieldChange(field.key, Number(e.target.value))}
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
            <Label htmlFor={fieldId} className="text-sm text-muted-foreground">
              {value ? 'Enabled' : 'Disabled'}
            </Label>
          </div>
        )}

        {field.type === 'select' && field.options && (
          <Select
            value={value?.toString() || ''}
            onValueChange={(newValue) => handleFieldChange(field.key, newValue)}
            disabled={readOnly}
          >
            <SelectTrigger className={error ? 'border-destructive' : ''}>
              <SelectValue placeholder="Select an option" />
            </SelectTrigger>
            <SelectContent>
              {field.options.map((option) => (
                <SelectItem key={option.value} value={option.value.toString()}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}

        {field.type === 'multiselect' && field.options && (
          <div className="space-y-2 max-h-32 overflow-y-auto">
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
                <Label htmlFor={`${fieldId}-${option.value}`} className="text-sm">
                  {option.label}
                </Label>
              </div>
            ))}
          </div>
        )}

        {field.type === 'json' && (
          <div className="space-y-2">
            <Textarea
              id={fieldId}
              value={typeof value === 'string' ? value : JSON.stringify(value, null, 2)}
              onChange={(e) => {
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
            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => {
                  try {
                    const formatted = JSON.stringify(JSON.parse(value), null, 2);
                    handleFieldChange(field.key, formatted);
                  } catch (e) {
                    // Invalid JSON, ignore
                  }
                }}
                disabled={readOnly}
              >
                <Code className="w-3 h-3 mr-1" />
                Format
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => {
                  navigator.clipboard.writeText(typeof value === 'string' ? value : JSON.stringify(value, null, 2));
                }}
              >
                <Copy className="w-3 h-3 mr-1" />
                Copy
              </Button>
            </div>
          </div>
        )}

        {error && (
          <Alert variant={error.severity === 'error' ? 'destructive' : 'default'} className="py-2">
            <AlertTriangle className="w-4 h-4" />
            <AlertDescription className="text-sm">{error.message}</AlertDescription>
          </Alert>
        )}

        {field.default !== undefined && !value && (
          <div className="text-xs text-muted-foreground">
            Default: {typeof field.default === 'object' ? JSON.stringify(field.default) : field.default.toString()}
          </div>
        )}
      </div>
    );
  };

  // Render field group
  const renderGroup = (group: FieldGroup) => {
    const isExpanded = expandedGroups.has(group.id);
    const GroupIcon = group.icon;
    const groupErrors = validationErrors.filter(e => 
      group.fields.some(f => f.key === e.field)
    );

    return (
      <Card key={group.id}>
        <Collapsible open={isExpanded} onOpenChange={() => toggleGroup(group.id)}>
          <CollapsibleTrigger asChild>
            <CardHeader className="cursor-pointer hover:bg-muted/50 transition-colors">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <GroupIcon className="w-5 h-5 text-muted-foreground" />
                  <div>
                    <CardTitle className="text-lg flex items-center gap-2">
                      {group.name}
                      {group.required && (
                        <Badge variant="outline" className="text-xs">Required</Badge>
                      )}
                    </CardTitle>
                    <CardDescription>{group.description}</CardDescription>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {groupErrors.length > 0 && (
                    <Badge variant="destructive" className="text-xs">
                      {groupErrors.length} error{groupErrors.length !== 1 ? 's' : ''}
                    </Badge>
                  )}
                  <Badge variant="outline" className="text-xs">
                    {group.fields.length} field{group.fields.length !== 1 ? 's' : ''}
                  </Badge>
                  {isExpanded ? (
                    <Minus className="w-4 h-4" />
                  ) : (
                    <Plus className="w-4 h-4" />
                  )}
                </div>
              </div>
            </CardHeader>
          </CollapsibleTrigger>
          
          <CollapsibleContent>
            <CardContent className="space-y-6">
              {group.fields.map(renderField)}
            </CardContent>
          </CollapsibleContent>
        </Collapsible>
      </Card>
    );
  };

  const errorCount = validationErrors.filter(e => e.severity === 'error').length;
  const warningCount = validationErrors.filter(e => e.severity === 'warning').length;

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
          {searchQuery && (
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search settings..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 w-64"
              />
            </div>
          )}
          
          {onPreview && (
            <Button variant="outline" size="sm" onClick={handlePreview}>
              <Eye className="w-4 h-4 mr-2" />
              Preview
            </Button>
          )}
        </div>
      </div>

      {/* Status Alerts */}
      {isDirty && (
        <Alert>
          <Info className="w-4 h-4" />
          <AlertDescription>
            You have unsaved changes. Don't forget to save your configuration.
          </AlertDescription>
        </Alert>
      )}

      {errorCount > 0 && (
        <Alert variant="destructive">
          <AlertTriangle className="w-4 h-4" />
          <AlertDescription>
            Please fix {errorCount} error{errorCount !== 1 ? 's' : ''} before saving.
          </AlertDescription>
        </Alert>
      )}

      {warningCount > 0 && (
        <Alert>
          <AlertTriangle className="w-4 h-4" />
          <AlertDescription>
            {warningCount} warning{warningCount !== 1 ? 's' : ''} found in your configuration.
          </AlertDescription>
        </Alert>
      )}

      {/* Configuration Form */}
      {filteredGroups.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Settings className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <h3 className="text-lg font-medium mb-2">
              {searchQuery ? 'No matching settings' : 'No Configuration Available'}
            </h3>
            <p className="text-muted-foreground">
              {searchQuery 
                ? 'Try adjusting your search query'
                : 'This plugin doesn\'t have any configurable settings.'
              }
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredGroups.map(renderGroup)}
        </div>
      )}

      {/* Action Buttons */}
      {!readOnly && filteredGroups.length > 0 && (
        <div className="flex items-center justify-between pt-6 border-t">
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={handleReset} disabled={!isDirty}>
              <RotateCcw className="w-4 h-4 mr-2" />
              Reset
            </Button>
          </div>
          
          <div className="flex items-center gap-2">
            <Button
              onClick={handleSave}
              disabled={!isDirty || saving || errorCount > 0}
            >
              {saving ? (
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Save className="w-4 h-4 mr-2" />
              )}
              {saving ? 'Saving...' : 'Save Configuration'}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};