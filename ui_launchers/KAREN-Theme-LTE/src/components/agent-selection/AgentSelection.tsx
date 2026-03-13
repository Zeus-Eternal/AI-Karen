"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { AgentSelectionProps, AgentSelectionContext } from './types';
import { useAgentSelectionStore } from './store/agentStore';
import { AgentCard } from './ui/AgentCard';
import { AgentDetails } from './ui/AgentDetails';
import { AgentFilters } from './ui/AgentFilters';
import { AgentComparison } from './ui/AgentComparison';
import { AgentRecommendations } from './ui/AgentRecommendations';
import { AgentConfiguration } from './ui/AgentConfiguration';
import { cn } from '@/lib/utils';

export function AgentSelection({
  className,
  onAgentSelect,
  onCompare,
  context,
  showRecommendations = true,
  maxComparisonAgents = 4,
  autoRefresh = false,
  refreshInterval = 30000, // 30 seconds
}: AgentSelectionProps) {
  const {
    // State
    agents,
    selectedAgent,
    comparisonAgents,
    recommendations,
    isLoading,
    error,
    filters,
    sortOptions,
    showDetails,
    showFilters,
    showComparison,
    showConfiguration,
    viewMode,
    configurationValues,
    selectionContext,
    
    // Actions
    fetchAgents,
    fetchAgent,
    selectAgent,
    deselectAgent,
    addToComparison,
    removeFromComparison,
    clearComparison,
    fetchRecommendations,
    updateConfiguration,
    resetConfiguration,
    setFilters,
    setSortOptions,
    clearFilters,
    setShowDetails,
    setShowFilters,
    setShowComparison,
    setShowConfiguration,
    setViewMode,
    setSelectionContext,
    clearError,
    reset,
  } = useAgentSelectionStore();

  const [activeView, setActiveView] = useState<'agents' | 'recommendations' | 'comparison' | 'configuration'>('agents');

  // Initialize context and fetch data
  useEffect(() => {
    if (context) {
      setSelectionContext(context);
    }
    
    // Fetch initial agents
    fetchAgents();
    
    // Fetch recommendations if enabled
    if (showRecommendations && context) {
      fetchRecommendations(context);
    }
    
    // Set up auto-refresh if enabled
    let interval: NodeJS.Timeout;
    if (autoRefresh) {
      interval = setInterval(() => {
        fetchAgents();
        if (showRecommendations && context) {
          fetchRecommendations(context);
        }
      }, refreshInterval);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [context, showRecommendations, autoRefresh, refreshInterval]);

  // Handle agent selection
  const handleAgentSelect = (agent: any, config?: any) => {
    selectAgent(agent);
    if (config) {
      updateConfiguration('global', config);
    }
    onAgentSelect?.(agent, config);
  };

  // Handle agent comparison
  const handleCompare = (agents: any[]) => {
    onCompare?.(agents);
  };

  // Handle view changes
  const handleViewChange = (view: typeof activeView) => {
    setActiveView(view);
    setShowDetails(false);
    setShowComparison(false);
    setShowConfiguration(false);
    
    if (view === 'comparison') {
      setShowComparison(true);
    } else if (view === 'configuration' && selectedAgent) {
      setShowConfiguration(true);
    }
  };

  // Render loading state
  if (isLoading && agents.length === 0) {
    return (
      <div className={cn("w-full max-w-6xl mx-auto p-6", className)}>
        <Card>
          <CardContent className="p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading agents...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Render error state
  if (error && agents.length === 0) {
    return (
      <div className={cn("w-full max-w-6xl mx-auto p-6", className)}>
        <Card>
          <CardContent className="p-8 text-center">
            <div className="text-red-500 mb-4">
              <svg className="w-8 h-8 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold mb-2">Error Loading Agents</h3>
            <p className="text-muted-foreground mb-4">{error}</p>
            <Button onClick={() => {
              clearError();
              fetchAgents();
            }}>
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Render main content
  return (
    <div className={cn("w-full max-w-6xl mx-auto p-6", className)}>
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-3xl font-bold">Agent Selection</h1>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-sm">
              {agents.length} agents available
            </Badge>
            {comparisonAgents.length > 0 && (
              <Badge variant="secondary" className="text-sm">
                {comparisonAgents.length} selected for comparison
              </Badge>
            )}
          </div>
        </div>
        
        {/* View Navigation */}
        <div className="flex space-x-1 border-b mb-6">
          <button
            className={cn(
              "px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors",
              activeView === 'agents'
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            )}
            onClick={() => handleViewChange('agents')}
          >
            All Agents
          </button>
          
          {showRecommendations && recommendations.length > 0 && (
            <button
              className={cn(
                "px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors",
                activeView === 'recommendations'
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              )}
              onClick={() => handleViewChange('recommendations')}
            >
              Recommendations
            </button>
          )}
          
          {comparisonAgents.length > 0 && (
            <button
              className={cn(
                "px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors",
                activeView === 'comparison'
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              )}
              onClick={() => handleViewChange('comparison')}
            >
              Comparison ({comparisonAgents.length})
            </button>
          )}
          
          {selectedAgent && (
            <button
              className={cn(
                "px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors",
                activeView === 'configuration'
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              )}
              onClick={() => handleViewChange('configuration')}
            >
              Configure {selectedAgent.name}
            </button>
          )}
        </div>
      </div>

      {/* Filters */}
      {showFilters && (
        <Card className="mb-6">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">Filters</CardTitle>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={clearFilters}>
                  Clear All
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowFilters(false)}
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-6">
            <AgentFilters
              filters={filters}
              onFiltersChange={setFilters}
              onClear={clearFilters}
              capabilities={[]}
              specializations={[]}
              developers={[]}
            />
          </CardContent>
        </Card>
      )}

      {/* Main Content */}
      <div className="space-y-6">
        {/* Agents View */}
        {activeView === 'agents' && (
          <div>
            {/* Toolbar */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowFilters(!showFilters)}
                >
                  <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
                  </svg>
                  Filters
                </Button>
                
                <div className="flex items-center border rounded-md">
                  <button
                    className={cn(
                      "px-3 py-1 text-sm",
                      viewMode === 'grid' ? "bg-muted" : ""
                    )}
                    onClick={() => setViewMode('grid')}
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                    </svg>
                  </button>
                  <button
                    className={cn(
                      "px-3 py-1 text-sm",
                      viewMode === 'list' ? "bg-muted" : ""
                    )}
                    onClick={() => setViewMode('list')}
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                    </svg>
                  </button>
                  <button
                    className={cn(
                      "px-3 py-1 text-sm",
                      viewMode === 'compact' ? "bg-muted" : ""
                    )}
                    onClick={() => setViewMode('compact')}
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                    </svg>
                  </button>
                </div>
              </div>
              
              {comparisonAgents.length > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleViewChange('comparison')}
                >
                  Compare Selected ({comparisonAgents.length})
                </Button>
              )}
            </div>
            
            {/* Agent Grid */}
            {agents.length === 0 ? (
              <Card>
                <CardContent className="p-8 text-center">
                  <p className="text-muted-foreground">No agents found matching your criteria.</p>
                  <Button variant="outline" className="mt-4" onClick={clearFilters}>
                    Clear Filters
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <div className={cn(
                viewMode === 'grid' && "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4",
                viewMode === 'list' && "space-y-4",
                viewMode === 'compact' && "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-2"
              )}>
                {agents.map((agent) => (
                  <AgentCard
                    key={agent.id}
                    agent={agent}
                    onSelect={handleAgentSelect}
                    onCompare={addToComparison}
                    compact={viewMode === 'compact'}
                    showDetails={showDetails}
                    showPerformance={true}
                    showRating={true}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {/* Recommendations View */}
        {activeView === 'recommendations' && (
          <AgentRecommendations
            recommendations={recommendations}
            context={selectionContext}
            onSelect={handleAgentSelect}
            onRefresh={() => fetchRecommendations(selectionContext)}
          />
        )}

        {/* Comparison View */}
        {activeView === 'comparison' && (
          <AgentComparison
            agents={comparisonAgents}
            onClose={() => {
              clearComparison();
              handleViewChange('agents');
            }}
            onSelect={handleAgentSelect}
          />
        )}

        {/* Configuration View */}
        {activeView === 'configuration' && selectedAgent && (
          <AgentConfiguration
            agent={selectedAgent}
            values={configurationValues}
            onChange={updateConfiguration}
            onReset={resetConfiguration}
            onSave={(config) => {
              updateConfiguration('global', config);
              handleAgentSelect(selectedAgent, config);
            }}
          />
        )}
      </div>

      {/* Agent Details Modal */}
      {showDetails && selectedAgent && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-background rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <AgentDetails
              agent={selectedAgent}
              onClose={() => setShowDetails(false)}
              onSelect={handleAgentSelect}
              onConfigure={(agent, config) => {
                updateConfiguration('global', config);
                handleAgentSelect(agent, config);
                setShowDetails(false);
                handleViewChange('configuration');
              }}
              showActions={true}
            />
          </div>
        </div>
      )}
    </div>
  );
}