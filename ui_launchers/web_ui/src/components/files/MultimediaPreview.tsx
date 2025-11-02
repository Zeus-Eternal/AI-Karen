"use client";

import React, { useState, useEffect, useMemo } from 'react';
import { AgCharts } from 'ag-charts-react';
import { AgChartOptions } from 'ag-charts-community';

import { } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';
import { FileMetadata } from './FileMetadataGrid';

interface MultimediaAnalysis {
  image_analysis?: {
    objects_detected: Array<{
      label: string;
      confidence: number;
      bbox: number[];
      description: string;
    }>;
    faces_detected: Array<{
      confidence: number;
      bbox: number[];
      age_estimate?: number;
      emotion?: string;
    }>;
    text_extracted?: string;
    scene_description?: string;
    dominant_colors: string[];
    image_properties: {
      format: string;
      mode: string;
      size: number[];
      has_transparency: boolean;
    };
    confidence_scores: Record<string, number>;
  };
  audio_analysis?: {
    transcription?: string;
    language_detected?: string;
    speaker_count?: number;
    audio_properties: Record<string, any>;
    sentiment_analysis?: {
      overall: string;
      confidence: number;
    };
  };
  video_analysis?: {
    frame_analysis: Array<{
      frame_path: string;
      timestamp: number;
      objects_detected: any[];
      scene_description: string;
    }>;
    video_properties: Record<string, any>;
    scene_changes: number[];
    key_frames: string[];
  };
  content_moderation?: {
    is_safe: boolean;
    confidence: number;
    categories_detected: string[];
    moderation_labels: string[];
    recommended_action: string;
  };
}

interface MultimediaPreviewProps {
  file: FileMetadata;
  analysis?: MultimediaAnalysis;
  onDownload?: (fileId: string) => void;
  onFullscreen?: (fileId: string) => void;
  className?: string;
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const formatDate = (dateString: string): string => {
  try {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'

  } catch {
    return dateString;
  }
};

const ImagePreview: React.FC<{ file: FileMetadata; analysis?: MultimediaAnalysis['image_analysis'] }> = ({ 
  file, 
  analysis 
}) => {
  const [zoom, setZoom] = useState(1);
  const [rotation, setRotation] = useState(0);

  const confidenceChartOptions = useMemo<AgChartOptions>(() => {
    if (!analysis?.confidence_scores) return {};

    const data = Object.entries(analysis.confidence_scores).map(([key, value]) => ({
      category: key.replace('_', ' ').toUpperCase(),
      confidence: Math.round(value * 100)
    }));

    return {
      data,
      series: [{
        type: 'bar',
        xKey: 'category',
        yKey: 'confidence',
        fill: '#3b82f6',
      }],
      axes: [
        {
          type: 'category',
          position: 'bottom',
          title: { text: 'Analysis Type' }
        },
        {
          type: 'number',
          position: 'left',
          title: { text: 'Confidence (%)' },
          min: 0,
          max: 100
        }
      ],
      title: { text: 'Analysis Confidence Scores' },
      height: 300,
    };
  }, [analysis?.confidence_scores]);

  return (
    <div className="space-y-4">
      {/* Image Viewer */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Image className="h-5 w-5 " />
            </CardTitle>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setZoom(Math.max(0.5, zoom - 0.25))}
              >
                <ZoomOut className="h-4 w-4 " />
              </Button>
              <span className="text-sm font-mono md:text-base lg:text-lg">{Math.round(zoom * 100)}%</span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setZoom(Math.min(3, zoom + 0.25))}
              >
                <ZoomIn className="h-4 w-4 " />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setRotation((rotation + 90) % 360)}
              >
                <RotateCw className="h-4 w-4 " />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex justify-center bg-muted rounded-lg p-4 overflow-auto max-h-96 sm:p-4 md:p-6">
            <img
              src={`/api/files/${file.file_id}/thumbnail`}
              alt={file.filename}
              className="max-w-full h-auto"
              style={{
                transform: `scale(${zoom}) rotate(${rotation}deg)`,
                transition: 'transform 0.2s ease'
              }}
              onError={(e) => {
                (e.target as HTMLImageElement).src = '/placeholder-image.png';
              }}
            />
          </div>
        </CardContent>
      </Card>

      {/* Analysis Results */}
      {analysis && (
        <Tabs defaultValue="objects" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="objects">Objects</TabsTrigger>
            <TabsTrigger value="text">Text</TabsTrigger>
            <TabsTrigger value="colors">Colors</TabsTrigger>
            <TabsTrigger value="confidence">Confidence</TabsTrigger>
          </TabsList>

          <TabsContent value="objects" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Detected Objects</CardTitle>
              </CardHeader>
              <CardContent>
                {analysis.objects_detected?.length > 0 ? (
                  <div className="space-y-2">
                    {analysis.objects_detected.map((obj, index) => (
                      <div key={index} className="flex items-center justify-between p-2 border rounded sm:p-4 md:p-6">
                        <div>
                          <span className="font-medium">{obj.label}</span>
                          <p className="text-sm text-muted-foreground md:text-base lg:text-lg">{obj.description}</p>
                        </div>
                        <Badge variant="secondary">
                          {Math.round(obj.confidence * 100)}%
                        </Badge>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted-foreground">No objects detected</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="text" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Extracted Text</CardTitle>
              </CardHeader>
              <CardContent>
                {analysis.text_extracted ? (
                  <div className="bg-muted p-4 rounded-lg sm:p-4 md:p-6">
                    <pre className="whitespace-pre-wrap text-sm md:text-base lg:text-lg">{analysis.text_extracted}</pre>
                  </div>
                ) : (
                  <p className="text-muted-foreground">No text detected in image</p>
                )}
              </CardContent>
            </Card>

            {analysis.scene_description && (
              <Card>
                <CardHeader>
                  <CardTitle>Scene Description</CardTitle>
                </CardHeader>
                <CardContent>
                  <p>{analysis.scene_description}</p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="colors" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Color Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {analysis.dominant_colors?.map((color, index) => (
                    <Badge key={index} variant="outline" className="capitalize">
                      {color.replace('-', ' ')}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="confidence" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Analysis Confidence</CardTitle>
              </CardHeader>
              <CardContent>
                {analysis.confidence_scores && Object.keys(analysis.confidence_scores).length > 0 ? (
                  <AgCharts options={confidenceChartOptions} />
                ) : (
                  <p className="text-muted-foreground">No confidence data available</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
};

const AudioPreview: React.FC<{ file: FileMetadata; analysis?: MultimediaAnalysis['audio_analysis'] }> = ({ 
  file, 
  analysis 
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [progress, setProgress] = useState(0);

  return (
    <div className="space-y-4">
      {/* Audio Player */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Music className="h-5 w-5 " />
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsPlaying(!isPlaying)}
              >
                {isPlaying ? <Pause className="h-4 w-4 " /> : <Play className="h-4 w-4 " />}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsMuted(!isMuted)}
              >
                {isMuted ? <VolumeX className="h-4 w-4 " /> : <Volume2 className="h-4 w-4 " />}
              </Button>
              <div className="flex-1">
                <Progress value={progress} className="h-2" />
              </div>
            </div>
            
            <audio
              controls
              className="w-full"
              src={`/api/files/${file.file_id}/download`}
              onError={() => console.error('Audio playback error')}
            >
              Your browser does not support the audio element.
            </audio>
          </div>
        </CardContent>
      </Card>

      {/* Analysis Results */}
      {analysis && (
        <Tabs defaultValue="transcription" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="transcription">Transcription</TabsTrigger>
            <TabsTrigger value="properties">Properties</TabsTrigger>
            <TabsTrigger value="sentiment">Sentiment</TabsTrigger>
          </TabsList>

          <TabsContent value="transcription" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Speech Transcription</CardTitle>
              </CardHeader>
              <CardContent>
                {analysis.transcription ? (
                  <div className="bg-muted p-4 rounded-lg sm:p-4 md:p-6">
                    <p className="whitespace-pre-wrap">{analysis.transcription}</p>
                  </div>
                ) : (
                  <p className="text-muted-foreground">No transcription available</p>
                )}
                
                {analysis.language_detected && (
                  <div className="mt-4">
                    <Badge variant="secondary">
                      Language: {analysis.language_detected.toUpperCase()}
                    </Badge>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="properties" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Audio Properties</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  {Object.entries(analysis.audio_properties || {}).map(([key, value]) => (
                    <div key={key} className="flex justify-between">
                      <span className="capitalize">{key.replace('_', ' ')}:</span>
                      <span className="font-mono">{String(value)}</span>
                    </div>
                  ))}
                  {analysis.speaker_count && (
                    <div className="flex justify-between">
                      <span>Speakers:</span>
                      <span className="font-mono">{analysis.speaker_count}</span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="sentiment" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Sentiment Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                {analysis.sentiment_analysis ? (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span>Overall Sentiment:</span>
                      <Badge 
                        variant="secondary" 
                        className={cn(
                          analysis.sentiment_analysis.overall === 'positive' && 'bg-green-100 text-green-800',
                          analysis.sentiment_analysis.overall === 'negative' && 'bg-red-100 text-red-800',
                          analysis.sentiment_analysis.overall === 'neutral' && 'bg-gray-100 text-gray-800'
                        )}
                      >
                        {analysis.sentiment_analysis.overall}
                      </Badge>
                    </div>
                    <div>
                      <span>Confidence:</span>
                      <Progress 
                        value={analysis.sentiment_analysis.confidence * 100} 
                        className="mt-2"
                      />
                      <span className="text-sm text-muted-foreground md:text-base lg:text-lg">
                        {Math.round(analysis.sentiment_analysis.confidence * 100)}%
                      </span>
                    </div>
                  </div>
                ) : (
                  <p className="text-muted-foreground">No sentiment analysis available</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
};

const VideoPreview: React.FC<{ file: FileMetadata; analysis?: MultimediaAnalysis['video_analysis'] }> = ({ 
  file, 
  analysis 
}) => {
  return (
    <div className="space-y-4">
      {/* Video Player */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Video className="h-5 w-5 " />
          </CardTitle>
        </CardHeader>
        <CardContent>
          <video
            controls
            className="w-full max-h-96 bg-black rounded"
            src={`/api/files/${file.file_id}/download`}
            onError={() => console.error('Video playback error')}
          >
            Your browser does not support the video element.
          </video>
        </CardContent>
      </Card>

      {/* Analysis Results */}
      {analysis && (
        <Tabs defaultValue="frames" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="frames">Key Frames</TabsTrigger>
            <TabsTrigger value="properties">Properties</TabsTrigger>
          </TabsList>

          <TabsContent value="frames" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Key Frames Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                {analysis.frame_analysis?.length > 0 ? (
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    {analysis.frame_analysis.map((frame, index) => (
                      <div key={index} className="space-y-2">
                        <div className="aspect-video bg-muted rounded flex items-center justify-center">
                          <Video className="h-8 w-8 text-muted-foreground " />
                        </div>
                        <div className="text-sm md:text-base lg:text-lg">
                          <p className="font-medium">Frame {index + 1}</p>
                          <p className="text-muted-foreground">
                            {frame.timestamp.toFixed(2)}s
                          </p>
                          <p className="text-xs sm:text-sm md:text-base">{frame.scene_description}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted-foreground">No frame analysis available</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="properties" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Video Properties</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  {Object.entries(analysis.video_properties || {}).map(([key, value]) => (
                    <div key={key} className="flex justify-between">
                      <span className="capitalize">{key.replace('_', ' ')}:</span>
                      <span className="font-mono">{String(value)}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
};

export const MultimediaPreview: React.FC<MultimediaPreviewProps> = ({
  file,
  analysis,
  onDownload,
  onFullscreen,
  className
}) => {
  const renderPreview = () => {
    switch (file.file_type) {
      case 'image':
        return <ImagePreview file={file} analysis={analysis?.image_analysis} />;
      case 'audio':
        return <AudioPreview file={file} analysis={analysis?.audio_analysis} />;
      case 'video':
        return <VideoPreview file={file} analysis={analysis?.video_analysis} />;
      default:
        return (
          <Card>
            <CardContent className="p-8 text-center sm:p-4 md:p-6">
              <FileText className="h-12 w-12 mx-auto mb-4 text-muted-foreground " />
              <p className="text-muted-foreground">
              </p>
            </CardContent>
          </Card>
        );
    }
  };

  return (
    <div className={cn('w-full space-y-6', className)}>
      {/* File Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <CardTitle className="flex items-center gap-2">
                <Eye className="h-5 w-5 " />
                {file.filename}
              </CardTitle>
              <div className="flex items-center gap-4 text-sm text-muted-foreground md:text-base lg:text-lg">
                <span className="flex items-center gap-1">
                  <HardDrive className="h-4 w-4 " />
                  {formatFileSize(file.file_size)}
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="h-4 w-4 " />
                  {formatDate(file.upload_timestamp)}
                </span>
                {file.security_scan_result && (
                  <span className="flex items-center gap-1">
                    <Shield className="h-4 w-4 " />
                    <Badge 
                      variant="secondary"
                      className={cn(
                        file.security_scan_result === 'safe' && 'bg-green-100 text-green-800',
                        file.security_scan_result === 'suspicious' && 'bg-yellow-100 text-yellow-800',
                        file.security_scan_result === 'malicious' && 'bg-red-100 text-red-800'
                      )}
                    >
                      {file.security_scan_result}
                    </Badge>
                  </span>
                )}
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              {onFullscreen && (
                <Button variant="outline" size="sm" onClick={() => onFullscreen(file.file_id)}>
                  <Maximize2 className="h-4 w-4 " />
                </Button>
              )}
              {onDownload && (
                <Button variant="outline" size="sm" onClick={() => onDownload(file.file_id)}>
                  <Download className="h-4 w-4 " />
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* File Tags */}
      {file.tags && file.tags.length > 0 && (
        <Card>
          <CardContent className="p-4 sm:p-4 md:p-6">
            <div className="flex items-center gap-2">
              <Tag className="h-4 w-4 text-muted-foreground " />
              <span className="text-sm font-medium md:text-base lg:text-lg">Tags:</span>
              <div className="flex flex-wrap gap-1">
                {file.tags.map((tag, index) => (
                  <Badge key={index} variant="outline">
                    {tag}
                  </Badge>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Content Moderation Warning */}
      {analysis?.content_moderation && !analysis.content_moderation.is_safe && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardContent className="p-4 sm:p-4 md:p-6">
            <div className="flex items-center gap-2 text-yellow-800">
              <Shield className="h-4 w-4 " />
              <span className="font-medium">Content Warning</span>
            </div>
            <p className="text-sm text-yellow-700 mt-1 md:text-base lg:text-lg">
              This content has been flagged by our moderation system. 
              Recommended action: {analysis.content_moderation.recommended_action}
            </p>
            {analysis.content_moderation.categories_detected.length > 0 && (
              <div className="mt-2">
                <span className="text-xs text-yellow-600 sm:text-sm md:text-base">Categories: </span>
                {analysis.content_moderation.categories_detected.map((category, index) => (
                  <Badge key={index} variant="outline" className="mr-1 text-yellow-700">
                    {category}
                  </Badge>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Preview Content */}
      {renderPreview()}

      {/* File Metadata */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Info className="h-5 w-5 " />
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
            <div>
              <span className="font-medium">MIME Type:</span>
              <p className="text-muted-foreground font-mono">{file.mime_type}</p>
            </div>
            <div>
              <span className="font-medium">Processing Status:</span>
              <p>
                <Badge 
                  variant="secondary"
                  className={cn(
                    file.processing_status === 'completed' && 'bg-green-100 text-green-800',
                    file.processing_status === 'processing' && 'bg-blue-100 text-blue-800',
                    file.processing_status === 'failed' && 'bg-red-100 text-red-800'
                  )}
                >
                  {file.processing_status}
                </Badge>
              </p>
            </div>
            <div>
              <span className="font-medium">Features:</span>
              <div className="flex gap-1 mt-1">
                {file.has_thumbnail && (
                  <Badge variant="outline" className="text-xs sm:text-sm md:text-base">Thumbnail</Badge>
                )}
                {file.preview_available && (
                  <Badge variant="outline" className="text-xs sm:text-sm md:text-base">Preview</Badge>
                )}
                {file.extracted_content_available && (
                  <Badge variant="outline" className="text-xs sm:text-sm md:text-base">Text</Badge>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default MultimediaPreview;