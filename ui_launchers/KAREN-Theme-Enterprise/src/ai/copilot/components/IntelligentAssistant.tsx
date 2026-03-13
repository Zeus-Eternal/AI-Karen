import React from 'react';
import { CopilotAction, SecurityContext } from '../types/backend';
import { CopilotSuggestion } from '../../../components/copilot-chat/types/copilot';
import { useCopilotExecuteAction, useCopilotDismissAction } from '../hooks/useCopilot';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, CheckCircle, X, Settings, Info, Lightbulb, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * IntelligentAssistant component
 * Renders backend-suggested actions and provides interface for executing them
 * Enhanced with modern aesthetics and production-ready features
 */
interface IntelligentAssistantProps {
  actions: CopilotAction[];
  suggestions: CopilotSuggestion[];
  securityContext: SecurityContext;
  onSelectSuggestion?: (suggestion: CopilotSuggestion) => void;
  className?: string;
}

export function IntelligentAssistant({
  actions,
  suggestions,
  securityContext,
  onSelectSuggestion,
  className = ''
}: IntelligentAssistantProps) {
  const executeAction = useCopilotExecuteAction();
  const dismissAction = useCopilotDismissAction();

  // Filter actions based on security context
  const filteredActions = actions.filter(action => {
    // Filter out actions that require higher privileges than user has
    if (action.riskLevel === 'evil-mode-only' && securityContext.securityMode !== 'evil') {
      return false;
    }
    
    if (action.riskLevel === 'privileged' && !securityContext.canAccessSensitive) {
      return false;
    }
    
    return true;
  });

  if (filteredActions.length === 0) {
    return null;
  }

  const getRiskLevelVariant = (riskLevel: string) => {
    switch (riskLevel) {
      case 'evil-mode-only': return 'destructive';
      case 'privileged': return 'secondary';
      case 'standard': return 'default';
      default: return 'outline';
    }
  };

  const getRiskLevelIcon = (riskLevel: string) => {
    switch (riskLevel) {
      case 'evil-mode-only': return <AlertTriangle className="h-4 w-4" />;
      case 'privileged': return <Settings className="h-4 w-4" />;
      case 'standard': return <CheckCircle className="h-4 w-4" />;
      default: return <Info className="h-4 w-4" />;
    }
  };

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-primary" />
          Intelligent Assistant
        </CardTitle>
        <CardDescription>
          Proactive suggestions and actions based on your conversation
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Proactive Suggestions Section */}
        {suggestions.length > 0 && (
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Lightbulb className="h-4 w-4 text-amber-500" />
              <h3 className="text-sm font-medium">Proactive Suggestions</h3>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {suggestions.slice(0, 4).map(suggestion => (
                <Card
                  key={suggestion.id}
                  className="border-border/50 shadow-sm cursor-pointer hover:shadow-md transition-shadow"
                  onClick={() => onSelectSuggestion && onSelectSuggestion(suggestion)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="text-sm font-medium">{suggestion.title}</h4>
                      <Badge
                        variant={
                          suggestion.priority === 'high' ? 'destructive' :
                          suggestion.priority === 'medium' ? 'default' : 'secondary'
                        }
                        className="text-xs"
                      >
                        {suggestion.priority}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground mb-3">
                      {suggestion.description}
                    </p>
                    <div className="flex items-center justify-between">
                      <Badge variant="outline" className="text-xs">
                        {suggestion.type}
                      </Badge>
                      <div className="flex items-center gap-1">
                        <div className="w-16 bg-gray-200 rounded-full h-1.5">
                          <div
                            className="bg-blue-600 h-1.5 rounded-full"
                            style={{ width: `${suggestion.confidence * 100}%` }}
                          ></div>
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {Math.round(suggestion.confidence * 100)}%
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}
        
        {/* Actions Section */}
        {filteredActions.length > 0 && (
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-primary" />
              <h3 className="text-sm font-medium">Available Actions</h3>
            </div>
            
            {filteredActions.map(action => (
              <Card key={action.id} className="border-border/50 shadow-sm">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <CardTitle className="text-lg">{action.title}</CardTitle>
                      <Badge variant={getRiskLevelVariant(action.riskLevel)} className="flex items-center gap-1 w-fit">
                        {getRiskLevelIcon(action.riskLevel)}
                        <span className="capitalize">{action.riskLevel.replace('-', ' ')}</span>
                      </Badge>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => dismissAction(action.id)}
                      className="h-8 w-8 p-0"
                    >
                      <X className="h-4 w-4" />
                      <span className="sr-only">Dismiss</span>
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="pt-0 space-y-4">
                  <p className="text-sm text-muted-foreground">
                    {action.description}
                  </p>
                  
                  {action.requiresConfirmation && (
                    <div className="bg-muted/50 p-3 rounded-md space-y-3">
                      <p className="text-sm font-medium">
                        This action requires confirmation. Are you sure you want to proceed?
                      </p>
                      <div className="flex gap-2">
                        <Button
                          onClick={() => executeAction(action)}
                          className="flex-1"
                        >
                          Confirm
                        </Button>
                        <Button
                          variant="outline"
                          onClick={() => dismissAction(action.id)}
                          className="flex-1"
                        >
                          Cancel
                        </Button>
                      </div>
                    </div>
                  )}
                  
                  {!action.requiresConfirmation && (
                    <div className="flex gap-2">
                      <Button
                        onClick={() => executeAction(action)}
                        className="flex-1"
                      >
                        Execute
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => dismissAction(action.id)}
                        className="flex-1"
                      >
                        Dismiss
                      </Button>
                    </div>
                  )}
                  
                  {action.config && Object.keys(action.config).length > 0 && (
                    <details className="space-y-2">
                      <summary className="text-sm font-medium cursor-pointer flex items-center gap-1">
                        <Settings className="h-4 w-4" />
                        Configuration
                      </summary>
                      <pre className="text-xs bg-muted p-3 rounded-md overflow-auto max-h-40">
                        {JSON.stringify(action.config, null, 2)}
                      </pre>
                    </details>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * ContextAwareSuggestions component
 * Renders context-aware suggestions from the backend
 */
interface ContextAwareSuggestionsProps {
  suggestions: string[];
  onSelectSuggestion: (suggestion: string) => void;
  className?: string;
}

export function ContextAwareSuggestions({ 
  suggestions, 
  onSelectSuggestion, 
  className = '' 
}: ContextAwareSuggestionsProps) {
  if (suggestions.length === 0) {
    return null;
  }

  return (
    <div className={`context-aware-suggestions ${className}`}>
      <div className="context-aware-suggestions__header">
        <h4 className="context-aware-suggestions__title">Suggestions</h4>
      </div>
      
      <div className="context-aware-suggestions__list">
        {suggestions.map((suggestion, index) => (
          <button
            key={index}
            className="context-aware-suggestions__item"
            onClick={() => onSelectSuggestion(suggestion)}
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  );
}

/**
 * PluginAwareActions component
 * Renders actions that are specific to available plugins
 */
interface PluginAwareActionsProps {
  actions: CopilotAction[];
  onExecuteAction: (action: CopilotAction) => void;
  onDismissAction: (actionId: string) => void;
  securityContext: SecurityContext;
  className?: string;
}

export function PluginAwareActions({ 
  actions, 
  onExecuteAction, 
  onDismissAction, 
  securityContext,
  className = '' 
}: PluginAwareActionsProps) {
  // Group actions by plugin
  const actionsByPlugin = actions.reduce((groups, action) => {
    if (!groups[action.pluginId]) {
      groups[action.pluginId] = [];
    }
    groups[action.pluginId].push(action);
    return groups;
  }, {} as Record<string, CopilotAction[]>);

  return (
    <div className={`plugin-aware-actions ${className}`}>
      <div className="plugin-aware-actions__header">
        <h3 className="plugin-aware-actions__title">Plugin Actions</h3>
        <p className="plugin-aware-actions__description">
          Actions available from your installed plugins
        </p>
      </div>
      
      <div className="plugin-aware-actions__plugins">
        {Object.entries(actionsByPlugin).map(([pluginId, pluginActions]) => (
          <div key={pluginId} className="plugin-aware-actions__plugin">
            <h4 className="plugin-aware-actions__plugin-name">{pluginId}</h4>
            
            <div className="plugin-aware-actions__plugin-actions">
              {pluginActions.map(action => (
                <div 
                  key={action.id} 
                  className={`plugin-aware-actions__action plugin-aware-actions__action--${action.riskLevel}`}
                >
                  <div className="plugin-aware-actions__action-header">
                    <h5 className="plugin-aware-actions__action-title">{action.title}</h5>
                    <span className={`plugin-aware-actions__action-risk plugin-aware-actions__action-risk--${action.riskLevel}`}>
                      {action.riskLevel}
                    </span>
                  </div>
                  
                  <p className="plugin-aware-actions__action-description">
                    {action.description}
                  </p>
                  
                  <div className="plugin-aware-actions__action-buttons">
                    <button 
                      className="plugin-aware-actions__action-execute-button"
                      onClick={() => onExecuteAction(action)}
                      disabled={
                        (action.riskLevel === 'evil-mode-only' && securityContext.securityMode !== 'evil') ||
                        (action.riskLevel === 'privileged' && !securityContext.canAccessSensitive)
                      }
                    >
                      Execute
                    </button>
                    <button 
                      className="plugin-aware-actions__action-dismiss-button"
                      onClick={() => onDismissAction(action.id)}
                    >
                      Dismiss
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}