"use client";

import { useCallback, useMemo } from "react";

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
  const isSupported = useMemo(() => {
    if (!enabled) {
      return false;
    }

    return typeof navigator !== "undefined" && Boolean(navigator.mediaDevices);
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
