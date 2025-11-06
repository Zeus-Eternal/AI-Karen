
"use client";
import React from 'react';
import { useState } from 'react';
import { useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { HelpCircle, ExternalLink } from 'lucide-react';
import { getHelpContent, type HelpContent } from '@/lib/help-content';

import { } from '@/components/ui/tooltip';

import { } from '@/components/ui/dialog';
export interface HelpTooltipProps {
  helpKey: string;
  category?: 'modelLibrary' | 'llmSettings';
  variant?: 'icon' | 'text' | 'inline';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

/**
 * Help tooltip component that provides contextual help information
 * with both tooltip and detailed dialog options.
 */
export function HelpTooltip({ 
  helpKey, 
  category = 'modelLibrary', 
  variant = 'icon',
  size = 'sm',
  className = '' 
}: HelpTooltipProps) {
  const [dialogOpen, setDialogOpen] = useState(false);
  const helpContent = getHelpContent(helpKey, category);

  if (!helpContent) {
    return null;
  }

  const iconSize = size === 'sm' ? 'h-3 w-3' : size === 'md' ? 'h-4 w-4' : 'h-5 w-5';
  
  const TriggerComponent = () => {
    switch (variant) {
      case 'text':

  // Focus management for accessibility
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        // Handle escape key
        onClose?.();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

        return (
          <Button variant="link" size="sm" className={`p-0 h-auto text-xs text-muted-foreground ${className}`} >
            <HelpCircle className={`${iconSize} mr-1`} />
          </Button>
        );
      case 'inline':
        return (
          <span className={`inline-flex items-center text-muted-foreground cursor-help ${className}`}>
            <HelpCircle className={iconSize} />
          </span>
        );
      default:
        return (
          <Button 
            variant="ghost" 
            size="sm" 
            className={`p-1 h-auto w-auto text-muted-foreground hover:text-foreground ${className}`}
           >
            <HelpCircle className={iconSize} />
          </Button>
        );
    }
  };

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <div>
                <TriggerComponent />
              </div>
            </DialogTrigger>
            <DialogContent className="max-w-2xl ">
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <HelpCircle className="h-5 w-5 text-primary " />
                  {helpContent.title}
                </DialogTitle>
                <DialogDescription>
                  {helpContent.description}
                </DialogDescription>
              </DialogHeader>
              
              <div className="space-y-4">
                {helpContent.details && (
                  <div>
                    <h4 className="font-medium mb-2">Details</h4>
                    <div className="text-sm text-muted-foreground whitespace-pre-line md:text-base lg:text-lg">
                      {helpContent.details}
                    </div>
                  </div>
                )}
                
                {helpContent.links && helpContent.links.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Additional Resources</h4>
                    <div className="flex flex-wrap gap-2">
                      {helpContent.links.map((link, index) => (
                        <Badge key={index} variant="outline" className="gap-1">
                          <ExternalLink className="h-3 w-3 " />
                          <a 
                            href={link.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="hover:underline"
                          >
                            {link.text}
                          </a>
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </DialogContent>
          </Dialog>
        </TooltipTrigger>
        <TooltipContent side="top" className="max-w-xs">
          <p className="text-sm md:text-base lg:text-lg">{helpContent.description}</p>
          <p className="text-xs text-muted-foreground mt-1 sm:text-sm md:text-base">Click for more details</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

export interface HelpSectionProps {
  title: string;
  helpKey: string;
  category?: 'modelLibrary' | 'llmSettings';
  children: React.ReactNode;
  className?: string;
}

/**
 * Help section component that wraps content with a help tooltip in the header.
 */
export function HelpSection({ 
  title, 
  helpKey, 
  category = 'modelLibrary', 
  children, 
  className = '' 
}: HelpSectionProps) {
  return (
    <div className={className}>
      <div className="flex items-center gap-2 mb-3">
        <h3 className="font-medium">{title}</h3>
        <HelpTooltip helpKey={helpKey} category={category} variant="inline" />
      </div>
      {children}
    </div>
  );
}

export interface QuickHelpProps {
  helpKeys: string[];
  category?: 'modelLibrary' | 'llmSettings';
  title?: string;
  className?: string;
}

/**
 * Quick help component that shows multiple help topics in a compact format.
 */
export function QuickHelp({ 
  helpKeys, 
  category = 'modelLibrary', 
  title = "Quick Help",
  className = '' 
}: QuickHelpProps) {
  const [expanded, setExpanded] = useState(false);
  
  return (
    <div className={`border rounded-lg p-3 ${className}`}>
      <div className="flex items-center justify-between">
        <h4 className="font-medium text-sm flex items-center gap-2 md:text-base lg:text-lg">
          <HelpCircle className="h-4 w-4 text-primary " />
          {title}
        </h4>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setExpanded(!expanded)}
          className="text-xs sm:text-sm md:text-base"
        >
          {expanded ? 'Hide' : 'Show'} Help
        </Button>
      </div>
      
      {expanded && (
        <div className="mt-3 space-y-2">
          {helpKeys.map(helpKey => {
            const content = getHelpContent(helpKey, category);
            if (!content) return null;
            
            return (
              <div key={helpKey} className="flex items-start gap-2 text-sm md:text-base lg:text-lg">
                <HelpTooltip helpKey={helpKey} category={category} variant="inline" size="sm" />
                <div>
                  <span className="font-medium">{content.title}:</span>
                  <span className="text-muted-foreground ml-1">{content.description}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}