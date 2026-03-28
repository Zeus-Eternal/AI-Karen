"use client";

import type { ChatMessage } from '@/lib/types';
import { useState, useRef, useEffect, FormEvent, useCallback } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Loader2, SendHorizontal, Mic, MicOff, Sparkles, Bot, Cpu, Square } from 'lucide-react';
import { getSuggestedStarter } from '@/app/actions';
import { MessageBubble } from './MessageBubble';
import { useToast } from "@/hooks/use-toast";
import { ApiError, apiClient } from '@/lib/api';
import { useAuth } from '@/lib/useAuth';
import { authService } from '@/lib/auth';

const PROCESSING_INPUT_STATES = [
  'Karen is reviewing your request...',
  'Karen is checking context and recent conversation...',
  'Karen is aligning tools, memory, and provider routing...',
  'Karen is reasoning through the next response...',
];

declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

const createSessionId = (): string => {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }

  const randomHex = (length: number) =>
    Array.from({ length }, () => Math.floor(Math.random() * 16).toString(16)).join('');

  return [
    randomHex(8),
    randomHex(4),
    `4${randomHex(3)}`,
    `${(8 + Math.floor(Math.random() * 4)).toString(16)}${randomHex(3)}`,
    randomHex(12),
  ].join('-');
};

export default function ChatInterface() {
  const sessionIdRef = useRef(createSessionId());
  const submitInFlightRef = useRef(false);
  const { user, isAuthenticated, isLoading: isAuthLoading } = useAuth();
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
  const [processingInputIndex, setProcessingInputIndex] = useState(0);
  const [isEditingDuringProcessing, setIsEditingDuringProcessing] = useState(false);
  const activeRequestControllerRef = useRef<AbortController | null>(null);

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

  const getDegradedResponseMessage = (error: unknown): string => {
    if (error instanceof ApiError) {
      const detail = error.message?.trim();

      if (detail && !/^HTTP \d+: /i.test(detail)) {
        return detail;
      }

      if (error.status >= 500) {
        return 'Karen is running in degraded mode right now. A response model is not available yet, so I cannot complete this message until local or remote model routing recovers.';
      }

      if (error.status === 401 || error.status === 403) {
        return 'Karen could not use the requested provider with your current session permissions. Sign in again or switch to an available model.';
      }
    }

    return 'Karen is running in degraded mode right now and could not complete this message. Check model availability and try again.';
  };

  const preferredAddressName =
    typeof user?.preferences?.preferred_address_name === 'string'
      ? user.preferences.preferred_address_name.trim()
      : '';
  const fullName = user?.full_name?.trim() || '';
  const emailName = user?.email?.split('@')[0]?.trim() || '';
  const displayName = (() => {
    const candidate = preferredAddressName || fullName || emailName || '';
    return candidate || null;
  })();
  const firstNameOption = fullName.split(/\s+/).filter(Boolean)[0] || displayName || null;
  const shouldPromptForPreferredName = Boolean(
    isAuthenticated &&
    !preferredAddressName &&
    fullName &&
    firstNameOption &&
    fullName.includes(' ') &&
    firstNameOption.toLowerCase() !== fullName.toLowerCase()
  );

  const recentMessages = messages
    .filter((message) => message.role === 'user' || message.role === 'assistant')
    .slice(-6)
    .map((message) => ({
      role: message.role,
      content: message.content,
    }));
  
  useEffect(() => {
    if (isAuthLoading) {
      return;
    }

    const greeting = displayName
      ? shouldPromptForPreferredName && firstNameOption
        ? `Hello there! I'm Karen. ${fullName}, how may I assist you today? Would you rather I address you as ${firstNameOption} or ${fullName}?`
        : `Hello there! I'm Karen. ${displayName}, how may I assist you today?`
      : "Hello! I'm Karen, your intelligent assistant. How can I help you today?";

    setMessages((currentMessages) => {
      if (currentMessages.length > 1) {
        return currentMessages;
      }

      if (
        currentMessages.length === 1 &&
        !currentMessages[0].id.startsWith('karen-initial-')
      ) {
        return currentMessages;
      }

      return [
        {
          id: 'karen-initial-' + Date.now(),
          role: 'assistant',
          content: greeting,
          timestamp: new Date(),
          metadata: shouldPromptForPreferredName && firstNameOption
            ? {
                addressPreferencePrompt: true,
                addressOptions: [firstNameOption, fullName],
              }
            : undefined,
        },
      ];
    });
  }, [displayName, firstNameOption, fullName, isAuthLoading, shouldPromptForPreferredName]);

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

  const savePreferredAddressName = useCallback(async (preferredName: string) => {
    if (!user) {
      return false;
    }

    const nextPreferences = {
      ...(user.preferences || {}),
      preferred_address_name: preferredName,
    };

    await apiClient.put('/api/auth/me', {
      preferences: nextPreferences,
    });

    authService.updateCurrentUser({
      preferences: nextPreferences,
    });

    await apiClient.post('/api/memory/commit', {
      user_id: user.user_id,
      text: `The user prefers to be addressed as ${preferredName}.`,
      tags: ['personal_fact', 'preferred_name', 'user_preference'],
      importance: 9,
      decay: 'pinned',
    }).catch(() => undefined);

    return true;
  }, [user]);

  const handleSubmit = useCallback(async () => {
    if (!input.trim() || isLoading || isAuthLoading || submitInFlightRef.current) return;

    const trimmedInput = input.trim();
    const lastAssistantMessage = [...messages].reverse().find((message) => message.role === 'assistant');
    const addressOptions = Array.isArray(lastAssistantMessage?.metadata?.addressOptions)
      ? (lastAssistantMessage.metadata.addressOptions as string[])
      : [];
    const matchedAddressOption = addressOptions.find(
      (option) => option.trim().toLowerCase() === trimmedInput.toLowerCase()
    );

    if (lastAssistantMessage?.metadata?.addressPreferencePrompt && matchedAddressOption) {
      setIsLoading(true);
      try {
        await savePreferredAddressName(matchedAddressOption);

        const userMessage: ChatMessage = {
          id: 'user-' + Date.now(),
          role: 'user',
          content: trimmedInput,
          timestamp: new Date(),
        };
        const assistantMessage: ChatMessage = {
          id: 'assistant-pref-' + Date.now(),
          role: 'assistant',
          content: `Understood. I'll address you as ${matchedAddressOption} from now on.`,
          timestamp: new Date(),
        };

        setMessages((prev) => [...prev, userMessage, assistantMessage]);
        setInput('');
      } catch {
        toast({
          title: 'Preference update failed',
          description: 'Karen could not save your preferred form of address.',
          variant: 'destructive',
        });
      } finally {
        setIsLoading(false);
      }
      return;
    }

    const userMessage: ChatMessage = {
      id: 'user-' + Date.now(),
      role: 'user',
      content: trimmedInput,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    submitInFlightRef.current = true;
    setIsLoading(true);
    setIsEditingDuringProcessing(false);
    setProcessingInputIndex(0);

    try {
      const controller = new AbortController();
      activeRequestControllerRef.current = controller;

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
              conversation_profile: {
                display_name: displayName,
                preferred_address_name: preferredAddressName || undefined,
                source: 'authenticated_profile',
              },
              recent_messages: recentMessages,
            }
          : {
              conversation_profile: {
                display_name: displayName,
                preferred_address_name: preferredAddressName || undefined,
                source: displayName ? 'derived_profile' : 'unknown',
              },
              recent_messages: recentMessages,
            },
        preferred_llm_provider: selectedProvider || undefined,
        preferred_model: selectedModel || undefined,
        session_id: sessionIdRef.current,
      }, {
        signal: controller.signal,
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
      if (error instanceof DOMException && error.name === 'AbortError') {
        return;
      }

      const assistantMessage: ChatMessage = {
        id: 'assistant-error-' + Date.now(),
        role: 'assistant',
        content: getDegradedResponseMessage(error),
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
      toast({
        title: 'Chat request failed',
        description: getDegradedResponseMessage(error),
        variant: 'destructive',
      });
      console.error('Chat request failed:', error);
    } finally {
      submitInFlightRef.current = false;
      activeRequestControllerRef.current = null;
      setIsLoading(false);
      setIsEditingDuringProcessing(false);
      setProcessingInputIndex(0);
    }

  }, [displayName, input, isAuthLoading, isAuthenticated, isLoading, messages, preferredAddressName, recentMessages, savePreferredAddressName, selectedProvider, selectedModel, toast, user]); 

  useEffect(() => {
    if (!isLoading || isEditingDuringProcessing) {
      return;
    }

    const timer = window.setInterval(() => {
      setProcessingInputIndex((current) => (current + 1) % PROCESSING_INPUT_STATES.length);
    }, 1800);

    return () => {
      window.clearInterval(timer);
    };
  }, [isEditingDuringProcessing, isLoading]);

  const stopActiveRequest = useCallback(() => {
    submitInFlightRef.current = false;
    activeRequestControllerRef.current?.abort();
    activeRequestControllerRef.current = null;
    setIsLoading(false);
  }, []);

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
    if (isLoading) {
      if (input.trim()) {
        stopActiveRequest();
      }
      return;
    }
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

  const displayedInputValue = isLoading && !isEditingDuringProcessing
    ? PROCESSING_INPUT_STATES[processingInputIndex]
    : input;
  const showStopButton = isLoading && input.trim().length > 0;
  
  return (
    <div className="flex flex-col flex-1">
      <ScrollArea className="flex-1 p-4 md:p-6" viewportRef={viewportRef}>
        <div className="w-full space-y-1 pb-4">
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
        </div>
      </ScrollArea>
      <div id="chat-input-area">
      <div className="chat-input-container border-t border-border p-3 md:p-4 bg-background/80 backdrop-blur-sm sticky bottom-0">
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
            disabled={isLoading || isAuthLoading || !speechRecognitionSupported}
          >
            {isRecording ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
          </Button>
          <Input
            type="text"
            value={displayedInputValue}
            onChange={(e) => {
              if (isLoading && !isEditingDuringProcessing) {
                return;
              }
              setInput(e.target.value);
            }}
            onKeyDown={(e) => {
              if (
                isLoading &&
                !isEditingDuringProcessing &&
                (e.key.length === 1 || e.key === 'Backspace' || e.key === 'Delete')
              ) {
                setIsEditingDuringProcessing(true);
                setInput('');
              }
            }}
            onPaste={(e) => {
              if (isLoading && !isEditingDuringProcessing) {
                e.preventDefault();
                const pastedText = e.clipboardData.getData('text');
                setIsEditingDuringProcessing(true);
                setInput(pastedText);
              }
            }}
            placeholder={
              isAuthLoading
                ? "Loading your profile..."
                : isLoading && isEditingDuringProcessing
                  ? "Type while Karen is still processing..."
                  : "Ask Karen anything..."
            }
            className="flex-1 bg-[#292929]"
            disabled={isAuthLoading}
          />
          <Button
            type={isLoading ? 'button' : 'submit'}
            size="icon"
            onClick={isLoading ? stopActiveRequest : undefined}
            disabled={
              isAuthLoading ||
              isRecording ||
              (!isLoading && !input.trim()) ||
              (isLoading && !showStopButton)
            }
          >
            {isLoading ? (
              showStopButton ? <Square className="h-4 w-4" /> : <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <SendHorizontal className="h-5 w-5" />
            )}
          </Button>
        </form>
      </div>
      </div>
    </div>
  );
}
