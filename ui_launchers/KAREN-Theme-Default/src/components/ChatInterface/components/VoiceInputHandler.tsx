"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Mic, Square, Loader2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { VOICE_TRANSCRIPT_CONFIDENCE_THRESHOLD } from "../constants";

interface VoiceInputHandlerProps {
  isRecording: boolean;
  isEnabled: boolean;
  onStart: () => void | Promise<void>;
  onStop: () => void | Promise<void>;
  onTranscript: (transcript: string) => void;
  onError?: (error: string) => void;
  className?: string;
  showConfidenceBadge?: boolean;
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

type SpeechRecognitionEventHandler<T extends Event> = (this: SpeechRecognition, ev: T) => void;

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
  message?: string;
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start(): void;
  stop(): void;
  abort(): void;
  onstart: SpeechRecognitionEventHandler<Event> | null;
  onend: SpeechRecognitionEventHandler<Event> | null;
  onerror: SpeechRecognitionEventHandler<SpeechRecognitionErrorEvent> | null;
  onresult: SpeechRecognitionEventHandler<SpeechRecognitionEvent> | null;
}



const VoiceInputHandler: React.FC<VoiceInputHandlerProps> = ({
  isRecording,
  isEnabled,
  onStart,
  onStop,
  onTranscript,
  onError,
  className = "",
  showConfidenceBadge = true,
}) => {
  const speechRecognitionCtor = React.useMemo(() => {
    if (typeof window === "undefined") {
      return undefined;
    }
    const win = window as Window & {
      SpeechRecognition?: typeof window.SpeechRecognition;
      webkitSpeechRecognition?: typeof window.SpeechRecognition;
    };
    return win.SpeechRecognition || win.webkitSpeechRecognition;
  }, []);
  const isSupported = Boolean(speechRecognitionCtor);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [confidence, setConfidence] = useState(0);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    const SpeechRecognition = speechRecognitionCtor;
    if (!SpeechRecognition) {
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";

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

    recognition.onerror = (event: Event) => {
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
        const resultConfidence = result[0].confidence;

        if (result.isFinal) {
          finalTranscript += transcriptText + " ";
          maxConfidence = Math.max(maxConfidence, resultConfidence);
        } else {
          interimTranscript += transcriptText;
        }
      }

      const fullTranscript = (finalTranscript + interimTranscript).trim();
      setTranscript(fullTranscript);
      setConfidence(maxConfidence);

      if (finalTranscript && maxConfidence >= VOICE_TRANSCRIPT_CONFIDENCE_THRESHOLD) {
        onTranscript(finalTranscript.trim());
      }
    };

    recognitionRef.current = recognition;

    return () => {
      recognition.abort();
    };
  }, [speechRecognitionCtor, isRecording, onStop, onError, onTranscript, toast]);

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
    <div className={`flex items-center gap-2 ${className}`}>
      <Button
        type="button"
        variant={isRecording ? "destructive" : "outline"}
        size="sm"
        onClick={isRecording ? handleStop : handleStart}
        disabled={!isSupported || isProcessing}
        className="h-8 w-8 p-0">
        {isProcessing ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : isRecording ? (
          <Square className="h-4 w-4" />
        ) : (
          <Mic className="h-4 w-4" />
        )}
      </Button>
      {showConfidenceBadge && transcript && (
        <Badge variant="outline" className="text-[10px]">
          {(confidence * 100).toFixed(0)}% confidence
        </Badge>
      )}
    </div>
  );
};

export default VoiceInputHandler;
