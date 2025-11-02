/**
 * Image Generation Controls Component
 * 
 * Provides controls for image generation parameters with model-specific validation
 * and preset configurations.
 */

import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Textarea } from '@/components/ui/textarea';
import { Separator } from '@/components/ui/separator';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { 
  Image, 
  Settings, 
  Shuffle, 
  RotateCcw, 
  Save, 
  ChevronDown, 
  ChevronRight, 
  Info,
  Palette,
  Zap,
  Target
} from 'lucide-react';
import { Model } from '@/lib/model-utils';
import { useToast } from '@/hooks/use-toast';

export interface ImageGenerationParams {
  prompt: string;
  negativePrompt?: string;
  width: number;
  height: number;
  steps: number;
  guidanceScale: number;
  seed?: number;
  batchSize: number;
  sampler?: string;
  scheduler?: string;
  // Model-specific parameters
  strength?: number; // For img2img
  denoisingStrength?: number; // For Flux
  aspectRatio?: string;
}

interface ImageGenerationControlsProps {
  model?: Model | null;
  params: ImageGenerationParams;
  onParamsChange: (params: ImageGenerationParams) => void;
  onGenerate?: (params: ImageGenerationParams) => void;
  isGenerating?: boolean;
  className?: string;
}

interface PresetConfig {
  name: string;
  description: string;
  params: Partial<ImageGenerationParams>;
  icon: React.ReactNode;
  category: 'quality' | 'speed' | 'style' | 'size';
}

const DEFAULT_PARAMS: ImageGenerationParams = {
  prompt: '',
  negativePrompt: '',
  width: 512,
  height: 512,
  steps: 20,
  guidanceScale: 7.5,
  batchSize: 1,
  sampler: 'euler_a',
  scheduler: 'normal'
};

// Preset configurations for different use cases
const PRESET_CONFIGS: PresetConfig[] = [
  {
    name: 'High Quality',
    description: 'Best quality with more steps',
    params: { steps: 50, guidanceScale: 8.0, width: 768, height: 768 },
    icon: <Target className="w-4 h-4 sm:w-auto md:w-full" />,
    category: 'quality'
  },
  {
    name: 'Fast Generation',
    description: 'Quick results with fewer steps',
    params: { steps: 10, guidanceScale: 6.0, width: 512, height: 512 },
    icon: <Zap className="w-4 h-4 sm:w-auto md:w-full" />,
    category: 'speed'
  },
  {
    name: 'Portrait',
    description: 'Optimized for portrait images',
    params: { width: 512, height: 768, guidanceScale: 7.0, steps: 25 },
    icon: <Image className="w-4 h-4 sm:w-auto md:w-full" />,
    category: 'size'
  },
  {
    name: 'Landscape',
    description: 'Optimized for landscape images',
    params: { width: 768, height: 512, guidanceScale: 7.0, steps: 25 },
    icon: <Image className="w-4 h-4 sm:w-auto md:w-full" />,
    category: 'size'
  },
  {
    name: 'Artistic',
    description: 'Creative and artistic style',
    params: { guidanceScale: 9.0, steps: 30, negativePrompt: 'blurry, low quality' },
    icon: <Palette className="w-4 h-4 sm:w-auto md:w-full" />,
    category: 'style'
  }
];

// Common aspect ratios
const ASPECT_RATIOS = [
  { label: '1:1 (Square)', value: '1:1', width: 512, height: 512 },
  { label: '4:3 (Standard)', value: '4:3', width: 512, height: 384 },
  { label: '3:4 (Portrait)', value: '3:4', width: 384, height: 512 },
  { label: '16:9 (Widescreen)', value: '16:9', width: 768, height: 432 },
  { label: '9:16 (Vertical)', value: '9:16', width: 432, height: 768 },
  { label: '3:2 (Photo)', value: '3:2', width: 768, height: 512 },
  { label: '2:3 (Photo Portrait)', value: '2:3', width: 512, height: 768 }
];

export default function ImageGenerationControls({
  model,
  params,
  onParamsChange,
  onGenerate,
  isGenerating = false,
  className = ''
}: ImageGenerationControlsProps) {
  const { toast } = useToast();
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState<string>('');

  // Get model-specific constraints and capabilities
  const modelConstraints = useMemo(() => {
    if (!model || !model.metadata) {
      return {
        maxWidth: 1024,
        maxHeight: 1024,
        minWidth: 256,
        minHeight: 256,
        maxSteps: 100,
        minSteps: 1,
        supportedSamplers: ['euler_a', 'ddim', 'dpm++'],
        supportsNegativePrompt: true,
        supportsImg2Img: false,
        defaultGuidanceRange: [1, 20]
      };
    }

    // Extract constraints based on model type and metadata
    const isFlux = model.subtype === 'flux';
    const isSD = model.subtype === 'stable-diffusion';
    
    return {
      maxWidth: isFlux ? 1024 : 768,
      maxHeight: isFlux ? 1024 : 768,
      minWidth: 256,
      minHeight: 256,
      maxSteps: isFlux ? 50 : 100,
      minSteps: isFlux ? 1 : 10,
      supportedSamplers: isFlux 
        ? ['euler', 'euler_a'] 
        : ['euler_a', 'ddim', 'dpm++', 'k_lms'],
      supportsNegativePrompt: !isFlux, // Flux typically doesn't use negative prompts
      supportsImg2Img: model.capabilities?.includes('img2img') || false,
      defaultGuidanceRange: isFlux ? [1, 10] : [1, 20]
    };
  }, [model]);

  // Validate and constrain parameters based on model
  const validateParams = (newParams: ImageGenerationParams): ImageGenerationParams => {
    return {
      ...newParams,
      width: Math.max(modelConstraints.minWidth, Math.min(modelConstraints.maxWidth, newParams.width)),
      height: Math.max(modelConstraints.minHeight, Math.min(modelConstraints.maxHeight, newParams.height)),
      steps: Math.max(modelConstraints.minSteps, Math.min(modelConstraints.maxSteps, newParams.steps)),
      guidanceScale: Math.max(
        modelConstraints.defaultGuidanceRange[0], 
        Math.min(modelConstraints.defaultGuidanceRange[1], newParams.guidanceScale)
      ),
      batchSize: Math.max(1, Math.min(4, newParams.batchSize))
    };
  };

  // Handle parameter changes with validation
  const handleParamChange = (key: keyof ImageGenerationParams, value: any) => {
    const newParams = { ...params, [key]: value };
    const validatedParams = validateParams(newParams);
    onParamsChange(validatedParams);
  };

  // Apply preset configuration
  const applyPreset = (preset: PresetConfig) => {
    const newParams = { ...params, ...preset.params };
    const validatedParams = validateParams(newParams);
    onParamsChange(validatedParams);
    setSelectedPreset(preset.name);
    
    toast({
      title: 'Preset Applied',
      description: `Applied ${preset.name} preset configuration`,
    });
  };

  // Apply aspect ratio
  const applyAspectRatio = (ratio: typeof ASPECT_RATIOS[0]) => {
    handleParamChange('width', ratio.width);
    handleParamChange('height', ratio.height);
    
    toast({
      title: 'Aspect Ratio Applied',
      description: `Set dimensions to ${ratio.width}x${ratio.height} (${ratio.label})`,
    });
  };

  // Generate random seed
  const generateRandomSeed = () => {
    const randomSeed = Math.floor(Math.random() * 1000000);
    handleParamChange('seed', randomSeed);
    
    toast({
      title: 'Random Seed Generated',
      description: `New seed: ${randomSeed}`,
    });
  };

  // Reset to defaults
  const resetToDefaults = () => {
    const validatedDefaults = validateParams(DEFAULT_PARAMS);
    onParamsChange(validatedDefaults);
    setSelectedPreset('');
    
    toast({
      title: 'Reset to Defaults',
      description: 'All parameters reset to default values',
    });
  };

  // Handle generation
  const handleGenerate = () => {
    if (!params.prompt.trim()) {
      toast({
        title: 'Missing Prompt',
        description: 'Please enter a prompt to generate an image',
        variant: 'destructive'
      });
      return;
    }

    onGenerate?.(params);
  };

  return (
    <TooltipProvider>
      <Card className={className}>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Image className="w-5 h-5 sm:w-auto md:w-full" />
                Image Generation Controls
              </CardTitle>
              <CardDescription>
                Configure parameters for {model?.name || 'image generation'}
              </CardDescription>
            </div>
            
            {model && (
              <Badge variant="outline" className="bg-purple-100 text-purple-800">
                {model.subtype || model.type}
              </Badge>
            )}
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Preset Configurations */}
          <div>
            <Label className="text-sm font-medium mb-3 block md:text-base lg:text-lg">Quick Presets</Label>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2">
              {PRESET_CONFIGS.map((preset) => (
                <Tooltip key={preset.name}>
                  <TooltipTrigger asChild>
                    <button
                      variant={selectedPreset === preset.name ? "default" : "outline"}
                      size="sm"
                      onClick={() = aria-label="Button"> applyPreset(preset)}
                      className="flex items-center gap-1 text-xs sm:text-sm md:text-base"
                    >
                      {preset.icon}
                      {preset.name}
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>{preset.description}</p>
                  </TooltipContent>
                </Tooltip>
              ))}
            </div>
          </div>

          <Separator />

          {/* Main Prompt */}
          <div className="space-y-2">
            <Label htmlFor="prompt" className="flex items-center gap-2">
              Prompt
              <Tooltip>
                <TooltipTrigger>
                  <Info className="w-4 h-4 text-gray-400 sm:w-auto md:w-full" />
                </TooltipTrigger>
                <TooltipContent>
                  <p>Describe what you want to generate. Be specific and detailed.</p>
                </TooltipContent>
              </Tooltip>
            </Label>
            <textarea
              id="prompt"
              value={params.prompt}
              onChange={(e) = aria-label="Textarea"> handleParamChange('prompt', e.target.value)}
              placeholder="A beautiful landscape with mountains and a lake at sunset..."
              className="min-h-[80px] resize-none"
            />
          </div>

          {/* Negative Prompt (if supported) */}
          {modelConstraints.supportsNegativePrompt && (
            <div className="space-y-2">
              <Label htmlFor="negativePrompt" className="flex items-center gap-2">
                Negative Prompt
                <Tooltip>
                  <TooltipTrigger>
                    <Info className="w-4 h-4 text-gray-400 sm:w-auto md:w-full" />
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Describe what you don't want in the image</p>
                  </TooltipContent>
                </Tooltip>
              </Label>
              <textarea
                id="negativePrompt"
                value={params.negativePrompt || ''}
                onChange={(e) = aria-label="Textarea"> handleParamChange('negativePrompt', e.target.value)}
                placeholder="blurry, low quality, distorted..."
                className="min-h-[60px] resize-none"
              />
            </div>
          )}

          {/* Dimensions and Aspect Ratio */}
          <div className="space-y-4">
            <Label className="text-sm font-medium md:text-base lg:text-lg">Dimensions</Label>
            
            {/* Aspect Ratio Presets */}
            <div>
              <Label className="text-xs text-gray-600 mb-2 block sm:text-sm md:text-base">Aspect Ratios</Label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                {ASPECT_RATIOS.map((ratio) => (
                  <button
                    key={ratio.value}
                    variant="outline"
                    size="sm"
                    onClick={() = aria-label="Button"> applyAspectRatio(ratio)}
                    className="text-xs sm:text-sm md:text-base"
                  >
                    {ratio.label}
                  </Button>
                ))}
              </div>
            </div>

            {/* Custom Dimensions */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="width" className="text-xs sm:text-sm md:text-base">Width</Label>
                <input
                  id="width"
                  type="number"
                  value={params.width}
                  onChange={(e) = aria-label="Input"> handleParamChange('width', parseInt(e.target.value) || 512)}
                  min={modelConstraints.minWidth}
                  max={modelConstraints.maxWidth}
                  step={64}
                />
              </div>
              <div>
                <Label htmlFor="height" className="text-xs sm:text-sm md:text-base">Height</Label>
                <input
                  id="height"
                  type="number"
                  value={params.height}
                  onChange={(e) = aria-label="Input"> handleParamChange('height', parseInt(e.target.value) || 512)}
                  min={modelConstraints.minHeight}
                  max={modelConstraints.maxHeight}
                  step={64}
                />
              </div>
            </div>
          </div>

          {/* Basic Parameters */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Steps */}
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                Steps: {params.steps}
                <Tooltip>
                  <TooltipTrigger>
                    <Info className="w-4 h-4 text-gray-400 sm:w-auto md:w-full" />
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>More steps = higher quality but slower generation</p>
                  </TooltipContent>
                </Tooltip>
              </Label>
              <Slider
                value={[params.steps]}
                onValueChange={([value]) => handleParamChange('steps', value)}
                min={modelConstraints.minSteps}
                max={modelConstraints.maxSteps}
                step={1}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500 sm:text-sm md:text-base">
                <span>{modelConstraints.minSteps}</span>
                <span>{modelConstraints.maxSteps}</span>
              </div>
            </div>

            {/* Guidance Scale */}
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                Guidance Scale: {params.guidanceScale}
                <Tooltip>
                  <TooltipTrigger>
                    <Info className="w-4 h-4 text-gray-400 sm:w-auto md:w-full" />
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>How closely to follow the prompt. Higher = more adherence</p>
                  </TooltipContent>
                </Tooltip>
              </Label>
              <Slider
                value={[params.guidanceScale]}
                onValueChange={([value]) => handleParamChange('guidanceScale', value)}
                min={modelConstraints.defaultGuidanceRange[0]}
                max={modelConstraints.defaultGuidanceRange[1]}
                step={0.1}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500 sm:text-sm md:text-base">
                <span>{modelConstraints.defaultGuidanceRange[0]}</span>
                <span>{modelConstraints.defaultGuidanceRange[1]}</span>
              </div>
            </div>
          </div>

          {/* Advanced Settings */}
          <Collapsible open={showAdvanced} onOpenChange={setShowAdvanced}>
            <CollapsibleTrigger asChild>
              <button variant="ghost" className="w-full justify-between p-2 sm:p-4 md:p-6" aria-label="Button">
                <span className="flex items-center gap-2">
                  <Settings className="w-4 h-4 sm:w-auto md:w-full" />
                  Advanced Settings
                </span>
                {showAdvanced ? <ChevronDown className="w-4 h-4 sm:w-auto md:w-full" /> : <ChevronRight className="w-4 h-4 sm:w-auto md:w-full" />}
              </Button>
            </CollapsibleTrigger>
            
            <CollapsibleContent className="space-y-4 mt-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Seed */}
                <div className="space-y-2">
                  <Label className="flex items-center gap-2">
                    Seed
                    <Tooltip>
                      <TooltipTrigger>
                        <Info className="w-4 h-4 text-gray-400 sm:w-auto md:w-full" />
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>Random seed for reproducible results. Leave empty for random.</p>
                      </TooltipContent>
                    </Tooltip>
                  </Label>
                  <div className="flex gap-2">
                    <input
                      type="number"
                      value={params.seed || ''}
                      onChange={(e) = aria-label="Input"> handleParamChange('seed', e.target.value ? parseInt(e.target.value) : undefined)}
                      placeholder="Random"
                    />
                    <button
                      variant="outline"
                      size="sm"
                      onClick={generateRandomSeed}
                     aria-label="Button">
                      <Shuffle className="w-4 h-4 sm:w-auto md:w-full" />
                    </Button>
                  </div>
                </div>

                {/* Batch Size */}
                <div className="space-y-2">
                  <Label className="flex items-center gap-2">
                    Batch Size: {params.batchSize}
                    <Tooltip>
                      <TooltipTrigger>
                        <Info className="w-4 h-4 text-gray-400 sm:w-auto md:w-full" />
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>Number of images to generate at once</p>
                      </TooltipContent>
                    </Tooltip>
                  </Label>
                  <Slider
                    value={[params.batchSize]}
                    onValueChange={([value]) => handleParamChange('batchSize', value)}
                    min={1}
                    max={4}
                    step={1}
                    className="w-full"
                  />
                </div>

                {/* Sampler */}
                <div className="space-y-2">
                  <Label>Sampler</Label>
                  <select 
                    value={params.sampler || 'euler_a'} 
                    onValueChange={(value) = aria-label="Select option"> handleParamChange('sampler', value)}
                  >
                    <selectTrigger aria-label="Select option">
                      <selectValue />
                    </SelectTrigger>
                    <selectContent aria-label="Select option">
                      {modelConstraints.supportedSamplers.map((sampler) => (
                        <selectItem key={sampler} value={sampler} aria-label="Select option">
                          {sampler.toUpperCase()}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Scheduler */}
                <div className="space-y-2">
                  <Label>Scheduler</Label>
                  <select 
                    value={params.scheduler || 'normal'} 
                    onValueChange={(value) = aria-label="Select option"> handleParamChange('scheduler', value)}
                  >
                    <selectTrigger aria-label="Select option">
                      <selectValue />
                    </SelectTrigger>
                    <selectContent aria-label="Select option">
                      <selectItem value="normal" aria-label="Select option">Normal</SelectItem>
                      <selectItem value="karras" aria-label="Select option">Karras</SelectItem>
                      <selectItem value="exponential" aria-label="Select option">Exponential</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CollapsibleContent>
          </Collapsible>

          <Separator />

          {/* Action Buttons */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <button
                variant="outline"
                size="sm"
                onClick={resetToDefaults}
                disabled={isGenerating}
               aria-label="Button">
                <RotateCcw className="w-4 h-4 mr-1 sm:w-auto md:w-full" />
                Reset
              </Button>
              
              <button
                variant="outline"
                size="sm"
                onClick={() = aria-label="Button"> {
                  // Save current params as preset (mock implementation)
                  toast({
                    title: 'Preset Saved',
                    description: 'Current settings saved as custom preset',
                  });
                }}
                disabled={isGenerating}
              >
                <Save className="w-4 h-4 mr-1 sm:w-auto md:w-full" />
                Save Preset
              </Button>
            </div>

            <button
              onClick={handleGenerate}
              disabled={!params.prompt.trim() || isGenerating}
              size="lg"
              className="px-8"
             aria-label="Button">
              {isGenerating ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2 sm:w-auto md:w-full" />
                  Generating...
                </>
              ) : (
                <>
                  <Image className="w-4 h-4 mr-2 sm:w-auto md:w-full" />
                  Generate Image
                </>
              )}
            </Button>
          </div>

          {/* Model-specific warnings or tips */}
          {model && (
            <div className="text-xs text-gray-600 bg-gray-50 p-3 rounded-lg sm:text-sm md:text-base">
              <div className="flex items-start gap-2">
                <Info className="w-4 h-4 mt-0.5 flex-shrink-0 sm:w-auto md:w-full" />
                <div>
                  <p className="font-medium mb-1">Tips for {model.name}:</p>
                  {model.subtype === 'flux' && (
                    <p>Flux models work best with detailed prompts and don't require negative prompts.</p>
                  )}
                  {model.subtype === 'stable-diffusion' && (
                    <p>Use negative prompts to avoid unwanted elements. Higher guidance scales give more prompt adherence.</p>
                  )}
                  {!model.subtype && (
                    <p>Experiment with different settings to find what works best for your prompts.</p>
                  )}
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </TooltipProvider>
  );
}