/**
 * Agent Selection Module
 * Exports all components, types, and utilities for the CoPilot Agent Selection System
 */

// Main component
export { AgentSelection } from './AgentSelection';

// UI Components
export { AgentCard } from './ui/AgentCard';
export { AgentDetails } from './ui/AgentDetails';
export { AgentFilters as AgentFiltersComponent } from './ui/AgentFilters';
export { AgentComparison } from './ui/AgentComparison';
export { AgentRecommendations } from './ui/AgentRecommendations';
export { AgentConfiguration } from './ui/AgentConfiguration';
export { AgentStatusBadge } from './ui/AgentStatusBadge';
export { AgentCapabilityBadge } from './ui/AgentCapabilityBadge';
export { AgentRating, SimpleAgentRating, InteractiveAgentRating } from './ui/AgentRating';
export { AgentPerformanceMetrics as AgentPerformanceMetricsComponent } from './ui/AgentPerformanceMetrics';

// Store
export { useAgentSelectionStore } from './store/agentStore';

// API
export { agentApi } from './services/agentApi';

// Types
export type {
  AgentStatus,
  AgentType,
  AgentCapability,
  AgentPerformanceMetrics as AgentPerformanceMetricsType,
  AgentRating as AgentRatingType,
  AgentConfiguration as AgentConfigurationType,
  AgentUseCase,
  Agent,
  AgentFilters as AgentFiltersType,
  AgentSortOptions,
  AgentListResponse,
  AgentRecommendation,
  AgentComparison as AgentComparisonType,
  AgentSelectionContext,
  AgentConfigurationValues,
  AgentSelectionState,
  AgentSelectionActions,
  AgentSelectionStore,
  AgentSelectionProps,
  AgentCardProps,
  AgentDetailsProps,
  AgentFiltersProps,
  AgentComparisonProps,
  AgentRecommendationsProps,
  AgentConfigurationProps,
  AgentStatusBadgeProps,
  AgentCapabilityBadgeProps,
  AgentRatingProps,
  AgentPerformanceMetricsProps,
} from './types';

// Utilities
export { formatRelativeTime } from '@/lib/utils';