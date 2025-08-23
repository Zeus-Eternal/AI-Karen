'use client';

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel,
  DropdownMenuShortcut
} from '@/components/ui/dropdown-menu';
import { 
  Brain, 
  Code, 
  Bug, 
  RefreshCw, 
  FileText, 
  Lightbulb,
  Sparkles,
  Zap,
  Search,
  TestTube,
  Shield,
  Cpu,
  GitBranch,
  MessageSquare,
  ChevronDown,
  Keyboard
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';

// Types for copilot actions and context
export interface CopilotAction {
  id: string;
  label: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  category: 'code' | 'debug' | 'docs' | 'analysis' | 'general';
  shortcut?: string;
  prompt: string;
  requiresSelection?: boolean;
  contextTypes?: string[];
}

export interface ChatContext {
  selectedText?: string;
  currentFile?: string;
  language?: string;
  recentMessages?: Array<{
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
  }>;
  codeContext?: {
    hasCode: boolean;
    language?: string;
    errorCount?: number;
  };
  conversationContext?: {
    topic?: string;
    intent?: string;
    complexity?: 'simple' | 'medium' | 'complex';
  };
}

export interface CopilotActionsProps {
  onActionTriggered: (action: CopilotAction) => void;
  context: ChatContext;
  className?: string;
  disabled?: boolean;
  showShortcuts?: boolean;
}

// Predefined copilot actions
const COPILOT_ACTIONS: CopilotAction[] = [
  // Code Actions
  {
    id: 'copilot.review',
    label: 'Review Code',
    description: 'Analyze code for best practices, bugs, and improvements',
    icon: Code,
    category: 'code',
    shortcut: 'Ctrl+Shift+R',
    prompt: '/copilot review',
    requiresSelection: false,
    contextTypes: ['code', 'file']
  },
  {
    id: 'copilot.debug',
    label: 'Debug Issue',
    description: 'Help identify and fix bugs in the code',
    icon: Bug,
    category: 'debug',
    shortcut: 'Ctrl+Shift+D',
    prompt: '/copilot debug',
    requiresSelection: false,
    contextTypes: ['code', 'error']
  },
  {
    id: 'copilot.refactor',
    label: 'Refactor Code',
    description: 'Suggest improvements and refactoring opportunities',
    icon: RefreshCw,
    category: 'code',
    shortcut: 'Ctrl+Shift+F',
    prompt: '/copilot refactor',
    requiresSelection: false,
    contextTypes: ['code']
  },
  {
    id: 'copilot.generate_tests',
    label: 'Generate Tests',
    description: 'Create unit tests for the selected code',
    icon: TestTube,
    category: 'code',
    shortcut: 'Ctrl+Shift+T',
    prompt: '/copilot generate_tests',
    requiresSelection: false,
    contextTypes: ['code', 'function']
  },
  
  // Documentation Actions
  {
    id: 'copilot.document',
    label: 'Generate Docs',
    description: 'Create comprehensive documentation',
    icon: FileText,
    category: 'docs',
    shortcut: 'Ctrl+Shift+G',
    prompt: '/copilot document',
    requiresSelection: false,
    contextTypes: ['code', 'function', 'class']
  },
  {
    id: 'copilot.explain',
    label: 'Explain Code',
    description: 'Provide detailed explanation of how code works',
    icon: Lightbulb,
    category: 'docs',
    shortcut: 'Ctrl+Shift+E',
    prompt: '/copilot explain',
    requiresSelection: false,
    contextTypes: ['code', 'algorithm']
  },
  
  // Analysis Actions
  {
    id: 'copilot.analyze_performance',
    label: 'Performance Analysis',
    description: 'Analyze code performance and suggest optimizations',
    icon: Zap,
    category: 'analysis',
    shortcut: 'Ctrl+Shift+P',
    prompt: '/copilot analyze performance',
    requiresSelection: false,
    contextTypes: ['code', 'function']
  },
  {
    id: 'copilot.security_scan',
    label: 'Security Scan',
    description: 'Check for security vulnerabilities and issues',
    icon: Shield,
    category: 'analysis',
    shortcut: 'Ctrl+Shift+S',
    prompt: '/copilot security_scan',
    requiresSelection: false,
    contextTypes: ['code', 'api']
  },
  {
    id: 'copilot.complexity_analysis',
    label: 'Complexity Analysis',
    description: 'Analyze code complexity and maintainability',
    icon: Cpu,
    category: 'analysis',
    shortcut: 'Ctrl+Shift+C',
    prompt: '/copilot analyze complexity',
    requiresSelection: false,
    contextTypes: ['code', 'function', 'class']
  },
  
  // General Actions
  {
    id: 'copilot.search_context',
    label: 'Search Context',
    description: 'Search for relevant information in the codebase',
    icon: Search,
    category: 'general',
    shortcut: 'Ctrl+Shift+/',
    prompt: '/copilot search',
    requiresSelection: false,
    contextTypes: ['any']
  },
  {
    id: 'copilot.suggest_improvements',
    label: 'Suggest Improvements',
    description: 'Get general suggestions for improvement',
    icon: Sparkles,
    category: 'general',
    shortcut: 'Ctrl+Shift+I',
    prompt: '/copilot suggest',
    requiresSelection: false,
    contextTypes: ['any']
  },
  {
    id: 'copilot.git_help',
    label: 'Git Assistance',
    description: 'Help with Git operations and best practices',
    icon: GitBranch,
    category: 'general',
    shortcut: 'Ctrl+Shift+G',
    prompt: '/copilot git',
    requiresSelection: false,
    contextTypes: ['git', 'repository']
  }
];

// Slash command patterns for parsing
const SLASH_COMMAND_PATTERNS = [
  { pattern: /^\/copilot\s+review/i, actionId: 'copilot.review' },
  { pattern: /^\/copilot\s+debug/i, actionId: 'copilot.debug' },
  { pattern: /^\/copilot\s+refactor/i, actionId: 'copilot.refactor' },
  { pattern: /^\/copilot\s+generate[_\s]tests?/i, actionId: 'copilot.generate_tests' },
  { pattern: /^\/copilot\s+document?/i, actionId: 'copilot.document' },
  { pattern: /^\/copilot\s+explain/i, actionId: 'copilot.explain' },
  { pattern: /^\/copilot\s+analyze\s+performance/i, actionId: 'copilot.analyze_performance' },
  { pattern: /^\/copilot\s+security[_\s]scan/i, actionId: 'copilot.security_scan' },
  { pattern: /^\/copilot\s+analyze\s+complexity/i, actionId: 'copilot.complexity_analysis' },
  { pattern: /^\/copilot\s+search/i, actionId: 'copilot.search_context' },
  { pattern: /^\/copilot\s+suggest/i, actionId: 'copilot.suggest_improvements' },
  { pattern: /^\/copilot\s+git/i, actionId: 'copilot.git_help' }
];

export const CopilotActions: React.FC<CopilotActionsProps> = ({
  onActionTriggered,
  context,
  className = '',
  disabled = false,
  showShortcuts = true
}) => {
  const { user } = useAuth();
  const { toast } = useToast();
  
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredActions, setFilteredActions] = useState<CopilotAction[]>(COPILOT_ACTIONS);

  // Context-aware action discovery
  const contextualActions = useMemo(() => {
    return COPILOT_ACTIONS.filter(action => {
      // If action has no context requirements, it's always available
      if (!action.contextTypes || action.contextTypes.includes('any')) {
        return true;
      }
      
      // Check if current context matches action requirements
      const hasMatchingContext = action.contextTypes.some(contextType => {
        switch (contextType) {
          case 'code':
            return context.codeContext?.hasCode || context.selectedText?.includes('function') || context.selectedText?.includes('class');
          case 'error':
            return context.codeContext?.errorCount && context.codeContext.errorCount > 0;
          case 'file':
            return !!context.currentFile;
          case 'function':
            return context.selectedText?.includes('function') || context.selectedText?.includes('def ');
          case 'class':
            return context.selectedText?.includes('class ');
          case 'api':
            return context.selectedText?.includes('api') || context.selectedText?.includes('endpoint');
          case 'git':
            return context.conversationContext?.topic?.includes('git') || context.currentFile?.includes('.git');
          case 'repository':
            return !!context.currentFile;
          case 'algorithm':
            return context.conversationContext?.complexity === 'complex';
          default:
            return false;
        }
      });
      
      return hasMatchingContext;
    });
  }, [context]);

  // Filter actions based on search query
  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredActions(contextualActions);
      return;
    }
    
    const query = searchQuery.toLowerCase();
    const filtered = contextualActions.filter(action => 
      action.label.toLowerCase().includes(query) ||
      action.description.toLowerCase().includes(query) ||
      action.category.toLowerCase().includes(query)
    );
    
    setFilteredActions(filtered);
  }, [searchQuery, contextualActions]);



  // Handle action selection
  const handleActionSelect = useCallback((action: CopilotAction) => {
    if (disabled) return;
    
    // Check if action requires selection and we don't have any
    if (action.requiresSelection && !context.selectedText) {
      toast({
        variant: 'destructive',
        title: 'Selection Required',
        description: `The "${action.label}" action requires text selection.`
      });
      return;
    }
    
    // Trigger the action
    onActionTriggered(action);
    setIsOpen(false);
    
    // Show feedback
    toast({
      title: 'Copilot Action Triggered',
      description: `${action.label}: ${action.description}`
    });
  }, [disabled, context.selectedText, onActionTriggered, toast]);

  // Keyboard shortcuts handler
  useEffect(() => {
    if (!showShortcuts) return;
    
    const handleKeyDown = (event: KeyboardEvent) => {
      // Check if we're in an input field
      const target = event.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.contentEditable === 'true') {
        return;
      }
      
      // Find matching action by shortcut
      const matchingAction = COPILOT_ACTIONS.find(action => {
        if (!action.shortcut) return false;
        
        const shortcut = action.shortcut.toLowerCase();
        const isCtrlShift = event.ctrlKey && event.shiftKey;
        const key = event.key.toLowerCase();
        
        // Parse shortcut format like "Ctrl+Shift+R"
        const shortcutParts = shortcut.split('+').map(part => part.trim());
        const shortcutKey = shortcutParts[shortcutParts.length - 1];
        
        return isCtrlShift && key === shortcutKey;
      });
      
      if (matchingAction) {
        event.preventDefault();
        handleActionSelect(matchingAction);
      }
    };
    
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [showShortcuts, handleActionSelect]);

  // Group actions by category
  const actionsByCategory = useMemo(() => {
    const grouped = filteredActions.reduce((acc, action) => {
      if (!acc[action.category]) {
        acc[action.category] = [];
      }
      acc[action.category].push(action);
      return acc;
    }, {} as Record<string, CopilotAction[]>);
    
    return grouped;
  }, [filteredActions]);

  // Category labels
  const categoryLabels = {
    code: 'Code Actions',
    debug: 'Debug & Fix',
    docs: 'Documentation',
    analysis: 'Analysis',
    general: 'General'
  };

  // Category icons
  const categoryIcons = {
    code: Code,
    debug: Bug,
    docs: FileText,
    analysis: Zap,
    general: Sparkles
  };

  return (
    <div className={`copilot-actions ${className}`}>
      <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
        <DropdownMenuTrigger asChild>
          <Button 
            variant="ghost" 
            size="sm" 
            disabled={disabled}
            className="h-8 px-3 text-sm font-medium"
          >
            <Brain className="h-4 w-4 mr-2" />
            Copilot Actions
            <ChevronDown className="h-3 w-3 ml-1" />
          </Button>
        </DropdownMenuTrigger>
        
        <DropdownMenuContent 
          className="w-80 max-h-96 overflow-y-auto"
          align="start"
          sideOffset={4}
        >
          <DropdownMenuLabel className="flex items-center gap-2">
            <Brain className="h-4 w-4" />
            AI Copilot Actions
            {showShortcuts && (
              <Badge variant="secondary" className="text-xs">
                <Keyboard className="h-3 w-3 mr-1" />
                Shortcuts enabled
              </Badge>
            )}
          </DropdownMenuLabel>
          
          <DropdownMenuSeparator />
          
          {/* Context indicator */}
          {context.selectedText && (
            <div className="px-2 py-1 text-xs text-muted-foreground">
              <MessageSquare className="h-3 w-3 inline mr-1" />
              Text selected ({context.selectedText.length} chars)
            </div>
          )}
          
          {context.codeContext?.hasCode && (
            <div className="px-2 py-1 text-xs text-muted-foreground">
              <Code className="h-3 w-3 inline mr-1" />
              Code context detected
              {context.language && ` (${context.language})`}
            </div>
          )}
          
          {Object.keys(actionsByCategory).length > 0 ? (
            Object.entries(actionsByCategory).map(([category, actions]) => {
              const CategoryIcon = categoryIcons[category as keyof typeof categoryIcons];
              
              return (
                <div key={category}>
                  <DropdownMenuLabel className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
                    <CategoryIcon className="h-3 w-3" />
                    {categoryLabels[category as keyof typeof categoryLabels]}
                  </DropdownMenuLabel>
                  
                  {actions.map((action) => (
                    <DropdownMenuItem
                      key={action.id}
                      onClick={() => handleActionSelect(action)}
                      className="flex items-center gap-3 py-2 cursor-pointer"
                      disabled={action.requiresSelection && !context.selectedText}
                    >
                      <action.icon className="h-4 w-4 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-sm">{action.label}</div>
                        <div className="text-xs text-muted-foreground truncate">
                          {action.description}
                        </div>
                      </div>
                      {showShortcuts && action.shortcut && (
                        <DropdownMenuShortcut className="text-xs">
                          {action.shortcut.replace('Ctrl+Shift+', '⌃⇧')}
                        </DropdownMenuShortcut>
                      )}
                    </DropdownMenuItem>
                  ))}
                  
                  <DropdownMenuSeparator />
                </div>
              );
            })
          ) : (
            <div className="px-2 py-4 text-center text-sm text-muted-foreground">
              No actions available for current context
            </div>
          )}
          
          {/* Quick help */}
          <DropdownMenuLabel className="text-xs text-muted-foreground">
            💡 Tip: Type slash commands like <code>/copilot review</code> in chat
          </DropdownMenuLabel>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
};

// Export utility functions for slash command parsing
export const parseSlashCommand = (input: string): CopilotAction | null => {
  for (const { pattern, actionId } of SLASH_COMMAND_PATTERNS) {
    if (pattern.test(input)) {
      return COPILOT_ACTIONS.find(action => action.id === actionId) || null;
    }
  }
  return null;
};

export { SLASH_COMMAND_PATTERNS, COPILOT_ACTIONS };

export default CopilotActions;