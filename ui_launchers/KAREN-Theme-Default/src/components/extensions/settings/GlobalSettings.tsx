"use client";

/**
 * Global Settings
 *
 * System-wide settings and preferences for the extension platform
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Slider } from '@/components/ui/slider';
import {
  Settings,
  Bell,
  Shield,
  Palette,
  Globe,
  RefreshCw,
  Save,
  RotateCcw,
  CheckCircle
} from 'lucide-react';

export interface GlobalSettingsConfig {
  notifications: {
    enabled: boolean;
    email: boolean;
    browser: boolean;
    sound: boolean;
  };
  security: {
    autoLogout: boolean;
    autoLogoutMinutes: number;
    requireMFA: boolean;
    allowRememberDevice: boolean;
  };
  appearance: {
    theme: 'light' | 'dark' | 'auto';
    compactMode: boolean;
    animationsEnabled: boolean;
  };
  general: {
    language: string;
    timezone: string;
    autoSave: boolean;
    autoSaveInterval: number;
  };
}

export interface GlobalSettingsProps {
  onSave?: (config: GlobalSettingsConfig) => Promise<void>;
  refreshInterval?: number;
}

export default function GlobalSettings({
  onSave,
  refreshInterval = 30000
}: GlobalSettingsProps) {
  const [config, setConfig] = useState<GlobalSettingsConfig>({
    notifications: {
      enabled: true,
      email: true,
      browser: true,
      sound: false
    },
    security: {
      autoLogout: true,
      autoLogoutMinutes: 30,
      requireMFA: false,
      allowRememberDevice: true
    },
    appearance: {
      theme: 'auto',
      compactMode: false,
      animationsEnabled: true
    },
    general: {
      language: 'en',
      timezone: 'UTC',
      autoSave: true,
      autoSaveInterval: 60
    }
  });

  const [hasChanges, setHasChanges] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const updateConfig = (section: keyof GlobalSettingsConfig, key: string, value: any) => {
    setConfig(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value
      }
    }));
    setHasChanges(true);
    setSaved(false);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      if (onSave) {
        await onSave(config);
      }
      setHasChanges(false);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (error) {
      console.error('Failed to save settings:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    setConfig({
      notifications: {
        enabled: true,
        email: true,
        browser: true,
        sound: false
      },
      security: {
        autoLogout: true,
        autoLogoutMinutes: 30,
        requireMFA: false,
        allowRememberDevice: true
      },
      appearance: {
        theme: 'auto',
        compactMode: false,
        animationsEnabled: true
      },
      general: {
        language: 'en',
        timezone: 'UTC',
        autoSave: true,
        autoSaveInterval: 60
      }
    });
    setHasChanges(false);
    setSaved(false);
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              Global Settings
            </div>
            <div className="flex gap-2">
              {hasChanges && (
                <Button onClick={handleReset} variant="outline" size="sm">
                  <RotateCcw className="h-4 w-4 mr-2" />
                  Reset
                </Button>
              )}
              <Button onClick={handleSave} disabled={!hasChanges || saving} size="sm">
                {saving ? (
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                ) : saved ? (
                  <CheckCircle className="h-4 w-4 mr-2 text-green-600" />
                ) : (
                  <Save className="h-4 w-4 mr-2" />
                )}
                {saving ? 'Saving...' : saved ? 'Saved!' : 'Save Changes'}
              </Button>
            </div>
          </CardTitle>
          <CardDescription>
            Configure system-wide preferences and settings
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="notifications">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="notifications">
                <Bell className="h-4 w-4 mr-2" />
                Notifications
              </TabsTrigger>
              <TabsTrigger value="security">
                <Shield className="h-4 w-4 mr-2" />
                Security
              </TabsTrigger>
              <TabsTrigger value="appearance">
                <Palette className="h-4 w-4 mr-2" />
                Appearance
              </TabsTrigger>
              <TabsTrigger value="general">
                <Globe className="h-4 w-4 mr-2" />
                General
              </TabsTrigger>
            </TabsList>

            {/* Notifications Tab */}
            <TabsContent value="notifications" className="space-y-4">
              <Card>
                <CardContent className="pt-6 space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium">Enable Notifications</h4>
                      <p className="text-sm text-muted-foreground">
                        Receive notifications about system events
                      </p>
                    </div>
                    <Switch
                      checked={config.notifications.enabled}
                      onCheckedChange={(checked) => updateConfig('notifications', 'enabled', checked)}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium">Email Notifications</h4>
                      <p className="text-sm text-muted-foreground">
                        Send notifications via email
                      </p>
                    </div>
                    <Switch
                      checked={config.notifications.email}
                      onCheckedChange={(checked) => updateConfig('notifications', 'email', checked)}
                      disabled={!config.notifications.enabled}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium">Browser Notifications</h4>
                      <p className="text-sm text-muted-foreground">
                        Show browser push notifications
                      </p>
                    </div>
                    <Switch
                      checked={config.notifications.browser}
                      onCheckedChange={(checked) => updateConfig('notifications', 'browser', checked)}
                      disabled={!config.notifications.enabled}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium">Sound Alerts</h4>
                      <p className="text-sm text-muted-foreground">
                        Play sound for important notifications
                      </p>
                    </div>
                    <Switch
                      checked={config.notifications.sound}
                      onCheckedChange={(checked) => updateConfig('notifications', 'sound', checked)}
                      disabled={!config.notifications.enabled}
                    />
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Security Tab */}
            <TabsContent value="security" className="space-y-4">
              <Card>
                <CardContent className="pt-6 space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium">Auto Logout</h4>
                      <p className="text-sm text-muted-foreground">
                        Automatically logout after inactivity
                      </p>
                    </div>
                    <Switch
                      checked={config.security.autoLogout}
                      onCheckedChange={(checked) => updateConfig('security', 'autoLogout', checked)}
                    />
                  </div>

                  {config.security.autoLogout && (
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <label className="text-sm font-medium">
                          Auto Logout After (minutes)
                        </label>
                        <span className="text-sm font-medium">{config.security.autoLogoutMinutes}</span>
                      </div>
                      <Slider
                        value={[config.security.autoLogoutMinutes]}
                        onValueChange={([value]) => updateConfig('security', 'autoLogoutMinutes', value)}
                        min={5}
                        max={120}
                        step={5}
                      />
                    </div>
                  )}

                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium">Require Multi-Factor Authentication</h4>
                      <p className="text-sm text-muted-foreground">
                        Add an extra layer of security
                      </p>
                    </div>
                    <Switch
                      checked={config.security.requireMFA}
                      onCheckedChange={(checked) => updateConfig('security', 'requireMFA', checked)}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium">Allow Remember Device</h4>
                      <p className="text-sm text-muted-foreground">
                        Remember trusted devices for 30 days
                      </p>
                    </div>
                    <Switch
                      checked={config.security.allowRememberDevice}
                      onCheckedChange={(checked) => updateConfig('security', 'allowRememberDevice', checked)}
                    />
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Appearance Tab */}
            <TabsContent value="appearance" className="space-y-4">
              <Card>
                <CardContent className="pt-6 space-y-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Theme</label>
                    <div className="flex gap-2">
                      {(['light', 'dark', 'auto'] as const).map((theme) => (
                        <Button
                          key={theme}
                          variant={config.appearance.theme === theme ? 'default' : 'outline'}
                          size="sm"
                          onClick={() => updateConfig('appearance', 'theme', theme)}
                          className="capitalize"
                        >
                          {theme}
                        </Button>
                      ))}
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium">Compact Mode</h4>
                      <p className="text-sm text-muted-foreground">
                        Reduce spacing for denser interface
                      </p>
                    </div>
                    <Switch
                      checked={config.appearance.compactMode}
                      onCheckedChange={(checked) => updateConfig('appearance', 'compactMode', checked)}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium">Enable Animations</h4>
                      <p className="text-sm text-muted-foreground">
                        Show smooth transitions and animations
                      </p>
                    </div>
                    <Switch
                      checked={config.appearance.animationsEnabled}
                      onCheckedChange={(checked) => updateConfig('appearance', 'animationsEnabled', checked)}
                    />
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* General Tab */}
            <TabsContent value="general" className="space-y-4">
              <Card>
                <CardContent className="pt-6 space-y-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Language</label>
                    <Input
                      value={config.general.language}
                      onChange={(e) => updateConfig('general', 'language', e.target.value)}
                      placeholder="en"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Timezone</label>
                    <Input
                      value={config.general.timezone}
                      onChange={(e) => updateConfig('general', 'timezone', e.target.value)}
                      placeholder="UTC"
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium">Auto Save</h4>
                      <p className="text-sm text-muted-foreground">
                        Automatically save changes
                      </p>
                    </div>
                    <Switch
                      checked={config.general.autoSave}
                      onCheckedChange={(checked) => updateConfig('general', 'autoSave', checked)}
                    />
                  </div>

                  {config.general.autoSave && (
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <label className="text-sm font-medium">
                          Auto Save Interval (seconds)
                        </label>
                        <span className="text-sm font-medium">{config.general.autoSaveInterval}</span>
                      </div>
                      <Slider
                        value={[config.general.autoSaveInterval]}
                        onValueChange={([value]) => updateConfig('general', 'autoSaveInterval', value)}
                        min={15}
                        max={300}
                        step={15}
                      />
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}

export { GlobalSettings };
export type { GlobalSettingsProps, GlobalSettingsConfig };
