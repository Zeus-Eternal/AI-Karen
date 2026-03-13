"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Agent, AgentConfiguration, AgentConfigurationValues } from '../types';
import { cn } from '@/lib/utils';

interface AgentConfigurationProps {
  agent: Agent;
  values: AgentConfigurationValues;
  onChange: (configId: string, value: any) => void;
  onReset?: () => void;
  onSave?: (values: AgentConfigurationValues) => void;
  className?: string;
}

function AgentConfigurationComponent({
  agent,
  values,
  onChange,
  onReset,
  onSave,
  className,
}: AgentConfigurationProps) {
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isValid, setIsValid] = useState(true);

  // Group configurations by category
  const groupedConfigs = agent.configuration.reduce((groups, config) => {
    const category = config.category || 'General';
    if (!groups[category]) {
      groups[category] = [];
    }
    groups[category].push(config);
    return groups;
  }, {} as Record<string, AgentConfiguration[]>);

  // Sort configurations within each category by order
  Object.keys(groupedConfigs || {}).forEach(category => {
    if (groupedConfigs && groupedConfigs[category]) {
      groupedConfigs[category].sort((a, b) => a.order - b.order);
    }
  });

  useEffect(() => {
    // Validate all configurations
    const newErrors: Record<string, string> = {};
    let valid = true;

    agent.configuration.forEach(config => {
      const value = values[config.id] ?? config.defaultValue;

      // Check required fields
      if (config.required && (value === undefined || value === null || value === '')) {
        newErrors[config.id] = `${config.label} is required`;
        valid = false;
      }

      // Type-specific validation
      if (value !== undefined && value !== null && value !== '') {
        if (config.type === 'number') {
          const numValue = Number(value);
          if (isNaN(numValue)) {
            newErrors[config.id] = `${config.label} must be a number`;
            valid = false;
          } else if (config.validation) {
            if (config.validation.min !== undefined && numValue < config.validation.min) {
              newErrors[config.id] = `${config.label} must be at least ${config.validation.min}`;
              valid = false;
            }
            if (config.validation.max !== undefined && numValue > config.validation.max) {
              newErrors[config.id] = `${config.label} must be at most ${config.validation.max}`;
              valid = false;
            }
          }
        } else if (config.type === 'string' && config.validation?.pattern) {
          const regex = new RegExp(config.validation.pattern);
          if (!regex.test(value)) {
            newErrors[config.id] = `${config.label} format is invalid`;
            valid = false;
          }
        }
      }
    });

    setErrors(newErrors);
    setIsValid(valid);
  }, [values, agent.configuration]);

  const handleReset = () => {
    const defaultValues: AgentConfigurationValues = {};
    agent.configuration.forEach(config => {
      defaultValues[config.id] = config.defaultValue;
    });
    
    // Clear errors
    setErrors({});
    
    // Call parent reset handler
    onReset?.();
  };

  const handleSave = () => {
    if (isValid) {
      onSave?.(values);
    }
  };

  const renderConfigField = (config: AgentConfiguration) => {
    const value = values[config.id] ?? config.defaultValue;
    const error = errors[config.id];

    const renderField = () => {
      switch (config.type) {
        case 'string':
          return (
            <input
              type="text"
              value={value || ''}
              onChange={(e) => onChange(config.id, e.target.value)}
              placeholder={config.defaultValue || ''}
              className={cn(
                "w-full p-2 border rounded-md",
                error && "border-red-500 focus:ring-red-500"
              )}
              required={config.required}
            />
          );

        case 'number':
          return (
            <input
              type="number"
              value={value || ''}
              onChange={(e) => onChange(config.id, e.target.value)}
              placeholder={config.defaultValue?.toString() || ''}
              className={cn(
                "w-full p-2 border rounded-md",
                error && "border-red-500 focus:ring-red-500"
              )}
              min={config.validation?.min}
              max={config.validation?.max}
              step="any"
              required={config.required}
            />
          );

        case 'boolean':
          return (
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id={config.id}
                checked={value ?? false}
                onChange={(e) => onChange(config.id, e.target.checked)}
                className="rounded"
              />
              <label htmlFor={config.id} className="text-sm">
                {config.label}
              </label>
            </div>
          );

        case 'select':
          return (
            <select
              value={value || ''}
              onChange={(e) => onChange(config.id, e.target.value)}
              className={cn(
                "w-full p-2 border rounded-md",
                error && "border-red-500 focus:ring-red-500"
              )}
              required={config.required}
            >
              <option value="">Select...</option>
              {config.options?.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          );

        case 'textarea':
          return (
            <textarea
              value={value || ''}
              onChange={(e) => onChange(config.id, e.target.value)}
              placeholder={config.defaultValue || ''}
              className={cn(
                "w-full p-2 border rounded-md min-h-[100px]",
                error && "border-red-500 focus:ring-red-500"
              )}
              required={config.required}
              rows={4}
            />
          );

        case 'file':
          return (
            <input
              type="file"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) {
                  onChange(config.id, file);
                }
              }}
              className={cn(
                "w-full p-2 border rounded-md",
                error && "border-red-500 focus:ring-red-500"
              )}
              required={config.required}
            />
          );

        default:
          return (
            <input
              type="text"
              value={value || ''}
              onChange={(e) => onChange(config.id, e.target.value)}
              className={cn(
                "w-full p-2 border rounded-md",
                error && "border-red-500 focus:ring-red-500"
              )}
            />
          );
      }
    };

    return (
      <div key={config.id} className="space-y-2">
        <div>
          <label className="block text-sm font-medium">
            {config.label}
            {config.required && <span className="text-red-500">*</span>}
          </label>
          {config.description && (
            <p className="text-xs text-muted-foreground mt-1">
              {config.description}
            </p>
          )}
        </div>
        
        <div>
          {renderField()}
          {error && (
            <p className="text-xs text-red-500 mt-1">{error}</p>
          )}
        </div>
      </div>
    );
  };

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-xl">Configure {agent.name}</CardTitle>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleReset}>
              Reset to Defaults
            </Button>
            <Button 
              size="sm" 
              onClick={handleSave}
              disabled={!isValid}
            >
              Save Configuration
            </Button>
          </div>
        </div>
        <p className="text-sm text-muted-foreground">
          Customize the agent settings to match your specific requirements.
        </p>
      </CardHeader>
      
      <CardContent className="p-6">
        {agent.configuration.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <p>This agent has no configurable settings.</p>
          </div>
        ) : (
          <div className="space-y-8">
            {Object.entries(groupedConfigs || {}).map(([category, configs]) => (
              <div key={category} className="space-y-4">
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-semibold">{category}</h3>
                  <Badge variant="outline" className="text-xs">
                    {configs.length} setting{configs.length !== 1 ? 's' : ''}
                  </Badge>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {configs.map(renderConfigField)}
                </div>
              </div>
            ))}
          </div>
        )}
        
        {/* Configuration Summary */}
        {agent.configuration.length > 0 && (
          <div className="mt-8 p-4 bg-muted/30 rounded-lg">
            <h3 className="text-sm font-medium mb-2">Configuration Summary</h3>
            <div className="text-sm text-muted-foreground space-y-1">
              <p>Total settings: {agent.configuration.length}</p>
              <p>Required settings: {agent.configuration.filter(c => c.required).length}</p>
              <p>Configured settings: {Object.keys(values).length}</p>
              <p className={cn("font-medium", isValid ? "text-green-600" : "text-red-600")}>
                Status: {isValid ? "Valid" : "Invalid"}
              </p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export { AgentConfigurationComponent as AgentConfiguration };