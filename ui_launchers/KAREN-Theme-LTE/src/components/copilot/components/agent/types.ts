// Type definitions for Agent Selection components

export interface Theme {
  colors: {
    primary: string;
    secondary: string;
    background: string;
    surface: string;
    text: string;
    textSecondary: string;
    border: string;
    error: string;
    warning: string;
    success: string;
    info: string;
  };
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
    xxl: string;
  };
  typography: {
    fontFamily: string;
    fontSize: {
      xs: string;
      sm: string;
      base: string;
      lg: string;
      xl: string;
      xxl: string;
    };
    fontWeight: {
      light: number;
      normal: number;
      medium: number;
      semibold: number;
      bold: number;
    };
  };
  borderRadius: string;
  shadows: {
    sm: string;
    md: string;
    lg: string;
  };
}

export enum AgentStatus {
  AVAILABLE = 'available',
  BUSY = 'busy',
  OFFLINE = 'offline',
  MAINTENANCE = 'maintenance'
}

export enum AgentType {
  GENERAL = 'general',
  SPECIALIST = 'specialist',
  CREATIVE = 'creative',
  ANALYTICAL = 'analytical',
  RESEARCH = 'research'
}

export enum AgentCapability {
  TEXT_GENERATION = 'text_generation',
  CODE_GENERATION = 'code_generation',
  DATA_ANALYSIS = 'data_analysis',
  RESEARCH = 'research',
  TRANSLATION = 'translation',
  SUMMARIZATION = 'summarization',
  CREATIVE_WRITING = 'creative_writing',
  PROBLEM_SOLVING = 'problem_solving',
  PLANNING = 'planning',
  CONVERSATION = 'conversation'
}

export interface AgentPersona {
  name: string;
  description: string;
  personality: string;
  communicationStyle: string;
  expertise: string[];
  avatar?: string;
  background?: string;
  tone: 'formal' | 'casual' | 'friendly' | 'professional';
}

export interface AgentCapabilityDetail {
  capability: AgentCapability;
  name: string;
  description: string;
  proficiency: number; // 1-5 scale
  enabled: boolean;
}

export interface Agent {
  id: string;
  name: string;
  type: AgentType;
  status: AgentStatus;
  persona: AgentPersona;
  capabilities: AgentCapabilityDetail[];
  createdAt: Date;
  lastActive?: Date;
  performance?: {
    tasksCompleted: number;
    averageResponseTime: number; // in seconds
    successRate: number; // 0-1 percentage
    userRating?: number; // 1-5 scale
  };
  metadata?: Record<string, any>;
}

export interface AgentFilter {
  status?: AgentStatus[];
  type?: AgentType[];
  capabilities?: AgentCapability[];
  searchQuery?: string;
}

export interface AgentFormData {
  name: string;
  type: AgentType;
  persona: AgentPersona;
  capabilities: AgentCapability[];
}

export interface AgentCustomizationOptions {
  persona: Partial<AgentPersona>;
  capabilities: Partial<Record<AgentCapability, boolean>>;
  settings: {
    responseLength: 'concise' | 'normal' | 'detailed';
    creativityLevel: number; // 1-5 scale
    formalityLevel: number; // 1-5 scale
  };
}