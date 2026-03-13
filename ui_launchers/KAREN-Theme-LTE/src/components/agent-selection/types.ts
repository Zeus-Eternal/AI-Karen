/**
 * Agent Selection Types
 * TypeScript interfaces for the CoPilot Agent Selection System
 */

// Agent status enumeration
export type AgentStatus = 'available' | 'busy' | 'maintenance' | 'offline' | 'error';

// Agent type enumeration
export type AgentType = 'general' | 'specialized' | 'custom' | 'system';

// Agent capability enumeration
export type AgentCapability = 
  | 'text-generation'
  | 'code-generation'
  | 'data-analysis'
  | 'image-processing'
  | 'audio-processing'
  | 'video-processing'
  | 'web-scraping'
  | 'api-integration'
  | 'database-query'
  | 'file-processing'
  | 'natural-language-understanding'
  | 'translation'
  | 'summarization'
  | 'classification'
  | 'recommendation'
  | 'automation'
  | 'monitoring'
  | 'security-analysis';

// Agent performance metrics
export interface AgentPerformanceMetrics {
  averageResponseTime: number; // in milliseconds
  successRate: number; // percentage (0-100)
  totalTasks: number;
  completedTasks: number;
  failedTasks: number;
  averageTaskDuration: number; // in milliseconds
  uptime: number; // percentage (0-100)
  lastUpdated: Date;
  resourceUsage: {
    cpu: number; // percentage
    memory: number; // in MB
    network: number; // in MB/s
  };
}

// Agent rating and review
export interface AgentRating {
  userId: string;
  rating: number; // 1-5
  review?: string;
  timestamp: Date;
  helpful?: boolean;
}

// Agent configuration schema
export interface AgentConfiguration {
  id: string;
  name: string;
  type: 'string' | 'number' | 'boolean' | 'select' | 'textarea' | 'file';
  label: string;
  description?: string;
  defaultValue?: any;
  required: boolean;
  options?: string[]; // for select type
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    custom?: string; // validation function name
  };
  category?: string;
  order: number;
}

// Agent use case
export interface AgentUseCase {
  id: string;
  title: string;
  description: string;
  category: string;
  complexity: 'simple' | 'medium' | 'complex';
  estimatedTime: number; // in minutes
  example?: string;
}

// Main agent interface
export interface Agent {
  id: string;
  name: string;
  description: string;
  version: string;
  type: AgentType;
  status: AgentStatus;
  capabilities: AgentCapability[];
  specializations: string[];
  tags: string[];
  icon?: string;
  avatar?: string;
  developer: {
    name: string;
    email?: string;
    website?: string;
  };
  performance: AgentPerformanceMetrics;
  ratings: {
    average: number; // 1-5
    count: number;
    distribution: Record<number, number>; // rating -> count
  };
  reviews: AgentRating[];
  configuration: AgentConfiguration[];
  useCases: AgentUseCase[];
  requirements: {
    minMemory?: number; // in MB
    minCpu?: number; // percentage
    dependencies?: string[];
    permissions?: string[];
  };
  compatibility: {
    platforms: string[];
    browsers: string[];
    devices: string[];
  };
  pricing?: {
    model: 'free' | 'pay-per-use' | 'subscription';
    costPerTask?: number;
    subscriptionPlans?: Array<{
      name: string;
      price: number;
      features: string[];
    }>;
  };
  documentation: {
    readme?: string;
    apiReference?: string;
    examples?: string;
    support?: string;
  };
  createdAt: Date;
  updatedAt: Date;
  lastUsed?: Date;
  isRecommended?: boolean;
  isBeta?: boolean;
  isDeprecated?: boolean;
}

// Agent filter options
export interface AgentFilters {
  status?: AgentStatus[];
  type?: AgentType[];
  capabilities?: AgentCapability[];
  specializations?: string[];
  tags?: string[];
  developer?: string[];
  rating?: {
    min: number;
    max: number;
  };
  pricing?: ('free' | 'paid')[];
  performance?: {
    minSuccessRate?: number;
    maxResponseTime?: number;
  };
  search?: string;
  includeDeprecated?: boolean;
  includeBeta?: boolean;
}

// Agent sort options
export interface AgentSortOptions {
  field: 'name' | 'rating' | 'performance' | 'createdAt' | 'lastUsed' | 'popularity';
  direction: 'asc' | 'desc';
}

// Agent list response
export interface AgentListResponse {
  agents: Agent[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

// Agent recommendation
export interface AgentRecommendation {
  agent: Agent;
  score: number; // 0-100
  reasons: string[];
  confidence: number; // 0-100
  context: string;
}

// Agent comparison
export interface AgentComparison {
  agents: Agent[];
  comparisonMatrix: Record<string, Record<string, any>>;
  recommendations: {
    bestOverall: Agent;
    bestPerformance: Agent;
    mostReliable: Agent;
    easiestToUse: Agent;
    bestValue: Agent;
  };
}

// Agent selection context
export interface AgentSelectionContext {
  taskType?: string;
  taskDescription?: string;
  userPreferences?: {
    preferredCapabilities?: AgentCapability[];
    budgetConstraints?: number;
    performanceRequirements?: {
      maxResponseTime?: number;
      minSuccessRate?: number;
    };
  };
  previousSelections?: Agent[];
  userHistory?: {
    completedTasks: number;
    averageRating: number;
    preferredAgents: string[];
  };
  [key: string]: unknown; // Index signature for API compatibility
}

// Agent configuration values
export interface AgentConfigurationValues {
  [configId: string]: any;
}

// Agent selection state
export interface AgentSelectionState {
  // Agents
  agents: Agent[];
  selectedAgent: Agent | null;
  comparisonAgents: Agent[];
  recommendations: AgentRecommendation[];
  isLoading: boolean;
  error: string | null;
  
  // Filters and sorting
  filters: AgentFilters;
  sortOptions: AgentSortOptions;
  
  // UI state
  showDetails: boolean;
  showFilters: boolean;
  showComparison: boolean;
  showConfiguration: boolean;
  viewMode: 'list' | 'grid' | 'compact';
  
  // Configuration
  configurationValues: AgentConfigurationValues;
  
  // Context
  selectionContext: AgentSelectionContext;
}

// Agent selection actions
export interface AgentSelectionActions {
  // Agent operations
  fetchAgents: (filters?: AgentFilters, sort?: AgentSortOptions) => Promise<void>;
  fetchAgent: (agentId: string) => Promise<void>;
  selectAgent: (agent: Agent) => void;
  deselectAgent: () => void;
  
  // Comparison
  addToComparison: (agent: Agent) => void;
  removeFromComparison: (agentId: string) => void;
  clearComparison: () => void;
  
  // Recommendations
  fetchRecommendations: (context: AgentSelectionContext) => Promise<void>;
  
  // Configuration
  updateConfiguration: (configId: string, value: any) => void;
  resetConfiguration: () => void;
  
  // Filters and sorting
  setFilters: (filters: AgentFilters) => void;
  setSortOptions: (sortOptions: AgentSortOptions) => void;
  clearFilters: () => void;
  
  // UI state
  setShowDetails: (show: boolean) => void;
  setShowFilters: (show: boolean) => void;
  setShowComparison: (show: boolean) => void;
  setShowConfiguration: (show: boolean) => void;
  setViewMode: (mode: 'list' | 'grid' | 'compact') => void;
  
  // Context
  setSelectionContext: (context: AgentSelectionContext) => void;
  
  // Utility
  clearError: () => void;
  reset: () => void;
}

// Agent selection store (combined state and actions)
export type AgentSelectionStore = AgentSelectionState & AgentSelectionActions;

// Props for AgentSelection component
export interface AgentSelectionProps {
  className?: string;
  onAgentSelect?: (agent: Agent, configuration?: AgentConfigurationValues) => void;
  onCompare?: (agents: Agent[]) => void;
  context?: AgentSelectionContext;
  showRecommendations?: boolean;
  maxComparisonAgents?: number;
  autoRefresh?: boolean;
  refreshInterval?: number; // in milliseconds
}

// Props for AgentCard component
export interface AgentCardProps {
  agent: Agent;
  onSelect?: (agent: Agent) => void;
  onCompare?: (agent: Agent) => void;
  showDetails?: boolean;
  compact?: boolean;
  showPerformance?: boolean;
  showRating?: boolean;
  className?: string;
}

// Props for AgentDetails component
export interface AgentDetailsProps {
  agent: Agent;
  onClose?: () => void;
  onSelect?: (agent: Agent) => void;
  onConfigure?: (agent: Agent, config: AgentConfigurationValues) => void;
  showActions?: boolean;
  className?: string;
}

// Props for AgentFilters component
export interface AgentFiltersProps {
  filters: AgentFilters;
  onFiltersChange: (filters: AgentFilters) => void;
  onClear: () => void;
  capabilities: AgentCapability[];
  specializations: string[];
  developers: string[];
  className?: string;
}

// Props for AgentComparison component
export interface AgentComparisonProps {
  agents: Agent[];
  onClose?: () => void;
  onSelect?: (agent: Agent) => void;
  className?: string;
}

// Props for AgentRecommendations component
export interface AgentRecommendationsProps {
  recommendations: AgentRecommendation[];
  context: AgentSelectionContext;
  onSelect?: (agent: Agent) => void;
  onRefresh?: () => void;
  className?: string;
}

// Props for AgentConfiguration component
export interface AgentConfigurationProps {
  agent: Agent;
  values: AgentConfigurationValues;
  onChange: (configId: string, value: any) => void;
  onReset?: () => void;
  onSave?: (values: AgentConfigurationValues) => void;
  className?: string;
}

// Props for AgentStatusBadge component
export interface AgentStatusBadgeProps {
  status: AgentStatus;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
  showLabel?: boolean;
  className?: string;
}

// Props for AgentCapabilityBadge component
export interface AgentCapabilityBadgeProps {
  capability: AgentCapability;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
  className?: string;
}

// Props for AgentRating component
export interface AgentRatingProps {
  rating: number;
  count?: number;
  showCount?: boolean;
  size?: 'sm' | 'md' | 'lg';
  interactive?: boolean;
  onChange?: (rating: number) => void;
  className?: string;
}

// Props for AgentPerformanceMetrics component
export interface AgentPerformanceMetricsProps {
  metrics: AgentPerformanceMetrics;
  compact?: boolean;
  showDetails?: boolean;
  className?: string;
}
