/**
 * Chat Mode Selector Component
 * 
 * Extends existing model switching functionality with context preservation
 * and confirmation dialogs for seamless mode transitions.
 */

import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogFooter, 
  DialogHeader, 
  DialogTitle 
} from '@/components/ui/dialog';
import { Separator } from '@/components/ui/separator';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { 
  MessageSquare, 
  Image, 
  Zap, 
  ArrowRight, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  Shuffle,
  Settings,
  Info
} from 'lucide-react';
import { useModelSelection } from '@/hooks/useModelSelection';
import { Model } from '@/lib/model-utils';
import { useToast } from '@/hooks/use-toast';

export type ChatMode = 'text' | 'image' | 'multimodal';

export interface ChatContext {
  messages: Array<{
    id: string;
    content: string;
    type: 'user' | 'assistant';
    mode: ChatMode;
    modelUsed?: string;
    timestamp: Date;
  }>;
  currentTopic?: string;
  conversationLength: number;
}

interface ChatModeSelectorProps {
  selectedModel?: Model | null;
  currentMode: ChatMode;
  chatContext?: ChatContext;
  onModeChange: (mode: ChatMode, model: Model | null) => void;
  onModelChange: (model: Model | null) => void;
  onContextPreservationChange?: (preserve: boolean) => void;
  className?: string;
  disabled?: boolean;
}

interface ModeTransition {
  fromMode: ChatMode;
  toMode: ChatMode;
  fromModel: Model | null;
  toModel: Model | null;
  requiresConfirmation: boolean;
  contextPreservable: boolean;
  warnings: string[];
}

export default function ChatModeSelector({
  selectedModel,
  currentMode,
  chatContext,
  onModeChange,
  onModelChange,
  onContextPreservationChange,
  className = '',
  disabled = false
}: ChatModeSelectorProps) {
  const { toast } = useToast();
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [pendingTransition, setPendingTransition] = useState<ModeTransition | null>(null);
  const [preserveContext, setPreserveContext] = useState(true);
  const [isTransitioning, setIsTransitioning] = useState(false);

  const {
    models,
    selectedModel: hookSelectedModel,
    selectedModelInfo,
    setSelectedModel,
    loading: modelsLoading,
    error: modelsError
  } = useModelSelection({
    autoSelect: false,
    preferLocal: true,
    onModelSelected: (model, reason) => {
      if (model && !isTransitioning) {
        onModelChange(model);
      }
    }
  });

  // Use provided selectedModel or fall back to hook's selectedModel
  const currentModel = selectedModel || selectedModelInfo;

  // Categorize models by their capabilities
  const categorizedModels = useMemo(() => {
    const textModels = models.filter(model => 
      model.type === 'text' || 
      model.type === 'multimodal' ||
      model.capabilities?.includes('text-generation') ||
      model.capabilities?.includes('chat')
    );

    const imageModels = models.filter(model => 
      model.type === 'image' || 
      model.type === 'multimodal' ||
      model.capabilities?.includes('image-generation')
    );

    const multimodalModels = models.filter(model => 
      model.type === 'multimodal' ||
      (model.capabilities?.includes('text-generation') && model.capabilities?.includes('image-generation'))
    );

    return {
      text: textModels,
      image: imageModels,
      multimodal: multimodalModels,
      all: models
    };
  }, [models]);

  // Get available modes based on available models
  const availableModes = useMemo((): ChatMode[] => {
    const modes: ChatMode[] = [];
    
    if (categorizedModels.text.length > 0) modes.push('text');
    if (categorizedModels.image.length > 0) modes.push('image');
    if (categorizedModels.multimodal.length > 0) modes.push('multimodal');
    
    return modes.length > 0 ? modes : ['text'];
  }, [categorizedModels]);

  // Get models for a specific mode
  const getModelsForMode = (mode: ChatMode): Model[] => {
    switch (mode) {
      case 'text':
        return categorizedModels.text;
      case 'image':
        return categorizedModels.image;
      case 'multimodal':
        return categorizedModels.multimodal;
      default:
        return [];
    }
  };

  // Get the best model for a mode
  const getBestModelForMode = (mode: ChatMode): Model | null => {
    const modelsForMode = getModelsForMode(mode);
    if (modelsForMode.length === 0) return null;

    // Prefer currently selected model if it supports the mode
    if (currentModel && modelsForMode.some(m => m.id === currentModel.id)) {
      return currentModel;
    }

    // Otherwise, return the first available model (could be enhanced with better selection logic)
    return modelsForMode[0];
  };

  // Get mode information
  const getModeInfo = (mode: ChatMode) => {
    switch (mode) {
      case 'text':
        return {
          icon: <MessageSquare className="w-4 h-4" />,
          label: 'Text Generation',
          description: 'Generate text responses and have conversations',
          color: 'bg-blue-100 text-blue-800',
          modelCount: categorizedModels.text.length
        };
      case 'image':
        return {
          icon: <Image className="w-4 h-4" />,
          label: 'Image Generation',
          description: 'Generate images from text descriptions',
          color: 'bg-purple-100 text-purple-800',
          modelCount: categorizedModels.image.length
        };
      case 'multimodal':
        return {
          icon: <Zap className="w-4 h-4" />,
          label: 'Multi-modal',
          description: 'Generate both text and images',
          color: 'bg-orange-100 text-orange-800',
          modelCount: categorizedModels.multimodal.length
        };
    }
  };

  // Analyze transition requirements
  const analyzeTransition = (
    fromMode: ChatMode,
    toMode: ChatMode,
    fromModel: Model | null,
    toModel: Model | null
  ): ModeTransition => {
    const warnings: string[] = [];
    let requiresConfirmation = false;
    let contextPreservable = true;

    // Check if we have an active conversation
    const hasActiveConversation = chatContext && chatContext.conversationLength > 0;

    // Mode change warnings
    if (fromMode !== toMode && hasActiveConversation) {
      warnings.push(`Switching from ${fromMode} to ${toMode} mode`);
      requiresConfirmation = true;
    }

    // Model change warnings
    if (fromModel && toModel && fromModel.id !== toModel.id && hasActiveConversation) {
      warnings.push(`Changing model from ${fromModel.name} to ${toModel.name}`);
      requiresConfirmation = true;
    }

    // Context preservation analysis
    if (fromMode === 'image' && toMode === 'text') {
      warnings.push('Image generation history may not be fully preserved in text mode');
      contextPreservable = true; // Can preserve text parts
    } else if (fromMode === 'text' && toMode === 'image') {
      warnings.push('Text conversation will be preserved but not directly usable for image generation');
      contextPreservable = true;
    } else if (fromMode !== toMode && toMode === 'multimodal') {
      // Multimodal can usually preserve context from both modes
      contextPreservable = true;
    }

    // Model compatibility warnings
    if (fromModel && toModel) {
      if (fromModel.type !== toModel.type) {
        warnings.push('Different model types may have different capabilities and response styles');
      }
      
      if (fromModel.subtype !== toModel.subtype) {
        warnings.push('Different model architectures may produce different results');
      }
    }

    // No model available warning
    if (!toModel) {
      warnings.push(`No models available for ${toMode} mode`);
      requiresConfirmation = true;
      contextPreservable = false;
    }

    return {
      fromMode,
      toMode,
      fromModel,
      toModel,
      requiresConfirmation,
      contextPreservable,
      warnings
    };
  };

  // Handle mode change
  const handleModeChange = (newMode: ChatMode) => {
    if (newMode === currentMode) return;

    const bestModel = getBestModelForMode(newMode);
    const transition = analyzeTransition(currentMode, newMode, currentModel, bestModel);

    if (transition.requiresConfirmation) {
      setPendingTransition(transition);
      setShowConfirmDialog(true);
    } else {
      executeTransition(transition);
    }
  };

  // Handle model change within current mode
  const handleModelChange = (modelId: string) => {
    const newModel = models.find(m => m.id === modelId) || null;
    if (!newModel || newModel.id === currentModel?.id) return;

    const transition = analyzeTransition(currentMode, currentMode, currentModel, newModel);

    if (transition.requiresConfirmation) {
      setPendingTransition(transition);
      setShowConfirmDialog(true);
    } else {
      executeTransition(transition);
    }
  };

  // Execute the transition
  const executeTransition = async (transition: ModeTransition) => {
    setIsTransitioning(true);
    
    try {
      // Update model selection if needed
      if (transition.toModel && transition.toModel.id !== currentModel?.id) {
        await setSelectedModel(transition.toModel.id);
      }

      // Notify parent components
      onModeChange(transition.toMode, transition.toModel);
      onModelChange(transition.toModel);
      onContextPreservationChange?.(preserveContext && transition.contextPreservable);

      toast({
        title: 'Mode Changed Successfully',
        description: `Switched to ${transition.toMode} mode${transition.toModel ? ` with ${transition.toModel.name}` : ''}`,
      });

    } catch (error) {
      console.error('Transition failed:', error);
      toast({
        title: 'Mode Change Failed',
        description: error instanceof Error ? error.message : 'Unknown error occurred',
        variant: 'destructive'
      });
    } finally {
      setIsTransitioning(false);
      setShowConfirmDialog(false);
      setPendingTransition(null);
    }
  };

  // Handle confirmation dialog
  const handleConfirmTransition = () => {
    if (pendingTransition) {
      executeTransition(pendingTransition);
    }
  };

  const handleCancelTransition = () => {
    setShowConfirmDialog(false);
    setPendingTransition(null);
  };

  // Quick switch to optimal model for current mode
  const handleQuickSwitch = () => {
    const bestModel = getBestModelForMode(currentMode);
    if (bestModel && bestModel.id !== currentModel?.id) {
      handleModelChange(bestModel.id);
    }
  };

  const currentModeInfo = getModeInfo(currentMode);
  const modelsForCurrentMode = getModelsForMode(currentMode);

  return (
    <TooltipProvider>
      <Card className={className}>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Settings className="w-5 h-5" />
                Chat Mode & Model Selection
              </CardTitle>
              <CardDescription>
                Switch between different chat modes and models
              </CardDescription>
            </div>
            
            {/* Current Mode Indicator */}
            <Badge variant="outline" className={currentModeInfo.color}>
              <span className="flex items-center gap-1">
                {currentModeInfo.icon}
                {currentModeInfo.label}
              </span>
            </Badge>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Mode Selection */}
          <div>
            <label className="text-sm font-medium mb-2 block">Chat Mode</label>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
              {availableModes.map((mode) => {
                const modeInfo = getModeInfo(mode);
                const isActive = mode === currentMode;
                const isDisabled = disabled || isTransitioning || modeInfo.modelCount === 0;
                
                return (
                  <Tooltip key={mode}>
                    <TooltipTrigger asChild>
                      <Button
                        variant={isActive ? "default" : "outline"}
                        onClick={() => handleModeChange(mode)}
                        disabled={isDisabled}
                        className="flex flex-col items-center gap-2 h-auto p-4"
                      >
                        <div className="flex items-center gap-2">
                          {modeInfo.icon}
                          <span className="font-medium">{modeInfo.label}</span>
                        </div>
                        <div className="text-xs text-center opacity-75">
                          {modeInfo.modelCount} model{modeInfo.modelCount !== 1 ? 's' : ''}
                        </div>
                        {isActive && (
                          <CheckCircle className="w-4 h-4 text-green-600" />
                        )}
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>{modeInfo.description}</p>
                      {modeInfo.modelCount === 0 && (
                        <p className="text-red-400 mt-1">No models available</p>
                      )}
                    </TooltipContent>
                  </Tooltip>
                );
              })}
            </div>
          </div>

          <Separator />

          {/* Model Selection for Current Mode */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">
                Model for {currentModeInfo.label}
              </label>
              
              {modelsForCurrentMode.length > 1 && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleQuickSwitch}
                      disabled={disabled || isTransitioning}
                    >
                      <Shuffle className="w-4 h-4 mr-1" />
                      Quick Switch
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Switch to optimal model for current mode</p>
                  </TooltipContent>
                </Tooltip>
              )}
            </div>

            {modelsForCurrentMode.length > 0 ? (
              <Select 
                value={currentModel?.id || ''} 
                onValueChange={handleModelChange}
                disabled={disabled || isTransitioning || modelsLoading}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a model" />
                </SelectTrigger>
                <SelectContent>
                  {modelsForCurrentMode.map((model) => (
                    <SelectItem key={model.id} value={model.id}>
                      <div className="flex items-center justify-between w-full">
                        <div className="flex items-center gap-2">
                          <span>{model.name}</span>
                          {model.id === currentModel?.id && (
                            <CheckCircle className="w-4 h-4 text-green-600" />
                          )}
                        </div>
                        <div className="flex items-center gap-1">
                          {model.capabilities?.slice(0, 2).map((cap) => (
                            <Badge key={cap} variant="secondary" className="text-xs">
                              {cap}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            ) : (
              <div className="text-center p-4 border border-dashed rounded-lg">
                <AlertTriangle className="w-6 h-6 text-yellow-500 mx-auto mb-2" />
                <p className="text-sm text-gray-600">
                  No models available for {currentModeInfo.label.toLowerCase()} mode
                </p>
              </div>
            )}
          </div>

          {/* Context Information */}
          {chatContext && chatContext.conversationLength > 0 && (
            <div className="bg-blue-50 p-3 rounded-lg">
              <div className="flex items-start gap-2">
                <Clock className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
                <div className="text-sm">
                  <p className="font-medium text-blue-900">Active Conversation</p>
                  <p className="text-blue-700">
                    {chatContext.conversationLength} message{chatContext.conversationLength !== 1 ? 's' : ''} in current conversation
                    {chatContext.currentTopic && ` about ${chatContext.currentTopic}`}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Loading/Error States */}
          {modelsLoading && (
            <div className="text-center text-gray-500 py-2">
              <div className="inline-flex items-center gap-2">
                <div className="w-4 h-4 border-2 border-gray-300 border-t-gray-600 rounded-full animate-spin" />
                Loading models...
              </div>
            </div>
          )}

          {modelsError && (
            <div className="text-center text-red-600 py-2">
              <AlertTriangle className="w-4 h-4 mx-auto mb-1" />
              <p className="text-sm">Error loading models: {modelsError}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Confirmation Dialog */}
      <Dialog open={showConfirmDialog} onOpenChange={setShowConfirmDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-yellow-500" />
              Confirm Mode Change
            </DialogTitle>
            <DialogDescription>
              This action will change your chat configuration. Please review the changes below.
            </DialogDescription>
          </DialogHeader>

          {pendingTransition && (
            <div className="space-y-4">
              {/* Transition Summary */}
              <div className="flex items-center justify-center gap-2 p-3 bg-gray-50 rounded-lg">
                <div className="text-center">
                  <Badge variant="outline" className={getModeInfo(pendingTransition.fromMode).color}>
                    {getModeInfo(pendingTransition.fromMode).label}
                  </Badge>
                  {pendingTransition.fromModel && (
                    <p className="text-xs text-gray-600 mt-1">
                      {pendingTransition.fromModel.name}
                    </p>
                  )}
                </div>
                
                <ArrowRight className="w-4 h-4 text-gray-400" />
                
                <div className="text-center">
                  <Badge variant="outline" className={getModeInfo(pendingTransition.toMode).color}>
                    {getModeInfo(pendingTransition.toMode).label}
                  </Badge>
                  {pendingTransition.toModel && (
                    <p className="text-xs text-gray-600 mt-1">
                      {pendingTransition.toModel.name}
                    </p>
                  )}
                </div>
              </div>

              {/* Warnings */}
              {pendingTransition.warnings.length > 0 && (
                <div className="space-y-2">
                  <p className="text-sm font-medium">Changes:</p>
                  <ul className="space-y-1">
                    {pendingTransition.warnings.map((warning, index) => (
                      <li key={index} className="flex items-start gap-2 text-sm text-gray-600">
                        <Info className="w-3 h-3 mt-0.5 flex-shrink-0" />
                        {warning}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Context Preservation Option */}
              {pendingTransition.contextPreservable && chatContext && chatContext.conversationLength > 0 && (
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="preserveContext"
                      checked={preserveContext}
                      onChange={(e) => setPreserveContext(e.target.checked)}
                      className="rounded"
                    />
                    <label htmlFor="preserveContext" className="text-sm font-medium">
                      Preserve conversation context
                    </label>
                  </div>
                  <p className="text-xs text-gray-600 ml-6">
                    Keep the current conversation history when switching modes/models
                  </p>
                </div>
              )}
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={handleCancelTransition}>
              Cancel
            </Button>
            <Button onClick={handleConfirmTransition} disabled={isTransitioning}>
              {isTransitioning ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                  Switching...
                </>
              ) : (
                'Confirm Change'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </TooltipProvider>
  );
}