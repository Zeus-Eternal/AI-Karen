'use client';

import React, { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  AlertTriangle,
  CheckCircle,
  Info,
  Brain,
  Target,
  Zap
} from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface ConfidenceMetrics {
  overall: number;
  reasoning: number;
  sources: number;
  consistency: number;
  completeness: number;
}

interface ConfidenceFactors {
  positive: Array<{
    factor: string;
    impact: number;
    description: string;
  }>;
  negative: Array<{
    factor: string;
    impact: number;
    description: string;
  }>;
}

interface ConfidenceScoringProps {
  confidence: number;
  metrics?: ConfidenceMetrics;
  factors?: ConfidenceFactors;
  reasoning?: {
    steps: number;
    averageConfidence: number;
    evidenceCount: number;
  };
  sources?: {
    count: number;
    averageReliability: number;
    averageRelevance: number;
  };
  className?: string;
  compact?: boolean;
  showDetails?: boolean;
}

export const ConfidenceScoring: React.FC<ConfidenceScoringProps> = ({
  confidence,
  metrics,
  factors,
  reasoning,
  sources,
  className = '',
  compact = false,
  showDetails = true
}) => {
  // Calculate confidence level and color
  const confidenceLevel = useMemo(() => {
    if (confidence >= 0.9) return { level: 'Excellent', color: 'text-green-600 bg-green-50 border-green-200', icon: CheckCircle };
    if (confidence >= 0.8) return { level: 'High', color: 'text-green-600 bg-green-50 border-green-200', icon: CheckCircle };
    if (confidence >= 0.6) return { level: 'Medium', color: 'text-yellow-600 bg-yellow-50 border-yellow-200', icon: Info };
    if (confidence >= 0.4) return { level: 'Low', color: 'text-orange-600 bg-orange-50 border-orange-200', icon: AlertTriangle };
    return { level: 'Very Low', color: 'text-red-600 bg-red-50 border-red-200', icon: AlertTriangle };
  }, [confidence]);

  // Default metrics if not provided
  const defaultMetrics: ConfidenceMetrics = useMemo(() => ({
    overall: confidence,
    reasoning: reasoning?.averageConfidence || confidence * 0.9,
    sources: sources ? (sources.averageReliability + sources.averageRelevance) / 2 : confidence * 0.8,
    consistency: confidence * 0.95,
    completeness: confidence * 0.85
  }), [confidence, reasoning, sources]);

  const finalMetrics = metrics || defaultMetrics;

  // Calculate trend
  const getTrend = (current: number, baseline: number = 0.7) => {
    const diff = current - baseline;
    if (Math.abs(diff) < 0.05) return { icon: Minus, color: 'text-gray-500', label: 'Stable' };
    if (diff > 0) return { icon: TrendingUp, color: 'text-green-600', label: 'Improving' };
    return { icon: TrendingDown, color: 'text-red-600', label: 'Declining' };
  };

  // Render compact version
  if (compact) {
    const Icon = confidenceLevel.icon;
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <div className={`flex items-center gap-2 ${className}`}>
              <Icon className="h-4 w-4 text-muted-foreground" />
              <div className={`px-2 py-1 rounded text-xs font-medium border ${confidenceLevel.color}`}>
                {Math.round(confidence * 100)}%
              </div>
              <span className="text-xs text-muted-foreground">
                {confidenceLevel.level}
              </span>
            </div>
          </TooltipTrigger>
          <TooltipContent>
            <div className="space-y-1">
              <p>Confidence: {Math.round(confidence * 100)}% ({confidenceLevel.level})</p>
              {reasoning && <p>Based on {reasoning.steps} reasoning steps</p>}
              {sources && <p>Using {sources.count} sources</p>}
            </div>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  return (
    <Card className={`${className}`}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Target className="h-5 w-5" />
          Confidence Analysis
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Overall Confidence */}
        <div className="text-center">
          <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg border ${confidenceLevel.color}`}>
            <confidenceLevel.icon className="h-5 w-5" />
            <span className="text-2xl font-bold">{Math.round(confidence * 100)}%</span>
            <span className="font-medium">{confidenceLevel.level}</span>
          </div>
          <p className="text-sm text-muted-foreground mt-2">
            Overall confidence in the AI response
          </p>
        </div>

        {/* Confidence Metrics */}
        {showDetails && (
          <div className="space-y-4">
            <h3 className="text-sm font-medium flex items-center gap-2">
              <Brain className="h-4 w-4" />
              Detailed Metrics
            </h3>
            
            <div className="grid grid-cols-1 gap-3">
              {/* Reasoning Quality */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Reasoning Quality</span>
                  <div className="flex items-center gap-2">
                    <span className="text-sm">{Math.round(finalMetrics.reasoning * 100)}%</span>
                    {(() => {
                      const trend = getTrend(finalMetrics.reasoning);
                      return <trend.icon className={`h-3 w-3 ${trend.color}`} />;
                    })()}
                  </div>
                </div>
                <Progress value={finalMetrics.reasoning * 100} className="h-2" />
                <p className="text-xs text-muted-foreground">
                  Based on logical consistency and evidence strength
                </p>
              </div>

              {/* Source Reliability */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Source Reliability</span>
                  <div className="flex items-center gap-2">
                    <span className="text-sm">{Math.round(finalMetrics.sources * 100)}%</span>
                    {(() => {
                      const trend = getTrend(finalMetrics.sources);
                      return <trend.icon className={`h-3 w-3 ${trend.color}`} />;
                    })()}
                  </div>
                </div>
                <Progress value={finalMetrics.sources * 100} className="h-2" />
                <p className="text-xs text-muted-foreground">
                  Quality and relevance of information sources
                </p>
              </div>

              {/* Response Consistency */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Response Consistency</span>
                  <div className="flex items-center gap-2">
                    <span className="text-sm">{Math.round(finalMetrics.consistency * 100)}%</span>
                    {(() => {
                      const trend = getTrend(finalMetrics.consistency);
                      return <trend.icon className={`h-3 w-3 ${trend.color}`} />;
                    })()}
                  </div>
                </div>
                <Progress value={finalMetrics.consistency * 100} className="h-2" />
                <p className="text-xs text-muted-foreground">
                  Internal consistency across reasoning steps
                </p>
              </div>

              {/* Completeness */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Response Completeness</span>
                  <div className="flex items-center gap-2">
                    <span className="text-sm">{Math.round(finalMetrics.completeness * 100)}%</span>
                    {(() => {
                      const trend = getTrend(finalMetrics.completeness);
                      return <trend.icon className={`h-3 w-3 ${trend.color}`} />;
                    })()}
                  </div>
                </div>
                <Progress value={finalMetrics.completeness * 100} className="h-2" />
                <p className="text-xs text-muted-foreground">
                  How thoroughly the response addresses the query
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Reasoning Stats */}
        {reasoning && (
          <div className="space-y-3">
            <h3 className="text-sm font-medium flex items-center gap-2">
              <Zap className="h-4 w-4" />
              Reasoning Statistics
            </h3>
            
            <div className="grid grid-cols-3 gap-4 text-center">
              <div className="space-y-1">
                <div className="text-lg font-bold text-primary">{reasoning.steps}</div>
                <div className="text-xs text-muted-foreground">Reasoning Steps</div>
              </div>
              <div className="space-y-1">
                <div className="text-lg font-bold text-primary">{reasoning.evidenceCount}</div>
                <div className="text-xs text-muted-foreground">Evidence Points</div>
              </div>
              <div className="space-y-1">
                <div className="text-lg font-bold text-primary">
                  {Math.round(reasoning.averageConfidence * 100)}%
                </div>
                <div className="text-xs text-muted-foreground">Avg Step Confidence</div>
              </div>
            </div>
          </div>
        )}

        {/* Source Stats */}
        {sources && (
          <div className="space-y-3">
            <h3 className="text-sm font-medium">Source Quality</h3>
            
            <div className="grid grid-cols-3 gap-4 text-center">
              <div className="space-y-1">
                <div className="text-lg font-bold text-primary">{sources.count}</div>
                <div className="text-xs text-muted-foreground">Sources Used</div>
              </div>
              <div className="space-y-1">
                <div className="text-lg font-bold text-primary">
                  {Math.round(sources.averageReliability * 100)}%
                </div>
                <div className="text-xs text-muted-foreground">Avg Reliability</div>
              </div>
              <div className="space-y-1">
                <div className="text-lg font-bold text-primary">
                  {Math.round(sources.averageRelevance * 100)}%
                </div>
                <div className="text-xs text-muted-foreground">Avg Relevance</div>
              </div>
            </div>
          </div>
        )}

        {/* Confidence Factors */}
        {factors && (
          <div className="space-y-4">
            <h3 className="text-sm font-medium">Confidence Factors</h3>
            
            {/* Positive Factors */}
            {factors.positive.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-green-600 flex items-center gap-2">
                  <TrendingUp className="h-4 w-4" />
                  Positive Factors
                </h4>
                <div className="space-y-2">
                  {factors.positive.map((factor, index) => (
                    <div key={index} className="flex items-center justify-between p-2 bg-green-50 border border-green-200 rounded">
                      <div className="flex-1">
                        <span className="text-sm font-medium">{factor.factor}</span>
                        <p className="text-xs text-muted-foreground">{factor.description}</p>
                      </div>
                      <Badge variant="secondary" className="text-xs">
                        +{Math.round(factor.impact * 100)}%
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Negative Factors */}
            {factors.negative.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-red-600 flex items-center gap-2">
                  <TrendingDown className="h-4 w-4" />
                  Limiting Factors
                </h4>
                <div className="space-y-2">
                  {factors.negative.map((factor, index) => (
                    <div key={index} className="flex items-center justify-between p-2 bg-red-50 border border-red-200 rounded">
                      <div className="flex-1">
                        <span className="text-sm font-medium">{factor.factor}</span>
                        <p className="text-xs text-muted-foreground">{factor.description}</p>
                      </div>
                      <Badge variant="destructive" className="text-xs">
                        -{Math.round(factor.impact * 100)}%
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Confidence Interpretation */}
        <div className="p-3 bg-muted/50 rounded-lg">
          <h4 className="text-sm font-medium mb-2">Interpretation</h4>
          <p className="text-sm text-muted-foreground">
            {confidence >= 0.9 && "This response has excellent confidence with strong reasoning and reliable sources. The information can be trusted with high certainty."}
            {confidence >= 0.8 && confidence < 0.9 && "This response has high confidence with good reasoning and sources. The information is likely accurate but consider verification for critical decisions."}
            {confidence >= 0.6 && confidence < 0.8 && "This response has medium confidence. While the reasoning is sound, consider additional verification or alternative perspectives."}
            {confidence >= 0.4 && confidence < 0.6 && "This response has low confidence. The information should be verified through additional sources before making important decisions."}
            {confidence < 0.4 && "This response has very low confidence. The information is uncertain and should be thoroughly verified through multiple reliable sources."}
          </p>
        </div>
      </CardContent>
    </Card>
  );
};

export default ConfidenceScoring;