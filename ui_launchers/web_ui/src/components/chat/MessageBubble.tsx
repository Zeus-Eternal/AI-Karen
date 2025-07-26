
"use client";

import type { ChatMessage, KarenSettings } from '@/lib/types';
import ForecastWidget from '../widgets/ForecastWidget';
import { widgetRefId } from '@/lib/utils';
import { useState, useRef, useEffect, useCallback } from 'react';
import { Avatar } from '@/components/ui/avatar';
import { Card, CardContent } from '@/components/ui/card';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { Button } from '@/components/ui/button';
// Imported User and Bot icons
import { User, Bot, Tags, Zap as KnowledgeGraphIcon, Speaker, StopCircle } from 'lucide-react';
import { format } from 'date-fns';
import { useToast } from "@/hooks/use-toast";
import { KAREN_SETTINGS_LS_KEY, DEFAULT_KAREN_SETTINGS } from '@/lib/constants';


interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const isSystemMessage = message.role === 'system';
  const { toast } = useToast();

  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [hasAutoplayed, setHasAutoplayed] = useState(false);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const [availableVoices, setAvailableVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [preferredVoiceURI, setPreferredVoiceURI] = useState<string | null>(null);

  const clearUtteranceHandlers = (utt: SpeechSynthesisUtterance | null) => {
    if (utt) {
      utt.onstart = null;
      utt.onend = null;
      utt.onerror = null;
    }
  };

  const loadVoicesAndPreferences = useCallback(() => {
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      const systemVoices = window.speechSynthesis.getVoices();
      setAvailableVoices(systemVoices); 

      try {
        const settingsStr = localStorage.getItem(KAREN_SETTINGS_LS_KEY);
        if (settingsStr) {
          const settings: Partial<KarenSettings> = JSON.parse(settingsStr);
          setPreferredVoiceURI(settings.ttsVoiceURI === undefined ? DEFAULT_KAREN_SETTINGS.ttsVoiceURI : settings.ttsVoiceURI);
        } else {
          setPreferredVoiceURI(DEFAULT_KAREN_SETTINGS.ttsVoiceURI);
        }
      } catch (error) {
        console.error("Error loading TTS preferences from localStorage:", error);
        setPreferredVoiceURI(DEFAULT_KAREN_SETTINGS.ttsVoiceURI);
      }
    }
  }, []); 

  useEffect(() => {
    loadVoicesAndPreferences(); 
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      window.speechSynthesis.addEventListener('voiceschanged', loadVoicesAndPreferences);
      return () => {
        window.speechSynthesis.removeEventListener('voiceschanged', loadVoicesAndPreferences);
      };
    }
  }, [loadVoicesAndPreferences]); 


  const handlePlayAudio = useCallback(() => {
    if (typeof window === 'undefined' || !window.speechSynthesis) {
      toast({
        variant: "destructive",
        title: "TTS Not Supported",
        description: "Your browser does not support text-to-speech.",
      });
      return;
    }
    
    if (!message.content || typeof message.content !== 'string' || message.content.trim() === '') {
        console.warn("Attempted to play empty or invalid message content:", message);
        toast({
            variant: "destructive",
            title: "TTS Error",
            description: "Cannot play empty message.",
        });
        return;
    }

    if (isPlayingAudio && utteranceRef.current && utteranceRef.current.text === message.content) {
      clearUtteranceHandlers(utteranceRef.current); 
      window.speechSynthesis.cancel(); 
      setIsPlayingAudio(false); 
      utteranceRef.current = null; 
    } else {
      window.speechSynthesis.cancel(); 

      const newUtterance = new SpeechSynthesisUtterance(message.content);
      
      const currentSystemVoices = window.speechSynthesis.getVoices(); 
      if (preferredVoiceURI && currentSystemVoices.length > 0) {
        const selectedVoice = currentSystemVoices.find(voice => voice.voiceURI === preferredVoiceURI);
        if (selectedVoice) {
          newUtterance.voice = selectedVoice;
        } else {
          console.warn(`Preferred voice URI "${preferredVoiceURI}" not found. Using default.`);
        }
      } else if (currentSystemVoices.length === 0 && preferredVoiceURI) {
        console.warn("No voices available at playback time, but a preferred voice was set. Using system default if TTS proceeds.");
      }

      newUtterance.onstart = () => {
        setIsPlayingAudio(true);
      };

      newUtterance.onend = () => {
        setIsPlayingAudio(false);
        if (utteranceRef.current === newUtterance) { 
          utteranceRef.current = null;
        }
        clearUtteranceHandlers(newUtterance);
      };

      newUtterance.onerror = (event: SpeechSynthesisErrorEvent) => {
        console.error("SpeechSynthesis Error Event:", { 
          type: event.type,
          error: event.error, 
          utteranceText: event.utterance?.text.substring(0, 100) + "...", // Log first 100 chars
          charIndex: event.charIndex,
          elapsedTime: event.elapsedTime,
          name: event.name,
          eventObject: event 
        });
        
        let errorDescription = "Could not play audio. Your browser's speech engine encountered an issue.";
        if (event && typeof event.error === 'string' && event.error.trim() !== "") {
          errorDescription = `Could not play audio. Error: ${event.error}.`;
        } else if (event && event.utterance) { 
           errorDescription = `Could not play audio for this message. Your browser's speech engine encountered an issue. It might be related to the specific voice or message content.`;
        }

        toast({
          variant: "destructive",
          title: "TTS Error",
          description: errorDescription,
        });
        setIsPlayingAudio(false);
        if (utteranceRef.current === newUtterance) { 
          utteranceRef.current = null;
        }
        clearUtteranceHandlers(newUtterance);
      };
      
      utteranceRef.current = newUtterance; 
      window.speechSynthesis.speak(newUtterance);
    }
  }, [message.content, toast, preferredVoiceURI, isPlayingAudio, loadVoicesAndPreferences]);


  useEffect(() => {
    if (message.shouldAutoPlay && message.role === 'assistant' && !isUser && !hasAutoplayed && typeof window !== 'undefined' && window.speechSynthesis) {
      const attemptAutoplay = () => {
        const freshVoices = window.speechSynthesis.getVoices(); 
        if (freshVoices.length > 0) {
          if(availableVoices.length === 0 && !hasAutoplayed) setAvailableVoices(freshVoices); 
          handlePlayAudio();
          setHasAutoplayed(true); 
        } else if (!hasAutoplayed) { 
          const onVoicesChangedForAutoplay = () => {
            window.speechSynthesis.removeEventListener('voiceschanged', onVoicesChangedForAutoplay);
            const currentVoices = window.speechSynthesis.getVoices();
            if (currentVoices.length > 0) {
              if(availableVoices.length === 0 && !hasAutoplayed) setAvailableVoices(currentVoices); 
              handlePlayAudio();
              setHasAutoplayed(true);
            } else {
              console.warn("Autoplay: Voices still not available after voiceschanged event.");
            }
          };
          window.speechSynthesis.addEventListener('voiceschanged', onVoicesChangedForAutoplay);
        }
      };

      const initialVoices = window.speechSynthesis.getVoices();
      if (initialVoices.length > 0) {
         if(availableVoices.length === 0 && !hasAutoplayed) setAvailableVoices(initialVoices); 
         attemptAutoplay();
      } else if (!hasAutoplayed) {
         const onVoicesChangedForAutoplayOnce = () => {
            window.speechSynthesis.removeEventListener('voiceschanged', onVoicesChangedForAutoplayOnce);
            attemptAutoplay();
         };
         window.speechSynthesis.addEventListener('voiceschanged', onVoicesChangedForAutoplayOnce);
      }
    }
  }, [message.shouldAutoPlay, message.role, isUser, hasAutoplayed, handlePlayAudio, availableVoices, message.content, loadVoicesAndPreferences]);


  useEffect(() => {
    return () => {
      if (utteranceRef.current && utteranceRef.current.text === message.content && window.speechSynthesis && window.speechSynthesis.speaking) {
        clearUtteranceHandlers(utteranceRef.current); 
        window.speechSynthesis.cancel(); 
      }
       if (utteranceRef.current && utteranceRef.current.text === message.content) {
         utteranceRef.current = null; 
      }
    };
  }, [message.content]); 


  return (
    <div className={`flex items-start gap-3 my-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <Avatar className="h-10 w-10 self-start shrink-0 flex items-center justify-center bg-muted rounded-full">
          <Bot className="h-5 w-5 text-primary" />
        </Avatar>
      )}
      <Card className={`max-w-xl shadow-md rounded-xl ${isUser ? 'bg-primary text-primary-foreground' : 'bg-card'}`}>
        <CardContent className="p-3 md:p-4">
          <div className="flex justify-between items-start">
            <p className={`whitespace-pre-wrap text-sm md:text-base flex-1 ${
              isSystemMessage ? 'text-foreground' : ''
            }`}>
              {message.content}
            </p>
            {message.widget && !isUser && (
              <div className="mt-2 w-full">
                <ForecastWidget refId={widgetRefId(message.widget)} />
              </div>
            )}
            {!isUser && message.role === 'assistant' && (
              <Button
                variant="ghost"
                size="icon"
                onClick={handlePlayAudio}
                className="ml-2 h-7 w-7 text-muted-foreground hover:text-foreground shrink-0"
                aria-label={isPlayingAudio ? "Stop audio playback" : "Play message audio"}
              >
                {isPlayingAudio ? <StopCircle className="h-4 w-4" /> : <Speaker className="h-4 w-4" />}
              </Button>
            )}
          </div>
          {!isUser && message.aiData && (Object.keys(message.aiData).length > 0) && !isSystemMessage && (
            <Accordion type="single" collapsible className="w-full mt-2.5">
              <AccordionItem value="ai-details" className="border-t border-border/50 pt-2">
                <AccordionTrigger className="text-xs hover:no-underline py-1.5 text-muted-foreground data-[state=open]:text-accent-foreground justify-start gap-1">
                  Show Details
                </AccordionTrigger>
                <AccordionContent className="pt-2 space-y-3">
                  {message.aiData.keywords && message.aiData.keywords.length > 0 && (
                    <div>
                      <div className="flex items-center text-xs font-medium mb-1.5 text-foreground/80">
                        <Tags className="h-3.5 w-3.5 mr-1.5 text-secondary" />
                        Extracted Keywords
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {message.aiData.keywords.map((keyword, index) => (
                          <Badge key={index} variant="secondary" className="text-xs font-normal bg-secondary/15 text-secondary-foreground hover:bg-secondary/25 px-2 py-0.5">
                            {keyword}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  {message.aiData.knowledgeGraphInsights && (
                     <div>
                      <div className="flex items-center text-xs font-medium mb-1.5 text-foreground/80">
                        <KnowledgeGraphIcon className="h-3.5 w-3.5 mr-1.5 text-secondary" />
                        Knowledge Insights
                      </div>
                      <p className="text-xs text-muted-foreground">{message.aiData.knowledgeGraphInsights}</p>
                    </div>
                  )}
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          )}
           <p className={`text-xs mt-2.5 ${isUser ? 'text-primary-foreground/70 text-right' : 'text-muted-foreground text-left'}`}>
            {format(new Date(message.timestamp), 'HH:mm')}
          </p>
        </CardContent>
      </Card>
      {isUser && (
         <Avatar className="h-10 w-10 self-start shrink-0 flex items-center justify-center bg-muted rounded-full">
          <User className="h-5 w-5 text-secondary" />
        </Avatar>
      )}
    </div>
  );
}
