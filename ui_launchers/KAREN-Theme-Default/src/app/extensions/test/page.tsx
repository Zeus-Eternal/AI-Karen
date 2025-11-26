/**
 * Extensions Overview Page
 * 
 * Main page for extension management and dashboard
 */

"use client";

import * as React from 'react';
import ExtensionDashboard from '@/components/extensions/ExtensionDashboard';
import { DynamicExtensionRouter } from '@/lib/extensions/dynamic-router';

export default function ExtensionsPage() {
  return (
    <div className="container mx-auto px-4 py-6">
      <DynamicExtensionRouter>
        <ExtensionDashboard />
      </DynamicExtensionRouter>
    </div>
  );
}
