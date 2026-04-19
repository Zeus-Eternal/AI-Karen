"use client";

import React, { useState } from 'react';
import type { AgentStepEvent } from '@/lib/api';

interface AgentActivityPanelProps {
  steps: AgentStepEvent[];
}

type ActionIconMap = Record<string, React.ReactNode>;

const renderToolInfo = (metadata?: Record<string, unknown>): React.ReactNode | null => {
  if (!metadata?.tool) return null;
  const toolValue = metadata.tool;
  return (
    <p className="text-xs text-blue-600 dark:text-blue-400">
      Tool: {typeof toolValue === 'string' ? toolValue : JSON.stringify(toolValue)}
    </p>
  );
};

const renderExtensionInfo = (metadata?: Record<string, unknown>): React.ReactNode | null => {
  if (!metadata?.extension_id) return null;
  const extValue = metadata.extension_id;
  return (
    <p className="text-xs text-purple-600 dark:text-purple-400">
      Extension: {typeof extValue === 'string' ? extValue : JSON.stringify(extValue)}
    </p>
  );
};

export default function AgentActivityPanel({ steps }: AgentActivityPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!steps || steps.length === 0) {
    return null;
  }

  const actionIcons: ActionIconMap = {
    agent_step_started: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7h7l-9-7v7h2V10z" />
      </svg>
    ),
    tool_execution_started: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065-2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37" />
      </svg>
    ),
    tool_execution_completed: (
      <svg className="w-4 h-4 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
      </svg>
    ),
    web_search_started: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9-9m9 9a9 9 0 01-9-9m9 9a9 9 0 01-9-9" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 12h4m-2-2v4m-2 2h4" />
      </svg>
    ),
    web_search_sources_found: (
      <svg className="w-4 h-4 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
    extension_execution_started: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-5" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4.5 4.5a2.121 2.121 0 013-3L21.5 2.5z" />
      </svg>
    ),
    extension_execution_completed: (
      <svg className="w-4 h-4 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4" />
      </svg>
    ),
    citation_bundle_ready: (
      <svg className="w-4 h-4 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
      </svg>
    ),
    degraded_mode_entered: (
      <svg className="w-4 h-4 text-yellow-600 dark:text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.932-3L13.932 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.932 3h13.856c1.54 0 2.502-1.667 1.932-3z" />
      </svg>
    ),
  };

  const getActionLabel = (type: string) => {
    switch (type) {
      case 'agent_step_started':
        return 'Processing';
      case 'agent_step_completed':
        return 'Completed';
      case 'tool_execution_started':
        return 'Executing tool';
      case 'tool_execution_completed':
        return 'Tool complete';
      case 'web_search_started':
        return 'Searching web';
      case 'web_search_sources_found':
        return 'Sources found';
      case 'extension_execution_started':
        return 'Running extension';
      case 'extension_execution_completed':
        return 'Extension complete';
      case 'citation_bundle_ready':
        return 'Citations ready';
      case 'degraded_mode_entered':
        return 'Degraded mode';
      default:
        return type.replace(/_/g, ' ');
    }
  };

  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-3 border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors"
      >
        <div className="flex items-center gap-2">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2h2a2 2 0 002-2z" />
          </svg>
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Agent Activity ({steps.length})
          </span>
        </div>
        <svg
          className={`w-4 h-4 transform transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isExpanded && (
        <div className="max-h-64 overflow-y-auto p-2 space-y-2">
          {steps.map((step, index) => (
            <div
              key={`${step.step_id}-${index}`}
              className="flex items-start gap-3 p-2 rounded-md bg-gray-50 dark:bg-gray-750 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              <span className="flex-shrink-0 mt-0.5">
                {actionIcons[step.type] || actionIcons.agent_step_started}
              </span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    {getActionLabel(step.type)}
                  </span>
                  {step.metadata && (
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {step.timestamp && new Date(step.timestamp).toLocaleTimeString()}
                    </span>
                  )}
                </div>
                {step.action_type && typeof step.action_type === 'string' && (
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    {step.action_type}
                  </p>
                )}
                {renderToolInfo(step.metadata)}
                {renderExtensionInfo(step.metadata)}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
