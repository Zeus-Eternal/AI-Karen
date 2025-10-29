/**
 * Adaptive Chat Interface Component
 * 
 * Adapts the chat interface based on the selected model's capabilities.
 * Supports seamless switching between text and image generation modes.
 */

import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { MessageSquare, Image, Zap, Settings, Send, Loader2, Sparkles } from 'lucide-react';
import { useModelSelection } from '@/hooks/useModelSelection';
import { Model } from '@/lib/model-utils';
import { useToast } from '@/hooks/use-toast';

interface AdaptiveChatInterfaceProps {
  selectedModel?: Model | null;
  onModelChange?: (model: Model | null) => void;
  onModeChange?: (mode: ChatMode) => void;
  className?: string;
}

export type ChatMode = 'text' | 'image' | 'multimodal';

interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  mode: ChatMode;
  timestamp: Date;
  modelUsed?: string;
  imageUrl?: string;
  metadata?: Record<string, any>;
}

interface GenerationParams {
  // Text generation params
  temperature?: number;
  topP?: number;
  topK?: number;
  maxTokens?: number;
  
  // Image generation params
  width?: number;
  height?: number;
  steps?: number;
  guidanceScale?: number;
  seed?: number;
}

export default function AdaptiveChatInterface({
  selectedModel,
  onModelChange,
  onModeChange,
  className = ''
}: AdaptiveChatInterfaceProps) {
  const { toast } = useToast();
  const [chatMode, setChatMode] = useState<ChatMode>('text');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationParams, setGenerationParams] = useState<GenerationParams>({
    temperature: 0.7,
    topP: 0.9,
    maxTokens: 2048,
    width: 512,
    height: 512,
    steps: 20,
    guidanceScale: 7.5
  });

  const {
    models,
    selectedModel: hookSelectedModel,
    selectedModelInfo,
    setSelectedModel,
    loading: modelsLoading,
    error: modelsError
  } = useModelSelection({
    autoSelect: true,
    preferLocal: true,
    onModelSelected: (model, reason) => {
      onModelChange?.(model);
      if (model) {
        toast({
          title: 'Model Selected',
          description: `${model.name} selected (${reason.replace('_', ' ')})`,
        });
      }
    }
  });

  // Use provided selectedModel or fall back to hook's selectedModel
  const currentModel = selectedModel || selectedModelInfo;

  // Determine available modes based on current model capabilities
  const availableModes = useMemo((): ChatMode[] => {
    if (!currentModel) return ['text'];
    
    const modes: ChatMode[] = [];
    
    // Check for text capabilities
    if (currentModel.type === 'text' || 
        currentModel.type === 'multimodal' ||
        currentModel.capabilities?.includes('text-generation') ||
        currentModel.capabilities?.includes('chat')) {
      modes.push('text');
    }
    
    // Check for image capabilities
    if (currentModel.type === 'image' || 
        currentModel.type === 'multimodal' ||
        currentModel.capabilities?.includes('image-generation')) {
      modes.push('image');
    }
    
    // Add multimodal if model supports both
    if (modes.includes('text') && modes.includes('image')) {
      modes.push('multimodal');
    }
    
    return modes.length > 0 ? modes : ['text'];
  }, [currentModel]);

  // Auto-adapt chat mode based on selected model
  useEffect(() => {
    if (currentModel && availableModes.length > 0) {
      let newMode: ChatMode = 'text';
      
      // Prioritize based on model type
      if (currentModel.type === 'image' && availableModes.includes('image')) {
        newMode = 'image';
      } else if (currentModel.type === 'multimodal' && availableModes.includes('multimodal')) {
        newMode = 'multimodal';
      } else if (availableModes.includes('text')) {
        newMode = 'text';
      } else {
        newMode = availableModes[0];
      }
      
      if (newMode !== chatMode) {
        setChatMode(newMode);
        onModeChange?.(newMode);
        
        toast({
          title: 'Chat Mode Adapted',
          description: `Switched to ${newMode} mode for ${currentModel.name}`,
        });
      }
    }
  }, [currentModel, availableModes, chatMode, onModeChange, toast]);

  // Get mode-specific capabilities and indicators
  const getModeInfo = (mode: ChatMode) => {
    switch (mode) {
      case 'text':
        return {
          icon: <MessageSquare className="w-4 h-4" />,
          label: 'Text Generation',
          description: 'Generate text responses and have conversations',
          color: 'bg-blue-100 text-blue-800'
        };
      case 'image':
        return {
          icon: <Image className="w-4 h-4" />,
          label: 'Image Generation',
          description: 'Generate images from text descriptions',
          color: 'bg-purple-100 text-purple-800'
        };
      case 'multimodal':
        return {
          icon: <Zap className="w-4 h-4" />,
          label: 'Multi-modal',
          description: 'Generate both text and images',
          color: 'bg-orange-100 text-orange-800'
        };
    }
  };

  const handleModeChange = (newMode: ChatMode) => {
    if (availableModes.includes(newMode)) {
      setChatMode(newMode);
      onModeChange?.(newMode);
      
      toast({
        title: 'Mode Changed',
        description: `Switched to ${newMode} mode`,
      });
    }
  };

  const handleModelChange = (modelId: string) => {
    setSelectedModel(modelId);
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || !currentModel || isGenerating) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue.trim(),
      mode: chatMode,
      timestamp: new Date(),
      modelUsed: currentModel.id
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsGenerating(true);

    try {
      // Generate response based on current mode
      let response: string | { text?: string; imageUrl?: string } = '';
      
      if (chatMode === 'text' || chatMode === 'multimodal') {
        // Text generation
        response = await generateTextResponse(userMessage.content, currentModel, generationParams);
      } else if (chatMode === 'image') {
        // Image generation
        response = await generateImageResponse(userMessage.content, currentModel, generationParams);
      }

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: typeof response === 'string' ? response : (response.text || 'Generated image'),
        mode: chatMode,
        timestamp: new Date(),
        modelUsed: currentModel.id,
        imageUrl: typeof response === 'object' ? response.imageUrl : undefined,
        metadata: { generationParams }
      };

      setMessages(prev => [...prev, assistantMessage]);

    } catch (error) {
      console.error('Generation error:', error);
      toast({
        title: 'Generation Failed',
        description: error instanceof Error ? error.message : 'Unknown error occurred',
        variant: 'destructive'
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const generateTextResponse = async (prompt: string, model: Model, params: GenerationParams): Promise<string> => {
    // Mock text generation - in real implementation, this would call the backend API
    await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000));
    
    return `This is a mock response from ${model.name} for the prompt: "${prompt}". In a real implementation, this would generate actual text using the model with parameters: temperature=${params.temperature}, maxTokens=${params.maxTokens}.`;
  };

  const generateImageResponse = async (prompt: string, model: Model, params: GenerationParams): Promise<{ imageUrl: string; text: string }> => {
    // Mock image generation - in real implementation, this would call the backend API
    await new Promise(resolve => setTimeout(resolve, 2000 + Math.random() * 3000));
    
    return {
      imageUrl: `https://picsum.photos/${params.width}/${params.height}?random=${Date.now()}`,
      text: `Generated image for: "${prompt}" using ${model.name}`
    };
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  if (modelsLoading) {
    return (
      <Card className={className}>
        <CardContent className="flex items-center justify-center p-6">
          <Loader2 className="h-6 w-6 animate-spin mr-2" />
          <span>Loading models...</span>
        </CardContent>
      </Card>
    );
  }

  if (modelsError) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="text-center text-red-600">
            <p>Error loading models: {modelsError}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const currentModeInfo = getModeInfo(chatMode);

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header with Model and Mode Selection */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="w-5 h-5" />
                Adaptive Chat Interface
              </CardTitle>
              <CardDescription>
                Chat interface that adapts to your selected model's capabilities
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
          {/* Model Selection */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Selected Model</label>
              <Select 
                value={currentModel?.id || ''} 
                onValueChange={handleModelChange}
                disabled={modelsLoading}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a model" />
                </SelectTrigger>
                <SelectContent>
                  {models.map((model) => (
                    <SelectItem key={model.id} value={model.id}>
                      <div className="flex items-center gap-2">
                        {model.type === 'text' && <MessageSquare className="w-4 h-4" />}
                        {model.type === 'image' && <Image className="w-4 h-4" />}
                        {model.type === 'multimodal' && <Zap className="w-4 h-4" />}
                        <span>{model.name}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Mode Selection */}
            <div>
              <label className="text-sm font-medium mb-2 block">Chat Mode</label>
              <Select value={chatMode} onValueChange={handleModeChange}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {availableModes.map((mode) => {
                    const modeInfo = getModeInfo(mode);
                    return (
                      <SelectItem key={mode} value={mode}>
                        <div className="flex items-center gap-2">
                          {modeInfo.icon}
                          <span>{modeInfo.label}</span>
                        </div>
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Model Capabilities */}
          {currentModel && (
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm text-gray-600">Capabilities:</span>
              {currentModel.capabilities?.slice(0, 4).map((capability) => (
                <Badge key={capability} variant="secondary" className="text-xs">
                  {capability}
                </Badge>
              ))}
              {currentModel.capabilities && currentModel.capabilities.length > 4 && (
                <Badge variant="secondary" className="text-xs">
                  +{currentModel.capabilities.length - 4} more
                </Badge>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Chat Messages */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {currentModeInfo.icon}
            {currentModeInfo.label} Chat
          </CardTitle>
          <CardDescription>{currentModeInfo.description}</CardDescription>
        </CardHeader>
        
        <CardContent>
          {/* Messages Container */}
          <div className="space-y-4 min-h-[300px] max-h-[500px] overflow-y-auto mb-4 p-4 border rounded-lg bg-gray-50">
            {messages.length === 0 ? (
              <div className="text-center text-gray-500 py-8">
                <div className="mb-2">{currentModeInfo.icon}</div>
                <p>Start a conversation in {currentModeInfo.label.toLowerCase()} mode</p>
                <p className="text-sm mt-1">{currentModeInfo.description}</p>
              </div>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] p-3 rounded-lg ${
                      message.type === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'bg-white border shadow-sm'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs opacity-70">
                        {message.type === 'user' ? 'You' : message.modelUsed}
                      </span>
                      <Badge variant="outline" className="text-xs">
                        {message.mode}
                      </Badge>
                    </div>
                    
                    <p className="text-sm">{message.content}</p>
                    
                    {message.imageUrl && (
                      <div className="mt-2">
                        <img
                          src={message.imageUrl}
                          alt="Generated image"
                          className="max-w-full h-auto rounded border"
                        />
                      </div>
                    )}
                    
                    <div className="text-xs opacity-50 mt-1">
                      {message.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))
            )}
            
            {isGenerating && (
              <div className="flex justify-start">
                <div className="bg-white border shadow-sm p-3 rounded-lg">
                  <div className="flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span className="text-sm">
                      {chatMode === 'image' ? 'Generating image...' : 'Generating response...'}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Input Area */}
          <div className="space-y-3">
            <div className="flex gap-2">
              <Textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={
                  chatMode === 'image' 
                    ? 'Describe the image you want to generate...'
                    : 'Type your message...'
                }
                className="flex-1 min-h-[60px] resize-none"
                disabled={isGenerating || !currentModel}
              />
              <Button
                onClick={handleSendMessage}
                disabled={!inputValue.trim() || isGenerating || !currentModel}
                size="lg"
                className="px-6"
              >
                {isGenerating ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </Button>
            </div>
            
            {!currentModel && (
              <p className="text-sm text-red-600">Please select a model to start chatting</p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}