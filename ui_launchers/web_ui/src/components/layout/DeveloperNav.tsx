"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  Code, 
  Terminal, 
  Activity, 
  Brain, 
  MessageSquare, 
  Settings,
  Zap,
  Monitor
} from "lucide-react";
import { cn } from "@/lib/utils";

interface DeveloperNavProps {
  className?: string;
}

export default function DeveloperNav({ className }: DeveloperNavProps) {
  const pathname = usePathname();
  
  const navItems = [
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

  return (
    <nav className={cn("space-y-2", className)}>
      <div className="px-3 py-2">
        <h2 className="mb-2 px-4 text-lg font-semibold tracking-tight flex items-center gap-2">
          <Zap className="h-5 w-5 text-blue-500" />
          Developer Tools
        </h2>
        <div className="space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;
            
            return (
              <Link key={item.href} href={item.href}>
                <Button
                  variant={isActive ? "secondary" : "ghost"}
                  className={cn(
                    "w-full justify-start h-auto p-3",
                    isActive && "bg-secondary"
                  )}
                >
                  <div className="flex items-center gap-3 w-full">
                    <Icon className="h-4 w-4 flex-shrink-0" />
                    <div className="flex-1 text-left">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{item.label}</span>
                        {item.badge && (
                          <Badge 
                            variant={item.badge === "AI" ? "default" : 
                                   item.badge === "Live" ? "destructive" :
                                   item.badge === "Beta" ? "secondary" :
                                   "outline"}
                            className="text-xs"
                          >
                            {item.badge}
                          </Badge>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">
                        {item.description}
                      </p>
                    </div>
                  </div>
                </Button>
              </Link>
            );
          })}
        </div>
      </div>
      
      <div className="px-3 py-2">
        <div className="px-4 py-2 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950 dark:to-purple-950 rounded-lg border">
          <div className="flex items-center gap-2 mb-1">
            <Brain className="h-4 w-4 text-purple-500" />
            <span className="text-sm font-medium">AI Assistant</span>
          </div>
          <p className="text-xs text-muted-foreground">
            Ask me about component optimization, code generation, or system health.
          </p>
        </div>
      </div>
    </nav>
  );
}