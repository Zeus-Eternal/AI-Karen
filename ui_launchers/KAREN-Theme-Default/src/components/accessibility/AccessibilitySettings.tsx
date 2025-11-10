"use client";

import * as React from 'react';

interface AccessibilitySettingsProps {
  className?: string;
}

export function AccessibilitySettings({ className }: AccessibilitySettingsProps) {
  return (
    <div className={className}>
      <p>Accessibility Settings - Temporarily disabled for build</p>
    </div>
  );
}