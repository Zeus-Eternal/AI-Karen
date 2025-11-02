"use client";

import React from 'react';
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { webUIConfig } from "@/lib/config";
import { cn } from "@/lib/utils";
import {
  Activity,
  Brain,
  Code,
  MessageSquare,
  Monitor,
  Terminal,
  Zap,
  type LucideIcon,
} from "lucide-react";

interface DeveloperNavProps {
  className?: string;
}

export default function DeveloperNav({ className }: DeveloperNavProps) {
  const pathname = usePathname();

  if (!webUIConfig.enableDeveloperTools) {
    return null;
  }

  const navItems: Array<{
    href: string;
    label: string;
    icon: LucideIcon;
    description: string;
    badge: string | null;
  }> = [
    {
      href: "/developer",
      label: "Dev Studio",
      icon: Code,
      description: "Component management and monitoring",
      badge: "AI",
    },
    {
      href: "/developer/chat",
      label: "Chat Debug",
      icon: MessageSquare,
      description: "Chat system debugging and metrics",
      badge: "Live",
    },
    {
      href: "/developer/hooks",
      label: "Hook System",
      icon: Activity,
      description: "Hook management and execution",
      badge: null,
    },
    {
      href: "/developer/ai-assistant",
      label: "AI Assistant",
      icon: Brain,
      description: "CopilotKit development assistance",
      badge: "Beta",
    },
    {
      href: "/developer/terminal",
      label: "Terminal",
      icon: Terminal,
      description: "Integrated development terminal",
      badge: null,
    },
    {
      href: "/developer/monitoring",
      label: "Monitoring",
      icon: Monitor,
      description: "System performance and health",
      badge: "Real-time",
    },
  ];

  const getBadgeVariant = (badge: string | null) => {
    switch (badge) {
      case "AI":
        return "default" as const;
      case "Live":
        return "destructive" as const;
      case "Beta":
        return "secondary" as const;
      default:
        return "outline" as const;
    }
  };

  return (
    <nav className={cn("space-y-2", className)}>
      <div className="px-3 py-2">
        <h2 className="mb-2 px-4 text-lg font-semibold tracking-tight flex items-center gap-2">
          <Zap className="h-5 w-5 text-blue-500 " />
        </h2>
        <div className="space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;
            
            return (
              <Button
                key={item.href}
                asChild
                variant={isActive ? "secondary" : "ghost"}
                className={cn(
                  "w-full justify-start h-auto p-3",
                  isActive && "bg-secondary"
                )}
              >
                <Link href={item.href} aria-label={item.label}>
                  <div className="flex items-center gap-3 w-full">
                    <Icon className="h-4 w-4 flex-shrink-0 " />
                    <div className="flex-1 text-left">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{item.label}</span>
                        {item.badge && (
                          <Badge
                            variant={getBadgeVariant(item.badge)}
                            className="text-xs sm:text-sm md:text-base"
                          >
                            {item.badge}
                          </Badge>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground mt-1 sm:text-sm md:text-base">
                        {item.description}
                      </p>
                    </div>
                  </div>
                </Link>
              </Button>
            );
          })}
        </div>
      </div>
      
      <div className="px-3 py-2">
        <div className="px-4 py-2 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950 dark:to-purple-950 rounded-lg border">
          <div className="flex items-center gap-2 mb-1">
            <Brain className="h-4 w-4 text-purple-500 " />
            <span className="text-sm font-medium md:text-base lg:text-lg">AI Assistant</span>
          </div>
          <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
            Ask me about component optimization, code generation, or system health.
          </p>
        </div>
      </div>
    </nav>
  );
}