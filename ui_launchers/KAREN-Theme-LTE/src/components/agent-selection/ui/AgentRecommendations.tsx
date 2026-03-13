"use client";

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Agent, AgentRecommendation, AgentSelectionContext } from '../types';
import { AgentStatusBadge } from './AgentStatusBadge';
import { AgentCapabilityBadge } from './AgentCapabilityBadge';
import { AgentRating } from './AgentRating';
import { cn } from '@/lib/utils';

interface AgentRecommendationsProps {
  recommendations: AgentRecommendation[];
  context: AgentSelectionContext;
  onSelect?: (agent: Agent) => void;
  onRefresh?: () => void;
  className?: string;
}

export function AgentRecommendations({
  recommendations,
  context,
  onSelect,
  onRefresh,
  className,
}: AgentRecommendationsProps) {
  const handleSelectAgent = (agent: Agent) => {
    onSelect?.(agent);
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 80) return 'text-blue-600';
    if (score >= 70) return 'text-yellow-600';
    return 'text-gray-600';
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 90) return 'bg-green-100 text-green-800';
    if (confidence >= 80) return 'bg-blue-100 text-blue-800';
    if (confidence >= 70) return 'bg-yellow-100 text-yellow-800';
    return 'bg-gray-100 text-gray-800';
  };

  if (recommendations.length === 0) {
    return (
      <Card className={cn("w-full", className)}>
        <CardHeader>
          <CardTitle className="text-xl">Agent Recommendations</CardTitle>
        </CardHeader>
        <CardContent className="p-8 text-center">
          <div className="space-y-4">
            <p className="text-muted-foreground">
              No recommendations available for the current context.
            </p>
            {onRefresh && (
              <Button variant="outline" onClick={onRefresh}>
                Refresh Recommendations
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-xl">Agent Recommendations</CardTitle>
          {onRefresh && (
            <Button variant="ghost" size="sm" onClick={onRefresh}>
              <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh
            </Button>
          )}
        </div>
        {context.taskType && (
          <p className="text-sm text-muted-foreground">
            Based on task type: <span className="font-medium">{context.taskType}</span>
          </p>
        )}
      </CardHeader>
      
      <CardContent className="p-6">
        <div className="space-y-6">
          {recommendations.map((recommendation, index) => (
            <Card key={recommendation.agent.id} className="p-6">
              <div className="flex items-start gap-4">
                {/* Agent Avatar/Icon */}
                <div className="flex items-center justify-center w-16 h-16 rounded-lg bg-primary/10 flex-shrink-0">
                  {recommendation.agent.avatar ? (
                    <img 
                      src={recommendation.agent.avatar} 
                      alt={recommendation.agent.name}
                      className="w-12 h-12 rounded-md object-cover"
                    />
                  ) : recommendation.agent.icon ? (
                    <div className="text-primary text-2xl" dangerouslySetInnerHTML={{ __html: recommendation.agent.icon }} />
                  ) : (
                    <div className="text-primary font-bold text-2xl">
                      {recommendation.agent.name.charAt(0).toUpperCase()}
                    </div>
                  )}
                </div>
                
                {/* Agent Information */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold">{recommendation.agent.name}</h3>
                    <AgentStatusBadge status={recommendation.agent.status} />
                    {recommendation.agent.isRecommended && (
                      <Badge variant="secondary" className="text-xs">
                        Recommended
                      </Badge>
                    )}
                  </div>
                  
                  <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
                    {recommendation.agent.description}
                  </p>
                  
                  {/* Score and Confidence */}
                  <div className="flex items-center gap-4 mb-3">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">Match Score:</span>
                      <span className={cn("text-lg font-bold", getScoreColor(recommendation.score))}>
                        {recommendation.score}%
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">Confidence:</span>
                      <Badge className={getConfidenceColor(recommendation.confidence)}>
                        {recommendation.confidence}%
                      </Badge>
                    </div>
                  </div>
                  
                  {/* Rating */}
                  <div className="flex items-center gap-2 mb-3">
                    <AgentRating 
                      rating={recommendation.agent.ratings.average} 
                      count={recommendation.agent.ratings.count} 
                      size="sm" 
                    />
                  </div>
                  
                  {/* Key Capabilities */}
                  <div className="flex flex-wrap gap-2 mb-3">
                    {recommendation.agent.capabilities.slice(0, 4).map((capability) => (
                      <AgentCapabilityBadge 
                        key={capability} 
                        capability={capability} 
                        size="sm" 
                      />
                    ))}
                    {recommendation.agent.capabilities.length > 4 && (
                      <Badge variant="outline" className="text-xs">
                        +{recommendation.agent.capabilities.length - 4} more
                      </Badge>
                    )}
                  </div>
                  
                  {/* Recommendation Reasons */}
                  {recommendation.reasons.length > 0 && (
                    <div className="mb-4">
                      <h4 className="text-sm font-medium mb-2">Why this agent?</h4>
                      <ul className="text-sm text-muted-foreground space-y-1">
                        {recommendation.reasons.slice(0, 3).map((reason, idx) => (
                          <li key={idx} className="flex items-start gap-2">
                            <svg className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                            <span>{reason}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {/* Context Information */}
                  {recommendation.context && (
                    <div className="mb-4">
                      <h4 className="text-sm font-medium mb-2">Context</h4>
                      <p className="text-sm text-muted-foreground">{recommendation.context}</p>
                    </div>
                  )}
                  
                  {/* Action Buttons */}
                  <div className="flex gap-2">
                    <Button 
                      onClick={() => handleSelectAgent(recommendation.agent)}
                      className="flex-1"
                    >
                      Select Agent
                    </Button>
                    <Button variant="outline" size="sm">
                      View Details
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
        
        {/* Context Summary */}
        {context && (
          <div className="mt-8 p-4 bg-muted/30 rounded-lg">
            <h3 className="text-sm font-medium mb-2">Recommendation Context</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              {context.taskType && (
                <div>
                  <span className="font-medium">Task Type:</span> {context.taskType}
                </div>
              )}
              {context.taskDescription && (
                <div className="md:col-span-2">
                  <span className="font-medium">Task Description:</span> {context.taskDescription}
                </div>
              )}
              {context.userPreferences?.preferredCapabilities && context.userPreferences.preferredCapabilities.length > 0 && (
                <div>
                  <span className="font-medium">Preferred Capabilities:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {context.userPreferences.preferredCapabilities.map((capability) => (
                      <AgentCapabilityBadge key={capability} capability={capability} size="sm" />
                    ))}
                  </div>
                </div>
              )}
              {context.userPreferences?.performanceRequirements && (
                <div>
                  <span className="font-medium">Performance Requirements:</span>
                  <ul className="mt-1 space-y-1">
                    {context.userPreferences.performanceRequirements.maxResponseTime && (
                      <li>Max Response Time: {context.userPreferences.performanceRequirements.maxResponseTime}ms</li>
                    )}
                    {context.userPreferences.performanceRequirements.minSuccessRate && (
                      <li>Min Success Rate: {context.userPreferences.performanceRequirements.minSuccessRate}%</li>
                    )}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}