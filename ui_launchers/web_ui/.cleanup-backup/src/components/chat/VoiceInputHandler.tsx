"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Mic, Square, Loader2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { safeError } from "@/lib/safe-console";

interface VoiceInputHandlerProps {
  isRecording: boolean;
  isEnabled: boolean;
  onStart: () => void;
  onStop: () => void;
  onTranscript: (transcript: string) => void;
  onError?: (error: string) => void;
  className?: string;
}

interface SpeechRecognitionEvent {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionResultList {
  length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
  length: number;
  item(index: number): SpeechRecognitionAlternative;
  [index: number]: SpeechRecognitionAlternative;
  isFinal: boolean;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start(): void;
  stop(): void;
  abort(): void;
  onstart: ((this: SpeechRecognition, ev: Event) => any) | null;
  onend: ((this: SpeechRecognition, ev: Event) => any) | null;
  onerror: ((this: SpeechRecognition, ev: Event) => any) | null;
  onresult: ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => any) | null;
}

declare global {
  interface Window {
    SpeechRecognition: new () => SpeechRecognition;
    webkitSpeechRecognition: new () => SpeechRecognition;
  }
}

export const VoiceInputHandler: React.FC<VoiceInputHandlerProps> = ({
  isRecording,
  isEnabled,
  onStart,
  onStop,
  onTranscript,
  onError,
  className = "",
}) => {
  const [isSupported, setIsSupported] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [confidence, setConfidence] = useState(0);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const { toast } = useToast();

  // Check for speech recognition support
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    setIsSupported(!!SpeechRecognition);
    
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';
      
      recognition.onstart = () => {
        setIsProcessing(true);
        setTranscript("");
        setConfidence(0);
      };
      
      recognition.onend = () => {
        setIsProcessing(false);
        if (isRecording) {
          onStop();
        }
      };
      
      recognition.onerror = (event: any) => {
        setIsProcessing(false);
        const errorMessage = `Speech recognition error: ${event.error}`;
        onError?.(errorMessage);
        toast({
          title: "Voice input error",
          description: errorMessage,
          variant: "destructive",
        });
      };
      
      recognition.onresult = (event: SpeechRecognitionEvent) => {
        let finalTranscript = "";
        let interimTranscript = "";
        let maxConfidence = 0;
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const result = event.results[i];
          const transcriptText = result[0].transcript;
          const confidence = result[0].confidence;
          
          if (result.isFinal) {
            finalTranscript += transcriptText + " ";
            maxConfidence = Math.max(maxConfidence, confidence);
          } else {
            interimTranscript += transcriptText;
          }
        }
        
        const fullTranscript = (finalTranscript + interimTranscript).trim();
        setTranscript(fullTranscript);
        setConfidence(maxConfidence);
        
        if (finalTranscript) {
          onTranscript(finalTranscript.trim());
        }
      };
      
      recognitionRef.current = recognition;
    }
    
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
    };
  }, [isRecording, onStop, onError, onTranscript, toast]);

  const handleStart = useCallback(() => {
    if (!isSupported) {
      toast({
        title: "Voice input not supported",
        description: "Your browser doesn't support speech recognition",
        variant: "destructive",
      });
      return;
    }
    
    if (recognitionRef.current && !isRecording) {
      try {
        recognitionRef.current.start();
        onStart();
      } catch (error) {
        safeError("Error starting speech recognition:", error);
        onError?.("Failed to start voice input");
      }
    }
  }, [isSupported, isRecording, onStart, onError, toast]);

  const handleStop = useCallback(() => {
    if (recognitionRef.current && isRecording) {
      recognitionRef.current.stop();
      onStop();
    }
  }, [isRecording, onStop]);

  if (!isEnabled) {
    return null;
  }

  return (
    <div className={`voice-input-handler flex items-center gap-2 ${className}`}>
      <Button
        type="button"
        variant={isRecording ? "destructive" : "outline"}
        size="sm"
        onClick={isRecording ? handleStop : handleStart}
        disabled={!isSupported || isProcessing}
        className="h-8 w-8 p-0"
        title={
          !isSupported 
            ? "Voice input not supported" 
            : isRecording 
            ? "Stop recording" 
            : "Start voice input"
        }
      >
        {isProcessing ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : isRecording ? (
          <Square className="h-4 w-4" />
        ) : (
          <Mic className="h-4 w-4" />
        )}
      </Button>

      {isRecording && (
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
            <span className="text-xs text-muted-foreground">Recording...</span>
          </div>
          
          {transcript && (
            <Badge variant="outline" className="text-xs max-w-32 truncate">
              {transcript}
            </Badge>
          )}
          
          {confidence > 0 && (
            <Badge variant="outline" className="text-xs">
              {Math.round(confidence * 100)}%
            </Badge>
          )}
        </div>
      )}

      {!isSupported && (
        <Badge variant="destructive" className="text-xs">
          Not supported
        </Badge>
      )}
    </div>
  );
};

export default VoiceInputHandler;
