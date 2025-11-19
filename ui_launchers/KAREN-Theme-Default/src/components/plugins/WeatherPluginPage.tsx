"use client";

import * as React from 'react';
import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { CloudSun, AlertTriangle, Info, Save, KeyRound } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { alertClassName } from "./utils/alertVariants";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import type { KarenSettings, TemperatureUnit, WeatherServiceOption } from "@/lib/types";
import { KAREN_SETTINGS_LS_KEY, DEFAULT_KAREN_SETTINGS } from "@/lib/constants";
import { useToast } from "@/hooks/use-toast";
import { Separator } from '../ui/separator';
/**
 * @file WeatherPluginPage.tsx
 * @description Page for configuring Weather Service settings for Karen AI.
 * When the backend provides an OPENWEATHER_API_KEY environment variable,
 * live weather data is fetched from OpenWeatherMap. Otherwise, mocked
 * responses are used. This page lets users set preferences for the future
 * full integration.
 */
export default function WeatherPluginPage() {
  const [settings, setSettings] = useState<Pick<KarenSettings, 'temperatureUnit' | 'weatherService' | 'weatherApiKey' | 'defaultWeatherLocation'>>(() => {
    const defaults = {
      temperatureUnit: DEFAULT_KAREN_SETTINGS.temperatureUnit,
      weatherService: DEFAULT_KAREN_SETTINGS.weatherService,
      weatherApiKey: DEFAULT_KAREN_SETTINGS.weatherApiKey,
      defaultWeatherLocation: DEFAULT_KAREN_SETTINGS.defaultWeatherLocation,
    };

    if (typeof window === 'undefined') {
      return defaults;
    }

    try {
      const storedSettingsStr = window.localStorage.getItem(KAREN_SETTINGS_LS_KEY);
      if (!storedSettingsStr) {
        return defaults;
      }

      const parsedSettings: Partial<KarenSettings> = JSON.parse(storedSettingsStr);

      return {
        ...defaults,
        temperatureUnit: parsedSettings.temperatureUnit || defaults.temperatureUnit,
        weatherService: parsedSettings.weatherService || defaults.weatherService,
        weatherApiKey:
          typeof parsedSettings.weatherApiKey === 'string'
            ? parsedSettings.weatherApiKey
            : defaults.weatherApiKey,
        defaultWeatherLocation:
          typeof parsedSettings.defaultWeatherLocation === 'string' && parsedSettings.defaultWeatherLocation.trim()
            ? parsedSettings.defaultWeatherLocation
            : defaults.defaultWeatherLocation,
      };
    } catch (error) {
      console.error('Failed to read stored weather settings:', error);
      return defaults;
    }
  });

  const { toast } = useToast();
  const handleUnitChange = (unit: TemperatureUnit) => {
    setSettings(prev => ({ ...prev, temperatureUnit: unit }));
  };
  const handleServiceChange = (service: WeatherServiceOption) => {
    setSettings(prev => ({
      ...prev,
      weatherService: service,
      // Reset API key if switching away from custom_api, or if custom_api is selected and no key was there
      weatherApiKey: service === 'custom_api' ? (prev.weatherApiKey || '') : null
    }));
  };
  const savePreferences = () => {
    try {
      const storedSettingsStr = window.localStorage.getItem(KAREN_SETTINGS_LS_KEY);
      let currentFullSettings: KarenSettings = { ...DEFAULT_KAREN_SETTINGS };
      if (storedSettingsStr) {
        currentFullSettings = { ...currentFullSettings, ...JSON.parse(storedSettingsStr) };
      }
      const updatedSettings: KarenSettings = {
        ...currentFullSettings,
        temperatureUnit: settings.temperatureUnit,
        weatherService: settings.weatherService,
        weatherApiKey: ['custom_api', 'openweather'].includes(settings.weatherService)
          ? settings.weatherApiKey
          : null,
        defaultWeatherLocation: settings.defaultWeatherLocation,
      };
      window.localStorage.setItem(KAREN_SETTINGS_LS_KEY, JSON.stringify(updatedSettings));
      toast({
        title: "Weather Preferences Saved",
        description: "Your weather service settings have been updated.",
      });
    } catch (error) {
      console.error('Failed to save weather preferences:', error);
      toast({
        variant: "destructive",
        title: "Save Error",
        description: "Could not save weather preferences.",
      });
    }
  };
  return (
    <div className="space-y-8">
      <div className="flex items-center space-x-3">
        <CloudSun className="h-8 w-8 text-primary " />
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">Weather Service Configuration</h2>
          <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
            Configure how Karen AI fetches and displays weather information.
          </p>
        </div>
      </div>
       <Alert>
        <Info className="h-4 w-4 " />
        <AlertTitle>How to Use Weather Features</AlertTitle>
        <AlertDescription>
          Ask Karen for the weather in a specific location directly in the chat (e.g., "What's the weather in London?").
          She can use different services based on your configuration below. The "Default Location" can be used if you ask for weather without specifying a place.
        </AlertDescription>
      </Alert>
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Weather Service & Preferences</CardTitle>
          <CardDescription>
            Choose your weather data source and display preferences.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="weather-service-select">Weather Service Source</Label>
            <Select
              value={settings.weatherService}
              onValueChange={(value) => handleServiceChange(value as WeatherServiceOption)}
            >
              <SelectTrigger id="weather-service-select">
                <SelectValue placeholder="Select a weather service" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="wttr_in">wttr.in (Free, Recommended)</SelectItem>
                <SelectItem value="openweather">OpenWeatherMap</SelectItem>
                <SelectItem value="custom_api">Custom API (Conceptual)</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
              Select the service Karen should use. "Custom API" is a placeholder for future integration with services requiring an API key.
            </p>
          </div>
          {['custom_api', 'openweather'].includes(settings.weatherService) && (
            <div className="space-y-2 pl-4 border-l-2 border-primary/20 py-3">
              <Label htmlFor="weather-api-key" className="flex items-center"><KeyRound className="mr-2 h-4 w-4 text-primary/80 "/>Weather API Key</Label>
              <Input
                id="weather-api-key"
                type="password"
                value={settings.weatherApiKey || ''}
                onChange={(e) => setSettings(prev => ({ ...prev, weatherApiKey: e.target.value }))}
                placeholder="Enter your API key"
                disabled /* Keep disabled until actual service logic is implemented */
              />
              <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
                API key usage requires backend support for the selected service.
              </p>
            </div>
          )}
          <Separator />
          <div className="space-y-2">
            <Label htmlFor="default-weather-location">Default Weather Location (Optional)</Label>
            <Input
              id="default-weather-location"
              value={settings.defaultWeatherLocation || ''}
              onChange={(e) => setSettings(prev => ({ ...prev, defaultWeatherLocation: e.target.value.trim() ? e.target.value : null }))}
              placeholder="e.g., London, UK or New York, US"
            />
            <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
              If set, Karen can use this location if you ask for weather without specifying a place.
            </p>
          </div>
          <Separator />
          <div className="space-y-2">
            <Label>Preferred Temperature Unit</Label>
            <div className="flex items-center space-x-2">
                <Button
                  variant={settings.temperatureUnit === 'C' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => handleUnitChange('C')}
                  className="rounded-md"
                >
                  Celsius (°C)
                </Button>
                <Button
                  variant={settings.temperatureUnit === 'F' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => handleUnitChange('F')}
                  className="rounded-md"
                >
                  Fahrenheit (°F)
                </Button>
            </div>
            <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
              This preference will be used when Karen reports the weather.
            </p>
          </div>
        </CardContent>
        <CardFooter className="flex justify-end">
          <Button onClick={savePreferences}>
            <Save className="mr-2 h-4 w-4 " /> Save Weather Preferences
          </Button>
        </CardFooter>
      </Card>
      <Alert className={alertClassName("destructive")}>
        <AlertTriangle className="h-4 w-4 " />
        <AlertTitle>About Weather Integration</AlertTitle>
        <AlertDescription>
          <p>
            If the backend is configured with a valid <code>OPENWEATHER_API_KEY</code>,
            Karen will fetch live weather data from OpenWeatherMap. Without it,
            the plugin returns mocked results for demo purposes. You can also set a default location
            to get weather information without specifying a city.
          </p>
        </AlertDescription>
      </Alert>
    </div>
  );
}
