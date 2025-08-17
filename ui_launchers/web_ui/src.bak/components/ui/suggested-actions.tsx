'use client';

/**
 * Suggested Actions Component
 * 
 * Features:
 * - Display suggested actions from copilot responses
 * - Interactive action buttons with icons
 * - Loading states and feedback
 * - Mobile-optimized touch interactions
 * - Confidence indicators
 */

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { 
  CheckSquare, 
  Pin, 
  Download, 
  Search, 
  MessageSquare, 
  ExternalLink,
  Loader2,
  Sparkles,
  ChevronRight,
  X
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useActionRegistry } from '@/hooks/use-action-registry';
import type { SuggestedAction, ActionResult } from '@/services/actionMapper';

interface SuggestedActionsProps {
  actions: SuggestedAction[];
  onActionComplete?: (action: SuggestedAction, result: ActionResult) => void;
  onDismiss?: () => void;
  className?: string;
  variant?: 'default' | 'compact' | 'inline';
  showConfidence?: boolean;
  maxActions?: number;
}

const actionIcons = {
  add_task: CheckSquare,
  pin_memory: Pin,
  open_doc: ExternalLink,
  export_note: Download,
  search_memory: Search,
  create_conversation: MessageSquare
};

const actionColors = {
  add_task: 'bg-blue-500 hover:bg-blue-600',
  pin_memory: 'bg-purple-500 hover:bg-purple-600',
  open_doc: 'bg-green-500 hover:bg-green-600',
  export_note: 'bg-orange-500 hover:bg-orange-600',
  search_memory: 'bg-indigo-500 hover:bg-indigo-600',
  create_conversation: 'bg-pink-500 hover:bg-pink-600'
};

const priorityColors = {
  high: 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950',
  medium: 'border-yellow-200 bg-yellow-50 dark:border-yellow-800 dark:bg-yellow-950',
  low: 'border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800'
};

export const SuggestedActions: React.FC<SuggestedActionsProps> = ({
  actions,
  onActionComplete,
  onDismiss,
  className,
  variant = 'default',
  showConfidence = true,
  maxActions = 5
}) => {
  const { performSuggestedAction, isLoading } = useActionRegistry({
    autoToast: true,
    onActionComplete: (actionType, result) => {
      const action = actions.find(a => a.type === actionType);
      if (action && onActionComplete) {
        onActionComplete(action, result);
      }
    }
  });

  const [executingActions, setExecutingActions] = useState<Set<string>>(new Set());
  const [completedActions, setCompletedActions] = useState<Set<string>>(new Set());

  if (!actions.length) return null;

  const displayActions = actions.slice(0, maxActions);

  const handleActionClick = async (action: SuggestedAction, index: number) => {
    const actionKey = `${action.type}_${index}`;
    
    setExecutingActions(prev => new Set(prev).add(actionKey));
    
    try {
      const result = await performSuggestedAction(action);
      
      if (result.success) {
        setCompletedActions(prev => new Set(prev).add(actionKey));
        
        // Auto-remove completed action after delay
        setTimeout(() => {
          setCompletedActions(prev => {
            const newSet = new Set(prev);
            newSet.delete(actionKey);
            return newSet;
          });
        }, 3000);
      }
    } finally {
      setExecutingActions(prev => {
        const newSet = new Set(prev);
        newSet.delete(actionKey);
        return newSet;
      });
    }
  };

  const ActionButton: React.FC<{ 
    action: SuggestedAction; 
    index: number;
    isCompact?: boolean;
  }> = ({ action, index, isCompact = false }) => {
    const actionKey = `${action.type}_${index}`;
    const isExecuting = executingActions.has(actionKey);
    const isCompleted = completedActions.has(actionKey);
    const IconComponent = actionIcons[action.type as keyof typeof actionIcons] || Sparkles;
    const colorClass = actionColors[action.type as keyof typeof actionColors] || 'bg-gray-500 hover:bg-gray-600';

    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95 }}
        transition={{ delay: index * 0.1 }}
        className={cn(
          'relative',
          isCompleted && 'opacity-75'
        )}
      >
        <Button
          onClick={() => handleActionClick(action, index)}
          disabled={isExecuting || isCompleted}
          variant="outline"
          size={isCompact ? "sm" : "default"}
          className={cn(
            'relative overflow-hidden transition-all duration-200',
            isCompleted && 'bg-green-50 border-green-200 text-green-700 dark:bg-green-950 dark:border-green-800 dark:text-green-300',
            !isCompleted && !isExecuting && 'hover:shadow-md',
            isCompact ? 'h-8 px-2 text-xs' : 'h-10 px-4'
          )}
        >
          <div className="flex items-center gap-2">
            {isExecuting ? (
              <Loader2 className={cn('animate-spin', isCompact ? 'h-3 w-3' : 'h-4 w-4')} />
            ) : isCompleted ? (
              <CheckSquare className={cn('text-green-600', isCompact ? 'h-3 w-3' : 'h-4 w-4')} />
            ) : (
              <IconComponent className={isCompact ? 'h-3 w-3' : 'h-4 w-4'} />
            )}
            
            <span className={cn('font-medium', isCompact && 'text-xs')}>
              {action.description || action.type.replace('_', ' ')}
            </span>
            
            {showConfidence && action.confidence && !isCompact && (
              <Badge variant="secondary" className="text-xs ml-1">
                {Math.round(action.confidence * 100)}%
              </Badge>
            )}
          </div>
          
          {/* Completion animation */}
          <AnimatePresence>
            {isCompleted && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                exit={{ scale: 0 }}
                className="absolute inset-0 bg-green-500/10 rounded-md"
              />
            )}
          </AnimatePresence>
        </Button>
      </motion.div>
    );
  };

  if (variant === 'inline') {
    return (
      <div className={cn('flex flex-wrap gap-2', className)}>
        <AnimatePresence mode="popLayout">
          {displayActions.map((action, index) => (
            <ActionButton 
              key={`${action.type}_${index}`}
              action={action} 
              index={index}
              isCompact
            />
          ))}
        </AnimatePresence>
      </div>
    );
  }

  if (variant === 'compact') {
    return (
      <Card className={cn('border-dashed', className)}>
        <CardContent className="p-3">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-blue-500" />
              <span className="text-sm font-medium">Suggested Actions</span>
            </div>
            {onDismiss && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onDismiss}
                className="h-6 w-6 p-0"
              >
                <X className="h-3 w-3" />
              </Button>
            )}
          </div>
          
          <div className="flex flex-wrap gap-2">
            <AnimatePresence mode="popLayout">
              {displayActions.map((action, index) => (
                <ActionButton 
                  key={`${action.type}_${index}`}
                  action={action} 
                  index={index}
                  isCompact
                />
              ))}
            </AnimatePresence>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Default variant
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn('space-y-3', className)}
    >
      <Card className="border-dashed border-blue-200 bg-blue-50/50 dark:border-blue-800 dark:bg-blue-950/20">
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-blue-500" />
              <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                Suggested Actions
              </h3>
              <Badge variant="secondary" className="text-xs">
                {displayActions.length}
              </Badge>
            </div>
            
            {onDismiss && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onDismiss}
                className="h-8 w-8 p-0"
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>

          <div className="space-y-2">
            <AnimatePresence mode="popLayout">
              {displayActions.map((action, index) => {
                const actionKey = `${action.type}_${index}`;
                const isExecuting = executingActions.has(actionKey);
                const isCompleted = completedActions.has(actionKey);
                const IconComponent = actionIcons[action.type as keyof typeof actionIcons] || Sparkles;
                const priorityClass = priorityColors[action.priority || 'medium'];

                return (
                  <motion.div
                    key={actionKey}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    transition={{ delay: index * 0.1 }}
                    className={cn(
                      'flex items-center justify-between p-3 rounded-lg border transition-all duration-200',
                      priorityClass,
                      isCompleted && 'bg-green-50 border-green-200 dark:bg-green-950 dark:border-green-800',
                      !isCompleted && 'hover:shadow-sm'
                    )}
                  >
                    <div className="flex items-center gap-3 flex-1">
                      <div className={cn(
                        'p-2 rounded-full text-white',
                        isCompleted ? 'bg-green-500' : actionColors[action.type as keyof typeof actionColors] || 'bg-gray-500'
                      )}>
                        {isCompleted ? (
                          <CheckSquare className="h-4 w-4" />
                        ) : (
                          <IconComponent className="h-4 w-4" />
                        )}
                      </div>
                      
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-gray-900 dark:text-gray-100">
                            {action.description || action.type.replace('_', ' ')}
                          </span>
                          
                          {action.priority === 'high' && (
                            <Badge variant="destructive" className="text-xs">
                              High Priority
                            </Badge>
                          )}
                          
                          {showConfidence && action.confidence && (
                            <Badge variant="outline" className="text-xs">
                              {Math.round(action.confidence * 100)}% confidence
                            </Badge>
                          )}
                        </div>
                        
                        {action.params && Object.keys(action.params).length > 0 && (
                          <p className="text-xs text-gray-500 mt-1">
                            {Object.entries(action.params)
                              .slice(0, 2)
                              .map(([key, value]) => `${key}: ${String(value).substring(0, 30)}`)
                              .join(', ')}
                          </p>
                        )}
                      </div>
                    </div>

                    <Button
                      onClick={() => handleActionClick(action, index)}
                      disabled={isExecuting || isCompleted}
                      size="sm"
                      variant={isCompleted ? "outline" : "default"}
                      className={cn(
                        'ml-3',
                        isCompleted && 'bg-green-100 border-green-300 text-green-700 hover:bg-green-200'
                      )}
                    >
                      {isExecuting ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : isCompleted ? (
                        'Done'
                      ) : (
                        <>
                          Execute
                          <ChevronRight className="h-4 w-4 ml-1" />
                        </>
                      )}
                    </Button>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>

          {actions.length > maxActions && (
            <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
              <p className="text-xs text-gray-500 text-center">
                {actions.length - maxActions} more actions available
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default SuggestedActions;