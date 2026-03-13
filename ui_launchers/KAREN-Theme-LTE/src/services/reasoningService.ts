/**
 * Reasoning Service
 * Provides AI reasoning and logic services
 */

export interface ReasoningRequest {
  query: string;
  context?: Record<string, unknown>;
  options?: {
    maxTokens?: number;
    temperature?: number;
    model?: string;
    reasoningMode?: 'chain_of_thought' | 'step_by_step' | 'direct';
  };
}

export interface ReasoningResponse {
  result: string;
  reasoning: string;
  confidence: number;
  tokensUsed: number;
  processingTime: number;
  metadata?: Record<string, unknown>;
}

export interface ReasoningStep {
  step: number;
  description: string;
  data: unknown;
  confidence: number;
  timestamp: string;
}

export class ReasoningService {
  private baseUrl: string;

  constructor(baseUrl: string = '/api') {
    this.baseUrl = baseUrl;
  }

  /**
   * Perform reasoning on a query
   */
  async performReasoning(request: ReasoningRequest): Promise<ReasoningResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/reasoning`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request)
      });

      if (!response.ok) {
        throw new Error(`Reasoning request failed: ${response.statusText}`);
      }

      const data: ReasoningResponse = await response.json();
      return data;
    } catch (error) {
      console.error('Reasoning service error:', error);
      throw error;
    }
  }

  /**
   * Get reasoning steps for a query
   */
  async getReasoningSteps(query: string): Promise<ReasoningStep[]> {
    try {
      const response = await fetch(`${this.baseUrl}/reasoning/steps?query=${encodeURIComponent(query)}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to get reasoning steps: ${response.statusText}`);
      }

      const data: ReasoningStep[] = await response.json();
      return data;
    } catch (error) {
      console.error('Get reasoning steps error:', error);
      throw error;
    }
  }

  /**
   * Analyze reasoning patterns
   */
  async analyzeReasoningPatterns(queries: string[]): Promise<{
    patterns: Array<{
      pattern: string;
      frequency: number;
      confidence: number;
    }>;
    metadata: Record<string, unknown>;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/reasoning/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ queries })
      });

      if (!response.ok) {
        throw new Error(`Failed to analyze reasoning patterns: ${response.statusText}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Analyze reasoning patterns error:', error);
      throw error;
    }
  }

  /**
   * Get reasoning statistics
   */
  async getReasoningStats(timeframe: 'day' | 'week' | 'month' = 'day'): Promise<{
    totalQueries: number;
    averageConfidence: number;
    topPatterns: Array<{
      pattern: string;
      count: number;
    }>;
    processingTime: number;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/reasoning/stats?timeframe=${timeframe}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to get reasoning stats: ${response.statusText}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Get reasoning stats error:', error);
      throw error;
    }
  }
}

// Create singleton instance
export const reasoningService = new ReasoningService();
export default reasoningService;
