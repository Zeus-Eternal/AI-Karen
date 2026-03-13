"use client";

import React from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Agent, AgentCapability } from '../types';
import { AgentStatusBadge } from './AgentStatusBadge';
import { AgentCapabilityBadge } from './AgentCapabilityBadge';
import { AgentRating } from './AgentRating';
import { AgentPerformanceMetrics } from './AgentPerformanceMetrics';
import { cn } from '@/lib/utils';
import { formatRelativeTime, truncateText } from '@/lib/utils';

interface AgentCardProps {
  agent: Agent;
  onSelect?: (agent: Agent) => void;
  onCompare?: (agent: Agent) => void;
  showDetails?: boolean;
  compact?: boolean;
  showPerformance?: boolean;
  showRating?: boolean;
  className?: string;
}

export function AgentCard({
  agent,
  onSelect,
  onCompare,
  showDetails = false,
  compact = false,
  showPerformance = true,
  showRating = true,
  className,
}: AgentCardProps) {
  const {
    id,
    name,
    description,
    version,
    type,
    status,
    capabilities,
    specializations,
    tags,
    icon,
    avatar,
    developer,
    performance,
    ratings,
    pricing,
    isRecommended,
    isBeta,
    isDeprecated,
    lastUsed,
  } = agent;

  const handleCardClick = () => {
    onSelect?.(agent);
  };

  const handleCompareClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onCompare?.(agent);
  };

  const handleDetailsClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onSelect?.(agent);
  };

  if (compact) {
    return (
      <Card 
        className={cn(
          "cursor-pointer hover:shadow-md transition-shadow",
          className
        )}
        onClick={handleCardClick}
      >
        <CardContent className="p-4">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-2">
                <h3 className="font-semibold truncate">{name}</h3>
                <AgentStatusBadge status={status} size="sm" />
                {isRecommended && (
                  <div className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold bg-secondary text-secondary-foreground">
                    Recommended
                  </div>
                )}
                {isBeta && (
                  <div className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold text-foreground">
                    Beta
                  </div>
                )}
              </div>
              
              {description && (
                <p className="text-sm text-muted-foreground mb-2 line-clamp-2">
                  {truncateText(description, 100)}
                </p>
              )}
              
              <div className="flex items-center gap-2 mb-2 flex-wrap">
                <Badge variant="outline" className="text-xs">
                  {type}
                </Badge>
                {showRating && (
                  <AgentRating rating={ratings.average} count={ratings.count} size="sm" />
                )}
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">
                  by {developer.name}
                </span>
                <div className="flex items-center gap-2">
                  {showPerformance && (
                    <AgentPerformanceMetrics metrics={performance} compact />
                  )}
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card 
      className={cn(
        "cursor-pointer hover:shadow-lg transition-all duration-200",
        isDeprecated && "opacity-75",
        className
      )}
      onClick={handleCardClick}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              {/* Agent Avatar or Icon */}
              <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-primary/10 flex-shrink-0">
                {avatar ? (
                  <img 
                    src={avatar} 
                    alt={name}
                    className="w-8 h-8 rounded-md object-cover"
                  />
                ) : icon ? (
                  <div className="text-primary" dangerouslySetInnerHTML={{ __html: icon }} />
                ) : (
                  <div className="text-primary font-bold text-lg">
                    {name.charAt(0).toUpperCase()}
                  </div>
                )}
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold truncate">{name}</h3>
                  <Badge variant="outline" className="text-xs">
                    v{version}
                  </Badge>
                  <AgentStatusBadge status={status} size="sm" />
                  {isRecommended && (
                    <Badge variant="secondary" className="text-xs">
                      Recommended
                    </Badge>
                  )}
                  {isBeta && (
                    <Badge variant="outline" className="text-xs">
                      Beta
                    </Badge>
                  )}
                  {isDeprecated && (
                    <Badge variant="destructive" className="text-xs">
                      Deprecated
                    </Badge>
                  )}
                </div>
                
                <p className="text-xs text-muted-foreground">
                  by {developer.name}
                  {pricing && (
                    <span className="ml-2">
                      {pricing.model === 'free' ? (
                        <div className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold bg-secondary text-secondary-foreground">Free</div>
                      ) : (
                        <div className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold text-foreground">Paid</div>
                      )}
                    </span>
                  )}
                </p>
              </div>
            </div>
            
            {showDetails && (
              <button
                className={cn(
                  "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-8 px-3",
                  "border border-input bg-background hover:bg-accent hover:text-accent-foreground"
                )}
                onClick={handleDetailsClick}
              >
                Details
              </button>
            )}
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="pt-0">
        {/* Description */}
        {description && (
          <p className="text-sm text-muted-foreground mb-3">
            {truncateText(description, 150)}
          </p>
        )}
        
        {/* Capabilities */}
        <div className="mb-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Capabilities</span>
            <span className="text-xs text-muted-foreground">
              {capabilities.length} total
            </span>
          </div>
          <div className="flex flex-wrap gap-1">
            {capabilities.slice(0, 4).map((capability) => (
              <AgentCapabilityBadge 
                key={capability} 
                capability={capability} 
                size="sm" 
                showIcon={false}
              />
            ))}
            {capabilities.length > 4 && (
              <Badge variant="outline" className="text-xs">
                +{capabilities.length - 4} more
              </Badge>
            )}
          </div>
        </div>
        
        {/* Specializations */}
        {specializations.length > 0 && (
          <div className="mb-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">Specializations</span>
              <span className="text-xs text-muted-foreground">
                {specializations.length} total
              </span>
            </div>
            <div className="flex flex-wrap gap-1">
              {specializations.slice(0, 3).map((specialization) => (
                <Badge key={specialization} variant="outline" className="text-xs">
                  {specialization}
                </Badge>
              ))}
              {specializations.length > 3 && (
                <Badge variant="outline" className="text-xs">
                  +{specializations.length - 3} more
                </Badge>
              )}
            </div>
          </div>
        )}
        
        {/* Tags */}
        {tags.length > 0 && (
          <div className="mb-3">
            <div className="flex flex-wrap gap-1">
              {tags.slice(0, 5).map((tag) => (
                <Badge key={tag} variant="secondary" className="text-xs">
                  {tag}
                </Badge>
              ))}
              {tags.length > 5 && (
                <Badge variant="secondary" className="text-xs">
                  +{tags.length - 5} more
                </Badge>
              )}
            </div>
          </div>
        )}
        
        {/* Performance Metrics */}
        {showPerformance && (
          <div className="mb-3">
            <AgentPerformanceMetrics metrics={performance} />
          </div>
        )}
        
        {/* Rating */}
        {showRating && (
          <div className="mb-3">
            <AgentRating 
              rating={ratings.average} 
              count={ratings.count} 
              showCount={true}
            />
          </div>
        )}
        
        {/* Footer */}
        <div className="flex items-center justify-between pt-3 border-t">
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            {lastUsed && (
              <span>Last used {formatRelativeTime(lastUsed)}</span>
            )}
            <span>Created {formatRelativeTime(agent.createdAt)}</span>
          </div>
          
          <div className="flex items-center gap-2">
            {onCompare && (
              <button
                className={cn(
                  "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-8 px-3",
                  "border border-input bg-background hover:bg-accent hover:text-accent-foreground"
                )}
                onClick={handleCompareClick}
                title="Add to comparison"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Grid view agent card
interface AgentGridCardProps {
  agent: Agent;
  onSelect?: (agent: Agent) => void;
  onCompare?: (agent: Agent) => void;
  className?: string;
}

export function AgentGridCard({
  agent,
  onSelect,
  onCompare,
  className,
}: AgentGridCardProps) {
  const handleCardClick = () => {
    onSelect?.(agent);
  };

  const handleCompareClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onCompare?.(agent);
  };

  const {
    name,
    description,
    version,
    type,
    status,
    capabilities,
    developer,
    performance,
    ratings,
    pricing,
    isRecommended,
    isBeta,
    isDeprecated,
    avatar,
    icon,
  } = agent;

  return (
    <Card 
      className={cn(
        "cursor-pointer hover:shadow-lg transition-all duration-200 h-full",
        isDeprecated && "opacity-75",
        className
      )}
      onClick={handleCardClick}
    >
      <CardContent className="p-4 flex flex-col h-full">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2">
            {/* Agent Avatar or Icon */}
            <div className="flex items-center justify-center w-8 h-8 rounded-md bg-primary/10 flex-shrink-0">
              {avatar ? (
                <img 
                  src={avatar} 
                  alt={name}
                  className="w-6 h-6 rounded object-cover"
                />
              ) : icon ? (
                <div className="text-primary text-sm" dangerouslySetInnerHTML={{ __html: icon }} />
              ) : (
                <div className="text-primary font-bold text-sm">
                  {name.charAt(0).toUpperCase()}
                </div>
              )}
            </div>
            
            <div className="flex-1 min-w-0">
              <h3 className="font-medium text-sm truncate">{name}</h3>
              <div className="flex items-center gap-1">
                <Badge variant="outline" className="text-xs px-1 py-0">
                  v{version}
                </Badge>
                <AgentStatusBadge status={status} size="sm" showLabel={false} />
                {isRecommended && (
                  <Badge variant="secondary" className="text-xs px-1 py-0">
                    ★
                  </Badge>
                )}
              </div>
            </div>
          </div>
        </div>
        
        {/* Description */}
        {description && (
          <p className="text-xs text-muted-foreground mb-3 line-clamp-2 flex-1">
            {truncateText(description, 80)}
          </p>
        )}
        
        {/* Tags and Type */}
        <div className="flex flex-wrap gap-1 mb-3">
          <Badge variant="outline" className="text-xs">
            {type}
          </Badge>
          {capabilities.slice(0, 2).map((capability) => (
            <AgentCapabilityBadge 
              key={capability} 
              capability={capability} 
              size="sm" 
              showIcon={false}
            />
          ))}
          {capabilities.length > 2 && (
            <Badge variant="secondary" className="text-xs">
              +{capabilities.length - 2}
            </Badge>
          )}
        </div>
        
        {/* Performance and Rating */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <AgentPerformanceMetrics metrics={performance} compact />
            <AgentRating rating={ratings.average} size="sm" />
          </div>
          {pricing && (
            <div className={cn(
              "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold",
              pricing.model === 'free'
                ? "bg-secondary text-secondary-foreground"
                : "text-foreground"
            )}>
              {pricing.model === 'free' ? 'Free' : 'Paid'}
            </div>
          )}
        </div>
        
        {/* Footer */}
        <div className="mt-auto pt-3 border-t flex items-center justify-between">
          <span className="text-xs text-muted-foreground">
            by {developer.name}
          </span>
          <div className="flex items-center gap-1">
            {onCompare && (
              <button
                className={cn(
                  "inline-flex items-center justify-center rounded-md text-xs font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-6 px-2",
                  "border border-input bg-background hover:bg-accent hover:text-accent-foreground"
                )}
                onClick={handleCompareClick}
                title="Add to comparison"
              >
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// List view agent card (more compact)
interface AgentListCardProps {
  agent: Agent;
  onSelect?: (agent: Agent) => void;
  onCompare?: (agent: Agent) => void;
  className?: string;
}

export function AgentListCard({
  agent,
  onSelect,
  onCompare,
  className,
}: AgentListCardProps) {
  const handleCardClick = () => {
    onSelect?.(agent);
  };

  const handleCompareClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onCompare?.(agent);
  };

  const {
    name,
    description,
    version,
    type,
    status,
    capabilities,
    specializations,
    developer,
    performance,
    ratings,
    pricing,
    isRecommended,
    isBeta,
    isDeprecated,
  } = agent;

  return (
    <Card 
      className={cn(
        "cursor-pointer hover:shadow-md transition-shadow mb-3",
        isDeprecated && "opacity-75",
        className
      )}
      onClick={handleCardClick}
    >
      <CardContent className="p-4">
        <div className="flex items-center gap-4">
          {/* Status indicator */}
          <div className="flex-shrink-0">
            <AgentStatusBadge status={status} size="sm" showLabel={false} />
          </div>
          
          {/* Agent info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="font-semibold">{name}</h3>
              <Badge variant="outline" className="text-xs">
                v{version}
              </Badge>
              <div className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold text-foreground">
                {type}
              </div>
              {isRecommended && (
                <Badge variant="secondary" className="text-xs">
                  Recommended
                </Badge>
              )}
              {isBeta && (
                <Badge variant="outline" className="text-xs">
                  Beta
                </Badge>
              )}
            </div>
            
            <div className="flex items-center gap-4 text-sm text-muted-foreground mb-2">
              <span>by {developer.name}</span>
              <span>•</span>
              <span>{capabilities.length} capabilities</span>
              <span>•</span>
              <span>{specializations.length} specializations</span>
              {pricing && (
                <>
                  <span>•</span>
                  <span>{pricing.model === 'free' ? 'Free' : 'Paid'}</span>
                </>
              )}
            </div>
            
            {description && (
              <p className="text-sm text-muted-foreground line-clamp-1">
                {truncateText(description, 120)}
              </p>
            )}
          </div>
          
          {/* Performance and rating */}
          <div className="flex flex-col items-end gap-2 flex-shrink-0">
            <AgentRating rating={ratings.average} size="sm" />
            <AgentPerformanceMetrics metrics={performance} compact />
            {onCompare && (
              <button
                className={cn(
                  "inline-flex items-center justify-center rounded-md text-xs font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-6 px-2",
                  "border border-input bg-background hover:bg-accent hover:text-accent-foreground"
                )}
                onClick={handleCompareClick}
                title="Add to comparison"
              >
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14A2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}