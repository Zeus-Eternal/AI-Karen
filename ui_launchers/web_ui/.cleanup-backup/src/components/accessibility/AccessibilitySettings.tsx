'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Label } from '../ui/label';
import { Switch } from '../ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Slider } from '../ui/slider';
import { Button } from '../ui/button';
import { useAccessibilityEnhancements } from './AccessibilityProvider';
import { useAccessibility } from '../../providers/accessibility-provider';
import { cn } from '../../lib/utils';

interface AccessibilitySettingsProps {
  className?: string;
}

export function AccessibilitySettings({ className }: AccessibilitySettingsProps) {
  const {
    highContrastMode,
    toggleHighContrast,
    keyboardNavigationEnabled,
    setKeyboardNavigationEnabled,
    textScale,
    setTextScale,
    colorBlindnessFilter,
    setColorBlindnessFilter,
    announceMessage,
  } = useAccessibilityEnhancements();

  const { settings, updateSetting, resetSettings } = useAccessibility();

  const handleFontSizeChange = (size: 'small' | 'medium' | 'large' | 'extra-large') => {
    updateSetting('fontSize', size);
    announceMessage(`Font size changed to ${size}`);
  };

  const handleLineHeightChange = (height: 'normal' | 'relaxed' | 'loose') => {
    updateSetting('lineHeight', height);
    announceMessage(`Line height changed to ${height}`);
  };

  const handleTextScaleChange = (value: number[]) => {
    const scale = value[0];
    setTextScale(scale);
    announceMessage(`Text scale changed to ${Math.round(scale * 100)}%`);
  };

  const handleResetSettings = () => {
    resetSettings();
    setTextScale(1);
    setKeyboardNavigationEnabled(true);
    announceMessage('Accessibility settings reset to defaults');
  };

  return (
    <div className={cn('space-y-6', className)}>
      {/* Visual Accessibility */}
      <Card>
        <CardHeader>
          <CardTitle>Visual Accessibility</CardTitle>
          <CardDescription>
            Adjust visual settings to improve readability and contrast
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* High Contrast Mode */}
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="high-contrast">High Contrast Mode</Label>
              <p className="text-sm text-muted-foreground">
                Increase contrast for better visibility
              </p>
            </div>
            <Switch
              id="high-contrast"
              checked={highContrastMode}
              onCheckedChange={toggleHighContrast}
              aria-describedby="high-contrast-description"
            />
          </div>

          {/* Font Size */}
          <div className="space-y-2">
            <Label htmlFor="font-size">Font Size</Label>
            <Select
              value={settings.fontSize}
              onValueChange={handleFontSizeChange}
            >
              <SelectTrigger id="font-size">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="small">Small</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="large">Large</SelectItem>
                <SelectItem value="extra-large">Extra Large</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Line Height */}
          <div className="space-y-2">
            <Label htmlFor="line-height">Line Height</Label>
            <Select
              value={settings.lineHeight}
              onValueChange={handleLineHeightChange}
            >
              <SelectTrigger id="line-height">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="normal">Normal</SelectItem>
                <SelectItem value="relaxed">Relaxed</SelectItem>
                <SelectItem value="loose">Loose</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Text Scale */}
          <div className="space-y-2">
            <Label htmlFor="text-scale">
              Text Scale: {Math.round(textScale * 100)}%
            </Label>
            <Slider
              id="text-scale"
              min={0.8}
              max={2}
              step={0.1}
              value={[textScale]}
              onValueChange={handleTextScaleChange}
              className="w-full"
              aria-describedby="text-scale-description"
            />
            <p id="text-scale-description" className="text-sm text-muted-foreground">
              Adjust the overall text size scaling
            </p>
          </div>

          {/* Color Blindness Support */}
          <div className="space-y-2">
            <Label htmlFor="color-blindness">Color Blindness Support</Label>
            <Select
              value={colorBlindnessFilter}
              onValueChange={setColorBlindnessFilter}
            >
              <SelectTrigger id="color-blindness">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">None</SelectItem>
                <SelectItem value="protanopia">Protanopia (Red-blind)</SelectItem>
                <SelectItem value="deuteranopia">Deuteranopia (Green-blind)</SelectItem>
                <SelectItem value="tritanopia">Tritanopia (Blue-blind)</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Motion and Animation */}
      <Card>
        <CardHeader>
          <CardTitle>Motion and Animation</CardTitle>
          <CardDescription>
            Control animations and motion effects
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="reduced-motion">Reduce Motion</Label>
              <p className="text-sm text-muted-foreground">
                Minimize animations and transitions
              </p>
            </div>
            <Switch
              id="reduced-motion"
              checked={settings.reducedMotion}
              onCheckedChange={(checked) => updateSetting('reducedMotion', checked)}
            />
          </div>
        </CardContent>
      </Card>

      {/* Interaction Accessibility */}
      <Card>
        <CardHeader>
          <CardTitle>Interaction</CardTitle>
          <CardDescription>
            Configure interaction and navigation preferences
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Keyboard Navigation */}
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="keyboard-nav">Enhanced Keyboard Navigation</Label>
              <p className="text-sm text-muted-foreground">
                Enable advanced keyboard navigation features
              </p>
            </div>
            <Switch
              id="keyboard-nav"
              checked={keyboardNavigationEnabled}
              onCheckedChange={setKeyboardNavigationEnabled}
            />
          </div>

          {/* Focus Visible */}
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="focus-visible">Focus Indicators</Label>
              <p className="text-sm text-muted-foreground">
                Show focus indicators for keyboard navigation
              </p>
            </div>
            <Switch
              id="focus-visible"
              checked={settings.focusVisible}
              onCheckedChange={(checked) => updateSetting('focusVisible', checked)}
            />
          </div>
        </CardContent>
      </Card>

      {/* Screen Reader */}
      <Card>
        <CardHeader>
          <CardTitle>Screen Reader</CardTitle>
          <CardDescription>
            Configure screen reader and assistive technology support
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Announcements */}
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="announcements">Live Announcements</Label>
              <p className="text-sm text-muted-foreground">
                Enable automatic announcements for screen readers
              </p>
            </div>
            <Switch
              id="announcements"
              checked={settings.announcements}
              onCheckedChange={(checked) => updateSetting('announcements', checked)}
            />
          </div>

          {/* Verbose Descriptions */}
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="verbose-descriptions">Verbose Descriptions</Label>
              <p className="text-sm text-muted-foreground">
                Provide detailed descriptions for complex elements
              </p>
            </div>
            <Switch
              id="verbose-descriptions"
              checked={settings.verboseDescriptions}
              onCheckedChange={(checked) => updateSetting('verboseDescriptions', checked)}
            />
          </div>
        </CardContent>
      </Card>

      {/* Reset Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Reset Settings</CardTitle>
          <CardDescription>
            Reset all accessibility settings to their default values
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button
            variant="outline"
            onClick={handleResetSettings}
            className="w-full"
          >
            Reset to Defaults
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

export default AccessibilitySettings;