"use client";

import * as React from 'react';
import { useState } from 'react';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Checkbox } from '@/components/ui/checkbox';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import type { KarenSettings, NotificationPreferences } from '@/lib/types';
import { KAREN_SETTINGS_LS_KEY, DEFAULT_KAREN_SETTINGS } from '@/lib/constants';
import { Button } from '../ui/button';
import { useToast } from '@/hooks/use-toast';
/**
 * @file NotificationSettings.tsx
 * @description Component for managing Karen AI's notification preferences.
 * Allows users to enable/disable notifications and select alert types.
 * Settings are saved to local storage.
 */
const mergeWithDefaults = (settings?: Partial<KarenSettings>): KarenSettings => ({
  ...DEFAULT_KAREN_SETTINGS,
  ...settings,
  notifications: {
    ...DEFAULT_KAREN_SETTINGS.notifications,
    ...(settings?.notifications || {}),
  },
  personalFacts:
    settings && Array.isArray(settings.personalFacts)
      ? settings.personalFacts
      : DEFAULT_KAREN_SETTINGS.personalFacts,
  ttsVoiceURI:
    settings?.ttsVoiceURI === undefined
      ? DEFAULT_KAREN_SETTINGS.ttsVoiceURI
      : settings.ttsVoiceURI,
  customPersonaInstructions:
    settings && typeof settings.customPersonaInstructions === 'string'
      ? settings.customPersonaInstructions
      : DEFAULT_KAREN_SETTINGS.customPersonaInstructions,
  memoryDepth: settings?.memoryDepth || DEFAULT_KAREN_SETTINGS.memoryDepth,
  personalityTone:
    settings?.personalityTone || DEFAULT_KAREN_SETTINGS.personalityTone,
  personalityVerbosity:
    settings?.personalityVerbosity || DEFAULT_KAREN_SETTINGS.personalityVerbosity,
});

export default function NotificationSettings() {
  const readAndNormalizeSettings = (): KarenSettings => {
    if (typeof window === 'undefined') {
      return DEFAULT_KAREN_SETTINGS;
    }

    try {
      const storedSettingsStr = localStorage.getItem(KAREN_SETTINGS_LS_KEY);
      if (!storedSettingsStr) {
        localStorage.setItem(
          KAREN_SETTINGS_LS_KEY,
          JSON.stringify(DEFAULT_KAREN_SETTINGS)
        );
        return DEFAULT_KAREN_SETTINGS;
      }

      const parsedSettings = JSON.parse(storedSettingsStr) as Partial<KarenSettings>;
      const mergedSettings = mergeWithDefaults(parsedSettings);
      const normalizedSettings = JSON.stringify(mergedSettings);

      if (normalizedSettings !== storedSettingsStr) {
        localStorage.setItem(KAREN_SETTINGS_LS_KEY, normalizedSettings);
      }

      return mergedSettings;
    } catch (error) {
      console.error('Failed to read notification settings from localStorage.', error);
      try {
        localStorage.setItem(
          KAREN_SETTINGS_LS_KEY,
          JSON.stringify(DEFAULT_KAREN_SETTINGS)
        );
      } catch (storageError) {
        console.error('Failed to reset notification settings in localStorage.', storageError);
      }
      return DEFAULT_KAREN_SETTINGS;
    }
  };

  const [notifications, setNotifications] = useState<NotificationPreferences>(() =>
    readAndNormalizeSettings().notifications
  );
  const { toast } = useToast();
  const handleEnabledChange = (enabled: boolean) => {
    setNotifications(prev => ({ ...prev, enabled }));
  };
  const handleAlertTypeChange = (alertType: keyof Omit<NotificationPreferences, 'enabled'>, checked: boolean) => {
    setNotifications(prev => ({ ...prev, [alertType]: checked }));
  };
  const getFullCurrentSettingsFromStorage = (): KarenSettings => {
    return readAndNormalizeSettings();
  };
  const saveSettings = () => {
    try {
      const currentFullSettings = getFullCurrentSettingsFromStorage();
      const safeNotifications = {
        ...DEFAULT_KAREN_SETTINGS.notifications,
        ...notifications
      };
      const newSettings: KarenSettings = {
        ...currentFullSettings,
        notifications: safeNotifications
      };
      localStorage.setItem(KAREN_SETTINGS_LS_KEY, JSON.stringify(newSettings));
      toast({
        title: "Notification Settings Saved",
        description: "Your notification preferences have been updated.",
      });
    } catch (error) {
      console.error('Failed to save notification settings.', error);
      toast({
        title: "Error Saving Notification Settings",
        description: "Could not save notification preferences. localStorage might be disabled or full.",
        variant: "destructive",
      });
    }
  };
  const resetToDefaults = () => {
    setNotifications(DEFAULT_KAREN_SETTINGS.notifications);
    try {
        const currentFullSettings = getFullCurrentSettingsFromStorage();
        const newFullSettings: KarenSettings = {
            ...currentFullSettings,
            notifications: DEFAULT_KAREN_SETTINGS.notifications,
        };
        localStorage.setItem(KAREN_SETTINGS_LS_KEY, JSON.stringify(newFullSettings));
        toast({
          title: "Notification Settings Reset",
          description: "Notification preferences have been reset to defaults.",
        });
    } catch (error) {
        console.error('Failed to reset notification settings.', error);
        toast({
            title: "Error Resetting Notification Settings",
            description: "Could not reset notification preferences.",
            variant: "destructive",
        });

    }
  };
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Notification Preferences</CardTitle>
        <CardDescription>
          Manage how and when Karen AI notifies you.
        </CardDescription>
      </CardHeader>
      <CardContent className="p-0 sm:p-4 md:p-6">
        <div className="divide-y divide-border">
          <div className="px-6 py-4">
            <div className="flex items-center space-x-2">
              <Switch
                id="enable-notifications"
                checked={notifications.enabled}
                onCheckedChange={handleEnabledChange}
              />
              <Label htmlFor="enable-notifications" className="cursor-pointer">Enable All Notifications</Label>
            </div>
            <p className="text-xs text-muted-foreground mt-2 sm:text-sm md:text-base">
              Toggle all app notifications on or off. Specific alert types below require this to be enabled.
            </p>
          </div>
          <div className="px-6 py-4 space-y-4">
            <Label className="text-base font-medium block mb-2">Alert Types</Label>
            <div className="space-y-1">
                <div className="flex items-center space-x-3">
                <Checkbox
                    id="alert-insights"
                    checked={notifications.alertOnNewInsights}
                    onCheckedChange={(checked) => handleAlertTypeChange('alertOnNewInsights', !!checked)}
                    disabled={!notifications.enabled}
                />
                <Label htmlFor="alert-insights" className={`cursor-pointer ${!notifications.enabled ? 'text-muted-foreground' : ''}`}>
                </Label>
                </div>
                <p className="text-xs text-muted-foreground pl-7 sm:text-sm md:text-base">
                Get a toast notification when Karen AI provides new insights in her message.
                </p>
            </div>
            <div className="space-y-1">
                <div className="flex items-center space-x-3">
                <Checkbox
                    id="alert-summary"
                    checked={notifications.alertOnSummaryReady}
                    onCheckedChange={(checked) => handleAlertTypeChange('alertOnSummaryReady', !!checked)}
                    disabled={!notifications.enabled}
                />
                <Label htmlFor="alert-summary" className={`cursor-pointer ${!notifications.enabled ? 'text-muted-foreground' : ''}`}>
                </Label>
                </div>
                <p className="text-xs text-muted-foreground pl-7 sm:text-sm md:text-base">
                  Notify when a conversation summary is generated.
                </p>
            </div>
          </div>
        </div>
      </CardContent>
      <CardFooter className="flex justify-end space-x-2">
            <Button variant="outline" onClick={resetToDefaults} >Reset to Defaults</Button>
            <Button onClick={saveSettings} >Save Settings</Button>
      </CardFooter>
    </Card>
  );
}
