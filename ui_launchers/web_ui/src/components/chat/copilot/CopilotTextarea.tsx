"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { CopilotTextarea as CopilotKitTextarea } from "@copilotkit/react-textarea";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

import {
  Lightbulb,
  Code,
  FileText,
  Zap,
  CheckCircle,
  AlertCircle,
  Loader2,
  Sparkles,
} from "lucide-react";
import { useCopilotKit } from "./CopilotKitProvider";
import { useHooks } from "@/contexts/HookContext";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";
import { safeError } from "@/lib/safe-console";

export interface AISuggestion {
  id: string;
  type: "completion" | "refactor" | "debug" | "optimize" | "explain";
  content: string;
  confidence: number;
  reasoning: string;
  language?: string;
}

export interface CopilotTextareaProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  language?: string;
  enableSuggestions?: boolean;
  enableCodeAnalysis?: boolean;
  enableDocGeneration?: boolean;
  className?: string;
  rows?: number;
  disabled?: boolean;
}

export const CopilotTextarea: React.FC<CopilotTextareaProps> = ({
  value,
  onChange,
  placeholder = "Start typing... AI assistance will appear as you work",
  language = "javascript",
  enableSuggestions = true,
  enableCodeAnalysis = true,
  enableDocGeneration = true,
  className = "",
  rows = 10,
  disabled = false,
}) => {
  const { user } = useAuth();
  const { triggerHooks } = useHooks();
  const { toast } = useToast();
  const {
    getSuggestions,
    analyzeCode,
    generateDocumentation,
    isLoading,
    config,
  } = useCopilotKit();

  const [suggestions, setSuggestions] = useState<AISuggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResults, setAnalysisResults] = useState<any>(null);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const debounceRef = useRef<NodeJS.Timeout>();

  // Debounced suggestion fetching
  const fetchSuggestions = useCallback(
    async (text: string, position: number) => {
      if (
        !enableSuggestions ||
        !config.features.contextualSuggestions ||
        text.length < 10
      ) {
        setSuggestions([]);
        return;
      }

      try {
        const context = text.substring(
          Math.max(0, position - 100),
          position + 100
        );
        const rawSuggestions = await getSuggestions(context, "code_completion");

        // Transform raw suggestions into our format
        const formattedSuggestions: AISuggestion[] = rawSuggestions.map(
          (suggestion, index) => ({
            id: `suggestion_${index}`,
            type: suggestion.type || "completion",
            content: suggestion.content || suggestion.text || "",
            confidence: suggestion.confidence || 0.8,
            reasoning: suggestion.reasoning || "AI-generated suggestion",
            language,
          })
        );

        setSuggestions(formattedSuggestions);
        setShowSuggestions(formattedSuggestions.length > 0);

        // Trigger hook for suggestion display
        await triggerHooks(
          "copilot_suggestions_displayed",
          {
            suggestionCount: formattedSuggestions.length,
            context: context.substring(0, 50) + "...",
            language,
            userId: user?.userId,
          },
          { userId: user?.userId }
        );
      } catch (error) {
        safeError("Failed to fetch suggestions:", error);
        setSuggestions([]);
        setShowSuggestions(false);
      }
    },
    [
      enableSuggestions,
      config.features.contextualSuggestions,
      getSuggestions,
      language,
      triggerHooks,
      user?.userId,
    ]
  );

  // Handle text changes with debounced suggestions
  const handleTextChange = useCallback(
    (newValue: string) => {
      onChange(newValue);

      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }

      debounceRef.current = setTimeout(() => {
        const textarea = textareaRef.current;
        if (textarea) {
          const position = textarea.selectionStart;
          fetchSuggestions(newValue, position);
        }
      }, 500);
    },
    [onChange, fetchSuggestions]
  );

  // Apply suggestion
  const applySuggestion = useCallback(
    async (suggestion: AISuggestion) => {
      const textarea = textareaRef.current;
      if (!textarea) return;

      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const newValue =
        value.substring(0, start) + suggestion.content + value.substring(end);

      onChange(newValue);
      setShowSuggestions(false);
      setSuggestions([]);

      // Trigger hook for suggestion applied
      await triggerHooks(
        "copilot_suggestion_applied",
        {
          suggestionType: suggestion.type,
          confidence: suggestion.confidence,
          language,
          userId: user?.userId,
        },
        { userId: user?.userId }
      );

      toast({
        title: "Suggestion Applied",
        description: `${suggestion.type} suggestion applied successfully`,
        duration: 2000,
      });
    },
    [value, onChange, triggerHooks, language, user?.userId, toast]
  );

  // Analyze current code
  const handleCodeAnalysis = useCallback(async () => {
    if (!enableCodeAnalysis || !value.trim()) return;

    setIsAnalyzing(true);
    try {
      const analysis = await analyzeCode(value, language);
      setAnalysisResults(analysis);

      toast({
        title: "Code Analysis Complete",
        description: `Found ${analysis.issues?.length || 0} potential issues`,
        duration: 3000,
      });
    } catch (error) {
      safeError("Code analysis failed:", error);
    } finally {
      setIsAnalyzing(false);
    }
  }, [enableCodeAnalysis, value, language, analyzeCode, toast]);

  // Generate documentation
  const handleDocGeneration = useCallback(async () => {
    if (!enableDocGeneration || !value.trim()) return;

    try {
      const documentation = await generateDocumentation(value, language);

      // Insert documentation at the beginning of the code
      const newValue = `/**\n * ${documentation
        .split("\n")
        .join("\n * ")}\n */\n\n${value}`;
      onChange(newValue);

      toast({
        title: "Documentation Generated",
        description: "AI-generated documentation added to your code",
        duration: 3000,
      });
    } catch (error) {
      safeError("Documentation generation failed:", error);
    }
  }, [
    enableDocGeneration,
    value,
    language,
    generateDocumentation,
    onChange,
    toast,
  ]);

  // Cleanup debounce on unmount
  useEffect(() => {
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, []);

  const SuggestionCard = ({ suggestion }: { suggestion: AISuggestion }) => {
    const getIcon = () => {
      switch (suggestion.type) {
        case "completion":
          return <Code className="h-4 w-4 sm:w-auto md:w-full" />;
        case "refactor":
          return <Zap className="h-4 w-4 sm:w-auto md:w-full" />;
        case "debug":
          return <AlertCircle className="h-4 w-4 sm:w-auto md:w-full" />;
        case "optimize":
          return <Sparkles className="h-4 w-4 sm:w-auto md:w-full" />;
        case "explain":
          return <FileText className="h-4 w-4 sm:w-auto md:w-full" />;
        default:
          return <Lightbulb className="h-4 w-4 sm:w-auto md:w-full" />;
      }
    };

    const getVariant = () => {
      switch (suggestion.type) {
        case "debug":
          return "destructive";
        case "optimize":
          return "default";
        default:
          return "secondary";
      }
    };

    return (
      <Card
        className="mb-2 cursor-pointer hover:bg-muted/50 transition-colors"
        onClick={() => applySuggestion(suggestion)}
      >
        <CardContent className="p-3 sm:p-4 md:p-6">
          <div className="flex items-start gap-3">
            <div className="p-1 bg-primary/10 rounded sm:p-4 md:p-6">{getIcon()}</div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <Badge variant={getVariant()} className="text-xs sm:text-sm md:text-base">
                  {suggestion.type}
                </Badge>
                <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                  {Math.round(suggestion.confidence * 100)}% confidence
                </Badge>
              </div>
              <p className="text-sm font-medium mb-1 md:text-base lg:text-lg">{suggestion.content}</p>
              <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
                {suggestion.reasoning}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  return (
    <div className={`relative ${className}`}>
      {/* Main Textarea */}
      <div className="relative">
        <CopilotKitTextarea
          ref={textareaRef}
          value={value}
          onChange={(e) => handleTextChange(e.target.value)}
          placeholder={placeholder}
          rows={rows}
          disabled={disabled}
          className="w-full p-3 border rounded-md resize-none focus:ring-2 focus:ring-primary focus:border-transparent sm:p-4 md:p-6"
          style={{ fontFamily: "monospace" }}
          autosuggestionsConfig={{
            textareaPurpose: `Code editor for ${language} with AI assistance`,
            chatApiConfigs: {
              suggestionsApiConfig: {
                maxTokens: 1000,
                stop: ["\n\n"],
              },
            },
          }}
        />

        {/* Loading indicator */}
        {(isLoading || isAnalyzing) && (
          <div className="absolute top-2 right-2">
            <Loader2 className="h-4 w-4 animate-spin text-primary sm:w-auto md:w-full" />
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex items-center gap-2 mt-2">
        <button
          variant="outline"
          size="sm"
          onClick={handleCodeAnalysis}
          disabled={isAnalyzing || !value.trim() || !enableCodeAnalysis}
         aria-label="Button">
          {isAnalyzing ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin sm:w-auto md:w-full" />
          ) : (
            <AlertCircle className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
          )}
          Analyze Code
        </Button>

        <button
          variant="outline"
          size="sm"
          onClick={handleDocGeneration}
          disabled={isLoading || !value.trim() || !enableDocGeneration}
         aria-label="Button">
          <FileText className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
          Generate Docs
        </Button>

        {analysisResults && (
          <Badge
            variant={
              analysisResults.issues?.length > 0 ? "destructive" : "default"
            }
          >
            {analysisResults.issues?.length || 0} issues found
          </Badge>
        )}
      </div>

      {/* AI Suggestions Panel */}
      {showSuggestions && suggestions.length > 0 && (
        <div className="absolute top-full left-0 right-0 z-50 mt-2 max-h-64 overflow-y-auto bg-background border rounded-md shadow-lg">
          <div className="p-3 border-b bg-muted/50 sm:p-4 md:p-6">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary sm:w-auto md:w-full" />
              <span className="text-sm font-medium md:text-base lg:text-lg">AI Suggestions</span>
              <Badge variant="secondary" className="text-xs sm:text-sm md:text-base">
                {suggestions.length}
              </Badge>
            </div>
          </div>
          <div className="p-2 sm:p-4 md:p-6">
            {suggestions.map((suggestion) => (
              <SuggestionCard key={suggestion.id} suggestion={suggestion} />
            ))}
          </div>
        </div>
      )}

      {/* Analysis Results Panel */}
      {analysisResults && (
        <Card className="mt-2">
          <CardContent className="p-3 sm:p-4 md:p-6">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle className="h-4 w-4 text-green-500 sm:w-auto md:w-full" />
              <span className="text-sm font-medium md:text-base lg:text-lg">Code Analysis Results</span>
            </div>

            {analysisResults.issues && analysisResults.issues.length > 0 ? (
              <div className="space-y-2">
                {analysisResults.issues
                  .slice(0, 3)
                  .map((issue: any, index: number) => (
                    <div
                      key={index}
                      className="p-2 bg-destructive/10 rounded border-l-2 border-destructive sm:p-4 md:p-6"
                    >
                      <p className="text-sm font-medium text-destructive md:text-base lg:text-lg">
                        {issue.type || "Issue"}
                      </p>
                      <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
                        {issue.message}
                      </p>
                    </div>
                  ))}
                {analysisResults.issues.length > 3 && (
                  <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
                    +{analysisResults.issues.length - 3} more issues
                  </p>
                )}
              </div>
            ) : (
              <p className="text-sm text-green-600 md:text-base lg:text-lg">
                No issues found! Your code looks good.
              </p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};
