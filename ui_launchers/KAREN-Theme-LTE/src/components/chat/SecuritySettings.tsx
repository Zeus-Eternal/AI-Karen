"use client";

import React, { useState, useEffect } from 'react';
import { useChatAuth } from '@/contexts/ChatAuthContext';
import { useSecurity } from '@/hooks/useSecurity';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Shield, 
  ShieldCheck, 
  ShieldAlert, 
  Eye, 
  EyeOff, 
  Lock, 
  Unlock, 
  AlertTriangle, 
  CheckCircle, 
  XCircle,
  Settings,
  Key,
  FileText,
  Users,
  Activity
} from 'lucide-react';

// Types for SecuritySettings
export interface SecuritySettingsProps {
  className?: string;
  onSettingsChange?: (settings: SecuritySettingsState) => void;
}

export interface SecuritySettingsState {
  securityLevel: 'low' | 'medium' | 'high' | 'strict';
  contentFiltering: {
    enabled: boolean;
    level: 'basic' | 'moderate' | 'strict';
    customFilters: string[];
  };
  dataProtection: {
    encryption: boolean;
    anonymization: boolean;
    dataRetention: number; // days
  };
  accessControl: {
    twoFactorAuth: boolean;
    sessionTimeout: number; // minutes
    ipWhitelist: string[];
    deviceTrust: boolean;
  };
  monitoring: {
    enabled: boolean;
    alertLevel: 'low' | 'medium' | 'high' | 'critical';
    logLevel: 'basic' | 'detailed' | 'verbose';
  };
  notifications: {
    securityEvents: boolean;
    accessAttempts: boolean;
    dataBreaches: boolean;
  };
}

// Security level descriptions
const SECURITY_LEVELS = {
  low: {
    name: 'Low',
    description: 'Basic security with minimal restrictions',
    color: 'bg-green-100 text-green-800',
    icon: <Unlock className="h-4 w-4" />,
    features: [
      'Basic input validation',
      'Simple content filtering',
      'Standard rate limiting'
    ]
  },
  medium: {
    name: 'Medium',
    description: 'Balanced security with moderate restrictions',
    color: 'bg-yellow-100 text-yellow-800',
    icon: <Shield className="h-4 w-4" />,
    features: [
      'Enhanced input validation',
      'Moderate content filtering',
      'Stricter rate limiting',
      'Basic threat detection'
    ]
  },
  high: {
    name: 'High',
    description: 'Strong security with significant restrictions',
    color: 'bg-orange-100 text-orange-800',
    icon: <ShieldCheck className="h-4 w-4" />,
    features: [
      'Advanced input validation',
      'Strict content filtering',
      'Aggressive rate limiting',
      'Enhanced threat detection',
      'Real-time monitoring'
    ]
  },
  strict: {
    name: 'Strict',
    description: 'Maximum security with comprehensive restrictions',
    color: 'bg-red-100 text-red-800',
    icon: <ShieldAlert className="h-4 w-4" />,
    features: [
      'Maximum input validation',
      'Very strict content filtering',
      'Very aggressive rate limiting',
      'Comprehensive threat detection',
      'Real-time monitoring',
      'Advanced logging',
      'Automatic blocking'
    ]
  }
};

// Main SecuritySettings component
export function SecuritySettings({ className, onSettingsChange }: SecuritySettingsProps) {
  const { setSecurityLevel, checkChatPermission } = useChatAuth();
  const {
    securityLevel: currentSecurityLevel,
    logSecurityEvent,
    securityEvents
  } = useSecurity();

  const [settings, setSettings] = useState<SecuritySettingsState>({
    securityLevel: currentSecurityLevel.level,
    contentFiltering: {
      enabled: true,
      level: 'moderate',
      customFilters: []
    },
    dataProtection: {
      encryption: true,
      anonymization: false,
      dataRetention: 30
    },
    accessControl: {
      twoFactorAuth: false,
      sessionTimeout: 30,
      ipWhitelist: [],
      deviceTrust: true
    },
    monitoring: {
      enabled: true,
      alertLevel: 'medium',
      logLevel: 'detailed'
    },
    notifications: {
      securityEvents: true,
      accessAttempts: true,
      dataBreaches: true
    }
  });

  const [activeTab, setActiveTab] = useState('general');

  // Check if user can change security settings
  const canChangeSecuritySettings = checkChatPermission('chat:security:write');

  // Update security level
  const handleSecurityLevelChange = (level: 'low' | 'medium' | 'high' | 'strict') => {
    if (!canChangeSecuritySettings) {
      logSecurityEvent({
        type: 'permission_change',
        severity: 'medium',
        message: 'User attempted to change security level without permission',
        details: { attemptedLevel: level }
      });
      return;
    }

    setSettings(prev => ({ ...prev, securityLevel: level }));
    setSecurityLevel(level);
    
    if (onSettingsChange) {
      onSettingsChange({ ...settings, securityLevel: level });
    }
  };

  // Update content filtering
  const handleContentFilteringChange = (field: string, value: any) => {
    if (!canChangeSecuritySettings) return;

    const newSettings = {
      ...settings,
      contentFiltering: {
        ...settings.contentFiltering,
        [field]: value
      }
    };
    
    setSettings(newSettings);
    if (onSettingsChange) {
      onSettingsChange(newSettings);
    }
  };

  // Update data protection
  const handleDataProtectionChange = (field: string, value: any) => {
    if (!canChangeSecuritySettings) return;

    const newSettings = {
      ...settings,
      dataProtection: {
        ...settings.dataProtection,
        [field]: value
      }
    };
    
    setSettings(newSettings);
    if (onSettingsChange) {
      onSettingsChange(newSettings);
    }
  };

  // Update access control
  const handleAccessControlChange = (field: string, value: any) => {
    if (!canChangeSecuritySettings) return;

    const newSettings = {
      ...settings,
      accessControl: {
        ...settings.accessControl,
        [field]: value
      }
    };
    
    setSettings(newSettings);
    if (onSettingsChange) {
      onSettingsChange(newSettings);
    }
  };

  // Update monitoring
  const handleMonitoringChange = (field: string, value: any) => {
    if (!canChangeSecuritySettings) return;

    const newSettings = {
      ...settings,
      monitoring: {
        ...settings.monitoring,
        [field]: value
      }
    };
    
    setSettings(newSettings);
    if (onSettingsChange) {
      onSettingsChange(newSettings);
    }
  };

  // Update notifications
  const handleNotificationsChange = (field: string, value: any) => {
    if (!canChangeSecuritySettings) return;

    const newSettings = {
      ...settings,
      notifications: {
        ...settings.notifications,
        [field]: value
      }
    };
    
    setSettings(newSettings);
    if (onSettingsChange) {
      onSettingsChange(newSettings);
    }
  };

  // Test content validation
  const testContentValidation = () => {
    const testContent = "Test content for validation <script>alert('xss')</script>";
    // Basic validation check
    const hasXSS = /<script[^>]*>.*?<\/script>/gi.test(testContent);
    const result = { isValid: !hasXSS, threats: hasXSS ? ['XSS: Cross-site scripting'] : [] };
    
    logSecurityEvent({
      type: 'security_violation',
      severity: result.isValid ? 'low' : 'medium',
      message: 'Content validation test performed',
      details: {
        testContent,
        result
      }
    });
  };

  // Clear security events
  const handleClearEvents = () => {
    // Events are managed by useSecurity hook
    logSecurityEvent({
      type: 'security_violation',
      severity: 'low',
      message: 'Security events cleared by user',
    });
  };

  // Sync settings with chat auth context
  useEffect(() => {
    setSettings(prev => ({ ...prev, securityLevel: currentSecurityLevel.level }));
  }, [currentSecurityLevel.level]);

  if (!canChangeSecuritySettings) {
    return (
      <Card className={`w-full max-w-4xl mx-auto ${className}`}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Lock className="h-5 w-5" />
            Security Settings
          </CardTitle>
          <CardDescription>
            You don't have permission to modify security settings.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Alert>
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Access Denied</AlertTitle>
            <AlertDescription>
              You need "chat:security:write" permission to modify security settings.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={`w-full max-w-4xl mx-auto space-y-6 ${className}`}>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Security Settings
          </CardTitle>
          <CardDescription>
            Configure security settings for your chat experience
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-5">
              <TabsTrigger value="general">General</TabsTrigger>
              <TabsTrigger value="content">Content</TabsTrigger>
              <TabsTrigger value="data">Data</TabsTrigger>
              <TabsTrigger value="access">Access</TabsTrigger>
              <TabsTrigger value="monitoring">Monitoring</TabsTrigger>
            </TabsList>

            {/* General Settings */}
            <TabsContent value="general" className="space-y-6">
              <div className="space-y-4">
                <div>
                  <h3 className="text-lg font-semibold mb-4">Security Level</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {Object.entries(SECURITY_LEVELS).map(([level, config]) => (
                      <Card 
                        key={level}
                        className={`cursor-pointer transition-all hover:shadow-md ${
                          settings.securityLevel === level ? 'ring-2 ring-primary' : ''
                        }`}
                        onClick={() => handleSecurityLevelChange(level as any)}
                      >
                        <CardHeader className="text-center pb-2">
                          <div className={`mx-auto mb-2 p-3 rounded-full ${config.color}`}>
                            {config.icon}
                          </div>
                          <CardTitle className="text-sm">{config.name}</CardTitle>
                        </CardHeader>
                        <CardContent className="pt-0">
                          <p className="text-xs text-muted-foreground text-center">
                            {config.description}
                          </p>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              </div>
            </TabsContent>

            {/* Content Filtering */}
            <TabsContent value="content" className="space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium">Enable Content Filtering</h4>
                    <p className="text-sm text-muted-foreground">
                      Filter inappropriate or harmful content
                    </p>
                  </div>
                  <Switch
                    checked={settings.contentFiltering.enabled}
                    onCheckedChange={(checked) => 
                      handleContentFilteringChange('enabled', checked)
                    }
                  />
                </div>

                {settings.contentFiltering.enabled && (
                  <>
                    <div>
                      <h4 className="font-medium mb-2">Filter Level</h4>
                      <div className="grid grid-cols-3 gap-2">
                        {(['basic', 'moderate', 'strict'] as const).map(level => (
                          <Button
                            key={level}
                            variant={settings.contentFiltering.level === level ? 'default' : 'outline'}
                            onClick={() => handleContentFilteringChange('level', level)}
                            className="justify-start"
                          >
                            {level.charAt(0).toUpperCase() + level.slice(1)}
                          </Button>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h4 className="font-medium mb-2">Custom Filters</h4>
                      <div className="space-y-2">
                        {settings.contentFiltering.customFilters.map((filter, index) => (
                          <div key={index} className="flex gap-2">
                            <input
                              type="text"
                              value={filter}
                              onChange={(e) => {
                                const newFilters = [...settings.contentFiltering.customFilters];
                                newFilters[index] = e.target.value;
                                handleContentFilteringChange('customFilters', newFilters);
                              }}
                              className="flex-1 px-3 py-2 border rounded-md"
                              placeholder="Enter custom filter..."
                            />
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                const newFilters = settings.contentFiltering.customFilters.filter((_, i) => i !== index);
                                handleContentFilteringChange('customFilters', newFilters);
                              }}
                            >
                              <XCircle className="h-4 w-4" />
                            </Button>
                          </div>
                        ))}
                        <Button
                          variant="outline"
                          onClick={() => {
                            const newFilters = [...settings.contentFiltering.customFilters, ''];
                            handleContentFilteringChange('customFilters', newFilters);
                          }}
                        >
                          Add Filter
                        </Button>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </TabsContent>

            {/* Data Protection */}
            <TabsContent value="data" className="space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium">Data Encryption</h4>
                    <p className="text-sm text-muted-foreground">
                      Encrypt sensitive data at rest
                    </p>
                  </div>
                  <Switch
                    checked={settings.dataProtection.encryption}
                    onCheckedChange={(checked) => 
                      handleDataProtectionChange('encryption', checked)
                    }
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium">Data Anonymization</h4>
                    <p className="text-sm text-muted-foreground">
                      Anonymize user data for privacy
                    </p>
                  </div>
                  <Switch
                    checked={settings.dataProtection.anonymization}
                    onCheckedChange={(checked) => 
                      handleDataProtectionChange('anonymization', checked)
                    }
                  />
                </div>

                <div>
                  <h4 className="font-medium mb-2">Data Retention (days)</h4>
                  <div className="flex items-center gap-4">
                    <Slider
                      value={[settings.dataProtection.dataRetention]}
                      onChange={(value) =>
                        handleDataProtectionChange('dataRetention', Array.isArray(value) ? value[0] : value)
                      }
                      max={365}
                      min={1}
                      step={1}
                      className="flex-1"
                    />
                    <span className="text-sm font-medium w-12">
                      {settings.dataProtection.dataRetention}
                    </span>
                  </div>
                </div>
              </div>
            </TabsContent>

            {/* Access Control */}
            <TabsContent value="access" className="space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium">Two-Factor Authentication</h4>
                    <p className="text-sm text-muted-foreground">
                      Require 2FA for additional security
                    </p>
                  </div>
                  <Switch
                    checked={settings.accessControl.twoFactorAuth}
                    onCheckedChange={(checked) => 
                      handleAccessControlChange('twoFactorAuth', checked)
                    }
                  />
                </div>

                <div>
                  <h4 className="font-medium mb-2">Session Timeout (minutes)</h4>
                  <div className="flex items-center gap-4">
                    <Slider
                      value={[settings.accessControl.sessionTimeout]}
                      onChange={(value) =>
                        handleAccessControlChange('sessionTimeout', Array.isArray(value) ? value[0] : value)
                      }
                      max={120}
                      min={5}
                      step={5}
                      className="flex-1"
                    />
                    <span className="text-sm font-medium w-12">
                      {settings.accessControl.sessionTimeout}
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium">Device Trust</h4>
                    <p className="text-sm text-muted-foreground">
                      Trust recognized devices
                    </p>
                  </div>
                  <Switch
                    checked={settings.accessControl.deviceTrust}
                    onCheckedChange={(checked) => 
                      handleAccessControlChange('deviceTrust', checked)
                    }
                  />
                </div>
              </div>
            </TabsContent>

            {/* Monitoring */}
            <TabsContent value="monitoring" className="space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium">Security Monitoring</h4>
                    <p className="text-sm text-muted-foreground">
                      Monitor security events and threats
                    </p>
                  </div>
                  <Switch
                    checked={settings.monitoring.enabled}
                    onCheckedChange={(checked) => 
                      handleMonitoringChange('enabled', checked)
                    }
                  />
                </div>

                {settings.monitoring.enabled && (
                  <>
                    <div>
                      <h4 className="font-medium mb-2">Alert Level</h4>
                      <div className="grid grid-cols-4 gap-2">
                        {(['low', 'medium', 'high', 'critical'] as const).map(level => (
                          <Button
                            key={level}
                            variant={settings.monitoring.alertLevel === level ? 'default' : 'outline'}
                            onClick={() => handleMonitoringChange('alertLevel', level)}
                            className="justify-start"
                          >
                            {level.charAt(0).toUpperCase() + level.slice(1)}
                          </Button>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h4 className="font-medium mb-2">Log Level</h4>
                      <div className="grid grid-cols-3 gap-2">
                        {(['basic', 'detailed', 'verbose'] as const).map(level => (
                          <Button
                            key={level}
                            variant={settings.monitoring.logLevel === level ? 'default' : 'outline'}
                            onClick={() => handleMonitoringChange('logLevel', level)}
                            className="justify-start"
                          >
                            {level.charAt(0).toUpperCase() + level.slice(1)}
                          </Button>
                        ))}
                      </div>
                    </div>

                    <div className="flex gap-2">
                      <Button onClick={testContentValidation}>
                        <Shield className="mr-2 h-4 w-4" />
                        Test Validation
                      </Button>
                      <Button variant="outline" onClick={handleClearEvents}>
                        <Activity className="mr-2 h-4 w-4" />
                        Clear Events
                      </Button>
                    </div>
                  </>
                )}
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Security Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Security Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="space-y-2">
              <h4 className="font-medium">Current Level</h4>
              <Badge className={SECURITY_LEVELS[settings.securityLevel].color}>
                {SECURITY_LEVELS[settings.securityLevel].name}
              </Badge>
            </div>
            
            <div className="space-y-2">
              <h4 className="font-medium">Active Events</h4>
              <p className="text-2xl font-bold">
                {securityEvents.length}
              </p>
            </div>
            
            <div className="space-y-2">
              <h4 className="font-medium">Threats Detected</h4>
              <p className="text-2xl font-bold text-red-600">
                {securityEvents.filter(e => e.type === 'security_violation').length}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default SecuritySettings;