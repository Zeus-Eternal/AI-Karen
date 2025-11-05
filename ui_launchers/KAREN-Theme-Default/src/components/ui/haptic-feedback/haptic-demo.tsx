"use client";

import React, { useState } from 'react';
import { HapticProvider } from './haptic-provider';
import { HapticButton } from './haptic-button';
import { HapticSettings } from './haptic-settings';
import { useHaptic } from './use-haptic';
import { MicroInteractionProvider } from '../micro-interactions/micro-interaction-provider';
import { InteractiveButton } from '../micro-interactions/interactive-button';
import { HapticPattern } from './types';
import { getHapticPatternInfo } from './haptic-utils';

function HapticDemoContent() {
  const { triggerHaptic, enabled, supported } = useHaptic();
  const [selectedPattern, setSelectedPattern] = useState<HapticPattern>('light');
  const [formData, setFormData] = useState({ name: '', email: '' });

  const patterns: HapticPattern[] = [
    'light', 'medium', 'heavy', 'success', 'warning', 'error', 
    'notification', 'selection', 'impact'
  ];

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name || !formData.email) {
      triggerHaptic('error');
      return;
    }
    triggerHaptic('success');
    setFormData({ name: '', email: '' });
  };

  const handleInputFocus = () => {
    triggerHaptic('selection');
  };

  return (
    <div className="p-8 space-y-8 max-w-6xl mx-auto ">
      <h1 className="text-3xl font-bold">Haptic Feedback Demo</h1>
      
      {/* Support Status */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Device Support</h2>
        <div className="p-4 border rounded-lg sm:p-4 md:p-6">
          <div className="flex items-center space-x-2">
            <span className={`text-2xl ${supported ? '✅' : '❌'}`}>
              {supported ? '✅' : '❌'}
            </span>
            <div>
              <p className="font-medium">
                Haptic feedback is {supported ? 'supported' : 'not supported'} on this device
              </p>
              <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                {supported 
                  ? `Feedback is currently ${enabled ? 'enabled' : 'disabled'}`
                  : 'Try this demo on a mobile device for the best experience'
                }
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Settings */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Haptic Settings</h2>
        <HapticSettings />
      </section>

      {/* Pattern Testing */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Pattern Testing</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2 md:text-base lg:text-lg">
              Select a pattern to test:
            </label>
            <select
              value={selectedPattern}
              onChange={(e) => setSelectedPattern(e.target.value as HapticPattern)}
              className="w-full max-w-xs p-2 border rounded-md sm:p-4 md:p-6"
              onFocus={handleInputFocus}
            >
              {patterns.map((pattern) => {
                const info = getHapticPatternInfo(pattern);
                return (
                  <option key={pattern} value={pattern}>
                    {info.name} - {info.description}
                  </option>
                );
              })}
            </select>
          </div>
          
          <InteractiveButton
            onClick={() => triggerHaptic(selectedPattern)}
            hapticFeedback={false} // Disable default haptic to use custom
          >
            Test {getHapticPatternInfo(selectedPattern).name} Pattern
          </InteractiveButton>
        </div>
      </section>

      {/* Interactive Examples */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Interactive Examples</h2>
        
        {/* Buttons with different haptic patterns */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium">Buttons with Haptic Feedback</h3>
          <div className="flex flex-wrap gap-4">
            <HapticButton hapticPattern="light">
            </HapticButton>
            <HapticButton hapticPattern="medium">
            </HapticButton>
            <HapticButton hapticPattern="heavy">
            </HapticButton>
            <HapticButton hapticPattern="success">
            </HapticButton>
            <HapticButton hapticPattern="warning">
            </HapticButton>
            <HapticButton hapticPattern="error">
            </HapticButton>
          </div>
        </div>

        {/* Form with haptic feedback */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium">Form with Haptic Feedback</h3>
          <form onSubmit={handleFormSubmit} className="space-y-4 max-w-md">
            <div>
              <label className="block text-sm font-medium mb-1 md:text-base lg:text-lg">Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                onFocus={handleInputFocus}
                className="w-full p-2 border rounded-md focus:ring-2 focus:ring-primary focus:border-transparent sm:p-4 md:p-6"
                placeholder="Enter your name"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1 md:text-base lg:text-lg">Email</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                onFocus={handleInputFocus}
                className="w-full p-2 border rounded-md focus:ring-2 focus:ring-primary focus:border-transparent sm:p-4 md:p-6"
                placeholder="Enter your email"
              />
            </div>
            <HapticButton 
              type="submit"
              hapticPattern="success"
            >
            </HapticButton>
            <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
              Try submitting with empty fields to feel error feedback, or with valid data for success feedback.
            </p>
          </form>
        </div>

        {/* Notification simulation */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium">Notification Simulation</h3>
          <div className="flex flex-wrap gap-4">
            <InteractiveButton
              onClick={() => triggerHaptic('notification')}
              variant="outline"
            >
              📧 New Message
            </InteractiveButton>
            <InteractiveButton
              onClick={() => triggerHaptic('warning')}
              variant="outline"
            >
              ⚠️ Warning Alert
            </InteractiveButton>
            <InteractiveButton
              onClick={() => triggerHaptic('error')}
              variant="outline"
            >
              🚨 Error Alert
            </InteractiveButton>
          </div>
        </div>
      </section>

      {/* Usage Guidelines */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Usage Guidelines</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-4 border rounded-lg sm:p-4 md:p-6">
            <h3 className="font-semibold mb-2 text-green-700">✅ Do</h3>
            <ul className="space-y-1 text-sm md:text-base lg:text-lg">
              <li>• Use light haptics for subtle interactions</li>
              <li>• Use success patterns for positive feedback</li>
              <li>• Use error patterns sparingly for critical alerts</li>
              <li>• Respect user preferences and device settings</li>
              <li>• Test on actual devices for best results</li>
            </ul>
          </div>
          
          <div className="p-4 border rounded-lg sm:p-4 md:p-6">
            <h3 className="font-semibold mb-2 text-red-700">❌ Don't</h3>
            <ul className="space-y-1 text-sm md:text-base lg:text-lg">
              <li>• Overuse haptic feedback - it can be annoying</li>
              <li>• Use heavy patterns for minor interactions</li>
              <li>• Ignore accessibility preferences</li>
              <li>• Assume all devices support haptics</li>
              <li>• Use haptics as the only form of feedback</li>
            </ul>
          </div>
        </div>
      </section>
    </div>
  );
}

export function HapticDemo() {
  return (
    <MicroInteractionProvider>
      <HapticProvider>
        <HapticDemoContent />
      </HapticProvider>
    </MicroInteractionProvider>
  );
}