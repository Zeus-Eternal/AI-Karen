
// src/components/chat/ChatInterface.tsx
"use client";

import type { ChatMessage, KarenSettings } from '@/lib/types';
import { useState, useRef, useEffect, FormEvent, useCallback } from 'react';
import { Input } from '@/components/ui/input';
import { sanitizeInput } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Loader2, SendHorizontal, Mic, MicOff, AlertTriangle, Sparkles } from 'lucide-react';
import { 
  handleUserMessage, 
  handleUserMessageWithKarenBackend,
  getSuggestedStarter, 
  type HandleUserMessageResult 
} from '@/app/actions';
import { MessageBubble } from './MessageBubble';
import { useToast } from "@/hooks/use-toast";
import { KAREN_SETTINGS_LS_KEY, DEFAULT_KAREN_SETTINGS, KAREN_SUGGESTED_FACTS_LS_KEY } from '@/lib/constants';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const viewportRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  const [isRecording, setIsRecording] = useState(false);
  const recognitionRef = useRef<any>(null);
  const [speechRecognitionSupported, setSpeechRecognitionSupported] = useState(true);
  const [micPermissionGranted, setMicPermissionGranted] = useState<boolean | null>(null);
  const [shouldSubmitVoiceInput, setShouldSubmitVoiceInput] = useState(false);
  const [lastInputMethod, setLastInputMethod] = useState<'voice' | 'text'>('text');
  const [isSuggestingStarter, setIsSuggestingStarter] = useState(false);
  const [activeListenMode, setActiveListenMode] = useState(DEFAULT_KAREN_SETTINGS.activeListenMode);
  const micReactivationTimerRef = useRef<NodeJS.Timeout | null>(null);


  useEffect(() => {
    setMessages([
      {
        id: 'karen-initial-' + Date.now(),
        role: 'assistant',
        content: "Hello! I'm Karen, your intelligent assistant. How can I help you today?",
        timestamp: new Date(),
        aiData: {
          knowledgeGraphInsights: "Karen AI aims to be a human-like AI assistant with advanced memory and learning capabilities. You can ask me about various topics!",
        },
        shouldAutoPlay: false,
      },
    ]);

    // Load activeListenMode setting
    try {
        const settingsStr = localStorage.getItem(KAREN_SETTINGS_LS_KEY);
        if (settingsStr) {
            const parsedSettings = JSON.parse(settingsStr) as Partial<KarenSettings>;
            setActiveListenMode(parsedSettings.activeListenMode ?? DEFAULT_KAREN_SETTINGS.activeListenMode);
        }
    } catch (e) {
        console.error("Failed to load activeListenMode from localStorage", e);
    }
    // Listen for settings changes from other tabs/components
    const handleStorageChange = (event: StorageEvent) => {
        if (event.key === KAREN_SETTINGS_LS_KEY && event.newValue) {
            try {
                const parsedSettings = JSON.parse(event.newValue) as Partial<KarenSettings>;
                 if (typeof parsedSettings.activeListenMode === 'boolean') {
                    setActiveListenMode(parsedSettings.activeListenMode);
                }
            } catch (e) {
                 console.error("Failed to parse settings from storage event for activeListenMode", e);
            }
        }
    };
    window.addEventListener('storage', handleStorageChange);
    return () => {
        window.removeEventListener('storage', handleStorageChange);
        if (micReactivationTimerRef.current) {
            clearTimeout(micReactivationTimerRef.current);
        }
    };

  }, []);

  const handleSubmit = useCallback(async (eventDetails?: { isVoiceSubmission?: boolean }) => {
    if (!input.trim() || isLoading) return;

    const isVoice = eventDetails?.isVoiceSubmission || lastInputMethod === 'voice';
    if (!eventDetails?.isVoiceSubmission) {
      setLastInputMethod('text');
    }

    const userMessage: ChatMessage = {
      id: 'user-' + Date.now(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    const currentInput = sanitizeInput(input.trim());
    setInput('');
    setIsLoading(true);
    let parsedSettings: KarenSettings = DEFAULT_KAREN_SETTINGS;

    try {
      const conversationHistory = messages
        .filter(msg => msg.role !== 'system')
        .map(msg => `${msg.role === 'user' ? 'User' : 'Karen'}: ${msg.content}`)
        .join('\n');
      
      let storedSettings: KarenSettings | null = null;
      try {
        const settingsStr = localStorage.getItem(KAREN_SETTINGS_LS_KEY);
        if (settingsStr) {
          const partialSettings = JSON.parse(settingsStr) as Partial<KarenSettings>;
          parsedSettings = {
            ...DEFAULT_KAREN_SETTINGS,
            ...partialSettings,
            notifications: {
              ...DEFAULT_KAREN_SETTINGS.notifications,
              ...(partialSettings.notifications || {}),
            },
            personalFacts: Array.isArray(partialSettings.personalFacts) ? partialSettings.personalFacts : DEFAULT_KAREN_SETTINGS.personalFacts,
            ttsVoiceURI: partialSettings.ttsVoiceURI === undefined ? DEFAULT_KAREN_SETTINGS.ttsVoiceURI : partialSettings.ttsVoiceURI,
            customPersonaInstructions: typeof partialSettings.customPersonaInstructions === 'string' ? partialSettings.customPersonaInstructions : DEFAULT_KAREN_SETTINGS.customPersonaInstructions,
            activeListenMode: typeof partialSettings.activeListenMode === 'boolean' ? partialSettings.activeListenMode : DEFAULT_KAREN_SETTINGS.activeListenMode,
          };
          storedSettings = parsedSettings;
          // Update local state for activeListenMode if it changed in localStorage
          if (typeof parsedSettings.activeListenMode === 'boolean' && parsedSettings.activeListenMode !== activeListenMode) {
            setActiveListenMode(parsedSettings.activeListenMode);
          }
        }
      } catch (error) {
        console.error("Failed to parse settings from localStorage", error);
      }
      
      const totalMessagesSoFar = messages.length; 

      const result: HandleUserMessageResult = await handleUserMessage(currentInput, conversationHistory, storedSettings, totalMessagesSoFar);
      
      const newMessages: ChatMessage[] = [];
      const autoPlayThisMessage = isVoice;

      if (result.acknowledgement) {
        newMessages.push({
          id: 'assistant-ack-' + Date.now(),
          role: 'assistant',
          content: result.acknowledgement,
          timestamp: new Date(),
          shouldAutoPlay: autoPlayThisMessage, 
        });
      }

      newMessages.push({
        id: 'assistant-final-' + Date.now(),
        role: 'assistant',
        content: result.finalResponse,
        timestamp: new Date(),
        aiData: result.aiDataForFinalResponse,
        shouldAutoPlay: autoPlayThisMessage,
      });

      if (result.proactiveSuggestion) {
        newMessages.push({
          id: 'assistant-proactive-' + Date.now(),
          role: 'assistant',
          content: result.proactiveSuggestion,
          timestamp: new Date(),
          shouldAutoPlay: autoPlayThisMessage, 
        });
      }

      setMessages((prev) => [...prev, ...newMessages]);

      // Active Listen Mode: Re-activate mic if conditions are met
      if (autoPlayThisMessage && parsedSettings.activeListenMode && newMessages.some(m => m.role === 'assistant')) {
        if (micReactivationTimerRef.current) clearTimeout(micReactivationTimerRef.current);
        micReactivationTimerRef.current = setTimeout(() => {
            // Check again if still in voice mode and not loading, and not recording
            if (!isLoading && !isRecording && speechRecognitionSupported && micPermissionGranted) {
                 console.log("Active Listen: Re-activating mic.");
                 handleMicClick();
            }
        }, 1500); // Delay to allow TTS to potentially start/user to process
      }


      if (result.summaryWasGenerated) {
        if (parsedSettings.notifications.enabled && parsedSettings.notifications.alertOnSummaryReady) {
          toast({
            title: "Conversation Summary Ready!",
            description: "A summary of your recent conversation has been generated.",
            duration: 7000,
          });
        }
      }

      if (result.suggestedNewFacts && result.suggestedNewFacts.length > 0) {
         try {
            const storedSuggestedFactsRaw = localStorage.getItem(KAREN_SUGGESTED_FACTS_LS_KEY);
            let existingSuggestedFacts: string[] = [];
            if (storedSuggestedFactsRaw) {
                existingSuggestedFacts = JSON.parse(storedSuggestedFactsRaw);
            }
            const updatedFacts = Array.from(new Set([...existingSuggestedFacts, ...(result.suggestedNewFacts || [])]));
            localStorage.setItem(KAREN_SUGGESTED_FACTS_LS_KEY, JSON.stringify(updatedFacts));
            window.dispatchEvent(new CustomEvent('karen-suggested-facts-updated'));
         } catch (error) {
            console.error("Failed to save/update suggested facts to localStorage:", error);
         }

         toast({
          title: "💡 Karen has some suggestions!",
          description: "Check the 'Facts' settings or Comms Center to review new info Karen offered to remember.",
          duration: 7000,
        });
      }


      if (result.aiDataForFinalResponse?.knowledgeGraphInsights && 
          parsedSettings.notifications.enabled && 
          parsedSettings.notifications.alertOnNewInsights) {
        toast({
          title: "✨ New Insight from Karen!",
          description: "Check her latest message for details.",
          duration: 5000,
        });
      }

    } catch (error) {
      console.error("Error sending message in ChatInterface handleSubmit:", error);
      
      setMessages((prevMessages) => prevMessages.filter(m => m.id !== userMessage.id));
      
      let errorMessageContent = "Failed to get a response from Karen. Please check your connection or try again later.";
      if (error instanceof Error && error.message) {
        if (error.message.startsWith("Karen: ")) { 
          errorMessageContent = error.message;
        } else if (error.message.includes("API key not valid")) {
          errorMessageContent = `Karen: There seems to be an issue with the API key. Please go to Settings > API Key for setup instructions. The key needs to be in a .env file at your project root, and the Genkit server must be restarted.`;
        } else if (
          error.message.includes("INVALID_ARGUMENT") &&
          error.message.includes("Schema validation failed") &&
          error.message.includes("(root): must be object") &&
          /Provided data:\s*null/.test(error.message) 
        ) {
          errorMessageContent = `Karen: I'm having a little trouble formulating a response right now. This can sometimes happen if the request is very complex or if content filters are active. Could you try rephrasing your request?`;
        } else {
          errorMessageContent = `Karen: I encountered an issue processing your request. Details: ${error.message.substring(0,150)}... Please try again.`;
        }
      }
       toast({
        variant: "destructive",
        title: "Processing Error",
        description: errorMessageContent.startsWith("Karen: ") ? errorMessageContent.substring(7) : errorMessageContent,
      });
      
      const systemErrorMessage: ChatMessage = {
        id: 'error-' + Date.now(),
        role: 'system',
        content: errorMessageContent,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, systemErrorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, [input, isLoading, messages, toast, lastInputMethod, activeListenMode, micPermissionGranted, speechRecognitionSupported]); // Added dependencies

  useEffect(() => {
    const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognitionAPI) {
      setSpeechRecognitionSupported(false);
      console.warn('SpeechRecognition API not supported in this browser.');
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
      console.error('Speech recognition error:', event.error, event.message);
      let errorTitle = 'Speech Recognition Error';
      let errorMessage = 'An unexpected error occurred during speech recognition.';
      
      switch (event.error) {
          case 'no-speech': errorMessage = 'No speech was detected. Please ensure your microphone is active and try again.'; break;
          case 'audio-capture': errorMessage = 'Audio capture failed. Please ensure your microphone is working and selected correctly.'; break;
          case 'not-allowed':
              errorTitle = 'Microphone Access Denied';
              errorMessage = 'Microphone access was denied. Enable it in browser settings and refresh.';
              setMicPermissionGranted(false);
              break;
          case 'aborted': break; 
          case 'network': errorMessage = 'Network error with speech service. Check connection.'; break;
          case 'service-not-allowed':
              errorTitle = 'Speech Service Unavailable';
              errorMessage = 'Speech recognition service unavailable/not allowed by browser/OS.';
              setSpeechRecognitionSupported(false);
              break;
          case 'bad-grammar': errorMessage = 'Could not understand. Speak more clearly.'; break;
          case 'language-not-supported':
              errorTitle = 'Language Not Supported';
              errorMessage = `Language (en-US) not supported by your browser's speech service.`;
              setSpeechRecognitionSupported(false);
              break;
          default: if (event.message) { errorMessage = `Error: ${event.message}`; } break;
      }
      
      if (event.error !== 'aborted' && event.error !== 'no-speech') { // Don't toast for these common, less critical errors
        toast({ variant: 'destructive', title: errorTitle, description: errorMessage });
      }
      setIsRecording(false); 
    };

    recognitionInstance.onend = () => {
      setIsRecording(false);
      setShouldSubmitVoiceInput(true); // Always attempt to submit after STT ends
    };
    
    recognitionRef.current = recognitionInstance;

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.onresult = null;
        recognitionRef.current.onerror = null;
        recognitionRef.current.onend = null;
        recognitionRef.current.stop();
      }
       if (micReactivationTimerRef.current) {
            clearTimeout(micReactivationTimerRef.current);
      }
    };
  }, [toast]); 


  useEffect(() => {
    if (shouldSubmitVoiceInput) {
      // Direct check of input from state, and isLoading
      if (input.trim() && !isLoading) {
        handleSubmit({isVoiceSubmission: true});
      }
      setShouldSubmitVoiceInput(false); 
    }
  }, [shouldSubmitVoiceInput, input, isLoading, handleSubmit]);


  useEffect(() => {
    if (viewportRef.current) {
      viewportRef.current.scrollTo({ top: viewportRef.current.scrollHeight, behavior: 'smooth' });
    }
  }, [messages]);


  const handleMicClick = async () => {
    if (!speechRecognitionSupported) {
      toast({
        variant: "destructive",
        title: "Audio Input Not Supported",
        description: "Your browser does not support speech recognition.",
      });
      return;
    }
    
    if (!recognitionRef.current) return;

    if (isRecording) {
      recognitionRef.current.stop(); 
    } else {
      try {
        let permissionState = 'prompt';
        if (navigator.permissions) {
          try {
            const micPermission = await navigator.permissions.query({ name: 'microphone' as PermissionName });
            permissionState = micPermission.state;
          } catch (permError) {
            console.warn("Could not query microphone permission state:", permError);
          }
        }

        if (permissionState === 'denied') {
          setMicPermissionGranted(false);
          toast({
            variant: 'destructive',
            title: 'Microphone Access Denied',
            description: 'Please enable microphone permissions in your browser settings to use voice input.',
          });
          return;
        }
        
        if (permissionState !== 'granted') {
          try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            stream.getTracks().forEach(track => track.stop()); 
            setMicPermissionGranted(true);
          } catch (err) {
             console.error('Error accessing microphone:', err);
            if (err instanceof Error && (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError')) {
                setMicPermissionGranted(false);
                toast({
                  variant: 'destructive',
                  title: 'Microphone Access Denied',
                  description: 'Please enable microphone permissions in your browser settings to use voice input.',
                });
            } else {
                toast({
                  variant: 'destructive',
                  title: 'Microphone Error',
                  description: 'Could not access the microphone. Ensure it is connected and not in use by another application.',
                });
            }
            return; 
          }
        } else {
           setMicPermissionGranted(true); 
        }
        
        setLastInputMethod('voice');
        setInput(''); 
        recognitionRef.current.start();
        setIsRecording(true);
        toast({
          title: "Listening...",
          description: "Using your browser's speech recognition. Stops on pause or click.",
        });

      } catch (err) { 
        console.error('Unexpected error in handleMicClick:', err);
        toast({
            variant: 'destructive',
            title: 'Audio Input Error',
            description: 'An unexpected error occurred while trying to start voice input.',
        });
      }
    }
  };
  
  const showMicPermissionAlert = micPermissionGranted === false && !isRecording;
  
  const handleFormSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    handleSubmit();
  };

  const handleSuggestStarter = async () => {
    setIsSuggestingStarter(true);
    try {
      const starter = await getSuggestedStarter("a curious and insightful assistant");
      const starterMessage: ChatMessage = {
        id: 'assistant-starter-' + Date.now(),
        role: 'assistant',
        content: `Here's an idea to get us talking: "${starter}"`,
        timestamp: new Date(),
        shouldAutoPlay: false,
      };
      setMessages(prev => [...prev, starterMessage]);
    } catch (error) {
      console.error("Error suggesting starter:", error);
      toast({
        variant: "destructive",
        title: "Suggestion Error",
        description: "Could not get a conversation starter at this time.",
      });
    } finally {
      setIsSuggestingStarter(false);
    }
  };


  return (
    <div className="flex flex-col flex-1 min-h-0">
      <ScrollArea className="flex-1 p-4 md:p-6" viewportRef={viewportRef}>
        <div className="max-w-4xl mx-auto w-full space-y-1 pb-4">
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
        </div>
      </ScrollArea>
      <div className="border-t border-border p-3 md:p-4 bg-background/80 backdrop-blur-sm sticky bottom-0">
        {showMicPermissionAlert && (
          <Alert variant="destructive" className="max-w-4xl mx-auto mb-3">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Microphone Access Denied</AlertTitle>
            <AlertDescription>
              Karen AI needs microphone access to enable voice input. Please enable it in your browser settings and refresh the page if necessary.
            </AlertDescription>
          </Alert>
        )}
        <div className="max-w-4xl mx-auto mb-2 flex justify-center">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleSuggestStarter}
            disabled={isLoading || isSuggestingStarter || isRecording}
            className="shadow-sm hover:shadow-md transition-shadow duration-150 ease-in-out rounded-lg border-border/70 hover:border-border"
          >
            {isSuggestingStarter ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="mr-2 h-4 w-4 text-primary/80" />
            )}
            {isSuggestingStarter ? "Getting idea..." : "Need an idea? Get a starter"}
          </Button>
        </div>
        <form onSubmit={handleFormSubmit} className="max-w-4xl mx-auto flex gap-2 md:gap-3 items-center">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className={`h-11 w-11 md:h-12 md:w-12 p-0 rounded-lg shrink-0 ${isRecording ? 'text-destructive animate-pulse' : 'text-muted-foreground hover:text-foreground'}`}
            onClick={handleMicClick}
            aria-label={isRecording ? "Stop recording" : "Start recording"}
            disabled={isLoading || !speechRecognitionSupported}
          >
            {isRecording ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
          </Button>
          <Input
            type="text"
            value={input}
            onChange={(e) => {
              setInput(e.target.value);
              if (!isRecording) setLastInputMethod('text');
            }}
            placeholder={isRecording ? "Listening..." : (speechRecognitionSupported ? "Ask Karen anything or use mic..." : "Ask Karen anything (mic not supported)...")}
            className="flex-1 text-sm md:text-base h-11 md:h-12 rounded-lg focus-visible:ring-primary focus-visible:ring-offset-0"
            disabled={isLoading || (isRecording && !input)} 
            aria-label="Chat input"
          />
          <Button
            type="submit"
            size="icon"
            className="h-11 w-11 md:h-12 md:w-12 p-0 rounded-lg bg-primary hover:bg-primary/90 shrink-0"
            disabled={isLoading || !input.trim() || isRecording}
            aria-label="Send message"
          >
            {isLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : <SendHorizontal className="h-5 w-5" />}
          </Button>
        </form>
      </div>
    </div>
  );
}
