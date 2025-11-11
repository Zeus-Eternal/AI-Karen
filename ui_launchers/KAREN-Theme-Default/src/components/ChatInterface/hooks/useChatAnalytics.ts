"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { ChatMessage, ChatAnalytics } from "../types";

const INITIAL_ANALYTICS: ChatAnalytics = {
  totalMessages: 0,
  userMessages: 0,
  assistantMessages: 0,
  averageResponseTime: 0,
  averageConfidence: 0,
  totalTokens: 0,
  totalCost: 0,
  sessionDuration: 0,
  topTopics: [],
  codeLanguages: [],
  errorRate: 0,
};

const calculateAnalytics = (
  messages: ChatMessage[],
  sessionStartTime: number
): ChatAnalytics => {
  if (messages.length === 0) {
    return {
      ...INITIAL_ANALYTICS,
      sessionDuration: Math.round((Date.now() - sessionStartTime) / 1000),
    };
  }

  const intents = messages
    .map((message) => message.metadata?.intent)
    .filter((value): value is string => typeof value === "string" && value.length > 0);
  const languages = messages
    .map((message) => message.language)
    .filter((value): value is string => typeof value === "string" && value.length > 0);

  const latencySamples = messages.filter((message) => message.metadata?.latencyMs);
  const confidenceSamples = messages.filter((message) => message.metadata?.confidence);

  const totalLatency = latencySamples.reduce(
    (accumulator, message) => accumulator + (message.metadata?.latencyMs ?? 0),
    0
  );
  const totalConfidence = confidenceSamples.reduce(
    (accumulator, message) => accumulator + (message.metadata?.confidence ?? 0),
    0
  );

  return {
    totalMessages: messages.length,
    userMessages: messages.filter((message) => message.role === "user").length,
    assistantMessages: messages.filter((message) => message.role === "assistant").length,
    averageResponseTime:
      Math.round(totalLatency / latencySamples.length) || 0,
    averageConfidence:
      Math.round(((totalConfidence / confidenceSamples.length) || 0) * 100),
    totalTokens: messages.reduce(
      (accumulator, message) => accumulator + (message.metadata?.tokens ?? 0),
      0
    ),
    totalCost: messages.reduce(
      (accumulator, message) => accumulator + (message.metadata?.cost ?? 0),
      0
    ),
    sessionDuration: Math.round((Date.now() - sessionStartTime) / 1000),
    topTopics: [...new Set(intents)].slice(0, 5),
    codeLanguages: [...new Set(languages)],
    errorRate:
      Math.round(
        ((messages.filter((message) => message.status === "error").length || 0) /
          messages.length) *
          100
      ) || 0,
  };
};

export const useChatAnalytics = (
  messages: ChatMessage[],
  sessionStartTime: number,
  onAnalyticsUpdate?: (analytics: ChatAnalytics) => void
) => {
  const [manualAnalytics, setManualAnalytics] = useState<ChatAnalytics | null>(null);
  const [lastResetMessageCount, setLastResetMessageCount] = useState<number | null>(null);

  const computedAnalytics = useMemo(
    () => calculateAnalytics(messages, sessionStartTime),
    [messages, sessionStartTime]
  );

  const analytics = useMemo(() => {
    if (manualAnalytics && lastResetMessageCount !== null) {
      if (messages.length === lastResetMessageCount) {
        return manualAnalytics;
      }
      return computedAnalytics;
    }

    return manualAnalytics ?? computedAnalytics;
  }, [
    computedAnalytics,
    lastResetMessageCount,
    manualAnalytics,
    messages.length,
  ]);

  useEffect(() => {
    if (onAnalyticsUpdate) {
      onAnalyticsUpdate(analytics);
    }
  }, [analytics, onAnalyticsUpdate]);

  const resetAnalytics = useCallback(() => {
    setManualAnalytics(INITIAL_ANALYTICS);
    setLastResetMessageCount(messages.length);

    if (onAnalyticsUpdate) {
      onAnalyticsUpdate(INITIAL_ANALYTICS);
    }
  }, [messages.length, onAnalyticsUpdate]);

  return {
    analytics,
    resetAnalytics,
  };
};