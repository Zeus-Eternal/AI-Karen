// ui_launchers/KAREN-Theme-Default/src/components/chat/VoiceInputHandler.tsx
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
  lang?: string; // default 'en-US'
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
  onerror: ((this: SpeechRecognition, ev: any) => any) | null;
  onresult: ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => any) | null;
}

declare global {
  interface Window {
    SpeechRecognition?: new () => SpeechRecognition;
    webkitSpeechRecognition?: new () => SpeechRecognition;
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
  lang = "en-US",
}) => {
  const { toast } = useToast();

  const [isSupported, setIsSupported] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [displayTranscript, setDisplayTranscript] = useState("");
  const [confidence, setConfidence] = useState(0);
  const [permissionDenied, setPermissionDenied] = useState(false);

  const recognitionRef = useRef<SpeechRecognition | null>(null);

  // SSR guard
  const getSR = useCallback(() => {
    if (typeof window === "undefined") return undefined;
    return window.SpeechRecognition || window.webkitSpeechRecognition;
  }, []);

  // Initialize SpeechRecognition
  useEffect(() => {
    const SR = getSR();
    const supported = Boolean(SR);
    setIsSupported(supported);

    if (!supported) return;

    const recognition = new SR!();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = lang;

    recognition.onstart = () => {
      setIsProcessing(true);
      setDisplayTranscript("");
      setConfidence(0);
    };

    recognition.onend = () => {
      setIsProcessing(false);
      // If UI state still says "recording", sync up and notify parent
      if (isRecording) {
        onStop();
      }
    };

    recognition.onerror = (event: any) => {
      setIsProcessing(false);
      // Handle mic permission explicitly
      if (event?.error === "not-allowed" || event?.error === "service-not-allowed") {
        setPermissionDenied(true);
      }
      const errorMessage = `Speech recognition error: ${event?.error ?? "unknown"}`;
      safeError(errorMessage);
      onError?.(errorMessage);
      toast({
        title: "Voice input error",
        description: errorMessage,
        variant: "destructive",
      });
    };

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let finalChunk = "";
      let interimChunk = "";
      let maxConf = 0;

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        const alt = result[0];
        if (!alt) continue;

        if (result.isFinal) {
          finalChunk += alt.transcript + " ";
          maxConf = Math.max(maxConf, alt.confidence ?? 0);
        } else {
          interimChunk += alt.transcript;
        }
      }

      const full = (finalChunk + interimChunk).trim();
      setDisplayTranscript(full);
      if (maxConf > 0) setConfidence(maxConf);

      // Only emit final chunks upward (prevents flooding)
      if (finalChunk.trim()) {
        onTranscript(finalChunk.trim());
      }
    };

    recognitionRef.current = recognition;

    return () => {
      try {
        recognitionRef.current?.abort();
      } catch (e) {
        // ignore abort errors
      }
      recognitionRef.current = null;
    };
  }, [getSR, isRecording, onStop, onError, onTranscript, toast, lang]);

  // Start recording
  const handleStart = useCallback(async () => {
    if (!isSupported) {
      toast({
        title: "Voice input not supported",
        description: "Your browser doesn't support speech recognition.",
        variant: "destructive",
      });
      return;
    }

    // Hint to request mic permission early (helps UX on some browsers)
    try {
      if (navigator?.mediaDevices?.getUserMedia) {
        // Don't await indefinitely—race with a short timeout
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 1500);
        await navigator.mediaDevices.getUserMedia({ audio: true, video: false }).catch(() => {});
        clearTimeout(timeout);
      }
    } catch {
      // ignore; SR may still prompt
    }

    if (recognitionRef.current && !isRecording) {
      try {
        recognitionRef.current.start();
        onStart();
      } catch (error) {
        safeError("Error starting speech recognition:", error);
        const msg = "Failed to start voice input";
        onError?.(msg);
        toast({ title: "Voice input error", description: msg, variant: "destructive" });
      }
    }
  }, [isSupported, isRecording, onStart, onError, toast]);

  // Stop recording
  const handleStop = useCallback(() => {
    if (recognitionRef.current && isRecording) {
      try {
        recognitionRef.current.stop();
      } catch {
        // ignore
      }
      onStop();
    }
  }, [isRecording, onStop]);

  if (!isEnabled) return null;

  return (
    <div className={`voice-input-handler flex items-center gap-2 ${className}`}>
      <Button
        type="button"
        variant={isRecording ? "destructive" : "outline"}
        size="sm"
        onClick={isRecording ? handleStop : handleStart}
        disabled={!isSupported || isProcessing}
        className="h-8 w-8 p-0"
        aria-label={
          !isSupported ? "Voice input not supported" : isRecording ? "Stop recording" : "Start voice input"
        }
        title={
          !isSupported ? "Voice input not supported" : isRecording ? "Stop recording" : "Start voice input"
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
        <div className="flex items-center gap-2 min-w-0">
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
            <span className="text-xs text-muted-foreground sm:text-sm md:text-base">Recording…</span>
          </div>

          {displayTranscript && (
            <Badge
              variant="outline"
              className="text-xs max-w-48 truncate sm:max-w-64 md:max-w-80"
              title={displayTranscript}
            >
              {displayTranscript}
            </Badge>
          )}

          {confidence > 0 && (
            <Badge variant="outline" className="text-xs sm:text-sm md:text-base" title="Recognition confidence">
              {Math.round(confidence * 100)}%
            </Badge>
          )}
        </div>
      )}

      {!isSupported && (
        <Badge variant="destructive" className="text-xs sm:text-sm md:text-base" title="Not supported">
          Voice Unsupported
        </Badge>
      )}

      {permissionDenied && (
        <Badge variant="destructive" className="text-xs sm:text-sm md:text-base" title="Microphone permission denied">
          Mic Permission Denied
        </Badge>
      )}
    </div>
  );
};

export default VoiceInputHandler;
