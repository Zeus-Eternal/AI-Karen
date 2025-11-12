"use client";

import React, { useCallback, useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useToast } from "@/hooks/use-toast";

// Icons
import {
  Brain,
  Zap,
  Eye,
  Search as SearchIcon,
  Copy,
  Palette,
  Image as ImageIcon,
  Tag,
  CheckCircle,
} from "lucide-react";

// Local types (align with your repo contracts)
import type { Attachment, AttachmentAnalysis } from "@/types/enhanced-chat";

/* -------------------------------------------------------------------------- */
/* Types                                                                      */
/* -------------------------------------------------------------------------- */

interface ImageAnalysisResult {
  objects: Array<{
    name: string;
    confidence: number;
    boundingBox?: { x: number; y: number; width: number; height: number };
  }>;
  text: Array<{
    content: string;
    confidence: number;
    boundingBox?: { x: number; y: number; width: number; height: number };
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

/* -------------------------------------------------------------------------- */
/* Component                                                                  */
/* -------------------------------------------------------------------------- */

export const ImageAnalysis: React.FC<ImageAnalysisProps> = ({
  attachment,
  onAnalysisComplete,
  className = "",
}) => {
  const { toast } = useToast();
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [analysisResult, setAnalysisResult] = useState<ImageAnalysisResult | null>(
    null
  );

  const isImage = attachment?.type === "image";

  // Simulated pipeline steps for UI feedback (replace with real service calls)
  const performImageAnalysis = useCallback(async (): Promise<ImageAnalysisResult> => {
    const steps = [
      "Loading image…",
      "Detecting objects…",
      "Extracting text…",
      "Analyzing colors…",
      "Detecting faces…",
      "Understanding scene…",
      "Evaluating quality…",
      "Finalizing results…",
    ];

    for (let i = 0; i < steps.length; i++) {
      // In a real implementation, update progress from service events
      setAnalysisProgress(((i + 1) / steps.length) * 100);
      // eslint-disable-next-line no-await-in-loop
      await new Promise((r) => setTimeout(r, 400));
    }

    // MOCK: deterministic, but rich enough for UI wiring
    return {
      objects: [
        { name: "person", confidence: 0.95 },
        { name: "building", confidence: 0.87 },
        { name: "car", confidence: 0.72 },
        { name: "tree", confidence: 0.68 },
      ],
      text: [
        { content: "STOP", confidence: 0.98 },
        { content: "Main Street", confidence: 0.85 },
        { content: "123", confidence: 0.92 },
      ],
      colors: [
        { color: "Blue", percentage: 35, hex: "#4A90E2" },
        { color: "Gray", percentage: 28, hex: "#8E8E93" },
        { color: "Green", percentage: 20, hex: "#7ED321" },
        { color: "White", percentage: 17, hex: "#FFFFFF" },
      ],
      faces: [
        {
          confidence: 0.94,
          emotions: { happy: 0.7, neutral: 0.2, surprised: 0.1 },
          age: 32,
          gender: "female",
        },
      ],
      scene: {
        description: "Urban street scene with buildings and vehicles",
        confidence: 0.89,
        tags: ["outdoor", "urban", "street", "daytime", "architecture"],
      },
      quality: {
        sharpness: 0.85,
        brightness: 0.72,
        contrast: 0.78,
        overall: 0.78,
      },
    };
  }, []);

  const handleAnalyze = useCallback(async () => {
    if (!isImage) return;

    setIsAnalyzing(true);
    setAnalysisProgress(0);

    try {
      const result = await performImageAnalysis();
      setAnalysisResult(result);

      const analysis: AttachmentAnalysis = {
        summary: `Image contains ${result.objects.length} objects, ${result.text.length} text elements, and ${result.faces.length} faces. Scene: ${result.scene.description}`,
        entities: result.objects.map((o) => o.name),
        topics: result.scene.tags,
        sentiment: "neutral",
        confidence: result.scene.confidence,
        extractedText: result.text.map((t) => t.content).join(" "),
      };

      onAnalysisComplete?.(analysis);

      toast({
        title: "Analysis Complete",
        description: "Image has been analyzed successfully.",
      });
      } catch (error) {
        console.error("Enhanced image analysis failed", error);
        toast({
          variant: "destructive",
          title: "Analysis Failed",
          description: "We couldn't analyze this image. Please try again.",
        });
    } finally {
      setIsAnalyzing(false);
      setAnalysisProgress(0);
    }
  }, [isImage, onAnalysisComplete, performImageAnalysis, toast]);

  const copyExtractedText = useCallback(async () => {
    if (!analysisResult) return;
    const text = analysisResult.text.map((t) => t.content).join(" ");
    try {
      await navigator.clipboard.writeText(text);
      toast({ title: "Copied", description: "Extracted text copied to clipboard." });
    } catch (error) {
      console.error("Failed to copy extracted image text", error);
      toast({
        variant: "destructive",
        title: "Copy Failed",
        description: "Clipboard permissions denied or unavailable.",
      });
    }
  }, [analysisResult, toast]);

  const getQualityColor = (score: number) => {
    if (score >= 0.8) return "text-green-600";
    if (score >= 0.6) return "text-yellow-600";
    return "text-red-600";
  };

  const getQualityLabel = (score: number) => {
    if (score >= 0.8) return "Excellent";
    if (score >= 0.6) return "Good";
    if (score >= 0.4) return "Fair";
    return "Poor";
  };

  const imageDims = attachment?.metadata?.dimensions;
  const colorMax = useMemo(
    () => Math.max(1, ...(analysisResult?.colors.map((c) => c.percentage) || [1])),
    [analysisResult]
  );

  return (
    <Card className={`h-full flex flex-col ${className}`}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2">
          <Brain className="h-5 w-5" /> Image Analysis
        </CardTitle>
      </CardHeader>

      <CardContent className="flex-1 space-y-4">
        {/* Image Preview */}
        <div className="relative">
          {isImage ? (
            <img
              src={attachment.url}
              alt={attachment.name || "Attachment"}
              className="w-full h-48 object-cover rounded-lg border"
            />
          ) : (
            <div className="w-full h-48 rounded-lg border grid place-items-center text-sm text-muted-foreground">
              Unsupported attachment type
            </div>
          )}
          {isImage && imageDims && (
            <Badge className="absolute top-2 right-2 bg-black/50 text-white">
              {imageDims.width} × {imageDims.height}
            </Badge>
          )}
        </div>

        {/* Controls */}
        <div className="flex items-center gap-2">
          <Button
            onClick={handleAnalyze}
            disabled={isAnalyzing || !isImage}
            className="flex-1"
            aria-label="Analyze Image"
          >
            <Zap className="h-4 w-4 mr-2" />
            {isAnalyzing ? "Analyzing…" : "Analyze Image"}
          </Button>
        </div>

        {/* Progress */}
        {isAnalyzing && (
          <div className="space-y-2">
            <Progress value={analysisProgress} className="h-2" />
            <p className="text-sm text-muted-foreground text-center">
              Processing image… {Math.round(analysisProgress)}%
            </p>
          </div>
        )}

        {/* Results */}
        {analysisResult && (
          <ScrollArea className="flex-1">
            <div className="space-y-4">
              {/* Objects */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2 md:text-base">
                    <Eye className="h-4 w-4" /> Objects Detected ({analysisResult.objects.length})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-2">
                    {analysisResult.objects.map((object, idx) => (
                      <div
                        key={`${object.name}-${idx}`}
                        className="flex items-center justify-between p-2 border rounded"
                      >
                        <span className="text-sm font-medium">{object.name}</span>
                        <Badge variant="secondary" className="text-xs">
                          {Math.round(object.confidence * 100)}%
                        </Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Text */}
              {analysisResult.text.length > 0 && (
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm flex items-center gap-2 md:text-base">
                      <SearchIcon className="h-4 w-4" /> Text Extracted ({analysisResult.text.length})
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={copyExtractedText}
                        className="ml-auto"
                        aria-label="Copy extracted text"
                      >
                        <Copy className="h-4 w-4" />
                      </Button>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {analysisResult.text.map((t, idx) => (
                        <div key={`${t.content}-${idx}`} className="flex items-center justify-between p-2 border rounded">
                          <span className="text-sm font-mono">{t.content}</span>
                          <Badge variant="outline" className="text-xs">
                            {Math.round(t.confidence * 100)}%
                          </Badge>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Colors */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2 md:text-base">
                    <Palette className="h-4 w-4" /> Color Palette
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {analysisResult.colors.map((c, idx) => (
                      <div key={`${c.hex}-${idx}`} className="flex items-center gap-3 p-2 border rounded">
                        <div className="w-6 h-6 rounded border" style={{ backgroundColor: c.hex }} />
                        <div className="flex-1">
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-medium">{c.color}</span>
                            <span className="text-xs text-muted-foreground">{c.percentage}%</span>
                          </div>
                          <div className="w-full bg-muted rounded-full h-2 mt-1">
                            <div
                              className="h-2 rounded-full bg-primary"
                              style={{ width: `${(c.percentage / colorMax) * 100}%` }}
                            />
                          </div>
                        </div>
                        <Badge variant="secondary" className="text-xs">
                          {c.hex}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Faces */}
              {analysisResult.faces.length > 0 && (
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm flex items-center gap-2 md:text-base">
                      <ImageIcon className="h-4 w-4" /> Faces Detected ({analysisResult.faces.length})
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {analysisResult.faces.map((face, idx) => (
                      <div key={`face-${idx}`} className="space-y-2 p-3 border rounded">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium">Face {idx + 1}</span>
                          <Badge variant="secondary" className="text-xs">
                            {Math.round(face.confidence * 100)}% confidence
                          </Badge>
                        </div>
                        {(face.age || face.gender) && (
                          <div className="flex gap-4 text-sm text-muted-foreground">
                            {face.age ? <span>Age: ~{face.age}</span> : null}
                            {face.gender ? <span>Gender: {face.gender}</span> : null}
                          </div>
                        )}
                        {face.emotions && (
                          <div className="space-y-1">
                            <span className="text-xs font-medium">Emotions:</span>
                            <div className="grid grid-cols-3 gap-1">
                              {Object.entries(face.emotions).map(([emotion, score]) => (
                                <div key={emotion} className="text-xs">
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

              {/* Scene */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2 md:text-base">
                    <Tag className="h-4 w-4" /> Scene Understanding
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div>
                      <p className="text-sm font-medium mb-2">Description</p>
                      <p className="text-sm text-muted-foreground">
                        {analysisResult.scene.description}
                      </p>
                      <Badge variant="outline" className="mt-2 text-xs">
                        {Math.round(analysisResult.scene.confidence * 100)}% confidence
                      </Badge>
                    </div>
                    <div>
                      <p className="text-sm font-medium mb-2">Tags</p>
                      <div className="flex flex-wrap gap-1">
                        {analysisResult.scene.tags.map((t, idx) => (
                          <Badge key={`${t}-${idx}`} variant="secondary" className="text-xs">
                            {t}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Quality */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2 md:text-base">
                    <CheckCircle className="h-4 w-4" /> Image Quality
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Overall Quality</span>
                      <div className="flex items-center gap-2">
                        <span className={`text-sm font-medium ${getQualityColor(analysisResult.quality.overall)}`}>
                          {getQualityLabel(analysisResult.quality.overall)}
                        </span>
                        <Badge variant="outline" className="text-xs">
                          {Math.round(analysisResult.quality.overall * 100)}%
                        </Badge>
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-3 text-sm">
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

        {/* Empty State */}
        {!analysisResult && !isAnalyzing && (
          <div className="text-center py-8">
            <Brain className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p className="text-sm text-muted-foreground mb-2">
              Click "Analyze Image" to extract insights from this image.
            </p>
            <div className="text-xs text-muted-foreground">Supported type: image</div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default ImageAnalysis;
