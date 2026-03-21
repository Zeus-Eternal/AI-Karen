"use client";

import type { ChatMessage, KarenSettings } from '@/lib/types';
import { useState, useRef, useEffect, FormEvent, useCallback } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Loader2, SendHorizontal, Mic, MicOff, Sparkles } from 'lucide-react';
import { getSuggestedStarter } from '@/app/actions';
import { MessageBubble } from './MessageBubble';
import { useToast } from "@/hooks/use-toast";

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
  const [shouldSubmitVoiceInput, setShouldSubmitVoiceInput] = useState(false);
  const [isSuggestingStarter, setIsSuggestingStarter] = useState(false);
  
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

    // Simulate a backend response
    setTimeout(() => {
      const assistantMessage: ChatMessage = {
        id: 'assistant-mock-' + Date.now(),
        role: 'assistant',
        content: "This is a mock response. The front-end is ready to be connected to a backend service.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setIsLoading(false);
    }, 1000);

  }, [input, isLoading]); 

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


  useEffect(() => {
    if (viewportRef.current) {
      viewportRef.current.scrollTo({ top: viewportRef.current.scrollHeight, behavior: 'smooth' });
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
        <div className="w-full mb-2 flex justify-center">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleSuggestStarter}
            disabled={isLoading || isSuggestingStarter || isRecording}
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
            className="flex-1"
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
