"use client";

import * as React from 'react';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { MessageSquare, Code, Image, Brain, Zap } from 'lucide-react';
import { cn } from '@/lib/utils';

export type ChatMode = 'chat' | 'code' | 'image' | 'agent' | 'quick';

export interface ChatModeOption {
  id: ChatMode;
  label: string;
  description?: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
}

export interface ChatModeSelectorProps {
  mode: ChatMode;
  onModeChange: (mode: ChatMode) => void;
  modes?: ChatModeOption[];
  variant?: 'tabs' | 'buttons';
  className?: string;
}

const defaultModes: ChatModeOption[] = [
  {
    id: 'chat',
    label: 'Chat',
    description: 'General conversation',
    icon: MessageSquare,
  },
  {
    id: 'code',
    label: 'Code',
    description: 'Code assistance',
    icon: Code,
  },
  {
    id: 'image',
    label: 'Image',
    description: 'Image generation',
    icon: Image,
    badge: 'New',
  },
  {
    id: 'agent',
    label: 'Agent',
    description: 'Autonomous tasks',
    icon: Brain,
    badge: 'Beta',
  },
  {
    id: 'quick',
    label: 'Quick',
    description: 'Fast responses',
    icon: Zap,
  },
];

export default function ChatModeSelector({
  mode,
  onModeChange,
  modes = defaultModes,
  variant = 'tabs',
  className,
}: ChatModeSelectorProps) {
  if (variant === 'buttons') {
    return (
      <div className={cn('flex flex-wrap gap-2', className)}>
        {modes.map((modeOption) => {
          const Icon = modeOption.icon;
          const isActive = mode === modeOption.id;

          return (
            <button
              key={modeOption.id}
              onClick={() => onModeChange(modeOption.id)}
              className={cn(
                'flex items-center gap-2 px-4 py-2 rounded-lg border transition-all',
                isActive
                  ? 'bg-blue-500 text-white border-blue-500'
                  : 'bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-700 hover:border-blue-400 dark:hover:border-blue-600'
              )}
              title={modeOption.description}
            >
              <Icon className="h-4 w-4" />
              <span className="font-medium">{modeOption.label}</span>
              {modeOption.badge && (
                <Badge
                  variant={isActive ? 'secondary' : 'outline'}
                  className="ml-1 text-xs"
                >
                  {modeOption.badge}
                </Badge>
              )}
            </button>
          );
        })}
      </div>
    );
  }

  // Default tabs variant
  return (
    <Tabs value={mode} onValueChange={(value) => onModeChange(value as ChatMode)} className={className}>
      <TabsList className="w-full justify-start">
        {modes.map((modeOption) => {
          const Icon = modeOption.icon;

          return (
            <TabsTrigger
              key={modeOption.id}
              value={modeOption.id}
              className="flex items-center gap-2"
              title={modeOption.description}
            >
              <Icon className="h-4 w-4" />
              <span>{modeOption.label}</span>
              {modeOption.badge && (
                <Badge variant="secondary" className="ml-1 text-xs">
                  {modeOption.badge}
                </Badge>
              )}
            </TabsTrigger>
          );
        })}
      </TabsList>
    </Tabs>
  );
}

export { ChatModeSelector };
