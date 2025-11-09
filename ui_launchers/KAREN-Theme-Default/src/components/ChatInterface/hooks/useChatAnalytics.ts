"use client";

import { useState, useCallback, useEffect } from "react";
import { ChatMessage, ChatAnalytics } from "../types";

export const useChatAnalytics = (
  messages: ChatMessage[],
  sessionStartTime: number,
  onAnalyticsUpdate?: (analytics: ChatAnalytics) => void
) => {
  const [analytics, setAnalytics] = useState<ChatAnalytics>({
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
  });

  // Update analytics when messages change
  useEffect(() => {
    const intents = messages
      .map((m) => m.metadata?.intent)
      .filter((v): v is string => typeof v === 'string' && v.length > 0);
    const langs = messages
      .map((m) => m.language)
      .filter((v): v is string => typeof v === 'string' && v.length > 0);

    const newAnalytics: ChatAnalytics = {
      totalMessages: messages.length,
      userMessages: messages.filter((m) => m.role === "user").length,
      assistantMessages: messages.filter((m) => m.role === "assistant").length,
      averageResponseTime:
        Math.round(
          messages.reduce((acc, m) => acc + (m.metadata?.latencyMs || 0), 0) /
            messages.filter((m) => m.metadata?.latencyMs).length
        ) || 0,
      averageConfidence:
        Math.round(
          (messages.reduce((acc, m) => acc + (m.metadata?.confidence || 0), 0) /
            messages.filter((m) => m.metadata?.confidence).length) *
            100
        ) || 0,
      totalTokens: messages.reduce(
        (acc, m) => acc + (m.metadata?.tokens || 0),
        0
      ),
      totalCost: messages.reduce((acc, m) => acc + (m.metadata?.cost || 0), 0),
      sessionDuration: Math.round((Date.now() - sessionStartTime) / 1000),
      topTopics: [...new Set(intents)].slice(0, 5),
      codeLanguages: [...new Set(langs)],
      errorRate:
        Math.round(
          (messages.filter((m) => m.status === "error").length /
            messages.length) *
            100
        ) || 0,
    };

    setAnalytics(newAnalytics);
    if (onAnalyticsUpdate) {
      onAnalyticsUpdate(newAnalytics);
    }
  }, [messages, sessionStartTime, onAnalyticsUpdate]);

  // Reset analytics
  const resetAnalytics = useCallback(() => {
    const resetAnalytics: ChatAnalytics = {
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
    setAnalytics(resetAnalytics);
    if (onAnalyticsUpdate) {
      onAnalyticsUpdate(resetAnalytics);
    }
  }, [onAnalyticsUpdate]);

  return {
    analytics,
    resetAnalytics,
  };
};