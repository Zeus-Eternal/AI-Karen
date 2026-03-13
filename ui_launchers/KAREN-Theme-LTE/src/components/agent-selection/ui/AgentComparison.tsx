"use client";

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Agent, AgentComparison as AgentComparisonType } from '../types';
import { AgentStatusBadge } from './AgentStatusBadge';
import { AgentCapabilityBadge } from './AgentCapabilityBadge';
import { AgentRating } from './AgentRating';
import { AgentPerformanceMetrics } from './AgentPerformanceMetrics';
import { cn } from '@/lib/utils';

interface AgentComparisonProps {
  agents: Agent[];
  onClose?: () => void;
  onSelect?: (agent: Agent) => void;
  className?: string;
}

export function AgentComparison({
  agents,
  onClose,
  onSelect,
  className,
}: AgentComparisonProps) {
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);

  if (agents.length === 0) {
    return (
      <Card className={cn("w-full max-w-6xl mx-auto", className)}>
        <CardContent className="p-8 text-center">
          <p className="text-muted-foreground">No agents selected for comparison.</p>
        </CardContent>
      </Card>
    );
  }

  const handleSelectAgent = (agent: Agent) => {
    setSelectedAgent(agent);
    onSelect?.(agent);
  };

  const renderComparisonMatrix = () => {
    const allCapabilities = Array.from(
      new Set(agents.flatMap(agent => agent.capabilities))
    ).sort();

    const allSpecializations = Array.from(
      new Set(agents.flatMap(agent => agent.specializations))
    ).sort();

    return (
      <div className="space-y-8">
        {/* Basic Information */}
        <div>
          <h3 className="text-lg font-semibold mb-4">Basic Information</h3>
          <div className="border rounded-lg overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="bg-muted/50">
                  <th className="text-left p-3 font-medium">Feature</th>
                  {agents.map((agent) => (
                    <th key={agent.id} className="text-left p-3 font-medium">
                      {agent.name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                <tr className="border-t">
                  <td className="p-3 font-medium">Status</td>
                  {agents.map((agent) => (
                    <td key={agent.id} className="p-3">
                      <AgentStatusBadge status={agent.status} size="sm" />
                    </td>
                  ))}
                </tr>
                <tr className="border-t bg-muted/25">
                  <td className="p-3 font-medium">Type</td>
                  {agents.map((agent) => (
                    <td key={agent.id} className="p-3">
                      <Badge variant="outline" className="capitalize">
                        {agent.type}
                      </Badge>
                    </td>
                  ))}
                </tr>
                <tr className="border-t">
                  <td className="p-3 font-medium">Version</td>
                  {agents.map((agent) => (
                    <td key={agent.id} className="p-3">
                      {agent.version}
                    </td>
                  ))}
                </tr>
                <tr className="border-t bg-muted/25">
                  <td className="p-3 font-medium">Developer</td>
                  {agents.map((agent) => (
                    <td key={agent.id} className="p-3">
                      {agent.developer.name}
                    </td>
                  ))}
                </tr>
                <tr className="border-t">
                  <td className="p-3 font-medium">Rating</td>
                  {agents.map((agent) => (
                    <td key={agent.id} className="p-3">
                      <AgentRating 
                        rating={agent.ratings.average} 
                        count={agent.ratings.count} 
                        size="sm" 
                      />
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Capabilities */}
        <div>
          <h3 className="text-lg font-semibold mb-4">Capabilities</h3>
          <div className="border rounded-lg overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="bg-muted/50">
                  <th className="text-left p-3 font-medium">Capability</th>
                  {agents.map((agent) => (
                    <th key={agent.id} className="text-left p-3 font-medium">
                      {agent.name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {allCapabilities.map((capability) => (
                  <tr key={capability} className="border-t">
                    <td className="p-3">
                      <AgentCapabilityBadge capability={capability} size="sm" />
                    </td>
                    {agents.map((agent) => (
                      <td key={agent.id} className="p-3">
                        {agent.capabilities.includes(capability) ? (
                          <svg className="w-5 h-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                        ) : (
                          <svg className="w-5 h-5 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Performance Metrics */}
        <div>
          <h3 className="text-lg font-semibold mb-4">Performance Metrics</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {agents.map((agent) => (
              <Card key={agent.id} className="p-4">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                    {agent.avatar ? (
                      <img 
                        src={agent.avatar} 
                        alt={agent.name}
                        className="w-8 h-8 rounded-md object-cover"
                      />
                    ) : (
                      <div className="text-primary font-bold text-sm">
                        {agent.name.charAt(0).toUpperCase()}
                      </div>
                    )}
                  </div>
                  <div>
                    <h4 className="font-medium">{agent.name}</h4>
                    <AgentStatusBadge status={agent.status} size="sm" />
                  </div>
                </div>
                <AgentPerformanceMetrics metrics={agent.performance} compact />
              </Card>
            ))}
          </div>
        </div>

        {/* Pricing */}
        <div>
          <h3 className="text-lg font-semibold mb-4">Pricing</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {agents.map((agent) => (
              <Card key={agent.id} className="p-4">
                <h4 className="font-medium mb-2">{agent.name}</h4>
                {agent.pricing ? (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Model</span>
                      <Badge variant={agent.pricing.model === 'free' ? 'secondary' : 'outline'}>
                        {agent.pricing.model === 'free' ? 'Free' : 'Paid'}
                      </Badge>
                    </div>
                    {agent.pricing.costPerTask && (
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Cost/Task</span>
                        <span className="text-sm font-medium">
                          ${agent.pricing.costPerTask.toFixed(2)}
                        </span>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">Pricing not available</p>
                )}
              </Card>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderRecommendations = () => {
    // Calculate recommendations based on agent properties
    const recommendations = {
      bestOverall: agents.reduce((best, agent) => 
        agent.ratings.average > best.ratings.average ? agent : best
      ),
      bestPerformance: agents.reduce((best, agent) => 
        agent.performance.successRate > best.performance.successRate ? agent : best
      ),
      mostReliable: agents.reduce((best, agent) => 
        agent.performance.uptime > best.performance.uptime ? agent : best
      ),
      fastestResponse: agents.reduce((best, agent) => 
        agent.performance.averageResponseTime < best.performance.averageResponseTime ? agent : best
      ),
    };

    return (
      <div className="space-y-4">
        <h3 className="text-lg font-semibold mb-4">Recommendations</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card className="p-4">
            <h4 className="font-medium mb-2">Best Overall</h4>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                {recommendations.bestOverall.avatar ? (
                  <img 
                    src={recommendations.bestOverall.avatar} 
                    alt={recommendations.bestOverall.name}
                    className="w-6 h-6 rounded-md object-cover"
                  />
                ) : (
                  <div className="text-primary font-bold text-xs">
                    {recommendations.bestOverall.name.charAt(0).toUpperCase()}
                  </div>
                )}
              </div>
              <div>
                <p className="font-medium">{recommendations.bestOverall.name}</p>
                <AgentRating rating={recommendations.bestOverall.ratings.average} size="sm" />
              </div>
            </div>
          </Card>

          <Card className="p-4">
            <h4 className="font-medium mb-2">Best Performance</h4>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                {recommendations.bestPerformance.avatar ? (
                  <img 
                    src={recommendations.bestPerformance.avatar} 
                    alt={recommendations.bestPerformance.name}
                    className="w-6 h-6 rounded-md object-cover"
                  />
                ) : (
                  <div className="text-primary font-bold text-xs">
                    {recommendations.bestPerformance.name.charAt(0).toUpperCase()}
                  </div>
                )}
              </div>
              <div>
                <p className="font-medium">{recommendations.bestPerformance.name}</p>
                <p className="text-sm text-muted-foreground">
                  {recommendations.bestPerformance.performance.successRate.toFixed(1)}% success rate
                </p>
              </div>
            </div>
          </Card>

          <Card className="p-4">
            <h4 className="font-medium mb-2">Most Reliable</h4>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                {recommendations.mostReliable.avatar ? (
                  <img 
                    src={recommendations.mostReliable.avatar} 
                    alt={recommendations.mostReliable.name}
                    className="w-6 h-6 rounded-md object-cover"
                  />
                ) : (
                  <div className="text-primary font-bold text-xs">
                    {recommendations.mostReliable.name.charAt(0).toUpperCase()}
                  </div>
                )}
              </div>
              <div>
                <p className="font-medium">{recommendations.mostReliable.name}</p>
                <p className="text-sm text-muted-foreground">
                  {recommendations.mostReliable.performance.uptime.toFixed(1)}% uptime
                </p>
              </div>
            </div>
          </Card>

          <Card className="p-4">
            <h4 className="font-medium mb-2">Fastest Response</h4>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                {recommendations.fastestResponse.avatar ? (
                  <img 
                    src={recommendations.fastestResponse.avatar} 
                    alt={recommendations.fastestResponse.name}
                    className="w-6 h-6 rounded-md object-cover"
                  />
                ) : (
                  <div className="text-primary font-bold text-xs">
                    {recommendations.fastestResponse.name.charAt(0).toUpperCase()}
                  </div>
                )}
              </div>
              <div>
                <p className="font-medium">{recommendations.fastestResponse.name}</p>
                <p className="text-sm text-muted-foreground">
                  {(recommendations.fastestResponse.performance.averageResponseTime / 1000).toFixed(1)}s avg response
                </p>
              </div>
            </div>
          </Card>
        </div>
      </div>
    );
  };

  return (
    <Card className={cn("w-full max-w-6xl mx-auto", className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-2xl">Agent Comparison</CardTitle>
          {onClose && (
            <Button variant="ghost" size="sm" onClick={onClose}>
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </Button>
          )}
        </div>
        <p className="text-muted-foreground">
          Comparing {agents.length} agent{agents.length !== 1 ? 's' : ''}
        </p>
      </CardHeader>
      
      <CardContent className="p-6">
        {/* Tab Navigation */}
        <div className="flex space-x-1 border-b mb-6">
          <button
            className={cn(
              "px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors",
              "border-primary text-primary"
            )}
          >
            Comparison Matrix
          </button>
          <button
            className={cn(
              "px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors",
              "border-transparent text-muted-foreground hover:text-foreground"
            )}
          >
            Recommendations
          </button>
        </div>
        
        {/* Tab Content */}
        <div className="mt-6">
          {renderComparisonMatrix()}
        </div>
        
        <Separator className="my-6" />
        
        <div className="mt-6">
          {renderRecommendations()}
        </div>
        
        {/* Action Buttons */}
        <div className="flex justify-end gap-3 mt-6 pt-6 border-t">
          <Button variant="outline" onClick={onClose}>
            Close Comparison
          </Button>
          {selectedAgent && (
            <Button onClick={() => handleSelectAgent(selectedAgent)}>
              Select {selectedAgent.name}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}