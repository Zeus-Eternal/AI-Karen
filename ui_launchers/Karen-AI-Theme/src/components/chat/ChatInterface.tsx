"use client";

import type { ChatMessage } from '@/lib/types';
import { useState, useRef, useEffect, FormEvent, useCallback } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Loader2, SendHorizontal, Mic, MicOff, Sparkles, Bot, Cpu } from 'lucide-react';
import { getSuggestedStarter } from '@/app/actions';
import { MessageBubble } from './MessageBubble';
import { useToast } from "@/hooks/use-toast";
import { apiClient } from '@/lib/api';
import { useAuth } from '@/lib/useAuth';

declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

export default function ChatInterface() {
  const sessionIdRef = useRef(
    typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
      ? `chat_${crypto.randomUUID()}`
      : `chat_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`
  );
  const { user, isAuthenticated } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const viewportRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  const [isRecording, setIsRecording] = useState(false);
  const recognitionRef = useRef<any>(null);
  const [speechRecognitionSupported, setSpeechRecognitionSupported] = useState(true);
  const [shouldSubmitVoiceInput, setShouldSubmitVoiceInput] = useState(false);
  const [isSuggestingStarter, setIsSuggestingStarter] = useState(false);
  const [modelSettings, setModelSettings] = useState<{
    selected_provider: string;
    selected_model: string;
    providers: Array<{
      id: string;
      display_name: string;
      base_url?: string | null;
      default_base_url?: string | null;
      models: Array<{
        id: string;
        name: string;
      }>;
    }>;
  } | null>(null);
  const [selectedProvider, setSelectedProvider] = useState('');
  const [selectedModel, setSelectedModel] = useState('');
  const [isUpdatingModelSelection, setIsUpdatingModelSelection] = useState(false);

  type ActionParam = Record<string, any>;
  type SuggestedAction = {
    type: string;
    params: ActionParam;
    confidence: number;
    description?: string;
  };
  
  type AssistResponse = {
    answer: string;
    structured_content?: Record<string, any>;
    actions?: SuggestedAction[];
    metadata?: Record<string, any>;
    correlation_id?: string;
  };

  const recentMessages = messages
    .filter((message) => message.role === 'user' || message.role === 'assistant')
    .slice(-6)
    .map((message) => ({
      role: message.role,
      content: message.content,
    }));
  
  useEffect(() => {
    setMessages([
      {
        id: 'karen-initial-' + Date.now(),
        role: 'assistant',
        content: "Hello! I'm the front-end for Karen, your intelligent assistant. How can I help you today?",
        timestamp: new Date(),
      },
    ]);
  }, []);

  useEffect(() => {
    let isMounted = true;

    const loadModelSettings = async () => {
      try {
        const response = await apiClient.get<{
          selected_provider: string;
          selected_model: string;
          providers: Array<{
            id: string;
            display_name: string;
            base_url?: string | null;
            default_base_url?: string | null;
            models: Array<{
              id: string;
              name: string;
            }>;
          }>;
        }>('/api/settings/model');

        if (!isMounted) {
          return;
        }

        setModelSettings(response);
        setSelectedProvider(response.selected_provider || response.providers[0]?.id || '');
        setSelectedModel(response.selected_model || response.providers.find((provider) => provider.id === response.selected_provider)?.models[0]?.id || '');
      } catch {
        // Chat should stay usable even if settings cannot be loaded.
      }
    };

    void loadModelSettings();

    return () => {
      isMounted = false;
    };
  }, []);

  const selectedProviderDetails = modelSettings?.providers.find((provider) => provider.id === selectedProvider) ?? null;
  const availableModels = selectedProviderDetails?.models ?? [];

  const applyModelSelection = useCallback(async (providerId: string, modelId: string) => {
    if (!modelSettings) {
      return;
    }

    const provider = modelSettings.providers.find((item) => item.id === providerId);
    if (!provider || !modelId) {
      return;
    }

    setIsUpdatingModelSelection(true);
    try {
      const response = await apiClient.put<{
        selected_provider: string;
        selected_model: string;
        providers: Array<{
          id: string;
          display_name: string;
          base_url?: string | null;
          default_base_url?: string | null;
          models: Array<{
            id: string;
            name: string;
          }>;
        }>;
      }>('/api/settings/model', {
        provider: providerId,
        model: modelId,
        base_url: (provider.base_url || provider.default_base_url || '').replace(/\/api$/, ''),
      });

      setModelSettings(response);
      setSelectedProvider(response.selected_provider);
      setSelectedModel(response.selected_model);
    } catch {
      toast({
        title: 'Model switch failed',
        description: 'Karen could not update the active provider and model.',
        variant: 'destructive',
      });
    } finally {
      setIsUpdatingModelSelection(false);
    }
  }, [modelSettings, toast]);

  const handleProviderChange = async (providerId: string) => {
    if (!modelSettings) {
      return;
    }

    const provider = modelSettings.providers.find((item) => item.id === providerId);
    const nextModel = provider?.models[0]?.id || '';
    setSelectedProvider(providerId);
    setSelectedModel(nextModel);

    if (nextModel) {
      await applyModelSelection(providerId, nextModel);
    }
  };

  const handleModelChange = async (modelId: string) => {
    setSelectedModel(modelId);
    if (selectedProvider) {
      await applyModelSelection(selectedProvider, modelId);
    }
  };

  const handleSubmit = useCallback(async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: 'user-' + Date.now(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await apiClient.post<AssistResponse>('/api/copilot/assist', {
        user_id: user?.user_id || 'anonymous',
        message: userMessage.content,
        top_k: 6,
        context: isAuthenticated && user
          ? {
              authenticated_user: {
                user_id: user.user_id,
                email: user.email,
                full_name: user.full_name,
                tenant_id: user.tenant_id,
                roles: user.roles,
              },
              recent_messages: recentMessages,
            }
          : {
              recent_messages: recentMessages,
            },
        preferred_llm_provider: selectedProvider || undefined,
        preferred_model: selectedModel || undefined,
        session_id: sessionIdRef.current,
      });

      const assistantMessage: ChatMessage = {
        id: response.correlation_id || 'assistant-' + Date.now(),
        role: 'assistant',
        content: response.answer?.trim() || 'Karen returned an empty response.',
        timestamp: new Date(),
        structuredContent: response.structured_content,
        actions: response.actions,
        metadata: response.metadata,
        aiData: response.metadata?.context && response.metadata.context.length > 0
          ? {
              knowledgeGraphInsights: response.metadata.context
                .map((item: any) => item.preview || item.text)
                .filter(Boolean)
                .join('\n'),
            }
          : undefined,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const assistantMessage: ChatMessage = {
        id: 'assistant-error-' + Date.now(),
        role: 'assistant',
        content: 'Karen could not generate a response with the current model. Check provider settings and try again.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
      toast({
        title: 'Chat request failed',
        description: 'Karen could not reach the selected provider and model for this message.',
        variant: 'destructive',
      });
      console.error('Chat request failed:', error);
    } finally {
      setIsLoading(false);
    }

  }, [input, isAuthenticated, isLoading, messages, recentMessages, selectedProvider, selectedModel, toast, user]); 

  useEffect(() => {
    const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognitionAPI) {
      setSpeechRecognitionSupported(false);
      return;
    }

    const recognitionInstance = new SpeechRecognitionAPI();
    recognitionInstance.continuous = false;
    recognitionInstance.interimResults = true;
    recognitionInstance.lang = 'en-US';

    recognitionInstance.onresult = (event: any) => {
      let interimTranscript = '';
      let finalTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        } else {
          interimTranscript += event.results[i][0].transcript;
        }
      }
      setInput(finalTranscript || interimTranscript);
    };

    recognitionInstance.onerror = (event: any) => {
      setIsRecording(false); 
    };

    recognitionInstance.onend = () => {
      setIsRecording(false);
      setShouldSubmitVoiceInput(true);
    };
    
    recognitionRef.current = recognitionInstance;

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, [toast]); 


  useEffect(() => {
    if (shouldSubmitVoiceInput) {
      if (input.trim() && !isLoading) {
        handleSubmit();
      }
      setShouldSubmitVoiceInput(false); 
    }
  }, [shouldSubmitVoiceInput, input, isLoading, handleSubmit]);


  // Smooth scroll to bottom on new messages
  useEffect(() => {
    if (viewportRef.current) {
      const viewport = viewportRef.current;
      const isAtBottom = viewport.scrollHeight - viewport.scrollTop - viewport.clientHeight < 150;

      if (isAtBottom) {
        requestAnimationFrame(() => {
          viewport.scrollTo({
            top: viewport.scrollHeight,
            behavior: 'smooth'
          });
        });
      }
    }
  }, [messages]);


  const handleMicClick = async () => {
    if (!speechRecognitionSupported) return;
    if (!recognitionRef.current) return;

    if (isRecording) {
      recognitionRef.current.stop(); 
    } else {
      try {
        setInput(''); 
        recognitionRef.current.start();
        setIsRecording(true);
      } catch (err) { 
        console.error('Error starting mic:', err);
      }
    }
  };
  
  const handleFormSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    handleSubmit();
  };

  const handleSuggestStarter = async () => {
    setIsSuggestingStarter(true);
    try {
      const starter = await getSuggestedStarter("a helpful assistant");
      setInput(starter);
    } finally {
      setIsSuggestingStarter(false);
    }
  };
  
  return (
    <div className="flex flex-col flex-1 min-h-0">
      <ScrollArea className="flex-1 p-4 md:p-6" viewportRef={viewportRef}>
        <div className="w-full space-y-1 pb-4">
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
        </div>
      </ScrollArea>
      <div className="border-t border-border p-3 md:p-4 bg-background/80 backdrop-blur-sm sticky bottom-0">
        <div className="mb-2 flex w-full flex-col gap-2 md:flex-row md:items-center md:justify-between">
          {modelSettings && selectedProviderDetails && availableModels.length > 0 && (
            <div className="grid gap-2 md:grid-cols-[minmax(15rem,18rem)_minmax(18rem,22rem)]">
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1.5 whitespace-nowrap text-[11px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
                  <Bot className="h-3.5 w-3.5" />
                  Provider
                </div>
                <Select value={selectedProvider} onValueChange={(value) => void handleProviderChange(value)} disabled={isUpdatingModelSelection}>
                  <SelectTrigger className="h-9 min-w-[11rem] border-border/70 bg-background/80 text-left shadow-sm">
                    <SelectValue placeholder="Select provider" />
                  </SelectTrigger>
                  <SelectContent>
                    {modelSettings.providers.map((provider) => (
                      <SelectItem key={provider.id} value={provider.id}>
                        {provider.display_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1.5 whitespace-nowrap text-[11px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
                  <Cpu className="h-3.5 w-3.5" />
                  Model
                </div>
                <Select value={selectedModel} onValueChange={(value) => void handleModelChange(value)} disabled={isUpdatingModelSelection}>
                  <SelectTrigger className="h-9 min-w-[14rem] border-border/70 bg-background/80 text-left shadow-sm">
                    <SelectValue placeholder="Select model" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableModels.map((model) => (
                      <SelectItem key={model.id} value={model.id}>
                        {model.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          )}

          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleSuggestStarter}
            disabled={isLoading || isSuggestingStarter || isRecording}
            className="self-center md:ml-auto md:self-auto"
          >
            <Sparkles className="mr-2 h-4 w-4" />
            {isSuggestingStarter ? "Getting idea..." : "Need an idea?"}
          </Button>
        </div>
        <form onSubmit={handleFormSubmit} className="w-full flex gap-2 md:gap-3 items-center">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className={`${isRecording ? 'text-destructive animate-pulse' : ''}`}
            onClick={handleMicClick}
            disabled={isLoading || !speechRecognitionSupported}
          >
            {isRecording ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
          </Button>
          <Input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask Karen anything..."
            className="flex-1 bg-[#292929]"
            disabled={isLoading}
          />
          <Button
            type="submit"
            size="icon"
            disabled={isLoading || !input.trim() || isRecording}
          >
            {isLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : <SendHorizontal className="h-5 w-5" />}
          </Button>
        </form>
      </div>
    </div>
  );
}
