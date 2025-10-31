/**
 * Plugin Marketplace Component
 * 
 * Browse and discover plugins from the marketplace.
 * Based on requirements: 5.5, 9.2
 */

"use client";

import React from 'react';
import { ArrowLeft, Search, Store } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { PluginMarketplaceEntry } from '@/types/plugins';

interface PluginMarketplaceProps {
  onClose: () => void;
  onInstall: (plugin: PluginMarketplaceEntry) => void;
}

export const PluginMarketplace: React.FC<PluginMarketplaceProps> = ({
  onClose,
  onInstall,
}) => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={onClose}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Plugins
        </Button>
        <div>
          <h1 className="text-2xl font-bold">Plugin Marketplace</h1>
          <p className="text-muted-foreground">Discover and install new plugins for your Kari AI system</p>
        </div>
      </div>

      {/* Placeholder Content */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Store className="w-5 h-5" />
            Plugin Marketplace
          </CardTitle>
          <CardDescription>
            This component will be implemented in task 4.4
          </CardDescription>
        </CardHeader>
        <CardContent className="py-12 text-center">
          <Store className="w-16 h-16 mx-auto mb-4 opacity-50" />
          <h3 className="text-lg font-medium mb-2">Marketplace Browser</h3>
          <p className="text-muted-foreground mb-6">
            The marketplace will include:
          </p>
          <ul className="text-left max-w-md mx-auto space-y-2 text-sm text-muted-foreground">
            <li>• Plugin search and discovery</li>
            <li>• Ratings and reviews</li>
            <li>• Category filtering</li>
            <li>• Installation from remote sources</li>
          </ul>
          <div className="flex justify-center gap-2 mt-8">
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};