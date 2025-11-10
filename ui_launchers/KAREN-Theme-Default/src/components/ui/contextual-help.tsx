"use client";

import { useState, type ReactNode } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from "@/components/ui/alert";
import { HelpTooltip } from '@/components/ui/help-tooltip';
import { getHelpContent } from '@/lib/help-content';
import {
  AlertTriangle,
  BookOpen,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  HelpCircle,
  Lightbulb,
} from 'lucide-react';

export interface ContextualHelpProps {
  section: string;
  helpKeys: string[];
  category?: 'modelLibrary' | 'llmSettings';
  className?: string;
  defaultExpanded?: boolean;
}

/**
 * Contextual help component that provides relevant help information
 * for specific sections or workflows.
 */
export function ContextualHelp({ 
  section, 
  helpKeys, 
  category = 'modelLibrary', 
  className = '',
  defaultExpanded = false 
}: ContextualHelpProps) {
  const [expanded, setExpanded] = useState(defaultExpanded);

  return (
    <Card className={`border-blue-200 bg-blue-50/50 ${className}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-sm font-medium text-blue-900 md:text-base lg:text-lg">
            <HelpCircle className="h-4 w-4 " />
            Help: {section}
          </CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setExpanded(!expanded)}
            className="text-blue-700 hover:text-blue-900 hover:bg-blue-100"
          >
            {expanded ? (
              <ChevronUp className="h-4 w-4 " />
            ) : (
              <ChevronDown className="h-4 w-4 " />
            )}
          </Button>
        </div>
      </CardHeader>
      
      {expanded && (
        <CardContent className="pt-0">
          <div className="space-y-3">
            {helpKeys.map(helpKey => {
              const content = getHelpContent(helpKey, category);
              if (!content) return null;
              
              return (
                <div
                  key={helpKey}
                  className="flex items-start gap-3 p-3 bg-white rounded-lg border border-blue-100 sm:p-4 md:p-6"
                >
                  <div className="flex-shrink-0 mt-0.5">
                    <Lightbulb className="h-4 w-4 text-blue-600 " />
                  </div>
                  <div className="flex-1 min-w-0 ">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-medium text-sm text-blue-900 md:text-base lg:text-lg">{content.title}</h4>
                      <HelpTooltip helpKey={helpKey} category={category} variant="inline" size="sm" />
                    </div>
                    <p className="text-sm text-blue-700 md:text-base lg:text-lg">{content.description}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      )}
    </Card>
  );
}

export interface HelpCalloutProps {
  type: 'tip' | 'warning' | 'info' | 'success';
  title: string;
  children: ReactNode;
  helpKey?: string;
  category?: 'modelLibrary' | 'llmSettings';
  className?: string;
}

/**
 * Help callout component for highlighting important information
 * with optional contextual help integration.
 */
export function HelpCallout({ 
  type, 
  title, 
  children, 
  helpKey, 
  category = 'modelLibrary',
  className = '' 
}: HelpCalloutProps) {
  const getIcon = () => {
    switch (type) {
      case 'tip':
        return <Lightbulb className="h-4 w-4 " />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 " />;
      case 'success':
        return <CheckCircle className="h-4 w-4 " />;
      default:
        return <BookOpen className="h-4 w-4 " />;
    }
  };

  const getColorClasses = () => {
    switch (type) {
      case 'tip':
        return 'border-blue-200 bg-blue-50 text-blue-900';
      case 'warning':
        return 'border-yellow-200 bg-yellow-50 text-yellow-900';
      case 'success':
        return 'border-green-200 bg-green-50 text-green-900';
      default:
        return 'border-gray-200 bg-gray-50 text-gray-900';
    }
  };

  return (
    <Alert className={`${getColorClasses()} ${className}`}>
      <div className="flex items-start gap-2">
        {getIcon()}
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <AlertDescription className="font-medium">{title}</AlertDescription>
            {helpKey && (
              <HelpTooltip helpKey={helpKey} category={category} variant="inline" size="sm" />
            )}
          </div>
          <AlertDescription className="text-sm opacity-90 md:text-base lg:text-lg">
            {children}
          </AlertDescription>
        </div>
      </div>
    </Alert>
  );
}

export interface QuickStartHelpProps {
  steps: Array<{
    title: string;
    description: string;
    helpKey?: string;
  }>;
  category?: 'modelLibrary' | 'llmSettings';
  className?: string;
}

/**
 * Quick start help component that provides step-by-step guidance
 * for common workflows.
 */
export function QuickStartHelp({
  steps,
  category = 'modelLibrary',
  className = ''
}: QuickStartHelpProps) {
  return (
    <Card className={`border-green-200 bg-green-50/50 ${className}`}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-green-900">
          <CheckCircle className="h-5 w-5 " />
        </CardTitle>
        <CardDescription className="text-green-700">
          Follow these steps to get up and running quickly.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {steps.map((step, index) => (
            <div key={index} className="flex items-start gap-3">
              <div className="flex-shrink-0">
                <Badge variant="outline" className="bg-green-100 text-green-800 border-green-300">
                  {index + 1}
                </Badge>
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h4 className="font-medium text-sm text-green-900 md:text-base lg:text-lg">{step.title}</h4>
                  {step.helpKey && (
                    <HelpTooltip helpKey={step.helpKey} category={category} variant="inline" size="sm" />
                  )}
                </div>
                <p className="text-sm text-green-700 md:text-base lg:text-lg">{step.description}</p>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
