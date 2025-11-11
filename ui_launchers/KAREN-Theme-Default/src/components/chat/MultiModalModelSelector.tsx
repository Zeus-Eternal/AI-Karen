// ui_launchers/KAREN-Theme-Default/src/components/chat/enhanced/MultiModalModelSelector.tsx
"use client";

import React, {
  useState,
  useEffect,
  useMemo,
  useCallback,
  useRef,
} from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  multiModalService,
  type MultiModalProvider,
  type ProviderType,
} from "@/lib/multi-modal-service";

type Props = {
  selectedProvider?: string;
  selectedType: ProviderType;
  onProviderChange: (providerId: string) => void;
  onTypeChange: (type: ProviderType) => void;
  prompt?: string;
  className?: string;
  onOpenSettings?: () => void; // optional hook to open settings modal
};

const providerTypeLabels: Record<ProviderType, string> = {
  "image-generation": "Image Generation",
  "image-analysis": "Image Analysis",
  "audio-generation": "Audio Generation",
  "video-generation": "Video Generation",
  "text-to-speech": "Text to Speech",
  "speech-to-text": "Speech to Text",
};

const providerTypeIcons: Record<ProviderType, string> = {
  "image-generation": "🎨",
  "image-analysis": "👁️",
  "audio-generation": "🎵",
  "video-generation": "🎬",
  "text-to-speech": "🗣️",
  "speech-to-text": "👂",
};

const statusColor = (status: MultiModalProvider["status"]) => {
  switch (status) {
    case "available":
      return "text-green-600";
    case "local":
      return "text-blue-600";
    case "api-key-required":
      return "text-yellow-600";
    case "unavailable":
      return "text-red-600";
    default:
      return "text-gray-600";
  }
};

const statusIcon = (status: MultiModalProvider["status"]) => {
  switch (status) {
    case "available":
      return "✅";
    case "local":
      return "💻";
    case "api-key-required":
      return "🔑";
    case "unavailable":
      return "❌";
    default:
      return "❓";
  }
};

const statusText = (status: MultiModalProvider["status"]) => {
  switch (status) {
    case "available":
      return "Ready";
    case "local":
      return "Local";
    case "api-key-required":
      return "API Key Required";
    case "unavailable":
      return "Unavailable";
    default:
      return "Unknown";
  }
};

export default function MultiModalModelSelector({
  selectedProvider,
  selectedType,
  onProviderChange,
  onTypeChange,
  prompt,
  className = "",
  onOpenSettings,
}: Props) {
  const [providers, setProviders] = useState<MultiModalProvider[]>([]);
  const [karenRecommendation, setKarenRecommendation] = useState<string | null>(
    null
  );
  const [isLoading, setIsLoading] = useState(false);
  const [recError, setRecError] = useState<string | null>(null);

  const debouncerRef = useRef<number | null>(null);

  const usable = useCallback(
    (p: MultiModalProvider) => p.status === "available" || p.status === "local",
    []
  );

  const refreshProviders = useCallback(() => {
    const available = multiModalService.getProviders(selectedType);
    setProviders(available);

    // auto-select first usable if none selected
    if (!selectedProvider && available.length > 0) {
      const first = available.find(usable);
      if (first) onProviderChange(first.id);
    }
  }, [onProviderChange, selectedProvider, selectedType, usable]);

  // Load providers when type changes (and on mount)
  useEffect(() => {
    refreshProviders();
  }, [refreshProviders]);

  // Debounced “Karen’s pick” based on prompt/type
  useEffect(() => {
    // Clear any pending debounce
    if (debouncerRef.current) {
      window.clearTimeout(debouncerRef.current);
      debouncerRef.current = null;
    }

    // No prompt or too short: clear recommendation
    if (!prompt || prompt.trim().length < 10) {
      setKarenRecommendation(null);
      setRecError(null);
      return;
    }

    setIsLoading(true);
    setRecError(null);

    debouncerRef.current = window.setTimeout(async () => {
      try {
        const best = await multiModalService.getBestProvider({
          prompt: prompt.trim(),
          type: selectedType,
        });
        setKarenRecommendation(best ?? null);
      } catch (error) {
        console.error("Failed to compute Karen's recommendation", error);
        setKarenRecommendation(null);
        setRecError("Could not compute recommendation.");
      } finally {
        setIsLoading(false);
      }
    }, 500);

    return () => {
      if (debouncerRef.current) {
        window.clearTimeout(debouncerRef.current);
      }
    };
  }, [prompt, selectedType]);

  const recommendedName = useMemo(() => {
    if (!karenRecommendation) return null;
    return providers.find((p) => p.id === karenRecommendation)?.name ?? null;
  }, [karenRecommendation, providers]);

  return (
    <div
      className={cn("multi-modal-selector", className)}
      role="group"
      aria-label="Multi-modal model selector"
    >
      {/* Type Selector */}
      <div className="mb-4">
        <label
          className="block text-sm font-medium text-gray-700 mb-2 md:text-base lg:text-lg"
          htmlFor="provider-type-selector"
        >
          Content Type
        </label>

        <div
          id="provider-type-selector"
          className="grid grid-cols-2 md:grid-cols-3 gap-2"
        >
          {(
            Object.entries(providerTypeLabels) as Array<[ProviderType, string]>
          ).map(([type, label]) => (
            <Button
              key={type}
              type="button"
              onClick={() => onTypeChange(type)}
              aria-pressed={selectedType === type}
              className={cn(
                "flex items-center justify-center p-3 rounded-lg border-2 transition-all",
                selectedType === type
                  ? "border-blue-500 bg-blue-50 text-blue-700"
                  : "border-gray-200 hover:border-gray-300 text-gray-600"
              )}
              title={label}
            >
              <span className="mr-2 text-lg">{providerTypeIcons[type]}</span>
              <span className="text-sm font-medium md:text-base lg:text-lg">
                {label}
              </span>
            </Button>
          ))}
        </div>
      </div>

      {/* Provider Selector */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <label className="block text-sm font-medium text-gray-700 md:text-base lg:text-lg">
            Providers
          </label>

          {isLoading && (
            <div
              className="flex items-center text-xs text-gray-500 sm:text-sm md:text-base"
              role="status"
              aria-live="polite"
            >
              <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-blue-500 mr-1" />
              Analyzing prompt…
            </div>
          )}
        </div>

        <div className="space-y-2">
          {providers.map((provider) => {
            const isSelected = selectedProvider === provider.id;
            const isRecommended = karenRecommendation === provider.id;
            const canUse = usable(provider);

            return (
              <div
                key={provider.id}
                role="button"
                tabIndex={0}
                aria-pressed={isSelected}
                onClick={() => canUse && onProviderChange(provider.id)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    if (canUse) onProviderChange(provider.id);
                  }
                }}
                className={cn(
                  "relative p-3 rounded-lg border-2 cursor-pointer transition-all outline-none",
                  isSelected
                    ? "border-blue-500 bg-blue-50"
                    : canUse
                    ? "border-gray-200 hover:border-gray-300"
                    : "border-gray-100 bg-gray-50 cursor-not-allowed opacity-60",
                  isRecommended && "ring-2 ring-purple-300"
                )}
              >
                {/* Karen's Recommendation Badge */}
                {isRecommended && (
                  <div className="absolute -top-2 -right-2 bg-purple-500 text-white text-xs px-2 py-1 rounded-full sm:text-sm md:text-base">
                    Karen&apos;s Pick ✨
                  </div>
                )}

                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="mr-3">
                      <span className="text-lg">
                        {statusIcon(provider.status)}
                      </span>
                    </div>

                    <div>
                      <h3 className="font-medium text-gray-900">
                        {provider.name}
                      </h3>
                      <div className="flex items-center space-x-2 text-sm text-gray-500 md:text-base lg:text-lg">
                        <span className={statusColor(provider.status)}>
                          {statusText(provider.status)}
                        </span>
                        {provider.pricing?.model && (
                          <span>• {provider.pricing.model}</span>
                        )}
                        {provider.pricing?.cost && (
                          <span>• {provider.pricing.cost}</span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Capabilities */}
                  <div className="flex flex-wrap gap-1 justify-end">
                    {provider.capabilities.slice(0, 3).map((cap) => (
                      <span
                        key={cap}
                        className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded sm:text-sm md:text-base"
                      >
                        {cap}
                      </span>
                    ))}
                    {provider.capabilities.length > 3 && (
                      <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded sm:text-sm md:text-base">
                        +{provider.capabilities.length - 3}
                      </span>
                    )}
                  </div>
                </div>

                {/* Limits */}
                {provider.limits && (
                  <div className="mt-2 text-xs text-gray-500 sm:text-sm md:text-base">
                    {provider.limits.maxResolution && (
                      <span>Max: {provider.limits.maxResolution}</span>
                    )}
                    {provider.limits.dailyLimit && (
                      <span className="ml-2">
                        Daily: {provider.limits.dailyLimit}
                      </span>
                    )}
                    {provider.limits.maxDuration && (
                      <span className="ml-2">
                        Duration: {provider.limits.maxDuration}s
                      </span>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Empty State */}
        {providers.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <div className="text-4xl mb-2">🤖</div>
            <p>No providers available for {providerTypeLabels[selectedType]}</p>
            <p className="text-sm mt-1 md:text-base lg:text-lg">
              Check your configuration or try a different content type.
            </p>
          </div>
        )}
      </div>

      {/* Karen's Insights */}
      {prompt && prompt.trim().length > 10 && (
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-3 sm:p-4 md:p-6">
          <div className="flex items-start">
            <div className="text-purple-500 mr-2">💡</div>
            <div className="flex-1">
              <h4 className="text-sm font-medium text-purple-800 mb-1 md:text-base lg:text-lg">
                Karen&apos;s Insights
              </h4>

              {recError && (
                <p className="text-sm text-purple-700 md:text-base lg:text-lg">
                  I couldn&apos;t compute a recommendation right now. You can
                  still pick any ready provider below.
                </p>
              )}

              {!recError && karenRecommendation && recommendedName && (
                <p className="text-sm text-purple-700 md:text-base lg:text-lg">
                  Based on your prompt, I recommend{" "}
                  <strong>{recommendedName}</strong> for the best results.
                </p>
              )}

              {!recError && !karenRecommendation && (
                <p className="text-sm text-purple-700 md:text-base lg:text-lg">
                  Your prompt looks great! Any of the available providers should
                  work well.
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="mt-4 flex space-x-2">
        <Button
          type="button"
          onClick={refreshProviders}
          className="flex-1 px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors md:text-base lg:text-lg"
          aria-label="Refresh providers"
        >
          🔄 Refresh
        </Button>

        <Button
          type="button"
          onClick={() => onOpenSettings?.()}
          className="flex-1 px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors md:text-base lg:text-lg"
          aria-label="Open provider settings"
        >
          ⚙️ Settings
        </Button>
      </div>
    </div>
  );
}
