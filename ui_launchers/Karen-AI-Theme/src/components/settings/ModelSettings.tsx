"use client";

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle, Bot, KeyRound } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert';
import { Label } from '../ui/label';
import { Input } from '../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import OllamaModelManager from './OllamaModelManager';

type AiProvider = 'gemini' | 'openai' | 'anthropic' | 'ollama';

export default function ModelSettings() {
  const [selectedProvider, setSelectedProvider] = useState<AiProvider>('ollama');

  const getProviderName = (provider: AiProvider) => {
    switch (provider) {
        case 'gemini': return 'Google Gemini';
        case 'openai': return 'OpenAI';
        case 'anthropic': return 'Anthropic';
        default: return '';
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center"><Bot className="mr-2 h-5 w-5"/>AI Model Configuration</CardTitle>
        <CardDescription>
          Configure the AI provider and model Karen should use for generating responses. (Conceptual UI).
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-2">
          <Label htmlFor="ai-provider">AI Provider</Label>
          <Select value={selectedProvider} onValueChange={(value) => setSelectedProvider(value as AiProvider)}>
            <SelectTrigger id="ai-provider">
              <SelectValue placeholder="Select an AI provider" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="gemini">Google Gemini (Cloud)</SelectItem>
              <SelectItem value="openai">OpenAI (Cloud)</SelectItem>
              <SelectItem value="anthropic">Anthropic (Cloud)</SelectItem>
              <SelectItem value="ollama">Ollama (Local Models)</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {selectedProvider === 'ollama' && <OllamaModelManager />}

        {(selectedProvider === 'gemini' || selectedProvider === 'openai' || selectedProvider === 'anthropic') && (
           <div className="space-y-6 p-4 border-l-2 border-primary/20">
             <div className="space-y-2">
                <Label htmlFor="cloud-model">Select Model</Label>
                 <Select disabled>
                    <SelectTrigger id="cloud-model">
                        <SelectValue placeholder="Select a model" />
                    </SelectTrigger>
                    <SelectContent>
                        {selectedProvider === 'gemini' && <>
                            <SelectItem value="gemini-1.5-pro">Gemini 1.5 Pro</SelectItem>
                            <SelectItem value="gemini-1.5-flash">Gemini 1.5 Flash</SelectItem>
                        </>}
                         {selectedProvider === 'openai' && <>
                            <SelectItem value="gpt-4o">GPT-4o</SelectItem>
                            <SelectItem value="gpt-4-turbo">GPT-4 Turbo</SelectItem>
                        </>}
                         {selectedProvider === 'anthropic' && <>
                            <SelectItem value="claude-3-opus">Claude 3 Opus</SelectItem>
                            <SelectItem value="claude-3-sonnet">Claude 3 Sonnet</SelectItem>
                        </>}
                    </SelectContent>
                </Select>
             </div>

             <div className="space-y-2">
                <Label htmlFor="cloud-api-key" className="flex items-center">
                    <KeyRound className="mr-2 h-4 w-4 text-primary/80" /> API Key
                </Label>
                <Input
                    id="cloud-api-key"
                    type="password"
                    placeholder={`Enter your ${getProviderName(selectedProvider)} API Key`}
                    disabled
                />
             </div>
             
             <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Backend Configuration Needed</AlertTitle>
                <AlertDescription className="text-xs">
                    Using cloud-based models requires configuring the corresponding API keys on the server-side, as well as updating the backend logic to call the selected provider's API. This UI is a conceptual placeholder.
                </AlertDescription>
            </Alert>
           </div>
        )}
      </CardContent>
    </Card>
  );
}
