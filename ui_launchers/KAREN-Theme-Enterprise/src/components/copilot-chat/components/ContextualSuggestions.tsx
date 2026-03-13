import React, { useState, useEffect } from 'react';
import { CopilotSuggestion } from '../types/copilot';

interface ContextualSuggestionsProps {
  suggestions: CopilotSuggestion[];
  onSelectSuggestion: (suggestion: CopilotSuggestion) => void;
  className?: string;
}

/**
 * ContextualSuggestions - Displays proactive, context-aware suggestions
 * Implements the contextual suggestion system described in the INNOVATIVE_COPILOT_PLAN.md
 */
export const ContextualSuggestions: React.FC<ContextualSuggestionsProps> = ({
  suggestions,
  onSelectSuggestion,
  className = ''
}) => {
  const [filteredSuggestions, setFilteredSuggestions] = useState<CopilotSuggestion[]>([]);
  const [selectedSuggestion, setSelectedSuggestion] = useState<string | null>(null);

  // Filter suggestions based on priority and confidence
  useEffect(() => {
    const filtered = suggestions
      .filter(suggestion => suggestion.confidence > 0.5) // Only show confident suggestions
      .sort((a, b) => {
        // Sort by priority first
        const priorityOrder = { 'high': 3, 'medium': 2, 'low': 1 };
        const priorityDiff = priorityOrder[b.priority] - priorityOrder[a.priority];
        if (priorityDiff !== 0) return priorityDiff;
        
        // Then sort by confidence
        return b.confidence - a.confidence;
      })
      .slice(0, 5); // Limit to top 5 suggestions
    
    setFilteredSuggestions(filtered);
  }, [suggestions]);

  const handleSelectSuggestion = (suggestion: CopilotSuggestion) => {
    setSelectedSuggestion(suggestion.id);
    onSelectSuggestion(suggestion);
  };

  const getSuggestionIcon = (type: CopilotSuggestion['type']) => {
    switch (type) {
      case 'action':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        );
      case 'response':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
        );
      case 'workflow':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
          </svg>
        );
      case 'artifact':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        );
      case 'setting':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-2.572-1.065c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        );
      default:
        return null;
    }
  };

  const getPriorityColor = (priority: CopilotSuggestion['priority']) => {
    switch (priority) {
      case 'high':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low':
        return 'bg-green-100 text-green-800 border-green-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  if (filteredSuggestions.length === 0) {
    return null;
  }

  return (
    <div className={`space-y-3 ${className}`}>
      <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">Suggestions</h3>
      <div className="space-y-2">
        {filteredSuggestions.map((suggestion) => (
          <button
            key={suggestion.id}
            onClick={() => handleSelectSuggestion(suggestion)}
            className={`flex flex-col items-start p-3 rounded-xl border transition-all duration-200 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 ${
              selectedSuggestion === suggestion.id
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700/50'
            }`}
            aria-label={`Select suggestion: ${suggestion.title}`}
          >
            <div className="flex items-center w-full mb-2">
              <div className="flex-shrink-0 text-blue-600 dark:text-blue-400 mr-2">
                {getSuggestionIcon(suggestion.type)}
              </div>
              <div className="flex-1 text-left">
                <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">{suggestion.title}</h4>
              </div>
              <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getPriorityColor(suggestion.priority)}`}>
                {suggestion.priority}
              </span>
            </div>
            <p className="text-xs text-gray-600 dark:text-gray-400 text-left mt-1">{suggestion.description}</p>
            <div className="mt-2 w-full flex justify-between items-center">
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
                <div
                  className="bg-blue-600 h-1.5 rounded-full"
                  style={{ width: `${suggestion.confidence * 100}%` }}
                ></div>
              </div>
              <span className="text-xs text-gray-500 dark:text-gray-400 ml-2">
                {Math.round(suggestion.confidence * 100)}%
              </span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};