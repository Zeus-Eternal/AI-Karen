import React, { useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
import type { CopilotAction, ChatContext } from "../types";
"use client";





  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";

  Brain,
  Code,
  Bug,
  RefreshCw,
  FileText,
  Lightbulb,
  Zap,
  Search,
  TestTube,
  Shield,
  Cpu,
  GitBranch,
  MessageSquare,
  Sparkles,
  ChevronDown,
} from "lucide-react";


interface CopilotActionsProps {
  actions?: CopilotAction[];
  onActionTriggered: (action: CopilotAction) => void;
  context: ChatContext;
  className?: string;
  disabled?: boolean;
  showShortcuts?: boolean;
}

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  Brain,
  Code,
  Bug,
  RefreshCw,
  FileText,
  Lightbulb,
  Zap,
  Search,
  TestTube,
  Shield,
  Cpu,
  GitBranch,
  MessageSquare,
  Sparkles,
};

const defaultActions: CopilotAction[] = [
  {
    id: "review",
    title: "Review Code",
    description: "Analyze code quality and potential issues",
    prompt: "/copilot review",
    category: "code",
    icon: Code,
    shortcut: "Ctrl+Shift+R",
  },
  {
    id: "debug",
    title: "Debug Issue",
    description: "Help identify and fix bugs",
    prompt: "/copilot debug",
    category: "debug",
    icon: Bug,
    shortcut: "Ctrl+Shift+D",
  },
  {
    id: "refactor",
    title: "Refactor Code",
    description: "Suggest refactoring opportunities",
    prompt: "/copilot refactor",
    category: "code",
    icon: RefreshCw,
  },
  {
    id: "tests",
    title: "Generate Tests",
    description: "Create unit tests for selected code",
    prompt: "/copilot generate_tests",
    category: "code",
    icon: TestTube,
  },
  {
    id: "docs",
    title: "Generate Docs",
    description: "Create documentation for code",
    prompt: "/copilot document",
    category: "docs",
    icon: FileText,
  },
  {
    id: "explain",
    title: "Explain Code",
    description: "Explain how the code works",
    prompt: "/copilot explain",
    category: "docs",
    icon: Lightbulb,
  },
  {
    id: "performance",
    title: "Performance Analysis",
    description: "Analyze performance characteristics",
    prompt: "/copilot analyze performance",
    category: "analysis",
    icon: Zap,
  },
  {
    id: "security",
    title: "Security Scan",
    description: "Find potential security issues",
    prompt: "/copilot security_scan",
    category: "analysis",
    icon: Shield,
  },
  {
    id: "complexity",
    title: "Complexity Analysis",
    description: "Evaluate code complexity",
    prompt: "/copilot analyze complexity",
    category: "analysis",
    icon: Cpu,
  },
  {
    id: "search",
    title: "Search Context",
    description: "Search for related information",
    prompt: "/copilot search",
    category: "general",
    icon: Search,
  },
  {
    id: "improve",
    title: "Suggest Improvements",
    description: "Get general improvement suggestions",
    prompt: "/copilot improve",
    category: "general",
    icon: Sparkles,
  },
  {
    id: "branch",
    title: "Outline Branch Plan",
    description: "Create a git branch plan",
    prompt: "/copilot plan branch",
    category: "general",
    icon: GitBranch,
  },
];

const resolveIcon = (icon?: CopilotAction["icon"]) => {
  if (!icon) return Brain;
  if (typeof icon === "string") {
    return iconMap[icon] ?? Brain;
  }
  return icon;
};

const CopilotActions: React.FC<CopilotActionsProps> = ({
  actions = defaultActions,
  onActionTriggered,
  context,
  className = "",
  disabled = false,
  showShortcuts = false,
}) => {
  const filteredActions = useMemo(() => {
    return actions.filter((action) =>
      action.requiresSelection ? Boolean(context?.selectedText) : true
    );
  }, [actions, context?.selectedText]);

  const groupedActions = useMemo(() => {
    return filteredActions.reduce<Record<string, CopilotAction[]>>((acc, action) => {
      const key = action.category ?? "general";
      acc[key] = acc[key] ? [...acc[key], action] : [action];
      return acc;
    }, {});
  }, [filteredActions]);

  const renderActionLabel = (action: CopilotAction) => {
    const Icon = resolveIcon(action.icon);
    return (
      <div className="flex items-center justify-between w-full">
        <div className="flex items-center gap-2">
          <Icon className="h-4 w-4 sm:w-auto md:w-full" />
          <span>{action.title}</span>
        </div>
        {showShortcuts && action.shortcut && (
          <Badge variant="outline" className="text-[10px]">
            {action.shortcut}
          </Badge>
        )}
      </div>
    );
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          variant="outline"
          size="sm"
          disabled={disabled}
          className={`flex items-center gap-2 ${className}`}
         aria-label="Button">
          <Sparkles className="h-4 w-4 sm:w-auto md:w-full" />
          Copilot Actions
          <ChevronDown className="h-3 w-3 sm:w-auto md:w-full" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-64 sm:w-auto md:w-full">
        <DropdownMenuLabel className="text-xs text-muted-foreground sm:text-sm md:text-base">
          Powered by CopilotKit
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        {Object.entries(groupedActions).map(([category, categoryActions], index) => (
          <React.Fragment key={category}>
            {index > 0 && <DropdownMenuSeparator />}
            <DropdownMenuLabel className="text-[11px] uppercase tracking-wide text-muted-foreground">
              {category}
            </DropdownMenuLabel>
            {categoryActions.map((action) => (
              <DropdownMenuItem
                key={action.id}
                onSelect={() => onActionTriggered(action)}
                className="text-sm md:text-base lg:text-lg"
              >
                {renderActionLabel(action)}
              </DropdownMenuItem>
            ))}
          </React.Fragment>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export const DEFAULT_COPILOT_ACTIONS = defaultActions;
export type { CopilotAction, ChatContext };
export default CopilotActions;
