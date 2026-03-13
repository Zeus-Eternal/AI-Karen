/**
 * Model Selector Component
 * Dropdown to select specific AI models from available providers
 * Displays model capabilities, performance metrics, and status
 */

import React, { useState, useEffect } from 'react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import {
  CheckCircle,
  Zap,
  Brain,
  MessageSquare,
  Code,
  Image as ImageIcon,
  Cpu,
  Clock,
  TrendingUp,
  Info,
  Star,
  Sparkles
} from 'lucide-react';
import { LLMModel, LLMProvider } from '@/types/chat';
import { cn } from '@/lib/utils';

interface ModelSelectorProps {
  models: LLMModel[];
  selectedModel?: string | null;
  onModelChange?: (modelId: string) => void;
  provider?: LLMProvider | null;
  showCapabilities?: boolean;
  showPerformance?: boolean;
  showRecommended?: boolean;
  className?: string;
}

interface ModelOption {
  model: LLMModel;
  isRecommended?: boolean;
  isLocal?: boolean;
  isFast?: boolean;
}

export const ModelSelector: React.FC<ModelSelectorProps> = ({
  models,
  selectedModel,
  onModelChange,
  provider,
  showCapabilities = true,
  showPerformance = true,
  showRecommended = true,
  className
}) => {
  const [isOpen, setIsOpen] = useState(false);

  // Get capability icon
  const getCapabilityIcon = (capability: string) => {
    const iconMap: Record<string, React.ReactNode> = {
      textGeneration: <MessageSquare className="h-3 w-3" />,
      streaming: <Zap className="h-3 w-3" />,
      functionCalling: <Code className="h-3 w-3" />,
      vision: <ImageIcon className="h-3 w-3" />,
      codeExecution: <Code className="h-3 w-3" />,
      embedding: <Brain className="h-3 w-3" />,
    };
    return iconMap[capability] || <Info className="h-3 w-3" />;
  };

  // Get model status color
  const getStatusColor = (model: LLMModel) => {
    if (model.status === 'available') return 'text-green-600';
    if (model.status === 'loading') return 'text-yellow-600';
    if (model.status === 'unavailable') return 'text-red-600';
    return 'text-gray-600';
  };

  // Get model status icon
  const getStatusIcon = (model: LLMModel) => {
    if (model.status === 'available') return <CheckCircle className="h-4 w-4 text-green-500" />;
    if (model.status === 'loading') return <Clock className="h-4 w-4 text-yellow-500 animate-spin" />;
    return <CheckCircle className="h-4 w-4 text-gray-400" />;
  };

  // Determine if model is recommended based on capabilities and performance
  const isModelRecommended = (model: LLMModel): boolean => {
    if (!showRecommended) return false;
    
    // Recommend models with good capabilities
    const hasGoodCapabilities = 
      model.capabilities.textGeneration &&
      (model.capabilities.streaming || model.capabilities.functionCalling);
    
    // Recommend faster models
    const isFast = model.performance?.averageResponseTime 
      ? model.performance.averageResponseTime < 2000 
      : false;
    
    // Recommend local models (faster, no API costs)
    const isLocal = model.id.toLowerCase().includes('local') || 
                   model.id.toLowerCase().includes('llamacpp') ||
                   model.id.toLowerCase().includes('transformers');

    return hasGoodCapabilities && (isFast || isLocal);
  };

  // Create model options
  const modelOptions: ModelOption[] = models.map(model => ({
    model,
    isRecommended: isModelRecommended(model),
    isLocal: model.id.toLowerCase().includes('local') || 
             model.id.toLowerCase().includes('llamacpp') ||
             model.id.toLowerCase().includes('transformers'),
    isFast: model.performance?.averageResponseTime 
      ? model.performance.averageResponseTime < 2000 
      : false,
  }));

  // Sort models: recommended first, then by name
  const sortedOptions = [...modelOptions].sort((a, b) => {
    if (a.isRecommended && !b.isRecommended) return -1;
    if (!a.isRecommended && b.isRecommended) return 1;
    return a.model.displayName.localeCompare(b.model.displayName);
  });

  const selectedModelData = models.find(m => m.id === selectedModel);

  if (models.length === 0) {
    return (
      <Card className={className}>
        <CardContent className="p-4">
          <div className="flex items-center gap-2 text-muted-foreground">
            <Info className="h-4 w-4" />
            <span className="text-sm">No models available for this provider</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <TooltipProvider>
        <Select
          value={selectedModel || ''}
          onValueChange={(value) => {
            onModelChange?.(value);
            setIsOpen(false);
          }}
          disabled={models.length === 0}
        >
          <SelectTrigger className="w-full">
            <div className="flex items-center gap-2 flex-1">
              {selectedModelData && getStatusIcon(selectedModelData)}
              <SelectValue placeholder="Select a model">
                {selectedModelData ? (
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{selectedModelData.displayName}</span>
                    {showRecommended && isModelRecommended(selectedModelData) && (
                      <Badge variant="secondary" className="text-xs">
                        <Star className="h-3 w-3 mr-1" />
                        Recommended
                      </Badge>
                    )}
                  </div>
                ) : (
                  'Select a model'
                )}
              </SelectValue>
            </div>
          </SelectTrigger>
          
          <SelectContent>
            {sortedOptions.map(({ model, isRecommended, isLocal, isFast }) => (
              <SelectItem key={model.id} value={model.id}>
                <div className="flex items-start gap-2 py-1 w-full">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium truncate">{model.displayName}</span>
                      {isRecommended && (
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Badge variant="secondary" className="text-xs">
                              <Star className="h-3 w-3 mr-1" />
                              Recommended
                            </Badge>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>This model offers a good balance of capabilities and performance</p>
                          </TooltipContent>
                        </Tooltip>
                      )}
                      {isLocal && (
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Badge variant="outline" className="text-xs">
                              <Cpu className="h-3 w-3 mr-1" />
                              Local
                            </Badge>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>Runs locally on your machine - fast and private</p>
                          </TooltipContent>
                        </Tooltip>
                      )}
                      {isFast && (
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Badge variant="outline" className="text-xs">
                              <Zap className="h-3 w-3 mr-1" />
                              Fast
                            </Badge>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>Quick response time</p>
                          </TooltipContent>
                        </Tooltip>
                      )}
                    </div>
                    
                    {showCapabilities && (
                      <div className="flex items-center gap-1 flex-wrap mb-1">
                        {model.capabilities.textGeneration && (
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Badge variant="outline" className="text-xs">
                                {getCapabilityIcon('textGeneration')}
                                <span className="ml-1">Text</span>
                              </Badge>
                            </TooltipTrigger>
                            <TooltipContent>
                              <p>Text generation</p>
                            </TooltipContent>
                          </Tooltip>
                        )}
                        {model.capabilities.streaming && (
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Badge variant="outline" className="text-xs">
                                {getCapabilityIcon('streaming')}
                                <span className="ml-1">Streaming</span>
                              </Badge>
                            </TooltipTrigger>
                            <TooltipContent>
                              <p>Real-time streaming responses</p>
                            </TooltipContent>
                          </Tooltip>
                        )}
                        {model.capabilities.functionCalling && (
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Badge variant="outline" className="text-xs">
                                {getCapabilityIcon('functionCalling')}
                                <span className="ml-1">Functions</span>
                              </Badge>
                            </TooltipTrigger>
                            <TooltipContent>
                              <p>Function calling support</p>
                            </TooltipContent>
                          </Tooltip>
                        )}
                        {model.capabilities.vision && (
                          <Tooltip>
                            <TooltipTrigger asChild>
                            <Badge variant="outline" className="text-xs">
                              {getCapabilityIcon('vision')}
                              <span className="ml-1">Vision</span>
                            </Badge>
                          </TooltipTrigger>
                            <TooltipContent>
                              <p>Image understanding</p>
                            </TooltipContent>
                          </Tooltip>
                        )}
                        {model.capabilities.codeExecution && (
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Badge variant="outline" className="text-xs">
                                {getCapabilityIcon('codeExecution')}
                                <span className="ml-1">Code</span>
                              </Badge>
                            </TooltipTrigger>
                            <TooltipContent>
                              <p>Code execution</p>
                            </TooltipContent>
                          </Tooltip>
                        )}
                      </div>
                    )}
                    
                    {showPerformance && model.performance && (
                      <div className="flex items-center gap-3 text-xs text-muted-foreground">
                        {model.performance.averageResponseTime && (
                          <div className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            <span>{model.performance.averageResponseTime}ms</span>
                          </div>
                        )}
                        {model.performance.successRate !== undefined && (
                          <div className="flex items-center gap-1">
                            <TrendingUp className="h-3 w-3" />
                            <span>{(model.performance.successRate * 100).toFixed(0)}% success</span>
                          </div>
                        )}
                      </div>
                    )}
                    
                    {model.description && (
                      <p className="text-xs text-muted-foreground truncate mt-1">
                        {model.description}
                      </p>
                    )}
                  </div>
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </TooltipProvider>

      {/* Model info tooltip */}
      {selectedModelData && (
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                <Info className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="right" className="max-w-sm">
              <div className="space-y-2">
                <div>
                  <h4 className="font-medium">{selectedModelData.displayName}</h4>
                  <p className="text-sm text-muted-foreground">{selectedModelData.id}</p>
                </div>
                {selectedModelData.description && (
                  <p className="text-sm">{selectedModelData.description}</p>
                )}
                {selectedModelData.performance && (
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    {selectedModelData.performance.averageResponseTime && (
                      <div>
                        <span className="font-medium">Response Time:</span>{' '}
                        {selectedModelData.performance.averageResponseTime}ms
                      </div>
                    )}
                    {selectedModelData.performance.successRate !== undefined && (
                      <div>
                        <span className="font-medium">Success Rate:</span>{' '}
                        {(selectedModelData.performance.successRate * 100).toFixed(1)}%
                      </div>
                    )}
                  </div>
                )}
              </div>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )}
    </div>
  );
};

export default ModelSelector;
