"use client";

/**
 * System Configuration Panel Component
 * 
 * This component provides the interface for managing system-wide configuration
 * settings including password policies, session settings, and general system options.
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Separator } from '@/components/ui/separator';
import { useToast } from '@/hooks/use-toast';

import { } from 'lucide-react';

interface SystemConfig {
  // Password Policy
  passwordMinLength: number;
  passwordRequireUppercase: boolean;
  passwordRequireLowercase: boolean;
  passwordRequireNumbers: boolean;
  passwordRequireSpecialChars: boolean;
  passwordExpirationDays: number;
  passwordHistoryCount: number;

  // Session Settings
  sessionTimeoutMinutes: number;
  adminSessionTimeoutMinutes: number;
  maxConcurrentSessions: number;
  sessionExtendOnActivity: boolean;

  // Security Settings
  maxLoginAttempts: number;
  lockoutDurationMinutes: number;
  requireMfaForAdmins: boolean;
  requireMfaForUsers: boolean;
  allowedIpRanges: string;

  // Email Settings
  emailFromAddress: string;
  emailFromName: string;
  emailSignature: string;
  enableEmailNotifications: boolean;

  // General Settings
  systemName: string;
  systemDescription: string;
  maintenanceMode: boolean;
  maintenanceMessage: string;
  enableRegistration: boolean;
  enablePasswordReset: boolean;
}

const defaultConfig: SystemConfig = {
  passwordMinLength: 12,
  passwordRequireUppercase: true,
  passwordRequireLowercase: true,
  passwordRequireNumbers: true,
  passwordRequireSpecialChars: true,
  passwordExpirationDays: 90,
  passwordHistoryCount: 5,
  sessionTimeoutMinutes: 60,
  adminSessionTimeoutMinutes: 30,
  maxConcurrentSessions: 3,
  sessionExtendOnActivity: true,
  maxLoginAttempts: 5,
  lockoutDurationMinutes: 15,
  requireMfaForAdmins: true,
  requireMfaForUsers: false,
  allowedIpRanges: '',
  emailFromAddress: '',
  emailFromName: 'System Administrator',
  emailSignature: '',
  enableEmailNotifications: true,
  systemName: 'Admin Management System',
  systemDescription: 'Secure administrative interface',
  maintenanceMode: false,
  maintenanceMessage: 'System is currently under maintenance. Please try again later.',
  enableRegistration: true,
  enablePasswordReset: true
};

export default function SystemConfigurationPanel() {
  const [config, setConfig] = useState<SystemConfig>(defaultConfig);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const { toast } = useToast();

  // Load current configuration
  useEffect(() => {
    loadConfiguration();
  }, []);

  const loadConfiguration = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/admin/system/config');
      if (response.ok) {
        const data = await response.json();
        setConfig({ ...defaultConfig, ...data });
      } else {
        throw new Error('Failed to load configuration');
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load system configuration',
        variant: 'destructive'

    } finally {
      setLoading(false);
    }
  };

  const handleConfigChange = (key: keyof SystemConfig, value: any) => {
    setConfig(prev => ({ ...prev, [key]: value }));
    setHasChanges(true);
  };

  const handleSaveConfiguration = async () => {
    setSaving(true);
    try {
      const response = await fetch('/api/admin/system/config', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)

      if (response.ok) {
        toast({
          title: 'Success',
          description: 'System configuration saved successfully'

        setHasChanges(false);
      } else {
        const error = await response.json();
        throw new Error(error.message || 'Failed to save configuration');
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to save configuration',
        variant: 'destructive'

    } finally {
      setSaving(false);
    }
  };

  const handleResetToDefaults = () => {
    if (confirm('Are you sure you want to reset all settings to their default values? This action cannot be undone.')) {
      setConfig(defaultConfig);
      setHasChanges(true);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary "></div>
        <span className="ml-2">Loading configuration...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Actions */}
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold">System Configuration</h3>
          <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
            Manage system-wide settings and policies
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={handleResetToDefaults}
            disabled={saving}
           >
            <RotateCcw className="mr-2 h-4 w-4 " />
          </Button>
          <button
            onClick={handleSaveConfiguration}
            disabled={!hasChanges || saving}
           aria-label="Button">
            <Save className="mr-2 h-4 w-4 " />
            {saving ? 'Saving...' : 'Save Changes'}
          </Button>
        </div>
      </div>

      {hasChanges && (
        <div className="flex items-center gap-2 p-4 bg-yellow-50 border border-yellow-200 rounded-lg sm:p-4 md:p-6">
          <AlertTriangle className="h-4 w-4 text-yellow-600 " />
          <span className="text-sm text-yellow-800 md:text-base lg:text-lg">
            You have unsaved changes. Don't forget to save your configuration.
          </span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Password Policy */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Key className="h-5 w-5 " />
            </CardTitle>
            <CardDescription>
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="passwordMinLength">Minimum Password Length</Label>
              <input
                id="passwordMinLength"
                type="number"
                min="8"
                max="128"
                value={config.passwordMinLength}
                onChange={(e) => handleConfigChange('passwordMinLength', parseInt(e.target.value))}
              />
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label htmlFor="requireUppercase">Require Uppercase Letters</Label>
                <Switch
                  id="requireUppercase"
                  checked={config.passwordRequireUppercase}
                  onCheckedChange={(checked) => handleConfigChange('passwordRequireUppercase', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="requireLowercase">Require Lowercase Letters</Label>
                <Switch
                  id="requireLowercase"
                  checked={config.passwordRequireLowercase}
                  onCheckedChange={(checked) => handleConfigChange('passwordRequireLowercase', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="requireNumbers">Require Numbers</Label>
                <Switch
                  id="requireNumbers"
                  checked={config.passwordRequireNumbers}
                  onCheckedChange={(checked) => handleConfigChange('passwordRequireNumbers', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="requireSpecialChars">Require Special Characters</Label>
                <Switch
                  id="requireSpecialChars"
                  checked={config.passwordRequireSpecialChars}
                  onCheckedChange={(checked) => handleConfigChange('passwordRequireSpecialChars', checked)}
                />
              </div>
            </div>

            <Separator />

            <div>
              <Label htmlFor="passwordExpirationDays">Password Expiration (Days)</Label>
              <input
                id="passwordExpirationDays"
                type="number"
                min="0"
                max="365"
                value={config.passwordExpirationDays}
                onChange={(e) => handleConfigChange('passwordExpirationDays', parseInt(e.target.value))}
              />
              <p className="text-xs text-muted-foreground mt-1 sm:text-sm md:text-base">
              </p>
            </div>

            <div>
              <Label htmlFor="passwordHistoryCount">Password History Count</Label>
              <input
                id="passwordHistoryCount"
                type="number"
                min="0"
                max="24"
                value={config.passwordHistoryCount}
                onChange={(e) => handleConfigChange('passwordHistoryCount', parseInt(e.target.value))}
              />
              <p className="text-xs text-muted-foreground mt-1 sm:text-sm md:text-base">
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Session Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5 " />
            </CardTitle>
            <CardDescription>
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="sessionTimeout">User Session Timeout (Minutes)</Label>
              <input
                id="sessionTimeout"
                type="number"
                min="5"
                max="1440"
                value={config.sessionTimeoutMinutes}
                onChange={(e) => handleConfigChange('sessionTimeoutMinutes', parseInt(e.target.value))}
              />
            </div>

            <div>
              <Label htmlFor="adminSessionTimeout">Admin Session Timeout (Minutes)</Label>
              <input
                id="adminSessionTimeout"
                type="number"
                min="5"
                max="480"
                value={config.adminSessionTimeoutMinutes}
                onChange={(e) => handleConfigChange('adminSessionTimeoutMinutes', parseInt(e.target.value))}
              />
            </div>

            <div>
              <Label htmlFor="maxConcurrentSessions">Max Concurrent Sessions</Label>
              <input
                id="maxConcurrentSessions"
                type="number"
                min="1"
                max="10"
                value={config.maxConcurrentSessions}
                onChange={(e) => handleConfigChange('maxConcurrentSessions', parseInt(e.target.value))}
              />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="sessionExtendOnActivity">Extend Session on Activity</Label>
              <Switch
                id="sessionExtendOnActivity"
                checked={config.sessionExtendOnActivity}
                onCheckedChange={(checked) => handleConfigChange('sessionExtendOnActivity', checked)}
              />
            </div>
          </CardContent>
        </Card>

        {/* Security Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5 " />
            </CardTitle>
            <CardDescription>
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="maxLoginAttempts">Max Login Attempts</Label>
              <input
                id="maxLoginAttempts"
                type="number"
                min="3"
                max="10"
                value={config.maxLoginAttempts}
                onChange={(e) => handleConfigChange('maxLoginAttempts', parseInt(e.target.value))}
              />
            </div>

            <div>
              <Label htmlFor="lockoutDuration">Lockout Duration (Minutes)</Label>
              <input
                id="lockoutDuration"
                type="number"
                min="1"
                max="1440"
                value={config.lockoutDurationMinutes}
                onChange={(e) => handleConfigChange('lockoutDurationMinutes', parseInt(e.target.value))}
              />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="requireMfaForAdmins">Require MFA for Admins</Label>
              <Switch
                id="requireMfaForAdmins"
                checked={config.requireMfaForAdmins}
                onCheckedChange={(checked) => handleConfigChange('requireMfaForAdmins', checked)}
              />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="requireMfaForUsers">Require MFA for Users</Label>
              <Switch
                id="requireMfaForUsers"
                checked={config.requireMfaForUsers}
                onCheckedChange={(checked) => handleConfigChange('requireMfaForUsers', checked)}
              />
            </div>

            <div>
              <Label htmlFor="allowedIpRanges">Allowed IP Ranges (Optional)</Label>
              <textarea
                id="allowedIpRanges"
                placeholder="192.168.1.0/24&#10;10.0.0.0/8"
                value={config.allowedIpRanges}
                onChange={(e) => handleConfigChange('allowedIpRanges', e.target.value)}
                rows={3}
              />
              <p className="text-xs text-muted-foreground mt-1 sm:text-sm md:text-base">
                One IP range per line. Leave empty to allow all IPs.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Email Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Mail className="h-5 w-5 " />
            </CardTitle>
            <CardDescription>
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <Label htmlFor="enableEmailNotifications">Enable Email Notifications</Label>
              <Switch
                id="enableEmailNotifications"
                checked={config.enableEmailNotifications}
                onCheckedChange={(checked) => handleConfigChange('enableEmailNotifications', checked)}
              />
            </div>

            <div>
              <Label htmlFor="emailFromAddress">From Email Address</Label>
              <input
                id="emailFromAddress"
                type="email"
                placeholder="noreply@example.com"
                value={config.emailFromAddress}
                onChange={(e) => handleConfigChange('emailFromAddress', e.target.value)}
              />
            </div>

            <div>
              <Label htmlFor="emailFromName">From Name</Label>
              <input
                id="emailFromName"
                placeholder="System Administrator"
                value={config.emailFromName}
                onChange={(e) => handleConfigChange('emailFromName', e.target.value)}
              />
            </div>

            <div>
              <Label htmlFor="emailSignature">Email Signature</Label>
              <textarea
                id="emailSignature"
                placeholder="Best regards,&#10;The Admin Team"
                value={config.emailSignature}
                onChange={(e) => handleConfigChange('emailSignature', e.target.value)}
                rows={3}
              />
            </div>
          </CardContent>
        </Card>

        {/* General Settings */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Info className="h-5 w-5 " />
            </CardTitle>
            <CardDescription>
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="systemName">System Name</Label>
                <input
                  id="systemName"
                  placeholder="Admin Management System"
                  value={config.systemName}
                  onChange={(e) => handleConfigChange('systemName', e.target.value)}
                />
              </div>

              <div>
                <Label htmlFor="systemDescription">System Description</Label>
                <input
                  id="systemDescription"
                  placeholder="Secure administrative interface"
                  value={config.systemDescription}
                  onChange={(e) => handleConfigChange('systemDescription', e.target.value)}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex items-center justify-between">
                <Label htmlFor="enableRegistration">Enable User Registration</Label>
                <Switch
                  id="enableRegistration"
                  checked={config.enableRegistration}
                  onCheckedChange={(checked) => handleConfigChange('enableRegistration', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="enablePasswordReset">Enable Password Reset</Label>
                <Switch
                  id="enablePasswordReset"
                  checked={config.enablePasswordReset}
                  onCheckedChange={(checked) => handleConfigChange('enablePasswordReset', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="maintenanceMode">Maintenance Mode</Label>
                <Switch
                  id="maintenanceMode"
                  checked={config.maintenanceMode}
                  onCheckedChange={(checked) => handleConfigChange('maintenanceMode', checked)}
                />
              </div>
            </div>

            {config.maintenanceMode && (
              <div>
                <Label htmlFor="maintenanceMessage">Maintenance Message</Label>
                <textarea
                  id="maintenanceMessage"
                  placeholder="System is currently under maintenance..."
                  value={config.maintenanceMessage}
                  onChange={(e) => handleConfigChange('maintenanceMessage', e.target.value)}
                  rows={2}
                />
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}