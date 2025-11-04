/**
 * CopilotKit-enhanced Memory Editor Component (Production)
 * - Fixes unclosed hooks/blocks
 * - Strong typing + accessibility
 * - Debounced AI suggestions
 * - Clean Tailwind UI (shadcn/ui compatible)
 * - Safe fetch + errors surfaced
 */

"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import { CopilotTextarea } from "@copilotkit/react-textarea";
import { useCopilotAction, useCopilotReadable } from "@copilotkit/react-core";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";

type MemoryType = "fact" | "preference" | "context";

interface MemoryGridRow {
  id: string;
  content: string;
  type: MemoryType;
  confidence: number; // 0..1
  last_accessed: string;
  relevance_score: number;
  semantic_cluster: string;
  relationships: string[];
  timestamp: number;
  user_id: string;
  session_id?: string;
  tenant_id?: string;
}

interface MemoryEditorProps {
  memory: MemoryGridRow | null;
  onSave: (updatedMemory: Partial<MemoryGridRow>) => Promise<void>;
  onCancel: () => void;
  onDelete?: (memoryId: string) => Promise<void>;
  isOpen: boolean;
  userId: string;
  tenantId?: string;
}

type AISuggestionType = "enhancement" | "categorization" | "relationship" | "correction";

interface AISuggestion {
  type: AISuggestionType;
  content: string;
  confidence: number;
  reasoning: string;
}

const CLUSTERS = ["technical", "personal", "work", "general"] as const;

export const MemoryEditor: React.FC<MemoryEditorProps> = ({
  memory,
  onSave,
  onCancel,
  onDelete,
  isOpen,
  userId,
  tenantId,
}) => {
  const [editedContent, setEditedContent] = useState("");
  const [editedType, setEditedType] = useState<MemoryType>("context");
  const [editedConfidence, setEditedConfidence] = useState(0.8);
  const [editedCluster, setEditedCluster] = useState<string>("general");

  const [aiSuggestions, setAiSuggestions] = useState<AISuggestion[]>([]);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize form when memory changes / modal opens
  useEffect(() => {
    if (!isOpen) return;
    if (memory) {
      setEditedContent(memory.content ?? "");
      setEditedType(memory.type ?? "context");
      setEditedConfidence(
        typeof memory.confidence === "number" ? memory.confidence : 0.8
      );
      setEditedCluster(memory.semantic_cluster ?? "general");
    } else {
      setEditedContent("");
      setEditedType("context");
      setEditedConfidence(0.8);
      setEditedCluster("general");
    }
    setError(null);
    setAiSuggestions([]);
  }, [memory, isOpen]);

  // Expose current memory context to CopilotKit
  useCopilotReadable({
    description: "Current memory being edited in the MemoryEditor modal",
    value: memory
      ? {
          id: memory.id,
          content: memory.content,
          type: memory.type,
          cluster: memory.semantic_cluster,
          relationships: memory.relationships,
        }
      : null,
  });

  // Fetch helpers
  const safeJsonPost = useCallback(
    async (url: string, payload: unknown) => {
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(`HTTP ${res.status}: ${text || res.statusText}`);
      }
      return res.json();
    },
    []
  );

  // Generate AI suggestions for memory enhancement
  const generateAISuggestions = useCallback(
    async (content?: string, context?: string) => {
      try {
        if (!(content || editedContent).trim()) return;
        setIsLoadingSuggestions(true);
        setError(null);
        const data = await safeJsonPost("/api/memory/ai-suggestions", {
          content: content ?? editedContent,
          context: context ?? "",
          memory_id: memory?.id,
          user_id: userId,
          tenant_id: tenantId,
          current_type: editedType,
          current_cluster: editedCluster,
        });
        setAiSuggestions(Array.isArray(data?.suggestions) ? data.suggestions : []);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to generate AI suggestions"
        );
      } finally {
        setIsLoadingSuggestions(false);
      }
    },
    [editedContent, editedType, editedCluster, memory?.id, tenantId, userId, safeJsonPost]
  );

  // Get category suggestions from AI
  const getCategorySuggestions = useCallback(
    async (content: string) => {
      if (!content.trim()) return;
      try {
        const data = await safeJsonPost("/api/memory/categorize", {
          content,
          user_id: userId,
          tenant_id: tenantId,
        });
        const suggestedType = (data?.suggested_type ?? "").toLowerCase();
        const suggestedCluster = (data?.suggested_cluster ?? "").toLowerCase();
        if (["fact", "preference", "context"].includes(suggestedType)) {
          setEditedType(suggestedType as MemoryType);
        }
        if (suggestedCluster) {
          setEditedCluster(suggestedCluster);
        }
        return {
          type: suggestedType as MemoryType | undefined,
          cluster: suggestedCluster || undefined,
          confidence: data?.confidence as number | undefined,
        };
      } catch {
        // Soft-fail: keep UI smooth
        return {};
      }
    },
    [tenantId, userId, safeJsonPost]
  );

  // CopilotKit actions
  useCopilotAction({
    name: "enhanceMemory",
    description: "Enhance and improve memory content with AI suggestions",
    parameters: [
      { name: "content", type: "string", description: "The memory content to enhance" },
      { name: "context", type: "string", description: "Additional context about the memory" },
    ],
    handler: async ({ content, context }) => {
      await generateAISuggestions(content, context);
    },
  });

  useCopilotAction({
    name: "categorizeMemory",
    description: "Suggest the best category and cluster for a memory",
    parameters: [{ name: "content", type: "string", description: "The memory to categorize" }],
    handler: async ({ content }) => {
      await getCategorySuggestions(content);
    },
  });

  // Debounced autosuggest while typing
  useEffect(() => {
    if (!editedContent.trim()) return;
    const handle = setTimeout(() => {
      // Passive suggestions; do not block typing
      generateAISuggestions(editedContent, "");
    }, 800);
    return () => clearTimeout(handle);
  }, [editedContent, generateAISuggestions]);

  // Apply an AI suggestion
  const applySuggestion = useCallback((suggestion: AISuggestion) => {
    switch (suggestion.type) {
      case "enhancement":
      case "correction":
        setEditedContent(suggestion.content);
        break;
      case "categorization": {
        // Expected simple "Type: X\nCluster: Y" format (fallback-safe)
        const lines = suggestion.content.split("\n");
        for (const line of lines) {
          if (line.toLowerCase().startsWith("type:")) {
            const v = line.split(":")[1]?.trim().toLowerCase();
            if (v && ["fact", "preference", "context"].includes(v)) {
              setEditedType(v as MemoryType);
            }
          } else if (line.toLowerCase().startsWith("cluster:")) {
            const c = line.split(":")[1]?.trim();
            if (c) setEditedCluster(c);
          }
        }
        break;
      }
      case "relationship":
        // Could open a relationship editor in a future pass
        break;
    }
  }, []);

  // Save
  const handleSave = useCallback(async () => {
    try {
      setIsSaving(true);
      setError(null);
      const payload: Partial<MemoryGridRow> = {
        content: editedContent,
        type: editedType,
        confidence: Math.max(0, Math.min(1, editedConfidence)),
        semantic_cluster: editedCluster,
        last_accessed: new Date().toISOString(),
      };
      await onSave(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save memory");
    } finally {
      setIsSaving(false);
    }
  }, [editedContent, editedType, editedConfidence, editedCluster, onSave]);

  // Delete
  const handleDelete = useCallback(async () => {
    if (!memory || !onDelete) return;
    // eslint-disable-next-line no-alert
    if (window.confirm("Delete this memory? This cannot be undone.")) {
      try {
        await onDelete(memory.id);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to delete memory");
      }
    }
  }, [memory, onDelete]);

  if (!isOpen) return null;

  return (
    <div
      data-kari="memory-editor"
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      aria-modal="true"
      role="dialog"
      aria-labelledby="memory-editor-title"
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" onClick={onCancel} />

      {/* Modal */}
      <div className="relative z-10 w-full max-w-4xl rounded-2xl bg-background shadow-xl ring-1 ring-border focus:outline-none">
        {/* Header */}
        <div className="flex items-center justify-between border-b p-5">
          <div>
            <h2 id="memory-editor-title" className="m-0 text-xl font-semibold">
              {memory ? "Edit Memory" : "Create New Memory"}
            </h2>
            <p className="text-sm text-muted-foreground">
              AI-assisted editing with CopilotKit autosuggestions.
            </p>
          </div>
          <Button variant="ghost" size="icon" aria-label="Close" onClick={onCancel}>
            ×
          </Button>
        </div>

        {/* Body */}
        <div className="grid gap-6 p-5 md:grid-cols-[2fr_1fr]">
          {/* Main editor */}
          <div>
            <div className="mb-4 space-y-2">
              <Label htmlFor="memory-content">Content</Label>
              <CopilotTextarea
                id="memory-content"
                className={cn(
                  "min-h-[140px] w-full resize-y rounded-md border p-3 text-sm",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                )}
                value={editedContent}
                onChange={(e) => setEditedContent(e.target.value)}
                placeholder="Enter memory content... (AI suggestions appear as you type)"
                autosuggestionsConfig={{
                  textareaPurpose: "Memory content editing with AI enhancement",
                  chatApiConfigs: {
                    suggestionsApiConfig: {
                      maxTokens: 250,
                      stop: ["\n"],
                    },
                  },
                }}
              />
            </div>

            <div className="mb-4 grid gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <Label htmlFor="memory-type">Type</Label>
                <select
                  id="memory-type"
                  value={editedType}
                  onChange={(e) => setEditedType(e.target.value as MemoryType)}
                  className="h-9 w-full rounded-md border bg-background px-3 text-sm"
                >
                  <option value="fact">Fact</option>
                  <option value="preference">Preference</option>
                  <option value="context">Context</option>
                </select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="memory-confidence">
                  Confidence ({Math.round(editedConfidence * 100)}%)
                </Label>
                <input
                  id="memory-confidence"
                  type="range"
                  min={0}
                  max={1}
                  step={0.05}
                  value={editedConfidence}
                  onChange={(e) => setEditedConfidence(parseFloat(e.target.value))}
                  className="w-full"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="memory-cluster">Cluster</Label>
                <select
                  id="memory-cluster"
                  value={editedCluster}
                  onChange={(e) => setEditedCluster(e.target.value)}
                  className="h-9 w-full rounded-md border bg-background px-3 text-sm"
                >
                  {CLUSTERS.map((c) => (
                    <option key={c} value={c}>
                      {c[0].toUpperCase() + c.slice(1)}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="mb-2 flex gap-2">
              <Button
                onClick={() => generateAISuggestions()}
                disabled={isLoadingSuggestions || !editedContent.trim()}
              >
                {isLoadingSuggestions ? "Generating…" : "Get AI Suggestions"}
              </Button>
              <Button
                variant="secondary"
                onClick={() => getCategorySuggestions(editedContent)}
                disabled={!editedContent.trim()}
              >
                Auto-Categorize
              </Button>
            </div>

            {error && (
              <div className="mt-3 rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-800">
                {error}
              </div>
            )}
          </div>

          {/* Suggestions panel */}
          <div>
            <h3 className="mb-3 text-base font-semibold">AI Suggestions</h3>
            {isLoadingSuggestions ? (
              <div className="rounded-md border p-4 text-center text-sm text-muted-foreground">
                Generating AI suggestions…
              </div>
            ) : aiSuggestions.length > 0 ? (
              <div className="max-h-[320px] space-y-2 overflow-y-auto pr-1">
                {aiSuggestions.map((s, i) => (
                  <div
                    key={`${s.type}-${i}`}
                    className="rounded-md border bg-muted/30 p-3"
                  >
                    <div className="mb-1 flex items-center justify-between">
                      <span className="text-xs font-bold uppercase text-muted-foreground">
                        {s.type}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {Math.round(s.confidence * 100)}% confidence
                      </span>
                    </div>
                    <div className="mb-2 text-sm">{s.content}</div>
                    {s.reasoning && (
                      <div className="mb-2 text-xs text-muted-foreground">
                        {s.reasoning}
                      </div>
                    )}
                    <Button
                      size="sm"
                      onClick={() => applySuggestion(s)}
                      className="h-7 px-2 text-xs"
                    >
                      Apply
                    </Button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="rounded-md border p-4 text-center text-sm text-muted-foreground">
                Click <em>Get AI Suggestions</em> to see enhancement recommendations.
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t p-5">
          <div>
            {memory && onDelete && (
              <Button variant="destructive" onClick={handleDelete}>
                Delete
              </Button>
            )}
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" onClick={onCancel}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={isSaving || !editedContent.trim()}>
              {isSaving ? "Saving…" : "Save Memory"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MemoryEditor;
