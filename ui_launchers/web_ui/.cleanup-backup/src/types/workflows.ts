/**
 * Workflow and Agent Orchestration Types
 * Defines interfaces for workflow management, agent orchestration, and execution monitoring
 */

export interface WorkflowNode {
  id: string;
  type: 'input' | 'output' | 'llm' | 'memory' | 'plugin' | 'condition' | 'loop' | 'custom';
  position: { x: number; y: number };
  data: {
    label: string;
    description?: string;
    config: Record<string, any>;
    inputs?: NodePort[];
    outputs?: NodePort[];
  };
  style?: Record<string, any>;
}

export interface NodePort {
  id: string;
  name: string;
  type: 'string' | 'number' | 'boolean' | 'object' | 'array' | 'any';
  required?: boolean;
  description?: string;
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
  type?: 'default' | 'straight' | 'step' | 'smoothstep';
  animated?: boolean;
  style?: Record<string, any>;
  data?: {
    condition?: string;
    transform?: string;
  };
}

export interface WorkflowVariable {
  id: string;
  name: string;
  type: 'string' | 'number' | 'boolean' | 'object' | 'array';
  value: any;
  description?: string;
  scope: 'global' | 'local';
}

export interface CronSchedule {
  expression: string;
  timezone: string;
  enabled: boolean;
  nextRun?: Date;
  lastRun?: Date;
}

export interface WorkflowDefinition {
  id: string;
  name: string;
  description: string;
  version: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  variables: WorkflowVariable[];
  schedule?: CronSchedule;
  tags: string[];
  metadata: {
    createdAt: Date;
    updatedAt: Date;
    createdBy: string;
    status: 'draft' | 'active' | 'paused' | 'archived';
  };
}

export interface WorkflowExecution {
  id: string;
  workflowId: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  startTime: Date;
  endTime?: Date;
  duration?: number;
  progress: number;
  currentNode?: string;
  logs: ExecutionLog[];
  results: Record<string, any>;
  error?: string;
  metadata: {
    triggeredBy: 'manual' | 'schedule' | 'event';
    trigger?: string;
  };
}

export interface ExecutionLog {
  id: string;
  timestamp: Date;
  level: 'debug' | 'info' | 'warn' | 'error';
  nodeId?: string;
  message: string;
  data?: any;
}

export interface NodeTemplate {
  id: string;
  name: string;
  category: 'input' | 'processing' | 'output' | 'control' | 'ai' | 'integration';
  description: string;
  icon: string;
  inputs: NodePort[];
  outputs: NodePort[];
  config: {
    schema: Record<string, any>;
    defaults: Record<string, any>;
  };
  implementation?: string;
}

export interface WorkflowValidationResult {
  valid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
}

export interface ValidationError {
  id: string;
  type: 'missing_connection' | 'invalid_config' | 'circular_dependency' | 'type_mismatch';
  nodeId?: string;
  edgeId?: string;
  message: string;
  severity: 'error' | 'warning';
}

export interface ValidationWarning {
  id: string;
  type: 'performance' | 'best_practice' | 'deprecated';
  nodeId?: string;
  message: string;
  suggestion?: string;
}

export interface WorkflowTestResult {
  success: boolean;
  duration: number;
  nodeResults: Record<string, any>;
  logs: ExecutionLog[];
  error?: string;
}

// Agent Management Types
export interface Agent {
  id: string;
  name: string;
  description: string;
  type: 'workflow' | 'autonomous' | 'reactive' | 'scheduled';
  status: 'idle' | 'running' | 'paused' | 'error' | 'stopped';
  config: AgentConfig;
  metrics: AgentMetrics;
  taskQueue: AgentTask[];
  lastActivity?: Date;
  health: AgentHealth;
}

export interface AgentConfig {
  maxConcurrentTasks: number;
  timeout: number;
  retryAttempts: number;
  resources: {
    cpu: number;
    memory: number;
    gpu?: number;
  };
  permissions: string[];
  environment: Record<string, string>;
}

export interface AgentMetrics {
  tasksCompleted: number;
  tasksInProgress: number;
  tasksFailed: number;
  averageExecutionTime: number;
  successRate: number;
  resourceUsage: {
    cpu: number;
    memory: number;
    gpu?: number;
  };
  uptime: number;
}

export interface AgentTask {
  id: string;
  type: string;
  priority: 'low' | 'normal' | 'high' | 'critical';
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
  payload: any;
  createdAt: Date;
  startedAt?: Date;
  completedAt?: Date;
  result?: any;
  error?: string;
}

export interface AgentHealth {
  status: 'healthy' | 'warning' | 'critical' | 'unknown';
  lastCheck: Date;
  checks: HealthCheck[];
  issues: HealthIssue[];
}

export interface HealthCheck {
  name: string;
  status: 'pass' | 'fail' | 'warn';
  message?: string;
  timestamp: Date;
  duration: number;
}

export interface HealthIssue {
  id: string;
  type: 'performance' | 'resource' | 'connectivity' | 'configuration';
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  timestamp: Date;
  resolved: boolean;
  resolution?: string;
}

// Workflow Scheduler Types
export interface WorkflowTrigger {
  id: string;
  name: string;
  type: 'schedule' | 'event' | 'webhook' | 'file' | 'condition';
  config: TriggerConfig;
  enabled: boolean;
  workflowId: string;
  lastTriggered?: Date;
  nextTrigger?: Date;
}

export interface TriggerConfig {
  schedule?: CronSchedule;
  event?: {
    source: string;
    type: string;
    filter?: Record<string, any>;
  };
  webhook?: {
    url: string;
    method: 'GET' | 'POST' | 'PUT' | 'DELETE';
    headers?: Record<string, string>;
    authentication?: {
      type: 'none' | 'basic' | 'bearer' | 'api_key';
      credentials?: Record<string, string>;
    };
  };
  file?: {
    path: string;
    pattern: string;
    action: 'created' | 'modified' | 'deleted';
  };
  condition?: {
    expression: string;
    checkInterval: number;
  };
}

export interface WorkflowQueue {
  id: string;
  name: string;
  priority: number;
  maxConcurrency: number;
  currentLoad: number;
  tasks: QueuedWorkflow[];
  metrics: QueueMetrics;
}

export interface QueuedWorkflow {
  id: string;
  workflowId: string;
  priority: number;
  queuedAt: Date;
  estimatedDuration: number;
  dependencies: string[];
  payload: any;
}

export interface QueueMetrics {
  totalProcessed: number;
  averageWaitTime: number;
  averageExecutionTime: number;
  throughput: number;
  errorRate: number;
}

export interface WorkflowAutomationAnalytics {
  successRate: number;
  failureRate: number;
  averageExecutionTime: number;
  resourceUtilization: {
    cpu: number;
    memory: number;
    gpu?: number;
  };
  costAnalysis: {
    totalCost: number;
    costPerExecution: number;
    costBreakdown: Record<string, number>;
  };
  trends: {
    executions: TimeSeriesData[];
    performance: TimeSeriesData[];
    errors: TimeSeriesData[];
  };
  bottlenecks: BottleneckAnalysis[];
  optimizationSuggestions: OptimizationSuggestion[];
}

export interface TimeSeriesData {
  timestamp: Date;
  value: number;
  metadata?: Record<string, any>;
}

export interface BottleneckAnalysis {
  nodeId: string;
  nodeName: string;
  averageExecutionTime: number;
  frequency: number;
  impact: 'low' | 'medium' | 'high';
  suggestions: string[];
}

export interface OptimizationSuggestion {
  id: string;
  type: 'performance' | 'cost' | 'reliability' | 'maintainability';
  priority: 'low' | 'medium' | 'high';
  title: string;
  description: string;
  estimatedImpact: string;
  implementation: string;
}