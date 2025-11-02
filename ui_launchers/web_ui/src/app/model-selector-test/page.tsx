"use client";
import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ModelSelector, EnhancedModelSelector as ChatEnhancedModelSelector } from "@/components/chat";
import EnhancedModelSelector from "@/components/models/EnhancedModelSelector";
import { Model } from "@/lib/model-utils";
export default function ModelSelectorTestPage() {
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [intelligentSelectedModel, setIntelligentSelectedModel] = useState<Model | null>(null);
  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Model Selector Test</h1>
          <p className="text-muted-foreground mt-2">
            Test the new modern model selector component with real data from the backend.
          </p>
        </div>
        <div className="grid gap-6 md:grid-cols-2">
          {/* Basic Model Selector */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Basic Model Selector</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <ModelSelector
                value={selectedModel}
                onValueChange={setSelectedModel}
                placeholder="Choose a model..."
              />
              {selectedModel && (
                <div className="p-3 bg-muted rounded-md">
                  <p className="text-sm font-medium">Selected Model:</p>
                  <Badge variant="outline" className="mt-1">
                    {selectedModel}
                  </Badge>
                </div>
              )}
            </CardContent>
          </Card>
          {/* Compact Model Selector */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Compact Version</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <ModelSelector
                value={selectedModel}
                onValueChange={setSelectedModel}
                placeholder="Select model..."
                showDetails={false}
                className="w-full"
              />
              <p className="text-sm text-muted-foreground">
                This version shows less detail for space-constrained layouts.
              </p>
            </CardContent>
          </Card>
          {/* Disabled State */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Disabled State</CardTitle>
            </CardHeader>
            <CardContent>
              <ModelSelector
                value=""
                onValueChange={() => {}}
                placeholder="Disabled selector..."
                disabled={true}
              />
            </CardContent>
          </Card>
          {/* Enhanced Model Selector */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Enhanced Model Selector</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <ChatEnhancedModelSelector
                value={selectedModel}
                onValueChange={setSelectedModel}
                placeholder="Choose a model..."
                showActions={true}
                onModelAction={(action, modelId) => {
                }}
              />
              <p className="text-sm text-muted-foreground">
                This version includes model actions like download, delete, and info.
              </p>
            </CardContent>
          </Card>
        </div>
        {/* Intelligent Model Selector */}
        <Card>
          <CardHeader>
            <CardTitle className="text-xl">🧠 Intelligent Model Selector</CardTitle>
            <p className="text-muted-foreground">
              Priority-based model selection: Last selected → Default → First available
            </p>
          </CardHeader>
          <CardContent>
            <EnhancedModelSelector
              preferLocal={true}
              showStats={true}
              showActions={true}
              onModelChange={(model) => {
                setIntelligentSelectedModel(model);
              }}
              className="w-full"
            />
            {intelligentSelectedModel && (
              <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                <h4 className="font-medium text-blue-900">Currently Selected Model</h4>
                <p className="text-blue-800">{intelligentSelectedModel.name}</p>
                <p className="text-sm text-blue-600 mt-1">
                  ID: {intelligentSelectedModel.id} | Provider: {intelligentSelectedModel.provider}
                </p>
              </div>
            )}
          </CardContent>
        </Card>
        {/* Features List */}
        <Card>
          <CardHeader>
            <CardTitle>Features</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <h4 className="font-medium mb-2">Visual Features</h4>
                <ul className="text-sm space-y-1 text-muted-foreground">
                  <li>• Provider icons (HDD, Brain, Zap, CPU)</li>
                  <li>• Status indicators (Local, Available, Downloading)</li>
                  <li>• Progress indicators for downloads</li>
                  <li>• Grouped by status with separators</li>
                  <li>• Tooltips with detailed information</li>
                  <li>• Responsive design with proper truncation</li>
                </ul>
              </div>
              <div>
                <h4 className="font-medium mb-2">Functional Features</h4>
                <ul className="text-sm space-y-1 text-muted-foreground">
                  <li>• Real-time model data from backend</li>
                  <li>• Automatic refresh and error handling</li>
                  <li>• Support for local and remote models</li>
                  <li>• Model metadata display (size, params, etc.)</li>
                  <li>• Keyboard navigation support</li>
                  <li>• Accessible with screen readers</li>
                </ul>
              </div>
              <div>
                <h4 className="font-medium mb-2">🧠 Intelligent Selection Features</h4>
                <ul className="text-sm space-y-1 text-muted-foreground">
                  <li>• Priority-based model selection logic</li>
                  <li>• Remembers last selected model</li>
                  <li>• Respects user-defined default model</li>
                  <li>• Smart fallback to first available model</li>
                  <li>• Preference for local models</li>
                  <li>• Real-time model readiness checking</li>
                  <li>• Automatic preference persistence</li>
                  <li>• Model selection statistics</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
