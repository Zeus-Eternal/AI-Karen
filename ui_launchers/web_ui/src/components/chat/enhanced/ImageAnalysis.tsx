'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Eye,
  Brain,
  Search,
  Tag,
  Palette,
  Image as ImageIcon,
  Zap,
  AlertCircle,
  CheckCircle,
  Copy
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { Attachment, AttachmentAnalysis } from '@/types/enhanced-chat';

interface ImageAnalysisResult {
  objects: Array<{
    name: string;
    confidence: number;
    boundingBox?: {
      x: number;
      y: number;
      width: number;
      height: number;
    };
  }>;
  text: Array<{
    content: string;
    confidence: number;
    boundingBox?: {
      x: number;
      y: number;
      width: number;
      height: number;
    };
  }>;
  colors: Array<{
    color: string;
    percentage: number;
    hex: string;
  }>;
  faces: Array<{
    confidence: number;
    emotions?: Record<string, number>;
    age?: number;
    gender?: string;
  }>;
  scene: {
    description: string;
    confidence: number;
    tags: string[];
  };
  quality: {
    sharpness: number;
    brightness: number;
    contrast: number;
    overall: number;
  };
}

interface ImageAnalysisProps {
  attachment: Attachment;
  onAnalysisComplete?: (analysis: AttachmentAnalysis) => void;
  className?: string;
}

export const ImageAnalysis: React.FC<ImageAnalysisProps> = ({
  attachment,
  onAnalysisComplete,
  className = ''
}) => {
  const { toast } = useToast();
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [analysisResult, setAnalysisResult] = useState<ImageAnalysisResult | null>(null);
  const [selectedRegion, setSelectedRegion] = useState<any>(null);

  // Simulate comprehensive image analysis
  const performImageAnalysis = async (): Promise<ImageAnalysisResult> => {
    const steps = [
      'Loading image...',
      'Detecting objects...',
      'Extracting text...',
      'Analyzing colors...',
      'Detecting faces...',
      'Understanding scene...',
      'Evaluating quality...',
      'Finalizing results...'
    ];

    for (let i = 0; i < steps.length; i++) {
      setAnalysisProgress((i + 1) / steps.length * 100);
      await new Promise(resolve => setTimeout(resolve, 500));
    }

    // Mock analysis results
    return {
      objects: [
        { name: 'person', confidence: 0.95 },
        { name: 'building', confidence: 0.87 },
        { name: 'car', confidence: 0.72 },
        { name: 'tree', confidence: 0.68 }
      ],
      text: [
        { content: 'STOP', confidence: 0.98 },
        { content: 'Main Street', confidence: 0.85 },
        { content: '123', confidence: 0.92 }
      ],
      colors: [
        { color: 'Blue', percentage: 35, hex: '#4A90E2' },
        { color: 'Gray', percentage: 28, hex: '#8E8E93' },
        { color: 'Green', percentage: 20, hex: '#7ED321' },
        { color: 'White', percentage: 17, hex: '#FFFFFF' }
      ],
      faces: [
        {
          confidence: 0.94,
          emotions: {
            happy: 0.7,
            neutral: 0.2,
            surprised: 0.1
          },
          age: 32,
          gender: 'female'
        }
      ],
      scene: {
        description: 'Urban street scene with buildings and vehicles',
        confidence: 0.89,
        tags: ['outdoor', 'urban', 'street', 'daytime', 'architecture']
      },
      quality: {
        sharpness: 0.85,
        brightness: 0.72,
        contrast: 0.78,
        overall: 0.78
      }
    };
  };

  // Handle analysis trigger
  const handleAnalyze = async () => {
    if (attachment.type !== 'image') return;

    setIsAnalyzing(true);
    setAnalysisProgress(0);

    try {
      const result = await performImageAnalysis();
      setAnalysisResult(result);

      // Create AttachmentAnalysis object
      const analysis: AttachmentAnalysis = {
        summary: `Image contains ${result.objects.length} objects, ${result.text.length} text elements, and ${result.faces.length} faces. Scene: ${result.scene.description}`,
        entities: result.objects.map(obj => obj.name),
        topics: result.scene.tags,
        sentiment: 'neutral',
        confidence: result.scene.confidence,
        extractedText: result.text.map(t => t.content).join(' ')
      };

      onAnalysisComplete?.(analysis);

      toast({
        title: 'Analysis Complete',
        description: 'Image has been analyzed successfully'
      });
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Analysis Failed',
        description: 'Failed to analyze image'
      });
    } finally {
      setIsAnalyzing(false);
      setAnalysisProgress(0);
    }
  };

  // Copy text to clipboard
  const copyExtractedText = async () => {
    if (!analysisResult) return;
    
    const text = analysisResult.text.map(t => t.content).join(' ');
    try {
      await navigator.clipboard.writeText(text);
      toast({
        title: 'Copied',
        description: 'Extracted text copied to clipboard'
      });
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Copy Failed',
        description: 'Failed to copy text'
      });
    }
  };

  // Get quality color
  const getQualityColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  // Get quality label
  const getQualityLabel = (score: number) => {
    if (score >= 0.8) return 'Excellent';
    if (score >= 0.6) return 'Good';
    if (score >= 0.4) return 'Fair';
    return 'Poor';
  };

  return (
    <Card className={`h-full flex flex-col ${className}`}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2">
          <Brain className="h-5 w-5 sm:w-auto md:w-full" />
          Image Analysis
        </CardTitle>
      </CardHeader>

      <CardContent className="flex-1 space-y-4">
        {/* Image Preview */}
        <div className="relative">
          <img
            src={attachment.url}
            alt={attachment.name}
            className="w-full h-48 object-cover rounded-lg border"
          />
          {attachment.metadata?.dimensions && (
            <Badge className="absolute top-2 right-2 bg-black/50 text-white">
              {attachment.metadata.dimensions.width} × {attachment.metadata.dimensions.height}
            </Badge>
          )}
        </div>

        {/* Analysis Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleAnalyze}
            disabled={isAnalyzing}
            className="flex-1"
           aria-label="Button">
            <Zap className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
            {isAnalyzing ? 'Analyzing...' : 'Analyze Image'}
          </Button>
        </div>

        {/* Analysis Progress */}
        {isAnalyzing && (
          <div className="space-y-2">
            <Progress value={analysisProgress} className="h-2" />
            <p className="text-sm text-muted-foreground text-center md:text-base lg:text-lg">
              Processing image... {Math.round(analysisProgress)}%
            </p>
          </div>
        )}

        {/* Analysis Results */}
        {analysisResult && (
          <ScrollArea className="flex-1">
            <div className="space-y-4">
              {/* Objects Detected */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2 md:text-base lg:text-lg">
                    <Eye className="h-4 w-4 sm:w-auto md:w-full" />
                    Objects Detected ({analysisResult.objects.length})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-2">
                    {analysisResult.objects.map((object, index) => (
                      <div key={index} className="flex items-center justify-between p-2 border rounded sm:p-4 md:p-6">
                        <span className="text-sm font-medium md:text-base lg:text-lg">{object.name}</span>
                        <Badge variant="secondary" className="text-xs sm:text-sm md:text-base">
                          {Math.round(object.confidence * 100)}%
                        </Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Text Extracted */}
              {analysisResult.text.length > 0 && (
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm flex items-center gap-2 md:text-base lg:text-lg">
                      <Search className="h-4 w-4 sm:w-auto md:w-full" />
                      Text Extracted ({analysisResult.text.length})
                      <button
                        variant="ghost"
                        size="sm"
                        onClick={copyExtractedText}
                        className="ml-auto"
                       aria-label="Button">
                        <Copy className="h-4 w-4 sm:w-auto md:w-full" />
                      </Button>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {analysisResult.text.map((text, index) => (
                        <div key={index} className="flex items-center justify-between p-2 border rounded sm:p-4 md:p-6">
                          <span className="text-sm font-mono md:text-base lg:text-lg">{text.content}</span>
                          <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                            {Math.round(text.confidence * 100)}%
                          </Badge>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Color Palette */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2 md:text-base lg:text-lg">
                    <Palette className="h-4 w-4 sm:w-auto md:w-full" />
                    Color Palette
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-2">
                    {analysisResult.colors.map((color, index) => (
                      <div key={index} className="flex items-center gap-2 p-2 border rounded sm:p-4 md:p-6">
                        <div
                          className="w-6 h-6 rounded border sm:w-auto md:w-full"
                          style={{ backgroundColor: color.hex }}
                        />
                        <div className="flex-1">
                          <span className="text-sm font-medium md:text-base lg:text-lg">{color.color}</span>
                          <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
                            {color.percentage}%
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Faces Detected */}
              {analysisResult.faces.length > 0 && (
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm flex items-center gap-2 md:text-base lg:text-lg">
                      <ImageIcon className="h-4 w-4 sm:w-auto md:w-full" />
                      Faces Detected ({analysisResult.faces.length})
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {analysisResult.faces.map((face, index) => (
                      <div key={index} className="space-y-2 p-3 border rounded sm:p-4 md:p-6">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium md:text-base lg:text-lg">Face {index + 1}</span>
                          <Badge variant="secondary" className="text-xs sm:text-sm md:text-base">
                            {Math.round(face.confidence * 100)}% confidence
                          </Badge>
                        </div>
                        
                        {face.age && face.gender && (
                          <div className="flex gap-4 text-sm text-muted-foreground md:text-base lg:text-lg">
                            <span>Age: ~{face.age}</span>
                            <span>Gender: {face.gender}</span>
                          </div>
                        )}
                        
                        {face.emotions && (
                          <div className="space-y-1">
                            <span className="text-xs font-medium sm:text-sm md:text-base">Emotions:</span>
                            <div className="grid grid-cols-3 gap-1">
                              {Object.entries(face.emotions).map(([emotion, score]) => (
                                <div key={emotion} className="text-xs sm:text-sm md:text-base">
                                  <span className="capitalize">{emotion}: </span>
                                  <span className="font-medium">{Math.round(score * 100)}%</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </CardContent>
                </Card>
              )}

              {/* Scene Understanding */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2 md:text-base lg:text-lg">
                    <Tag className="h-4 w-4 sm:w-auto md:w-full" />
                    Scene Understanding
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div>
                      <p className="text-sm font-medium mb-2 md:text-base lg:text-lg">Description</p>
                      <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                        {analysisResult.scene.description}
                      </p>
                      <Badge variant="outline" className="mt-2 text-xs sm:text-sm md:text-base">
                        {Math.round(analysisResult.scene.confidence * 100)}% confidence
                      </Badge>
                    </div>
                    
                    <div>
                      <p className="text-sm font-medium mb-2 md:text-base lg:text-lg">Tags</p>
                      <div className="flex flex-wrap gap-1">
                        {analysisResult.scene.tags.map((tag, index) => (
                          <Badge key={index} variant="secondary" className="text-xs sm:text-sm md:text-base">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Image Quality */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2 md:text-base lg:text-lg">
                    <CheckCircle className="h-4 w-4 sm:w-auto md:w-full" />
                    Image Quality
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium md:text-base lg:text-lg">Overall Quality</span>
                      <div className="flex items-center gap-2">
                        <span className={`text-sm font-medium ${getQualityColor(analysisResult.quality.overall)}`}>
                          {getQualityLabel(analysisResult.quality.overall)}
                        </span>
                        <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                          {Math.round(analysisResult.quality.overall * 100)}%
                        </Badge>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-3 gap-3 text-sm md:text-base lg:text-lg">
                      <div className="text-center">
                        <div className="font-medium">Sharpness</div>
                        <div className={getQualityColor(analysisResult.quality.sharpness)}>
                          {Math.round(analysisResult.quality.sharpness * 100)}%
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="font-medium">Brightness</div>
                        <div className={getQualityColor(analysisResult.quality.brightness)}>
                          {Math.round(analysisResult.quality.brightness * 100)}%
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="font-medium">Contrast</div>
                        <div className={getQualityColor(analysisResult.quality.contrast)}>
                          {Math.round(analysisResult.quality.contrast * 100)}%
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </ScrollArea>
        )}

        {/* No Analysis State */}
        {!analysisResult && !isAnalyzing && (
          <div className="text-center py-8">
            <Brain className="h-12 w-12 mx-auto mb-4 opacity-50 sm:w-auto md:w-full" />
            <p className="text-sm text-muted-foreground mb-4 md:text-base lg:text-lg">
              Click "Analyze Image" to extract insights from this image
            </p>
            <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
              Analysis includes object detection, text extraction, color analysis, and more
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default ImageAnalysis;