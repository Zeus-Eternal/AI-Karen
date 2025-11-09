"use client";

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Image, Wand2, Settings2 } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface ImageGenerationParams {
  prompt: string;
  model?: string;
  size?: string;
  quality?: string;
  style?: string;
  steps?: number;
  guidance?: number;
}

export interface ImageGenerationControlsProps {
  onGenerate?: (params: ImageGenerationParams) => void;
  isGenerating?: boolean;
  showAdvanced?: boolean;
  className?: string;
}

export default function ImageGenerationControls({
  onGenerate,
  isGenerating = false,
  showAdvanced = false,
  className,
}: ImageGenerationControlsProps) {
  const [prompt, setPrompt] = useState('');
  const [model, setModel] = useState('dall-e-3');
  const [size, setSize] = useState('1024x1024');
  const [quality, setQuality] = useState('standard');
  const [style, setStyle] = useState('vivid');
  const [steps, setSteps] = useState([30]);
  const [guidance, setGuidance] = useState([7.5]);

  const handleGenerate = () => {
    if (prompt.trim() && onGenerate) {
      onGenerate({
        prompt: prompt.trim(),
        model,
        size,
        quality,
        style,
        steps: steps[0],
        guidance: guidance[0],
      });
    }
  };

  return (
    <Card className={cn('w-full', className)}>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Image className="h-5 w-5 text-purple-600 dark:text-purple-400" />
          <CardTitle>Image Generation</CardTitle>
        </div>
        <CardDescription>
          Create images from text descriptions using AI
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Prompt Input */}
        <div className="space-y-2">
          <Label htmlFor="prompt">Prompt</Label>
          <Input
            id="prompt"
            placeholder="Describe the image you want to generate..."
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            disabled={isGenerating}
          />
        </div>

        {/* Model Selection */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="model">Model</Label>
            <Select value={model} onValueChange={setModel} disabled={isGenerating}>
              <SelectTrigger id="model">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="dall-e-3">DALL-E 3</SelectItem>
                <SelectItem value="dall-e-2">DALL-E 2</SelectItem>
                <SelectItem value="stable-diffusion">Stable Diffusion</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="size">Size</Label>
            <Select value={size} onValueChange={setSize} disabled={isGenerating}>
              <SelectTrigger id="size">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1024x1024">1024×1024</SelectItem>
                <SelectItem value="1024x1792">1024×1792 (Portrait)</SelectItem>
                <SelectItem value="1792x1024">1792×1024 (Landscape)</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Quality and Style */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="quality">Quality</Label>
            <Select value={quality} onValueChange={setQuality} disabled={isGenerating}>
              <SelectTrigger id="quality">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="standard">Standard</SelectItem>
                <SelectItem value="hd">HD</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="style">Style</Label>
            <Select value={style} onValueChange={setStyle} disabled={isGenerating}>
              <SelectTrigger id="style">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="vivid">Vivid</SelectItem>
                <SelectItem value="natural">Natural</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Advanced Settings */}
        {showAdvanced && (
          <>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="steps">Steps: {steps[0]}</Label>
              </div>
              <Slider
                id="steps"
                min={10}
                max={50}
                step={1}
                value={steps}
                onValueChange={setSteps}
                disabled={isGenerating}
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="guidance">Guidance Scale: {guidance[0]}</Label>
              </div>
              <Slider
                id="guidance"
                min={1}
                max={20}
                step={0.5}
                value={guidance}
                onValueChange={setGuidance}
                disabled={isGenerating}
              />
            </div>
          </>
        )}
      </CardContent>

      <CardFooter>
        <Button
          onClick={handleGenerate}
          disabled={!prompt.trim() || isGenerating}
          className="w-full"
        >
          {isGenerating ? (
            <>
              <Settings2 className="h-4 w-4 mr-2 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <Wand2 className="h-4 w-4 mr-2" />
              Generate Image
            </>
          )}
        </Button>
      </CardFooter>
    </Card>
  );
}

export { ImageGenerationControls };
