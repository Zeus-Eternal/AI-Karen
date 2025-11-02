
"use client";
import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { format } from 'date-fns';
import { useToast } from '@/hooks/use-toast';

import { } from 'lucide-react';



import { } from '@/components/ui/collapsible';

import { } from '@/components/ui/tooltip';

import { } from '@/types/enhanced-chat';

interface ReasoningVisualizationProps {
  reasoning: ReasoningChain;
  onExport?: (reasoning: ReasoningChain) => void;
  className?: string;
  compact?: boolean;
}

export const ReasoningVisualization: React.FC<ReasoningVisualizationProps> = ({
  reasoning,
  onExport,
  className = '',
  compact = false
}) => {
  const { toast } = useToast();
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set());
  const [showSources, setShowSources] = useState(false);

  // Toggle step expansion
  const toggleStep = (stepId: string) => {
    setExpandedSteps(prev => {
      const newSet = new Set(prev);
      if (newSet.has(stepId)) {
        newSet.delete(stepId);
      } else {
        newSet.add(stepId);
      }
      return newSet;

  };

  // Get step icon based on type
  const getStepIcon = (type: ReasoningStep['type']) => {
    switch (type) {
      case 'analysis':
        return Search;
      case 'inference':
        return Lightbulb;
      case 'retrieval':
        return Database;
      case 'synthesis':
        return Zap;
      default:
        return Brain;
    }
  };

  // Get confidence color
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-50 border-green-200';
    if (confidence >= 0.6) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };

  // Get confidence label
  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 0.9) return 'Very High';
    if (confidence >= 0.8) return 'High';
    if (confidence >= 0.6) return 'Medium';
    if (confidence >= 0.4) return 'Low';
    return 'Very Low';
  };

  // Calculate overall progress
  const overallProgress = useMemo(() => {
    return (reasoning.steps.length / Math.max(reasoning.steps.length, 1)) * 100;
  }, [reasoning.steps]);

  // Export reasoning chain
  const handleExport = () => {
    if (onExport) {
      onExport(reasoning);
    } else {
      // Default export as JSON
      const exportData = {
        reasoning,
        exportedAt: new Date().toISOString(),
        metadata: {
          totalSteps: reasoning.steps.length,
          overallConfidence: reasoning.confidence,
          methodology: reasoning.methodology
        }
      };
      
      const blob = new Blob([JSON.stringify(exportData, null, 2)], {
        type: 'application/json'

      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `reasoning-chain-${Date.now()}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      toast({
        title: 'Exported',
        description: 'Reasoning chain exported successfully'

    }
  };

  // Copy reasoning summary
  const copyReasoningSummary = async () => {
    const summary = reasoning.steps
      .map((step, index) => `${index + 1}. ${step.description} (${Math.round(step.confidence * 100)}% confidence)`)
      .join('\n');
    
    try {
      await navigator.clipboard.writeText(summary);
      toast({
        title: 'Copied',
        description: 'Reasoning summary copied to clipboard'

    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Copy Failed',
        description: 'Failed to copy reasoning summary'

    }
  };

  // Render step component
  const renderStep = (step: ReasoningStep, index: number) => {
    const Icon = getStepIcon(step.type);
    const isExpanded = expandedSteps.has(step.id);
    const confidenceColor = getConfidenceColor(step.confidence);

    return (
      <Card key={step.id} className="relative">
        <Collapsible open={isExpanded} onOpenChange={() => toggleStep(step.id)}>
          <CollapsibleTrigger asChild>
            <CardHeader className="pb-3 cursor-pointer hover:bg-muted/50 transition-colors">
              <div className="flex items-center gap-3">
                {/* Step Number */}
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center ">
                  <span className="text-sm font-medium text-primary md:text-base lg:text-lg">{index + 1}</span>
                </div>

                {/* Step Icon */}
                <div className="flex-shrink-0">
                  <Icon className="h-5 w-5 text-muted-foreground " />
                </div>

                {/* Step Content */}
                <div className="flex-1 min-w-0 ">
                  <div className="flex items-center gap-2 mb-1">
                    <CardTitle className="text-sm font-medium truncate md:text-base lg:text-lg">
                      {step.description}
                    </CardTitle>
                    <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                      {step.type}
                    </Badge>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <div className={`px-2 py-1 rounded text-xs font-medium border ${confidenceColor}`}>
                      {getConfidenceLabel(step.confidence)} ({Math.round(step.confidence * 100)}%)
                    </div>
                    <span className="text-xs text-muted-foreground sm:text-sm md:text-base">
                      {format(step.timestamp, 'HH:mm:ss')}
                    </span>
                  </div>
                </div>

                {/* Expand Icon */}
                <div className="flex-shrink-0">
                  {isExpanded ? (
                    <ChevronDown className="h-4 w-4 text-muted-foreground " />
                  ) : (
                    <ChevronRight className="h-4 w-4 text-muted-foreground " />
                  )}
                </div>
              </div>
            </CardHeader>
          </CollapsibleTrigger>

          <CollapsibleContent>
            <CardContent className="pt-0">
              <Separator className="mb-4" />
              
              {/* Evidence */}
              {step.evidence && step.evidence.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium mb-2 flex items-center gap-2 md:text-base lg:text-lg">
                    <Info className="h-4 w-4 " />
                  </h4>
                  <ul className="space-y-1">
                    {step.evidence.map((evidence, evidenceIndex) => (
                      <li key={evidenceIndex} className="text-sm text-muted-foreground flex items-start gap-2 md:text-base lg:text-lg">
                        <CheckCircle className="h-3 w-3 mt-0.5 flex-shrink-0 text-green-600 " />
                        {evidence}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Confidence Breakdown */}
              <div className="mb-4">
                <h4 className="text-sm font-medium mb-2 md:text-base lg:text-lg">Confidence Analysis</h4>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm md:text-base lg:text-lg">
                    <span>Step Confidence</span>
                    <span className="font-medium">{Math.round(step.confidence * 100)}%</span>
                  </div>
                  <Progress value={step.confidence * 100} className="h-2" />
                  <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
                  </p>
                </div>
              </div>

              {/* Timestamp Details */}
              <div className="flex items-center gap-2 text-xs text-muted-foreground sm:text-sm md:text-base">
                <Clock className="h-3 w-3 " />
                <span>Processed at {format(step.timestamp, 'MMM dd, yyyy HH:mm:ss')}</span>
              </div>
            </CardContent>
          </CollapsibleContent>
        </Collapsible>
      </Card>
    );
  };

  // Render source attribution
  const renderSources = () => (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm flex items-center gap-2 md:text-base lg:text-lg">
          <Database className="h-4 w-4 " />
          Source Attribution ({reasoning.sources.length})
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {reasoning.sources.map((source, index) => (
            <div key={source.id} className="p-3 border rounded-lg sm:p-4 md:p-6">
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <h4 className="text-sm font-medium md:text-base lg:text-lg">{source.title}</h4>
                  <Badge variant="outline" className="text-xs mt-1 sm:text-sm md:text-base">
                    {source.type}
                  </Badge>
                </div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground sm:text-sm md:text-base">
                  <span>Reliability: {Math.round(source.reliability * 100)}%</span>
                  <span>Relevance: {Math.round(source.relevance * 100)}%</span>
                </div>
              </div>
              
              {source.snippet && (
                <p className="text-sm text-muted-foreground italic md:text-base lg:text-lg">
                  "{source.snippet}"
                </p>
              )}
              
              {source.url && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="mt-2 h-auto p-0 text-xs sm:text-sm md:text-base"
                  onClick={() => window.open(source.url, '_blank')}
                >
                  <Eye className="h-3 w-3 mr-1 " />
                </Button>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );

  if (compact) {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <div className={`flex items-center gap-2 ${className}`}>
              <Brain className="h-4 w-4 text-muted-foreground " />
              <div className={`px-2 py-1 rounded text-xs font-medium border ${getConfidenceColor(reasoning.confidence)}`}>
                {Math.round(reasoning.confidence * 100)}%
              </div>
              <span className="text-xs text-muted-foreground sm:text-sm md:text-base">
                {reasoning.steps.length} steps
              </span>
            </div>
          </TooltipTrigger>
          <TooltipContent>
            <p>AI Reasoning: {reasoning.methodology}</p>
            <p>{reasoning.steps.length} reasoning steps with {Math.round(reasoning.confidence * 100)}% confidence</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  return (
    <Card className={`h-full flex flex-col ${className}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5 " />
          </CardTitle>
          
          <div className="flex items-center gap-2">
            <div className={`px-3 py-1 rounded-full text-sm font-medium border ${getConfidenceColor(reasoning.confidence)}`}>
              {getConfidenceLabel(reasoning.confidence)} ({Math.round(reasoning.confidence * 100)}%)
            </div>
            
            <Button variant="outline" size="sm" onClick={copyReasoningSummary} >
              <Copy className="h-4 w-4 " />
            </Button>
            
            <Button variant="outline" size="sm" onClick={handleExport} >
              <Download className="h-4 w-4 " />
            </Button>
          </div>
        </div>

        {/* Methodology */}
        <div className="mt-2">
          <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
            <strong>Methodology:</strong> {reasoning.methodology}
          </p>
        </div>

        {/* Overall Progress */}
        <div className="mt-3">
          <div className="flex items-center justify-between text-sm mb-2 md:text-base lg:text-lg">
            <span>Reasoning Progress</span>
            <span>{reasoning.steps.length} steps completed</span>
          </div>
          <Progress value={overallProgress} className="h-2" />
        </div>
      </CardHeader>

      <CardContent className="flex-1 p-0 sm:p-4 md:p-6">
        <ScrollArea className="h-full px-4">
          <div className="space-y-4 pb-4">
            {/* Reasoning Steps */}
            <div className="space-y-3">
              {reasoning.steps.map((step, index) => renderStep(step, index))}
            </div>

            {/* Sources Toggle */}
            {reasoning.sources.length > 0 && (
              <div className="pt-4">
                <Button
                  variant="outline"
                  onClick={() => setShowSources(!showSources)}
                  className="w-full"
                >
                  <Database className="h-4 w-4 mr-2 " />
                  {showSources ? 'Hide' : 'Show'} Sources ({reasoning.sources.length})
                  {showSources ? (
                    <ChevronDown className="h-4 w-4 ml-2 " />
                  ) : (
                    <ChevronRight className="h-4 w-4 ml-2 " />
                  )}
                </Button>
                
                {showSources && (
                  <div className="mt-4">
                    {renderSources()}
                  </div>
                )}
              </div>
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
};

export default ReasoningVisualization;