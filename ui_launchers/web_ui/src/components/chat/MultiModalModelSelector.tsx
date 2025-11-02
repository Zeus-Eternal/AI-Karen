/**
 * Multi-Modal Model Selector Component
 * 
 * Provides an intelligent interface for selecting multi-modal AI providers
 * with Karen's recommendations and real-time availability status.
 */
import React, { useState, useEffect } from 'react';
import { multiModalService, MultiModalProvider, ProviderType } from '../../lib/multi-modal-service';
interface MultiModalModelSelectorProps {
  selectedProvider?: string;
  selectedType: ProviderType;
  onProviderChange: (providerId: string) => void;
  onTypeChange: (type: ProviderType) => void;
  prompt?: string;
  className?: string;
}
const providerTypeLabels: Record<ProviderType, string> = {
  'image-generation': 'Image Generation',
  'image-analysis': 'Image Analysis',
  'audio-generation': 'Audio Generation',
  'video-generation': 'Video Generation',
  'text-to-speech': 'Text to Speech',
  'speech-to-text': 'Speech to Text'
};
const providerTypeIcons: Record<ProviderType, string> = {
  'image-generation': '🎨',
  'image-analysis': '👁️',
  'audio-generation': '🎵',
  'video-generation': '🎬',
  'text-to-speech': '🗣️',
  'speech-to-text': '👂'
};
export default function MultiModalModelSelector({
  selectedProvider,
  selectedType,
  onProviderChange,
  onTypeChange,
  prompt,
  className = ''
}: MultiModalModelSelectorProps) {
  const [providers, setProviders] = useState<MultiModalProvider[]>([]);
  const [karenRecommendation, setKarenRecommendation] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  // Load providers when type changes
  useEffect(() => {
    const loadProviders = () => {
      const availableProviders = multiModalService.getProviders(selectedType);
      setProviders(availableProviders);
      // Auto-select first available provider if none selected
      if (!selectedProvider && availableProviders.length > 0) {
        const firstAvailable = availableProviders.find(p => 
          p.status === 'available' || p.status === 'local'
        );
        if (firstAvailable) {
          onProviderChange(firstAvailable.id);
        }
      }
    };
    loadProviders();
  }, [selectedType, selectedProvider, onProviderChange]);
  // Get Karen's recommendation when prompt changes
  useEffect(() => {
    const getRecommendation = async () => {
      if (!prompt || prompt.trim().length < 10) {
        setKarenRecommendation(null);
        return;
      }
      setIsLoading(true);
      try {
        const bestProvider = await multiModalService.getBestProvider({
          prompt,
          type: selectedType

        setKarenRecommendation(bestProvider);
      } catch (error) {
        setKarenRecommendation(null);
      } finally {
        setIsLoading(false);
      }
    };
    const debounceTimer = setTimeout(getRecommendation, 500);
    return () => clearTimeout(debounceTimer);
  }, [prompt, selectedType]);
  const getProviderStatusColor = (status: MultiModalProvider['status']) => {
    switch (status) {
      case 'available': return 'text-green-600';
      case 'local': return 'text-blue-600';
      case 'api-key-required': return 'text-yellow-600';
      case 'unavailable': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };
  const getProviderStatusIcon = (status: MultiModalProvider['status']) => {
    switch (status) {
      case 'available': return '✅';
      case 'local': return '💻';
      case 'api-key-required': return '🔑';
      case 'unavailable': return '❌';
      default: return '❓';
    }
  };
  const getProviderStatusText = (status: MultiModalProvider['status']) => {
    switch (status) {
      case 'available': return 'Ready';
      case 'local': return 'Local';
      case 'api-key-required': return 'API Key Required';
      case 'unavailable': return 'Unavailable';
      default: return 'Unknown';
    }
  };
  const isProviderRecommended = (providerId: string) => {
    return karenRecommendation === providerId;
  };
  const isProviderUsable = (provider: MultiModalProvider) => {
    return provider.status === 'available' || provider.status === 'local';
  };
  return (
    <div className={`multi-modal-selector ${className}`} role="dialog">
      {/* Type Selector */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2 md:text-base lg:text-lg">
        </label>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
          {Object.entries(providerTypeLabels).map(([type, label]) => (
            <button
              key={type}
              onClick={() => onTypeChange(type as ProviderType)}
              className={`
                flex items-center justify-center p-3 rounded-lg border-2 transition-all
                ${selectedType === type
                  ? 'border-blue-500 bg-blue-50 text-blue-700'
                  : 'border-gray-200 hover:border-gray-300 text-gray-600'
                }
              `}
            >
              <span className="mr-2 text-lg">
                {providerTypeIcons[type as ProviderType]}
              </span>
              <span className="text-sm font-medium md:text-base lg:text-lg">{label}</span>
            </button>
          ))}
        </div>
      </div>
      {/* Provider Selector */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <label className="block text-sm font-medium text-gray-700 md:text-base lg:text-lg">
          </label>
          {isLoading && (
            <div className="flex items-center text-xs text-gray-500 sm:text-sm md:text-base">
              <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-blue-500 mr-1 "></div>
              Karen is analyzing...
            </div>
          )}
        </div>
        <div className="space-y-2">
          {providers.map((provider) => {
            const isSelected = selectedProvider === provider.id;
            const isRecommended = isProviderRecommended(provider.id);
            const isUsable = isProviderUsable(provider);
            return (
              <div
                key={provider.id}
                className={`
                  relative p-3 rounded-lg border-2 cursor-pointer transition-all
                  ${isSelected
                    ? 'border-blue-500 bg-blue-50'
                    : isUsable
                    ? 'border-gray-200 hover:border-gray-300'
                    : 'border-gray-100 bg-gray-50 cursor-not-allowed opacity-60'
                  }
                  ${isRecommended ? 'ring-2 ring-purple-300' : ''}
                `}
                onClick={() => isUsable && onProviderChange(provider.id)}
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
                        {getProviderStatusIcon(provider.status)}
                      </span>
                    </div>
                    <div>
                      <h3 className="font-medium text-gray-900">
                        {provider.name}
                      </h3>
                      <div className="flex items-center space-x-2 text-sm text-gray-500 md:text-base lg:text-lg">
                        <span className={getProviderStatusColor(provider.status)}>
                          {getProviderStatusText(provider.status)}
                        </span>
                        {provider.pricing && (
                          <span>• {provider.pricing.model}</span>
                        )}
                        {provider.pricing?.cost && (
                          <span>• {provider.pricing.cost}</span>
                        )}
                      </div>
                    </div>
                  </div>
                  {/* Capabilities */}
                  <div className="flex flex-wrap gap-1">
                    {provider.capabilities.slice(0, 3).map((capability) => (
                      <span
                        key={capability}
                        className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded sm:text-sm md:text-base"
                      >
                        {capability}
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
                      <span className="ml-2">Daily: {provider.limits.dailyLimit}</span>
                    )}
                    {provider.limits.maxDuration && (
                      <span className="ml-2">Duration: {provider.limits.maxDuration}s</span>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
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
              {karenRecommendation ? (
                <p className="text-sm text-purple-700 md:text-base lg:text-lg">
                  Based on your prompt, I recommend{' '}
                  <strong>
                    {providers.find(p => p.id === karenRecommendation)?.name}
                  </strong>{' '}
                  for the best results.
                </p>
              ) : (
                <p className="text-sm text-purple-700 md:text-base lg:text-lg">
                  Your prompt looks great! Any of the available providers should work well.
                </p>
              )}
            </div>
          </div>
        </div>
      )}
      {/* Quick Actions */}
      <div className="mt-4 flex space-x-2">
        <button
          onClick={() => {
            // Refresh providers
            const refreshedProviders = multiModalService.getProviders(selectedType);
            setProviders(refreshedProviders);
          }}
          className="flex-1 px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors md:text-base lg:text-lg"
        >
          🔄 Refresh
        </button>
        <button
          onClick={() => {
            // Open provider settings (would open a modal in real implementation)
          }}
          className="flex-1 px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors md:text-base lg:text-lg"
        >
          ⚙️ Settings
        </button>
      </div>
    </div>
  );
}
