/**
 * Dynamic Extension Pages
 * 
 * Handles all extension-specific pages using dynamic routing
 */


import * as React from 'react';
import { DynamicExtensionRouter } from '@/lib/extensions/dynamic-router';
import { ExtensionPageFallback } from '@/components/extensions/ExtensionPageFallback';

interface ExtensionPageProps {
  params: Promise<{
    slug: string[];
  }>;
}

export default async function ExtensionPage({ params }: ExtensionPageProps) {
  const resolvedParams = await params;
  const extensionPath = `/extensions/${resolvedParams.slug.join('/')}`;

  return (
    <div className="container mx-auto px-4 py-6">
      <DynamicExtensionRouter fallback={ExtensionPageFallback}>
        <ExtensionPageFallback extensionPath={extensionPath} />
      </DynamicExtensionRouter>
    </div>
  );
}