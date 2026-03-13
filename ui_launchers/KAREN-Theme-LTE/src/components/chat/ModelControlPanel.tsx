/**
 * Model Control Panel Component
 * Combined provider and model selection with status indicators
 * Displays current selection and allows switching between providers/models
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { ProviderSelector } from './ProviderSelector';
import { ModelSelector } from './ModelSelector';
import { useEnhancedChatStore } from '@/stores/enhancedChatStore';
import {
  Settings,
  ChevronDown,
  ChevronUp,
  Cpu,
  Zap,
  CheckCircle,
  Info,
  RefreshCw
} from 'lucide-react';
import { LLMProvider, LLMModel } from '@/types/chat';
import { cn } from '@/lib/utils';

interface ModelControlPanelProps {
  className?: string;
  defaultExpanded?: boolean;
}

export const ModelControlPanel: React.FC<ModelControlPanelProps> = ({
  className,
  defaultExpanded = false
}) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  
  // Get state from chat store
  const {
    availableProviders,
    selectedProvider,
    selectedModel,
    providerModels,
    providerStatus,
    loadProviders,
    selectProvider,
    selectModel,
    connectionStatus
  } = useEnhancedChatStore();

  // Get current provider data
  const currentProvider = availableProviders.find(p => p.id === selectedProvider);
  
  // Get current model data
  const currentModel = providerModels.find(m => m.id === selectedModel);

  // Load providers on mount
  useEffect(() => {
    if (availableProviders.length === 0) {
      loadProviders();
    }
  }, []);

  // Handle provider change
  const handleProviderChange = async (provider: LLMProvider) => {
    await selectProvider(provider.id);
    // Clear selected model when provider changes
    selectModel('');
  };

  // Handle model change
  const handleModelChange = (modelId: string) => {
    selectModel(modelId);
  };

  // Get provider status
  const getProviderStatus = () => {
    if (!currentProvider) return 'unknown';
    return providerStatus[currentProvider.id] || 'unknown';
  };

  const providerStatusValue = getProviderStatus();

  // Count total available models
  const totalModels = availableProviders.reduce(
    (total, provider) => total + (provider.models?.length || 0),
    0
  );

  return (
    <Card className={className}>
      <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
        <CardHeader className="py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Cpu className="h-5 w-5 text-primary" />
              <CardTitle className="text-lg">AI Model Selection</CardTitle>
              {connectionStatus?.isConnected && (
                <Badge variant="outline" className="text-xs">
                  <CheckCircle className="h-3 w-3 mr-1 text-green-500" />
                  Connected
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => loadProviders()}
                className="h-8 w-8 p-0"
              >
                <RefreshCw className="h-4 w-4" />
              </Button>
              <CollapsibleTrigger asChild>
                <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                  {isExpanded ? (
                    <ChevronUp className="h-4 w-4" />
                  ) : (
                    <ChevronDown className="h-4 w-4" />
                  )}
                </Button>
              </CollapsibleTrigger>
            </div>
          </div>
        </CardHeader>

        <CollapsibleContent>
          <CardContent className="space-y-4 pt-0">
            {/* Current Selection Summary */}
            {(currentProvider || currentModel) && (
              <>
                <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium">Current Selection:</span>
                      {providerStatusValue === 'active' && (
                        <CheckCircle className="h-3 w-3 text-green-500" />
                      )}
                    </div>
                    <div className="space-y-1">
                      {currentProvider && (
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="text-xs">
                            Provider
                          </Badge>
                          <span className="text-sm truncate">{currentProvider.displayName}</span>
                        </div>
                      )}
                      {currentModel && (
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="text-xs">
                            Model
                          </Badge>
                          <span className="text-sm truncate">{currentModel.displayName}</span>
                          {currentModel.performance?.averageResponseTime && (
                            <span className="text-xs text-muted-foreground">
                              ({currentModel.performance.averageResponseTime}ms)
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
                <Separator />
              </>
            )}

            {/* Provider Selection */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium">
                  Provider
                </label>
                <span className="text-xs text-muted-foreground">
                  {availableProviders.length} available
                </span>
              </div>
              <ProviderSelector
                currentProvider={currentProvider || null}
                onProviderChange={handleProviderChange}
                showStatus={true}
                showSettings={false}
              />
            </div>

            {/* Model Selection */}
            {currentProvider && providerModels.length > 0 && (
              <>
                <Separator />
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <label className="text-sm font-medium">
                      Model
                    </label>
                    <span className="text-xs text-muted-foreground">
                      {providerModels.length} available
                    </span>
                  </div>
                  <ModelSelector
                    models={providerModels}
                    selectedModel={selectedModel}
                    onModelChange={handleModelChange}
                    provider={currentProvider}
                    showCapabilities={true}
                    showPerformance={true}
                    showRecommended={true}
                  />
                </div>
              </>
            )}

            {/* Info Section */}
            {totalModels > 0 && (
              <>
                <Separator />
                <div className="p-3 bg-muted/30 rounded-lg">
                  <div className="flex items-start gap-2">
                    <Info className="h-4 w-4 text-muted-foreground mt-0.5" />
                    <div className="flex-1 text-sm text-muted-foreground space-y-1">
                      <p>
                        <span className="font-medium">Total Available:</span> {availableProviders.length} providers, {totalModels} models
                      </p>
                      {currentProvider?.models && currentProvider.models.length > 0 && (
                        <p>
                          <span className="font-medium">Current Provider:</span> {currentProvider.models.length} models available
                        </p>
                      )}
                      <p className="text-xs">
                        Select a provider first, then choose a specific model. Local models (marked with <Cpu className="h-3 w-3 inline mx-0.5" />) run on your machine for faster responses.
                      </p>
                    </div>
                  </div>
                </div>
              </>
            )}

            {/* No providers available */}
            {availableProviders.length === 0 && (
              <div className="p-4 text-center text-muted-foreground">
                <p className="text-sm">No AI providers configured.</p>
                <p className="text-xs mt-1">Add providers in the settings to get started.</p>
              </div>
            )}
          </CardContent>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
};

export default ModelControlPanel;
