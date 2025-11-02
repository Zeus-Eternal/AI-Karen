"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  listLlamaModels, 
  listTransformersModels, 
  listOpenaiModels,
  listAllAvailableModels,
  getProvidersWithModels 
} from '@/lib/providers-api';

interface ModelInfo {
  id: string;
  provider: string;
  displayName: string;
  family: string;
  installed: boolean;
}

interface ProviderInfo {
  id: string;
  title: string;
  group: string;
  available: boolean;
  modelCount: number;
}

export default function ModelAvailabilityCheck() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const checkAvailability = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Check all models
      const allModels = await listAllAvailableModels();
      setModels(allModels);
      
      // Check providers with models
      const providersWithModels = await getProvidersWithModels();
      const providerInfo = providersWithModels.map(p => ({
        id: p.id,
        title: p.title,
        group: p.group,
        available: p.available,
        modelCount: allModels.filter(m => m.provider === p.id).length
      }));
      setProviders(providerInfo);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkAvailability();
  }, []);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            Model Availability Check
            <button onClick={checkAvailability} disabled={loading} aria-label="Button">
              {loading ? 'Checking...' : 'Refresh'}
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded mb-4 sm:p-4 md:p-6">
              <p className="text-red-700">Error: {error}</p>
            </div>
          )}
          
          <div className="grid md:grid-cols-2 gap-6">
            {/* Providers */}
            <div>
              <h3 className="text-lg font-semibold mb-3">Providers</h3>
              <div className="space-y-2">
                {providers.length === 0 ? (
                  <p className="text-gray-500">No providers with models found</p>
                ) : (
                  providers.map(provider => (
                    <div key={provider.id} className="flex items-center justify-between p-3 border rounded sm:p-4 md:p-6">
                      <div>
                        <span className="font-medium">{provider.title}</span>
                        <Badge variant="outline" className="ml-2">
                          {provider.group}
                        </Badge>
                      </div>
                      <div className="text-right">
                        <Badge variant={provider.available ? "default" : "secondary"}>
                          {provider.modelCount} models
                        </Badge>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
            
            {/* Models */}
            <div>
              <h3 className="text-lg font-semibold mb-3">Available Models</h3>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {models.length === 0 ? (
                  <p className="text-gray-500">No models found</p>
                ) : (
                  models.map(model => (
                    <div key={model.id} className="p-3 border rounded sm:p-4 md:p-6">
                      <div className="font-medium">{model.displayName}</div>
                      <div className="text-sm text-gray-600 md:text-base lg:text-lg">
                        Provider: {model.provider} | Family: {model.family}
                      </div>
                      <Badge 
                        variant={model.installed ? "default" : "outline"}
                        className="mt-1"
                      >
                        {model.installed ? "Installed" : "Available"}
                      </Badge>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
      
      {/* Troubleshooting */}
      <Card>
        <CardHeader>
          <CardTitle>Troubleshooting</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <h4 className="font-semibold">If no models are showing:</h4>
              <ul className="list-disc list-inside text-sm text-gray-600 mt-2 space-y-1 md:text-base lg:text-lg">
                <li>Check that your backend server is running</li>
                <li>Verify model files exist in the models directory</li>
                <li>Check the model registry configuration</li>
                <li>Ensure provider configurations are correct</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold">For Vicuña30k model:</h4>
              <ul className="list-disc list-inside text-sm text-gray-600 mt-2 space-y-1 md:text-base lg:text-lg">
                <li>This model needs to be downloaded separately</li>
                <li>Check if you have the correct model file format</li>
                <li>Verify the model is registered in your model registry</li>
                <li>Ensure the provider supports this model family</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
