"use client";

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Agent, AgentConfigurationValues } from '../types';
import { AgentStatusBadge } from './AgentStatusBadge';
import { AgentCapabilityBadge } from './AgentCapabilityBadge';
import { AgentRating } from './AgentRating';
import { AgentPerformanceMetrics } from './AgentPerformanceMetrics';
import { cn } from '@/lib/utils';
import { formatRelativeTime } from '@/lib/utils';

interface AgentDetailsProps {
  agent: Agent;
  onClose?: () => void;
  onSelect?: (agent: Agent, configuration?: AgentConfigurationValues) => void;
  onConfigure?: (agent: Agent, config: AgentConfigurationValues) => void;
  showActions?: boolean;
  className?: string;
}

export function AgentDetails({
  agent,
  onClose,
  onSelect,
  onConfigure,
  showActions = true,
  className,
}: AgentDetailsProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'capabilities' | 'performance' | 'configuration' | 'reviews'>('overview');
  const [configurationValues, setConfigurationValues] = useState<AgentConfigurationValues>({});
  const [showFullDescription, setShowFullDescription] = useState(false);

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
    configuration,
    useCases,
    requirements,
    compatibility,
    pricing,
    documentation,
    createdAt,
    updatedAt,
    lastUsed,
    isRecommended,
    isBeta,
    isDeprecated,
  } = agent;

  const handleSelect = () => {
    onSelect?.(agent, configurationValues);
  };

  const handleConfigure = () => {
    onConfigure?.(agent, configurationValues);
  };

  const handleConfigurationChange = (configId: string, value: any) => {
    setConfigurationValues(prev => ({
      ...prev,
      [configId]: value,
    }));
  };

  const resetConfiguration = () => {
    const defaultValues: AgentConfigurationValues = {};
    configuration.forEach(config => {
      defaultValues[config.id] = config.defaultValue;
    });
    setConfigurationValues(defaultValues);
  };

  const renderOverviewTab = () => (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start gap-4 mb-6">
        <div className="flex items-center justify-center w-16 h-16 rounded-lg bg-primary/10 flex-shrink-0">
          {avatar ? (
            <img 
              src={avatar} 
              alt={name}
              className="w-12 h-12 rounded-md object-cover"
            />
          ) : icon ? (
            <div className="text-primary text-2xl" dangerouslySetInnerHTML={{ __html: icon }} />
          ) : (
            <div className="text-primary font-bold text-2xl">
              {name.charAt(0).toUpperCase()}
            </div>
          )}
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-2xl font-bold">{name}</h1>
            <div className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold text-foreground">
              v{version}
            </div>
            <AgentStatusBadge status={status} />
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
            {isDeprecated && (
              <div className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold bg-destructive text-destructive-foreground">
                Deprecated
              </div>
            )}
          </div>
          
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span>by {developer.name}</span>
            {developer.website && (
              <a 
                href={developer.website}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:underline"
              >
                Website
              </a>
            )}
            {developer.email && (
              <a 
                href={`mailto:${developer.email}`}
                className="text-primary hover:underline"
              >
                Contact
              </a>
            )}
          </div>
          
          <div className="text-sm text-muted-foreground">
            Created {formatRelativeTime(createdAt)}
            {updatedAt && ` • Updated ${formatRelativeTime(updatedAt)}`}
            {lastUsed && ` • Last used ${formatRelativeTime(lastUsed)}`}
          </div>
        </div>
      </div>

      {/* Description */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-lg font-semibold">Description</h2>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowFullDescription(!showFullDescription)}
          >
            {showFullDescription ? 'Show Less' : 'Show More'}
          </Button>
        </div>
        <p className={cn("text-muted-foreground", showFullDescription ? "" : "line-clamp-3")}>
          {description}
        </p>
      </div>

      {/* Tags and Specializations */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {tags.length > 0 && (
          <div>
            <h3 className="text-lg font-semibold mb-3">Tags</h3>
            <div className="flex flex-wrap gap-2">
              {tags.map((tag) => (
                <Badge key={tag} variant="secondary" className="text-sm">
                  {tag}
                </Badge>
              ))}
            </div>
          </div>
        )}
        
        {specializations.length > 0 && (
          <div>
            <h3 className="text-lg font-semibold mb-3">Specializations</h3>
            <div className="flex flex-wrap gap-2">
              {specializations.map((specialization) => (
                <Badge key={specialization} variant="outline" className="text-sm">
                  {specialization}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Performance and Rating */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <h3 className="text-lg font-semibold mb-3">Performance</h3>
          <AgentPerformanceMetrics metrics={performance} showDetails />
        </div>
        
        <div>
          <h3 className="text-lg font-semibold mb-3">Rating</h3>
          <div className="space-y-2">
            <AgentRating rating={ratings.average} count={ratings.count} size="lg" />
            {ratings.count > 0 && (
              <div className="text-sm text-muted-foreground">
                {ratings.count.toLocaleString()} {ratings.count === 1 ? 'rating' : 'ratings'}
              </div>
            )}
            {ratings.distribution && (
              <div className="space-y-1">
                {[5, 4, 3, 2, 1].map((rating) => (
                  <div key={rating} className="flex items-center gap-2">
                    <span className="text-sm w-8">{rating}</span>
                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-yellow-400 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${(ratings.distribution?.[rating] || 0) / ratings.count * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Pricing */}
      {pricing && (
        <div>
          <h3 className="text-lg font-semibold mb-3">Pricing</h3>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Model</span>
              <div className={cn(
                "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold",
                pricing.model === 'free'
                  ? "bg-secondary text-secondary-foreground"
                  : "text-foreground"
              )}>
                {pricing.model === 'free' ? 'Free' : 'Paid'}
              </div>
            </div>
            
            {pricing.costPerTask && (
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Cost per Task</span>
                <span className="text-sm">${pricing.costPerTask.toFixed(2)}</span>
              </div>
            )}
            
            {pricing.subscriptionPlans && pricing.subscriptionPlans.length > 0 && (
              <div>
                <span className="text-sm font-medium mb-2">Subscription Plans</span>
                <div className="space-y-2">
                  {pricing.subscriptionPlans.map((plan, index) => (
                    <Card key={index} className="p-4">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium">{plan.name}</h4>
                        <span className="text-lg font-semibold">${plan.price.toFixed(2)}</span>
                      </div>
                      <ul className="text-sm space-y-1">
                        {plan.features.map((feature, idx) => (
                          <li key={idx} className="flex items-start gap-2">
                            <svg className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L7 5m0 4l-4-4m0 4l4 4m0 0v6M7 11l-3-3m0 0l-4 4" />
                            </svg>
                            <span>{feature}</span>
                          </li>
                        ))}
                      </ul>
                    </Card>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );

  const renderCapabilitiesTab = () => (
    <div className="space-y-6">
      <h2 className="text-xl font-bold mb-4">Capabilities</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {capabilities.map((capability) => (
          <Card key={capability} className="p-4">
            <div className="flex items-center gap-3 mb-2">
              <AgentCapabilityBadge capability={capability} size="md" />
              <h3 className="font-semibold capitalize">
                {capability.replace(/-/g, ' ')}
              </h3>
            </div>
            <p className="text-sm text-muted-foreground">
              {getCapabilityDescription(capability)}
            </p>
          </Card>
        ))}
      </div>
    </div>
  );

  const getCapabilityDescription = (capability: string) => {
    const descriptions: Record<string, string> = {
      'text-generation': 'Generates human-like text content for various purposes including creative writing, summarization, and conversation.',
      'code-generation': 'Writes, analyzes, and debugs code in multiple programming languages with best practices.',
      'data-analysis': 'Processes, analyzes, and visualizes data to extract insights and patterns.',
      'image-processing': 'Analyzes, processes, and manipulates images including recognition, enhancement, and generation.',
      'audio-processing': 'Processes, analyzes, and manipulates audio files including transcription and enhancement.',
      'video-processing': 'Analyzes, processes, and manipulates video content including transcoding and analysis.',
      'web-scraping': 'Extracts data from websites automatically for data collection and analysis.',
      'api-integration': 'Connects to and interacts with external APIs to extend functionality.',
      'database-query': 'Queries and manipulates databases to retrieve and store information efficiently.',
      'file-processing': 'Processes, converts, and manages various file formats and operations.',
      'natural-language-understanding': 'Understands and interprets human language with context awareness.',
      'translation': 'Translates text between multiple languages with high accuracy.',
      'summarization': 'Creates concise summaries of longer text documents and conversations.',
      'classification': 'Categorizes data into predefined classes based on features and patterns.',
      'recommendation': 'Provides personalized suggestions based on user preferences and behavior.',
      'automation': 'Automates repetitive tasks and workflows to increase efficiency.',
      'monitoring': 'Continuously monitors systems and processes for performance and issues.',
      'security-analysis': 'Analyzes systems and data for security vulnerabilities and threats.',
    };
    
    return descriptions[capability] || 'No description available.';
  };

  const renderPerformanceTab = () => (
    <div className="space-y-6">
      <h2 className="text-xl font-bold mb-4">Performance Metrics</h2>
      <AgentPerformanceMetrics metrics={performance} showDetails={true} />
    </div>
  );

  const renderConfigurationTab = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold">Configuration</h2>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={resetConfiguration}
          >
            Reset to Defaults
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleConfigure}
          >
            Apply Configuration
          </Button>
        </div>
      </div>
      
      <div className="space-y-6">
        {configuration.map((config) => (
          <div key={config.id} className="space-y-2">
            <div>
              <label className="block text-sm font-medium">
                {config.label}
                {config.required && <span className="text-red-500">*</span>}
              </label>
              {config.description && (
                <p className="text-xs text-muted-foreground mt-1">
                  {config.description}
                </p>
              )}
            </div>
            
            <div>
              {config.type === 'string' && (
                <input
                  type="text"
                  value={configurationValues[config.id] || config.defaultValue || ''}
                  onChange={(e) => handleConfigurationChange(config.id, e.target.value)}
                  placeholder={config.defaultValue || ''}
                  className="w-full p-2 border rounded-md"
                  required={config.required}
                />
              )}
              
              {config.type === 'number' && (
                <input
                  type="number"
                  value={configurationValues[config.id] || config.defaultValue || ''}
                  onChange={(e) => handleConfigurationChange(config.id, e.target.value)}
                  placeholder={config.defaultValue?.toString() || ''}
                  className="w-full p-2 border rounded-md"
                  min={config.validation?.min}
                  max={config.validation?.max}
                  required={config.required}
                />
              )}
              
              {config.type === 'boolean' && (
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={configurationValues[config.id] ?? config.defaultValue ?? false}
                    onChange={(e) => handleConfigurationChange(config.id, e.target.checked)}
                    className="rounded"
                  />
                  <label className="text-sm">{config.label}</label>
                </div>
              )}
              
              {config.type === 'select' && config.options && (
                <select
                  value={configurationValues[config.id] || config.defaultValue || ''}
                  onChange={(e) => handleConfigurationChange(config.id, e.target.value)}
                  className="w-full p-2 border rounded-md"
                  required={config.required}
                >
                  <option value="">Select...</option>
                  {config.options.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              )}
              
              {config.type === 'textarea' && (
                <textarea
                  value={configurationValues[config.id] || config.defaultValue || ''}
                  onChange={(e) => handleConfigurationChange(config.id, e.target.value)}
                  placeholder={config.defaultValue || ''}
                  className="w-full p-2 border rounded-md min-h-[100px]"
                  required={config.required}
                  rows={4}
                />
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderReviewsTab = () => (
    <div className="space-y-6">
      <h2 className="text-xl font-bold mb-4">User Reviews</h2>
      
      {ratings.count > 0 ? (
        <div className="space-y-4">
          {/* Mock reviews data for now - in a real app this would come from the agent data */}
          {[
            { userId: 'user1', rating: 5, timestamp: '2023-01-01T00:00:00Z', helpful: true, review: 'Excellent agent!' },
            { userId: 'user2', rating: 4, timestamp: '2023-01-02T00:00:00Z', helpful: false, review: 'Good but needs improvement' },
            { userId: 'user3', rating: 5, timestamp: '2023-01-03T00:00:00Z', helpful: true, review: 'Works perfectly' }
          ].slice(0, 5).map((review: any, index: number) => (
            <Card key={index} className="p-4">
              <div className="flex items-start gap-3 mb-2">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
                    <span className="text-sm font-medium">
                      {review.userId.charAt(0).toUpperCase()}
                    </span>
                  </div>
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium">{review.userId}</span>
                    <AgentRating rating={review.rating} size="sm" />
                    <span className="text-xs text-muted-foreground">
                      {formatRelativeTime(review.timestamp)}
                    </span>
                  </div>
                  
                  {review.helpful !== undefined && (
                    <Badge variant={review.helpful ? 'secondary' : 'outline'} className="text-xs">
                      {review.helpful ? 'Helpful' : 'Not Helpful'}
                    </Badge>
                  )}
                </div>
                
                {review.review && (
                  <p className="text-sm text-muted-foreground mt-2">
                    {review.review}
                  </p>
                )}
              </div>
            </Card>
          ))}
          
          {false && (
            <div className="text-center">
              <Button variant="outline" size="sm">
                Load More Reviews
              </Button>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center py-8 text-muted-foreground">
          No reviews yet. Be the first to review this agent!
        </div>
      )}
    </div>
  );

  const tabs = [
    { id: 'overview', label: 'Overview', content: renderOverviewTab() },
    { id: 'capabilities', label: 'Capabilities', content: renderCapabilitiesTab() },
    { id: 'performance', label: 'Performance', content: renderPerformanceTab() },
    { id: 'configuration', label: 'Configuration', content: renderConfigurationTab() },
    { id: 'reviews', label: 'Reviews', content: renderReviewsTab() },
  ];

  return (
    <Card className={cn("w-full max-w-4xl mx-auto", className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-2xl">{name}</CardTitle>
          {onClose && (
            <Button variant="ghost" size="sm" onClick={onClose}>
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </Button>
          )}
        </div>
      </CardHeader>
      
      <CardContent className="p-6">
        {/* Tab Navigation */}
        <div className="flex space-x-1 border-b mb-6">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              className={cn(
                "px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors",
                activeTab === tab.id
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              )}
              onClick={() => setActiveTab(tab.id as 'overview' | 'capabilities' | 'performance' | 'configuration' | 'reviews')}
            >
              {tab.label}
            </button>
          ))}
        </div>
        
        {/* Tab Content */}
        <div className="mt-6">
          {tabs.find(tab => tab.id === activeTab)?.content}
        </div>
        
        {/* Action Buttons */}
        {showActions && (
          <div className="flex justify-end gap-3 mt-6 pt-6 border-t">
            <button
              className={cn(
                "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-9 px-3",
                "border border-input bg-background hover:bg-accent hover:text-accent-foreground"
              )}
              onClick={handleSelect}
            >
              Select Agent
            </button>
            {onConfigure && (
              <button
                className={cn(
                  "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-9 px-3",
                  "bg-primary text-primary-foreground hover:bg-primary/90"
                )}
                onClick={handleConfigure}
              >
                Configure & Select
              </button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}