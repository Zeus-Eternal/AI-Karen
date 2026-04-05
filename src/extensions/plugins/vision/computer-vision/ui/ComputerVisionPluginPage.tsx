"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Eye, Upload, Image, Layers, Settings } from "lucide-react";

export default function ComputerVisionPluginPage() {
  return (
    <div className="space-y-8">
      <div className="flex items-center space-x-3">
        <Eye className="h-8 w-8 text-blue-600" />
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">Computer Vision & OCR</h2>
          <p className="text-sm text-muted-foreground">
            Advanced computer vision capabilities including OCR, image analysis, and AI-powered visual understanding
          </p>
        </div>
      </div>

      <Alert variant="default" className="bg-yellow-50 dark:bg-yellow-950/20 border-yellow-200 dark:border-yellow-800">
        <AlertTitle className="text-yellow-800 dark:text-yellow-200">Setup Required</AlertTitle>
        <AlertDescription className="text-yellow-700 dark:text-yellow-300">
          This plugin requires file system access permissions. Please configure the appropriate permissions in your system settings.
        </AlertDescription>
      </Alert>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Features</CardTitle>
          <CardDescription>Available computer vision capabilities</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-start gap-4 p-4 border rounded-lg">
            <Upload className="h-8 w-8 text-blue-500 mt-1" />
            <div>
              <h4 className="font-semibold">OCR - Optical Character Recognition</h4>
              <p className="text-sm text-muted-foreground">
                Extract text from images, scanned documents, and screenshots with high accuracy
              </p>
            </div>
          </div>

          <div className="flex items-start gap-4 p-4 border rounded-lg">
            <Image className="h-8 w-8 text-green-500 mt-1" />
            <div>
              <h4 className="font-semibold">Image Analysis</h4>
              <p className="text-sm text-muted-foreground">
                Analyze images for objects, scenes, and visual patterns using advanced AI
              </p>
            </div>
          </div>

          <div className="flex items-start gap-4 p-4 border rounded-lg">
            <Layers className="h-8 w-8 text-purple-500 mt-1" />
            <div>
              <h4 className="font-semibold">Object Detection</h4>
              <p className="text-sm text-muted-foreground">
                Identify and classify objects within images with bounding boxes and confidence scores
              </p>
            </div>
          </div>

          <div className="flex items-start gap-4 p-4 border rounded-lg">
            <Settings className="h-8 w-8 text-gray-500 mt-1" />
            <div>
              <h4 className="font-semibold">Visual Understanding</h4>
              <p className="text-sm text-muted-foreground">
                Get detailed descriptions and contextual understanding of visual content
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Usage</CardTitle>
          <CardDescription>How to use computer vision features</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-4">
            You can use computer vision capabilities by uploading images or sharing screenshots with Karen.
          </p>
          <Alert>
            <AlertTitle className="text-sm font-semibold">Example Prompts</AlertTitle>
            <AlertDescription className="text-xs">
              <ul className="list-disc list-inside space-y-1">
                <li>"Extract all text from this image"</li>
                <li>"What objects do you see in this picture?"</li>
                <li>"Describe this screenshot in detail"</li>
                <li>"Identify the text in this document"</li>
              </ul>
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    </div>
  );
}