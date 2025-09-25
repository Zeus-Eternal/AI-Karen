"use client";

import { useCallback, useEffect, useState } from "react";

interface UseVoiceInputOptions {
  enabled: boolean;
  isRecording: boolean;
  startRecording: () => Promise<void> | void;
  stopRecording: () => void;
}

export const useVoiceInput = ({
  enabled,
  isRecording,
  startRecording,
  stopRecording,
}: UseVoiceInputOptions) => {
  const [isSupported, setIsSupported] = useState(false);

  useEffect(() => {
    if (!enabled) {
      setIsSupported(false);
      return;
    }
    setIsSupported(typeof navigator !== "undefined" && !!navigator.mediaDevices);
  }, [enabled]);

  const handleVoiceStart = useCallback(async () => {
    if (!enabled || !isSupported || isRecording) return;
    await startRecording();
  }, [enabled, isSupported, isRecording, startRecording]);

  const handleVoiceStop = useCallback(() => {
    if (!isRecording) return;
    stopRecording();
  }, [isRecording, stopRecording]);

  return {
    isVoiceSupported: isSupported,
    handleVoiceStart,
    handleVoiceStop,
  };
};
