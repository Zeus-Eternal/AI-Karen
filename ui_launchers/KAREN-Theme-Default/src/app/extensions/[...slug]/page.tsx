/**
 * Dynamic Extension Pages
 *
 * Handles all extension-specific pages using dynamic routing
 */

import * as React from 'react';
import { DynamicExtensionRouter } from '@/lib/extensions/dynamic-router';
import { ExtensionPageFallback } from '@/components/extensions/ExtensionPageFallback';

interface ExtensionPageProps {
  params: {
    slug?: string[];
  };
}

export default function ExtensionPage({ params }: ExtensionPageProps) {
  const extensionPath = `/extensions/${(params.slug ?? []).join('/')}`;

  return (
    <div className="container mx-auto px-4 py-6">
      <DynamicExtensionRouter>
        <ExtensionPageFallback extensionPath={extensionPath} />
      </DynamicExtensionRouter>
    </div>
  );
}

// Import generateStaticParams for static generation
// eslint-disable-next-line react-refresh/only-export-components
export { generateStaticParams } from './generate-static-params';
