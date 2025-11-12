"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { ChatMessage, CopilotArtifact } from "../types";
import { generateUUID } from "@/lib/uuid";
import { useInputPreservation } from "@/hooks/use-input-preservation";
import { safeDebug, safeError } from "@/lib/safe-console";

export const useChatState = (initialMessages: ChatMessage[] = [], welcomeMessage?: string) => {
  const { preserveInput, restoreInput, clearPreservedInput } = useInputPreservation("chat-interface");
  const [isTyping, setIsTyping] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(() => generateUUID());
  const [conversationId, setConversationId] = useState<string | null>(() => generateUUID());
  const [activeTab, setActiveTab] = useState<"chat" | "code" | "analytics">("chat");
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showRoutingHistory, setShowRoutingHistory] = useState(false);
  const [showCodePreview, setShowCodePreview] = useState(false);
  const [selectedMessages, setSelectedMessages] = useState<Set<string>>(new Set());
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    if (initialMessages.length > 0) {
      return [...initialMessages];
    }

    if (welcomeMessage) {
      return [
        {
          id: `welcome-${Date.now()}`,
          role: "assistant",
          content: welcomeMessage,
          timestamp: new Date(),
          type: "text",
          metadata: { confidence: 1.0 },
        },
      ];
    }

    return [];
  });
  const [inputValue, setInputValue] = useState(() => {
    if (typeof window === "undefined") {
      return "";
    }

    const preserved = restoreInput();
    return preserved ?? "";
  });
  const [codeValue, setCodeValue] = useState("");
  const [copilotArtifacts, setCopilotArtifacts] = useState<CopilotArtifact[]>([]);
  const [selectedText, setSelectedText] = useState("");
  const [sessionStartTime] = useState(() => Date.now());

  // Refs for media recording
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Input preservation
  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  // Preserve input on changes
  useEffect(() => {
    if (inputValue) {
      preserveInput(inputValue);
    }
  }, [inputValue, preserveInput]);

  // Message management
  const addMessage = useCallback((message: ChatMessage) => {
    setMessages(prev => [...prev, message]);
  }, []);

  const updateMessage = useCallback((messageId: string, updates: Partial<ChatMessage>) => {
    setMessages(prev => prev.map(msg =>
      msg.id === messageId ? { ...msg, ...updates } : msg
    ));
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  // Selection management
  const toggleMessageSelection = useCallback((messageId: string) => {
    setSelectedMessages(prev => {
      const newSet = new Set(prev);
      if (newSet.has(messageId)) {
        newSet.delete(messageId);
      } else {
        newSet.add(messageId);
      }
      return newSet;
    });
  }, []);

  const clearSelectedMessages = useCallback(() => {
    setSelectedMessages(new Set());
  }, []);

  // Input management
  const clearInput = useCallback(() => {
    setInputValue("");
    setCodeValue("");
    clearPreservedInput();
  }, [clearPreservedInput]);

  // Voice recording management
  const startRecording = useCallback(async () => {
    if (isRecording) return;

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      const chunks: BlobPart[] = [];
      mediaRecorder.ondataavailable = (event) => {
        chunks.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunks, { type: "audio/wav" });
        // TODO: Implement speech-to-text conversion
        safeDebug("Voice recording stopped, audio blob created:", audioBlob);
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      safeError("Failed to access microphone:", error);
      throw error;
    }
  }, [isRecording]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream
        .getTracks()
        .forEach((track) => track.stop());
      setIsRecording(false);
    }
  }, [isRecording]);

  // Copilot artifact management
  const addCopilotArtifact = useCallback((artifact: CopilotArtifact) => {
    setCopilotArtifacts(prev => [...prev, artifact]);
  }, []);

  const updateCopilotArtifact = useCallback((artifactId: string, updates: Partial<CopilotArtifact>) => {
    setCopilotArtifacts(prev => prev.map(artifact =>
      artifact.id === artifactId ? { ...artifact, ...updates } : artifact
    ));
  }, []);

  const removeCopilotArtifact = useCallback((artifactId: string) => {
    setCopilotArtifacts(prev => prev.filter(artifact => artifact.id !== artifactId));
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      mediaRecorderRef.current?.stop();
      setIsTyping(false);
      setIsRecording(false);
    };
  }, []);

  return {
    // State
    messages,
    isTyping,
    isRecording,
    isAnalyzing,
    sessionId,
    conversationId,
    activeTab,
    isFullscreen,
    showRoutingHistory,
    showCodePreview,
    selectedMessages,
    inputValue,
    codeValue,
    copilotArtifacts,
    selectedText,
    sessionStartTime,
    messagesEndRef,
    mediaRecorderRef,

    // Setters
    setMessages,
    setIsTyping,
    setIsRecording,
    setIsAnalyzing,
    setSessionId,
    setConversationId,
    setActiveTab,
    setIsFullscreen,
    setShowRoutingHistory,
    setShowCodePreview,
    setSelectedMessages,
    setInputValue,
    setCodeValue,
    setCopilotArtifacts,
    setSelectedText,

    // Actions
    addMessage,
    updateMessage,
    clearMessages,
    toggleMessageSelection,
    clearSelectedMessages,
    clearInput,
    startRecording,
    stopRecording,
    addCopilotArtifact,
    updateCopilotArtifact,
    removeCopilotArtifact,
  };
};